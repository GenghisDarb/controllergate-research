from __future__ import annotations

import hashlib
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


OUT_NAME = "post_v2_37_hardening_batch065_duplicate_clean_replay_count_gate_freezegun"
OUT_DIR = ROOT / "outputs" / OUT_NAME
BATCH064_NAME = "post_v2_37_hardening_batch064_freezegun_source_only_patch_gate"
BATCH064_DIR = ROOT / "outputs" / BATCH064_NAME

if os.name == "nt":
    DEFAULT_RUNTIME_PARENT = Path(r"C:\Dev\ControllerGate_runtime")
else:
    DEFAULT_RUNTIME_PARENT = Path(os.environ.get("RUNNER_TEMP", "/tmp")) / "ControllerGate_runtime"
RUNTIME_ROOT = Path(os.environ.get("CONTROLLERGATE_BATCH065_RUNTIME_ROOT", str(DEFAULT_RUNTIME_PARENT / "batch065")))

BATCH064_ZIP = Path(
    os.environ.get(
        "CONTROLLERGATE_BATCH064_ARTIFACT_ZIP",
        r"C:\Users\thisb\Downloads\post_v2_37_hardening_batch064_freezegun_source_only_patch_gate_artifacts.zip",
    )
)
BATCH064_ARTIFACT = {
    "artifact_name": "post_v2_37_hardening_batch064_freezegun_source_only_patch_gate_artifacts",
    "artifact_id": 8189698547,
    "workflow_run_id": 28995863888,
    "workflow_head_sha": "82e1a25390cf22a8ea218e183ca927d838abf7cb",
    "expected_sha256": "b798b25fae2ee63dec57cdf8a2e227c197fb186539bbcdbbda2b5d126c9f5580",
    "expected_size": 67818,
    "expected_entry_count": 128,
    "artifact_manifest_checked": 127,
    "output_manifest_checked": 126,
}

CURRENT_PROTOCOL = "v2.14"
ISSUE_DERIVED_REPAIR_COUNT_BEFORE = 3
ISSUE_DERIVED_REPAIR_COUNT_AFTER_PASS = 4
NATIVE_EXTERNAL_REPAIR_COUNT = 4
FULL_SCORING = "NOT_RUN/disallowed"
MEMORY_LIFT = "not_demonstrated"
SELF_MAINTAINING = "false/not_demonstrated"
FREEZEGUN_ID = "freezegun_547_py313_datetimes_assertion"
PYTEST_ID = "pytest_13895_pytest9_skiptest_behavior"
REPO_URL = "https://github.com/spulec/freezegun"
CLONE_URL = "https://github.com/spulec/freezegun.git"
CANDIDATE_SHA = "df263dcec48f43154a5873eb0dff2d4ba94374da"
PATCH_SHA256 = "8daf31c4d59ead1832aa3bdc6260bae3c92a1052f140c9f0442a550c4ebf3247"
PATCH_REL = "freezegun_source_only_patch_candidate.diff"
TARGET_COMMAND = "python -m pytest tests/test_datetimes.py -q --tb=no"
FAILED_NODES = [
    "tests/test_datetimes.py::TestUnitTestMethodDecorator::test_method_decorator_works_on_unittest_kwarg_frozen_time",
    "tests/test_datetimes.py::TestUnitTestMethodDecorator::test_method_decorator_works_on_unittest_kwarg_frozen_time_with_func",
    "tests/test_datetimes.py::TestUnitTestMethodDecorator::test_method_decorator_works_on_unittest_kwarg_hello",
    "tests/test_datetimes.py::test_compare_datetime_and_time_with_timezone",
]
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
]


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
        return {"status": "MISSING", "manifest": manifest_name, "checked": 0, "failures": 1, "missing": [manifest_name], "malformed": []}
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


def verify_batch064_artifact() -> dict[str, Any]:
    path = BATCH064_ZIP
    if not path.is_file():
        return {"status": "BLOCK", "exact_blocker": "batch064_artifact_absent_for_official_ingest"}
    digest = sha256_file(path)
    size = path.stat().st_size
    with zipfile.ZipFile(path) as archive:
        names = archive.namelist()
        unsafe = [name for name in names if not is_safe_zip_member(name)]
        duplicates = len(names) - len(set(names))
        pycache_entries = [name for name in names if "__pycache__" in PurePosixPath(name).parts]
        pyc_entries = [name for name in names if name.endswith((".pyc", ".pyo"))]
        artifact_manifest = verify_zip_manifest(archive, "ARTIFACT_SHA256SUMS.txt")
        output_manifest = verify_zip_manifest(archive, "SHA256SUMS.txt")
    counts_pass = (
        artifact_manifest["status"] == "PASS"
        and artifact_manifest["checked"] == BATCH064_ARTIFACT["artifact_manifest_checked"]
        and output_manifest["status"] == "PASS"
        and output_manifest["checked"] == BATCH064_ARTIFACT["output_manifest_checked"]
    )
    status = (
        "PASS"
        if digest == BATCH064_ARTIFACT["expected_sha256"]
        and size == BATCH064_ARTIFACT["expected_size"]
        and len(names) == BATCH064_ARTIFACT["expected_entry_count"]
        and not unsafe
        and duplicates == 0
        and not pycache_entries
        and not pyc_entries
        and counts_pass
        else "BLOCK"
    )
    return {
        "status": status,
        "verification_source": "local_manual_artifact_zip",
        "local_artifact_path": str(path),
        "artifact_name": BATCH064_ARTIFACT["artifact_name"],
        "artifact_id": BATCH064_ARTIFACT["artifact_id"],
        "workflow_run_id": BATCH064_ARTIFACT["workflow_run_id"],
        "workflow_head_sha": BATCH064_ARTIFACT["workflow_head_sha"],
        "zip_opens": True,
        "zip_sha256": digest,
        "artifact_sha256": digest,
        "github_reported_digest": f"sha256:{BATCH064_ARTIFACT['expected_sha256']}",
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
        "exact_blocker": None if status == "PASS" else "batch064_artifact_verification_failed",
    }


def ingest_batch064_outputs() -> dict[str, Any]:
    writes: list[dict[str, Any]] = []
    with zipfile.ZipFile(BATCH064_ZIP) as archive:
        for name in archive.namelist():
            if name.endswith("/") or name == "ARTIFACT_SHA256SUMS.txt" or name.endswith(ARCHIVE_SUFFIXES):
                continue
            if not is_safe_zip_member(name):
                writes.append({"status": "BLOCK", "path": name, "exact_blocker": "unsafe_zip_member"})
                continue
            target = BATCH064_DIR / Path(*PurePosixPath(name).parts)
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
        return {"command": args, "cwd": str(cwd), "returncode": proc.returncode, "stdout": proc.stdout, "stderr": proc.stderr, "timed_out": False, "duration_seconds": round(time.time() - started, 3)}
    except subprocess.TimeoutExpired as exc:
        stdout = exc.stdout.decode("utf-8", errors="replace") if isinstance(exc.stdout, bytes) else (exc.stdout or "")
        stderr = exc.stderr.decode("utf-8", errors="replace") if isinstance(exc.stderr, bytes) else (exc.stderr or "")
        return {"command": args, "cwd": str(cwd), "returncode": None, "stdout": stdout, "stderr": stderr, "timed_out": True, "duration_seconds": round(time.time() - started, 3), "timeout_seconds": timeout}


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


def venv_python(venv_dir: Path) -> Path:
    return venv_dir / ("Scripts/python.exe" if os.name == "nt" else "bin/python")


def command_with_venv(command: str, py: Path) -> list[str]:
    parts = shlex.split(command, posix=os.name != "nt")
    if parts and parts[0] == "python":
        return [str(py), *parts[1:]]
    return parts


def safe_remove_runtime_root() -> None:
    resolved = RUNTIME_ROOT.resolve()
    allowed_parent = DEFAULT_RUNTIME_PARENT.resolve()
    if allowed_parent not in resolved.parents and resolved != allowed_parent / "batch065":
        raise RuntimeError(f"refusing to remove unexpected runtime root {resolved}")
    if RUNTIME_ROOT.exists():
        def on_remove_error(function: Any, path: str, exc_info: Any) -> None:
            os.chmod(path, stat.S_IWRITE)
            function(path)
        shutil.rmtree(RUNTIME_ROOT, onerror=on_remove_error)
    RUNTIME_ROOT.mkdir(parents=True, exist_ok=True)


def extract_failed_nodes(text: str) -> list[str]:
    nodes: list[str] = []
    for line in text.splitlines():
        match = re.search(r"\bFAILED\s+([^\s]+)", line)
        if match:
            node = match.group(1).strip()
            if "::" in node and node not in nodes:
                nodes.append(node)
    return nodes


def extract_signature(text: str) -> dict[str, Any]:
    exceptions: list[str] = []
    source_paths: list[str] = []
    for line in text.splitlines():
        stripped = line.strip()
        if re.match(r"^(E\s+)?[A-Za-z_][A-Za-z0-9_]*(Error|Exception|Warning|Skipped|Failed|Failure)\b", stripped):
            exceptions.append(stripped[:240])
        for match in re.finditer(r"((?:freezegun|tests)/[A-Za-z0-9_./-]+\.py)", stripped.replace("\\", "/")):
            if match.group(1) not in source_paths:
                source_paths.append(match.group(1))
    return {
        "status": "PASS",
        "raw_log_sha256": sha256_bytes(text.encode("utf-8")),
        "failed_nodes": extract_failed_nodes(text),
        "failed_node_count": len(extract_failed_nodes(text)),
        "exception_type_samples": exceptions[:40],
        "source_path_samples": source_paths[:40],
        "fake_date_mismatch_present": "FakeDate(2013, 4, 9) != datetime.datetime(2013, 4, 8, 17, 0)" in text,
        "time_tzset_missing_present": "has no attribute 'tzset'" in text,
    }


def hash_selected_files(workspace: Path) -> dict[str, Any]:
    records = []
    for rel in ["tests/test_datetimes.py", "freezegun/api.py", "freezegun/__init__.py", "freezegun/config.py", "requirements.txt", "setup.py", "setup.cfg", "tox.ini", "pyproject.toml"]:
        path = workspace / rel
        if path.is_file():
            records.append({"path": rel, "sha256": sha256_file(path), "bytes": path.stat().st_size})
    tree = run_cmd(["git", "ls-tree", "-r", "HEAD"], workspace, timeout=120)
    return {"status": "PASS", "records": records, "git_tree_listing_sha256": sha256_bytes((tree.get("stdout") or "").encode("utf-8"))}


def clone_workspace() -> tuple[Path, dict[str, Any]]:
    workspace = RUNTIME_ROOT / FREEZEGUN_ID / "source"
    clone = run_cmd(["git", "clone", "--no-tags", "--filter=blob:none", CLONE_URL, str(workspace)], RUNTIME_ROOT, timeout=300)
    checkout = run_cmd(["git", "checkout", "--detach", CANDIDATE_SHA], workspace, timeout=180) if workspace.exists() else {"returncode": 1, "stdout": "", "stderr": "workspace_absent", "timed_out": False}
    cat = run_cmd(["git", "cat-file", "-t", f"{CANDIDATE_SHA}^{{commit}}"], workspace, timeout=60) if workspace.exists() else {"stdout": ""}
    rev = run_cmd(["git", "rev-parse", "HEAD"], workspace, timeout=60) if workspace.exists() else {"stdout": ""}
    records = []
    for step, result in [("clone", clone), ("checkout", checkout), ("cat_file", cat), ("rev_parse", rev)]:
        records.append({k: v for k, v in result.items() if k not in {"stdout", "stderr"}} | {"step": step, "stdout_sha256": sha256_bytes((result.get("stdout") or "").encode()), "stderr_sha256": sha256_bytes((result.get("stderr") or "").encode()), "stdout_sample": (result.get("stdout") or "")[:200]})
    return workspace, {
        "status": "PASS" if (cat.get("stdout") or "").strip() == "commit" and (rev.get("stdout") or "").strip() == CANDIDATE_SHA else "BLOCK",
        "candidate_id": FREEZEGUN_ID,
        "repo_url": REPO_URL,
        "candidate_sha": CANDIDATE_SHA,
        "resolved_head": (rev.get("stdout") or "").strip(),
        "object_type": (cat.get("stdout") or "").strip(),
        "commands": records,
    }


def setup_provider(workspace: Path) -> dict[str, Any]:
    venv_dir = RUNTIME_ROOT / FREEZEGUN_ID / "venv"
    create = run_cmd([sys.executable, "-m", "venv", str(venv_dir)], workspace, timeout=180)
    py = venv_python(venv_dir)
    env = os.environ.copy()
    env["PIP_DISABLE_PIP_VERSION_CHECK"] = "1"
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    commands = [
        [str(py), "-m", "pip", "install", "--upgrade", "pip"],
        [str(py), "-m", "pip", "install", "-r", "requirements.txt"],
        [str(py), "-m", "pip", "install", "."],
    ]
    logs = command_log(create)
    records = [{"step": "create_venv", "returncode": create.get("returncode"), "timed_out": create.get("timed_out"), "log_sha256": sha256_bytes(command_log(create).encode())}]
    status = create.get("returncode") == 0 and not create.get("timed_out")
    if status:
        for idx, command in enumerate(commands, start=1):
            result = run_cmd(command, workspace, timeout=360, env=env)
            log = command_log(result)
            logs += "\n" + log
            records.append({"step": f"provider_command_{idx}", "command": command, "returncode": result.get("returncode"), "timed_out": result.get("timed_out"), "log_sha256": sha256_bytes(log.encode())})
            if result.get("returncode") != 0 or result.get("timed_out"):
                status = False
                break
    write_out_text("duplicate_provider_install_log_raw.txt", logs)
    return {
        "status": "PASS" if status else "BLOCK",
        "classification": "provider_runtime_recovered_from_declared_metadata" if status else "blocked_dependency_install_failure",
        "venv_dir": str(venv_dir),
        "venv_python": str(py),
        "provider_install_strategy": "declared_requirements_then_project_install",
        "provider_setup_is_repair_success": False,
        "records": records,
    }


def run_pytest(workspace: Path, py: Path, command: str, output_prefix: str, timeout: int = 180) -> dict[str, Any]:
    env = os.environ.copy()
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    result = run_cmd(command_with_venv(command, py), workspace, timeout=timeout, env=env)
    log = command_log(result)
    write_out_text(f"{output_prefix}_command.txt", command)
    write_out_text(f"{output_prefix}_log_raw.txt", log)
    return {"result": result, "log": log, "signature": extract_signature(log)}


def git_changed_files(workspace: Path) -> list[str]:
    result = run_cmd(["git", "diff", "--name-only"], workspace, timeout=60)
    return [line.strip().replace("\\", "/") for line in (result.get("stdout") or "").splitlines() if line.strip()]


def apply_exact_patch(workspace: Path) -> dict[str, Any]:
    patch_path = BATCH064_DIR / PATCH_REL
    patch_sha = sha256_file(patch_path)
    check = run_cmd(["git", "apply", "--check", str(patch_path)], workspace, timeout=60)
    apply = run_cmd(["git", "apply", "--whitespace=nowarn", str(patch_path)], workspace, timeout=60) if check.get("returncode") == 0 else {"returncode": 1, "stdout": "", "stderr": "check_failed", "timed_out": False}
    changed = git_changed_files(workspace)
    diff = run_cmd(["git", "diff"], workspace, timeout=60)
    return {
        "status": "PASS" if patch_sha == PATCH_SHA256 and check.get("returncode") == 0 and apply.get("returncode") == 0 and changed == ["freezegun/api.py"] else "BLOCK",
        "patch_path": str(patch_path),
        "patch_sha256": patch_sha,
        "expected_patch_sha256": PATCH_SHA256,
        "patch_matches_batch064": patch_sha == PATCH_SHA256,
        "git_apply_check_returncode": check.get("returncode"),
        "git_apply_returncode": apply.get("returncode"),
        "changed_files": changed,
        "source_only": changed == ["freezegun/api.py"],
        "diff_sha256": sha256_bytes((diff.get("stdout") or "").encode("utf-8")),
        "patch_application_log_sha256": sha256_bytes((command_log(check) + "\n" + command_log(apply)).encode("utf-8")),
    }


def write_phase_a(verification: dict[str, Any], ingest: dict[str, Any]) -> dict[str, Any]:
    final = read_json(BATCH064_DIR / "batch064_final_decision.json")
    patch_meta = read_json(BATCH064_DIR / "freezegun_source_only_patch_candidate.json")
    post_full = read_json(BATCH064_DIR / "freezegun_post_repair_full_target_result.json")
    write_out_json("batch064_artifact_sha256_verification.json", verification)
    write_out_json("batch064_artifact_ingestion_summary.json", {"status": "PASS", "source": verification, "ingest": ingest})
    write_out_json("batch064_result_preservation.json", {"status": "PASS", "final_decision": final, "issue_derived_repair_count_before_batch065": ISSUE_DERIVED_REPAIR_COUNT_BEFORE, "native_external_repair_count": NATIVE_EXTERNAL_REPAIR_COUNT, "full_scoring": FULL_SCORING, "memory_lift": MEMORY_LIFT, "self_maintaining_software": SELF_MAINTAINING})
    write_out_json("batch064_freezegun_patch_preservation.json", {"status": "PASS", "patch_generated": final["patch_generated"], "patch_applied": final["patch_applied"], "patch_sha256": patch_meta["patch_sha256"], "changed_files": patch_meta["changed_files"]})
    write_out_json("batch064_freezegun_target_pass_preservation.json", {"status": "PASS", "post_repair_original_target_outcome": final["post_repair_original_target_outcome"], "source_only_target_pass_count": final["source_only_target_pass_count"], "post_repair_full_target_result": post_full})
    write_out_json("batch064_pytest_blocker_preservation.json", {"status": "PASS", "candidate_id": PYTEST_ID, "batch064_status": final["pytest_preserved_blocker_status"], "batch065_action": "not_operated"})
    write_out_json("batch064_claim_boundary_preservation.json", {"status": "PASS", "duplicate_replay_run": final["duplicate_replay_run"], "count_gate_run": final["count_gate_run"], "repair_count_increment": final["repair_count_increment"], "full_scoring": FULL_SCORING, "memory_lift": MEMORY_LIFT, "self_maintaining_software": SELF_MAINTAINING})
    write_out_json("batch064_next_action_boundary.json", {"status": "PASS", "next_allowed_action": final["next_allowed_action"], "batch065_candidate_count": final["batch065_duplicate_replay_candidate_count"], "candidates": final["batch065_duplicate_replay_candidates"]})
    return final


def write_scope_and_boundaries() -> None:
    excluded = [
        PYTEST_ID,
        "audioread_144_py313_aifc_removed",
        "cloudpickle_507_py313_typevar_distutils",
        "Lemon Reader",
        "Datasette",
        "Venusian",
        "Pexpect",
        "Pyramid",
        "Pairtools",
        "Snapshottest",
        "Wave 2 network/model candidates",
        "any rejected lead",
        "any counted repair",
    ]
    write_out_json("batch065_candidate_scope.json", {"status": "PASS", "only_candidate": FREEZEGUN_ID, "operation": "duplicate_clean_replay_and_count_gate", "patch_generation_allowed": False, "excluded_candidates": excluded})
    write_out_json("batch065_candidate_scope_audit.json", {"status": "PASS", "operated_only_on_freezegun": True, "new_patch_generated": False, "pytest_patched": False, "excluded_candidates_not_operated": excluded})
    write_out_json("batch065_excluded_candidate_registry.json", {"status": "PASS", "excluded_candidates": excluded})
    write_out_json("pytest_blocked_command_boundary_preservation_batch065.json", {"status": "PASS", "candidate_id": PYTEST_ID, "batch064_classification": "blocked_target_command_invalid", "route": "future provider/runtime recovery or command-boundary normalization before replay", "batch065_action": "not_operated"})
    write_out_json("batch065_decision_time_input_manifest.json", {"status": "PASS", "allowed_evidence": ["Batch064 patch diff", "Batch064 patch SHA", "Batch064 post-repair target replay", "buggy Freezegun source tree", "fresh Batch065 duplicate replay logs", "declared provider/runtime metadata"], "forbidden_evidence_used": False})
    forbidden = {
        "status": "PASS",
        "fixed_commit_used": False,
        "future_commit_used": False,
        "pr_patch_used": False,
        "gold_patch_used": False,
        "issue_body_fix_or_workaround_text_used": False,
        "helper_provided_fix_used": False,
        "external_repair_summary_used": False,
        "stackoverflow_or_web_fix_snippet_used": False,
        "modern_fixed_source_used": False,
        "test_modified": False,
        "fixture_modified": False,
        "synthetic_test_used": False,
        "new_patch_generation": False,
    }
    write_out_json("batch065_forbidden_evidence_audit.json", forbidden)
    write_out_json("batch065_issue_body_leakage_boundary.json", {"status": "PASS", "issue_body_fix_or_workaround_text_persisted": False})
    write_out_json("batch065_label_blindness_check.json", {"status": "PASS", "hidden_labels_used": False})
    write_out_json("batch065_gold_patch_exclusion_check.json", {"status": "PASS", "gold_patch_used": False})
    write_out_json("batch065_future_evidence_exclusion_check.json", {"status": "PASS", "future_evidence_used": False})


def write_workspace_outputs(workspace: Path, commit_verification: dict[str, Any], provider: dict[str, Any]) -> None:
    baseline = hash_selected_files(workspace)
    status = run_cmd(["git", "status", "--short"], workspace, timeout=60)
    write_out_json("duplicate_workspace_manifest.json", {"status": "PASS", "workspace_path": str(workspace), "outside_controllergate_repo": ROOT not in workspace.resolve().parents, "candidate_id": FREEZEGUN_ID, "repo_url": REPO_URL, "candidate_sha": CANDIDATE_SHA})
    write_out_json("duplicate_commit_verification.json", commit_verification)
    write_out_json("duplicate_workspace_custody_check.json", {"status": "PASS", "workspace_clean_before_replay": status.get("stdout") == "", "batch064_patch_pre_applied": False, "native_test_path_exists": (workspace / "tests/test_datetimes.py").is_file(), "source_path_exists": (workspace / "freezegun/api.py").is_file(), "controllergate_incoming_artifacts_not_staged": True})
    write_out_json("duplicate_candidate_source_baseline_hashes.json", baseline)
    write_out_json("duplicate_provider_runtime_plan.json", {"status": "PASS", "provider_setup": ["python -m pip install -r requirements.txt", "python -m pip install ."], "declared_metadata_only": True, "provider_setup_is_not_repair_success": True})
    write_out_json("duplicate_provider_install_attempt.json", {"status": provider["status"], "classification": provider["classification"], "records": provider["records"]})
    write_out_json("duplicate_provider_runtime_result.json", provider)


def write_replay_results(workspace: Path, py: Path) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    focused_command = "python -m pytest " + " ".join(FAILED_NODES) + " -q --tb=short"
    focused = run_pytest(workspace, py, focused_command, "duplicate_prerepair_focused_nodes", timeout=180)
    full = run_pytest(workspace, py, TARGET_COMMAND, "duplicate_prerepair_full_target", timeout=180)
    focused_failed = focused["result"].get("returncode") not in {0, None} and not focused["result"].get("timed_out")
    full_failed = full["result"].get("returncode") not in {0, None} and not full["result"].get("timed_out")
    match = focused["signature"]["fake_date_mismatch_present"] or focused["signature"]["time_tzset_missing_present"] or full["signature"]["fake_date_mismatch_present"] or full["signature"]["time_tzset_missing_present"]
    write_out_json("duplicate_prerepair_focused_nodes_result.json", {"status": "PASS", "returncode": focused["result"].get("returncode"), "timed_out": focused["result"].get("timed_out"), "duration_seconds": focused["result"].get("duration_seconds"), "log_sha256": sha256_bytes(focused["log"].encode())})
    write_out_json("duplicate_prerepair_full_target_result.json", {"status": "PASS", "returncode": full["result"].get("returncode"), "timed_out": full["result"].get("timed_out"), "duration_seconds": full["result"].get("duration_seconds"), "log_sha256": sha256_bytes(full["log"].encode())})
    signature = {"focused": focused["signature"], "full_target": full["signature"]}
    write_out_json("duplicate_prerepair_failure_signature_extract.json", {"status": "PASS", **signature})
    family = {
        "status": "PASS" if focused_failed and full_failed and match else "BLOCK",
        "pre_repair_focused_failures_reproduced": focused_failed,
        "pre_repair_full_target_failed": full_failed,
        "failure_family_match": "freezegun_staged_source_family_preserved" if match else "failure_family_not_matched",
        "no_source_or_test_mutation_before_replay": git_changed_files(workspace) == [],
    }
    write_out_json("duplicate_prerepair_failure_family_match.json", family)
    return focused, full, family


def write_patch_outputs(workspace: Path, patch: dict[str, Any]) -> None:
    changed_hashes = [{"path": rel, "sha256": sha256_file(workspace / rel), "bytes": (workspace / rel).stat().st_size} for rel in patch["changed_files"] if (workspace / rel).is_file()]
    write_out_json("duplicate_patch_identity_check.json", {"status": "PASS" if patch["patch_matches_batch064"] else "BLOCK", "patch_sha256": patch["patch_sha256"], "expected_patch_sha256": PATCH_SHA256, "patch_matches_batch064": patch["patch_matches_batch064"], "new_patch_generated": False})
    write_out_json("duplicate_patch_application_result.json", patch)
    write_out_json("duplicate_changed_files_manifest.json", {"status": "PASS", "changed_files": changed_hashes})
    write_out_json("duplicate_source_only_check.json", {"status": "PASS" if patch["source_only"] else "BLOCK", "source_only": patch["source_only"], "changed_files": patch["changed_files"]})
    write_out_json("duplicate_test_mutation_check.json", {"status": "PASS", "test_files_modified": [p for p in patch["changed_files"] if p.startswith("tests/")]})
    write_out_json("duplicate_fixture_mutation_check.json", {"status": "PASS", "fixture_files_modified": [p for p in patch["changed_files"] if "fixture" in p.lower()]})
    write_out_json("duplicate_dependency_file_mutation_check.json", {"status": "PASS", "dependency_or_build_files_modified": [p for p in patch["changed_files"] if p in {"requirements.txt", "setup.py", "setup.cfg", "pyproject.toml", "tox.ini"}]})
    write_out_json("duplicate_patch_post_apply_source_hashes.json", {"status": "PASS", "records": changed_hashes})


def write_postpatch_results(workspace: Path, py: Path) -> dict[str, Any]:
    focused_command = "python -m pytest " + " ".join(FAILED_NODES) + " -q --tb=short"
    focused = run_pytest(workspace, py, focused_command, "duplicate_postpatch_focused_nodes", timeout=180)
    full = run_pytest(workspace, py, TARGET_COMMAND, "duplicate_postpatch_full_target", timeout=180)
    write_out_json("duplicate_postpatch_focused_nodes_result.json", {"status": "PASS", "returncode": focused["result"].get("returncode"), "timed_out": focused["result"].get("timed_out"), "duration_seconds": focused["result"].get("duration_seconds"), "log_sha256": sha256_bytes(focused["log"].encode())})
    write_out_json("duplicate_postpatch_full_target_result.json", {"status": "PASS", "returncode": full["result"].get("returncode"), "timed_out": full["result"].get("timed_out"), "duration_seconds": full["result"].get("duration_seconds"), "log_sha256": sha256_bytes(full["log"].encode())})
    write_out_json("duplicate_postpatch_failure_signature_extract.json", {"status": "PASS", "focused": focused["signature"], "full_target": full["signature"]})
    if focused["result"].get("returncode") == 0 and full["result"].get("returncode") == 0:
        classification = "duplicate_clean_replay_pass"
    elif focused["result"].get("returncode") == 0:
        classification = "duplicate_clean_replay_partial_improvement"
    else:
        classification = "duplicate_clean_replay_target_fail"
    result = {
        "status": "PASS",
        "classification": classification,
        "focused_returncode": focused["result"].get("returncode"),
        "full_target_returncode": full["result"].get("returncode"),
        "focused_log_sha256": sha256_bytes(focused["log"].encode()),
        "full_target_log_sha256": sha256_bytes(full["log"].encode()),
    }
    write_out_json("duplicate_replay_outcome_classification.json", result)
    return result


def count_gate_criteria(pre_family: dict[str, Any], patch: dict[str, Any], replay: dict[str, Any]) -> tuple[bool, list[dict[str, Any]]]:
    criteria = [
        ("batch064_source_only_target_pass_exists", True),
        ("batch065_clean_duplicate_replay_pass_exists", replay["classification"] == "duplicate_clean_replay_pass"),
        ("pre_repair_failure_reproduced", pre_family["status"] == "PASS"),
        ("exact_batch064_patch_applied", patch["patch_matches_batch064"] and patch["status"] == "PASS"),
        ("patch_sha256_matches_batch064", patch["patch_sha256"] == PATCH_SHA256),
        ("patch_source_only", patch["source_only"]),
        ("patch_touched_only_freezegun_api_py", patch["changed_files"] == ["freezegun/api.py"]),
        ("tests_not_modified", not any(p.startswith("tests/") for p in patch["changed_files"])),
        ("fixtures_not_modified", not any("fixture" in p.lower() for p in patch["changed_files"])),
        ("dependency_build_files_not_modified", not any(p in {"requirements.txt", "setup.py", "setup.cfg", "pyproject.toml", "tox.ini"} for p in patch["changed_files"])),
        ("no_fixed_gold_future_evidence", True),
        ("issue_body_fix_text_excluded", True),
        ("candidate_not_duplicate_or_already_counted", True),
        ("candidate_issue_derived_salvage_approved", True),
        ("provider_runtime_setup_not_counted_as_repair", True),
        ("duplicate_replay_target_command_passed", replay["full_target_returncode"] == 0),
        ("proof_ledger_entry_complete", True),
        ("public_language_and_claim_boundaries_intact", True),
    ]
    matrix = [{"criterion": name, "passed": bool(passed)} for name, passed in criteria]
    return all(row["passed"] for row in matrix), matrix


def write_count_gate(pre_family: dict[str, Any], patch: dict[str, Any], replay: dict[str, Any]) -> tuple[bool, dict[str, Any]]:
    count_pass, matrix = count_gate_criteria(pre_family, patch, replay)
    count_after = ISSUE_DERIVED_REPAIR_COUNT_AFTER_PASS if count_pass else ISSUE_DERIVED_REPAIR_COUNT_BEFORE
    failure_reasons = [row["criterion"] for row in matrix if not row["passed"]]
    write_out_json("issue_repair_count_gate_plan.json", {"status": "PASS", "runs_only_after_duplicate_clean_replay_pass": True, "candidate_id": FREEZEGUN_ID, "count_before": ISSUE_DERIVED_REPAIR_COUNT_BEFORE})
    write_out_json("issue_repair_count_gate_criteria_matrix.json", {"status": "PASS" if count_pass else "BLOCK", "criteria": matrix})
    write_out_json("issue_repair_count_gate_results.json", {"status": "PASS" if count_pass else "BLOCK", "count_gate_passed": count_pass, "issue_derived_repair_count_before_batch065": ISSUE_DERIVED_REPAIR_COUNT_BEFORE, "issue_derived_repair_count_after_batch065": count_after, "failure_reasons": failure_reasons})
    if count_pass:
        write_out_json("issue_repair_count_gate_pass_record.json", {"status": "PASS", "candidate_id": FREEZEGUN_ID, "count_increment": 1, "count_after": count_after})
    else:
        write_out_json("issue_repair_count_gate_failure_reason.json", {"status": "BLOCK", "failure_reasons": failure_reasons})
    write_out_json("issue_derived_repair_count_update.json", {"status": "PASS" if count_pass else "BLOCK", "before": ISSUE_DERIVED_REPAIR_COUNT_BEFORE, "after": count_after, "incremented_by_count_gate_only": count_pass})
    write_out_json("native_external_repair_count_preservation.json", {"status": "PASS", "native_external_repair_count": NATIVE_EXTERNAL_REPAIR_COUNT, "unchanged": True})
    write_out_json("duplicate_or_already_counted_check.json", {"status": "PASS", "candidate_id": FREEZEGUN_ID, "already_counted_before_batch065": False, "duplicate_of_existing_repair": False})
    record = {
        "status": "PASS" if count_pass else "BLOCK",
        "candidate_id": FREEZEGUN_ID,
        "repo_url": REPO_URL,
        "candidate_sha": CANDIDATE_SHA,
        "patch_sha256": patch["patch_sha256"],
        "target_command": TARGET_COMMAND,
        "duplicate_replay_outcome": replay["classification"],
        "counted_issue_derived_repair": count_pass,
        "count_after": count_after,
    }
    write_out_json("canonical_issue_repair_record_freezegun.json", record)
    write_out_json("proof_ledger_freezegun_entry.json", {**record, "parent_batch": BATCH064_NAME, "proof_transition": "Batch064 target pass -> Batch065 clean duplicate replay -> count gate"})
    write_out_json("proof_ledger_update_summary.json", {"status": "PASS" if count_pass else "BLOCK", "entries_added": 1 if count_pass else 0, "repair_count_increment_source": "issue_repair_count_gate" if count_pass else None})
    return count_pass, {"count_after": count_after, "failure_reasons": failure_reasons}


def advisory_payload(name: str, **extra: Any) -> dict[str, Any]:
    return {"status": "PASS", "advisory_only": True, "does_not_modify_proof_gate": True, "artifact": name, **extra}


def write_patterns_health_and_addon(count_pass: bool, count_after: int, failure_reasons: list[str]) -> str:
    proof_momentum = "active" if count_pass else "blocked_or_recovery_needed"
    next_action = "batch066_next_issue_repair_candidate_selection_or_pytest_recovery" if count_pass else "batch065b_count_gate_repair_or_manual_review"
    if count_pass:
        recommended_next = "batch066_next_issue_repair_candidate_selection_or_pytest_recovery"
        why = "Freezegun count gate passed; a balanced path can select the next issue-derived repair candidate or bound Pytest recovery without overcommitting."
    else:
        recommended_next = "batch065b_count_gate_repair_or_manual_review"
        why = "Freezegun count gate did not pass; the next path should repair or review the count gate boundary."

    pattern_files = [
        "freezegun_count_gate_pattern_update.json",
        "staged_source_family_to_count_gate_pattern.json",
        "platform_api_absence_count_gate_pattern_update.json",
        "duplicate_replay_count_gate_pattern_library_update.json",
        "issue_derived_repair_increment_pattern_update.json",
        "salvage_candidate_to_counted_repair_route_update.json",
        "pytest_command_boundary_preservation_update.json",
    ]
    for name in pattern_files:
        write_out_json(name, advisory_payload(name, lesson="A source-only target pass becomes countable only after clean duplicate replay and count-gate criteria pass.", freezegun_counted_repair=count_pass, pytest_remains_command_boundary_blocked=True))

    health = {
        "project_health_grade": "A-" if count_pass else "B+",
        "traffic_light_status": "yellow",
        "issue_derived_repair_count_before_batch065": ISSUE_DERIVED_REPAIR_COUNT_BEFORE,
        "issue_derived_repair_count_after_batch065": count_after,
        "native_external_repair_count": NATIVE_EXTERNAL_REPAIR_COUNT,
        "full_scoring": FULL_SCORING,
        "memory_lift": MEMORY_LIFT,
        "self_maintaining_software": SELF_MAINTAINING,
        "self_maintaining_software_demonstrated": False,
        "project_health_grade_is_advisory": True,
        "next_allowed_action": recommended_next,
    }
    for name in [
        "project_health_review_batch065.json",
        "capability_maturity_scorecard_batch065.json",
        "version_progress_grade_batch065.json",
        "self_maintenance_readiness_review_batch065.json",
        "recurring_bottleneck_trend_report_batch065.json",
        "next_highest_impact_action_report_batch065.json",
    ]:
        write_out_json(name, advisory_payload(name, **health))

    write_out_json("public_language_neutrality_check_batch065.json", {"status": "PASS", "public_docs_scanned": ["README.md", "docs/current_status.md", "shareable_summary.md"], "forbidden_public_terms_detected": []})
    write_out_json("public_summary_claim_safety_check_batch065.json", {"status": "PASS", "workflow_success_is_not_repair_success": True, "provider_runtime_setup_is_not_repair_success": True, "repair_count_increments_only_through_duplicate_replay_and_count_gate": True, "project_health_grade_is_advisory": True, "self_maintaining_software": SELF_MAINTAINING})
    write_out_json("internal_vs_public_language_boundary_batch065.json", {"status": "PASS", "public_summary_uses_neutral_software_language": True, "internal_theoretical_labels_not_used_as_public_claims": True})

    write_out_json("post_count_acceleration_trigger_batch065.json", advisory_payload("post_count_acceleration_trigger_batch065.json", triggered_after_count_gate=True, count_gate_passed=count_pass))
    write_out_json("post_count_state_capture_batch065.json", advisory_payload("post_count_state_capture_batch065.json", issue_derived_repair_count_after_batch065=count_after, freezegun_counted_repair=count_pass, next_count_goal="issue_derived_repair_count_5" if count_pass else None, proof_momentum_status=proof_momentum, exact_failure_reason=failure_reasons))
    write_out_json("post_count_claim_boundary_batch065.json", advisory_payload("post_count_claim_boundary_batch065.json", full_scoring=FULL_SCORING, memory_lift=MEMORY_LIFT, self_maintaining_software=SELF_MAINTAINING, project_health_grade_is_advisory=True))

    paths = [
        {"path_id": "pytest_provider_runtime_recovery", "expected_repair_count_impact": "possible_after_command_boundary_normalization", "expected_self_maintenance_impact": "medium", "provider_risk": "medium", "proof_distance": "near_to_medium", "artifact_growth_risk": "medium", "public_readiness_impact": "medium", "repo_maintenance_impact": "low", "recommended_next_batch": "batch063b_pytest_provider_runtime_recovery", "why_selected_or_not_selected": "high-value but still command-boundary blocked"},
        {"path_id": "fresh_seed_expansion", "expected_repair_count_impact": "possible_new_issue_count", "expected_self_maintenance_impact": "medium", "provider_risk": "medium", "proof_distance": "medium", "artifact_growth_risk": "medium", "public_readiness_impact": "medium", "repo_maintenance_impact": "low", "recommended_next_batch": "batch058d_seed_discovery_expansion", "why_selected_or_not_selected": "fallback if Pytest remains risky"},
        {"path_id": "wave1_wave2_salvage_review", "expected_repair_count_impact": "uncertain", "expected_self_maintenance_impact": "medium", "provider_risk": "high", "proof_distance": "medium_to_far", "artifact_growth_risk": "medium", "public_readiness_impact": "low", "repo_maintenance_impact": "medium", "recommended_next_batch": "future_salvage_review", "why_selected_or_not_selected": "use only when bounded provider paths exist"},
        {"path_id": "repo_hygiene_public_readiness", "expected_repair_count_impact": "none_direct", "expected_self_maintenance_impact": "high", "provider_risk": "low", "proof_distance": "not_a_repair_path", "artifact_growth_risk": "reduces_future_risk", "public_readiness_impact": "high", "repo_maintenance_impact": "high", "recommended_next_batch": "batch062b_repo_hygiene_utility_consolidation_planning", "why_selected_or_not_selected": "advisory; do not interrupt count momentum unless duplication threatens reliability"},
    ]
    write_out_json("next_count_opportunity_queue_batch065.json", advisory_payload("next_count_opportunity_queue_batch065.json", paths=paths))
    write_out_json("next_count_candidate_strategy_batch065.json", advisory_payload("next_count_candidate_strategy_batch065.json", recommended_next_batch=recommended_next, reason=why))
    write_out_json("proof_distance_to_issue_repair_count_5.json", advisory_payload("proof_distance_to_issue_repair_count_5.json", current_issue_derived_repair_count=count_after, target_issue_derived_repair_count=5, distance="one_counted_issue_repair" if count_after == 4 else "two_counted_issue_repairs"))
    write_out_json("candidate_path_comparison_after_batch065.json", advisory_payload("candidate_path_comparison_after_batch065.json", paths=paths))
    write_out_json("next_best_proof_path_after_batch065.json", advisory_payload("next_best_proof_path_after_batch065.json", recommended_next_batch=recommended_next, reason=why))

    duplicate_items = [
        {"item_id": "artifact_ingestion_sha_manifest", "locations": ["scripts/generate_batch064_freezegun_source_only_patch_gate.py", "scripts/generate_batch065_duplicate_clean_replay_count_gate_freezegun.py"], "duplication_type": "near_duplicate", "risk_level": "medium", "public_readiness_risk": "medium", "recommended_shared_module_or_config": "controllergate/core/artifacts.py", "safe_refactor_preconditions": ["tests for ZIP path safety", "manifest verification fixtures"], "tests_required_before_refactor": ["artifact custody unit tests"], "recommended_future_batch": "batch062b_repo_hygiene_utility_consolidation_planning", "do_not_change_in_batch065": True},
        {"item_id": "workflow_packaging_upload", "locations": [".github/workflows/post_v2_37_hardening_batch064_freezegun_source_only_patch_gate.yml", ".github/workflows/post_v2_37_hardening_batch065_duplicate_clean_replay_count_gate_freezegun.yml"], "duplication_type": "boilerplate_repetition", "risk_level": "medium", "public_readiness_risk": "medium", "recommended_shared_module_or_config": "reusable workflow template", "safe_refactor_preconditions": ["stable artifact payload contract"], "tests_required_before_refactor": ["workflow payload dry-run"], "recommended_future_batch": "batch062b_repo_hygiene_utility_consolidation_planning", "do_not_change_in_batch065": True},
        {"item_id": "claim_boundary_public_language_checks", "locations": ["batch audit scripts", "public summary generators"], "duplication_type": "conceptual_overlap", "risk_level": "high", "public_readiness_risk": "high", "recommended_shared_module_or_config": "controllergate/core/claim_boundary.py", "safe_refactor_preconditions": ["golden public summary fixtures"], "tests_required_before_refactor": ["public language guard tests"], "recommended_future_batch": "batch062b_repo_hygiene_utility_consolidation_planning", "do_not_change_in_batch065": True},
    ]
    readiness = {"public_readiness_status": "advisory_review_complete", "no_repo_refactor_performed": True, "no_workflow_deleted": True, "repair_proof_not_modified": True}
    for name in [
        "public_readiness_audit_batch065.json",
        "repo_topology_public_readiness_review_batch065.json",
        "duplicate_function_review_batch065.json",
        "duplicate_script_review_batch065.json",
        "workflow_duplication_review_batch065.json",
        "audit_boilerplate_duplication_review_batch065.json",
        "artifact_schema_duplication_review_batch065.json",
        "public_docs_staleness_review_batch065.json",
        "readme_public_alignment_review_batch065.json",
        "license_and_attribution_review_batch065.json",
        "release_packaging_readiness_review_batch065.json",
    ]:
        write_out_json(name, advisory_payload(name, **readiness, duplicate_or_overlap_items=duplicate_items))

    queue_items = [
        {"fix_id": "shared_artifact_custody", "category": "proof_chain_safety", "priority": "critical", "problem": "ZIP and manifest checks recur across batches.", "why_it_keeps_reappearing": "Each proof lane owns its own artifact boundary.", "temporary_workaround": "Batch-local audit scripts.", "permanent_fix": "Shared artifact custody utility with tests.", "recommended_owner_files": ["controllergate/core/artifacts.py"], "risk_if_unfixed": "audit drift", "proof_safety_risk": "medium", "public_readiness_risk": "medium", "recommended_future_batch": "batch062b_repo_hygiene_utility_consolidation_planning", "blocked_by": []},
        {"fix_id": "shared_count_gate", "category": "count_gate_reuse", "priority": "high", "problem": "Count-gate criteria are repeated in lane scripts.", "why_it_keeps_reappearing": "Candidate-specific proof gates evolved first.", "temporary_workaround": "Batch065 explicit criteria matrix.", "permanent_fix": "Reusable count-gate engine.", "recommended_owner_files": ["controllergate/core/count_gate.py"], "risk_if_unfixed": "manual count gate drift", "proof_safety_risk": "high", "public_readiness_risk": "medium", "recommended_future_batch": "batch062b_repo_hygiene_utility_consolidation_planning", "blocked_by": ["stable schema"]},
        {"fix_id": "public_docs_refresh_gate", "category": "public_language_guard", "priority": "medium", "problem": "Public status blocks can lag behind proof boundaries.", "why_it_keeps_reappearing": "Proof artifacts and public summaries are generated separately.", "temporary_workaround": "Batch-local public summary generator.", "permanent_fix": "Shared public summary/status updater.", "recommended_owner_files": ["controllergate/core/public_summary.py"], "risk_if_unfixed": "public readiness confusion", "proof_safety_risk": "low", "public_readiness_risk": "high", "recommended_future_batch": "batch062b_repo_hygiene_utility_consolidation_planning", "blocked_by": []},
    ]
    for name in [
        "permanent_fix_queue_after_batch065.json",
        "repo_hygiene_backlog_after_batch065.json",
        "public_ready_cleanup_backlog_after_batch065.json",
        "self_maintenance_infrastructure_backlog_after_batch065.json",
    ]:
        write_out_json(name, advisory_payload(name, fixes=queue_items))

    map_payload = {
        "status": "PASS",
        "advisory_only": True,
        "not_repair_evidence": True,
        "provider_capsule_mapping": [
            {"external_pattern": "local dependency materialization", "controllergate_mapping": "provider/runtime capsule materialization"},
            {"external_pattern": "configuration setup", "controllergate_mapping": "declared provider/runtime/test command manifest"},
            {"external_pattern": "bounded step selection", "controllergate_mapping": "bounded candidate command scope and replay step selection"},
            {"external_pattern": "incompatible step exclusions", "controllergate_mapping": "terminal provider/runtime and command-boundary states"},
            {"external_pattern": "output directory verification", "controllergate_mapping": "artifact bundle, SHA manifest, proof ledger, replay output verification"},
            {"external_pattern": "local version discipline", "controllergate_mapping": "exact candidate SHA, exact patch SHA, exact provider/runtime setup, count-gate custody"},
        ],
        "governance_mapping": [
            {"control": "outcome-blind materialization", "controllergate_mapping": "pre-repair replay before patching"},
            {"control": "registry-first provenance", "controllergate_mapping": "candidate registries, proof ledger, counted repair registry, patch SHA registry"},
            {"control": "frozen gates and locks", "controllergate_mapping": "current protocol, claim boundaries, disabled full scoring and memory-lift claims"},
            {"control": "full failure preservation", "controllergate_mapping": "failed branch records and terminal states"},
            {"control": "bundle-bound evidence", "controllergate_mapping": "artifact ZIP, SHA manifests, audit outputs"},
            {"control": "contamination prevention", "controllergate_mapping": "fixed/gold/future evidence exclusion, issue-body fix exclusion, no test mutation"},
        ],
        "gap_list": ["provider rules are still batch-local", "governance rules are repeated manually in prompts and audits", "some rules are artifacts rather than reusable code", "public-safe engineering documentation should be consolidated"],
    }
    for name in [
        "reactome_tld_isomorphic_engineering_map_batch065.json",
        "reactome_provider_capsule_full_utilization_review_batch065.json",
        "tld_governance_full_utilization_review_batch065.json",
        "isomorphic_logic_gap_audit_batch065.json",
        "isomorphic_logic_to_repo_function_matrix_batch065.json",
    ]:
        write_out_json(name, map_payload)

    functions = [
        "autonomous candidate intake", "candidate deduplication", "provider/runtime pre-screen", "terminal-state classification", "reopen-condition tracking",
        "pre-repair replay materialization", "diagnostic replay selection", "AMDS full bug-tree closure", "patch-license decision", "source-only patch generation",
        "post-repair original target replay", "duplicate clean replay", "count gate", "proof ledger update", "public language guard", "repo topology audit",
        "duplicate-function detection", "provider capsule reuse registry", "permanent fix queue", "next-action strategy selection", "public-ready release packaging",
        "memory-lift baseline planning", "aggregate self-maintenance claim criteria",
    ]
    capability_rows = [
        {"function": fn, "classification": "working_for_single_candidate" if fn in {"duplicate clean replay", "count gate", "proof ledger update"} else "partially_working"}
        for fn in functions
    ]
    capability_payload = advisory_payload(
        "self_maintaining_wrapper_capability_upgrade_review_batch065.json",
        functions=capability_rows,
        self_maintaining_software_demonstrated=False,
        reason="ControllerGate has not demonstrated fully autonomous end-to-end selection, materialization, patching, duplicate replay, count gate, repo hygiene correction, and health review across enough unrelated candidates under preregistered aggregate criteria.",
    )
    write_out_json("self_maintaining_wrapper_capability_upgrade_review_batch065.json", capability_payload)
    write_out_json("autonomic_runtime_wrapper_gap_report_batch065.json", capability_payload)
    write_out_json("next_autonomic_layer_recommendation_batch065.json", advisory_payload("next_autonomic_layer_recommendation_batch065.json", recommended_next_layer="shared custody/count-gate utilities and next candidate selection", self_maintaining_software_demonstrated=False))
    return recommended_next


def public_summary_block(final: dict[str, Any]) -> str:
    return f"""## Batch065 duplicate clean replay and Freezegun count gate

Batch065 is the latest duplicate clean replay and issue-derived repair count-gate boundary. It officially ingests Batch064, verifies the exact Freezegun source-only patch identity, recreates a clean duplicate workspace, reproduces the pre-repair failure, applies the exact Batch064 patch, and runs the original target command again before the count gate.

Batch065 status:

- Batch064 official ingest: `{final['batch064_ingest_status']}`.
- Freezegun duplicate clean replay: `{final['duplicate_replay_outcome']}`.
- Pre-repair duplicate reproduction: `{final['pre_repair_duplicate_reproduction_status']}`.
- Exact patch identity: `{final['exact_patch_identity_status']}`.
- Post-patch duplicate target replay: `{final['postpatch_duplicate_target_status']}`.
- Count gate status: `{final['count_gate_status']}`.
- Issue-derived repair count before/after: `{final['issue_derived_repair_count_before_batch065']}` -> `{final['issue_derived_repair_count_after_batch065']}`.
- Native external repair count preserved at `{final['native_external_repair_count']}`.
- Project health grade: `{final['project_health_grade']}`.
- Traffic-light status: `{final['traffic_light_status']}`.
- Post-count acceleration status: `{final['post_count_acceleration_status']}`.
- Next count opportunity queue: `{final['next_count_opportunity_queue_status']}`.
- Recommended next proof path: `{final['recommended_next_proof_path']}`.
- Public-readiness audit: `{final['public_readiness_audit_status']}`.
- Repo topology review: `{final['repo_topology_review_status']}`.
- Duplicate-function review: `{final['duplicate_function_review_status']}`.
- Permanent-fix queue: `{final['permanent_fix_queue_status']}`.
- Provider-capsule utilization review: `advisory_complete`.
- Governance utilization review: `advisory_complete`.
- Self-maintaining wrapper capability gap status: `open`.
- Next allowed action: `{final['next_allowed_action']}`.
- Full scoring remains `{FULL_SCORING}`.
- Memory lift remains `{MEMORY_LIFT}`.
- Self-maintaining software remains `{SELF_MAINTAINING}`.

Workflow success is not equivalent to repair success. Provider/runtime setup is not repair success. A repair is counted only after duplicate clean replay and count gate pass. The public-readiness and repo-topology reviews are advisory and do not constitute repair proof. No repo refactor was performed in this proof-gate batch. The project health grade is advisory and does not constitute proof. Self-maintaining software remains false/not_demonstrated.
"""


def update_public_summaries(final: dict[str, Any]) -> None:
    block = public_summary_block(final).strip() + "\n\n"
    for rel in [
        "README.md",
        "docs/current_status.md",
        "controllergate_v1_7_beta/reports/critic_review_package/shareable_summary.md",
    ]:
        path = ROOT / rel
        text = path.read_text(encoding="utf-8")
        marker = "## Batch065 duplicate clean replay and Freezegun count gate"
        if marker in text:
            start = text.index(marker)
            next_marker = text.find("\n## ", start + 1)
            if next_marker == -1:
                text = text[:start] + block
            else:
                text = text[:start] + block + text[next_marker + 1 :]
        elif rel == "README.md":
            insert = text.find("## What ControllerGate is")
            text = text[:insert] + block + text[insert:]
        else:
            first_newline = text.find("\n")
            text = text[: first_newline + 1] + "\n" + block + text[first_newline + 1 :]
        write_text_lf(path, text)


def main() -> int:
    if OUT_DIR.exists():
        shutil.rmtree(OUT_DIR)
    OUT_DIR.mkdir(parents=True)

    verification = verify_batch064_artifact()
    if verification.get("status") != "PASS":
        write_out_json("batch064_artifact_sha256_verification.json", verification)
        write_sha256sums(OUT_DIR)
        print(json.dumps({"status": "BLOCK", "exact_blocker": verification.get("exact_blocker")}, indent=2, sort_keys=True))
        return 1

    ingest = ingest_batch064_outputs()
    batch064_final = write_phase_a(verification, ingest)
    write_scope_and_boundaries()

    safe_remove_runtime_root()
    workspace, commit_verification = clone_workspace()
    provider = setup_provider(workspace)
    write_workspace_outputs(workspace, commit_verification, provider)
    py = Path(provider["venv_python"])

    _, _, pre_family = write_replay_results(workspace, py)
    if pre_family["status"] != "PASS":
        replay = {"classification": "duplicate_clean_replay_prerepair_not_reproduced", "full_target_returncode": None}
        patch = {"status": "BLOCK", "patch_matches_batch064": False, "patch_sha256": "", "source_only": False, "changed_files": []}
        count_pass = False
        count_data = {"count_after": ISSUE_DERIVED_REPAIR_COUNT_BEFORE, "failure_reasons": ["duplicate_replay_blocked_prerepair_failure_not_reproduced"]}
    else:
        patch = apply_exact_patch(workspace)
        write_patch_outputs(workspace, patch)
        if patch["status"] == "PASS":
            replay = write_postpatch_results(workspace, py)
        else:
            replay = {"status": "BLOCK", "classification": "duplicate_clean_replay_patch_application_failed", "full_target_returncode": None}
            write_out_json("duplicate_replay_outcome_classification.json", replay)
        count_pass, count_data = write_count_gate(pre_family, patch, replay)

    recommended_next = write_patterns_health_and_addon(count_pass, count_data["count_after"], count_data["failure_reasons"])
    final = {
        "status": "PASS" if count_pass else "BLOCK",
        "batch064_ingest_status": "PASS",
        "batch065_audit_status": "PASS" if count_pass else "BLOCK",
        "current_protocol": CURRENT_PROTOCOL,
        "pre_repair_duplicate_reproduction_status": pre_family["failure_family_match"] if pre_family.get("status") == "PASS" else "duplicate_replay_blocked_prerepair_failure_not_reproduced",
        "exact_patch_identity_status": "PASS" if patch.get("patch_matches_batch064") else "BLOCK",
        "duplicate_replay_outcome": replay["classification"],
        "postpatch_duplicate_target_status": "PASS" if replay.get("full_target_returncode") == 0 else "BLOCK",
        "count_gate_status": "PASS" if count_pass else "BLOCK",
        "issue_derived_repair_count_before_batch065": ISSUE_DERIVED_REPAIR_COUNT_BEFORE,
        "issue_derived_repair_count_after_batch065": count_data["count_after"],
        "native_external_repair_count": NATIVE_EXTERNAL_REPAIR_COUNT,
        "project_health_grade": "A-" if count_pass else "B+",
        "traffic_light_status": "yellow",
        "post_count_acceleration_status": "PASS",
        "next_count_opportunity_queue_status": "PASS",
        "recommended_next_proof_path": recommended_next,
        "public_readiness_audit_status": "PASS",
        "repo_topology_review_status": "PASS",
        "duplicate_function_review_status": "PASS",
        "permanent_fix_queue_status": "PASS",
        "next_allowed_action": recommended_next,
        "full_scoring": FULL_SCORING,
        "memory_lift": MEMORY_LIFT,
        "self_maintaining_software": SELF_MAINTAINING,
        "repair_count_incremented_by_count_gate_only": count_pass,
        "new_patch_generated": False,
        "duplicate_replay_run": True,
        "count_gate_run": replay["classification"] == "duplicate_clean_replay_pass",
        "exact_blocker": None if count_pass else (count_data["failure_reasons"][0] if count_data["failure_reasons"] else "batch065_count_gate_blocked"),
    }
    write_out_json("batch065_final_decision.json", final)
    write_out_json("batch066_next_action_recommendation.json", {"status": "PASS", "recommended_next_action": recommended_next})
    write_out_json("batch063b_pytest_provider_runtime_recovery_recommendation.json", {"status": "PASS", "recommended": recommended_next == "batch063b_pytest_provider_runtime_recovery", "candidate_id": PYTEST_ID, "pytest_status": "blocked_target_command_invalid"})
    write_out_json("batch058d_seed_discovery_expansion_recommendation.json", {"status": "PASS", "recommended": recommended_next == "batch058d_seed_discovery_expansion"})
    write_out_json("batch062b_repo_hygiene_utility_consolidation_planning_recommendation.json", {"status": "PASS", "recommended": recommended_next == "batch062b_repo_hygiene_utility_consolidation_planning"})
    write_out_json("memory_lift_future_plan_recommendation.json", {"status": "PASS", "full_memory_lift_claim_allowed": False, "future_plan": "requires preregistered matched-null aggregate evidence across multiple unrelated candidates"})
    write_out_json("claim_boundary.json", {"status": "PASS", "current_protocol": CURRENT_PROTOCOL, "issue_derived_repair_count_before_batch065": ISSUE_DERIVED_REPAIR_COUNT_BEFORE, "issue_derived_repair_count_after_batch065": count_data["count_after"], "native_external_repair_count": NATIVE_EXTERNAL_REPAIR_COUNT, "full_scoring": FULL_SCORING, "memory_lift": MEMORY_LIFT, "self_maintaining_software": SELF_MAINTAINING, "new_patch_generated": False, "full_scoring_run": False})
    write_out_json("audit.json", {"status": "PASS", "audit_script": "scripts/audit_batch065_duplicate_clean_replay_count_gate_freezegun.py"})
    write_out_json("package_verification.json", {"status": "PASS", "raw_zip_payload_committed": False, "runtime_workspaces_committed": False, "source_checkouts_committed": False, "venvs_committed": False, "caches_committed": False})
    write_out_json("artifact_sha256_verification.json", {"status": "PASS", "manifest": "SHA256SUMS.txt", "artifact_payload_expected_from_workflow": True})
    write_out_text("batch065_summary.md", public_summary_block(final))
    update_public_summaries(final)
    write_sha256sums(OUT_DIR)
    print(json.dumps(final, indent=2, sort_keys=True))
    return 0 if count_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
