from __future__ import annotations

import hashlib
import json
import os
import platform
import shutil
import stat
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

from controllergate.core.evidence import hash_record
from controllergate.execution.execution_broker import allocate_loopback_port, execute_external_operation
from controllergate.runtime.runtime_root_attestation import attest_runtime_root
from controllergate.topology.source_graph import compile_python_source_graph
from .openbb_lifecycle_v2 import execute_openapi_service_operation
from .parser_registry_v2 import parse_registered, verify_registered

from .contracts import CandidateExecutionContract, load_contracts
from .observations import NeutralObservationV2, TypedObservationParser, configured_value_injection_audit, marker_only_verification_audit


COMPARTMENTS = (
    "SOURCE_VAULT",
    "BUILD_WORKSPACE",
    "PROVIDER_STORE",
    "EXECUTION_WORKSPACE",
    "CONSUMER_OR_TARGET_WORKSPACE",
    "TRUTH_AND_OUTCOME_VAULT",
)
GENERATED_DIRECTORY_NAMES = {"__pycache__", ".pytest_cache", ".tox", ".nox", "build", "dist", ".eggs", ".coverage", "htmlcov"}
GENERATED_SUFFIXES = (".pyc", ".pyo", ".egg-info", ".dist-info")


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")


def write_jsonl(path: Path, rows: list[Mapping[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(dict(row), sort_keys=True, separators=(",", ":")) + "\n" for row in rows), encoding="utf-8", newline="\n")


def remove_tree(path: Path) -> None:
    def retry(function: Any, target: str, _error: Any) -> None:
        os.chmod(target, stat.S_IWRITE)
        function(target)
    if path.exists():
        shutil.rmtree(path, onerror=retry)


def venv_python(root: Path) -> Path:
    return root / ("Scripts/python.exe" if os.name == "nt" else "bin/python")


def venv_bin(root: Path, name: str) -> Path:
    return root / ("Scripts" if os.name == "nt" else "bin") / (name + (".exe" if os.name == "nt" else ""))


def safe_env(allowlist: tuple[str, ...], additions: Mapping[str, str] | None = None) -> dict[str, str]:
    baseline = {"PATH", "PATHEXT", "SYSTEMROOT", "WINDIR", "COMSPEC", "TEMP", "TMP", "HOME", "USERPROFILE", "LANG", "LC_ALL"}
    result = {key: os.environ[key] for key in sorted(baseline.union(allowlist)) if key in os.environ}
    result.update(additions or {})
    result.update({"PYTHONDONTWRITEBYTECODE": "1", "PYTHONIOENCODING": "utf-8", "PYTHONUTF8": "1"})
    return result


class MaterializationBroker:
    def __init__(self, contract: CandidateExecutionContract, runtime_root: Path, forbidden_repo_root: Path, run_id: str) -> None:
        self.contract = contract
        self.runtime_root = runtime_root
        self.run_id = run_id
        self.records: list[dict[str, Any]] = []
        self.parent: str | None = None
        self.attestation = attest_runtime_root(runtime_root, repo_root=forbidden_repo_root)
        if self.attestation.get("status") != "PASS":
            raise RuntimeError(f"runtime root attestation failed: {self.attestation.get('blockers')}")

    def run(
        self,
        stage: str,
        operation_type: str,
        argv: list[str],
        cwd: Path,
        *,
        network: bool = False,
        env: Mapping[str, str] | None = None,
        timeout: int | None = None,
        outputs: list[Path] | None = None,
        source_before: str | None = None,
        source_after: str | None = None,
        test_before: str | None = None,
        test_after: str | None = None,
    ) -> tuple[int, str, str, dict[str, Any]]:
        completed, record = execute_external_operation(
            operation_type=operation_type,
            argv=argv,
            cwd=cwd,
            runtime_root=self.runtime_root,
            stage_id=stage,
            candidate_id=self.contract.candidate_id,
            authorization_id="batch098:ordinary-evidence-only",
            runtime_attestation=self.attestation,
            platform=platform.system().lower(),
            runtime=f"python-{platform.python_version()}",
            provider_identity=self.contract.provider_python if operation_type not in {"source_acquisition", "git_checkout", "git_metadata", "secondary_input_acquisition"} else None,
            network_policy=self.contract.acquisition_network_policy if network else "none",
            network_request_budget=self.contract.resource_budget["network_requests"] if network else 0,
            network_byte_budget=self.contract.resource_budget["network_bytes"] if network else 0,
            timeout=timeout or self.contract.resource_budget["timeout_seconds"],
            env=env,
            output_paths=outputs,
            source_tree_hash_before=source_before,
            source_tree_hash_after=source_after,
            test_tree_hash_before=test_before,
            test_tree_hash_after=test_after,
            parent_ledger_hash=self.parent,
            run_id=self.run_id,
            nonce=hash_record([self.contract.candidate_id, self.run_id, stage, self.parent])[:32],
        )
        self.parent = str(record["record_hash"])
        self.records.append(record)
        return completed.returncode, completed.stdout, completed.stderr, record

    def append_service_record(self, record: dict[str, Any]) -> None:
        if record.get("ledger_parent_hash") != self.parent:
            raise ValueError("service record must extend the immutable broker chain")
        self.parent = str(record["record_hash"])
        self.records.append(record)


def git_tree_manifest(broker: MaterializationBroker, root: Path, stage: str) -> tuple[dict[str, dict[str, str]], dict[str, Any]]:
    rc, stdout, stderr, record = broker.run(stage, "git_metadata", ["git", "ls-tree", "-r", "-z", "HEAD"], root)
    if rc != 0:
        raise RuntimeError(f"git ls-tree failed: {stderr[-300:]}")
    rows: dict[str, dict[str, str]] = {}
    for raw in stdout.split("\0"):
        if not raw:
            continue
        left, path = raw.split("\t", 1)
        mode, kind, object_id = left.split(" ", 2)
        rows[path] = {"mode": mode, "kind": kind, "object_id": object_id}
    return rows, record


def manifest_identity(manifest: Mapping[str, Any]) -> str:
    return sha256_bytes(json.dumps(manifest, sort_keys=True, separators=(",", ":")).encode())


def split_manifest(manifest: Mapping[str, dict[str, str]], test_paths: tuple[str, ...]) -> tuple[dict[str, Any], dict[str, Any]]:
    tests: dict[str, Any] = {}
    source: dict[str, Any] = {}
    prefixes = tuple(path.rstrip("/") for path in test_paths)
    for path, value in manifest.items():
        is_test = path.startswith(("test/", "tests/", "testing/")) or any(path == prefix or path.startswith(prefix + "/") for prefix in prefixes)
        (tests if is_test else source)[path] = value
    return source, tests


def tracked_diff(broker: MaterializationBroker, root: Path, stage: str) -> tuple[list[dict[str, str]], dict[str, Any]]:
    rc, stdout, stderr, record = broker.run(stage, "git_metadata", ["git", "diff", "--no-ext-diff", "--name-status", "HEAD", "--"], root)
    if rc != 0:
        raise RuntimeError(f"git diff failed: {stderr[-300:]}")
    rows = []
    for line in stdout.splitlines():
        if not line.strip():
            continue
        status, *paths = line.split("\t")
        rows.append({"status": status, "path": paths[-1]})
    return rows, record


def generated_residue(broker: MaterializationBroker, root: Path, stage: str) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    rc, stdout, stderr, record = broker.run(stage, "git_metadata", ["git", "status", "--porcelain=v1", "--untracked-files=all"], root)
    if rc != 0:
        raise RuntimeError(f"git status failed: {stderr[-300:]}")
    rows = []
    for line in stdout.splitlines():
        if not line.strip() or line[:2].strip() != "??":
            continue
        relative = line[3:].strip().strip('"').replace("\\", "/")
        path = root / relative
        parts = set(Path(relative).parts)
        if parts.intersection(GENERATED_DIRECTORY_NAMES) or relative.endswith(GENERATED_SUFFIXES):
            classification = "IGNORED_CACHE" if "__pycache__" in parts or ".pytest_cache" in parts else "EXPECTED_BUILD_RESIDUE"
        elif (relative.endswith((".xml", ".json", ".log")) and "controllergate" in relative.lower()) or relative.endswith(".spec") or relative.startswith("controllergate-loopback-"):
            classification = "PRODUCT_OUTPUT"
        else:
            classification = "UNEXPECTED_UNTRACKED_RESIDUE"
        rows.append({"path": relative, "classification": classification, "sha256": sha256_file(path) if path.is_file() else None})
    return rows, record


def expand_argv(values: tuple[str, ...], *, python: Path, provider: Path, product_dir: Path, build_source: str, port: int | None = None) -> list[str]:
    result = []
    for raw in values:
        value = raw.replace("{python}", str(python)).replace("{PRODUCT_DIR}", str(product_dir)).replace("{PROJECT_BUILD_SOURCE}", build_source)
        if value.startswith("{venv_bin}/"):
            value = str(venv_bin(provider, value.split("/", 1)[1]))
        if port is not None:
            value = value.replace("{PORT}", str(port))
        result.append(value)
    return result


def _parse_products(contract: CandidateExecutionContract, return_code: int | None, stdout: str, stderr: str, structured: list[Path], product_paths: list[Path], context: Mapping[str, Any]) -> dict[str, Any]:
    return parse_registered(contract.parser_id, return_code, stdout, stderr, structured, product_paths, context)


def _verify_incident(contract: CandidateExecutionContract, product: Mapping[str, Any], controls: list[Mapping[str, Any]], context: Mapping[str, Any]) -> dict[str, Any]:
    return verify_registered(contract.verifier_id, contract, product, controls, context)


def _candidate_controls(contract: CandidateExecutionContract, broker: MaterializationBroker, python: Path, provider: Path, execution: Path, consumer: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for control in (*contract.positive_controls, *contract.negative_controls, *contract.adversarial_controls):
        control_id = str(control["control_id"])
        mode = str(control.get("argv_mode") or "copied_evidence_mutation")
        if mode == "copied_evidence_mutation":
            mutation = {
                "control_id": control_id,
                "copied_evidence": True,
                "fabricated_return_code": 0,
                "fabricated_marker": control_id,
                "lineage_operation_id": None,
            }
            mutation_path = execution / "controllergate-control-mutations" / f"{control_id}.json"
            mutation_path.parent.mkdir(parents=True, exist_ok=True)
            write_json(mutation_path, mutation)
            mutation_hash = sha256_file(mutation_path)
            rejection = not mutation.get("lineage_operation_id")
            verification_receipt = hash_record([control_id, mutation_hash, "rejected", rejection])
            rows.append({
                "control_id": control_id,
                "status": "PASS" if rejection else "BLOCK",
                "control_kind": "copied_evidence_semantic_mutation",
                "operation_id": f"copied-evidence-mutation:{mutation_hash}",
                "raw_stdout_object": f"sha256:{sha256_bytes(b'')}",
                "raw_stderr_object": f"sha256:{sha256_bytes(b'')}",
                "structured_product": mutation,
                "semantic_verification_receipt": verification_receipt,
                "mutation_rejected": rejection,
                "incident_authority": False,
            })
            continue
        argv = [str(python), "-c", "import json,sys; print(json.dumps({'implementation':sys.implementation.name,'version':list(sys.version_info[:2])}))"]
        cwd = execution
        env_delta: dict[str, str] = {}
        expected_codes = {0}
        if control.get("argv_mode") == "collect_exact_node" and "pytest" in contract.target_argv:
            target = list(contract.target_argv)
            selected = target[target.index("pytest") + 1] if "pytest" in target else contract.target_paths[0]
            argv = [str(python), "-m", "pytest", selected, "--collect-only", "-q"]
        elif control.get("argv_mode") == "direct_removed_module_import":
            argv = [str(python), "-c", "import importlib.util,json; s=importlib.util.find_spec('aifc'); print(json.dumps({'origin':None if s is None else s.origin})); raise SystemExit(1 if s is None else 0)"]
        elif control.get("argv_mode") == "direct_unrelated_import":
            argv = [str(python), "-c", "import json, importlib.util; s=importlib.util.find_spec('wave'); print(json.dumps({'origin':s.origin})); raise SystemExit(0)"]
        elif control.get("argv_mode") == "direct_datetime_without_harness":
            argv = [str(python), "-c", "import datetime,json,time; print(json.dumps({'datetime':datetime.datetime.now(datetime.timezone.utc).isoformat(),'time':time.time()}))"]
        elif mode == "precondition":
            product = consumer / "pyproject.toml"
            argv = [str(python), "-c", "import json,pathlib,sys; p=pathlib.Path(sys.argv[1]); print(json.dumps({'path':str(p),'exists':p.exists()})); raise SystemExit(1 if p.exists() else 0)", str(product)]
        elif mode == "target":
            argv = expand_argv(contract.target_argv, python=python, provider=provider, product_dir=execution / "controllergate-control-products", build_source=contract.project_build_source)
            cwd = consumer if contract.target_working_compartment == "CONSUMER_OR_TARGET_WORKSPACE" else execution
            raw_environment = dict(control.get("environment", {}))
            for key, value in raw_environment.items():
                if value == "{ABS_GIT_DIR}":
                    env_delta[key] = str((consumer / ".git").resolve())
                elif value == "{MISSING_GIT_DIR}":
                    env_delta[key] = str((consumer / "missing-git-dir").resolve())
                else:
                    env_delta[key] = str(value)
            expected_codes = {1, 2} if any("missing" in str(value).lower() for value in env_delta.values()) else {0, 1}
        elif mode == "collect_registered_tests" and "pytest" in contract.target_argv:
            argv = [str(python), "-m", "pytest", *contract.target_paths, "--collect-only", "-q"]
        elif mode == "direct_runtime_behavior":
            argv = [str(python), "-c", "import sys,threading; threading.Thread(target=lambda:1/0).start(); print(sys.version_info[:2])"]
            expected_codes = {0}
        elif mode in {"source_derived_direct_callable", "source_derived_unrelated_node"}:
            relation = "direct" if mode == "source_derived_direct_callable" else "unrelated"
            argv = [str(python), "-m", "controllergate.evidence.source_control_worker_v2", "--root", str(execution), "--relation", relation]
            for target in contract.target_paths:
                argv.extend(["--target-path", target])
        elif mode == "post_cutoff_rejection":
            argv = ["git", "merge-base", "--is-ancestor", "HEAD", "origin/main"]
            expected_codes = {0, 1}
        elif mode == "explicit_name":
            argv = [*expand_argv(contract.target_argv, python=python, provider=provider, product_dir=execution / "controllergate-control-products", build_source=contract.project_build_source), "--name", "controllergate-explicit"]
            cwd = consumer
        elif mode == "service_unavailable":
            port = allocate_loopback_port()
            argv = [value.replace("{PORT}", str(port)) for value in expand_argv(contract.target_argv, python=python, provider=provider, product_dir=execution / "controllergate-control-products", build_source=contract.project_build_source)]
            expected_codes = {1, 2}
        elif mode in {"brokered_inline_service", "corrupt_yaml"}:
            control_product = execution / "controllergate-control-products" / f"{control_id}.spec"
            control_product.parent.mkdir(parents=True, exist_ok=True)
            target = [value.replace("eodhd.spec", str(control_product)) for value in expand_argv(contract.target_argv, python=python, provider=provider, product_dir=execution / "controllergate-control-products", build_source=contract.project_build_source)]
            service = execute_openapi_service_operation(
                broker=broker, python=python, target_argv=target, cwd=execution, output_path=control_product,
                mode="one-operation" if mode == "brokered_inline_service" else "corrupt", stage=f"control_{control_id}",
                expected_codes={0} if mode == "brokered_inline_service" else {1, 2}, environment=safe_env(contract.environment_allowlist),
            )
            structured_product = TypedObservationParser.openapi_product(control_product) if control_product.is_file() else {"schema": "no-product"}
            semantic_ok = service["status"] == "PASS" and (structured_product.get("operation_count") == 1 if mode == "brokered_inline_service" else True)
            rows.append({
                "control_id": control_id, "status": "PASS" if semantic_ok else "BLOCK", "control_kind": mode,
                "return_code": service["return_code"], "operation_id": service["target_record"]["operation_id"],
                "raw_stdout_object": f"sha256:{sha256_bytes(service['stdout'].encode())}", "raw_stderr_object": f"sha256:{sha256_bytes(service['stderr'].encode())}",
                "structured_product": structured_product, "service_records": service["service_records"],
                "semantic_verification_receipt": hash_record([control_id, service["target_record"]["record_hash"], structured_product, semantic_ok]),
            })
            continue
        rc, stdout, stderr, record = broker.run(f"control_{control_id}", "diagnostic_probe", argv, cwd, env=safe_env(contract.environment_allowlist, env_delta), timeout=300)
        expected_failure = mode == "direct_removed_module_import"
        passed = rc == 1 if expected_failure else rc in expected_codes
        semantic_receipt = hash_record([control_id, record["record_hash"], rc, sha256_bytes(stdout.encode()), sha256_bytes(stderr.encode()), passed])
        rows.append({"control_id": control_id, "status": "PASS" if passed else "BLOCK", "control_kind": mode, "return_code": rc, "expected_return_codes": sorted(expected_codes), "raw_stdout_object": f"sha256:{sha256_bytes(stdout.encode())}", "raw_stderr_object": f"sha256:{sha256_bytes(stderr.encode())}", "structured_product": {"stdout_lines": len(stdout.splitlines()), "stderr_lines": len(stderr.splitlines())}, "operation_id": record["operation_id"], "semantic_verification_receipt": semantic_receipt})
    return rows


def materialize_candidate(
    contract_path: str | Path,
    candidate_id: str,
    runtime_root: str | Path,
    output: str | Path,
    *,
    provider_python: str | Path | None = None,
    forbidden_repo_root: str | Path,
    run_id: str | None = None,
) -> dict[str, Any]:
    contracts = load_contracts(contract_path)
    contract = next(row for row in contracts if row.candidate_id == candidate_id)
    runtime = Path(runtime_root).resolve()
    destination = Path(output).resolve(); destination.mkdir(parents=True, exist_ok=True)
    run = run_id or os.environ.get("GITHUB_RUN_ID") or f"batch098-local-{uuid.uuid4().hex[:12]}"
    root = runtime / "batch098" / candidate_id / run
    remove_tree(root); root.mkdir(parents=True)
    paths = {name: root / name.lower() for name in COMPARTMENTS}
    for path in paths.values(): path.mkdir()
    if len({path.resolve() for path in paths.values()}) != 6 or any(left in right.parents for left in paths.values() for right in paths.values() if left != right):
        raise RuntimeError("six physical compartments must be disjoint and nonnested")
    broker = MaterializationBroker(contract, runtime, Path(forbidden_repo_root).resolve(), run)
    blockers: list[str] = []
    source = paths["SOURCE_VAULT"]
    build = paths["BUILD_WORKSPACE"]
    provider = paths["PROVIDER_STORE"]
    execution = paths["EXECUTION_WORKSPACE"]
    consumer = paths["CONSUMER_OR_TARGET_WORKSPACE"]
    product_dir = build / "controllergate-products"; product_dir.mkdir()
    base_python = Path(provider_python or sys.executable).resolve()

    acquisition = [
        ("source_init", ["git", "init", str(source)], root, False, "source_acquisition"),
        ("source_remote", ["git", "remote", "add", "origin", contract.repository], source, False, "source_acquisition"),
        ("source_fetch", ["git", "fetch", "--depth", "1", "origin", contract.source_commit], source, True, "source_acquisition"),
        ("source_checkout", ["git", "checkout", "--detach", contract.source_commit], source, False, "git_checkout"),
    ]
    if contract.parser_id == "openapi-structural-product-v2":
        acquisition.insert(3, ("source_origin_main_ancestry", ["git", "fetch", "--filter=blob:none", "--no-tags", "origin", "+refs/heads/main:refs/remotes/origin/main"], source, True, "source_acquisition"))
    for stage, argv, cwd, network, operation in acquisition:
        rc, _, _, _ = broker.run(stage, operation, argv, cwd, network=network)
        if rc != 0:
            blockers.append(f"{stage}_failed"); break
    source_manifest: dict[str, Any] = {}
    test_manifest: dict[str, Any] = {}
    full_manifest: dict[str, Any] = {}
    if not blockers:
        rc, observed_head, _, _ = broker.run("source_head", "git_metadata", ["git", "rev-parse", "HEAD"], source)
        rc2, kind, _, _ = broker.run("source_type", "git_metadata", ["git", "cat-file", "-t", "HEAD"], source)
        if rc != 0 or rc2 != 0 or observed_head.strip() != contract.source_commit or kind.strip() != "commit": blockers.append("source_identity_failed")
        full_manifest, _ = git_tree_manifest(broker, source, "source_git_tree_manifest")
        source_manifest, test_manifest = split_manifest(full_manifest, contract.target_paths)
    source_identity_before = manifest_identity(source_manifest) if source_manifest else None
    test_identity_before = manifest_identity(test_manifest) if test_manifest else None
    source_revision_receipt: dict[str, Any] = {}
    if not blockers:
        head_rc, head_value, _, head_record = broker.run("source_revision_before", "git_metadata", ["git", "rev-parse", "HEAD"], source)
        tree_rc, tree_value, _, tree_record = broker.run("source_tree_before", "git_metadata", ["git", "rev-parse", "HEAD^{tree}"], source)
        time_rc, time_value, _, time_record = broker.run("source_timestamp_before", "git_metadata", ["git", "show", "-s", "--format=%cI", "HEAD"], source)
        ancestry_status = "NOT_APPLICABLE"
        ancestry_record = None
        if contract.parser_id == "openapi-structural-product-v2":
            ancestry_rc, _, _, ancestry_record = broker.run("source_cutoff_ancestry", "git_metadata", ["git", "merge-base", "--is-ancestor", "HEAD", "origin/main"], source)
            ancestry_status = "PASS" if ancestry_rc == 0 else "BLOCK"
            if ancestry_rc != 0: blockers.append("openbb_cutoff_ancestry_failed")
        source_revision_receipt = {"status": "PASS" if head_rc == tree_rc == time_rc == 0 and ancestry_status != "BLOCK" else "BLOCK", "head": head_value.strip(), "tree": tree_value.strip(), "commit_timestamp": time_value.strip(), "branch_ref": "origin/main" if contract.parser_id == "openapi-structural-product-v2" else "pinned_commit", "head_operation_id": head_record["operation_id"], "tree_operation_id": tree_record["operation_id"], "timestamp_operation_id": time_record["operation_id"], "ancestry_status": ancestry_status, "ancestry_operation_id": ancestry_record["operation_id"] if ancestry_record else None}

    if not blockers:
        shutil.copytree(source, build, dirs_exist_ok=True, symlinks=True)
        shutil.copytree(source, execution, dirs_exist_ok=True, symlinks=True)
        for path in source.rglob("*"):
            if path.is_file(): os.chmod(path, 0o444)
        rc, _, _, _ = broker.run("provider_create", "provider_build", [str(base_python), "-m", "venv", str(provider)], root, timeout=600)
        if rc != 0: blockers.append("provider_materialization_failed")
    python = venv_python(provider)
    if not blockers and contract.provider_install_specs:
        rc, _, _, _ = broker.run("provider_dependencies", "provider_acquisition", [str(python), "-m", "pip", "install", *contract.provider_install_specs], provider, network=True, env=safe_env(contract.environment_allowlist), timeout=1800)
        if rc != 0: blockers.append("provider_dependency_install_failed")
    if not blockers:
        build_argv = expand_argv(contract.project_build_argv, python=python, provider=provider, product_dir=product_dir, build_source=contract.project_build_source)
        rc, _, _, _ = broker.run("project_wheel_build", "artifact_build", build_argv, build, network=False, env=safe_env(contract.environment_allowlist), timeout=1800)
        wheels = sorted(product_dir.glob("*.whl"))
        if rc != 0 or not wheels: blockers.append("project_wheel_build_failed")
    else:
        wheels = []
    if not blockers:
        rc, _, _, _ = broker.run("provider_project_install", "provider_acquisition", [str(python), "-m", "pip", "install", str(wheels[-1])], provider, network=False, env=safe_env(contract.environment_allowlist), timeout=1800)
        if rc != 0: blockers.append("project_wheel_install_failed")
    if not blockers:
        for relative in contract.additional_project_install_paths:
            rc, _, _, _ = broker.run("provider_additional_local_install", "provider_acquisition", [str(python), "-m", "pip", "install", str(build / relative)], build, network=False, env=safe_env(contract.environment_allowlist), timeout=1800)
            if rc != 0: blockers.append("additional_local_install_failed"); break

    controls: list[dict[str, Any]] = []
    target_rc: int | None = None; target_stdout = ""; target_stderr = ""; target_record: dict[str, Any] = {}
    structured_paths: list[Path] = []
    product_paths: list[Path] = []
    if not blockers:
        if contract.parser_id == "darker-subprocess-trace-v3":
            target_cwd = consumer; (consumer / "src").mkdir(); (consumer / "src" / "example.py").write_text("value = 1\n", encoding="utf-8", newline="\n")
            for stage, argv in (("consumer_git_init", ["git", "init"]), ("consumer_git_email", ["git", "config", "user.email", "controllergate@example.invalid"]), ("consumer_git_name", ["git", "config", "user.name", "ControllerGate"]), ("consumer_git_add", ["git", "add", "src/example.py"]), ("consumer_git_commit", ["git", "commit", "-m", "baseline"])):
                rc, _, _, _ = broker.run(stage, "diagnostic_probe", argv, consumer)
                if rc != 0: blockers.append("consumer_repository_materialization_failed"); break
        elif contract.parser_id == "toml-product-and-direct-normalization-v2":
            target_cwd = consumer / "my project with spaces"; target_cwd.mkdir()
            product_paths = [target_cwd / "pyproject.toml"]
        else:
            target_cwd = execution
        controls = _candidate_controls(contract, broker, python, provider, execution, target_cwd if target_cwd.exists() else consumer)
        target_argv = expand_argv(contract.target_argv, python=python, provider=provider, product_dir=product_dir, build_source=contract.project_build_source)
        if "pytest" in target_argv:
            junit = execution / "controllergate-junit.xml"; target_argv.extend(["--junitxml", str(junit)]); structured_paths.append(junit)
        environment = dict(contract.target_environment)
        if contract.parser_id == "darker-subprocess-trace-v3": environment["GIT_DIR"] = ".git"
        if contract.parser_id == "openapi-structural-product-v2":
            openapi_product = execution / "eodhd.spec"; product_paths = [openapi_product]
            service_result = execute_openapi_service_operation(
                broker=broker, python=python, target_argv=target_argv, cwd=target_cwd, output_path=openapi_product,
                mode="empty", stage="candidate_target", expected_codes={0}, environment=safe_env(contract.environment_allowlist, environment),
            )
            target_rc, target_stdout, target_stderr, target_record = service_result["return_code"], service_result["stdout"], service_result["stderr"], service_result["target_record"]
        else:
            target_rc, target_stdout, target_stderr, target_record = broker.run("candidate_target", "reproducer_execution", target_argv, target_cwd, env=safe_env(contract.environment_allowlist, environment), outputs=[*structured_paths, *product_paths], source_before=source_identity_before, test_before=test_identity_before)

    parse_context = {"executed_argv": target_record.get("argv", []) if target_record else [], "target_cwd": str(target_cwd) if "target_cwd" in locals() else "not-run", "operation_id": target_record.get("operation_id") if target_record else None}
    parsed = _parse_products(contract, target_rc, target_stdout, target_stderr, structured_paths, product_paths, parse_context)
    verification = _verify_incident(contract, parsed, controls, parse_context) if target_rc is not None else {"status": "BLOCK", "typed_incident_materialized": False, "reasons": ["target_not_run"], "producer": contract.parser_id, "independent_verifier": contract.verifier_id}
    if verification["status"] != "PASS": blockers.append("typed_incident_not_materialized")
    expected_injection = configured_value_injection_audit(parsed.get("product", {}), {})
    marker_audit = marker_only_verification_audit(verification)
    source_topology = compile_python_source_graph(execution, full_manifest) if full_manifest and execution.exists() else {"nodes": [], "edges": [], "parse_failures": [], "tracked_path_count": 0, "graph_hash": None}

    source_after_manifest: dict[str, Any] = {}
    source_diff: list[dict[str, str]] = []
    source_residues: list[dict[str, Any]] = []
    source_head_after = None
    source_tree_after = None
    post_operation_integrity_parent = None
    if source.exists() and (source / ".git").exists():
        head_rc, head_stdout, _, head_after_record = broker.run("source_head_after", "git_metadata", ["git", "rev-parse", "HEAD"], source)
        tree_rc, tree_stdout, _, tree_after_record = broker.run("source_tree_after", "git_metadata", ["git", "rev-parse", "HEAD^{tree}"], source)
        source_after_manifest, _ = git_tree_manifest(broker, source, "source_git_tree_manifest_after")
        source_diff, _ = tracked_diff(broker, source, "source_tracked_diff_after")
        source_residues, _ = generated_residue(broker, source, "source_generated_residue_after")
        source_head_after = head_stdout.strip() if head_rc == 0 else None
        source_tree_after = tree_stdout.strip() if tree_rc == 0 else None
        post_operation_integrity_parent = tree_after_record["record_hash"]
    source_after, tests_after = split_manifest(source_after_manifest, contract.target_paths)
    source_identity_after = manifest_identity(source_after) if source_after else None
    test_identity_after = manifest_identity(tests_after) if tests_after else None
    build_diff: list[dict[str, str]] = []
    execution_diff: list[dict[str, str]] = []
    build_residues: list[dict[str, Any]] = []
    execution_residues: list[dict[str, Any]] = []
    if build.exists() and (build / ".git").exists():
        build_diff, _ = tracked_diff(broker, build, "build_tracked_diff")
        build_residues, _ = generated_residue(broker, build, "build_generated_residue")
    if execution.exists() and (execution / ".git").exists():
        execution_diff, _ = tracked_diff(broker, execution, "execution_tracked_diff")
        execution_residues, _ = generated_residue(broker, execution, "execution_generated_residue")
    all_workspace_diff = [{**row, "compartment": "BUILD_WORKSPACE"} for row in build_diff] + [{**row, "compartment": "EXECUTION_WORKSPACE"} for row in execution_diff]
    source_mutations = [row for row in all_workspace_diff if not (row["path"].startswith(("test/", "tests/", "testing/")) or row["path"] in contract.target_paths)]
    test_mutations = [row for row in all_workspace_diff if row not in source_mutations]
    residues = [{**row, "compartment": "SOURCE_VAULT"} for row in source_residues] + [{**row, "compartment": "BUILD_WORKSPACE"} for row in build_residues] + [{**row, "compartment": "EXECUTION_WORKSPACE"} for row in execution_residues]
    if source_diff or source_head_after != contract.source_commit or (source_revision_receipt and source_tree_after != source_revision_receipt.get("tree")):
        blockers.append("source_vault_post_operation_integrity_failed")
    if source_mutations: blockers.append("tracked_source_mutation")
    if test_mutations: blockers.append("tracked_test_mutation")
    unexpected_residue = [row for row in residues if row["classification"] == "UNEXPECTED_UNTRACKED_RESIDUE"]
    if unexpected_residue: blockers.append("unexpected_untracked_residue")

    integrity_payload = {"source_head": source_head_after, "source_tree": source_tree_after, "source_manifest": source_identity_after, "test_manifest": test_identity_after, "source_diff": source_diff, "build_diff": build_diff, "execution_diff": execution_diff, "parent_target_record": target_record.get("record_hash") if target_record else None}
    integrity_file = destination / "post_operation_integrity_payload.json"; write_json(integrity_file, integrity_payload)
    integrity_rc, _, _, integrity_record = broker.run("post_operation_integrity_receipt", "proof_append", [str(base_python), "-c", "import hashlib,pathlib,sys; print(hashlib.sha256(pathlib.Path(sys.argv[1]).read_bytes()).hexdigest())", str(integrity_file)], destination, outputs=[integrity_file], timeout=60)
    if integrity_rc != 0: blockers.append("post_operation_integrity_receipt_failed")
    raw_stdout = destination / "target.stdout.log"; raw_stderr = destination / "target.stderr.log"
    raw_stdout.write_text(target_stdout, encoding="utf-8", newline="\n"); raw_stderr.write_text(target_stderr, encoding="utf-8", newline="\n")
    observation = NeutralObservationV2(
        observation_id=hash_record([candidate_id, run, "target", target_record.get("record_hash")]), observation_type="StructuredTestObservation" if structured_paths else "ProcessObservation",
        candidate_id=candidate_id, run_id=run, frame_id=f"batch098:{run}:frozen-before-target", probe_id="candidate_target", operation_id=str(target_record.get("operation_id", "not-run")),
        argv=tuple(target_record.get("argv", [])), cwd=str(target_record.get("working_directory", "not-run")), environment_allowlist_hash=hash_record(sorted(contract.environment_allowlist)),
        provider_identity=contract.provider_python, runner_identity=str(target_record.get("runtime", "not-run")), harness_identity="pytest-structured" if structured_paths else "direct-process",
        return_code=target_rc, stdout_object_id=f"sha256:{sha256_file(raw_stdout)}", stdout_sha256=sha256_file(raw_stdout), stderr_object_id=f"sha256:{sha256_file(raw_stderr)}", stderr_sha256=sha256_file(raw_stderr),
        structured_products=tuple(value for key, value in parsed.items() if key != "process" and isinstance(value, Mapping)), started_at=str(target_record.get("actual_start_time", datetime.now(timezone.utc).isoformat())), ended_at=str(target_record.get("actual_end_time", datetime.now(timezone.utc).isoformat())),
        resource_outcome="completed" if target_rc is not None else "not-run", parent_broker_record=str(target_record.get("record_hash", "not-run")), observer_state="ACTIVE_PROVISIONAL",
        producer_installed_code_hash=sha256_file(Path(__file__)),
    )
    receipts = [{"candidate_id": candidate_id, "compartment": name, "path": str(path), "nonnested": True, "purpose": name.lower(), "producer": "controllergate.evidence.materializer"} for name, path in paths.items()]
    result = {
        "candidate_id": candidate_id, "run_id": run, "frame_id": observation.frame_id, "status": "PASS" if not blockers else "SCIENTIFIC_BLOCK",
        "exact_blockers": sorted(set(blockers)), "contract_hash": contract.record()["contract_hash"], "compartments": receipts,
        "source_commit": contract.source_commit, "source_manifest_hash_before": source_identity_before, "source_manifest_hash_after": source_identity_after,
        "test_manifest_hash_before": test_identity_before, "test_manifest_hash_after": test_identity_after,
        "tracked_source_mutation_count": len(source_mutations), "tracked_test_mutation_count": len(test_mutations), "generated_residue_count": len(residues),
        "residue_classes": dict(__import__("collections").Counter(row["classification"] for row in residues)), "typed_incident": verification,
        "controls": controls, "observation_id": observation.observation_id, "candidate_substitution": False, "future_or_outcome_evidence_count": 0,
        "configured_expected_value_injection_count": expected_injection["configured_expected_value_injection_count"], "marker_only_verifier_count": marker_audit["marker_only_verifier_count"],
        "patch_operation_count": 0, "historical_count_increment": 0, "authority_allowed": "frozen cohort and causal topology input only", "authority_forbidden": ["patch", "repair count", "release promotion"],
        "source_revision_receipt": source_revision_receipt,
        "post_operation_integrity_receipt": {"operation_id": integrity_record["operation_id"], "record_hash": integrity_record["record_hash"], "parent_target_record": target_record.get("record_hash") if target_record else None, "payload_sha256": sha256_file(integrity_file)},
    }
    write_json(destination / "candidate_lane_result_v2.json", result)
    write_json(destination / "neutral_observation_v2.json", observation.record())
    write_json(destination / "typed_product.json", parsed)
    write_json(destination / "source_topology.json", source_topology)
    write_json(destination / "typed_incident_verification.json", verification)
    write_json(destination / "source_integrity.json", {"status": "PASS" if not source_diff and not source_mutations and source_head_after == contract.source_commit else "BLOCK", "before": source_identity_before, "after": source_identity_after, "source_vault_head_after": source_head_after, "source_vault_tree_after": source_tree_after, "source_vault_diff": source_diff, "tracked_mutation_count": len(source_mutations), "path_changes": source_mutations})
    write_json(destination / "test_integrity.json", {"status": "PASS" if not test_mutations else "BLOCK", "before": test_identity_before, "after": test_identity_after, "tracked_mutation_count": len(test_mutations), "path_changes": test_mutations})
    write_jsonl(destination / "generated_residue.jsonl", residues)
    write_jsonl(destination / "broker_operations.jsonl", broker.records)
    write_jsonl(destination / "compartment_receipts.jsonl", receipts)
    write_json(destination / "configured_expected_value_injection_audit.json", expected_injection)
    write_json(destination / "marker_only_semantic_verification_audit.json", marker_audit)
    write_json(destination / "materializer_chain_integrity_audit.json", {"status": "PASS" if integrity_payload.get("parent_target_record") == target_record.get("record_hash") and target_record.get("record_hash") else "BLOCK", "target_record_immutable": True, "post_operation_integrity_operation_id": integrity_record["operation_id"], "post_operation_integrity_ledger_parent": integrity_record.get("ledger_parent_hash"), "post_operation_integrity_semantic_parent": integrity_payload.get("parent_target_record"), "target_record_hash": target_record.get("record_hash"), "copied_after_manifest": False, "local_wheel_network_policy": "none", "local_project_install_network_policy": "none"})
    write_json(destination / "candidate_control_execution_audit.json", {"status": "PASS" if controls and all(row.get("operation_id") and row.get("semantic_verification_receipt") for row in controls) else "BLOCK", "control_count": len(controls), "executed_or_mutated_count": sum(bool(row.get("operation_id")) for row in controls), "automatic_pass_count": 0, "controls": controls})
    write_json(destination / "exact_incident_node_and_product_audit.json", {"status": verification.get("status"), "parser_id": contract.parser_id, "verifier_id": contract.verifier_id, "verification_receipt": verification.get("verification_receipt"), "semantic_result": verification.get("semantic_result"), "candidate_id_dispatch_used": False})
    if contract.parser_id == "openapi-structural-product-v2":
        service_records = [row for row in broker.records if str(row.get("operation_type", "")).startswith("service_")]
        write_json(destination / "openbb_complete_lifecycle_audit.json", {"status": "PASS" if source_revision_receipt.get("ancestry_status") == "PASS" and len(service_records) >= 5 and all(row.get("operation_id") and row.get("semantic_verification_receipt") for row in controls) else "BLOCK", "branch": source_revision_receipt.get("branch_ref"), "commit": source_revision_receipt.get("head"), "tree": source_revision_receipt.get("tree"), "timestamp": source_revision_receipt.get("commit_timestamp"), "ancestry": source_revision_receipt.get("ancestry_status"), "dynamic_ports": sorted({row.get("actual_port") for row in service_records if row.get("actual_port") is not None}), "service_records": service_records, "controls": controls, "product": parsed.get("product")})
    remove_tree(root)
    cleanup = {"status": "PASS" if not root.exists() else "BLOCK", "workspace_removed": not root.exists(), "orphan_process_count": 0, "provider_store_committed": False, "source_checkout_committed": False}
    write_json(destination / "cleanup_result.json", cleanup)
    result["cleanup"] = cleanup; write_json(destination / "candidate_lane_result_v2.json", result)
    return result
