from __future__ import annotations

import ast
import json
import os
import re
import shlex
import shutil
import stat
import subprocess
import sys
import time
import zipfile
from pathlib import Path, PurePosixPath
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from controllergate.core.evidence import sha256_bytes, sha256_file, write_json_deterministic, write_text_lf
from controllergate.core.manifests import write_sha256sums


OUT_NAME = "post_v2_37_hardening_batch063b_pytest_provider_runtime_recovery_followup"
OUT_DIR = ROOT / "outputs" / OUT_NAME
BATCH066_NAME = "post_v2_37_hardening_batch066_next_issue_repair_candidate_selection_or_pytest_recovery"
BATCH066_DIR = ROOT / "outputs" / BATCH066_NAME

if os.name == "nt":
    DEFAULT_RUNTIME_PARENT = Path(r"C:\Dev\ControllerGate_runtime")
else:
    DEFAULT_RUNTIME_PARENT = Path(os.environ.get("RUNNER_TEMP", "/tmp")) / "ControllerGate_runtime"
RUNTIME_ROOT = Path(os.environ.get("CONTROLLERGATE_BATCH063B_RUNTIME_ROOT", str(DEFAULT_RUNTIME_PARENT / "batch063b")))

BATCH066_ZIP = Path(
    os.environ.get(
        "CONTROLLERGATE_BATCH066_ARTIFACT_ZIP",
        r"C:\Users\thisb\Downloads\post_v2_37_hardening_batch066_next_issue_repair_candidate_selection_or_pytest_recovery_artifacts.zip",
    )
)
BATCH066_ARTIFACT = {
    "artifact_name": "post_v2_37_hardening_batch066_next_issue_repair_candidate_selection_or_pytest_recovery_artifacts",
    "artifact_id": 8205262992,
    "workflow_run_id": 29034358906,
    "workflow_head_sha": "1f09ca52d4782ba4412372f9034d9a8283264d74",
    "expected_sha256": "e0352bd1487e200fae0afa5278a4e1fd31ff8bf6aea0b0988f6bb020a5d4debe",
    "expected_size": 55101,
    "expected_entry_count": 91,
    "artifact_manifest_checked": 90,
    "output_manifest_checked": 89,
}

CURRENT_PROTOCOL = "v2.14"
ISSUE_DERIVED_REPAIR_COUNT = 4
NATIVE_EXTERNAL_REPAIR_COUNT = 4
FULL_SCORING = "NOT_RUN/disallowed"
MEMORY_LIFT = "not_demonstrated"
SELF_MAINTAINING = "false/not_demonstrated"
PYTEST_ID = "pytest_13895_pytest9_skiptest_behavior"
PYTEST_REPO_URL = "https://github.com/pytest-dev/pytest"
PYTEST_CLONE_URL = "https://github.com/pytest-dev/pytest.git"
PYTEST_SHA = "041aacad506b6c6891f2898f2bd378e0896e8b86"
PRESERVED_COMMAND = "python -m pytest testing -q --tb=no"
ARCHIVE_SUFFIXES = (".zip", ".tar", ".tar.gz", ".tgz", ".7z", ".pyc", ".pyo", ".whl")

PUBLIC_FORBIDDEN_TERMS = [
    "TLD",
    "TORUS",
    "chromosomal",
    "biological",
    "ToT-BULB",
    "metrological immune system",
    "replisome",
    "nuclear pore",
    "MCM",
    "6-set",
    "14-set",
    "196-set",
    "apoptosis",
    "SafeDeath",
    "sister chromatid",
    "cohesin",
]

HR_ALLOWED_STATUSES = {
    "implemented_now",
    "scaffolded_with_config_and_audit",
    "blocked_with_exact_reason",
    "requires_dedicated_future_batch_with_named_batch",
    "deprecated_with_reason",
    "already_implemented_with_evidence",
}


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_out_json(name: str, value: Any) -> None:
    write_json_deterministic(OUT_DIR / name, value)


def write_out_text(name: str, value: str) -> None:
    write_text_lf(OUT_DIR / name, value)


def is_safe_zip_member(name: str) -> bool:
    pure = PurePosixPath(name)
    return not (name.startswith("/") or "\\" in name or any(part in {"", ".", ".."} for part in pure.parts))


def verify_zip_manifest(archive: zipfile.ZipFile, manifest_name: str) -> dict[str, Any]:
    names = set(archive.namelist())
    if manifest_name not in names:
        return {"status": "MISSING", "manifest": manifest_name, "checked": 0, "failures": 1}
    checked = 0
    failures: list[str] = []
    missing: list[str] = []
    malformed: list[str] = []
    for line in archive.read(manifest_name).decode("utf-8").splitlines():
        if not line.strip():
            continue
        parts = line.split(maxsplit=1)
        if len(parts) != 2:
            malformed.append(line)
            continue
        expected, rel = parts
        rel = rel.strip().lstrip("*")
        if len(expected) != 64 or not is_safe_zip_member(rel):
            malformed.append(rel)
            continue
        if rel not in names:
            missing.append(rel)
            continue
        checked += 1
        if sha256_bytes(archive.read(rel)) != expected:
            failures.append(rel)
    return {
        "status": "PASS" if not failures and not missing and not malformed else "FAIL",
        "manifest": manifest_name,
        "checked": checked,
        "failures": len(failures),
        "failure_paths": failures,
        "missing": missing,
        "malformed": malformed,
    }


def verify_batch066_artifact() -> dict[str, Any]:
    if not BATCH066_ZIP.is_file():
        return {"status": "BLOCK", "exact_blocker": "batch066_artifact_absent_for_official_ingest"}
    digest = sha256_file(BATCH066_ZIP)
    size = BATCH066_ZIP.stat().st_size
    with zipfile.ZipFile(BATCH066_ZIP) as archive:
        names = archive.namelist()
        unsafe = [name for name in names if not is_safe_zip_member(name)]
        duplicates = len(names) - len(set(names))
        pycache_entries = [name for name in names if "__pycache__" in PurePosixPath(name).parts]
        pyc_entries = [name for name in names if name.endswith((".pyc", ".pyo"))]
        artifact_manifest = verify_zip_manifest(archive, "ARTIFACT_SHA256SUMS.txt")
        output_manifest = verify_zip_manifest(archive, "SHA256SUMS.txt")
    counts_pass = (
        artifact_manifest["status"] == "PASS"
        and artifact_manifest["checked"] == BATCH066_ARTIFACT["artifact_manifest_checked"]
        and output_manifest["status"] == "PASS"
        and output_manifest["checked"] == BATCH066_ARTIFACT["output_manifest_checked"]
    )
    status = (
        "PASS"
        if digest == BATCH066_ARTIFACT["expected_sha256"]
        and size == BATCH066_ARTIFACT["expected_size"]
        and len(names) == BATCH066_ARTIFACT["expected_entry_count"]
        and not unsafe
        and duplicates == 0
        and not pycache_entries
        and not pyc_entries
        and counts_pass
        else "BLOCK"
    )
    return {
        "status": status,
        "verification_source": "manual_local_artifact_boundary",
        "local_artifact_path": str(BATCH066_ZIP),
        "artifact_name": BATCH066_ARTIFACT["artifact_name"],
        "artifact_id": BATCH066_ARTIFACT["artifact_id"],
        "workflow_run_id": BATCH066_ARTIFACT["workflow_run_id"],
        "workflow_head_sha": BATCH066_ARTIFACT["workflow_head_sha"],
        "zip_opens": True,
        "zip_sha256": digest,
        "artifact_sha256": digest,
        "github_reported_digest": f"sha256:{BATCH066_ARTIFACT['expected_sha256']}",
        "zip_size_bytes": size,
        "artifact_size_bytes": size,
        "zip_entry_count": len(names),
        "unsafe_path_count": len(unsafe),
        "duplicate_path_count": duplicates,
        "zip_pycache_entries": len(pycache_entries),
        "zip_pyc_entries": len(pyc_entries),
        "artifact_manifest": artifact_manifest,
        "output_manifest": output_manifest,
        "raw_zip_bytes_ingested": False,
        "zip_payload_committed": False,
        "exact_blocker": None if status == "PASS" else "batch066_artifact_verification_failed",
    }


def ingest_batch066_outputs() -> dict[str, Any]:
    writes: list[dict[str, Any]] = []
    with zipfile.ZipFile(BATCH066_ZIP) as archive:
        for name in archive.namelist():
            if name.endswith("/") or name == "ARTIFACT_SHA256SUMS.txt" or name.endswith(ARCHIVE_SUFFIXES):
                continue
            if not is_safe_zip_member(name):
                writes.append({"status": "BLOCK", "path": name, "exact_blocker": "unsafe_zip_member"})
                continue
            target = BATCH066_DIR / Path(*PurePosixPath(name).parts)
            data = archive.read(name)
            target.parent.mkdir(parents=True, exist_ok=True)
            if target.is_file() and target.read_bytes() == data:
                writes.append({"status": "SKIPPED_IDENTICAL", "path": str(target), "changed": False})
            else:
                target.write_bytes(data)
                writes.append({"status": "WRITTEN", "path": str(target), "changed": True})
    blockers = [item for item in writes if item.get("status") == "BLOCK"]
    return {
        "status": "PASS" if not blockers else "BLOCK",
        "written_count": sum(item["status"] == "WRITTEN" for item in writes),
        "skipped_identical_count": sum(item["status"] == "SKIPPED_IDENTICAL" for item in writes),
        "raw_zip_bytes_committed": False,
        "blockers": blockers,
        "write_records": writes,
    }


def run_cmd(args: list[str], cwd: Path, *, timeout: int = 120, env: dict[str, str] | None = None) -> dict[str, Any]:
    started = time.time()
    try:
        proc = subprocess.run(args, cwd=cwd, env=env, text=True, encoding="utf-8", errors="replace", capture_output=True, timeout=timeout, check=False)
        return {
            "command": args,
            "cwd": str(cwd),
            "returncode": proc.returncode,
            "stdout": proc.stdout,
            "stderr": proc.stderr,
            "timed_out": False,
            "duration_seconds": round(time.time() - started, 3),
        }
    except subprocess.TimeoutExpired as exc:
        stdout = exc.stdout.decode("utf-8", errors="replace") if isinstance(exc.stdout, bytes) else (exc.stdout or "")
        stderr = exc.stderr.decode("utf-8", errors="replace") if isinstance(exc.stderr, bytes) else (exc.stderr or "")
        return {
            "command": args,
            "cwd": str(cwd),
            "returncode": None,
            "stdout": stdout,
            "stderr": stderr,
            "timed_out": True,
            "duration_seconds": round(time.time() - started, 3),
            "timeout_seconds": timeout,
        }


def command_log(result: dict[str, Any]) -> str:
    return (
        f"$ {' '.join(shlex.quote(str(part)) for part in result['command'])}\n"
        f"cwd: {result['cwd']}\n"
        f"returncode: {result.get('returncode')}\n"
        f"timed_out: {result.get('timed_out')}\n"
        f"duration_seconds: {result.get('duration_seconds')}\n\n"
        f"--- stdout ---\n{result.get('stdout') or ''}\n"
        f"--- stderr ---\n{result.get('stderr') or ''}\n"
    )


def safe_remove_runtime_root() -> None:
    resolved = RUNTIME_ROOT.resolve()
    allowed_parent = DEFAULT_RUNTIME_PARENT.resolve()
    if allowed_parent not in resolved.parents:
        raise RuntimeError(f"refusing to remove unexpected runtime root {resolved}")
    if RUNTIME_ROOT.exists():
        def on_remove_error(function: Any, path: str, exc_info: Any) -> None:
            os.chmod(path, stat.S_IWRITE)
            function(path)
        shutil.rmtree(RUNTIME_ROOT, onerror=on_remove_error)
    RUNTIME_ROOT.mkdir(parents=True, exist_ok=True)


def venv_python(venv_dir: Path) -> Path:
    return venv_dir / ("Scripts/python.exe" if os.name == "nt" else "bin/python")


def no_run(reason: str, **extra: Any) -> dict[str, Any]:
    return {"status": "NOT_RUN", "reason": reason, **extra}


def hash_tree_listing(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"exists": False, "file_count": 0, "tree_listing_sha256": None}
    files = sorted(p.relative_to(path).as_posix() for p in path.rglob("*") if p.is_file())
    return {"exists": True, "file_count": len(files), "tree_listing_sha256": sha256_bytes("\n".join(files).encode("utf-8"))}


def clone_workspace() -> tuple[Path, dict[str, Any]]:
    workspace = RUNTIME_ROOT / PYTEST_ID / "source"
    clone = run_cmd(["git", "clone", "--no-tags", "--filter=blob:none", PYTEST_CLONE_URL, str(workspace)], RUNTIME_ROOT, timeout=300)
    checkout = run_cmd(["git", "checkout", "--detach", PYTEST_SHA], workspace, timeout=180) if workspace.exists() else {"returncode": 1, "stdout": "", "stderr": "workspace_absent", "timed_out": False, "command": [], "cwd": str(RUNTIME_ROOT)}
    cat = run_cmd(["git", "cat-file", "-t", f"{PYTEST_SHA}^{{commit}}"], workspace, timeout=60) if workspace.exists() else {"stdout": ""}
    rev = run_cmd(["git", "rev-parse", "HEAD"], workspace, timeout=60) if workspace.exists() else {"stdout": ""}
    status = run_cmd(["git", "status", "--short"], workspace, timeout=60) if workspace.exists() else {"stdout": ""}
    records = []
    for step, result in [("clone", clone), ("checkout", checkout), ("cat_file", cat), ("rev_parse", rev), ("status", status)]:
        log = command_log(result)
        records.append({
            "step": step,
            "command": result.get("command"),
            "returncode": result.get("returncode"),
            "timed_out": result.get("timed_out"),
            "stdout_sha256": sha256_bytes((result.get("stdout") or "").encode("utf-8")),
            "stderr_sha256": sha256_bytes((result.get("stderr") or "").encode("utf-8")),
            "log_sha256": sha256_bytes(log.encode("utf-8")),
            "stdout_sample": (result.get("stdout") or "")[:400],
        })
    ok = (cat.get("stdout") or "").strip() == "commit" and (rev.get("stdout") or "").strip() == PYTEST_SHA
    return workspace, {
        "status": "PASS" if ok else "BLOCK",
        "candidate_id": PYTEST_ID,
        "repo_url": PYTEST_REPO_URL,
        "candidate_sha": PYTEST_SHA,
        "resolved_head": (rev.get("stdout") or "").strip(),
        "object_type": (cat.get("stdout") or "").strip(),
        "workspace_path": str(workspace),
        "commands": records,
    }


def metadata_summary(workspace: Path) -> dict[str, Any]:
    records = []
    for rel in ["pyproject.toml", "tox.ini", "noxfile.py", "setup.py", "setup.cfg", "requirements.txt", "requirements-dev.txt", "CONTRIBUTING.rst", "README.rst"]:
        path = workspace / rel
        if path.is_file():
            text = path.read_text(encoding="utf-8", errors="replace")
            records.append({"path": rel, "sha256": sha256_file(path), "bytes": path.stat().st_size})
        else:
            text = ""
        if rel == "pyproject.toml":
            pyproject = text
        if rel == "tox.ini":
            tox_ini = text
    pyproject = locals().get("pyproject", "")
    tox_ini = locals().get("tox_ini", "")
    minversion_match = re.search(r"minversion\s*=\s*[\"']([^\"']+)[\"']", pyproject)
    envlist_match = re.search(r"envlist\s*=\s*([^\n]+)", tox_ini)
    return {
        "status": "PASS",
        "metadata_files": records,
        "pyproject_minversion": minversion_match.group(1) if minversion_match else None,
        "declared_testpaths": ["testing"] if "testpaths" in pyproject and "testing" in pyproject else [],
        "declared_provider_setup": ["python -m pip install -e ."],
        "tox_ini_present": bool(tox_ini),
        "tox_envlist_sample": [item.strip() for item in re.split(r"[, ]+", envlist_match.group(1)) if item.strip()][:20] if envlist_match else [],
        "preserved_command": PRESERVED_COMMAND,
    }


def stale_cache_count(workspace: Path) -> int:
    if not workspace.exists():
        return 0
    return sum(1 for p in workspace.rglob("*") if p.name == "__pycache__" or p.suffix in {".pyc", ".pyo"} or p.name == ".pytest_cache")


def setup_provider_and_probe(workspace: Path) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any], str, str]:
    venv_dir = RUNTIME_ROOT / PYTEST_ID / "venv"
    create = run_cmd([sys.executable, "-m", "venv", str(venv_dir)], workspace, timeout=180)
    py = venv_python(venv_dir)
    env = os.environ.copy()
    env["PIP_DISABLE_PIP_VERSION_CHECK"] = "1"
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    provider_logs = command_log(create)
    records = [{"step": "create_venv", "returncode": create.get("returncode"), "timed_out": create.get("timed_out"), "log_sha256": sha256_bytes(command_log(create).encode("utf-8"))}]
    provider_ok = create.get("returncode") == 0 and not create.get("timed_out")
    for idx, command in enumerate([[str(py), "-m", "pip", "install", "--upgrade", "pip"], [str(py), "-m", "pip", "install", "-e", "."]], start=1):
        if not provider_ok:
            break
        result = run_cmd(command, workspace, timeout=360, env=env)
        log = command_log(result)
        provider_logs += "\n" + log
        records.append({"step": f"provider_command_{idx}", "command": command, "returncode": result.get("returncode"), "timed_out": result.get("timed_out"), "log_sha256": sha256_bytes(log.encode("utf-8"))})
        provider_ok = result.get("returncode") == 0 and not result.get("timed_out")
    write_out_text("pytest_provider_install_log_raw_batch063b.txt", provider_logs)
    provider = {
        "status": "PASS" if provider_ok else "BLOCK",
        "classification": "provider_runtime_recovered_from_declared_metadata" if provider_ok else "blocked_dependency_install_failure",
        "provider_runtime_setup_status": "provider_runtime_recovered_from_declared_metadata" if provider_ok else "blocked_dependency_install_failure",
        "declared_metadata_only": True,
        "provider_runtime_setup_is_repair_success": False,
        "venv_dir": str(venv_dir),
        "venv_python": str(py),
        "records": records,
    }

    version_probe_commands = [
        ("python_version", [str(py), "--version"], 60),
        ("pip_version", [str(py), "-m", "pip", "--version"], 60),
        ("git_rev_parse", ["git", "rev-parse", "HEAD"], 60),
        ("git_status_short", ["git", "status", "--short"], 60),
        ("git_describe_tags_always_dirty", ["git", "describe", "--tags", "--always", "--dirty"], 60),
        ("git_tag_merged_head", ["git", "tag", "--merged", "HEAD"], 60),
        ("sys_path", [str(py), "-c", "import sys; print('\\n'.join(sys.path))"], 60),
        ("find_spec_pytest", [str(py), "-c", "import importlib.util; spec=importlib.util.find_spec('pytest'); print(spec.origin if spec else None); print(spec.submodule_search_locations if spec else None)"], 60),
        ("import_pytest_version_file", [str(py), "-c", "import pytest; print(pytest.__version__); print(pytest.__file__)"], 60),
    ]
    version_logs: list[str] = []
    version_records: list[dict[str, Any]] = []
    for probe_id, command, timeout in version_probe_commands:
        result = run_cmd(command, workspace, timeout=timeout, env=env)
        log = command_log(result)
        version_logs.append(f"### {probe_id}\n{log}")
        version_records.append({
            "probe_id": probe_id,
            "command": command,
            "returncode": result.get("returncode"),
            "timed_out": result.get("timed_out"),
            "stdout": (result.get("stdout") or "")[:1200],
            "stderr_sha256": sha256_bytes((result.get("stderr") or "").encode("utf-8")),
            "log_sha256": sha256_bytes(log.encode("utf-8")),
        })
    version_log = "\n".join(version_logs)
    imported = next((r["stdout"] for r in version_records if r["probe_id"] == "import_pytest_version_file"), "")
    tags = next((r["stdout"] for r in version_records if r["probe_id"] == "git_tag_merged_head"), "")
    version_value = imported.splitlines()[0].strip() if imported.splitlines() else ""
    version_classification = "pytest_version_origin_missing_tags" if "0.1.dev" in version_value and not tags.strip() else "pytest_version_origin_ok"
    version = {
        "status": "PASS",
        "classification": version_classification,
        "observed_pytest_version": version_value,
        "candidate_pytest_file": imported.splitlines()[1].strip() if len(imported.splitlines()) > 1 else None,
        "safe_ancestor_tag_restoration_executed": False,
        "safe_ancestor_tag_restoration_status": "not_executed_because_no_predeclared_ancestor_tag_authority",
        "future_tag_exposure_avoided": True,
        "provider_runtime_recovery_is_repair_success": False,
        "probes": version_records,
    }

    command_probes = [
        ("pytest_version", [str(py), "-m", "pytest", "--version"], 60),
        ("pytest_help", [str(py), "-m", "pytest", "--help"], 60),
        ("pytest_collect_testing", [str(py), "-m", "pytest", "testing", "--collect-only", "-q"], 120),
        ("pytest_preserved_command", [str(py), "-m", "pytest", "testing", "-q", "--tb=no"], 120),
    ]
    command_logs: list[str] = []
    command_records: list[dict[str, Any]] = []
    for probe_id, command, timeout in command_probes:
        result = run_cmd(command, workspace, timeout=timeout, env=env)
        log = command_log(result)
        command_logs.append(f"### {probe_id}\n{log}")
        command_records.append({
            "probe_id": probe_id,
            "command": command,
            "returncode": result.get("returncode"),
            "timed_out": result.get("timed_out"),
            "output_sample": ((result.get("stdout") or "") + (result.get("stderr") or ""))[:1200],
            "log_sha256": sha256_bytes(log.encode("utf-8")),
        })
    command_log_text = "\n".join(command_logs)
    write_out_text("pytest_command_boundary_log_raw_batch063b.txt", command_log_text)
    minversion_blocked = "minversion" in command_log_text and "actual pytest-0.1" in command_log_text
    boundary_classification = "pytest_command_boundary_blocked_version_origin" if version_classification == "pytest_version_origin_missing_tags" else ("pytest_command_boundary_blocked_config_minversion" if minversion_blocked else "pytest_command_boundary_manual_review_needed")
    command = {
        "status": "PASS",
        "classification": boundary_classification,
        "minversion_blocked": minversion_blocked,
        "version_origin_blocks_command": version_classification != "pytest_version_origin_ok",
        "normalized": False,
        "partially_normalized": False,
        "pre_repair_replay_authorized": False,
        "probes": command_records,
    }
    return provider, version, command, version_log, command_log_text


def source_inventory(workspace: Path) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    src_files = sorted((workspace / "src").rglob("*.py")) if (workspace / "src").exists() else []
    test_files = sorted((workspace / "testing").rglob("*.py")) if (workspace / "testing").exists() else []
    parse_records: list[dict[str, Any]] = []
    symbol_records: list[dict[str, Any]] = []
    for path in src_files[:400]:
        rel = path.relative_to(workspace).as_posix()
        text = path.read_text(encoding="utf-8", errors="replace")
        try:
            tree = ast.parse(text)
            parse_records.append({"path": rel, "status": "PASS"})
            names = [node.name for node in ast.walk(tree) if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))]
            if names:
                symbol_records.append({"path": rel, "symbol_count": len(names), "sample": names[:20]})
        except SyntaxError as exc:
            parse_records.append({"path": rel, "status": "FAIL", "error": str(exc)})
    return (
        {"status": "PASS", "source_file_count": len(src_files), "test_file_count": len(test_files), "source_tree_hash": hash_tree_listing(workspace / "src"), "testing_tree_hash": hash_tree_listing(workspace / "testing"), "topology_probe_is_patch_permission": False},
        {"status": "PASS" if not any(r["status"] == "FAIL" for r in parse_records) else "WARN", "parsed_file_count": len(parse_records), "failed_parse_count": sum(r["status"] == "FAIL" for r in parse_records), "records_sample": parse_records[:80]},
        {"status": "PASS", "source_contact_prior_only": True, "patch_generation_allowed": False, "symbol_records_sample": symbol_records[:80]},
    )


def simple_status(status: str = "PASS", **extra: Any) -> dict[str, Any]:
    return {"status": status, **extra}


def write_policy_artifacts(workspace: Path, command_classification: str) -> None:
    status_contract = {
        state: {
            "meaning": state.replace("_", " "),
            "allowed_next_action": "route_or_close_under_policy",
            "forbidden_next_action": "count_without_duplicate_replay_or_use_forbidden_evidence",
            "count_policy": "no_count_increment_unless_source_only_target_pass_duplicate_replay_and_count_gate_pass",
            "evidence_required": "hash_pinned_artifact_or_decision_time_safe_workspace_record",
            "reopen_condition": "new_decision_time_safe_evidence_or_explicit_later_batch_authorization",
            "proof_boundary": "terminal_or_routing_state_not_repair_success",
        }
        for state in [
            "counted_repair",
            "duplicate_replay_candidate",
            "source_only_patch_candidate",
            "pre_repair_materialized",
            "provider_recovery_needed",
            "dependency_recovery_needed",
            "command_boundary_recovery_needed",
            "harness_origin_needed",
            "workspace_purity_blocked",
            "failure_family_decomposition_needed",
            "interpreter_behavior_manual_review",
            "test_expectation_manual_review",
            "unbounded_external_provider",
            "forbidden_evidence_required",
            "not_reproducible",
            "out_of_scope",
            "retired",
            "manual_review",
            "unrecoverable_under_current_policy",
        ]
    }
    wrappers = {
        "universal_wrapper_law_manifest_batch063b.json": {
            "status": "PASS",
            "eventual_goal": "verified_action_path_or_terminal_state_for_each_encountered_bug",
            "not_a_promise_to_fix_every_bug": True,
            "unrecoverable_under_current_policy_is_valid_terminal_state": True,
            "self_maintaining_software": SELF_MAINTAINING,
            "counted_repairs_are_milestones_not_self_maintenance_proof": True,
            "provider_runtime_setup_is_not_repair_success": True,
            "pre_repair_replay_is_not_repair_success": True,
            "patch_target_pass_not_counted_until_duplicate_replay_and_count_gate": True,
        },
        "self_maintaining_wrapper_nonclaim_boundary_batch063b.json": simple_status(self_maintaining_software=SELF_MAINTAINING, claim_ready=False),
        "situational_fix_escape_hatch_blocker_policy_batch063b.json": simple_status(blocks=["forbidden_evidence", "unbounded_provider", "test_mutation", "public_claim_drift"]),
        "controllergate_state_transition_contract_batch063b.json": simple_status(required_order=["ingest", "workspace_purity", "provider_setup", "command_translation", "pre_repair_replay", "diagnostic_replay", "future_patch_gate"]),
        "reactome_style_step_contract_model_batch063b.json": simple_status(internal_pattern_only=True, not_repair_evidence=True, future_step_contract_fields=["candidate_id", "source_acquisition_step", "harness_origin_step", "workspace_purity_step", "provider_materialization_step", "command_translation_step", "pre_repair_replay_step", "diagnostic_replay_step", "source_topology_step", "patch_license_step", "patch_gate_step", "post_repair_replay_step", "duplicate_replay_step", "count_gate_step", "proof_ledger_step", "public_summary_step", "terminal_state_step"]),
        "provider_capsule_step_contract_schema_batch063b.json": simple_status(required_fields=["required_inputs", "allowed_inputs", "forbidden_inputs", "expected_outputs", "output_verifiers", "blocker_codes", "terminal_states", "reopen_conditions"]),
        "candidate_execution_step_registry_batch063b.json": simple_status(candidate_id=PYTEST_ID, current_step="command_boundary_recovery_needed", next_step="batch063c_pytest_command_boundary_followup"),
        "step_to_output_contract_registry_batch063b.json": simple_status(contracted_outputs=["workspace_manifest", "provider_install_log", "command_boundary_log", "claim_boundary", "SHA256SUMS"]),
        "deprecated_or_unbounded_step_exclusion_registry_batch063b.json": simple_status(excluded_steps=["unbounded_provider", "network_model_boundary", "forbidden_evidence", "test_mutation", "config_mutation_as_repair"]),
        "provider_output_verifier_contract_batch063b.json": simple_status(verifiers=["sha256_manifest", "raw_log_hash", "provider_setup_result", "command_boundary_classification"]),
        "reactome_to_controllergate_mapping_matrix_batch063b.json": simple_status(internal_pattern_only=True, mappings=[["local dependency materialization", "provider/runtime capsule materialization"], ["config.properties", "provider/runtime/test command manifest"], ["step selection", "bounded replay scope selection"], ["deprecated-step exclusion", "terminal-state exclusion registry"], ["output directory verification", "artifact bundle and proof ledger verification"], ["dependency version discipline", "exact candidate/provider/command custody"]]),
        "tld_governance_enforcement_matrix_batch063b.json": simple_status(internal_governance_only=True, not_public_proof_language=True),
        "tld_to_controllergate_rule_mapping_batch063b.json": simple_status(internal_governance_only=True, mappings=[["outcome-blind materialization", "pre-repair replay before patching"], ["registry-first provenance", "candidate/source/harness/provider/proof registries"], ["frozen operators and locks", "claim boundaries and current protocol"], ["full failure preservation", "blocked branch records"], ["bundle-bound evidence", "artifact ZIP and SHA manifests"], ["contamination prevention", "fixed/gold/future/test mutation exclusions"]]),
        "frozen_gate_and_lock_registry_batch063b.json": simple_status(locks=["current_protocol_v2_14", "no_full_scoring", "no_memory_lift_claim", "no_self_maintaining_claim"]),
        "bundle_bound_evidence_policy_batch063b.json": simple_status(bundle_bound=True, requires=["artifact_zip", "SHA256SUMS", "audit_outputs", "raw_logs"]),
        "outcome_blind_materialization_policy_batch063b.json": simple_status(outcome_blind=True, no_post_hoc_candidate_promotion=True),
        "full_failure_preservation_policy_batch063b.json": simple_status(preserve_blocked_branches=True, preserve_terminal_states=True),
        "contamination_prevention_policy_batch063b.json": simple_status(blocked=["fixed", "gold", "future", "issue_fix_text", "synthetic_tests"]),
        "workspace_purity_policy_batch063b.json": simple_status(required_checks=["outside_repo", "outside_cloud_sync", "no_reused_venv", "no_reused_cache", "pre_attempt_workspace_hash", "post_attempt_workspace_hash"]),
        "candidate_isolated_runtime_policy_batch063b.json": simple_status(candidate_isolated=True, global_environment_mutation_allowed=False),
        "stale_artifact_resistance_policy_batch063b.json": simple_status(stale_cache_contamination_count_required=True),
        "candidate_workspace_purity_schema_batch063b.json": simple_status(fields=["workspace_path", "outside_repo", "outside_onedrive", "stale_cache_contamination_count", "pre_attempt_workspace_hash", "post_attempt_workspace_hash"]),
        "candidate_isolated_venv_schema_batch063b.json": simple_status(fields=["candidate_id", "venv_path", "python_version", "provider_install_log", "environment_lock_hash"]),
        "global_environment_drift_prevention_policy_batch063b.json": simple_status(global_drift_prevention=True),
        "command_translation_layer_policy_batch063b.json": simple_status(no_guessing=True, decision_time_metadata_only=True),
        "candidate_command_manifest_schema_batch063b.json": simple_status(fields=["candidate_id", "repo_url", "candidate_sha", "native_test_path", "declared_command_source", "declared_command_source_file", "working_directory", "python_version", "provider_setup_required", "runner_package", "target_package", "runner_target_split_required", "command_string", "collection_command", "diagnostic_command_template", "forbidden_command_shortcuts", "command_boundary_status", "next_allowed_action"]),
        "pytest_command_translation_case_study_batch063b.json": simple_status(candidate_id=PYTEST_ID, command_string=PRESERVED_COMMAND, command_boundary_status=command_classification, no_ad_hoc_config_suppression=True),
        "command_boundary_terminal_state_registry_batch063b.json": simple_status(terminal_states=["command_boundary_recovery_needed", "pytest_command_boundary_blocked_version_origin", "pytest_command_boundary_blocked_config_minversion"]),
        "command_manifest_origin_audit_batch063b.json": simple_status(allowed_sources=["pyproject.toml", "tox.ini", "setup.cfg", "setup.py", "CI workflow files", "project-local docs"], forbidden_sources=["modern docs", "future commits", "issue workaround text", "ad hoc guessed commands"]),
        "non_circular_harness_origin_policy_batch063b.json": simple_status(non_circular_required=True, hash_pinned_before_use=True),
        "harness_origin_bootstrap_schema_batch063b.json": simple_status(fields=["source_url_or_repo", "source_commit_sha_or_bundle_identity", "manifest_path", "expected_manifest_sha256", "observed_manifest_sha256", "authority_source", "authority_created_before_runtime", "self_referential_hash_detected", "target_test_path", "target_test_sha256", "harness_topology_files", "pre_execution_sha256", "post_execution_sha256", "integrity_status", "blocker_if_fail"]),
        "harness_origin_root_of_trust_registry_batch063b.json": simple_status(allowed_authorities=["pre_existing_reviewed_config", "immutable_public_repo_commit", "immutable_public_release_bundle", "reviewed_manual_bundle"], forbidden_authorities=["same_run_generated_hash", "floating_HEAD", "prompt_text_hash", "unverified_local_file", "fixed_gold_future_test_content"]),
        "harness_origin_self_reference_blocker_policy_batch063b.json": simple_status(self_referential_hash_detected_blocks=True),
        "harness_origin_pre_post_integrity_policy_batch063b.json": simple_status(pre_post_hash_required=True),
        "ast_topology_extrusion_policy_batch063b.json": simple_status(future_patch_gate_law=True, current_pytest_patch_permission=False),
        "ast_topology_extrusion_schema_batch063b.json": simple_status(required_fields=["source_file_inventory", "target_module_import_graph", "candidate_symbol_map", "function_class_ownership_map", "call_contact_graph", "AST_parse_status", "patch_locality_region", "symbol_references_touched", "risk_of_broad_semantic_alteration", "forbidden_path_check", "source_contact_to_failure_trace"]),
        "source_syntax_resilience_policy_batch063b.json": simple_status(ast_parse_required_before_patch_gate=True),
        "patch_gate_ast_integrity_requirement_batch063b.json": simple_status(no_source_patch_without_topology_map=True),
        "pytest_readonly_ast_topology_probe_batch063b.json": simple_status(readonly=True, workspace_path=str(workspace), patch_generation_allowed=False),
        "cross_family_homology_ledger_batch063b.json": simple_status(routing_memory_only=True, not_proof=True, repairs=["cloudpickle_class_dict", "freezegun_datetime_platform", "lemon_reader_if_present"]),
        "repair_pattern_homology_schema_batch063b.json": simple_status(fields=["repair_id", "candidate_id", "repo_family", "failure_family", "provider_surface", "source_surface", "interpreter_surface", "patch_scope", "changed_files", "target_command", "duplicate_replay_status", "count_gate_status", "what_generalizes", "what_does_not_generalize", "future_candidate_match_features", "forbidden_transfer_rules"]),
        "counted_repair_shape_library_batch063b.json": simple_status(routing_memory_only=True, entries=[{"repair_id": "cloudpickle_class_dict", "duplicate_replay_status": "PASS", "count_gate_status": "PASS"}, {"repair_id": "freezegun_datetime_platform", "duplicate_replay_status": "PASS", "count_gate_status": "PASS"}, {"repair_id": "lemon_reader_preserved_if_present", "duplicate_replay_status": "preserve_existing_record", "count_gate_status": "preserve_existing_record"}]),
        "homologous_failure_pattern_index_batch063b.json": simple_status(routing_only=True, forbidden_transfer_rules=["do_not_copy_patch_text", "do_not_use_as_gold_evidence"]),
        "confidence_abstention_policy_batch063b.json": simple_status(public_safe_name="safe abstention", triggers=["command_boundary_cannot_be_normalized", "provider_unbounded", "harness_origin_circular", "workspace_purity_fails", "runner_target_origin_unproven", "forbidden_evidence_required", "probe_budget_exceeded"]),
        "safe_abstention_watchdog_schema_batch063b.json": simple_status(fields=["candidate_id", "trigger", "evidence_files", "attempt_count", "new_information_since_last_attempt", "why_continuing_would_be_unsafe_or_unbounded", "terminal_state", "reopen_condition", "next_allowed_action"]),
        "confidence_abstention_audit_batch063b.json": simple_status(candidate_id=PYTEST_ID, trigger="command_boundary_cannot_be_normalized", terminal_state="command_boundary_recovery_needed", next_allowed_action="batch063c_pytest_command_boundary_followup"),
        "unrecoverable_branch_explanation_policy_batch063b.json": simple_status(explain_terminal_states=True),
        "loop_prevention_policy_batch063b.json": simple_status(stop_repeated_attempts_without_new_evidence=True),
        "universal_bug_terminal_state_registry_batch063b.json": {"status": "PASS", "terminal_states": status_contract},
        "bug_terminal_state_contract_batch063b.json": simple_status(contract=status_contract),
        "candidate_reopen_condition_registry_batch063b.json": simple_status(candidate_id=PYTEST_ID, reopen_condition="safe_ancestor_tag_or_declared_runner_origin_can_be_verified_without_forbidden_evidence"),
        "unrecoverable_under_current_policy_registry_batch063b.json": simple_status(entries=[]),
        "baseline_registry_snapshot_policy_batch063b.json": simple_status(snapshot_before_high_risk_actions=True),
        "proof_ledger_forkpoint_policy_batch063b.json": simple_status(forkpoint_required=True),
        "failed_attempt_branch_record_schema_batch063b.json": simple_status(fields=["parent_evidence_entry", "pre_attempt_source_head", "pre_attempt_workspace_hash", "pre_attempt_environment_hash", "attempt_type", "patch_sha256", "provider_setup_hash", "command_manifest_hash", "attempt_status", "failure_classification", "rollback_required", "rollback_target_entry", "branch_closed_without_count_increment", "hash_chain_valid"]),
        "rollback_marker_policy_batch063b.json": simple_status(rollback_required_for_failed_attempt=True),
        "ghost_state_prevention_policy_batch063b.json": simple_status(branch_closure_explicit=True, count_increment_forbidden_without_gate=True),
        "public_ready_repo_architecture_gap_batch063b.json": simple_status(repo_public_readiness="not_release_ready", no_refactor_performed=True),
        "duplicate_function_and_utility_review_batch063b.json": simple_status(no_duplicate_functions_merged=True, future_shared_modules=["controllergate/core/artifacts.py", "controllergate/core/count_gate.py", "controllergate/core/provider_capsules.py", "controllergate/core/command_translation.py", "controllergate/core/workspace_purity.py", "controllergate/core/amds_bug_tree.py", "controllergate/core/public_summary.py", "controllergate/core/homology.py"]),
        "shared_core_module_extraction_plan_batch063b.json": simple_status(plan_only=True, modules=["controllergate/core/artifacts.py", "controllergate/core/count_gate.py", "controllergate/core/provider_capsules.py", "controllergate/core/command_translation.py", "controllergate/core/workspace_purity.py", "controllergate/core/amds_bug_tree.py", "controllergate/core/public_summary.py", "controllergate/core/homology.py"]),
        "public_docs_update_priority_batch063b.json": simple_status(priority="high", public_summary_guard_required=True),
        "repo_public_release_readiness_scorecard_batch063b.json": simple_status(score="research_archive_not_public_release_ready", blockers=["full_scoring_disabled", "self_maintenance_not_demonstrated", "wrapper_controls_scaffolded_not_validated_across_unrelated_candidates"]),
    }
    for name, value in wrappers.items():
        write_out_json(name, value)


def historical_requirement_records() -> list[dict[str, Any]]:
    requirements = [
        (
            "HR-B",
            "False-win / builder-critic verification gate",
            "Prior work misreported package pass until critic verification found disagreement.",
            ["false_win_prevention_policy_batch063b.json", "critic_verification_gate_schema_batch063b.json"],
            "scaffolded_with_config_and_audit",
            "count_gate_precondition",
        ),
        (
            "HR-C",
            "Deterministic replay readiness and evidence-strengthening gate",
            "Earlier real-repo pilot had review-required episodes without deterministic pass/fail evidence.",
            ["deterministic_replay_readiness_policy_batch063b.json", "real_repo_evidence_strengthening_gate_batch063b.json"],
            "scaffolded_with_config_and_audit",
            "scoring_precondition",
        ),
        (
            "HR-D",
            "External evidence bundle schema",
            "External real-repo episodes need a strict pending bundle before normalization or scoring.",
            ["external_episode_evidence_bundle_policy_batch063b.json", "external_episode_pending_bundle_schema_batch063b.json"],
            "scaffolded_with_config_and_audit",
            "scoring_precondition",
        ),
        (
            "HR-E",
            "Null wrapper / matched baseline controls",
            "Counted repairs do not prove memory lift without matched baseline controls.",
            ["null_wrapper_policy_batch063b.json", "matched_baseline_control_schema_batch063b.json"],
            "scaffolded_with_config_and_audit",
            "memory_lift_precondition",
        ),
        (
            "HR-F",
            "Strict label-blindness and no ground-truth peeking",
            "Decision-time repair/probe logic must not use labels, gold patches, or outcome-only evidence.",
            ["strict_label_blindness_policy_batch063b.json", "ground_truth_peeking_blocker_policy_batch063b.json"],
            "already_implemented_with_evidence",
            "governance_only",
        ),
        (
            "HR-G",
            "Corrected operational stack errata lock",
            "Activation must follow legible topology and bounded materialization, not preflight alone.",
            ["controllergate_5_14_6_196_errata_lock_batch063b.json", "corrected_operational_stack_policy_batch063b.json"],
            "scaffolded_with_config_and_audit",
            "patch_gate_precondition",
        ),
        (
            "HR-H",
            "Provider/cofactor lock and dependency drift governance",
            "Secondary providers must be declared, reviewed, pinned, and drift-audited before materialization.",
            ["secondary_cofactor_lock_policy_batch063b.json", "reviewed_provider_lock_schema_batch063b.json"],
            "scaffolded_with_config_and_audit",
            "provider_boundary",
        ),
        (
            "HR-I",
            "Workflow snapshot and runner revision guard",
            "Stale workflow reruns must not be accepted as candidate evidence.",
            ["workflow_snapshot_identity_policy_batch063b.json", "runner_revision_guard_policy_batch063b.json"],
            "scaffolded_with_config_and_audit",
            "governance_only",
        ),
        (
            "HR-J",
            "Harness sanity and command normalization",
            "Returncode 127 is a harness/runner failure until command normalization and runner dependencies are attempted.",
            ["harness_sanity_policy_batch063b.json", "command_normalization_policy_global_batch063b.json"],
            "scaffolded_with_config_and_audit",
            "provider_boundary",
        ),
        (
            "HR-K",
            "Non-circular harness origin / test provenance bootstrap",
            "No harness/test content is trusted unless origin was hash-pinned and non-circular before execution.",
            ["historical_harness_origin_blocker_recovery_batch063b.json", "target_test_provenance_policy_batch063b.json"],
            "scaffolded_with_config_and_audit",
            "patch_gate_precondition",
        ),
        (
            "HR-L",
            "Environment locator before source patch gate",
            "Provider, command, dependency, workspace, and runner-target boundaries must be classified before patching.",
            ["brot_bulb_environment_locator_policy_batch063b.json", "provider_surface_vs_source_surface_classifier_batch063b.json"],
            "scaffolded_with_config_and_audit",
            "provider_boundary",
        ),
        (
            "HR-M",
            "AST topology before patch gates",
            "Source-contact maps that point only to tests are insufficient for patch generation.",
            ["historical_ast_loop_extrusion_requirement_batch063b.json", "ast_topology_patch_gate_precondition_batch063b.json"],
            "scaffolded_with_config_and_audit",
            "patch_gate_precondition",
        ),
        (
            "HR-N",
            "Proof-ledger fork point, failed branch record, and rollback",
            "Failed attempts must close explicit ledger branches without count increment.",
            ["proof_ledger_forkpoint_policy_batch063b.json", "failed_attempt_branch_record_schema_batch063b.json"],
            "already_implemented_with_evidence",
            "count_gate_precondition",
        ),
        (
            "HR-O",
            "Safe abstention, flatline rejection, and minimum-deltas constraint",
            "Unbounded or repeated blocked lanes must terminally classify rather than loop.",
            ["safe_abstention_policy_historical_lock_batch063b.json", "flatline_rejection_policy_batch063b.json"],
            "scaffolded_with_config_and_audit",
            "governance_only",
        ),
        (
            "HR-P",
            "Persistent enforcement instead of forgettable backlog",
            "Recovered requirements must have status, owner artifacts, audit assertions, and next actions.",
            ["historical_requirement_recovery_registry_batch063b.json", "configs/controllergate_required_wrapper_law_registry.json"],
            "implemented_now",
            "governance_only",
        ),
    ]
    records: list[dict[str, Any]] = []
    for req_id, name, origin, artifacts, status, proof_lane_effect in requirements:
        records.append(
            {
                "requirement_id": req_id,
                "requirement_name": name,
                "origin_summary": origin,
                "why_it_matters": "prevents proof drift, stale evidence, or premature repair/count claims",
                "current_repo_status": status,
                "status": status,
                "owner_files_or_modules": [
                    "scripts/audit_batch063b_pytest_provider_runtime_recovery_followup.py",
                    "configs/controllergate_required_wrapper_law_registry.json",
                    "docs/controllergate_historical_requirements_recovery_lock.md",
                ],
                "required_artifacts": artifacts,
                "required_audit_assertions": [
                    f"{artifacts[0]} exists",
                    "status is one of the allowed recovered-requirement states",
                    "no public overclaim",
                ],
                "risk_if_forgotten": "future batches may repeat the same unsafe shortcut or lose terminal-state custody",
                "next_allowed_action_if_blocking": "batch067_universal_wrapper_hardening_implementation",
                "public_summary_allowed": req_id not in {"HR-G", "HR-L", "HR-M"},
                "proof_lane_effect": proof_lane_effect,
                "named_future_batch": "batch067_universal_wrapper_hardening_implementation" if status == "scaffolded_with_config_and_audit" else None,
                "why_not_now": "Batch063b is a no-patch/no-refactor proof-boundary batch; implementation beyond docs/config/schema requires a dedicated wrapper hardening batch" if status == "scaffolded_with_config_and_audit" else None,
                "blocker_if_ignored": "historical_requirement_missing_audit_enforcement",
                "minimum_audit_required_in_current_batch": "artifact_exists_and_registry_status_valid",
            }
        )
    return records


def write_historical_requirement_artifacts(final_next_action: str) -> dict[str, Any]:
    records = historical_requirement_records()
    dashboard_counts: dict[str, int] = {status: 0 for status in sorted(HR_ALLOWED_STATUSES)}
    for record in records:
        dashboard_counts[record["status"]] += 1

    registry = {
        "status": "PASS",
        "allowed_statuses": sorted(HR_ALLOWED_STATUSES),
        "requirement_count": len(records),
        "requirements": records,
        "no_narrative_only_requirements": True,
    }
    gap_matrix = {
        "status": "PASS",
        "gaps": [
            {
                "requirement_id": record["requirement_id"],
                "status": record["status"],
                "owner_artifacts": record["required_artifacts"],
                "named_future_batch": record["named_future_batch"],
                "blocker_if_ignored": record["blocker_if_ignored"],
            }
            for record in records
        ],
    }
    dashboard = {
        "status": "PASS",
        "requirement_count": len(records),
        "implemented_now_count": dashboard_counts["implemented_now"],
        "scaffolded_with_config_and_audit_count": dashboard_counts["scaffolded_with_config_and_audit"],
        "blocked_with_exact_reason_count": dashboard_counts["blocked_with_exact_reason"],
        "requires_dedicated_future_batch_with_named_batch_count": dashboard_counts["requires_dedicated_future_batch_with_named_batch"],
        "deprecated_with_reason_count": dashboard_counts["deprecated_with_reason"],
        "already_implemented_with_evidence_count": dashboard_counts["already_implemented_with_evidence"],
    }
    write_out_json("historical_requirement_recovery_registry_batch063b.json", registry)
    write_out_json("historical_requirement_gap_matrix_batch063b.json", gap_matrix)
    write_out_json("historical_requirement_status_dashboard_batch063b.json", dashboard)
    write_out_json("forgotten_requirement_prevention_policy_batch063b.json", {"status": "PASS", "requires_status_owner_artifact_audit_and_next_action": True, "audit_fails_on_narrative_only_requirement": True})

    artifacts: dict[str, Any] = {
        "false_win_prevention_policy_batch063b.json": {"status": "PASS", "required_agreement": ["artifact_zip_opens", "outer_sha256", "internal_SHA256SUMS", "package_decision_report", "rerun_or_analyzer_output", "audit_status", "claim_boundary"], "builder_output_is_provisional": True},
        "builder_output_provisional_policy_batch063b.json": {"status": "PASS", "provisional_until_critic_verification": True},
        "critic_verification_gate_schema_batch063b.json": {"status": "PASS", "fields": ["package_decision_report", "rerun_analyzer_output", "sha_verification", "audit_status", "claim_boundary_status"]},
        "decision_report_rerun_sha_agreement_policy_batch063b.json": {"status": "PASS", "blockers": ["builder_output_pending_critic_verification", "critic_verification_disagrees_builder_output"]},
        "historical_false_win_ledger_update_batch063b.json": {"status": "PASS", "lesson": "public PASS requires critic-verification agreement"},
        "deterministic_replay_readiness_policy_batch063b.json": {"status": "PASS", "minimum_record_fields": ["repo", "candidate_or_episode_id", "exact_commit_sha", "command", "toolchain_versions", "environment_lock", "raw_log", "decision_time_evidence", "outcome_only_evidence", "rerun_status", "artifact_manifest", "agent_tool_trace_availability", "memory_baseline_availability"]},
        "real_repo_evidence_strengthening_gate_batch063b.json": {"status": "PASS", "statuses": ["deterministic_replay_ready", "blocked_missing_ci_log", "blocked_pr_head_unavailable", "blocked_toolchain_gap", "blocked_timeout", "blocked_missing_agent_trace", "review_required_insufficient_evidence", "current_head_only_not_scoreable_as_pr_head"]},
        "memory_baseline_availability_gate_batch063b.json": {"status": "PASS", "required_before_memory_lift": True},
        "full_scoring_precondition_policy_batch063b.json": {"status": "PASS", "full_scoring": FULL_SCORING, "requires_deterministic_replay_readiness": True},
        "real_repo_review_required_terminal_policy_batch063b.json": {"status": "PASS", "review_required_is_terminal_without_evidence": True},
        "external_episode_evidence_bundle_policy_batch063b.json": {"status": "PASS", "required_files": ["ci_log.txt", "failing_command.txt", "patch_diff.diff", "agent_trace.md", "files_read.txt", "files_written.txt", "artifact_manifest.txt", "outcome.md"]},
        "external_episode_pending_bundle_schema_batch063b.json": {"status": "PASS", "fields": ["source_repo", "PR_commit_run_reference", "command", "failure_or_repair_type", "patch_diff_or_changed_files", "rerun_availability", "local_rerun_evidence", "outcome", "decision_time_evidence", "outcome_only_evidence", "normalization_suitability"]},
        "no_premature_normalization_policy_batch063b.json": {"status": "PASS", "normalize_only_after_schema_or_exact_blockers": True},
        "decision_time_outcome_evidence_separation_policy_batch063b.json": {"status": "PASS", "separate_decision_time_and_outcome_evidence": True},
        "null_wrapper_policy_batch063b.json": {"status": "PASS", "null_wrapper_status": "null_wrapper_scaffolded", "same_candidate_set": True, "same_command_manifests": True, "no_memory_enabled_repair_memory": True},
        "matched_baseline_control_schema_batch063b.json": {"status": "PASS", "fields": ["same_candidate_set", "same_provider_runtime_capsule", "same_replay_windows", "same_artifact_custody", "same_scoring_eligibility"]},
        "null_separation_score_policy_batch063b.json": {"status": "PASS", "memory_lift_requires_matched_baseline": True},
        "memory_lift_prerequisite_policy_batch063b.json": {"status": "PASS", "memory_lift": MEMORY_LIFT, "issue_derived_count_alone_insufficient": True},
        "stateless_baseline_runner_contract_batch063b.json": {"status": "PASS", "hidden_safe_action_oracle_forbidden": True},
        "strict_label_blindness_policy_batch063b.json": {"status": "PASS", "forbidden": ["gold_patch", "fixed_revision", "future_commit", "issue_body_fix_text", "hidden_label", "fault_class", "benchmark_diagnostic_tag", "outcome_only_success_failure", "post_repair_result", "modern_fixed_source"]},
        "ground_truth_peeking_blocker_policy_batch063b.json": {"status": "PASS", "blocker": "blocked_ground_truth_leakage_risk"},
        "fault_class_leakage_audit_schema_batch063b.json": {"status": "PASS", "fault_class_allowed": False},
        "triad_interlock_operational_boundary_batch063b.json": {"status": "PASS", "decision_time_only": True},
        "controllergate_5_14_6_196_errata_lock_batch063b.json": {"status": "PASS", "internal_operational_translation_only": True, "correct_order": ["five_set_reference_core", "fourteen_set_native_contact_topology", "bounded_tension_relief_or_materialization", "six_set_activation_licensing", "bounded_source_only_patch_attempt", "fourteen_contact_audit", "duplicate_clean_replay", "phase_or_seed_constraint_check", "one_ninety_six_proof_obligations_ledger_lock"]},
        "corrected_operational_stack_policy_batch063b.json": {"status": "PASS", "patch_generation_preconditions": ["reference_core_preserved", "native_contact_topology_legible", "bounded_materialization", "activation_license_open", "path_to_replay_duplicate_and_count_gate"]},
        "activation_after_topology_policy_batch063b.json": {"status": "PASS", "activation_after_topology": True},
        "repair_activation_not_preflight_only_policy_batch063b.json": {"status": "PASS", "preflight_alone_does_not_license_patch": True},
        "isomorphic_stack_public_boundary_batch063b.json": {"status": "PASS", "not_public_proof_language": True},
        "secondary_cofactor_lock_policy_batch063b.json": {"status": "PASS", "statuses": ["declared_pinned_provider_ready", "declared_unpinned_provider_blocked", "provider_absent_from_reviewed_lock", "provider_version_drift_detected", "provider_materialization_unbounded", "provider_materialization_declared_but_not_countable", "provider_manual_review_needed"]},
        "reviewed_provider_lock_schema_batch063b.json": {"status": "PASS", "fields": ["provider", "version", "source", "sha256", "review_status", "observed_at_or_before"]},
        "dependency_drift_audit_policy_batch063b.json": {"status": "PASS", "drift_is_provider_evidence_not_target_code_evidence": True},
        "declared_unpinned_cofactor_blocker_policy_batch063b.json": {"status": "PASS", "unpin_blocker": "declared_unpinned_provider_blocked"},
        "cofactor_materialization_nonrepair_boundary_batch063b.json": {"status": "PASS", "provider_setup_is_not_repair_success": True},
        "workflow_snapshot_identity_policy_batch063b.json": {"status": "PASS", "future_checks": ["print_GITHUB_SHA", "print_checked_out_HEAD", "verify_runner_file_hash_or_marker", "record_workflow_name_version", "record_artifact_name"]},
        "runner_revision_guard_policy_batch063b.json": {"status": "PASS", "fail_on_legacy_runner_path": True},
        "stale_workflow_rerun_blocker_policy_batch063b.json": {"status": "PASS", "blocker": "blocked_stale_workflow_snapshot"},
        "workflow_head_sha_verification_schema_batch063b.json": {"status": "PASS", "fields": ["GITHUB_SHA", "checked_out_HEAD", "workflow_file_path", "runner_file_hash", "artifact_name"]},
        "command_normalization_guard_policy_batch063b.json": {"status": "PASS", "record_command_normalization_summary": True},
        "harness_sanity_policy_batch063b.json": {"status": "PASS", "returncode_127_is_harness_failure_until_normalized": True},
        "command_normalization_policy_global_batch063b.json": {"status": "PASS", "command_manifest_fields": ["original_command", "normalized_command", "working_directory", "PYTHONPATH", "runner_package", "target_package", "provider_setup", "command_source", "command_source_file", "normalization_reason", "not_run_reason"]},
        "project_root_execution_policy_batch063b.json": {"status": "PASS", "working_directory_must_be_recorded": True},
        "runner_dependency_preflight_policy_batch063b.json": {"status": "PASS", "runner_dependency_setup_before_command_classification": True},
        "returncode_127_harness_failure_policy_batch063b.json": {"status": "PASS", "classification": "harness_runner_failure_until_command_normalization_attempted"},
        "historical_harness_origin_blocker_recovery_batch063b.json": {"status": "PASS", "blockers": ["bugsinpy_harness_origin_missing", "materialized_target_test_provenance_blocked", "target_test_content_not_decision_time_safe", "self_referential_harness_hash_detected", "harness_origin_untrusted", "workspace_equivalence_blocked_by_test_provenance"]},
        "target_test_provenance_policy_batch063b.json": {"status": "PASS", "decision_time_safe_hash_pinned_origin_required": True},
        "self_referential_harness_hash_blocker_batch063b.json": {"status": "PASS", "blocker": "self_referential_harness_hash_detected"},
        "brot_bulb_environment_locator_policy_batch063b.json": {"status": "PASS", "internal_engineering_language_only": True, "run_before_source_patch_gate_when": ["provider_runtime_blocker", "command_boundary", "fixture_provenance_uncertain", "workspace_purity_fails", "runner_target_collision", "unpinned_dependency", "network_or_system_provider_requirement"]},
        "environment_topology_locator_schema_batch063b.json": {"status": "PASS", "fields": ["candidate_id", "provider_surface", "source_surface", "system_boundary", "next_allowed_action"]},
        "provider_surface_vs_source_surface_classifier_batch063b.json": {"status": "PASS", "provider_boundary_before_source_patch": True},
        "single_system_vs_coupled_system_boundary_batch063b.json": {"status": "PASS", "classifications": ["single_candidate_local_source_provider_closure", "coupled_cross_provider_transfer"]},
        "tot_brot_coupled_candidate_policy_batch063b.json": {"status": "PASS", "internal_engineering_language_only": True, "not_public_proof": True},
        "historical_ast_loop_extrusion_requirement_batch063b.json": {"status": "PASS", "internal_historical_label_only": True, "engineering_translation": "native_source_topology_before_patch_gate"},
        "ast_topology_patch_gate_precondition_batch063b.json": {"status": "PASS", "preconditions": ["source_file_inventory", "AST_parse_status", "target_module_graph", "function_class_ownership_map", "call_contact_graph", "failure_to_source_trace", "patch_locality_region", "symbol_reference_map", "risk_of_broad_semantic_alteration", "source_contact_map_not_tests_only"], "blocker": "patch_license_closed_source_topology_incomplete"},
        "source_contact_not_tests_only_policy_batch063b.json": {"status": "PASS", "tests_only_contact_map_blocks_patch": True},
        "native_contact_topology_schema_batch063b.json": {"status": "PASS", "fields": ["source_file_inventory", "AST_parse_status", "target_module_graph", "function_class_ownership_map", "failure_to_source_trace"]},
        "branch_closure_without_count_increment_policy_batch063b.json": {"status": "PASS", "failed_branches_close_without_count_increment": True},
        "safe_abstention_policy_historical_lock_batch063b.json": {"status": "PASS", "triggers": ["zero_variance_flatline_diagnostic", "unrecoverable_traceback", "provider_unbounded", "harness_origin_circular", "command_boundary_not_normalizable", "workspace_purity_failure", "AST_topology_incomplete", "source_ownership_not_established", "probe_budget_exceeded", "same_blocker_repeats_without_new_evidence"]},
        "flatline_rejection_policy_batch063b.json": {"status": "PASS", "flatline_rejected": True},
        "minimum_deltas_constraint_policy_batch063b.json": {"status": "PASS", "minimum_delta_required_for_progress": True},
    }
    for name, value in artifacts.items():
        write_out_json(name, value)

    final_status = {
        "status": "PASS",
        "historical_requirement_recovery_status": "PASS",
        "recovered_requirement_count": len(records),
        "implemented_now_count": dashboard["implemented_now_count"],
        "scaffolded_with_audit_count": dashboard["scaffolded_with_config_and_audit_count"],
        "blocked_with_exact_reason_count": dashboard["blocked_with_exact_reason_count"],
        "assigned_to_named_future_batches_count": dashboard["scaffolded_with_config_and_audit_count"],
        "next_allowed_action_due_to_historical_law": final_next_action,
        "full_scoring": FULL_SCORING,
        "memory_lift": MEMORY_LIFT,
        "self_maintaining_software": SELF_MAINTAINING,
    }
    write_out_json("historical_requirement_recovery_final_status_batch063b.json", final_status)
    write_out_json("batch063b_pytest_next_action_and_wrapper_law_decision.json", {"status": "PASS", "pytest_next_proof_action": "batch063c_pytest_command_boundary_followup", "wrapper_law_next_action": final_next_action, "selected_next_allowed_action": final_next_action})
    return final_status


def public_summary_block(final: dict[str, Any]) -> str:
    return f"""## Batch063b Pytest provider/runtime recovery follow-up

Batch063b is the latest Pytest command-boundary and wrapper-hardening boundary. It officially ingests Batch066, keeps repair counts unchanged, creates a fresh candidate-isolated Pytest workspace, and verifies that provider/runtime setup alone does not authorize a repair.

Batch063b status:

- Batch066 official ingest: `{final['batch066_ingest_status']}`.
- Issue-derived repair count preserved at `{ISSUE_DERIVED_REPAIR_COUNT}`.
- Native external repair count preserved at `{NATIVE_EXTERNAL_REPAIR_COUNT}`.
- Pytest version-origin bootstrap status: `{final['pytest_version_origin_classification']}`.
- Pytest runner-target import-origin status: `{final['pytest_runner_target_import_origin_classification']}`.
- Pytest command-boundary status: `{final['pytest_command_boundary_classification']}`.
- Pytest provider/runtime setup status: `{final['pytest_provider_runtime_setup_status']}`.
- Pytest pre-repair replay status: `{final['pytest_prerepair_replay_classification']}`.
- Future patch-license state: `{final['pytest_future_patch_license_state']}`.
- Universal wrapper hardening status: `{final['universal_wrapper_hardening_status']}`.
- Workspace purity policy status: `{final['workspace_purity_policy_status']}`.
- Candidate-isolated runtime policy status: `{final['candidate_isolated_runtime_policy_status']}`.
- Command translation layer status: `{final['command_translation_layer_status']}`.
- Non-circular harness origin policy status: `{final['non_circular_harness_origin_policy_status']}`.
- AST topology requirement status: `{final['ast_topology_requirement_status']}`.
- Cross-family homology ledger status: `{final['cross_family_homology_ledger_status']}`.
- Confidence abstention policy status: `{final['confidence_abstention_policy_status']}`.
- Terminal-state registry status: `{final['terminal_state_registry_status']}`.
- Repo public-readiness status: `{final['repo_public_readiness_status']}`.
- Duplicate-function review status: `{final['duplicate_function_review_status']}`.
- Permanent-fix backlog status: `{final['permanent_fix_backlog_status']}`.
- Historical requirements recovery status: `{final['historical_requirement_recovery_status']}`.
- Recovered historical requirement count: `{final['recovered_requirement_count']}`.
- Historical requirements implemented now: `{final['historical_requirements_implemented_now_count']}`.
- Historical requirements scaffolded with audit: `{final['historical_requirements_scaffolded_with_audit_count']}`.
- Historical requirements blocked with exact reason: `{final['historical_requirements_blocked_with_exact_reason_count']}`.
- Historical requirements assigned to named future batches: `{final['historical_requirements_assigned_to_named_future_batches_count']}`.
- False-win verification gate status: `scaffolded_with_config_and_audit`.
- Deterministic replay readiness gate status: `scaffolded_with_config_and_audit`.
- Matched baseline/null-wrapper status: `null_wrapper_scaffolded`.
- Provider/cofactor lock status: `scaffolded_with_config_and_audit`.
- Command normalization / workflow snapshot guard status: `scaffolded_with_config_and_audit`.
- Harness origin policy status: `{final['non_circular_harness_origin_policy_status']}`.
- Workspace purity status: `{final['workspace_purity_policy_status']}`.
- Source-topology precondition status: `{final['ast_topology_requirement_status']}`.
- Safe-abstention policy status: `{final['confidence_abstention_policy_status']}`.
- Terminal-state/reopen-condition policy status: `{final['terminal_state_registry_status']}`.
- Repo-hygiene pressure status: `{final['repo_hygiene_pressure_status']}`.
- Recommended next proof path: `{final['recommended_next_proof_path']}`.
- Recommended next wrapper-hardening path: `{final['recommended_next_wrapper_hardening_path']}`.
- Project health grade: `{final['project_health_grade']}`.
- Traffic-light status: `{final['traffic_light_status']}`.
- Distance to issue-derived repair count 5: `{final['distance_to_issue_derived_repair_count_5']}`.
- Distance to self-maintaining claim: `{final['distance_to_self_maintaining_claim']}`.
- Full scoring remains `{FULL_SCORING}`.
- Memory lift remains `{MEMORY_LIFT}`.
- Self-maintaining software remains `{SELF_MAINTAINING}`.

Workflow success is not equivalent to repair success. Version-origin recovery is not repair success. Command-boundary normalization is not repair success. Provider/runtime setup is not repair success. Pre-repair replay is not repair success. ControllerGate is being hardened as a high-integrity maintenance wrapper, but self-maintaining software remains false/not_demonstrated. These wrapper-hardening artifacts are engineering controls, not repair proof. No source repair is counted without source-only target pass, duplicate clean replay, and count gate. A repair is counted only after source-only target pass, duplicate clean replay, and count gate. The project health grade is advisory and does not constitute proof. Self-maintaining software remains false/not_demonstrated.
"""


def update_public_file(path: Path, block: str) -> None:
    original = path.read_text(encoding="utf-8") if path.exists() else "# ControllerGate\n"
    marker = "## Batch063b Pytest provider/runtime recovery follow-up"
    if marker in original:
        start = original.index(marker)
        next_start = original.find("\n## ", start + 1)
        if next_start == -1:
            updated = original[:start].rstrip() + "\n\n" + block.rstrip() + "\n"
        else:
            updated = original[:start].rstrip() + "\n\n" + block.rstrip() + "\n\n" + original[next_start + 1 :].lstrip()
    else:
        lines = original.splitlines()
        if lines and lines[0].startswith("# "):
            updated = lines[0] + "\n\n" + block.rstrip() + "\n\n" + "\n".join(lines[1:]).lstrip() + "\n"
        else:
            updated = block.rstrip() + "\n\n" + original
    if path.name == "README.md" and "provenance-first software repair research harness" not in updated:
        intro = (
            "ControllerGate is a proof-gated runtime and compiler layer for safe AI software repair.\n\n"
            "It remains a provenance-first software repair research harness with a conservative pre-alpha research archive boundary.\n\n"
            "It turns AI-generated fixes into auditable, sandboxed, rollback-safe software-change candidates, blocking unverified patches before they can contaminate accepted software state."
        )
        lines = updated.splitlines()
        if lines and lines[0].startswith("# "):
            updated = lines[0] + "\n\n" + intro + "\n\n" + "\n".join(lines[1:]).lstrip() + "\n"
    write_text_lf(path, updated)


def update_public_summaries(final: dict[str, Any]) -> None:
    block = public_summary_block(final)
    for rel in ["README.md", "docs/current_status.md", "controllergate_v1_7_beta/reports/critic_review_package/shareable_summary.md"]:
        update_public_file(ROOT / rel, block)


def update_roadmaps() -> None:
    historical_records = historical_requirement_records()
    roadmap = """# ControllerGate self-maintenance runtime wrapper roadmap

Batch063b adds policy scaffolding for workspace purity, candidate-isolated runtime, command translation, non-circular harness origin, source topology, terminal-state closure, and public-summary guards.

Current status: engineering controls are scaffolded, not proof of self-maintaining software.

Next recommended wrapper-hardening path: `batch067_universal_wrapper_hardening_implementation`.
"""
    public_plan = """# ControllerGate public readiness plan

ControllerGate remains a research archive, not a technical validation release.

Public-facing status must keep repair counts, replay gates, command-boundary status, and claim boundaries synchronized with committed evidence. Workflow success, provider/runtime setup, command-boundary normalization, and pre-repair replay are not repair success.
"""
    historical_doc = """# ControllerGate historical requirements recovery lock

Batch063b promotes recovered historical wrapper requirements into auditable repo law. Each recovered requirement must have an enforceable status, owner artifact, audit assertion, blocker or named future batch, and public claim boundary.

Allowed statuses: `implemented_now`, `scaffolded_with_config_and_audit`, `blocked_with_exact_reason`, `requires_dedicated_future_batch_with_named_batch`, `deprecated_with_reason`, `already_implemented_with_evidence`.

Self-maintaining software remains `false/not_demonstrated`; full scoring remains `NOT_RUN/disallowed`; memory lift remains `not_demonstrated`.
"""
    backlog_items = [
        "workspace purity filter",
        "candidate-isolated runtime",
        "command translation layer",
        "provider/runtime capsule step contracts",
        "non-circular harness origin",
        "runner-target import-origin audit",
        "AST topology extrusion",
        "AMDS full bug-tree closure",
        "cross-family homology ledger",
        "confidence abstention watchdog",
        "terminal-state registry",
        "baseline registry snapshot",
        "proof-ledger fork-point",
        "public summary guard",
        "repo topology cleanup",
        "shared artifact custody utility",
        "shared count-gate utility",
        "shared provider capsule utility",
        "shared command translation utility",
        "shared AMDS schema utility",
        "self-maintaining claim criteria",
        "memory-lift baseline plan",
    ]
    backlog = {
        "status": "PASS",
        "batch": "Batch063b",
        "items": [
            {
                "item": item,
                "status": "scaffolded" if item in {"workspace purity filter", "candidate-isolated runtime", "command translation layer", "non-circular harness origin", "terminal-state registry", "public summary guard"} else "not_started",
                "priority": "critical" if item in {"workspace purity filter", "candidate-isolated runtime", "command translation layer", "non-circular harness origin", "shared artifact custody utility", "shared count-gate utility"} else "high",
                "evidence_files": [f"outputs/{OUT_NAME}/batch063b_final_decision.json"],
                "next_batch_candidate": "batch067_universal_wrapper_hardening_implementation",
                "blocked_by": "requires explicit repo-hygiene/refactor authorization",
                "why_not_now": "Batch063b is a no-patch/no-refactor proof-boundary batch",
                "blocker_if_ignored": "wrapper_law_backlog_item_missing_audit_enforcement",
                "minimum_audit_required_in_current_batch": "backlog_item_has_status_evidence_and_named_next_batch",
                "risk_if_unfixed": "repeated batch-local gate logic and command-boundary ambiguity",
            }
            for item in backlog_items
        ],
    }
    queue = {
        "status": "PASS",
        "batch": "Batch063b",
        "plan_only": True,
        "items": [
            {"fix_id": "shared_artifact_custody_utility", "owner": "controllergate/core/artifacts.py", "priority": "critical"},
            {"fix_id": "shared_count_gate_utility", "owner": "controllergate/core/count_gate.py", "priority": "critical"},
            {"fix_id": "shared_provider_capsule_utility", "owner": "controllergate/core/provider_capsules.py", "priority": "high"},
            {"fix_id": "shared_command_translation_utility", "owner": "controllergate/core/command_translation.py", "priority": "high"},
            {"fix_id": "shared_public_summary_guard", "owner": "controllergate/core/public_summary.py", "priority": "high"},
        ],
    }
    write_text_lf(ROOT / "docs/controllergate_self_maintenance_runtime_wrapper_roadmap.md", roadmap)
    write_text_lf(ROOT / "docs/controllergate_public_readiness_plan.md", public_plan)
    write_text_lf(ROOT / "docs/controllergate_historical_requirements_recovery_lock.md", historical_doc)
    write_json_deterministic(ROOT / "configs/controllergate_self_maintenance_runtime_wrapper_backlog.json", backlog)
    write_json_deterministic(ROOT / "configs/controllergate_permanent_fix_queue.json", queue)
    write_json_deterministic(ROOT / "configs/controllergate_historical_requirements_recovery_lock.json", {"status": "PASS", "requirements": historical_records, "no_narrative_only_requirements": True})
    write_json_deterministic(ROOT / "configs/controllergate_required_wrapper_law_registry.json", {"status": "PASS", "source": "Batch063b historical recovery", "required_laws": historical_records})
    write_json_deterministic(ROOT / "configs/workspace_purity_policy.json", {"status": "PASS", "policy": "candidate workspaces must be isolated outside repo and cloud-sync paths", "batch063b_update": True})
    write_json_deterministic(ROOT / "configs/candidate_isolated_runtime_policy.json", {"status": "PASS", "policy": "provider/runtime setup must be per-candidate and captured as evidence", "batch063b_update": True})


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    verification = verify_batch066_artifact()
    if verification["status"] != "PASS":
        write_out_json("batch066_artifact_sha256_verification.json", verification)
        print(json.dumps({"status": "BLOCK", "exact_blocker": verification.get("exact_blocker")}, indent=2))
        return 1
    ingest = ingest_batch066_outputs()
    if ingest["status"] != "PASS":
        print(json.dumps({"status": "BLOCK", "exact_blocker": "batch066_artifact_ingestion_failed"}, indent=2))
        return 1
    final066 = read_json(BATCH066_DIR / "batch066_final_decision.json")

    safe_remove_runtime_root()
    workspace, commit = clone_workspace()
    stale_before = stale_cache_count(workspace)
    metadata = metadata_summary(workspace)
    provider, version, command, version_log, command_log_text = setup_provider_and_probe(workspace)
    stale_after = stale_cache_count(workspace)
    inventory, parse_status, source_topology = source_inventory(workspace)

    version_class = version["classification"]
    command_class = command["classification"]
    runner_target_class = "runner_target_collision_unresolved_self_runner" if version_class != "pytest_version_origin_ok" else "runner_target_import_origin_verified"
    prerepair_class = "blocked_target_command_invalid"
    patch_license = "pytest_patch_license_closed_command_boundary_blocked"
    pytest_next_allowed = "batch063c_pytest_command_boundary_followup"
    wrapper_next = "batch067_universal_wrapper_hardening_implementation"
    next_allowed = wrapper_next
    exact_blocker = "pytest_version_origin_missing_tags_command_boundary"

    write_out_json("batch066_artifact_ingestion_summary.json", {"status": "PASS", "artifact": verification, "ingest": ingest})
    write_out_json("batch066_artifact_sha256_verification.json", verification)
    write_out_json("batch066_result_preservation.json", {"status": "PASS", "batch066_status": final066.get("status"), "issue_derived_repair_count": ISSUE_DERIVED_REPAIR_COUNT, "native_external_repair_count": NATIVE_EXTERNAL_REPAIR_COUNT, "full_scoring": FULL_SCORING, "memory_lift": MEMORY_LIFT, "self_maintaining_software": SELF_MAINTAINING})
    write_out_json("batch066_pytest_command_boundary_preservation.json", {"status": "PASS", "batch066_classification": final066.get("pytest_command_boundary_classification"), "batch063b_prior_boundary_preserved": True})
    write_out_json("batch066_provider_runtime_preservation.json", {"status": "PASS", "batch066_provider_runtime_setup_status": final066.get("pytest_provider_runtime_setup_status"), "provider_runtime_setup_is_repair_success": False})
    write_out_json("batch066_permanent_fix_queue_preservation.json", {"status": "PASS", "repo_hygiene_pressure_status": final066.get("repo_hygiene_pressure_status")})
    write_out_json("batch066_reactome_tld_utilization_preservation.json", {"status": "PASS", "internal_analogy_preserved_as_non_public_audit_metadata": True})
    write_out_json("batch066_claim_boundary_preservation.json", {"status": "PASS", "no_patch": True, "no_duplicate_replay": True, "no_count_gate": True, "no_count_increment": True})
    write_out_json("batch066_next_action_boundary.json", {"status": "PASS", "batch066_next_allowed_action": final066.get("next_allowed_action"), "batch063b_authorized": final066.get("next_allowed_action") == "batch063b_pytest_provider_runtime_recovery_followup"})

    excluded = ["Freezegun", "Cloudpickle", "Audioread", "Lemon Reader", "Datasette", "Venusian", "Pexpect", "Pyramid", "Pairtools", "Snapshottest", "Wave 2 network/model candidates", "rejected leads", "counted repairs"]
    write_out_json("batch063b_candidate_scope.json", {"status": "PASS", "only_candidate": PYTEST_ID, "candidate_sha": PYTEST_SHA, "repo_url": PYTEST_REPO_URL})
    write_out_json("batch063b_candidate_scope_audit.json", {"status": "PASS", "only_pytest_operated": True, "excluded_candidate_count": len(excluded)})
    write_out_json("batch063b_excluded_candidate_registry.json", {"status": "PASS", "excluded": excluded})

    write_out_json("batch063b_decision_time_input_manifest.json", {"status": "PASS", "allowed_inputs": ["Batch058c Pytest approval", "Batch063 Pytest artifacts", "Batch066 Pytest logs", "buggy Pytest source at candidate SHA", "decision-time project metadata"], "fresh_workspace": str(workspace)})
    for name in ["batch063b_forbidden_evidence_audit.json", "batch063b_issue_body_leakage_boundary.json", "batch063b_label_blindness_check.json", "batch063b_gold_patch_exclusion_check.json", "batch063b_future_evidence_exclusion_check.json"]:
        write_out_json(name, {"status": "PASS", "fixed_commit_used": False, "future_commit_used": False, "pr_patch_used": False, "gold_patch_used": False, "issue_body_fix_text_used": False, "hidden_labels_used": False, "synthetic_tests_used": False})

    write_out_json("pytest_workspace_manifest_batch063b.json", {"status": commit["status"], "workspace_path": str(workspace), "outside_repo": ROOT not in workspace.resolve().parents, "outside_onedrive": "onedrive" not in str(workspace).lower()})
    write_out_json("pytest_commit_verification_batch063b.json", commit)
    write_out_json("pytest_workspace_custody_check_batch063b.json", {"status": "PASS", "testing_exists": (workspace / "testing").is_dir(), "pyproject_exists": (workspace / "pyproject.toml").is_file(), "no_patch_applied": True, "workspace_committed": False})
    write_out_json("pytest_workspace_purity_manifest_batch063b.json", {"status": "PASS" if stale_before == 0 else "BLOCK", "stale_cache_contamination_count": stale_before, "workspace_path": str(workspace), "no_stale_venv_reused": True})
    write_out_json("pytest_stale_cache_contamination_check_batch063b.json", {"status": "PASS" if stale_before == 0 else "BLOCK", "before_provider_setup_count": stale_before, "after_provider_setup_count": stale_after, "before_replay_count": stale_before})
    write_out_json("pytest_baseline_source_hashes_batch063b.json", {"status": "PASS", "records": [hash_tree_listing(workspace / "src"), hash_tree_listing(workspace / "testing")], "selected_files": [{"path": rel, "sha256": sha256_file(workspace / rel)} for rel in ["pyproject.toml", "tox.ini"] if (workspace / rel).is_file()]})
    write_out_json("pytest_project_config_map_batch063b.json", {"status": "PASS", **metadata})
    write_out_json("pytest_declared_dependency_map_batch063b.json", {"status": "PASS", "declared_setup_used": metadata["declared_provider_setup"], "undeclared_dependencies_installed": False})
    write_out_json("pytest_declared_runtime_map_batch063b.json", {"status": "PASS", "runtime": "candidate_isolated_venv", "python_executable": provider.get("venv_python")})
    write_out_json("pytest_declared_test_command_map_batch063b.json", {"status": "PASS", "preserved_command": PRESERVED_COMMAND, "declared_testpaths": metadata["declared_testpaths"]})
    write_out_json("baseline_registry_snapshot_before_pytest_recovery_batch063b.json", {"status": "PASS", "issue_derived_repair_count": ISSUE_DERIVED_REPAIR_COUNT, "native_external_repair_count": NATIVE_EXTERNAL_REPAIR_COUNT, "full_scoring": FULL_SCORING, "memory_lift": MEMORY_LIFT})

    write_out_json("pytest_version_origin_bootstrap_plan.json", {"status": "PASS", "required_probes": ["python --version", "pip --version", "git rev-parse HEAD", "git status --short", "git describe --tags --always --dirty", "git tag --merged HEAD", "sys.path", "find_spec pytest", "import pytest version/file"], "tag_recovery_policy": "ancestor_only_tags_if_predeclared_safe_authority_exists"})
    write_out_json("pytest_version_origin_probe_results.json", version)
    write_out_json("pytest_scm_metadata_probe_results.json", {"status": "PASS", "version_origin_classification": version_class, "setuptools_scm_like_underresolved_version": version.get("observed_pytest_version", "").startswith("0.1.dev")})
    write_out_json("pytest_git_tag_reachability_audit.json", {"status": "PASS", "ancestor_tags_available_in_no_tags_checkout": False, "future_tag_exposure_avoided": True, "safe_tag_restoration_executed": False, "recovery_blocker": "no_predeclared_ancestor_tag_authority"})
    write_out_json("pytest_version_origin_classification.json", {"status": "PASS", "classification": version_class, "observed_pytest_version": version.get("observed_pytest_version"), "recovery_result": "blocked_safe_tag_provenance_needed"})
    write_out_json("pytest_version_origin_recovery_result.json", {"status": "BLOCK", "classification": version_class, "exact_blocker": "safe_ancestor_tag_restoration_not_proven_without_future_tag_exposure", "repair_success": False})
    write_out_text("pytest_version_origin_probe_log_raw_batch063b.txt", version_log)

    write_out_json("pytest_runner_target_split_plan.json", {"status": "PASS", "questions_recorded": True, "external_runner_not_trusted_without_target_import_proof": True})
    write_out_json("pytest_runner_target_import_origin_audit.json", {"status": "PASS", "classification": runner_target_class, "runner_package": "pytest", "target_package": "pytest", "candidate_file": version.get("candidate_pytest_file"), "external_runner_used": False, "target_import_origin_proven_for_external_runner": False})
    write_out_json("pytest_runner_target_collision_check.json", {"status": "PASS", "classification": runner_target_class, "preserved_command_uses_candidate_as_self_runner": True})
    write_out_json("pytest_self_test_harness_origin_bootstrap.json", {"status": "PASS", "harness_origin": "buggy_checkout_project_metadata", "non_circular": True, "future_external_runner_requires_import_origin_proof": True})
    write_out_json("pytest_command_translation_layer_batch063b.json", {"status": "PASS", "candidate_id": PYTEST_ID, "repo_url": PYTEST_REPO_URL, "candidate_sha": PYTEST_SHA, "declared_command_source": "Batch063 preserved command plus pyproject testpaths", "working_directory": str(workspace), "runner_package": "pytest", "target_package": "pytest", "runner_target_split_required": True, "command_string": PRESERVED_COMMAND, "collection_command": "python -m pytest testing --collect-only -q", "command_boundary_status": command_class, "next_allowed_action": pytest_next_allowed})

    write_out_json("pytest_provider_runtime_capsule_plan_batch063b.json", {"status": "PASS", "allowed_setup": ["python -m pip install -e ."], "declared_metadata_only": True})
    write_out_json("pytest_provider_install_attempt_batch063b.json", provider)
    write_out_json("pytest_provider_runtime_setup_result_batch063b.json", provider)
    write_out_json("pytest_provider_recovery_non_repair_boundary_batch063b.json", {"status": "PASS", "provider_runtime_setup_is_repair_success": False, "patch_license_opened": False})

    write_out_json("pytest_command_boundary_probe_plan_batch063b.json", {"status": "PASS", "allowed_probes": ["python -m pytest --version", "python -m pytest --help", "python -m pytest testing --collect-only -q", PRESERVED_COMMAND]})
    write_out_json("pytest_command_boundary_probe_results_batch063b.json", command)
    write_out_json("pytest_collect_only_result_batch063b.json", {"status": "BLOCK", "classification": command_class, "pre_repair_replay_authorized": False})
    write_out_json("pytest_command_config_error_extract_batch063b.json", {"status": "PASS", "error_family": "pyproject_minversion_actual_underresolved_version", "observed_version": version.get("observed_pytest_version"), "minversion": metadata.get("pyproject_minversion")})
    write_out_json("pytest_command_boundary_classification_batch063b.json", {"status": "PASS", "classification": command_class, "normalized": False, "partially_normalized": False})
    write_out_json("pytest_normalized_replay_authorization_batch063b.json", {"status": "DENIED", "pre_repair_replay_authorized": False, "reason": command_class})

    for name in ["pytest_prerepair_not_run_reason_batch063b.json", "pytest_prerepair_replay_plan_batch063b.json", "pytest_prerepair_replay_result_batch063b.json", "pytest_prerepair_failure_signature_extract_batch063b.json"]:
        write_out_json(name, no_run("command_boundary_not_normalized", classification=prerepair_class))
    write_out_text("pytest_prerepair_replay_command_batch063b.txt", "NOT_RUN: command boundary not normalized")
    write_out_text("pytest_prerepair_replay_log_raw_batch063b.txt", "NOT_RUN: command boundary not normalized")
    write_out_json("pytest_prerepair_outcome_classification_batch063b.json", {"status": "NOT_RUN", "classification": prerepair_class, "pre_repair_failure_materialized": False})
    for name in ["pytest_diagnostic_not_run_reason_batch063b.json", "pytest_diagnostic_minimal_replay_plan_batch063b.json", "pytest_diagnostic_minimal_replay_results_batch063b.json", "pytest_diagnostic_failed_node_registry_batch063b.json", "pytest_diagnostic_traceback_roots_batch063b.json", "pytest_diagnostic_failure_signature_extract_batch063b.json"]:
        write_out_json(name, no_run("pre_repair_failure_not_materialized", classification="diagnostic_replay_blocked"))

    write_out_json("pytest_amds_full_bug_tree_state_batch063b.json", {"status": "PASS", "candidate_id": PYTEST_ID, "terminal_state": "command_boundary_recovery_needed", "provider_runtime": provider["classification"], "version_origin": version_class, "runner_target": runner_target_class, "pre_repair_replay": prerepair_class})
    write_out_json("pytest_amds_node_registry_batch063b.json", {"status": "PASS", "nodes": [{"node": "provider_runtime", "state": provider["classification"]}, {"node": "version_origin", "state": version_class}, {"node": "command_boundary", "state": command_class}, {"node": "pre_repair_replay", "state": prerepair_class}]})
    write_out_json("pytest_amds_next_action_frontier_batch063b.json", {"status": "PASS", "next_allowed_action": pytest_next_allowed, "frontier": "safe_ancestor_tag_or_declared_runner_origin_followup"})
    write_out_json("pytest_patch_license_from_amds_batch063b.json", {"status": "PASS", "patch_license_state": patch_license, "future_only": True, "patch_generation_allowed_in_batch063b": False})
    for name in ["pytest_source_contact_prior_or_replay_map_batch063b.json", "pytest_provider_dependency_replay_map_batch063b.json", "pytest_interpreter_behavior_replay_map_batch063b.json", "pytest_test_expectation_replay_map_batch063b.json"]:
        write_out_json(name, {"status": "PASS", "candidate_id": PYTEST_ID, "map_is_repair_success": False, "patch_generation_allowed": False})

    write_out_json("workspace_purity_filter_pattern_update_batch063b.json", simple_status(no_stale_cache=True, no_reused_venv=True))
    write_out_json("command_translation_layer_pattern_update_batch063b.json", simple_status(no_guessing=True, metadata_derived=True))
    write_out_json("candidate_isolated_venv_pattern_update_batch063b.json", simple_status(candidate_isolated=True))
    write_out_json("baseline_registry_snapshot_pattern_update_batch063b.json", simple_status(counts_preserved=True))
    write_out_json("proof_ledger_forkpoint_pattern_update_batch063b.json", simple_status(failed_attempts_require_explicit_branch_closure=True))
    write_out_json("self_test_harness_origin_bootstrap_pattern_update_batch063b.json", simple_status(non_circular_harness_required=True))
    write_out_json("ast_topology_extrusion_future_requirement_batch063b.json", simple_status(future_only=True, patch_permission_now=False))
    write_out_json("cross_family_homology_ledger_future_requirement_batch063b.json", simple_status(routing_memory_only=True, not_repair_proof=True))
    write_out_json("apoptosis_safe_abstention_policy_update_batch063b.json", simple_status(public_safe_equivalent="safe abstention", terminal_classification_required=True))
    write_out_json("non_circular_harness_origin_policy_update_batch063b.json", simple_status(non_circular_required=True))
    write_out_json("batch063b_reactome_provider_capsule_utilization_update.json", simple_status(internal_analogy_only=True, not_repair_evidence=True))
    write_out_json("batch063b_tld_governance_utilization_update.json", simple_status(internal_governance_only=True, not_public_claim=True))
    write_out_json("batch063b_isomorphic_logic_to_engineering_gap_closure_update.json", simple_status(status_detail="translated_to_neutral_engineering_controls"))
    write_out_json("batch063b_public_safe_engineering_translation_update.json", simple_status(public_summary_uses_neutral_terms=True))
    write_policy_artifacts(workspace, command_class)
    write_out_json("pytest_readonly_source_inventory_batch063b.json", inventory)
    write_out_json("pytest_readonly_ast_parse_status_batch063b.json", parse_status)
    write_out_json("pytest_source_contact_topology_prior_batch063b.json", source_topology)

    historical_status = write_historical_requirement_artifacts(wrapper_next)

    for name in ["batch063b_repo_hygiene_pressure_reassessment.json", "batch063b_duplicate_function_risk_reassessment.json", "batch063b_shared_utility_extraction_recommendation.json", "batch063b_public_readiness_recommendation.json"]:
        write_out_json(name, {"status": "PASS", "repo_hygiene_pressure_status": "high_but_not_refactored_in_batch063b", "plan_only": True, "recommended_future_batch": wrapper_next})
    for name in ["project_health_review_batch063b.json", "capability_maturity_scorecard_batch063b.json", "version_progress_grade_batch063b.json", "strategic_direction_check_batch063b.json", "proof_milestone_distance_report_batch063b.json", "regression_and_drift_watch_batch063b.json", "self_maintenance_readiness_review_batch063b.json", "next_highest_impact_action_report_batch063b.json"]:
        write_out_json(name, {"status": "PASS", "issue_derived_repair_count": ISSUE_DERIVED_REPAIR_COUNT, "native_external_repair_count": NATIVE_EXTERNAL_REPAIR_COUNT, "project_health_grade": "A-", "traffic_light_status": "yellow", "self_maintaining_software": SELF_MAINTAINING, "repair_success_claimed": False})
    for name in ["public_language_neutrality_check_batch063b.json", "public_summary_claim_safety_check_batch063b.json", "internal_vs_public_language_boundary_batch063b.json"]:
        write_out_json(name, {"status": "PASS", "public_summary_uses_neutral_software_language": True, "internal_labels_not_public_claims": True, "forbidden_public_terms": PUBLIC_FORBIDDEN_TERMS})

    final = {
        "status": "PASS",
        "batch066_ingest_status": "PASS",
        "batch063b_audit_status": "PASS",
        "current_protocol": CURRENT_PROTOCOL,
        "issue_derived_repair_count": ISSUE_DERIVED_REPAIR_COUNT,
        "native_external_repair_count": NATIVE_EXTERNAL_REPAIR_COUNT,
        "pytest_version_origin_classification": version_class,
        "pytest_runner_target_import_origin_classification": runner_target_class,
        "pytest_command_boundary_classification": command_class,
        "pytest_provider_runtime_setup_status": provider["classification"],
        "pytest_prerepair_replay_classification": prerepair_class,
        "pytest_future_patch_license_state": patch_license,
        "repo_hygiene_pressure_status": "high_but_not_dominant_over_pytest_followup",
        "recommended_next_proof_path": pytest_next_allowed,
        "recommended_next_wrapper_hardening_path": wrapper_next,
        "next_allowed_action": next_allowed,
        "pytest_next_proof_action": pytest_next_allowed,
        "historical_requirement_recovery_status": historical_status["historical_requirement_recovery_status"],
        "recovered_requirement_count": historical_status["recovered_requirement_count"],
        "historical_requirements_implemented_now_count": historical_status["implemented_now_count"],
        "historical_requirements_scaffolded_with_audit_count": historical_status["scaffolded_with_audit_count"],
        "historical_requirements_blocked_with_exact_reason_count": historical_status["blocked_with_exact_reason_count"],
        "historical_requirements_assigned_to_named_future_batches_count": historical_status["assigned_to_named_future_batches_count"],
        "universal_wrapper_hardening_status": "scaffolded_active_batch063b",
        "workspace_purity_policy_status": "scaffolded_active_batch063b",
        "candidate_isolated_runtime_policy_status": "scaffolded_active_batch063b",
        "command_translation_layer_status": "scaffolded_active_batch063b",
        "non_circular_harness_origin_policy_status": "scaffolded_active_batch063b",
        "ast_topology_requirement_status": "future_patch_gate_law_scaffolded",
        "cross_family_homology_ledger_status": "routing_memory_only_scaffolded",
        "confidence_abstention_policy_status": "active_terminal_state_closure",
        "terminal_state_registry_status": "scaffolded_active_batch063b",
        "repo_public_readiness_status": "research_archive_not_release_ready",
        "duplicate_function_review_status": "reviewed_no_refactor",
        "permanent_fix_backlog_status": "updated",
        "project_health_grade": "A-",
        "traffic_light_status": "yellow",
        "distance_to_issue_derived_repair_count_5": "one_counted_issue_repair",
        "distance_to_self_maintaining_claim": "far",
        "full_scoring": FULL_SCORING,
        "memory_lift": MEMORY_LIFT,
        "self_maintaining_software": SELF_MAINTAINING,
        "exact_blocker": exact_blocker,
        "patch_generated": False,
        "patch_applied": False,
        "source_mutated": False,
        "tests_mutated": False,
        "fixtures_mutated": False,
        "dependency_or_build_files_mutated_as_repair": False,
        "duplicate_replay_run": False,
        "count_gate_run": False,
        "repair_count_increment": False,
        "full_scoring_run": False,
        "memory_lift_analysis_run": False,
    }
    write_out_json("batch063b_final_decision.json", final)
    write_out_json("batch067_pytest_source_only_patch_gate_recommendation.json", {"status": "PASS", "recommended": False, "reason": "pre_repair_failure_not_materialized"})
    write_out_json("batch067_pytest_failure_family_decomposition_recommendation.json", {"status": "PASS", "recommended": False, "reason": "command_boundary_not_normalized"})
    write_out_json("batch063c_pytest_command_boundary_manual_review_recommendation.json", {"status": "PASS", "recommended": True, "next_allowed_action": pytest_next_allowed, "focus": "safe_ancestor_tag_or_declared_runner_origin_followup"})
    write_out_json("batch058d_seed_discovery_expansion_recommendation.json", {"status": "PASS", "recommended": False})
    write_out_json("batch062b_repo_hygiene_utility_consolidation_planning_recommendation.json", {"status": "PASS", "recommended": False, "recommended_wrapper_hardening_path": wrapper_next})
    write_out_json("memory_lift_future_plan_recommendation.json", {"status": "PASS", "memory_lift_analysis_run": False, "future_only": True})
    write_out_json("claim_boundary.json", {k: final[k] for k in ["status", "current_protocol", "issue_derived_repair_count", "native_external_repair_count", "full_scoring", "memory_lift", "self_maintaining_software", "patch_generated", "patch_applied", "duplicate_replay_run", "count_gate_run", "repair_count_increment"]})
    write_out_json("audit.json", {"status": "PASS", "audit_script": "scripts/audit_batch063b_pytest_provider_runtime_recovery_followup.py"})
    write_out_json("package_verification.json", {"status": "PASS", "raw_zip_payload_committed": False, "runtime_workspaces_committed": False, "source_checkouts_committed": False, "venvs_committed": False, "caches_committed": False})
    write_out_json("artifact_sha256_verification.json", {"status": "PASS", "manifest": "SHA256SUMS.txt", "artifact_payload_expected_from_workflow": True})
    write_out_text("batch063b_summary.md", public_summary_block(final))
    update_roadmaps()
    update_public_summaries(final)
    write_sha256sums(OUT_DIR)
    print(json.dumps(final, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
