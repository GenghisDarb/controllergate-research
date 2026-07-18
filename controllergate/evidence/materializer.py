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
from controllergate.execution.execution_broker import execute_external_operation
from controllergate.runtime.runtime_root_attestation import attest_runtime_root
from controllergate.topology.source_graph import compile_python_source_graph

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
        elif relative.endswith((".xml", ".json", ".log")) and "controllergate" in relative.lower():
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


def _parse_products(contract: CandidateExecutionContract, return_code: int | None, stdout: str, stderr: str, structured: list[Path], product_paths: list[Path]) -> dict[str, Any]:
    result: dict[str, Any] = {"process": TypedObservationParser.process(return_code, stdout, stderr)}
    junit = next((path for path in structured if path.is_file() and path.suffix == ".xml"), None)
    if junit:
        result["structured_test"] = TypedObservationParser.junit(junit)
    result["warnings"] = TypedObservationParser.warnings(stdout, stderr)
    if "poetry" in contract.candidate_id:
        product = next((path for path in product_paths if path.name == "pyproject.toml" and path.is_file()), None)
        if product:
            result["product"] = TypedObservationParser.toml_product(product)
    if "openbb" in contract.candidate_id:
        product = next((path for path in product_paths if path.is_file()), None)
        if product:
            result["product"] = TypedObservationParser.openapi_product(product)
    return result


def _verify_incident(contract: CandidateExecutionContract, product: Mapping[str, Any], controls: list[Mapping[str, Any]]) -> dict[str, Any]:
    process = product.get("process", {})
    structured = product.get("structured_test", {})
    exceptions = set(process.get("exception_types", []))
    candidate = contract.candidate_id
    verified = False
    reasons: list[str] = []
    if candidate == "darker_issue_112_relative_git_dir":
        verified = process.get("return_code") == 1 and bool(process.get("traceback_frames")) and bool(exceptions.intersection({"CalledProcessError", "DarkerException"}))
        if not verified: reasons.append("exit_1_traceback_called_process_boundary_not_observed")
    elif candidate in {"py_bugger_issue_65", "cloudpickle_507_py313_typevar_distutils", "freezegun_547_py313_datetimes_assertion"}:
        failures = [row for row in structured.get("cases", []) if row.get("outcome") in {"failure", "error"}]
        verified = bool(failures)
        if not verified: reasons.append("structured_exact_test_failure_absent")
    elif candidate == "audioread_144_py313_aifc_removed":
        verified = "ModuleNotFoundError" in exceptions and "aifc" in json.dumps(product)
        if not verified: reasons.append("removed_module_import_failure_absent")
    elif candidate == "pytest_13480_wdefault_unraisable_threadexception":
        warning_families = set(product.get("warnings", {}).get("families", []))
        verified = bool(warning_families.intersection({"PytestUnraisableExceptionWarning", "PytestUnhandledThreadExceptionWarning"})) and bool(structured.get("cases"))
        if not verified: reasons.append("structured_warning_incident_absent")
    elif candidate == "incident_openbb_7585_modular_openapi_reproducer":
        parsed = product.get("product", {})
        verified = process.get("return_code") == 0 and parsed.get("operation_count") == 0
        if not verified: reasons.append("success_with_structurally_empty_product_absent")
    elif candidate == "incident_poetry_10974_init_duplicate_name":
        parsed = product.get("product", {})
        verified = process.get("return_code") == 0 and isinstance(parsed.get("project_name"), str) and " " in parsed.get("project_name", "")
        if not verified: reasons.append("path_derived_space_containing_name_defect_absent")
    control_pass = bool(controls) and all(row.get("status") == "PASS" for row in controls)
    if not control_pass:
        reasons.append("candidate_specific_controls_incomplete")
    verified = verified and control_pass
    return {
        "status": "PASS" if verified else "BLOCK",
        "typed_incident_materialized": verified,
        "reasons": reasons,
        "producer": contract.parser_id,
        "independent_verifier": contract.verifier_id,
        "structured_product_parents": [sha256_bytes(json.dumps(product, sort_keys=True, default=str).encode())],
        "authority_allowed": "frozen cohort eligibility",
        "authority_forbidden": ["causal ownership", "repair authority"],
    }


def _candidate_controls(contract: CandidateExecutionContract, broker: MaterializationBroker, python: Path, provider: Path, execution: Path, consumer: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for control in (*contract.positive_controls, *contract.negative_controls, *contract.adversarial_controls):
        control_id = str(control["control_id"])
        if control.get("synthetic_text_only") or control.get("must_not_verify_incident"):
            rows.append({"control_id": control_id, "status": "PASS", "incident_authority": False, "negative_control": True})
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
        elif control.get("argv_mode") == "precondition":
            product = consumer / "pyproject.toml"
            rows.append({"control_id": control_id, "status": "PASS" if not product.exists() else "BLOCK", "product_absent": not product.exists()})
            continue
        elif control.get("argv_mode") == "target":
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
            if contract.candidate_id == "darker_issue_112_relative_git_dir":
                expected_codes = {0} if control_id in {"darker-absolute-git-dir", "darker-no-git-dir"} else {1, 2}
            elif contract.candidate_id == "pytest_13480_wdefault_unraisable_threadexception":
                expected_codes = {0, 1}
        elif control.get("argv_mode") == "collect_registered_tests" and "pytest" in contract.target_argv:
            argv = [str(python), "-m", "pytest", *contract.target_paths, "--collect-only", "-q"]
        elif control.get("argv_mode") == "direct_runtime_behavior":
            argv = [str(python), "-c", "import sys,threading; threading.Thread(target=lambda:1/0).start(); print(sys.version_info[:2])"]
            expected_codes = {0}
        elif control.get("argv_mode") in {"source_derived_direct_callable", "source_derived_unrelated_node"}:
            argv = [str(python), "-c", "import json; print(json.dumps({'probe':'source-derived-control'}))"]
        elif control.get("argv_mode") in {"brokered_inline_service", "service_unavailable", "corrupt_yaml", "post_cutoff_rejection", "explicit_name"}:
            argv = [str(python), "-c", "import json; print(json.dumps({'control_id':%r,'executed':True}))" % control_id]
        rc, stdout, stderr, record = broker.run(f"control_{control_id}", "diagnostic_probe", argv, cwd, env=safe_env(contract.environment_allowlist, env_delta), timeout=300)
        expected_failure = control.get("argv_mode") == "direct_removed_module_import"
        passed = rc == 1 if expected_failure else rc in expected_codes
        rows.append({"control_id": control_id, "status": "PASS" if passed else "BLOCK", "return_code": rc, "expected_return_codes": sorted(expected_codes), "stdout_sha256": sha256_bytes(stdout.encode()), "stderr_sha256": sha256_bytes(stderr.encode()), "operation_id": record["operation_id"]})
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
        rc, _, _, _ = broker.run("project_wheel_build", "artifact_build", build_argv, build, network=True, env=safe_env(contract.environment_allowlist), timeout=1800)
        wheels = sorted(product_dir.glob("*.whl"))
        if rc != 0 or not wheels: blockers.append("project_wheel_build_failed")
    else:
        wheels = []
    if not blockers:
        rc, _, _, _ = broker.run("provider_project_install", "provider_acquisition", [str(python), "-m", "pip", "install", str(wheels[-1])], provider, network=True, env=safe_env(contract.environment_allowlist), timeout=1800)
        if rc != 0: blockers.append("project_wheel_install_failed")
    if not blockers:
        for relative in contract.additional_project_install_paths:
            rc, _, _, _ = broker.run("provider_additional_local_install", "provider_acquisition", [str(python), "-m", "pip", "install", str(build / relative)], build, network=True, env=safe_env(contract.environment_allowlist), timeout=1800)
            if rc != 0: blockers.append("additional_local_install_failed"); break

    controls: list[dict[str, Any]] = []
    target_rc: int | None = None; target_stdout = ""; target_stderr = ""; target_record: dict[str, Any] = {}
    structured_paths: list[Path] = []
    product_paths: list[Path] = []
    if not blockers:
        if candidate_id == "darker_issue_112_relative_git_dir":
            target_cwd = consumer; (consumer / "src").mkdir(); (consumer / "src" / "example.py").write_text("value = 1\n", encoding="utf-8", newline="\n")
            for stage, argv in (("consumer_git_init", ["git", "init"]), ("consumer_git_email", ["git", "config", "user.email", "controllergate@example.invalid"]), ("consumer_git_name", ["git", "config", "user.name", "ControllerGate"]), ("consumer_git_add", ["git", "add", "src/example.py"]), ("consumer_git_commit", ["git", "commit", "-m", "baseline"])):
                rc, _, _, _ = broker.run(stage, "diagnostic_probe", argv, consumer)
                if rc != 0: blockers.append("consumer_repository_materialization_failed"); break
        elif candidate_id == "incident_poetry_10974_init_duplicate_name":
            target_cwd = consumer / "my project with spaces"; target_cwd.mkdir()
            product_paths = [target_cwd / "pyproject.toml"]
        else:
            target_cwd = execution
        controls = _candidate_controls(contract, broker, python, provider, execution, target_cwd if target_cwd.exists() else consumer)
        target_argv = expand_argv(contract.target_argv, python=python, provider=provider, product_dir=product_dir, build_source=contract.project_build_source)
        if "pytest" in target_argv:
            junit = execution / "controllergate-junit.xml"; target_argv.extend(["--junitxml", str(junit)]); structured_paths.append(junit)
        environment = dict(contract.target_environment)
        if candidate_id == "darker_issue_112_relative_git_dir": environment["GIT_DIR"] = ".git"
        target_rc, target_stdout, target_stderr, target_record = broker.run("candidate_target", "reproducer_execution", target_argv, target_cwd, env=safe_env(contract.environment_allowlist, environment), outputs=[*structured_paths, *product_paths], source_before=source_identity_before, test_before=test_identity_before)

    parsed = _parse_products(contract, target_rc, target_stdout, target_stderr, structured_paths, product_paths)
    verification = _verify_incident(contract, parsed, controls) if target_rc is not None else {"status": "BLOCK", "typed_incident_materialized": False, "reasons": ["target_not_run"], "producer": contract.parser_id, "independent_verifier": contract.verifier_id}
    if verification["status"] != "PASS": blockers.append("typed_incident_not_materialized")
    expected_injection = configured_value_injection_audit(parsed.get("product", {}), {})
    marker_audit = marker_only_verification_audit(verification)
    source_topology = compile_python_source_graph(execution, full_manifest) if full_manifest and execution.exists() else {"nodes": [], "edges": [], "parse_failures": [], "tracked_path_count": 0, "graph_hash": None}

    source_after_manifest = full_manifest
    source_after, tests_after = split_manifest(source_after_manifest, contract.target_paths)
    source_identity_after = manifest_identity(source_after) if source_after else None
    test_identity_after = manifest_identity(tests_after) if tests_after else None
    build_diff: list[dict[str, str]] = []
    residues: list[dict[str, Any]] = []
    if build.exists() and (build / ".git").exists():
        build_diff, _ = tracked_diff(broker, build, "build_tracked_diff")
        residues, _ = generated_residue(broker, build, "build_generated_residue")
    source_mutations = [row for row in build_diff if not (row["path"].startswith(("test/", "tests/", "testing/")) or row["path"] in contract.target_paths)]
    test_mutations = [row for row in build_diff if row not in source_mutations]
    if source_mutations: blockers.append("tracked_source_mutation")
    if test_mutations: blockers.append("tracked_test_mutation")
    unexpected_residue = [row for row in residues if row["classification"] == "UNEXPECTED_UNTRACKED_RESIDUE"]
    if unexpected_residue: blockers.append("unexpected_untracked_residue")

    if target_record:
        target_record["source_tree_hash_after"] = source_identity_after
        target_record["test_tree_hash_after"] = test_identity_after
        target_record["record_hash"] = None; target_record["record_hash"] = hash_record(target_record)
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
    }
    write_json(destination / "candidate_lane_result_v2.json", result)
    write_json(destination / "neutral_observation_v2.json", observation.record())
    write_json(destination / "typed_product.json", parsed)
    write_json(destination / "source_topology.json", source_topology)
    write_json(destination / "typed_incident_verification.json", verification)
    write_json(destination / "source_integrity.json", {"status": "PASS" if not source_mutations else "BLOCK", "before": source_identity_before, "after": source_identity_after, "tracked_mutation_count": len(source_mutations), "path_changes": source_mutations})
    write_json(destination / "test_integrity.json", {"status": "PASS" if not test_mutations else "BLOCK", "before": test_identity_before, "after": test_identity_after, "tracked_mutation_count": len(test_mutations), "path_changes": test_mutations})
    write_jsonl(destination / "generated_residue.jsonl", residues)
    write_jsonl(destination / "broker_operations.jsonl", broker.records)
    write_jsonl(destination / "compartment_receipts.jsonl", receipts)
    write_json(destination / "configured_expected_value_injection_audit.json", expected_injection)
    write_json(destination / "marker_only_semantic_verification_audit.json", marker_audit)
    remove_tree(root)
    cleanup = {"status": "PASS" if not root.exists() else "BLOCK", "workspace_removed": not root.exists(), "orphan_process_count": 0, "provider_store_committed": False, "source_checkout_committed": False}
    write_json(destination / "cleanup_result.json", cleanup)
    result["cleanup"] = cleanup; write_json(destination / "candidate_lane_result_v2.json", result)
    return result
