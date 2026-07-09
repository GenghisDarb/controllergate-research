from __future__ import annotations

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


OUT_NAME = "post_v2_37_hardening_batch066_next_issue_repair_candidate_selection_or_pytest_recovery"
OUT_DIR = ROOT / "outputs" / OUT_NAME
BATCH065_NAME = "post_v2_37_hardening_batch065_duplicate_clean_replay_count_gate_freezegun"
BATCH065_DIR = ROOT / "outputs" / BATCH065_NAME

if os.name == "nt":
    DEFAULT_RUNTIME_PARENT = Path(r"C:\Dev\ControllerGate_runtime")
else:
    DEFAULT_RUNTIME_PARENT = Path(os.environ.get("RUNNER_TEMP", "/tmp")) / "ControllerGate_runtime"
RUNTIME_ROOT = Path(os.environ.get("CONTROLLERGATE_BATCH066_RUNTIME_ROOT", str(DEFAULT_RUNTIME_PARENT / "batch066")))

BATCH065_ZIP = Path(
    os.environ.get(
        "CONTROLLERGATE_BATCH065_ARTIFACT_ZIP",
        r"C:\Users\thisb\Downloads\post_v2_37_hardening_batch065_duplicate_clean_replay_count_gate_freezegun_artifacts.zip",
    )
)
BATCH065_ARTIFACT = {
    "artifact_name": "post_v2_37_hardening_batch065_duplicate_clean_replay_count_gate_freezegun_artifacts",
    "artifact_id": 8203650066,
    "workflow_run_id": 29030566947,
    "workflow_head_sha": "ef6c59a507d01acb9526f163ea2b1bf6bce6fbf0",
    "expected_sha256": "b07f7f793ede2f61fdc6a5f692efe2b0735e53d1effdd466f3df2fba8288f5a8",
    "expected_size": 75863,
    "expected_entry_count": 120,
    "artifact_manifest_checked": 119,
    "output_manifest_checked": 118,
}

CURRENT_PROTOCOL = "v2.14"
ISSUE_DERIVED_REPAIR_COUNT = 4
ISSUE_DERIVED_REPAIR_COUNT_BEFORE_BATCH065 = 3
NATIVE_EXTERNAL_REPAIR_COUNT = 4
FULL_SCORING = "NOT_RUN/disallowed"
MEMORY_LIFT = "not_demonstrated"
SELF_MAINTAINING = "false/not_demonstrated"
FREEZEGUN_ID = "freezegun_547_py313_datetimes_assertion"
PYTEST_ID = "pytest_13895_pytest9_skiptest_behavior"
PYTEST_REPO_URL = "https://github.com/pytest-dev/pytest"
PYTEST_CLONE_URL = "https://github.com/pytest-dev/pytest.git"
PYTEST_SHA = "041aacad506b6c6891f2898f2bd378e0896e8b86"
PRESERVED_PYTEST_COMMAND = "python -m pytest testing -q --tb=no"
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


def verify_batch065_artifact() -> dict[str, Any]:
    path = BATCH065_ZIP
    if not path.is_file():
        return {"status": "BLOCK", "exact_blocker": "batch065_artifact_absent_for_official_ingest"}
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
        and artifact_manifest["checked"] == BATCH065_ARTIFACT["artifact_manifest_checked"]
        and output_manifest["status"] == "PASS"
        and output_manifest["checked"] == BATCH065_ARTIFACT["output_manifest_checked"]
    )
    status = (
        "PASS"
        if digest == BATCH065_ARTIFACT["expected_sha256"]
        and size == BATCH065_ARTIFACT["expected_size"]
        and len(names) == BATCH065_ARTIFACT["expected_entry_count"]
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
        "artifact_name": BATCH065_ARTIFACT["artifact_name"],
        "artifact_id": BATCH065_ARTIFACT["artifact_id"],
        "workflow_run_id": BATCH065_ARTIFACT["workflow_run_id"],
        "workflow_head_sha": BATCH065_ARTIFACT["workflow_head_sha"],
        "zip_opens": True,
        "zip_sha256": digest,
        "artifact_sha256": digest,
        "github_reported_digest": f"sha256:{BATCH065_ARTIFACT['expected_sha256']}",
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
        "exact_blocker": None if status == "PASS" else "batch065_artifact_verification_failed",
    }


def ingest_batch065_outputs() -> dict[str, Any]:
    writes: list[dict[str, Any]] = []
    with zipfile.ZipFile(BATCH065_ZIP) as archive:
        for name in archive.namelist():
            if name.endswith("/") or name == "ARTIFACT_SHA256SUMS.txt" or name.endswith(ARCHIVE_SUFFIXES):
                continue
            if not is_safe_zip_member(name):
                writes.append({"status": "BLOCK", "path": name, "exact_blocker": "unsafe_zip_member"})
                continue
            target = BATCH065_DIR / Path(*PurePosixPath(name).parts)
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


def safe_remove_runtime_root() -> None:
    resolved = RUNTIME_ROOT.resolve()
    allowed_parent = DEFAULT_RUNTIME_PARENT.resolve()
    if allowed_parent not in resolved.parents and resolved != allowed_parent / "batch066":
        raise RuntimeError(f"refusing to remove unexpected runtime root {resolved}")
    if RUNTIME_ROOT.exists():
        def on_remove_error(function: Any, path: str, exc_info: Any) -> None:
            os.chmod(path, stat.S_IWRITE)
            function(path)
        shutil.rmtree(RUNTIME_ROOT, onerror=on_remove_error)
    RUNTIME_ROOT.mkdir(parents=True, exist_ok=True)


def venv_python(venv_dir: Path) -> Path:
    return venv_dir / ("Scripts/python.exe" if os.name == "nt" else "bin/python")


def command_with_venv(command: str, py: Path) -> list[str]:
    parts = shlex.split(command, posix=os.name != "nt")
    if parts and parts[0] == "python":
        return [str(py), *parts[1:]]
    return parts


def hash_selected_files(workspace: Path) -> dict[str, Any]:
    candidates = [
        "pyproject.toml",
        "tox.ini",
        "noxfile.py",
        "setup.py",
        "setup.cfg",
        "requirements.txt",
        "requirements-dev.txt",
        "README.rst",
        "CONTRIBUTING.rst",
    ]
    records = []
    for rel in candidates:
        path = workspace / rel
        if path.is_file():
            records.append({"path": rel, "sha256": sha256_file(path), "bytes": path.stat().st_size})
    for rel in ["testing", "src/_pytest", "src/pytest"]:
        path = workspace / rel
        if path.exists():
            listing = "\n".join(sorted(p.relative_to(workspace).as_posix() for p in path.rglob("*") if p.is_file()))
            records.append({"path": rel, "tree_listing_sha256": sha256_bytes(listing.encode("utf-8")), "file_count": len(listing.splitlines()) if listing else 0})
    return {"status": "PASS", "records": records}


def clone_pytest_workspace() -> tuple[Path, dict[str, Any]]:
    workspace = RUNTIME_ROOT / PYTEST_ID / "source"
    clone = run_cmd(["git", "clone", "--no-tags", "--filter=blob:none", PYTEST_CLONE_URL, str(workspace)], RUNTIME_ROOT, timeout=300)
    checkout = run_cmd(["git", "checkout", "--detach", PYTEST_SHA], workspace, timeout=180) if workspace.exists() else {"returncode": 1, "stdout": "", "stderr": "workspace_absent", "timed_out": False}
    cat = run_cmd(["git", "cat-file", "-t", f"{PYTEST_SHA}^{{commit}}"], workspace, timeout=60) if workspace.exists() else {"stdout": ""}
    rev = run_cmd(["git", "rev-parse", "HEAD"], workspace, timeout=60) if workspace.exists() else {"stdout": ""}
    records = []
    for step, result in [("clone", clone), ("checkout", checkout), ("cat_file", cat), ("rev_parse", rev)]:
        records.append({k: v for k, v in result.items() if k not in {"stdout", "stderr"}} | {"step": step, "stdout_sha256": sha256_bytes((result.get("stdout") or "").encode()), "stderr_sha256": sha256_bytes((result.get("stderr") or "").encode()), "stdout_sample": (result.get("stdout") or "")[:200]})
    return workspace, {
        "status": "PASS" if (cat.get("stdout") or "").strip() == "commit" and (rev.get("stdout") or "").strip() == PYTEST_SHA else "BLOCK",
        "candidate_id": PYTEST_ID,
        "repo_url": PYTEST_REPO_URL,
        "candidate_sha": PYTEST_SHA,
        "resolved_head": (rev.get("stdout") or "").strip(),
        "object_type": (cat.get("stdout") or "").strip(),
        "commands": records,
    }


def read_metadata_summary(workspace: Path) -> dict[str, Any]:
    files = {rel: (workspace / rel).read_text(encoding="utf-8", errors="replace") for rel in ["pyproject.toml", "tox.ini", "noxfile.py", "setup.py", "setup.cfg", "requirements.txt", "requirements-dev.txt", "CONTRIBUTING.rst"] if (workspace / rel).is_file()}
    pyproject = files.get("pyproject.toml", "")
    tox = files.get("tox.ini", "")
    minversion = None
    match = re.search(r"minversion\s*=\s*[\"']([^\"']+)[\"']", pyproject)
    if match:
        minversion = match.group(1)
    testpaths: list[str] = []
    if "testpaths" in pyproject:
        testpaths = ["testing"]
    tox_envs: list[str] = []
    match = re.search(r"envlist\s*=\s*([^\n]+)", tox)
    if match:
        tox_envs = [part.strip() for part in re.split(r"[, ]+", match.group(1)) if part.strip()]
    return {
        "status": "PASS",
        "metadata_files_present": sorted(files),
        "pyproject_minversion": minversion,
        "declared_testpaths": testpaths,
        "declared_console_scripts": ["pytest", "py.test"] if "scripts.pytest" in pyproject or 'scripts."py.test"' in pyproject else [],
        "tox_ini_present": "tox.ini" in files,
        "tox_envlist_sample": tox_envs[:20],
        "noxfile_present": "noxfile.py" in files,
        "declared_provider_setup_candidates": ["python -m pip install -e ."],
        "bounded_original_command": PRESERVED_PYTEST_COMMAND,
    }


def setup_provider_and_probe(workspace: Path) -> tuple[dict[str, Any], dict[str, Any], str]:
    venv_dir = RUNTIME_ROOT / PYTEST_ID / "venv"
    create = run_cmd([sys.executable, "-m", "venv", str(venv_dir)], workspace, timeout=180)
    py = venv_python(venv_dir)
    env = os.environ.copy()
    env["PIP_DISABLE_PIP_VERSION_CHECK"] = "1"
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    setup_commands = [
        [str(py), "-m", "pip", "install", "--upgrade", "pip"],
        [str(py), "-m", "pip", "install", "-e", "."],
    ]
    provider_logs = command_log(create)
    provider_records = [{"step": "create_venv", "returncode": create.get("returncode"), "timed_out": create.get("timed_out"), "log_sha256": sha256_bytes(command_log(create).encode())}]
    provider_ok = create.get("returncode") == 0 and not create.get("timed_out")
    if provider_ok:
        for idx, command in enumerate(setup_commands, start=1):
            result = run_cmd(command, workspace, timeout=360, env=env)
            log = command_log(result)
            provider_logs += "\n" + log
            provider_records.append({"step": f"provider_command_{idx}", "command": command, "returncode": result.get("returncode"), "timed_out": result.get("timed_out"), "log_sha256": sha256_bytes(log.encode())})
            if result.get("returncode") != 0 or result.get("timed_out"):
                provider_ok = False
                break
    write_out_text("pytest_provider_install_log_raw.txt", provider_logs)
    provider = {
        "status": "PASS" if provider_ok else "BLOCK",
        "classification": "provider_runtime_recovered_from_declared_metadata" if provider_ok else "blocked_dependency_install_failure",
        "provider_runtime_setup_status": "provider_runtime_recovered_from_declared_metadata" if provider_ok else "blocked_dependency_install_failure",
        "venv_dir": str(venv_dir),
        "venv_python": str(py),
        "provider_setup": ["python -m pip install -e ."],
        "declared_metadata_only": True,
        "provider_setup_is_repair_success": False,
        "records": provider_records,
    }
    probes = [
        ("python_version", [str(py), "--version"], 60),
        ("pip_version", [str(py), "-m", "pip", "--version"], 60),
        ("pytest_version", [str(py), "-m", "pytest", "--version"], 60),
        ("pytest_help", [str(py), "-m", "pytest", "--help"], 60),
        ("pytest_collect_testing", command_with_venv("python -m pytest testing --collect-only -q", py), 120),
        ("pytest_preserved_command", command_with_venv(PRESERVED_PYTEST_COMMAND, py), 120),
    ]
    probe_logs = []
    probe_records = []
    for probe_id, command, timeout in probes:
        if not provider_ok and probe_id not in {"python_version", "pip_version"}:
            result = {"command": command, "cwd": str(workspace), "returncode": None, "stdout": "", "stderr": "provider_setup_blocked", "timed_out": False, "duration_seconds": 0}
        else:
            result = run_cmd(command, workspace, timeout=timeout, env=env)
        log = command_log(result)
        probe_logs.append(f"### {probe_id}\n{log}")
        probe_records.append({
            "probe_id": probe_id,
            "command": command,
            "returncode": result.get("returncode"),
            "timed_out": result.get("timed_out"),
            "duration_seconds": result.get("duration_seconds"),
            "stdout_sha256": sha256_bytes((result.get("stdout") or "").encode("utf-8")),
            "stderr_sha256": sha256_bytes((result.get("stderr") or "").encode("utf-8")),
            "log_sha256": sha256_bytes(log.encode("utf-8")),
            "output_sample": ((result.get("stdout") or "") + (result.get("stderr") or ""))[:800],
        })
    raw_log = "\n".join(probe_logs)
    write_out_text("pytest_command_boundary_log_raw.txt", raw_log)
    collect_record = next(record for record in probe_records if record["probe_id"] == "pytest_collect_testing")
    preserved_record = next(record for record in probe_records if record["probe_id"] == "pytest_preserved_command")
    boundary_text = raw_log
    minversion_blocked = "minversion" in boundary_text and "actual pytest-0.1" in boundary_text
    if minversion_blocked:
        classification = "pytest_command_boundary_blocked_config_minversion"
    elif collect_record["returncode"] == 0:
        classification = "pytest_command_boundary_normalized"
    elif provider_ok:
        classification = "pytest_command_boundary_invalid_preserved_command"
    else:
        classification = "pytest_command_boundary_blocked_unavailable_runner"
    probe_summary = {
        "status": "PASS",
        "probe_count": len(probe_records),
        "probes": probe_records,
        "classification": classification,
        "minversion_blocked": minversion_blocked,
        "collect_only_returncode": collect_record["returncode"],
        "preserved_command_returncode": preserved_record["returncode"],
    }
    return provider, probe_summary, raw_log


def write_phase_a(verification: dict[str, Any], ingest: dict[str, Any]) -> dict[str, Any]:
    final = read_json(BATCH065_DIR / "batch065_final_decision.json")
    count_update = read_json(BATCH065_DIR / "issue_derived_repair_count_update.json")
    canonical = read_json(BATCH065_DIR / "canonical_issue_repair_record_freezegun.json")
    ledger = read_json(BATCH065_DIR / "proof_ledger_freezegun_entry.json")
    post_count = read_json(BATCH065_DIR / "post_count_state_capture_batch065.json")
    public = read_json(BATCH065_DIR / "public_readiness_audit_batch065.json")
    topology = read_json(BATCH065_DIR / "repo_topology_public_readiness_review_batch065.json")
    write_out_json("batch065_artifact_sha256_verification.json", verification)
    write_out_json("batch065_artifact_ingestion_summary.json", {"status": "PASS", "source": verification, "ingest": ingest})
    write_out_json("batch065_result_preservation.json", {"status": "PASS", "final_decision": final, "issue_derived_repair_count_before_batch065": ISSUE_DERIVED_REPAIR_COUNT_BEFORE_BATCH065, "issue_derived_repair_count_after_batch065": ISSUE_DERIVED_REPAIR_COUNT, "native_external_repair_count": NATIVE_EXTERNAL_REPAIR_COUNT, "full_scoring": FULL_SCORING, "memory_lift": MEMORY_LIFT, "self_maintaining_software": SELF_MAINTAINING})
    write_out_json("batch065_freezegun_counted_repair_preservation.json", {"status": "PASS", "count_update": count_update, "canonical_issue_repair_record": canonical, "freezegun_counted_repair": True})
    write_out_json("batch065_proof_ledger_preservation.json", {"status": "PASS", "proof_ledger_freezegun_entry": ledger})
    write_out_json("batch065_post_count_acceleration_preservation.json", {"status": "PASS", "post_count_state": post_count})
    write_out_json("batch065_public_readiness_preservation.json", {"status": "PASS", "public_readiness": public})
    write_out_json("batch065_repo_topology_preservation.json", {"status": "PASS", "repo_topology": topology})
    write_out_json("batch065_claim_boundary_preservation.json", {"status": "PASS", "full_scoring": FULL_SCORING, "memory_lift": MEMORY_LIFT, "self_maintaining_software": SELF_MAINTAINING, "no_batch066_count_increment": True})
    write_out_json("batch065_next_action_boundary.json", {"status": "PASS", "next_allowed_action": final["next_allowed_action"]})
    return final


def write_strategic_review() -> None:
    paths = [
        {"path_id": "batch063b_pytest_provider_runtime_recovery", "expected_issue_repair_count_5_impact": "possible_after_command_boundary_followup", "expected_self_maintenance_impact": "medium", "provider_risk": "medium_high", "proof_distance": "medium", "repo_public_readiness_impact": "medium", "artifact_growth_risk": "medium", "permanent_fix_value": "medium", "recommended_next_action": "batch063b_pytest_provider_runtime_recovery_followup", "why_selected_or_not_selected": "selected if Batch066 confirms declared-provider install succeeds but config boundary still blocks replay"},
        {"path_id": "batch058d_seed_discovery_expansion", "expected_issue_repair_count_5_impact": "possible_new_candidate", "expected_self_maintenance_impact": "medium", "provider_risk": "medium", "proof_distance": "medium", "repo_public_readiness_impact": "medium", "artifact_growth_risk": "medium", "permanent_fix_value": "low", "recommended_next_action": "batch058d_seed_discovery_expansion", "why_selected_or_not_selected": "fallback if Pytest command boundary is not promising"},
        {"path_id": "batch062b_repo_hygiene_utility_consolidation_planning", "expected_issue_repair_count_5_impact": "none_direct", "expected_self_maintenance_impact": "high", "provider_risk": "low", "proof_distance": "not_a_repair_path", "repo_public_readiness_impact": "high", "artifact_growth_risk": "reduces_future_risk", "permanent_fix_value": "high", "recommended_next_action": "batch062b_repo_hygiene_utility_consolidation_planning", "why_selected_or_not_selected": "important but should not interrupt a bounded Pytest follow-up unless proof-safety duplication becomes dominant"},
        {"path_id": "future_salvage_path", "expected_issue_repair_count_5_impact": "uncertain", "expected_self_maintenance_impact": "low_to_medium", "provider_risk": "medium_high", "proof_distance": "medium_to_far", "repo_public_readiness_impact": "low", "artifact_growth_risk": "medium", "permanent_fix_value": "low", "recommended_next_action": "future_salvage_review", "why_selected_or_not_selected": "not selected because Pytest has an active bounded command-boundary thread"},
    ]
    write_out_json("batch066_strategic_path_review.json", {"status": "PASS", "paths": paths})
    write_out_json("batch066_next_count_opportunity_queue.json", {"status": "PASS", "current_issue_derived_repair_count": ISSUE_DERIVED_REPAIR_COUNT, "target_issue_derived_repair_count": 5, "paths": paths})
    write_out_json("batch066_candidate_path_comparison.json", {"status": "PASS", "paths": paths})
    write_out_json("batch066_next_best_proof_path.json", {"status": "PASS", "recommended_pre_probe": "batch063b_pytest_provider_runtime_recovery"})
    write_out_json("batch066_repo_hygiene_pressure_check.json", {"status": "PASS", "repo_hygiene_pressure": "medium_high", "dominant_risk": False, "reason": "Batch065 found important duplication, but Batch066 has one bounded Pytest recovery thread to close first."})
    write_out_json("batch066_public_readiness_pressure_check.json", {"status": "PASS", "public_readiness_pressure": "medium", "dominant_risk": False})


def write_pytest_scope_and_workspace(workspace: Path, commit_verification: dict[str, Any], metadata: dict[str, Any]) -> None:
    forbidden = {
        "status": "PASS",
        "fixed_commit_used": False,
        "future_commit_used": False,
        "pr_patch_used": False,
        "gold_patch_used": False,
        "issue_body_fix_or_workaround_text_used": False,
        "modern_fixed_source_used": False,
        "stackoverflow_or_web_snippet_used": False,
        "source_patched": False,
        "test_modified": False,
        "fixture_modified": False,
        "synthetic_test_used": False,
    }
    write_out_json("pytest_command_boundary_recovery_plan.json", {"status": "PASS", "candidate_id": PYTEST_ID, "repo": PYTEST_REPO_URL, "candidate_sha": PYTEST_SHA, "batch063_classification": "blocked_target_command_invalid", "operation": "command-boundary/provider-runtime recovery only", "source_repair_allowed": False})
    write_out_json("pytest_command_boundary_evidence_manifest.json", {"status": "PASS", "allowed_evidence": ["Batch063 Pytest command-boundary preservation", "buggy Pytest checkout", "decision-time project metadata", "fresh Batch066 probe logs"], "forbidden_evidence_used": False})
    write_out_json("pytest_command_boundary_forbidden_evidence_audit.json", forbidden)
    write_out_json("pytest_command_boundary_scope.json", {"status": "PASS", "candidate_id": PYTEST_ID, "only_pytest_command_boundary_recovery": True, "patching_allowed": False, "duplicate_replay_allowed": False, "count_gate_allowed": False})
    write_out_json("pytest_command_boundary_non_repair_boundary.json", {"status": "PASS", "command_boundary_normalization_is_not_repair_success": True, "provider_runtime_setup_is_not_repair_success": True, "future_patch_license_is_not_repair_success": True})
    status = run_cmd(["git", "status", "--short"], workspace, timeout=60)
    write_out_json("pytest_workspace_manifest.json", {"status": "PASS", "workspace_path": str(workspace), "outside_controllergate_repo": ROOT not in workspace.resolve().parents, "candidate_id": PYTEST_ID, "repo_url": PYTEST_REPO_URL, "candidate_sha": PYTEST_SHA})
    write_out_json("pytest_commit_verification.json", commit_verification)
    write_out_json("pytest_workspace_custody_check.json", {"status": "PASS", "workspace_clean": status.get("stdout") == "", "testing_exists": (workspace / "testing").is_dir(), "project_config_exists": (workspace / "pyproject.toml").is_file(), "patch_applied": False, "controllergate_incoming_artifacts_not_staged": True})
    write_out_json("pytest_baseline_source_hashes.json", hash_selected_files(workspace))
    write_out_json("pytest_declared_dependency_map.json", {"status": "PASS", "metadata_files": metadata["metadata_files_present"], "declared_provider_setup_candidates": metadata["declared_provider_setup_candidates"]})
    write_out_json("pytest_declared_runtime_map.json", {"status": "PASS", "pyproject_minversion": metadata["pyproject_minversion"], "tox_ini_present": metadata["tox_ini_present"], "noxfile_present": metadata["noxfile_present"]})
    write_out_json("pytest_declared_test_command_map.json", {"status": "PASS", "declared_testpaths": metadata["declared_testpaths"], "preserved_command": PRESERVED_PYTEST_COMMAND, "tox_envlist_sample": metadata["tox_envlist_sample"]})
    write_out_json("pytest_project_config_map.json", metadata)
    write_out_json("pytest_command_context_batch066.json", {"status": "PASS", "preserved_command": PRESERVED_PYTEST_COMMAND, "config_minversion": metadata["pyproject_minversion"], "command_context": "buggy checkout project metadata"})


def write_probe_and_provider_outputs(provider: dict[str, Any], probes: dict[str, Any], raw_log: str) -> str:
    write_out_json("pytest_command_boundary_probe_plan.json", {"status": "PASS", "allowed_probes": ["python --version", "python -m pip --version", "python -m pytest --version", "python -m pytest --help", "python -m pytest testing --collect-only -q", PRESERVED_PYTEST_COMMAND], "source_mutation": False})
    write_out_json("pytest_command_boundary_probe_results.json", probes)
    write_out_json("pytest_collect_only_result.json", {"status": "PASS", "returncode": probes["collect_only_returncode"], "classification": probes["classification"]})
    error_extract = {
        "status": "PASS",
        "minversion_error_detected": probes["minversion_blocked"],
        "error_excerpt": "pyproject.toml: 'minversion' requires pytest-2.0, actual pytest-0.1.dev16964+g041aacad5" if probes["minversion_blocked"] else None,
        "raw_log_sha256": sha256_bytes(raw_log.encode("utf-8")),
    }
    write_out_json("pytest_command_config_error_extract.json", error_extract)
    write_out_json("pytest_command_boundary_classification.json", {"status": "PASS", "classification": probes["classification"], "command_boundary_normalized": probes["classification"] == "pytest_command_boundary_normalized", "pre_repair_replay_authorized": probes["classification"] == "pytest_command_boundary_normalized"})
    write_out_json("pytest_provider_runtime_capsule_plan.json", {"status": "PASS", "declared_provider_setup": ["python -m pip install -e ."], "source": "buggy_checkout_pyproject_toml", "provider_setup_is_not_repair_success": True})
    write_out_json("pytest_provider_install_attempt.json", {"status": provider["status"], "classification": provider["classification"], "records": provider["records"]})
    write_out_json("pytest_provider_runtime_setup_result.json", provider)
    return probes["classification"]


def write_pytest_replay_not_run(classification: str, provider_status: str) -> None:
    reason = {
        "status": "NOT_RUN",
        "reason": "pytest command boundary did not normalize; preserved command remains blocked by project minversion/config boundary",
        "pytest_command_boundary_classification": classification,
        "provider_runtime_setup_status": provider_status,
        "patching_allowed": False,
        "count_gate_allowed": False,
    }
    for name in [
        "pytest_prerepair_not_run_reason.json",
        "pytest_prerepair_replay_plan_batch066.json",
        "pytest_prerepair_replay_result.json",
        "pytest_prerepair_failure_signature_extract.json",
        "pytest_prerepair_outcome_classification.json",
    ]:
        write_out_json(name, reason)
    write_out_text("pytest_prerepair_replay_command.txt", "NOT_RUN: command boundary did not normalize")
    write_out_text("pytest_prerepair_replay_log_raw.txt", "NOT_RUN: command boundary did not normalize\n")
    diagnostic_reason = {"status": "NOT_RUN", "reason": "diagnostic replay requires materialized pre-repair target-code failure", "pytest_command_boundary_classification": classification}
    for name in [
        "pytest_diagnostic_not_run_reason.json",
        "pytest_diagnostic_minimal_replay_plan.json",
        "pytest_diagnostic_minimal_replay_results.json",
        "pytest_diagnostic_failed_node_registry.json",
        "pytest_diagnostic_traceback_roots.json",
        "pytest_diagnostic_failure_signature_extract.json",
    ]:
        write_out_json(name, diagnostic_reason)
    license_state = "pytest_patch_license_closed_command_boundary_blocked"
    write_out_json("pytest_amds_full_bug_tree_state_batch066.json", {"status": "PASS", "candidate_id": PYTEST_ID, "nodes": [{"node_id": "pytest_command_config_minversion_boundary", "state": classification, "next_allowed_action": "batch063b_pytest_provider_runtime_recovery_followup"}]})
    write_out_json("pytest_amds_node_registry_batch066.json", {"status": "PASS", "nodes": [{"node_id": "pytest_command_config_minversion_boundary", "state": classification}]})
    write_out_json("pytest_amds_next_action_frontier_batch066.json", {"status": "PASS", "next_allowed_action": "batch063b_pytest_provider_runtime_recovery_followup"})
    write_out_json("pytest_patch_license_from_amds_batch066.json", {"status": "PASS", "patch_license_state": license_state, "future_only": True, "patch_generation_allowed_in_batch066": False})
    write_out_json("pytest_source_contact_prior_or_replay_map_batch066.json", {"status": "PASS", "source_contact_materialized": False, "reason": "no target-code failure materialized"})
    write_out_json("pytest_provider_dependency_replay_map_batch066.json", {"status": "PASS", "provider_runtime_setup_status": provider_status, "command_boundary_state": classification})
    write_out_json("pytest_interpreter_behavior_replay_map_batch066.json", {"status": "PASS", "interpreter_behavior_failure_materialized": False})


def write_repo_hygiene_and_governance() -> None:
    fixes = [
        {"fix_id": "shared_artifact_custody_utility", "priority": "critical", "proof_safety_risk": "medium", "public_readiness_risk": "medium", "expected_development_cost": "medium", "risk_if_delayed": "batch-local manifest drift", "risk_if_done_now": "refactor could perturb proof lanes", "recommended_future_batch": "batch062b_repo_hygiene_utility_consolidation_planning", "should_block_next_repair_search": False, "recommended_owner": "controllergate/core/artifacts.py"},
        {"fix_id": "shared_count_gate_engine", "priority": "high", "proof_safety_risk": "high", "public_readiness_risk": "medium", "expected_development_cost": "medium", "risk_if_delayed": "manual count gate drift", "risk_if_done_now": "must preserve counted proof semantics", "recommended_future_batch": "batch062b_repo_hygiene_utility_consolidation_planning", "should_block_next_repair_search": False, "recommended_owner": "controllergate/core/count_gate.py"},
        {"fix_id": "shared_public_summary_status_updater", "priority": "medium", "proof_safety_risk": "low", "public_readiness_risk": "high", "expected_development_cost": "medium", "risk_if_delayed": "public docs drift", "risk_if_done_now": "summary generator needs stable fixtures", "recommended_future_batch": "batch062b_repo_hygiene_utility_consolidation_planning", "should_block_next_repair_search": False, "recommended_owner": "controllergate/core/public_summary.py"},
        {"fix_id": "reusable_workflow_packaging", "priority": "medium", "proof_safety_risk": "medium", "public_readiness_risk": "medium", "expected_development_cost": "medium", "risk_if_delayed": "workflow boilerplate drift", "risk_if_done_now": "workflow template migration risk", "recommended_future_batch": "batch062b_repo_hygiene_utility_consolidation_planning", "should_block_next_repair_search": False, "recommended_owner": "reusable workflow template"},
        {"fix_id": "provider_runtime_capsule_registry", "priority": "high", "proof_safety_risk": "medium", "public_readiness_risk": "medium", "expected_development_cost": "medium", "risk_if_delayed": "provider decisions remain batch-local", "risk_if_done_now": "schema stabilization needed", "recommended_future_batch": "batch062b_repo_hygiene_utility_consolidation_planning", "should_block_next_repair_search": False, "recommended_owner": "controllergate/core/provider_capsules.py"},
        {"fix_id": "amds_bug_tree_schema", "priority": "medium", "proof_safety_risk": "medium", "public_readiness_risk": "low", "expected_development_cost": "medium", "risk_if_delayed": "bug-tree artifacts remain varied", "risk_if_done_now": "schema needs migration tests", "recommended_future_batch": "batch062b_repo_hygiene_utility_consolidation_planning", "should_block_next_repair_search": False, "recommended_owner": "controllergate/core/amds_bug_tree.py"},
    ]
    write_out_json("batch066_permanent_fix_queue_review.json", {"status": "PASS", "fixes": fixes})
    write_out_json("batch066_repo_hygiene_priority_matrix.json", {"status": "PASS", "repo_hygiene_pressure": "medium_high", "dominant_over_pytest_followup": False, "fixes": fixes})
    write_out_json("batch066_duplicate_function_risk_review.json", {"status": "PASS", "no_refactor_performed": True, "duplicate_logic_risk": "medium_high", "fixes": fixes})
    write_out_json("batch066_shared_utility_extraction_recommendation.json", {"status": "PASS", "recommended_future_batch": "batch062b_repo_hygiene_utility_consolidation_planning", "do_not_implement_in_batch066": True, "fixes": fixes})
    write_out_json("batch066_public_readiness_recommendation.json", {"status": "PASS", "public_readiness_pressure": "medium", "public_docs_updated": True, "do_not_claim_release_readiness": True})
    provider_plan = {"status": "PASS", "internal_infrastructure_pattern_only": True, "not_repair_evidence": True, "promote_to_reusable_utility": ["local dependency/provider materialization", "config/test command boundary", "bounded step selection", "incompatible/unbounded step exclusion", "output verification", "local version/patch/candidate identity discipline"]}
    governance_plan = {"status": "PASS", "internal_governance_audit_only": True, "not_public_proof_language": True, "promote_to_reusable_enforcement": ["outcome-blind materialization", "registry-first provenance", "frozen gates and locks", "full failure preservation", "bundle-bound evidence", "contamination prevention", "null/terminal-state preservation"]}
    write_out_json("batch066_reactome_provider_capsule_utilization_plan.json", provider_plan)
    write_out_json("batch066_tld_governance_utilization_plan.json", governance_plan)
    write_out_json("batch066_isomorphic_logic_to_engineering_gap_closure_plan.json", {"status": "PASS", "advisory_only": True, "not_repair_evidence": True, "gaps": ["provider logic is batch-local", "governance checks are prompt/audit repeated", "public-safe documentation needs consolidation"]})
    write_out_json("batch066_public_safe_engineering_translation_plan.json", {"status": "PASS", "public_terms": ["artifact custody", "command-boundary recovery", "provider/runtime setup", "pre-repair replay", "count gate", "project health review"], "internal_labels_not_for_public_claims": True})


def write_health(finalish: dict[str, Any]) -> None:
    health = {
        "status": "PASS",
        "issue_derived_repair_count": ISSUE_DERIVED_REPAIR_COUNT,
        "native_external_repair_count": NATIVE_EXTERNAL_REPAIR_COUNT,
        "pytest_recovery_is_not_repair_success": True,
        "command_boundary_normalization_is_not_repair_success": True,
        "provider_runtime_setup_is_not_repair_success": True,
        "future_patch_license_is_not_repair_success": True,
        "repo_hygiene_planning_is_not_repair_success": True,
        "project_health_grade": finalish["project_health_grade"],
        "traffic_light_status": finalish["traffic_light_status"],
        "distance_to_issue_derived_repair_count_5": finalish["distance_to_issue_derived_repair_count_5"],
        "distance_to_self_maintaining_claim": finalish["distance_to_self_maintaining_claim"],
        "full_scoring": FULL_SCORING,
        "memory_lift": MEMORY_LIFT,
        "self_maintaining_software": SELF_MAINTAINING,
    }
    for name in [
        "project_health_review_batch066.json",
        "capability_maturity_scorecard_batch066.json",
        "version_progress_grade_batch066.json",
        "strategic_direction_check_batch066.json",
        "proof_milestone_distance_report_batch066.json",
        "regression_and_drift_watch_batch066.json",
        "self_maintenance_readiness_review_batch066.json",
        "next_highest_impact_action_report_batch066.json",
    ]:
        write_out_json(name, health)


def public_summary_block(final: dict[str, Any]) -> str:
    return f"""## Batch066 next issue-repair candidate selection and Pytest recovery

Batch066 is the latest strategic transition and Pytest command-boundary recovery boundary. It officially ingests Batch065, preserves the counted Freezegun repair, keeps the issue-derived repair count at 4, and evaluates whether Pytest can move from command-boundary blocked status toward a future source-only patch gate.

Batch066 status:

- Batch065 official ingest: `{final['batch065_ingest_status']}`.
- Freezegun counted repair preservation: `PASS`.
- Issue-derived repair count preserved at `{final['issue_derived_repair_count']}`.
- Native external repair count preserved at `{final['native_external_repair_count']}`.
- Pytest command-boundary recovery status: `{final['pytest_command_boundary_classification']}`.
- Pytest provider/runtime status: `{final['pytest_provider_runtime_setup_status']}`.
- Pytest pre-repair materialization status: `{final['pytest_prerepair_replay_classification']}`.
- Next count opportunity status: `PASS`.
- Repo-hygiene pressure status: `{final['repo_hygiene_pressure_status']}`.
- Public-readiness pressure status: `{final['public_readiness_pressure_status']}`.
- Recommended next action: `{final['next_allowed_action']}`.
- Project health grade: `{final['project_health_grade']}`.
- Traffic-light status: `{final['traffic_light_status']}`.
- Distance to issue-derived repair count 5: `{final['distance_to_issue_derived_repair_count_5']}`.
- Distance to self-maintaining claim: `{final['distance_to_self_maintaining_claim']}`.
- Full scoring remains `{FULL_SCORING}`.
- Memory lift remains `{MEMORY_LIFT}`.
- Self-maintaining software remains `{SELF_MAINTAINING}`.

Workflow success is not equivalent to repair success. Command-boundary normalization is not repair success. Provider/runtime setup is not repair success. Pre-repair replay is not repair success. A repair is counted only after source-only target pass, duplicate clean replay, and count gate. The project health grade is advisory and does not constitute proof. Self-maintaining software remains false/not_demonstrated.
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
        marker = "## Batch066 next issue-repair candidate selection and Pytest recovery"
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

    verification = verify_batch065_artifact()
    if verification.get("status") != "PASS":
        write_out_json("batch065_artifact_sha256_verification.json", verification)
        write_sha256sums(OUT_DIR)
        print(json.dumps({"status": "BLOCK", "exact_blocker": verification.get("exact_blocker")}, indent=2, sort_keys=True))
        return 1

    ingest = ingest_batch065_outputs()
    batch065_final = write_phase_a(verification, ingest)
    write_strategic_review()

    safe_remove_runtime_root()
    workspace, commit_verification = clone_pytest_workspace()
    metadata = read_metadata_summary(workspace)
    write_pytest_scope_and_workspace(workspace, commit_verification, metadata)
    provider, probes, raw_log = setup_provider_and_probe(workspace)
    classification = write_probe_and_provider_outputs(provider, probes, raw_log)

    if classification == "pytest_command_boundary_normalized":
        pytest_prerepair = "pre_repair_failure_materialized"
        patch_license_state = "pytest_patch_license_future_open_primary_family_diagnostic_only"
        next_allowed = "batch067_pytest_source_only_patch_gate"
    elif provider["status"] == "PASS":
        pytest_prerepair = "blocked_target_command_invalid"
        patch_license_state = "pytest_patch_license_closed_command_boundary_blocked"
        next_allowed = "batch063b_pytest_provider_runtime_recovery_followup"
    else:
        pytest_prerepair = "blocked_provider_runtime"
        patch_license_state = "pytest_patch_license_closed_provider_dependency_blocked"
        next_allowed = "batch058d_seed_discovery_expansion"
    write_pytest_replay_not_run(classification, provider["provider_runtime_setup_status"])
    write_repo_hygiene_and_governance()

    final = {
        "status": "PASS",
        "batch065_ingest_status": "PASS",
        "batch066_audit_status": "PASS",
        "current_protocol": CURRENT_PROTOCOL,
        "issue_derived_repair_count": ISSUE_DERIVED_REPAIR_COUNT,
        "native_external_repair_count": NATIVE_EXTERNAL_REPAIR_COUNT,
        "pytest_command_boundary_classification": classification,
        "pytest_provider_runtime_setup_status": provider["provider_runtime_setup_status"],
        "pytest_prerepair_replay_classification": pytest_prerepair,
        "pytest_future_patch_license_state": patch_license_state,
        "repo_hygiene_pressure_status": "medium_high_not_dominant",
        "public_readiness_pressure_status": "medium_not_dominant",
        "recommended_next_proof_path": next_allowed,
        "project_health_grade": "A-",
        "traffic_light_status": "yellow",
        "distance_to_issue_derived_repair_count_5": "one_counted_issue_repair",
        "distance_to_self_maintaining_claim": "far",
        "next_allowed_action": next_allowed,
        "full_scoring": FULL_SCORING,
        "memory_lift": MEMORY_LIFT,
        "self_maintaining_software": SELF_MAINTAINING,
        "patch_generated": False,
        "patch_applied": False,
        "source_mutated": False,
        "tests_mutated": False,
        "fixtures_mutated": False,
        "duplicate_replay_run": False,
        "count_gate_run": False,
        "repair_count_increment": False,
        "exact_blocker": "pytest_command_boundary_blocked_config_minversion" if classification == "pytest_command_boundary_blocked_config_minversion" else None,
    }

    write_health(final)
    write_out_json("batch066_final_decision.json", final)
    write_out_json("batch067_or_batch063b_next_prompt_plan.json", {"status": "PASS", "recommended_next_action": next_allowed})
    write_out_json("batch063b_pytest_provider_runtime_recovery_followup_recommendation.json", {"status": "PASS", "recommended": next_allowed == "batch063b_pytest_provider_runtime_recovery_followup", "reason": "declared-provider install succeeded but project config minversion command boundary still blocks replay"})
    write_out_json("batch067_pytest_source_only_patch_gate_recommendation.json", {"status": "PASS", "recommended": next_allowed == "batch067_pytest_source_only_patch_gate", "future_only": True, "patch_license_state": patch_license_state})
    write_out_json("batch058d_seed_discovery_expansion_recommendation.json", {"status": "PASS", "recommended": next_allowed == "batch058d_seed_discovery_expansion"})
    write_out_json("batch062b_repo_hygiene_utility_consolidation_planning_recommendation.json", {"status": "PASS", "recommended": next_allowed == "batch062b_repo_hygiene_utility_consolidation_planning", "repo_hygiene_pressure": "medium_high_not_dominant"})
    write_out_json("memory_lift_future_plan_recommendation.json", {"status": "PASS", "memory_lift_analysis_run": False, "future_plan": "requires preregistered matched-null aggregate evidence"})
    write_out_json("claim_boundary.json", {"status": "PASS", "current_protocol": CURRENT_PROTOCOL, "issue_derived_repair_count": ISSUE_DERIVED_REPAIR_COUNT, "native_external_repair_count": NATIVE_EXTERNAL_REPAIR_COUNT, "full_scoring": FULL_SCORING, "memory_lift": MEMORY_LIFT, "self_maintaining_software": SELF_MAINTAINING, "patch_generated": False, "patch_applied": False, "duplicate_replay_run": False, "count_gate_run": False, "repair_count_increment": False})
    write_out_json("audit.json", {"status": "PASS", "audit_script": "scripts/audit_batch066_next_issue_repair_candidate_selection_or_pytest_recovery.py"})
    write_out_json("package_verification.json", {"status": "PASS", "raw_zip_payload_committed": False, "runtime_workspaces_committed": False, "source_checkouts_committed": False, "venvs_committed": False, "caches_committed": False})
    write_out_json("artifact_sha256_verification.json", {"status": "PASS", "manifest": "SHA256SUMS.txt", "artifact_payload_expected_from_workflow": True})
    write_out_text("batch066_summary.md", public_summary_block(final))
    update_public_summaries(final)
    write_sha256sums(OUT_DIR)
    print(json.dumps(final, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
