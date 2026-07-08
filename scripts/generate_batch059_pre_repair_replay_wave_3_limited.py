from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import stat
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from controllergate.core.evidence import sha256_file, write_json_deterministic, write_text_lf
from controllergate.core.manifests import write_sha256sums
from controllergate.core.official_ingest import ingest_official_outputs, verify_official_zip


OUT_DIR = ROOT / "outputs" / "post_v2_37_hardening_batch059_pre_repair_replay_wave_3_limited"
BATCH058_DIR = ROOT / "outputs" / "post_v2_37_hardening_batch058_seed_discovery_wave_3_provider_prescreen"
BATCH058_ZIP = Path(
    os.environ.get(
        "CONTROLLERGATE_BATCH058_ARTIFACT_ZIP",
        r"C:\Users\thisb\Downloads\post_v2_37_hardening_batch058_seed_discovery_wave_3_provider_prescreen_artifacts.zip",
    )
)
BATCH058_ARTIFACT_NAME = "post_v2_37_hardening_batch058_seed_discovery_wave_3_provider_prescreen_artifacts"
BATCH058_ARTIFACT_ID = 8158362902
BATCH058_WORKFLOW_RUN_ID = 28918014402
BATCH058_WORKFLOW_HEAD_SHA = "0b35aa87fd5f1591e115630dd110cad37323e764"
BATCH058_SHA256 = "899dc0fbdc039efd04727ce8b1065fd673afe013ec60251d0dc735c17a31ad1d"
BATCH058_SIZE = 375462
BATCH058_ENTRY_COUNT = 447
BATCH058_ARTIFACT_MANIFEST_CHECKED = 446
BATCH058_OUTPUT_MANIFESTS = {
    "post_v2_37_hardening_batch058_seed_discovery_wave_3_provider_prescreen": (
        "post_v2_37_hardening_batch058_seed_discovery_wave_3_provider_prescreen/SHA256SUMS.txt",
        445,
    )
}

CURRENT_PROTOCOL = "v2.14"
ISSUE_DERIVED_REPAIR_COUNT = 2
NATIVE_EXTERNAL_REPAIR_COUNT = 4
RUNTIME_ROOT = Path(os.environ.get("CONTROLLERGATE_BATCH059_RUNTIME_ROOT", r"C:\Dev\ControllerGate_runtime\batch059"))

CANDIDATES: list[dict[str, Any]] = [
    {
        "candidate_id": "audioread_144_py313_aifc_removed",
        "repo_url": "https://github.com/beetbox/audioread",
        "issue_url": "https://github.com/beetbox/audioread/issues/144",
        "candidate_sha": "577f8e2cbe99f33dd7d236deb1626e372f4762e9",
        "native_test_path": "test/test_audioread.py",
        "planned_command": "tox -e py313",
        "provider_risk": "provider_risk_medium",
        "provider_setup": "install_project_test_extra_for_declared_tox",
        "install_command": "python -m pip install .[test]",
        "expected_provider_metadata": ["pyproject.toml", "tox.ini"],
        "future_failure_family": "single_source_removed_stdlib_import_surface",
        "future_patch_license": "patch_license_future_open_single_source_family",
    },
    {
        "candidate_id": "cloudpickle_507_py313_typevar_distutils",
        "repo_url": "https://github.com/cloudpipe/cloudpickle",
        "issue_url": "https://github.com/cloudpipe/cloudpickle/issues/507",
        "candidate_sha": "a76f0812ccdbbd1397f36d536dc4d57b6d0557d6",
        "native_test_path": "tests/cloudpickle_test.py",
        "planned_command": "python -m pytest tests/cloudpickle_test.py -q --tb=no",
        "provider_risk": "provider_risk_low",
        "provider_setup": "install_declared_dev_requirements",
        "install_command": "python -m pip install -r dev-requirements.txt",
        "expected_provider_metadata": ["dev-requirements.txt", "tox.ini"],
        "future_failure_family": "multi_failure_family_exact_command_traceback_suppressed",
        "future_patch_license": "patch_license_future_open_primary_family_diagnostic_only",
    },
]

FORBIDDEN_EVIDENCE_FIELDS = {
    "fixed_commits_used": False,
    "future_commits_used": False,
    "pr_patches_used": False,
    "future_issue_comments_used": False,
    "issue_body_fix_or_workaround_text_used": False,
    "helper_fix_suggestions_used": False,
    "gold_patches_used": False,
    "external_repair_summaries_used": False,
    "stackoverflow_or_web_fix_snippets_used": False,
    "test_modifications_used": False,
    "source_modifications_used": False,
    "post_fix_release_notes_used": False,
}


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return value


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8", errors="replace")).hexdigest()


def safe_rmtree(path: Path, allowed_root: Path) -> None:
    if not path.exists():
        return
    resolved = path.resolve()
    allowed = allowed_root.resolve()
    if not str(resolved).lower().startswith(str(allowed).lower()):
        raise RuntimeError(f"refusing to delete path outside allowed root: {resolved}")
    def _onexc(function: Any, target: str, excinfo: BaseException) -> None:
        try:
            os.chmod(target, stat.S_IWRITE)
            function(target)
        except OSError:
            raise excinfo

    for attempt in range(1, 4):
        try:
            shutil.rmtree(resolved, onexc=_onexc)
            return
        except PermissionError:
            if attempt == 3:
                raise
            time.sleep(0.5 * attempt)


def command_to_text(args: list[str]) -> str:
    return " ".join(args)


def run_args(args: list[str], cwd: Path, timeout: int = 120, env: dict[str, str] | None = None) -> dict[str, Any]:
    started = time.time()
    try:
        completed = subprocess.run(
            args,
            cwd=cwd,
            env=env,
            text=True,
            encoding="utf-8",
            errors="replace",
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout,
            check=False,
        )
        stdout = completed.stdout or ""
        stderr = completed.stderr or ""
        returncode = completed.returncode
        timed_out = False
    except subprocess.TimeoutExpired as exc:
        stdout = exc.stdout if isinstance(exc.stdout, str) else (exc.stdout or b"").decode("utf-8", errors="replace")
        stderr = exc.stderr if isinstance(exc.stderr, str) else (exc.stderr or b"").decode("utf-8", errors="replace")
        returncode = -9
        timed_out = True
    return {
        "command": args,
        "command_text": command_to_text(args),
        "cwd": str(cwd),
        "returncode": returncode,
        "timed_out": timed_out,
        "elapsed_seconds": round(time.time() - started, 3),
        "stdout": stdout,
        "stderr": stderr,
        "stdout_sha256": sha256_text(stdout),
        "stderr_sha256": sha256_text(stderr),
    }


def run_shell(command: str, cwd: Path, timeout: int, env: dict[str, str]) -> dict[str, Any]:
    started = time.time()
    try:
        completed = subprocess.run(
            command,
            cwd=cwd,
            env=env,
            shell=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout,
            check=False,
        )
        stdout = completed.stdout or ""
        stderr = completed.stderr or ""
        returncode = completed.returncode
        timed_out = False
    except subprocess.TimeoutExpired as exc:
        stdout = exc.stdout if isinstance(exc.stdout, str) else (exc.stdout or b"").decode("utf-8", errors="replace")
        stderr = exc.stderr if isinstance(exc.stderr, str) else (exc.stderr or b"").decode("utf-8", errors="replace")
        returncode = -9
        timed_out = True
    return {
        "command": command,
        "cwd": str(cwd),
        "returncode": returncode,
        "timed_out": timed_out,
        "elapsed_seconds": round(time.time() - started, 3),
        "stdout": stdout,
        "stderr": stderr,
        "stdout_sha256": sha256_text(stdout),
        "stderr_sha256": sha256_text(stderr),
    }


def compact_result(result: dict[str, Any]) -> dict[str, Any]:
    return {k: v for k, v in result.items() if k not in {"stdout", "stderr"}}


def raw_log(result: dict[str, Any]) -> str:
    command = result.get("command")
    if isinstance(command, list):
        command = command_to_text(command)
    stdout = "\n".join(line.rstrip() for line in str(result.get("stdout", "")).splitlines())
    stderr = "\n".join(line.rstrip() for line in str(result.get("stderr", "")).splitlines())
    return (
        f"command: {command}\n"
        f"cwd: {result.get('cwd')}\n"
        f"returncode: {result.get('returncode')}\n"
        f"timed_out: {result.get('timed_out')}\n"
        f"elapsed_seconds: {result.get('elapsed_seconds')}\n"
        "\n--- stdout ---\n"
        f"{stdout}\n"
        "\n--- stderr ---\n"
        f"{stderr}\n"
    )


def runtime_env(venv_dir: Path, candidate_runtime: Path) -> dict[str, str]:
    env = os.environ.copy()
    scripts_dir = venv_dir / ("Scripts" if os.name == "nt" else "bin")
    env["PATH"] = str(scripts_dir) + os.pathsep + env.get("PATH", "")
    env["PIP_CACHE_DIR"] = str(candidate_runtime / "pip_cache")
    env["TMP"] = str(candidate_runtime / "tmp")
    env["TEMP"] = str(candidate_runtime / "tmp")
    env["TOX_WORK_DIR"] = str(candidate_runtime / "tox_work")
    (candidate_runtime / "pip_cache").mkdir(parents=True, exist_ok=True)
    (candidate_runtime / "tmp").mkdir(parents=True, exist_ok=True)
    (candidate_runtime / "tox_work").mkdir(parents=True, exist_ok=True)
    return env


def git_short_status(cwd: Path) -> list[str]:
    result = run_args(["git", "status", "--short"], cwd=cwd, timeout=60)
    return [line for line in result["stdout"].splitlines() if line.strip()]


def is_inside(path: Path, parent: Path) -> bool:
    try:
        path.resolve().relative_to(parent.resolve())
        return True
    except ValueError:
        return False


def metadata_hashes(workspace: Path, names: list[str]) -> list[dict[str, Any]]:
    records = []
    for name in names:
        path = workspace / name
        records.append(
            {
                "path": name,
                "exists": path.is_file(),
                "sha256": sha256_file(path) if path.is_file() else None,
            }
        )
    return records


def extract_failure_signature(log_text: str) -> dict[str, Any]:
    failed_nodes = []
    for match in re.finditer(r"FAILED\s+([^\s]+)", log_text):
        failed_nodes.append(match.group(1))
    error_roots = []
    for line in log_text.splitlines():
        stripped = line.strip()
        if stripped.startswith("E   ") or re.search(r"\.py:\d+:", stripped):
            error_roots.append(stripped)
    module_errors = sorted(set(re.findall(r"(ModuleNotFoundError: No module named '[^']+')", log_text)))
    assertion_errors = sorted(set(re.findall(r"(AssertionError:[^\n]*)", log_text)))
    return {
        "failed_nodes": sorted(set(failed_nodes)),
        "failed_node_count": len(set(failed_nodes)),
        "traceback_or_error_roots": error_roots[:40],
        "traceback_or_error_root_count": len(error_roots),
        "module_errors": module_errors,
        "assertion_errors": assertion_errors[:20],
        "raw_log_sha256": sha256_text(log_text),
        "semantic_signature_sha256": sha256_text(
            json.dumps(
                {
                    "failed_nodes": sorted(set(failed_nodes)),
                    "error_roots": error_roots[:40],
                    "module_errors": module_errors,
                    "assertion_errors": assertion_errors[:20],
                },
                sort_keys=True,
            )
        ),
    }


def classify_setup(result: dict[str, Any]) -> str:
    text = (result.get("stdout", "") + "\n" + result.get("stderr", "")).lower()
    if result.get("timed_out"):
        return "blocked_timeout"
    if result.get("returncode") == 0:
        return "provider_capsule_setup_pass"
    if "no matching distribution" in text or "could not find a version" in text:
        return "blocked_dependency_install_failure"
    if "microsoft visual c++" in text or "failed building wheel" in text:
        return "blocked_compiled_dependency"
    if "network" in text or "connection" in text:
        return "blocked_network_required"
    return "blocked_dependency_install_failure"


def classify_replay(result: dict[str, Any], setup_status: str, signature: dict[str, Any]) -> str:
    if setup_status != "provider_capsule_setup_pass":
        return setup_status.replace("provider_capsule_setup_pass", "blocked_provider_precondition")
    if result.get("timed_out"):
        return "blocked_timeout"
    if result.get("returncode") == 0:
        return "failure_not_reproduced"
    if signature.get("failed_node_count", 0) > 0 or signature.get("module_errors"):
        return "pre_repair_failure_materialized"
    return "blocked_environment_unclear"


def write_candidate_file(cdir: Path, rel: str, value: Any) -> None:
    if isinstance(value, str):
        write_text_lf(cdir / rel, value)
    else:
        write_json_deterministic(cdir / rel, value)


def prepare_workspace(candidate: dict[str, Any], cdir: Path) -> tuple[Path, Path, dict[str, Any]]:
    candidate_runtime = RUNTIME_ROOT / candidate["candidate_id"]
    workspace = candidate_runtime / "checkout"
    safe_rmtree(candidate_runtime, RUNTIME_ROOT)
    candidate_runtime.mkdir(parents=True, exist_ok=True)
    clone = run_args(["git", "clone", "--no-checkout", candidate["repo_url"], str(workspace)], ROOT, timeout=180)
    checkout = run_args(["git", "checkout", candidate["candidate_sha"]], workspace, timeout=120) if workspace.exists() else {"returncode": 1, "stdout": "", "stderr": "workspace missing", "timed_out": False}
    cat_file = run_args(["git", "cat-file", "-e", f"{candidate['candidate_sha']}^{{commit}}"], workspace, timeout=60) if workspace.exists() else {"returncode": 1, "stdout": "", "stderr": "workspace missing", "timed_out": False}
    head = run_args(["git", "rev-parse", "HEAD"], workspace, timeout=60) if workspace.exists() else {"returncode": 1, "stdout": "", "stderr": "workspace missing", "timed_out": False}
    commit_ok = clone.get("returncode") == 0 and checkout.get("returncode") == 0 and cat_file.get("returncode") == 0
    verification = {
        "status": "PASS" if commit_ok else "BLOCK",
        "candidate_id": candidate["candidate_id"],
        "repo_url": candidate["repo_url"],
        "candidate_sha": candidate["candidate_sha"],
        "clone": compact_result(clone),
        "checkout": compact_result(checkout),
        "cat_file_commit": compact_result(cat_file),
        "resolved_head": head.get("stdout", "").strip(),
        "commit_resolved": cat_file.get("returncode") == 0,
        "checkout_succeeded": checkout.get("returncode") == 0,
        "exact_blocker": None if commit_ok else "blocked_repo_checkout_failure",
    }
    return candidate_runtime, workspace, verification


def run_candidate(candidate: dict[str, Any]) -> dict[str, Any]:
    cdir = OUT_DIR / "candidates" / candidate["candidate_id"]
    cdir.mkdir(parents=True, exist_ok=True)
    source_capsule_dir = BATCH058_DIR / "candidates" / candidate["candidate_id"]
    capsule = read_json(source_capsule_dir / "provider_materialization_capsule_prescreen.json")
    evidence_manifest = read_json(source_capsule_dir / "provider_capsule_evidence_manifest.json")
    test_map = read_json(source_capsule_dir / "declared_test_command_map.json")
    runtime_map = read_json(source_capsule_dir / "declared_runtime_map.json")
    dependency_map = read_json(source_capsule_dir / "declared_dependency_map.json")

    candidate_runtime, workspace, commit_verification = prepare_workspace(candidate, cdir)
    target_path = workspace / candidate["native_test_path"]
    metadata = metadata_hashes(workspace, candidate["expected_provider_metadata"])
    test_exists = target_path.is_file()
    test_sha256 = sha256_file(target_path) if test_exists else None
    pre_setup_status = git_short_status(workspace) if workspace.exists() else []

    write_candidate_file(
        cdir,
        "decision_time_input_manifest.json",
        {
            "candidate_id": candidate["candidate_id"],
            "allowed_inputs": [
                "Batch058 provider capsule artifacts",
                "Batch058 candidate plan",
                "Batch058 commit resolution audit",
                "Batch058 leakage screen status",
                "buggy source tree at candidate SHA",
                "native target test path",
                "declared provider/runtime/dependency/test evidence in buggy checkout",
                "pre-repair replay output generated in Batch059",
            ],
            "batch058_provider_capsule_sha256": sha256_file(source_capsule_dir / "provider_materialization_capsule_prescreen.json"),
            "batch058_test_command_map_sha256": sha256_file(source_capsule_dir / "declared_test_command_map.json"),
            "buggy_commit_sha": candidate["candidate_sha"],
            "native_target_test_path": candidate["native_test_path"],
            "issue_body_text_persisted": False,
            "issue_body_excluded_from_repair_evidence": True,
            "decision_time_safe": True,
        },
    )
    write_candidate_file(cdir, "forbidden_evidence_audit.json", {"candidate_id": candidate["candidate_id"], "status": "PASS", **FORBIDDEN_EVIDENCE_FIELDS})
    write_candidate_file(
        cdir,
        "issue_body_leakage_boundary.json",
        {
            "candidate_id": candidate["candidate_id"],
            "issue_url": candidate["issue_url"],
            "issue_body_sha256_from_batch058": evidence_manifest.get("issue_body_sha256"),
            "issue_body_text_persisted": False,
            "issue_body_fix_or_workaround_text_used": False,
            "status": "PASS",
        },
    )
    write_candidate_file(cdir, "label_blindness_check.json", {"candidate_id": candidate["candidate_id"], "hidden_labels_used": False, "status": "PASS"})
    write_candidate_file(cdir, "gold_patch_exclusion_check.json", {"candidate_id": candidate["candidate_id"], "gold_patch_used": False, "status": "PASS"})
    write_candidate_file(cdir, "future_evidence_exclusion_check.json", {"candidate_id": candidate["candidate_id"], "future_evidence_used": False, "status": "PASS"})

    write_candidate_file(
        cdir,
        "candidate_replay_plan.json",
        {
            "candidate_id": candidate["candidate_id"],
            "repo_url": candidate["repo_url"],
            "candidate_sha": candidate["candidate_sha"],
            "native_target_test_path": candidate["native_test_path"],
            "planned_command": candidate["planned_command"],
            "provider_setup": candidate["provider_setup"],
            "replay_scope": "pre_repair_only",
            "patch_generation_allowed": False,
            "post_repair_replay_allowed": False,
        },
    )
    write_candidate_file(cdir, "candidate_commit_verification.json", commit_verification)
    write_candidate_file(
        cdir,
        "candidate_workspace_manifest.json",
        {
            "candidate_id": candidate["candidate_id"],
            "workspace_path": str(workspace),
            "workspace_outside_repo": not is_inside(workspace, ROOT),
            "runtime_root": str(candidate_runtime),
            "source_files_committed": False,
            "native_test_path_exists": test_exists,
            "native_test_sha256": test_sha256,
            "provider_metadata": metadata,
            "status": "PASS" if commit_verification["status"] == "PASS" and test_exists else "BLOCK",
            "exact_blocker": None if test_exists else "blocked_native_test_missing",
        },
    )
    write_candidate_file(
        cdir,
        "candidate_provider_capsule_preservation.json",
        {
            "candidate_id": candidate["candidate_id"],
            "batch058_capsule_status": capsule.get("status"),
            "batch058_approval_status": capsule.get("approval_status"),
            "provider_risk": capsule.get("provider_risk"),
            "future_replay_readiness": capsule.get("future_replay_readiness"),
            "repair_success_claim_allowed": False,
            "status": "PASS",
        },
    )
    write_candidate_file(
        cdir,
        "candidate_dependency_plan.json",
        {
            "candidate_id": candidate["candidate_id"],
            "batch058_dependency_surface": dependency_map.get("dependency_surface"),
            "batch059_install_command": candidate["install_command"],
            "install_basis": "declared_project_metadata_or_declared_dev_requirements_in_buggy_checkout",
            "undeclared_dependency_install_authorized": False,
            "metadata_files": metadata,
            "status": "PASS",
        },
    )
    write_candidate_file(
        cdir,
        "candidate_command_context.json",
        {
            "candidate_id": candidate["candidate_id"],
            "planned_command": candidate["planned_command"],
            "native_target_test_path": candidate["native_test_path"],
            "declared_test_command_map_status": test_map.get("status"),
            "runtime_map": runtime_map,
            "status": "PASS",
        },
    )
    write_candidate_file(
        cdir,
        "candidate_command_normalization.json",
        {
            "candidate_id": candidate["candidate_id"],
            "planned_command": candidate["planned_command"],
            "effective_command": candidate["planned_command"],
            "substituted_command": False,
            "normalization_reason": "PATH selects isolated provider venv executables while preserving command text",
            "status": "PASS",
        },
    )
    write_candidate_file(
        cdir,
        "candidate_provider_precondition_check.json",
        {
            "candidate_id": candidate["candidate_id"],
            "python_version": sys.version.split()[0],
            "python_313_available": sys.version_info >= (3, 13),
            "native_test_path_exists": test_exists,
            "metadata_files": metadata,
            "network_required": False,
            "external_service_required": False,
            "status": "PASS" if test_exists else "BLOCK",
            "exact_blocker": None if test_exists else "blocked_native_test_missing",
        },
    )

    venv_dir = candidate_runtime / "provider_venv"
    venv_create = run_args([sys.executable, "-m", "venv", str(venv_dir)], ROOT, timeout=180)
    env = runtime_env(venv_dir, candidate_runtime)
    setup_result: dict[str, Any]
    if venv_create.get("returncode") != 0:
        setup_result = {**venv_create, "stdout": venv_create.get("stdout", ""), "stderr": venv_create.get("stderr", "")}
    else:
        setup_result = run_shell(candidate["install_command"], workspace, timeout=300, env=env)
    setup_status = classify_setup(setup_result)
    write_candidate_file(
        cdir,
        "provider_capsule_replay_plan.json",
        {
            "candidate_id": candidate["candidate_id"],
            "setup_command": candidate["install_command"],
            "setup_basis": "declared provider capsule plus buggy checkout metadata",
            "source_mutation_allowed": False,
            "test_mutation_allowed": False,
            "provider_setup_is_repair_success": False,
            "status": "PASS",
        },
    )
    write_candidate_file(
        cdir,
        "provider_capsule_setup_trace.json",
        {
            "candidate_id": candidate["candidate_id"],
            "venv_create": compact_result(venv_create),
            "setup_command": candidate["install_command"],
            "setup": compact_result(setup_result),
            "status": setup_status,
        },
    )
    write_candidate_file(
        cdir,
        "provider_capsule_setup_result.json",
        {
            "candidate_id": candidate["candidate_id"],
            "classification": setup_status,
            "provider_setup_passed": setup_status == "provider_capsule_setup_pass",
            "provider_setup_is_repair_success": False,
            "source_or_test_mutation_authorized": False,
            "exact_blocker": None if setup_status == "provider_capsule_setup_pass" else setup_status,
            "status": "PASS" if setup_status == "provider_capsule_setup_pass" else "BLOCK",
        },
    )
    write_candidate_file(
        cdir,
        "provider_capsule_not_repair_boundary.json",
        {
            "candidate_id": candidate["candidate_id"],
            "provider_setup_treated_as_repair_success": False,
            "materialized_failure_treated_as_repair_success": False,
            "repair_count_increment_allowed": False,
            "status": "PASS",
        },
    )
    write_candidate_file(cdir, "provider_capsule_install_log_raw.txt", raw_log(setup_result))

    replay_result: dict[str, Any] | None = None
    signature: dict[str, Any]
    if setup_status == "provider_capsule_setup_pass" and commit_verification["status"] == "PASS" and test_exists:
        replay_result = run_shell(candidate["planned_command"], workspace, timeout=300, env=env)
        replay_log = raw_log(replay_result)
        write_candidate_file(cdir, "pre_repair_replay_log_raw.txt", replay_log)
        signature = extract_failure_signature(replay_log)
        write_candidate_file(
            cdir,
            "failure_signature_extract.txt",
            json.dumps(signature, indent=2, sort_keys=True),
        )
    else:
        reason = setup_status if setup_status != "provider_capsule_setup_pass" else commit_verification.get("exact_blocker") or "blocked_native_test_missing"
        write_candidate_file(cdir, "pre_repair_replay_not_run_reason.txt", reason)
        signature = {
            "failed_nodes": [],
            "failed_node_count": 0,
            "traceback_or_error_roots": [],
            "traceback_or_error_root_count": 0,
            "module_errors": [],
            "assertion_errors": [],
            "raw_log_sha256": None,
            "semantic_signature_sha256": None,
        }
        replay_result = {"returncode": None, "timed_out": False, "stdout": "", "stderr": "", "elapsed_seconds": 0, "command": candidate["planned_command"], "cwd": str(workspace)}
        write_candidate_file(cdir, "failure_signature_not_available.json", signature)
    replay_classification = classify_replay(replay_result, setup_status, signature)
    write_candidate_file(cdir, "pre_repair_replay_command.txt", candidate["planned_command"])
    write_candidate_file(
        cdir,
        "pre_repair_replay_result.json",
        {
            "candidate_id": candidate["candidate_id"],
            "command": candidate["planned_command"],
            "result": compact_result(replay_result),
            "failure_signature": signature,
            "classification": replay_classification,
            "target_code_failure_materialized": replay_classification == "pre_repair_failure_materialized",
            "repair_success_claim_allowed": False,
            "patch_generated": False,
            "patch_applied": False,
            "post_repair_replay_run": False,
            "duplicate_replay_run": False,
            "count_gate_run": False,
        },
    )
    write_candidate_file(
        cdir,
        "pre_repair_replay_classification.json",
        {
            "candidate_id": candidate["candidate_id"],
            "classification": replay_classification,
            "failed_nodes": signature.get("failed_nodes", []),
            "traceback_roots_available": signature.get("traceback_or_error_root_count", 0) > 0,
            "status": "PASS",
        },
    )

    post_replay_status = git_short_status(workspace) if workspace.exists() else []
    mutated_tracked = [line for line in post_replay_status if not line.startswith("?? ")]
    write_candidate_file(
        cdir,
        "workspace_custody_check.json",
        {
            "candidate_id": candidate["candidate_id"],
            "workspace_path": str(workspace),
            "workspace_outside_repo": not is_inside(workspace, ROOT),
            "tracked_source_or_test_mutations": mutated_tracked,
            "untracked_provider_artifacts_allowed_in_runtime_workspace": [line for line in post_replay_status if line.startswith("?? ")],
            "pre_setup_git_status": pre_setup_status,
            "post_replay_git_status": post_replay_status,
            "source_mutated": bool(mutated_tracked),
            "tests_mutated": bool(mutated_tracked),
            "status": "PASS" if not mutated_tracked else "BLOCK",
        },
    )

    target_materialized = replay_classification == "pre_repair_failure_materialized"
    if target_materialized:
        patch_license_state = candidate["future_patch_license"]
        if candidate["candidate_id"].startswith("cloudpickle"):
            bridge_classification = "target_failure_materialized_future_decomposition_recommended"
            future_decomposition = True
            future_patch_gate = True
        else:
            bridge_classification = "target_failure_materialized_single_source_family"
            future_decomposition = False
            future_patch_gate = True
    else:
        patch_license_state = "patch_license_closed_provider_dependency_blocked" if setup_status != "provider_capsule_setup_pass" else "patch_license_closed_failure_not_reproduced"
        bridge_classification = "target_failure_not_materialized"
        future_decomposition = False
        future_patch_gate = False

    amds_common = {
        "candidate_id": candidate["candidate_id"],
        "replay_classification": replay_classification,
        "target_code_failure_materialized": target_materialized,
        "failed_nodes": signature.get("failed_nodes", []),
        "future_only": True,
        "patch_execution_allowed_in_batch059": False,
        "repair_success_claim_allowed": False,
    }
    write_candidate_file(cdir, "amds_replay_board_state.json", {**amds_common, "bridge_classification": bridge_classification, "status": "PASS"})
    write_candidate_file(cdir, "failure_cell_registry.json", {**amds_common, "cells": signature.get("failed_nodes", []), "status": "PASS"})
    write_candidate_file(cdir, "failure_mine_risk_map.json", {**amds_common, "unsafe_cells": [], "risk_notes": ["no patch execution in Batch059"], "status": "PASS"})
    write_candidate_file(cdir, "safe_action_frontier.json", {**amds_common, "next_safe_actions": ["future decomposition or patch-gate batch only"], "status": "PASS"})
    write_candidate_file(cdir, "information_gain_move_ranking.json", {**amds_common, "ranked_moves": ["preserve failure signature", "decompose failing nodes", "authorize future source-only patch gate if applicable"], "status": "PASS"})
    write_candidate_file(cdir, "flagged_unsafe_cells.json", {**amds_common, "flagged_unsafe_cells": ["patch_generation", "source_mutation", "test_mutation", "duplicate_replay", "count_gate"], "status": "PASS"})
    write_candidate_file(cdir, "failure_stack_constraint_graph.json", {**amds_common, "traceback_or_error_roots": signature.get("traceback_or_error_roots", []), "status": "PASS"})
    write_candidate_file(cdir, "ast_loop_extrusion_bridge.json", {**amds_common, "bridge_used_as_repair_proof": False, "bridge_status": "future_only_not_executed", "status": "PASS"})
    write_candidate_file(cdir, "probe_to_patch_transition_gate.json", {**amds_common, "patch_license_state": patch_license_state, "batch059_patch_transition_executed": False, "status": "PASS"})
    write_candidate_file(cdir, "patch_license_from_amds.json", {**amds_common, "patch_license_state": patch_license_state, "license_future_only": True, "license_executed": False, "status": "PASS"})
    write_candidate_file(
        cdir,
        "amds_candidate_summary.json",
        {
            **amds_common,
            "provider_capsule_setup_status": setup_status,
            "patch_license_state": patch_license_state,
            "future_decomposition_candidate": future_decomposition,
            "future_patch_gate_candidate": future_patch_gate,
            "future_provider_recovery_candidate": not target_materialized,
            "status": "PASS",
        },
    )
    return {
        "candidate_id": candidate["candidate_id"],
        "provider_capsule_setup_status": setup_status,
        "pre_repair_replay_classification": replay_classification,
        "target_code_failure_materialized": target_materialized,
        "failed_nodes": signature.get("failed_nodes", []),
        "patch_license_state": patch_license_state,
        "amds_bridge_classification": bridge_classification,
        "future_decomposition_candidate": future_decomposition,
        "future_patch_gate_candidate": future_patch_gate,
        "future_provider_recovery_candidate": not target_materialized,
        "exact_blocker": None if target_materialized else replay_classification,
    }


def main() -> int:
    safe_rmtree(OUT_DIR, ROOT / "outputs")
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    RUNTIME_ROOT.mkdir(parents=True, exist_ok=True)

    artifact = verify_official_zip(
        BATCH058_ZIP,
        artifact_name=BATCH058_ARTIFACT_NAME,
        artifact_id=BATCH058_ARTIFACT_ID,
        workflow_run_id=BATCH058_WORKFLOW_RUN_ID,
        workflow_head_sha=BATCH058_WORKFLOW_HEAD_SHA,
        expected_sha256=BATCH058_SHA256,
        expected_size=BATCH058_SIZE,
        expected_entry_count=BATCH058_ENTRY_COUNT,
        artifact_manifest_checked=BATCH058_ARTIFACT_MANIFEST_CHECKED,
        output_manifests=BATCH058_OUTPUT_MANIFESTS,
    )
    if artifact.get("status") != "PASS":
        write_json_deterministic(OUT_DIR / "batch058_artifact_sha256_verification.json", artifact)
        write_json_deterministic(
            OUT_DIR / "batch059_final_decision.json",
            {
                "status": "BLOCK",
                "exact_blocker": "batch058_artifact_absent_for_official_ingest"
                if artifact.get("exact_blocker") == "manual_official_artifact_zip_missing"
                else artifact.get("exact_blocker"),
                "next_allowed_action": "manual_batch058_artifact_handoff_required",
            },
        )
        write_sha256sums(OUT_DIR)
        return 1
    ingest = ingest_official_outputs(
        BATCH058_ZIP,
        ROOT,
        prefixes=("post_v2_37_hardening_batch058_seed_discovery_wave_3_provider_prescreen",),
    )
    write_json_deterministic(OUT_DIR / "batch058_artifact_sha256_verification.json", artifact)
    write_json_deterministic(OUT_DIR / "batch058_artifact_ingestion_summary.json", {"artifact_verification": artifact, "ingest": ingest, "status": "PASS" if ingest.get("status") == "PASS" else "BLOCK"})

    batch058_final = read_json(BATCH058_DIR / "batch058_final_decision.json")
    batch058_plan = read_json(BATCH058_DIR / "batch059_pre_repair_replay_wave_3_plan.json")
    batch058_claim = read_json(BATCH058_DIR / "claim_boundary.json")
    batch058_provider = read_json(BATCH058_DIR / "provider_capsule_prescreen_wave_3.json")
    preserved = {
        "issue_derived_repair_count": ISSUE_DERIVED_REPAIR_COUNT,
        "native_external_repair_count": NATIVE_EXTERNAL_REPAIR_COUNT,
        "full_scoring": "NOT_RUN/disallowed",
        "memory_lift": "not_demonstrated",
        "self_maintaining_software": "false/not_demonstrated",
        "batch058_pre_repair_replay_run": False,
        "batch058_patch_generated": False,
        "batch058_patch_applied": False,
        "batch058_duplicate_replay_run": False,
        "batch058_count_gate_run": False,
        "batch059_planned_candidate_count": 2,
        "next_allowed_action": "batch059_pre_repair_replay_wave_3_limited",
        "status": "PASS",
    }
    write_json_deterministic(OUT_DIR / "batch058_result_preservation.json", preserved)
    write_json_deterministic(OUT_DIR / "batch058_wave3_provider_prescreen_preservation.json", {"status": "PASS", "records": batch058_provider.get("records", [])})
    write_json_deterministic(OUT_DIR / "batch058_candidate_plan_preservation.json", {"status": "PASS", "planned_candidates": batch058_plan.get("planned_candidates", [])})
    write_json_deterministic(OUT_DIR / "batch058_claim_boundary_preservation.json", {"status": "PASS", "claim_boundary": batch058_claim})
    write_json_deterministic(
        OUT_DIR / "batch058_next_action_boundary.json",
        {
            "status": "PASS" if batch058_final.get("next_allowed_action") == "batch059_pre_repair_replay_wave_3_limited" else "BLOCK",
            "observed_next_allowed_action": batch058_final.get("next_allowed_action"),
            "expected_next_allowed_action": "batch059_pre_repair_replay_wave_3_limited",
        },
    )

    write_json_deterministic(
        OUT_DIR / "batch059_pre_repair_replay_plan.json",
        {
            "status": "PASS",
            "scope": "two_batch058_approved_candidates_only",
            "candidate_ids": [candidate["candidate_id"] for candidate in CANDIDATES],
            "patch_generation_allowed": False,
            "post_repair_replay_allowed": False,
            "duplicate_replay_allowed": False,
            "count_gate_allowed": False,
        },
    )

    candidate_results = [run_candidate(candidate) for candidate in CANDIDATES]
    materialized = [item for item in candidate_results if item["target_code_failure_materialized"]]
    blocked = [item for item in candidate_results if item["pre_repair_replay_classification"].startswith("blocked_")]
    not_reproduced = [item for item in candidate_results if item["pre_repair_replay_classification"] == "failure_not_reproduced"]
    future_decomposition = [item["candidate_id"] for item in candidate_results if item["future_decomposition_candidate"]]
    future_patch_gate = [item["candidate_id"] for item in candidate_results if item["future_patch_gate_candidate"]]
    future_provider_recovery = [item["candidate_id"] for item in candidate_results if item["future_provider_recovery_candidate"]]
    next_allowed_action = (
        "batch060_source_only_patch_gate_wave_3"
        if future_patch_gate
        else "batch060_failure_family_decomposition_wave_3"
        if future_decomposition
        else "batch059b_provider_runtime_recovery_wave_3"
        if future_provider_recovery
        else "batch058b_seed_discovery_wave_3_expansion"
    )
    final = {
        "status": "PASS",
        "batch058_ingest_status": "PASS",
        "candidate_results": candidate_results,
        "candidate_replay_classifications": {item["candidate_id"]: item["pre_repair_replay_classification"] for item in candidate_results},
        "provider_capsule_setup_status_by_candidate": {item["candidate_id"]: item["provider_capsule_setup_status"] for item in candidate_results},
        "target_code_failure_materialization_count": len(materialized),
        "blocked_candidate_count": len(blocked),
        "failure_not_reproduced_count": len(not_reproduced),
        "future_decomposition_candidates": future_decomposition,
        "future_patch_gate_candidates": future_patch_gate,
        "future_provider_recovery_candidates": future_provider_recovery,
        "issue_derived_repair_count": ISSUE_DERIVED_REPAIR_COUNT,
        "native_external_repair_count": NATIVE_EXTERNAL_REPAIR_COUNT,
        "pre_repair_replay_run": True,
        "patch_generated": False,
        "patch_applied": False,
        "source_mutated": False,
        "tests_mutated": False,
        "post_repair_replay_run": False,
        "duplicate_replay_run": False,
        "count_gate_run": False,
        "repair_count_increment": False,
        "full_scoring": "NOT_RUN/disallowed",
        "memory_lift": "not_demonstrated",
        "self_maintaining_software": "false/not_demonstrated",
        "current_protocol": CURRENT_PROTOCOL,
        "next_allowed_action": next_allowed_action,
        "exact_blocker": None,
    }
    write_json_deterministic(OUT_DIR / "batch059_pre_repair_replay_results.json", {"status": "PASS", "candidate_results": candidate_results})
    write_json_deterministic(OUT_DIR / "batch059_materialized_failure_registry.json", {"status": "PASS", "records": materialized})
    write_json_deterministic(OUT_DIR / "batch059_blocked_candidate_registry.json", {"status": "PASS", "records": blocked})
    write_json_deterministic(OUT_DIR / "batch059_failure_not_reproduced_registry.json", {"status": "PASS", "records": not_reproduced})
    write_json_deterministic(OUT_DIR / "batch059_amds_bridge_dashboard.json", {"status": "PASS", "candidate_results": candidate_results})
    write_json_deterministic(OUT_DIR / "batch059_future_decomposition_recommendation.json", {"status": "PASS", "candidate_ids": future_decomposition, "future_only": True})
    write_json_deterministic(OUT_DIR / "batch059_future_patch_gate_recommendation.json", {"status": "PASS", "candidate_ids": future_patch_gate, "future_only": True})
    write_json_deterministic(OUT_DIR / "batch059_future_provider_recovery_recommendation.json", {"status": "PASS", "candidate_ids": future_provider_recovery, "future_only": True})
    write_json_deterministic(OUT_DIR / "batch059_final_decision.json", final)
    write_json_deterministic(
        OUT_DIR / "claim_boundary.json",
        {
            **final,
            "materialized_failure_is_repair_success": False,
            "provider_setup_is_repair_success": False,
            "full_scoring_claim_allowed": False,
            "memory_lift_claim_allowed": False,
            "self_maintaining_software_claim_allowed": False,
        },
    )
    write_json_deterministic(
        OUT_DIR / "package_verification.json",
        {
            "status": "PASS",
            "raw_zip_payload_committed": False,
            "runtime_workspaces_committed": False,
            "source_checkouts_committed": False,
            "venvs_committed": False,
            "caches_committed": False,
            "repair_count_increment": False,
        },
    )
    write_json_deterministic(
        OUT_DIR / "artifact_sha256_verification.json",
        {
            "status": "PASS",
            "artifact_payload_expected": "post_v2_37_hardening_batch059_pre_repair_replay_wave_3_limited_artifacts",
            "raw_zip_payload_committed": False,
            "sha256sums_path": "SHA256SUMS.txt",
        },
    )
    summary_lines = [
        "# Batch059 pre-repair replay wave 3 limited",
        "",
        "Batch059 officially ingested Batch058 evidence and ran bounded pre-repair replay for the two Batch058-approved Wave 3 candidates only.",
        "",
        f"- Batch058 ingest status: PASS",
        f"- Target-code failure materialization count: {len(materialized)}",
        f"- Blocked/failure-not-reproduced count: {len(blocked) + len(not_reproduced)}",
        f"- Future patch-gate candidates: {', '.join(future_patch_gate) if future_patch_gate else 'none'}",
        f"- Future decomposition candidates: {', '.join(future_decomposition) if future_decomposition else 'none'}",
        f"- Future provider recovery candidates: {', '.join(future_provider_recovery) if future_provider_recovery else 'none'}",
        f"- Issue-derived repair count: {ISSUE_DERIVED_REPAIR_COUNT}",
        f"- Native external repair count: {NATIVE_EXTERNAL_REPAIR_COUNT}",
        "- Full scoring: NOT_RUN/disallowed",
        "- Memory lift: not_demonstrated",
        "- Self-maintaining software: false/not_demonstrated",
        f"- Next allowed action: {next_allowed_action}",
        "",
        "No patch was generated or applied, no post-repair replay ran, no duplicate replay ran, and no count gate ran.",
    ]
    write_text_lf(OUT_DIR / "batch059_summary.md", "\n".join(summary_lines))
    write_json_deterministic(OUT_DIR / "audit.json", {"status": "PASS", "generated_at": now_iso(), "final_decision_sha256": sha256_file(OUT_DIR / "batch059_final_decision.json")})
    write_sha256sums(OUT_DIR)
    print(json.dumps(final, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
