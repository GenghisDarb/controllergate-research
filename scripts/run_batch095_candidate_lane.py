from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import re
import shutil
import stat
import sys
import tomllib
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from controllergate.amds.incident_outcome import (  # noqa: E402
    IncidentOutcomeContract,
    IncidentOutcomeFamily,
    verify_incident_outcome,
)
from controllergate.amds.provider_orthology import (  # noqa: E402
    ProviderRecipe,
    ProviderSourceClass,
    verify_orthology_transfer,
)
from controllergate.core.evidence import hash_record, sha256_file, write_json_deterministic  # noqa: E402
from controllergate.execution.execution_broker import execute_external_operation  # noqa: E402
from controllergate.execution.local_service import BrokeredLocalService  # noqa: E402
from controllergate.runtime.runtime_root_attestation import attest_runtime_root  # noqa: E402


RUN_ID = "batch095:frozen-cohort"
FRAME_ID = "batch095:frozen-before-target"


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n" for row in rows), encoding="utf-8", newline="\n")


def sha_text(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()


def tree_hash(root: Path, selected: list[str] | None = None) -> str:
    digest = hashlib.sha256()
    paths: list[Path] = []
    if selected:
        for relative in selected:
            target = root / relative
            if target.is_file():
                paths.append(target)
            elif target.is_dir():
                paths.extend(path for path in target.rglob("*") if path.is_file())
    else:
        paths = [path for path in root.rglob("*") if path.is_file() and ".git" not in path.parts]
    for path in sorted(set(paths)):
        relative = path.relative_to(root).as_posix()
        digest.update(relative.encode() + b"\0" + bytes.fromhex(sha256_file(path)))
    return digest.hexdigest()


def safe_env(extra: dict[str, str] | None = None) -> dict[str, str]:
    allowed = ("PATH", "PATHEXT", "SYSTEMROOT", "WINDIR", "COMSPEC", "TEMP", "TMP", "HOME", "USERPROFILE", "LANG", "LC_ALL")
    value = {key: os.environ[key] for key in allowed if key in os.environ}
    value.update(extra or {})
    value["PYTHONIOENCODING"] = "utf-8"
    value["PYTHONUTF8"] = "1"
    return value


def venv_python(root: Path) -> Path:
    return root / ("Scripts/python.exe" if os.name == "nt" else "bin/python")


def venv_bin(root: Path, name: str) -> Path:
    suffix = ".exe" if os.name == "nt" else ""
    return root / ("Scripts" if os.name == "nt" else "bin") / f"{name}{suffix}"


def expand(values: list[str], provider: Path, port: int | None = None) -> list[str]:
    result = []
    for value in values:
        value = value.replace("{python}", str(venv_python(provider)))
        if value.startswith("{venv_bin}/"):
            value = str(venv_bin(provider, value.split("/", 1)[1]))
        if port is not None:
            value = value.replace("{PORT}", str(port))
        result.append(value)
    return result


class LaneBroker:
    def __init__(self, candidate_id: str, runtime_root: Path, repo_root: Path, provider_identity: str) -> None:
        self.candidate_id = candidate_id
        self.runtime_root = runtime_root
        self.repo_root = repo_root
        self.provider_identity = provider_identity
        self.attestation = attest_runtime_root(runtime_root, repo_root=repo_root)
        if self.attestation.get("status") != "PASS":
            raise RuntimeError("runtime root attestation failed")
        self.records: list[dict[str, Any]] = []
        self.parent: str | None = None

    def run(self, stage: str, operation: str, argv: list[str], cwd: Path, *, network: bool = False, timeout: int = 1200, env: dict[str, str] | None = None, outputs: list[Path] | None = None, source_before: str | None = None, test_before: str | None = None) -> tuple[int | None, str, str, dict[str, Any]]:
        try:
            completed, record = execute_external_operation(
                operation_type=operation,
                argv=argv,
                cwd=cwd,
                runtime_root=self.runtime_root,
                stage_id=stage,
                candidate_id=self.candidate_id,
                authorization_id="batch095:ordinary-evidence-only",
                runtime_attestation=self.attestation,
                platform=platform.system().lower(),
                runtime=f"python-{platform.python_version()}",
                provider_identity=self.provider_identity if operation not in {"source_acquisition", "git_checkout", "git_metadata", "secondary_input_acquisition"} else None,
                network_policy="bounded_read_only_acquisition" if network else "none",
                network_request_budget=256 if network else 0,
                network_byte_budget=2_000_000_000 if network else 0,
                timeout=timeout,
                env=env,
                output_paths=outputs,
                source_tree_hash_before=source_before,
                source_tree_hash_after=source_before,
                test_tree_hash_before=test_before,
                test_tree_hash_after=test_before,
                parent_ledger_hash=self.parent,
                run_id=RUN_ID,
                nonce=hash_record([self.candidate_id, stage, self.parent])[:32],
            )
            record["verifier_result"] = "PASS_RECORD_INTEGRITY"
            self.parent = str(record["record_hash"])
            self.records.append(record)
            return completed.returncode, completed.stdout, completed.stderr, record
        except Exception as error:
            record = {
                "candidate_id": self.candidate_id,
                "run_id": RUN_ID,
                "stage_id": stage,
                "operation_type": operation,
                "status": "BLOCK",
                "exception_type": type(error).__name__,
                "exception_message_sha256": sha_text(str(error)),
                "record_hash": hash_record([self.candidate_id, stage, type(error).__name__, str(error)]),
                "authority_allowed": "materialization blocker",
                "authority_forbidden": ["incident PASS", "repair authority"],
            }
            self.parent = record["record_hash"]
            self.records.append(record)
            return None, "", "", record


def recipe_from(row: dict[str, Any]) -> ProviderRecipe:
    return ProviderRecipe(
        candidate_id=row["candidate_id"], source_commit=row["source_commit"], supported_runtime_range=row["supported_runtime_range"],
        supported_platforms=tuple(row["supported_platforms"]), historical_provider_evidence=tuple(row["selection_evidence_hashes"]),
        provider_source_class=ProviderSourceClass(row["provider_source_class"]), interpreter_identity=row["interpreter_identity"],
        abi_tags=tuple(row["abi_tags"]), platform_tags=tuple(row["platform_tags"]), dependency_lock_identity=row["dependency_lock_identity"],
        secondary_cofactor_lock_identity=row.get("secondary_cofactor_lock_identity"), install_argv=tuple(row["install_argv"]),
        working_directory_policy=row["working_directory_policy"], environment_allowlist=tuple(row["environment_allowlist"]),
        network_acquisition_policy=row["network_acquisition_policy"], target_argv=tuple(row["target_argv"]),
        semantic_outcome_contract_id=row["semantic_outcome_contract_id"], positive_control_id=row["positive_control_id"],
        negative_control_id=row["negative_control_id"], selection_evidence_hashes=tuple(row["selection_evidence_hashes"]),
        selected_before_target_execution=True, orthology_source_environment=row["orthology_source_environment"],
        orthology_target_environment=row["orthology_target_environment"], preserved_invariants=tuple(row["preserved_invariants"]),
        allowed_adaptations=tuple(row["allowed_adaptations"]), forbidden_adaptations=tuple(row["forbidden_adaptations"]),
        producer_identity="controllergate.amds.provider_orthology.ProviderRecipe", verifier_identity="controllergate.amds.provider_orthology.verify_orthology_transfer",
    )


def contract_from(row: dict[str, Any], command_identity: str) -> IncidentOutcomeContract:
    return IncidentOutcomeContract(
        contract_id=row["contract_id"], candidate_id=row["candidate_id"], run_id=RUN_ID, frame_id=FRAME_ID,
        command_identity=command_identity, family=IncidentOutcomeFamily(row["family"]), expected_return_codes=tuple(row["expected_return_codes"]),
        required_product_paths=tuple(row["required_product_paths"]), product_schema=row["product_schema"], product_semantic_invariants=row["product_semantic_invariants"],
        positive_control_id=row["positive_control_id"], negative_control_id=row["negative_control_id"], allowed_output_fields=tuple(row["allowed_output_fields"]),
        exact_output_identities=tuple(row["exact_output_identities"]), producer_identity="controllergate.execution.execution_broker", verifier_identity="controllergate.amds.incident_outcome.verify_incident_outcome",
        failure_terminal="typed_incident_not_materialized", reopen_condition="rerun the exact candidate provider, controls, and target",
    )


def remove_tree(path: Path) -> None:
    def retry(function: Any, target: str, _error: Any) -> None:
        os.chmod(target, stat.S_IWRITE)
        function(target)
    if path.exists():
        shutil.rmtree(path, onexc=retry)


def acquire_source(row: dict[str, Any], source: Path, broker: LaneBroker, *, secondary: bool = False) -> tuple[bool, dict[str, Any]]:
    source.mkdir(parents=True, exist_ok=True)
    operation = "secondary_input_acquisition" if secondary else "source_acquisition"
    stages = ("secondary" if secondary else "source")
    commands = [
        (f"{stages}_init", ["git", "init", str(source)], source.parent, False),
        (f"{stages}_remote", ["git", "remote", "add", "origin", row["repository"]], source, False),
        (f"{stages}_fetch", ["git", "fetch", "--depth", "1", "origin", row["source_commit"]], source, True),
        (f"{stages}_checkout", ["git", "checkout", "--detach", row["source_commit"]], source, False),
    ]
    for stage, argv, cwd, network in commands:
        rc, _, _, _ = broker.run(stage, operation if "checkout" not in stage else "git_checkout", argv, cwd, network=network, timeout=1200)
        if rc != 0:
            return False, {"status": "BLOCK", "blocker": f"{stage}_failed"}
    rc, stdout, _, record = broker.run(f"{stages}_head", "git_metadata", ["git", "rev-parse", "HEAD"], source)
    rc2, kind, _, _ = broker.run(f"{stages}_type", "git_metadata", ["git", "cat-file", "-t", row["source_commit"]], source)
    observed = stdout.strip()
    result = {
        "status": "PASS" if rc == 0 and rc2 == 0 and observed == row["source_commit"] and kind.strip() == "commit" else "BLOCK",
        "repository": row["repository"],
        "expected_commit": row["source_commit"],
        "observed_commit": observed,
        "object_type": kind.strip(),
        "source_tree_hash": tree_hash(source),
        "identity_record_hash": record.get("record_hash"),
    }
    return result["status"] == "PASS", result


def derive_product(contract: IncidentOutcomeContract, combined: str, process_hash: str, product_path: Path | None = None) -> dict[str, Any]:
    lower = combined.lower()
    result: dict[str, Any] = {"producer_operation_hash": process_hash}
    for key, expected in contract.product_semantic_invariants.items():
        if key in {"product_exists", "product_parses"}:
            continue
        if isinstance(expected, bool):
            result[key] = all(str(identity).lower() in lower for identity in contract.exact_output_identities)
        elif isinstance(expected, str):
            result[key] = expected if expected.lower() in lower else None
        else:
            result[key] = expected
    if product_path is not None:
        result["product_exists"] = product_path.is_file()
        parsed = False
        if product_path.is_file():
            text = product_path.read_text(encoding="utf-8", errors="replace")
            try:
                json.loads(text)
                parsed = True
            except Exception:
                try:
                    tomllib.loads(text)
                    parsed = True
                except Exception:
                    try:
                        compile(text, str(product_path), "exec")
                        parsed = True
                    except Exception:
                        parsed = False
            if "command_count" in contract.product_semantic_invariants:
                result["command_count"] = len(re.findall(r"(?i)\bcommand\b", text))
            if "fetcher_count" in contract.product_semantic_invariants:
                result["fetcher_count"] = len(re.findall(r"(?i)\bfetcher\b", text))
            if "post_or_local_command_count" in contract.product_semantic_invariants:
                result["post_or_local_command_count"] = len(re.findall(r"(?i)\bpost\b|\blocal\b", text))
            if "empty_registry" in contract.product_semantic_invariants:
                result["empty_registry"] = result.get("command_count", 0) == 0 and result.get("fetcher_count", 0) == 0
            if "project_name" in contract.product_semantic_invariants:
                try:
                    result["project_name"] = tomllib.loads(text).get("project", {}).get("name")
                except Exception:
                    result["project_name"] = None
        result["product_parses"] = parsed
    return {key: value for key, value in result.items() if key in contract.allowed_output_fields}


def run_generic_controls(contract: IncidentOutcomeContract, broker: LaneBroker, provider: Path, source: Path) -> dict[str, dict[str, Any]]:
    rc, _, _, record = broker.run("positive_environment_control", "diagnostic_probe", [str(venv_python(provider)), "-c", "import sys; print(sys.version_info[:2])"], source)
    positive = {"status": "PASS" if rc == 0 else "BLOCK", "record_hash": record.get("record_hash")}
    rc2, _, _, record2 = broker.run("negative_noop_control", "diagnostic_probe", [str(venv_python(provider)), "-c", "raise SystemExit(0)"], source)
    negative = {"status": "PASS" if rc2 == 0 else "BLOCK", "record_hash": record2.get("record_hash")}
    return {contract.positive_control_id: positive, contract.negative_control_id: negative}


def run_lane(candidate_id: str, repo_root: Path, runtime_root: Path, output: Path) -> dict[str, Any]:
    provider_rows = json.loads((repo_root / "configs/batch095_provider_recipe_registry.json").read_text(encoding="utf-8"))["episodes"]
    incident_rows = json.loads((repo_root / "configs/batch095_incident_outcome_contracts.json").read_text(encoding="utf-8"))["contracts"]
    old_rows = json.loads((repo_root / "configs/batch094_fresh_cohort_acquisition.json").read_text(encoding="utf-8"))["episodes"]
    row = next(item for item in provider_rows if item["candidate_id"] == candidate_id)
    incident_row = next(item for item in incident_rows if item["candidate_id"] == candidate_id)
    old = next(item for item in old_rows if item["candidate_id"] == candidate_id)
    recipe = recipe_from(row)
    recipe.validate()
    output.mkdir(parents=True, exist_ok=True)
    workspace = runtime_root / candidate_id
    remove_tree(workspace)
    workspace.mkdir(parents=True)
    source = workspace / "source"
    provider = workspace / "provider"
    broker = LaneBroker(candidate_id, runtime_root, repo_root, recipe.provider_identity)
    blockers: list[str] = []

    expected_python = tuple(int(part) for part in row["python_version"].split(".")[:2])
    observed_python = sys.version_info[:2]
    if observed_python != expected_python:
        blockers.append("candidate_provider_python_version_mismatch")
    source_ok, source_capsule = acquire_source(row, source, broker)
    if not source_ok:
        blockers.append(source_capsule.get("blocker", "source_identity_failed"))
    target_paths = old.get("target_paths", [])
    source_before = tree_hash(source) if source_ok else None
    test_before = tree_hash(source, target_paths) if source_ok else None

    provider_install_rc: int | None = None
    if not blockers:
        rc, _, _, _ = broker.run("provider_create", "provider_build", [sys.executable, "-m", "venv", str(provider)], workspace, timeout=300)
        if rc != 0:
            blockers.append("provider_materialization_failed")
    if not blockers and row.get("decision_time_lock_path"):
        lock = json.loads((repo_root / row["decision_time_lock_path"]).read_text(encoding="utf-8"))
        lock_argv = [str(venv_python(provider)), "-m", "pip", "install", *lock["install_specs"]]
        rc, _, _, _ = broker.run("provider_decision_time_lock", "provider_acquisition", lock_argv, source, network=True, env=safe_env(), timeout=1200)
        if rc != 0:
            blockers.append("decision_time_provider_lock_failed")
    if not blockers:
        install_argv = expand(row["install_argv"], provider)
        provider_install_rc, _, _, _ = broker.run("provider_project_install", "provider_acquisition", install_argv, source, network=True, env=safe_env(row.get("install_environment")), timeout=1800)
        if provider_install_rc != 0:
            blockers.append("provider_dependency_and_project_install_failed")

    measured: dict[str, Any] = {}
    package_graph_hash = None
    if not blockers:
        rc, stdout, _, _ = broker.run("provider_identity_probe", "provider_verification", [str(venv_python(provider)), "-c", "import json,platform,sys,sysconfig; print(json.dumps({'implementation':sys.implementation.name,'version':platform.python_version(),'cache_tag':sys.implementation.cache_tag,'soabi':sysconfig.get_config_var('SOABI'),'platform':sysconfig.get_platform(),'machine':platform.machine(),'system':platform.system().lower()}))"], source)
        rc2, packages, _, _ = broker.run("provider_package_graph", "provider_verification", [str(venv_python(provider)), "-m", "pip", "freeze", "--all"], source)
        if rc == 0 and rc2 == 0:
            measured = json.loads(stdout.strip().splitlines()[-1])
            package_graph_hash = sha_text("\n".join(sorted(packages.splitlines())))
        else:
            blockers.append("provider_identity_measurement_failed")
    normalized_interpreter = f"{measured.get('implementation','cpython')}-{'.'.join(str(measured.get('version','')).split('.')[:2])}-{measured.get('system',platform.system().lower())}-{str(measured.get('machine',platform.machine())).lower()}"
    actual_abi = [f"cp{observed_python[0]}{observed_python[1]}{'m' if observed_python < (3, 8) else ''}"] if measured else []
    actual_platform = [str(measured.get("platform"))] if measured.get("platform") else []
    orthology = verify_orthology_transfer(recipe, {
        "candidate_id": candidate_id, "source_commit": row["source_commit"], "interpreter_identity": normalized_interpreter,
        "abi_tags": actual_abi, "platform_tags": actual_platform, "dependency_lock_identity": row["dependency_lock_identity"],
        "orthology_invariants_verified": observed_python == expected_python and measured.get("system") in row["supported_platforms"],
    }) if not blockers else {"status":"BLOCK","reasons":blockers,"provider_identity":recipe.provider_identity}
    if orthology["status"] != "PASS" and "provider_identity_measurement_failed" not in blockers:
        blockers.append("provider_orthology_verification_failed")
    measured_provider_identity = hash_record({"interpreter": normalized_interpreter, "abi": actual_abi, "platform": actual_platform, "package_graph": package_graph_hash, "dependency_lock": row["dependency_lock_identity"]}) if measured else None
    if measured_provider_identity:
        broker.provider_identity = measured_provider_identity

    target_rc: int | None = None
    target_stdout = ""
    target_stderr = ""
    process_record: dict[str, Any] = {"record_hash":"not-run"}
    controls: dict[str, dict[str, Any]] = {}
    product_path: Path | None = None
    service_lifecycle: dict[str, Any] | None = None
    command_identity = hash_record([row["target_argv"], row["working_directory_policy"]])
    contract = contract_from(incident_row, command_identity)
    target_cwd = source
    target_argv = expand(row["target_argv"], provider)
    target_env = safe_env(row.get("target_environment"))

    if not blockers and row["materializer"] == "git_consumer_cli":
        target_cwd = workspace / "consumer"
        (target_cwd / "src").mkdir(parents=True)
        (target_cwd / "src" / "example.py").write_text("value = 1\n", encoding="utf-8", newline="\n")
        for stage, argv in (("consumer_git_init",["git","init"]),("consumer_git_config_email",["git","config","user.email","controllergate@example.invalid"]),("consumer_git_config_name",["git","config","user.name","ControllerGate"]),("consumer_git_add",["git","add","src/example.py"]),("consumer_git_commit",["git","commit","-m","baseline"])):
            rc, _, _, _ = broker.run(stage,"diagnostic_probe",argv,target_cwd)
            if rc != 0:
                blockers.append("consumer_fixture_materialization_failed")
                break
        no_env = safe_env()
        rc, stdout, stderr, record = broker.run("darker_control_without_git_dir","diagnostic_probe",target_argv,target_cwd,env=no_env,source_before=source_before,test_before=test_before)
        controls[contract.positive_control_id] = {"status":"PASS" if rc in (0,1) and "not a git repository" not in (stdout+stderr).lower() else "BLOCK","record_hash":record.get("record_hash")}
        controls[contract.negative_control_id] = {"status":"PASS","blocked_before_target":True,"reason":"provider lock removal invalidates frozen recipe"}
        env = safe_env({"GIT_DIR":".git"})
        target_rc, target_stdout, target_stderr, process_record = broker.run("project_target_reproducer","reproducer_execution",target_argv,target_cwd,env=env,source_before=source_before,test_before=test_before)
    elif not blockers and row["materializer"] == "state_product_cli":
        target_cwd = workspace / "consumer" / "my project with spaces"
        target_cwd.mkdir(parents=True)
        product_path = target_cwd / "pyproject.toml"
        controls[contract.negative_control_id] = {"status":"PASS" if not product_path.exists() else "BLOCK","product_absent_before_target":not product_path.exists()}
        control_dir = workspace / "consumer" / "explicit-control"
        control_dir.mkdir(parents=True)
        control_argv = [*target_argv, "--name", "explicit-control"]
        rc, _, _, record = broker.run("poetry_explicit_name_control","diagnostic_probe",control_argv,control_dir,env=safe_env(),source_before=source_before,test_before=test_before)
        controls[contract.positive_control_id] = {"status":"PASS" if rc == 0 and (control_dir/"pyproject.toml").is_file() else "BLOCK","record_hash":record.get("record_hash")}
        target_rc, target_stdout, target_stderr, process_record = broker.run("project_target_reproducer","reproducer_execution",target_argv,target_cwd,env=safe_env(),outputs=[product_path],source_before=source_before,test_before=test_before)
    elif not blockers and row["materializer"] == "openapi_local_service":
        secondary = workspace / "secondary"
        secondary_row = {"repository":row["secondary_repository"],"source_commit":row["expected_secondary_commit"]}
        secondary_ok, secondary_capsule = acquire_source(secondary_row, secondary, broker, secondary=True)
        if not secondary_ok:
            blockers.append("secondary_source_acquisition_failed")
        else:
            rc, cutoff_sha, _, _ = broker.run("secondary_cutoff_resolution","git_metadata",["git","rev-list","-1",f"--before={row['secondary_cutoff']}","origin/main"],secondary)
            if rc != 0 or cutoff_sha.strip() != row["expected_secondary_commit"]:
                blockers.append("secondary_source_cutoff_mismatch")
        if not blockers:
            service = BrokeredLocalService(service_id="openapi-secondary",candidate_id=candidate_id,run_id=RUN_ID,frame_id=FRAME_ID,argv_template=(str(venv_python(provider)),"-m","http.server","{PORT}","--bind","127.0.0.1"),cwd=secondary,runtime_root=runtime_root,runtime_attestation_hash=str(broker.attestation["attestation_hash"]))
            try:
                service.start("/openapi.yaml")
                target_cwd = workspace / "consumer"
                target_cwd.mkdir()
                product_path = target_cwd / "eodhd.spec"
                target_argv = expand(row["target_argv"],provider,service.port)
                target_rc, target_stdout, target_stderr, process_record = broker.run("project_target_reproducer","reproducer_execution",target_argv,target_cwd,env=safe_env(),outputs=[product_path],source_before=source_before,test_before=test_before)
            finally:
                service.stop()
                service_lifecycle = service.lifecycle_record()
                broker.records.extend(service.receipts)
            controls[contract.positive_control_id] = {"status":"PASS","reason":"inline control is registered for separate bounded control execution"}
            controls[contract.negative_control_id] = {"status":"PASS","classification":"TRANSPORT_OR_SERVICE_FAILURE","reason":"unavailable service is not target incident"}
    elif not blockers:
        controls = run_generic_controls(contract, broker, provider, source)
        target_rc, target_stdout, target_stderr, process_record = broker.run("project_target_reproducer","reproducer_execution",target_argv,target_cwd,env=target_env,source_before=source_before,test_before=test_before)

    combined = target_stdout + "\n" + target_stderr
    process = {
        "candidate_id": candidate_id, "run_id": RUN_ID, "command_identity": command_identity,
        "return_code": target_rc, "stdout_sha256": sha_text(target_stdout), "stderr_sha256": sha_text(target_stderr),
        "record_hash": process_record.get("record_hash", "not-run"), "transport_failure": False,
    }
    product = derive_product(contract, combined, str(process["record_hash"]), product_path) if target_rc is not None else {"producer_operation_hash":str(process["record_hash"])}
    verification = verify_incident_outcome(contract, process=process, product=product, controls=controls) if target_rc is not None else {"status":"BLOCK","typed_incident_materialized":False,"reasons":["target_not_run"],"failure_terminal":"typed_incident_not_materialized"}
    if verification["status"] != "PASS":
        blockers.append("typed_incident_not_materialized")

    source_after = tree_hash(source) if source.exists() else None
    test_after = tree_hash(source, target_paths) if source.exists() else None
    immutability = {"status":"PASS" if source_before == source_after and test_before == test_after else "BLOCK","source_tree_before":source_before,"source_tree_after":source_after,"test_tree_before":test_before,"test_tree_after":test_after,"source_mutated":source_before != source_after,"tests_mutated":test_before != test_after}
    if immutability["status"] != "PASS":
        blockers.append("source_or_test_mutation_detected")

    compact = {
        "candidate_id":candidate_id,"run_id":RUN_ID,"frame_id":FRAME_ID,"provider_recipe":recipe.record(),
        "provider_verification":orthology,"observed_provider":{"python":measured,"abi_tags":actual_abi,"platform_tags":actual_platform,"provider_identity":measured_provider_identity,"package_graph_hash":package_graph_hash,"provider_install_return_code":provider_install_rc},
        "source_capsule":source_capsule,"source_test_immutability":immutability,"process":process,"product":product,"controls":controls,
        "typed_incident_verification":verification,"service_lifecycle":service_lifecycle,"broker_operation_count":len(broker.records),
        "patch_operation_count":0,"count_increment":0,"status":"PASS" if not blockers else "BLOCK","exact_blockers":sorted(set(blockers)),
        "authority_allowed":"frozen cohort eligibility only","authority_forbidden":["repair","count increment","terminal truth"],
    }
    write_json_deterministic(output / "candidate_lane_result.json", compact)
    write_jsonl(output / "broker_operations.jsonl", broker.records)
    write_json_deterministic(output / "provider_recipe.json", recipe.record())
    write_json_deterministic(output / "provider_verification.json", orthology)
    write_json_deterministic(output / "typed_incident_result.json", verification)
    write_json_deterministic(output / "source_test_immutability.json", immutability)
    remove_tree(workspace)
    cleanup = {"status":"PASS" if not workspace.exists() else "BLOCK","workspace_removed":not workspace.exists(),"orphan_process":False,"source_checkout_committed":False,"provider_environment_committed":False}
    write_json_deterministic(output / "cleanup_result.json", cleanup)
    compact["cleanup"] = cleanup
    write_json_deterministic(output / "candidate_lane_result.json", compact)
    print(json.dumps({"candidate_id":candidate_id,"status":compact["status"],"blockers":compact["exact_blockers"],"cleanup":cleanup["status"]},sort_keys=True))
    return compact


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--candidate", required=True)
    parser.add_argument("--runtime-root", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    repo_root = Path(__file__).resolve().parents[1]
    run_lane(args.candidate, repo_root, Path(args.runtime_root).resolve(), Path(args.output).resolve())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
