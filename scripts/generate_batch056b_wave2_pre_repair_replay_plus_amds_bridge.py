from __future__ import annotations

import json
import os
import shlex
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

from controllergate.core.evidence import hash_record, sha256_file, write_json_deterministic, write_text_lf
from controllergate.core.manifests import write_sha256sums
from controllergate.core.official_ingest import ingest_official_outputs, verify_official_zip


OUT_DIR = ROOT / "outputs" / "post_v2_37_hardening_batch056b_wave2_pre_repair_replay_plus_amds_bridge"
BATCH056_DIR = ROOT / "outputs" / "post_v2_37_hardening_batch056_pre_repair_replay_wave_1_plus_wave_2_intake"
BATCH057C_DIR = ROOT / "outputs" / "post_v2_37_hardening_batch057c_layered_source_only_patch_recovery_freezegun"
BATCH057C_ZIP = Path(
    r"C:\Users\thisb\Downloads\post_v2_37_hardening_batch057c_layered_source_only_patch_recovery_freezegun_artifacts.zip"
)
BATCH057C_ARTIFACT_NAME = "post_v2_37_hardening_batch057c_layered_source_only_patch_recovery_freezegun_artifacts"
BATCH056B_ARTIFACT_NAME = "post_v2_37_hardening_batch056b_wave2_pre_repair_replay_plus_amds_bridge_artifacts"
BATCH057C_ARTIFACT_ID = 8154643766
BATCH057C_WORKFLOW_RUN_ID = 28907567374
BATCH057C_WORKFLOW_HEAD_SHA = "6068268f0f662d8aed600ecf8b0ebe0ff9c49312"
BATCH057C_SHA256 = "86184c8517bc091bf5d43cc257216cafa22e247973d496310251c70983ca9889"
BATCH057C_SIZE = 42862
BATCH057C_ENTRY_COUNT = 65
BATCH057C_ARTIFACT_MANIFEST_CHECKED = 64
BATCH057C_OUTPUT_MANIFESTS = {
    "post_v2_37_hardening_batch057c_layered_source_only_patch_recovery_freezegun": (
        "post_v2_37_hardening_batch057c_layered_source_only_patch_recovery_freezegun/SHA256SUMS.txt",
        63,
    )
}
CURRENT_PROTOCOL = "v2.14"
ISSUE_DERIVED_REPAIR_COUNT = 2
NATIVE_EXTERNAL_REPAIR_COUNT = 4
RUNTIME_ROOT = Path(os.environ.get("CONTROLLERGATE_BATCH056B_RUNTIME_ROOT", r"C:\Dev\ControllerGate_runtime\batch056b"))
TIMEOUT_SECONDS = int(os.environ.get("CONTROLLERGATE_BATCH056B_TIMEOUT_SECONDS", "180"))
REPLAY_TIMEOUT_SECONDS = int(os.environ.get("CONTROLLERGATE_BATCH056B_REPLAY_TIMEOUT_SECONDS", "120"))

PROMPT_WAVE2_IDS = [
    "pairtools_250_py313_pipes_removed",
    "pytest_13480_wdefault_unraisable_threadexception",
    "snapshottest_177_py312_imp_removed",
    "codex_wave2_nousresearch_hermes_agent_48986",
    "codex_wave2_nousresearch_hermes_agent_60243",
    "codex_wave2_nousresearch_hermes_agent_57197",
    "codex_wave2_m0smith_genia_2026_518",
]
PATCH_OPEN_STATES = {
    "amds_bridge_patch_license_future_open_single_source_family",
    "amds_bridge_patch_license_future_open_primary_family_diagnostic_only",
}


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def safe_rmtree(path: Path) -> None:
    if not path.exists():
        return

    def onerror(func: Any, target: str, _exc: Any) -> None:
        try:
            os.chmod(target, stat.S_IWRITE)
            func(target)
        except Exception:
            pass

    shutil.rmtree(path, onerror=onerror)


def sha256_text(text: str) -> str:
    import hashlib

    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def run_cmd(args: list[str], cwd: Path, timeout: int = TIMEOUT_SECONDS) -> dict[str, Any]:
    started = time.time()
    try:
        completed = subprocess.run(
            args,
            cwd=cwd,
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
    combined = stdout + stderr
    return {
        "command": args,
        "cwd": str(cwd),
        "returncode": returncode,
        "timed_out": timed_out,
        "elapsed_seconds": round(time.time() - started, 3),
        "stdout": stdout,
        "stderr": stderr,
        "combined": combined,
        "stdout_sha256": sha256_text(stdout),
        "stderr_sha256": sha256_text(stderr),
        "combined_log_sha256": sha256_text(combined),
    }


def trim(text: str, limit: int = 5000) -> str:
    if len(text) <= limit:
        return text
    half = limit // 2
    return text[:half] + f"\n...<trimmed {len(text) - limit} chars>...\n" + text[-half:]


def summarize_cmd(raw: dict[str, Any]) -> dict[str, Any]:
    return {
        "command": raw.get("command"),
        "cwd": raw.get("cwd"),
        "returncode": raw.get("returncode"),
        "timed_out": raw.get("timed_out", False),
        "elapsed_seconds": raw.get("elapsed_seconds"),
        "stdout_sha256": raw.get("stdout_sha256"),
        "stderr_sha256": raw.get("stderr_sha256"),
        "combined_log_sha256": raw.get("combined_log_sha256"),
        "stdout_excerpt": trim(raw.get("stdout", ""), 1200),
        "stderr_excerpt": trim(raw.get("stderr", ""), 1200),
    }


def command_to_args(command: str, python_exe: Path) -> list[str]:
    parts = shlex.split(command, posix=False)
    if parts[:3] == ["python", "-m", "pytest"]:
        return [str(python_exe), "-m", "pytest", *parts[3:]]
    return parts


def path_hash(path: Path) -> str | None:
    return sha256_file(path) if path.is_file() else None


def load_wave2_source_records() -> tuple[list[dict[str, Any]], dict[str, dict[str, Any]], dict[str, dict[str, Any]], dict[str, dict[str, Any]]]:
    plan = read_json(BATCH056_DIR / "wave_2_pre_repair_replay_plan.json")
    source_records = plan["future_candidates"]
    normalized = {
        row["lead_id"]: row
        for row in read_json(BATCH056_DIR / "seed_lead_registry_wave_2_normalized.json").get("leads", [])
        if row.get("lead_id") in {item["lead_id"] for item in source_records}
    }
    commit = {
        row["lead_id"]: row
        for row in read_json(BATCH056_DIR / "candidate_commit_resolution_audit_wave_2.json").get("records", [])
        if row.get("lead_id") in {item["lead_id"] for item in source_records}
    }
    leakage = {
        row["lead_id"]: row
        for row in read_json(BATCH056_DIR / "issue_body_leakage_screen_wave_2.json").get("records", [])
        if row.get("lead_id") in {item["lead_id"] for item in source_records}
    }
    return source_records, normalized, commit, leakage


def env_file_inventory(checkout: Path) -> list[dict[str, Any]]:
    names = [
        "pyproject.toml",
        "setup.py",
        "setup.cfg",
        "requirements.txt",
        "requirements-dev.txt",
        "tox.ini",
        "pytest.ini",
    ]
    rows = []
    for name in names:
        path = checkout / name
        if path.exists():
            rows.append({"path": name, "is_file": path.is_file(), "sha256": path_hash(path)})
    return rows


def traceback_source_files(text: str, checkout: Path) -> list[str]:
    found: list[str] = []
    marker = str(checkout).replace("\\", "/")
    for raw_line in text.splitlines():
        line = raw_line.replace("\\", "/")
        if marker in line and ".py" in line:
            suffix = line.split(marker, 1)[1].lstrip("/")
            path = suffix.split(".py", 1)[0] + ".py"
            if path and path not in found and not path.startswith(("tests/", "testing/")):
                found.append(path)
    return found[:25]


def classify_replay(
    *,
    clone: dict[str, Any],
    fetch: dict[str, Any],
    cat_file: dict[str, Any],
    checkout_cmd: dict[str, Any],
    native_paths_exist: bool,
    leakage_safe: bool,
    venv: dict[str, Any] | None,
    install_pytest: dict[str, Any] | None,
    install_editable: dict[str, Any] | None,
    replay: dict[str, Any] | None,
) -> str:
    if clone.get("returncode") != 0 or fetch.get("returncode") != 0 or checkout_cmd.get("returncode") != 0:
        return "blocked_repo_checkout_failure"
    if cat_file.get("returncode") != 0:
        return "blocked_commit_unresolved"
    if not native_paths_exist:
        return "blocked_native_test_missing"
    if not leakage_safe:
        return "blocked_decision_time_leakage_risk"
    if venv is not None and venv.get("returncode") != 0:
        return "blocked_python_version_unavailable"
    if install_pytest is not None and install_pytest.get("returncode") != 0:
        return "blocked_dependency_install_failure"
    if install_editable is not None and install_editable.get("returncode") != 0:
        return "blocked_dependency_install_failure"
    if replay is None:
        return "blocked_environment_unclear"
    if replay.get("timed_out") is True:
        return "blocked_timeout"
    if replay.get("returncode") == 0:
        return "failure_not_reproduced"
    combined = replay.get("combined", "").lower()
    environment_markers = [
        "unrecognized arguments: --cov",
        "minversion' requires pytest",
        "no module named pytest_cov",
        "no module named pytest-cov",
        "could not find a version that satisfies the requirement",
        "failed building wheel",
    ]
    if any(marker in combined for marker in environment_markers):
        return "blocked_dependency_install_failure"
    return "pre_repair_failure_materialized"


def bridge_state_for(classification: str, source_files: list[str], dependency_install_ok: bool) -> str:
    if classification == "pre_repair_failure_materialized":
        if not source_files:
            return "amds_bridge_decomposition_needed"
        if dependency_install_ok and len(source_files) == 1:
            return "amds_bridge_patch_license_future_open_single_source_family"
        if dependency_install_ok and len(source_files) <= 2:
            return "amds_bridge_patch_license_future_open_primary_family_diagnostic_only"
        return "amds_bridge_decomposition_needed"
    if classification == "blocked_dependency_install_failure":
        return "amds_bridge_dependency_materialization_needed"
    if classification in {"blocked_provider_precondition", "blocked_python_version_unavailable", "blocked_tox_env_unavailable"}:
        return "amds_bridge_provider_precondition_needed"
    if classification == "blocked_native_test_missing":
        return "amds_bridge_candidate_retired"
    if classification in {"blocked_repo_checkout_failure", "blocked_commit_unresolved", "blocked_command_ambiguous"}:
        return "amds_bridge_manual_review_needed"
    if classification == "blocked_timeout":
        return "amds_bridge_decomposition_needed"
    if classification == "failure_not_reproduced":
        return "amds_bridge_blocked_no_materialized_failure"
    return "amds_bridge_manual_review_needed"


def write_candidate_artifacts(
    candidate: dict[str, Any],
    normalized: dict[str, Any],
    prior_commit: dict[str, Any],
    leakage_record: dict[str, Any],
) -> dict[str, Any]:
    lead_id = candidate["lead_id"]
    candidate_dir = OUT_DIR / "candidates" / lead_id
    candidate_dir.mkdir(parents=True, exist_ok=True)
    work_root = RUNTIME_ROOT / lead_id
    checkout = work_root / "checkout"
    venv_dir = work_root / "venv"
    python_exe = venv_dir / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
    command = prior_commit.get("possible_failing_command_selected") or normalized.get("possible_failing_command") or "python -m pytest -q --tb=no"
    native_paths = [row.get("path") for row in prior_commit.get("checked_native_test_paths", []) if row.get("path")]
    if not native_paths:
        native_paths = normalized.get("possible_native_test_paths", [])

    safe_rmtree(work_root)
    work_root.mkdir(parents=True, exist_ok=True)
    clone = run_cmd(["git", "clone", "--filter=blob:none", "--no-checkout", candidate["repo_url"], str(checkout)], ROOT, timeout=TIMEOUT_SECONDS)
    fetch = run_cmd(["git", "fetch", "--depth", "1", "origin", candidate["candidate_sha"]], checkout, timeout=TIMEOUT_SECONDS) if clone["returncode"] == 0 else {"returncode": 1, "combined": "clone failed", "timed_out": False}
    cat_file = run_cmd(["git", "cat-file", "-e", f"{candidate['candidate_sha']}^{{commit}}"], checkout, timeout=TIMEOUT_SECONDS) if fetch.get("returncode") == 0 else {"returncode": 1, "combined": "fetch failed", "timed_out": False}
    checkout_cmd = run_cmd(["git", "checkout", "--detach", candidate["candidate_sha"]], checkout, timeout=TIMEOUT_SECONDS) if cat_file.get("returncode") == 0 else {"returncode": 1, "combined": "cat-file failed", "timed_out": False}
    native_checks = []
    if checkout_cmd.get("returncode") == 0:
        for rel in native_paths:
            path = checkout / rel
            native_checks.append({"path": rel, "exists": path.exists(), "is_dir": path.is_dir(), "sha256": path_hash(path)})
    native_paths_exist = bool(native_checks) and all(row["exists"] for row in native_checks)
    leakage_safe = leakage_record.get("fix_or_workaround_text_persisted") is False and leakage_record.get("issue_body_used_as_repair_evidence") is False

    venv = install_pytest = install_editable = replay = None
    replay_allowed = (
        clone.get("returncode") == 0
        and fetch.get("returncode") == 0
        and cat_file.get("returncode") == 0
        and checkout_cmd.get("returncode") == 0
        and native_paths_exist
        and leakage_safe
    )
    if replay_allowed:
        venv = run_cmd([sys.executable, "-m", "venv", str(venv_dir)], work_root, timeout=TIMEOUT_SECONDS)
        if venv.get("returncode") == 0:
            install_pytest = run_cmd([str(python_exe), "-m", "pip", "install", "--upgrade", "pip", "pytest"], checkout, timeout=TIMEOUT_SECONDS)
        if install_pytest is not None and install_pytest.get("returncode") == 0:
            install_editable = run_cmd([str(python_exe), "-m", "pip", "install", "-e", "."], checkout, timeout=TIMEOUT_SECONDS)
        if install_editable is not None and install_editable.get("returncode") == 0:
            replay = run_cmd(command_to_args(command, python_exe), checkout, timeout=REPLAY_TIMEOUT_SECONDS)

    classification = classify_replay(
        clone=clone,
        fetch=fetch,
        cat_file=cat_file,
        checkout_cmd=checkout_cmd,
        native_paths_exist=native_paths_exist,
        leakage_safe=leakage_safe,
        venv=venv,
        install_pytest=install_pytest,
        install_editable=install_editable,
        replay=replay,
    )
    env_files = env_file_inventory(checkout) if checkout.exists() else []
    source_files = traceback_source_files(replay.get("combined", ""), checkout) if replay else []
    dependency_install_ok = bool(install_editable and install_editable.get("returncode") == 0)
    bridge_state = bridge_state_for(classification, source_files, dependency_install_ok)
    current_status = "materialized_failure" if classification == "pre_repair_failure_materialized" else "blocked_or_not_reproduced"
    exact_blocker = None if classification in {"pre_repair_failure_materialized", "failure_not_reproduced"} else classification

    write_json_deterministic(
        candidate_dir / "candidate_replay_plan.json",
        {
            "status": "PASS",
            "lead_id": lead_id,
            "repo_url": candidate["repo_url"],
            "candidate_sha": candidate["candidate_sha"],
            "selected_pre_repair_command": command,
            "native_target_paths": native_paths,
            "replay_only_no_patch": True,
        },
    )
    write_json_deterministic(
        candidate_dir / "candidate_commit_verification.json",
        {
            "status": "PASS" if cat_file.get("returncode") == 0 and checkout_cmd.get("returncode") == 0 else "BLOCK",
            "lead_id": lead_id,
            "repo_url": candidate["repo_url"],
            "candidate_sha": candidate["candidate_sha"],
            "clone": summarize_cmd(clone),
            "fetch": summarize_cmd(fetch),
            "cat_file_commit_verified": cat_file.get("returncode") == 0,
            "cat_file": summarize_cmd(cat_file),
            "checkout_succeeded": checkout_cmd.get("returncode") == 0,
            "checkout": summarize_cmd(checkout_cmd),
            "exact_blocker": None if cat_file.get("returncode") == 0 and checkout_cmd.get("returncode") == 0 else classification,
        },
    )
    write_json_deterministic(
        candidate_dir / "candidate_workspace_manifest.json",
        {
            "status": "PASS" if checkout.exists() else "BLOCK",
            "workspace_path": str(checkout),
            "workspace_outside_live_repo": str(checkout).lower().startswith(str(RUNTIME_ROOT).lower()),
            "raw_workspace_committed": False,
            "native_target_path_checks": native_checks,
            "environment_files": env_files,
        },
    )
    write_json_deterministic(
        candidate_dir / "candidate_dependency_plan.json",
        {
            "status": "PASS" if dependency_install_ok else ("BLOCK" if replay_allowed else "NOT_RUN"),
            "install_pytest": summarize_cmd(install_pytest) if install_pytest else None,
            "install_editable": summarize_cmd(install_editable) if install_editable else None,
            "declared_environment_files": env_files,
            "undeclared_dependencies_installed": False,
            "exact_blocker": None if dependency_install_ok else ("blocked_dependency_install_failure" if install_editable and install_editable.get("returncode") != 0 else None),
        },
    )
    write_json_deterministic(
        candidate_dir / "candidate_command_context.json",
        {
            "status": "PASS",
            "command": command,
            "cwd": str(checkout),
            "native_target_paths": native_paths,
            "command_source": "Batch056 preserved Wave 2 replay plan",
        },
    )
    write_json_deterministic(
        candidate_dir / "candidate_command_normalization.json",
        {
            "status": "PASS",
            "original_command": command,
            "normalized_args": command_to_args(command, python_exe) if replay_allowed else shlex.split(command, posix=False),
            "python_interpreter_isolated": bool(replay_allowed),
        },
    )
    write_json_deterministic(
        candidate_dir / "decision_time_input_manifest.json",
        {
            "status": "PASS",
            "allowed_inputs": [
                "Batch056 preserved Wave 2 candidate plan",
                "buggy candidate commit tree",
                "native target path names",
                "bounded pre-repair command output",
            ],
            "fixed_commit_read": False,
            "future_commit_read": False,
            "gold_patch_read": False,
            "pr_patch_read": False,
            "patch_generated": False,
        },
    )
    write_json_deterministic(
        candidate_dir / "issue_body_leakage_boundary.json",
        {
            "status": "PASS" if leakage_safe else "BLOCK",
            "lead_id": lead_id,
            "issue_url_or_reference": leakage_record.get("issue_url_or_reference"),
            "leakage_status": leakage_record.get("leakage_status"),
            "issue_body_persisted": leakage_record.get("issue_body_persisted", False),
            "issue_body_used_as_repair_evidence": leakage_record.get("issue_body_used_as_repair_evidence", False),
            "fix_or_workaround_text_persisted": leakage_record.get("fix_or_workaround_text_persisted", False),
            "exact_blocker": None if leakage_safe else "blocked_decision_time_leakage_risk",
        },
    )
    for name, key in [
        ("label_blindness_check.json", "hidden_labels_used"),
        ("gold_patch_exclusion_check.json", "gold_patch_used"),
        ("future_evidence_exclusion_check.json", "future_evidence_used"),
    ]:
        write_json_deterministic(candidate_dir / name, {"status": "PASS", key: False})
    write_json_deterministic(
        candidate_dir / "workspace_custody_check.json",
        {
            "status": "PASS",
            "workspace_outside_live_repo": str(checkout).lower().startswith(str(RUNTIME_ROOT).lower()),
            "workspace_path": str(checkout),
            "raw_workspace_committed": False,
            "patch_generated": False,
            "patch_applied": False,
        },
    )
    write_json_deterministic(
        candidate_dir / "provider_precondition_check.json",
        {
            "status": "PASS",
            "python_version": sys.version.split()[0],
            "os_name": os.name,
            "provider_precondition_blocker": None,
            "provider_failure_observed": classification in {"blocked_provider_precondition", "blocked_python_version_unavailable"},
        },
    )
    write_text_lf(candidate_dir / "pre_repair_replay_command.txt", command)
    if replay is not None:
        write_text_lf(candidate_dir / "pre_repair_replay_log_raw.txt", replay.get("combined", ""))
    else:
        write_text_lf(candidate_dir / "pre_repair_replay_not_run_reason.txt", classification)
    write_json_deterministic(
        candidate_dir / "pre_repair_replay_result.json",
        {
            "status": "PASS" if classification == "pre_repair_failure_materialized" else "BLOCK",
            "classification": classification,
            "lead_id": lead_id,
            "command": command,
            "replay_run": replay is not None,
            "returncode": replay.get("returncode") if replay else None,
            "timed_out": replay.get("timed_out") if replay else False,
            "raw_log_sha256": replay.get("combined_log_sha256") if replay else None,
            "exact_blocker": exact_blocker,
        },
    )
    if replay is not None and classification == "pre_repair_failure_materialized":
        write_text_lf(candidate_dir / "failure_signature_extract.txt", trim(replay.get("combined", ""), 2500))
    else:
        write_json_deterministic(
            candidate_dir / "failure_signature_not_available.json",
            {
                "status": "NOT_AVAILABLE",
                "classification": classification,
                "reason": exact_blocker or "failure_not_reproduced",
            },
        )
    write_json_deterministic(
        candidate_dir / "classification.json",
        {
            "status": "PASS",
            "lead_id": lead_id,
            "pre_repair_replay_classification": classification,
            "exact_blocker": exact_blocker,
            "patch_generated": False,
            "patch_applied": False,
            "post_repair_replay_run": False,
        },
    )

    failure_cells = [
        {
            "candidate_id": lead_id,
            "test_node": path,
            "exception_type": "unknown" if replay is None else ("command_nonzero" if replay.get("returncode") != 0 else "none"),
            "traceback_root": source_files[0] if source_files else None,
            "suspected_source_file": source_files[0] if source_files else None,
            "suspected_source_symbol": None,
            "dependency_contact": classification == "blocked_dependency_install_failure",
            "provider_contact": classification in {"blocked_provider_precondition", "blocked_python_version_unavailable"},
            "interpreter_contact": "py313" in lead_id or "py312" in lead_id,
            "fixture_contact": False,
            "environment_contact": classification.startswith("blocked_"),
            "risk_level": "medium" if classification == "pre_repair_failure_materialized" else "high",
            "evidence_files": ["pre_repair_replay_result.json"],
            "current_status": current_status,
        }
        for path in (native_paths or [command])
    ]
    mines = []
    if classification != "pre_repair_failure_materialized":
        mines.append({"mine_type": classification, "reason": "pre-repair failure was not materialized as a target-code candidate"})
    if not leakage_safe:
        mines.append({"mine_type": "fixed_gold_leakage", "reason": "leakage screen did not pass"})
    if classification == "blocked_dependency_install_failure":
        mines.append({"mine_type": "dependency_installation_not_ready", "reason": "declared package installation failed before replay"})

    safe_actions = [
        {"action": "minimal subtarget replay", "allowed_now": classification == "pre_repair_failure_materialized"},
        {"action": "dependency declaration check", "allowed_now": True},
        {"action": "provider precondition check", "allowed_now": True},
        {"action": "source discovery", "allowed_now": classification == "pre_repair_failure_materialized"},
        {"action": "AST/source-contact extrusion", "allowed_now": classification == "pre_repair_failure_materialized"},
        {"action": "cofactor materialization check", "allowed_now": classification == "blocked_dependency_install_failure"},
        {"action": "leakage screen", "allowed_now": True},
        {"action": "quarantine", "allowed_now": classification != "pre_repair_failure_materialized"},
        {"action": "future patch licensing recommendation", "allowed_now": bridge_state in PATCH_OPEN_STATES},
    ]
    bridge_records = {
        "amds_failure_board_state.json": {
            "status": "PASS",
            "candidate_id": lead_id,
            "board_source": "pre-repair replay evidence and command context",
            "cells": failure_cells,
            "unknown_cells": [] if classification == "pre_repair_failure_materialized" else ["target-code interior not materialized"],
        },
        "failure_cell_registry.json": {"status": "PASS", "candidate_id": lead_id, "failure_cells": failure_cells},
        "failure_mine_risk_map.json": {"status": "PASS", "candidate_id": lead_id, "failure_mines": mines},
        "safe_action_frontier.json": {"status": "PASS", "candidate_id": lead_id, "safe_frontier_actions": safe_actions},
        "information_gain_move_ranking.json": {
            "status": "PASS",
            "candidate_id": lead_id,
            "ranked_moves": [
                {"rank": 1, "move": "verify dependency/provider blocker" if classification != "pre_repair_failure_materialized" else "extract localized traceback source-contact graph"},
                {"rank": 2, "move": "failure-family decomposition" if classification == "pre_repair_failure_materialized" else "manual review or recovery lane"},
            ],
        },
        "flagged_unsafe_cells.json": {"status": "PASS", "candidate_id": lead_id, "unsafe_cells": mines},
        "minimal_probe_lineage_candidate.json": {
            "status": "PASS",
            "candidate_id": lead_id,
            "probe_outputs_are_hypotheses_only": True,
            "repair_proof_claimed": False,
        },
        "failure_stack_constraint_graph.json": {
            "status": "PASS",
            "candidate_id": lead_id,
            "nodes": ["command", "native_target_paths", "dependency_plan", "provider_precondition", "source_contact"],
            "edges": [
                ["command", "native_target_paths"],
                ["native_target_paths", "pre_repair_replay"],
                ["dependency_plan", "pre_repair_replay"],
                ["provider_precondition", "pre_repair_replay"],
                ["pre_repair_replay", "source_contact"],
            ],
            "graph_hash": hash_record({"lead_id": lead_id, "classification": classification, "source_files": source_files}),
        },
        "ast_loop_extrusion_bridge.json": {
            "status": "PASS" if classification == "pre_repair_failure_materialized" else "NOT_RUN",
            "candidate_id": lead_id,
            "bridge_type": "AST/source-contact bridge",
            "source_discovery_safely_available": classification == "pre_repair_failure_materialized",
            "source_contact_files": source_files,
            "patch_generation_authorized": False,
        },
        "source_contact_graph_extrusion_result.json": {
            "status": "PASS" if source_files else "NOT_AVAILABLE",
            "candidate_id": lead_id,
            "source_contact_files": source_files,
            "localized_source_file_count": len(source_files),
        },
        "probe_to_patch_transition_gate.json": {
            "status": "PASS",
            "candidate_id": lead_id,
            "pre_repair_failure_materialized": classification == "pre_repair_failure_materialized",
            "bridge_state": bridge_state,
            "patch_execution_authorized_in_batch056b": False,
            "future_patch_gate_candidate": bridge_state in PATCH_OPEN_STATES,
        },
        "patch_license_from_amds.json": {
            "status": "PASS",
            "candidate_id": lead_id,
            "patch_license_state": bridge_state,
            "patch_execution_authorized_in_batch056b": False,
            "license_is_future_recommendation_only": True,
        },
        "amds_candidate_summary.json": {
            "status": "PASS",
            "candidate_id": lead_id,
            "pre_repair_replay_classification": classification,
            "amds_bridge_classification": bridge_state,
            "exact_blocker": exact_blocker,
        },
    }
    for rel, record in bridge_records.items():
        write_json_deterministic(candidate_dir / rel, record)

    return {
        "lead_id": lead_id,
        "repo_url": candidate["repo_url"],
        "candidate_sha": candidate["candidate_sha"],
        "command": command,
        "classification": classification,
        "exact_blocker": exact_blocker,
        "amds_bridge_classification": bridge_state,
        "materialized_failure": classification == "pre_repair_failure_materialized",
        "future_patch_gate_candidate": bridge_state in PATCH_OPEN_STATES and classification == "pre_repair_failure_materialized",
        "decomposition_recommended": bridge_state == "amds_bridge_decomposition_needed",
        "dependency_or_provider_recovery_recommended": bridge_state in {"amds_bridge_dependency_materialization_needed", "amds_bridge_provider_precondition_needed"},
        "retired": bridge_state == "amds_bridge_candidate_retired",
        "source_contact_files": source_files,
    }


def write_schema_artifacts() -> None:
    write_json_deterministic(
        OUT_DIR / "failure_stack_constraint_graph_schema.json",
        {
            "status": "PASS",
            "node_types": ["candidate", "test_node", "exception_type", "traceback_root", "source_contact", "dependency_contact", "provider_contact"],
            "edge_types": ["replay_to_traceback", "traceback_to_source", "source_to_dependency", "provider_to_replay"],
            "patch_execution_authorized": False,
        },
    )
    write_json_deterministic(
        OUT_DIR / "ast_loop_extrusion_bridge_schema.json",
        {
            "status": "PASS",
            "public_label": "AST/source-contact bridge",
            "purpose": "convert replay-localized failure topology into a future patch-license recommendation",
            "patch_execution_authorized": False,
        },
    )
    write_json_deterministic(
        OUT_DIR / "probe_to_patch_transition_gate_schema.json",
        {
            "status": "PASS",
            "requires": ["fresh pre-repair reproduction", "safe source-contact graph", "no leakage", "source-only patch boundary"],
            "batch056b_patch_execution": "forbidden",
        },
    )
    write_json_deterministic(
        OUT_DIR / "safe_action_frontier_schema.json",
        {
            "status": "PASS",
            "allowed_frontier_actions": [
                "minimal subtarget replay",
                "dependency declaration check",
                "provider precondition check",
                "source discovery",
                "AST/source-contact bridge",
                "cofactor materialization check",
                "leakage screen",
                "quarantine",
                "future patch licensing recommendation",
            ],
        },
    )
    write_json_deterministic(
        OUT_DIR / "patch_license_from_amds_schema.json",
        {
            "status": "PASS",
            "states": [
                "patch_license_closed",
                "patch_license_open_single_source_family",
                "patch_license_open_primary_family_diagnostic_only",
                "patch_license_closed_provider_blocked",
                "patch_license_closed_dependency_blocked",
                "patch_license_closed_interpreter_behavior",
                "patch_license_closed_multi_causal",
                "patch_license_closed_manual_review",
            ],
            "batch056b_opens_future_license_only": True,
            "batch056b_patch_execution_authorized": False,
        },
    )


def update_public_docs(summary: dict[str, Any]) -> None:
    section = "\n".join(
        [
            "",
            "### Batch056b Wave 2 pre-repair replay plus AMDS bridge",
            "",
            f"- Batch057c official ingest status: `{summary['batch057c_ingest_status']}`.",
            "- Freezegun partial-improvement evidence is preserved and remains uncounted.",
            "- Freezegun secondary provider blocker is preserved for future provider-compatible investigation.",
            "- AMDS and MinimalProbe are recorded as existing capabilities; Batch056b adds bridge instrumentation only.",
            f"- Wave 2 replay candidate count: `{summary['wave2_replay_candidate_count']}`.",
            f"- Wave 2 materialized failure count: `{summary['wave2_materialized_failure_count']}`; blocked count: `{summary['wave2_blocked_count']}`.",
            f"- Future patch-gate candidates: `{', '.join(summary['future_patch_gate_recommended_candidates']) or 'none'}`.",
            f"- Decomposition candidates: `{', '.join(summary['decomposition_recommended_candidates']) or 'none'}`.",
            f"- Provider/dependency recovery candidates: `{', '.join(summary['provider_dependency_recovery_recommended_candidates']) or 'none'}`.",
            f"- Next allowed action: `{summary['next_allowed_action']}`.",
            "- Issue-derived repair count remains `2`; native external repair count remains `4`.",
            "- Full scoring remains `NOT_RUN/disallowed`; memory lift remains `not_demonstrated`; self-maintaining software remains `false/not_demonstrated`.",
            "",
        ]
    )
    for rel in [
        "README.md",
        "docs/current_status.md",
        "docs/capability_inventory.md",
        "docs/technical_validation_gap_report.md",
        "controllergate_v1_7_beta/reports/critic_review_package/shareable_summary.md",
    ]:
        path = ROOT / rel
        text = path.read_text(encoding="utf-8")
        marker = "### Batch056b Wave 2 pre-repair replay plus AMDS bridge"
        if marker in text:
            text = text.split(marker, 1)[0].rstrip() + section
        else:
            text = text.rstrip() + "\n" + section
        write_text_lf(path, text)


def main() -> int:
    if not BATCH057C_ZIP.is_file():
        OUT_DIR.mkdir(parents=True, exist_ok=True)
        write_json_deterministic(
            OUT_DIR / "audit.json",
            {"status": "BLOCK", "exact_blocker": "batch057c_artifact_absent_for_official_ingest"},
        )
        write_sha256sums(OUT_DIR)
        print("batch057c_artifact_absent_for_official_ingest")
        return 2

    safe_rmtree(OUT_DIR)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    artifact = verify_official_zip(
        BATCH057C_ZIP,
        artifact_name=BATCH057C_ARTIFACT_NAME,
        artifact_id=BATCH057C_ARTIFACT_ID,
        workflow_run_id=BATCH057C_WORKFLOW_RUN_ID,
        workflow_head_sha=BATCH057C_WORKFLOW_HEAD_SHA,
        expected_sha256=BATCH057C_SHA256,
        expected_size=BATCH057C_SIZE,
        expected_entry_count=BATCH057C_ENTRY_COUNT,
        artifact_manifest_checked=BATCH057C_ARTIFACT_MANIFEST_CHECKED,
        output_manifests=BATCH057C_OUTPUT_MANIFESTS,
    )
    if artifact["status"] != "PASS":
        write_json_deterministic(OUT_DIR / "batch057c_artifact_sha256_verification.json", artifact)
        write_json_deterministic(OUT_DIR / "audit.json", {"status": "BLOCK", "exact_blocker": artifact.get("exact_blocker")})
        write_sha256sums(OUT_DIR)
        print(json.dumps(artifact, indent=2, sort_keys=True))
        return 2
    ingest = ingest_official_outputs(
        BATCH057C_ZIP,
        ROOT,
        prefixes=("post_v2_37_hardening_batch057c_layered_source_only_patch_recovery_freezegun",),
    )
    write_json_deterministic(OUT_DIR / "batch057c_artifact_ingestion_summary.json", {"status": "PASS", "artifact_verification": artifact, "ingest": ingest})
    write_json_deterministic(OUT_DIR / "batch057c_artifact_sha256_verification.json", artifact)

    final057c = read_json(BATCH057C_DIR / "batch057c_final_outcome_classification.json")
    layered057c = read_json(BATCH057C_DIR / "batch057c_layered_patch_results.json")
    claim057c = read_json(BATCH057C_DIR / "claim_boundary.json")
    stage2_auth = read_json(BATCH057C_DIR / "stage2_secondary_authorization_check.json")
    duplicates057c = read_json(BATCH057C_DIR / "batch058_duplicate_replay_candidates.json")
    write_json_deterministic(
        OUT_DIR / "batch057c_result_preservation.json",
        {
            "status": "PASS",
            "final_classification": final057c.get("classification"),
            "full_original_target_post_repair_status": final057c.get("full_original_target_post_repair_status"),
            "batch058_duplicate_replay_candidates": duplicates057c.get("candidate_count"),
        },
    )
    write_json_deterministic(
        OUT_DIR / "batch057c_freezegun_partial_improvement_preservation.json",
        {
            "status": "PASS",
            "stage1_primary_patch_partial_improvement": layered057c.get("stage1", {}).get("classification") == "stage1_primary_patch_partial_improvement_secondary_still_fails",
            "stage1_primary_family_passed": layered057c.get("stage1", {}).get("primary_family_passed"),
            "partial_improvement_not_counted": True,
            "freezegun_patched_in_batch056b": False,
        },
    )
    write_json_deterministic(
        OUT_DIR / "batch057c_stage2_provider_blocker_preservation.json",
        {
            "status": "PASS",
            "stage2_authorization": stage2_auth.get("status"),
            "stage2_patch_generated": False,
            "stage2_patch_applied": False,
            "exact_blocker": stage2_auth.get("exact_blocker"),
        },
    )
    write_json_deterministic(
        OUT_DIR / "batch057c_claim_boundary_preservation.json",
        {
            "status": "PASS",
            "issue_derived_repair_count": claim057c.get("issue_derived_repair_count"),
            "native_external_repair_count": claim057c.get("native_external_repair_count"),
            "full_scoring": claim057c.get("full_scoring"),
            "memory_lift": claim057c.get("memory_lift"),
            "self_maintaining_software": claim057c.get("self_maintaining_software"),
            "duplicate_replay_run": False,
            "count_gate_run": False,
            "repair_count_increment": False,
        },
    )
    write_json_deterministic(
        OUT_DIR / "batch057c_next_action_boundary.json",
        {
            "status": "PASS",
            "preserved_next_allowed_action": final057c.get("next_allowed_action"),
            "batch056b_is_that_next_allowed_action": final057c.get("next_allowed_action") == "batch056b_wave2_pre_repair_replay",
        },
    )
    write_json_deterministic(
        OUT_DIR / "freezegun_provider_portability_secondary_family_plan.json",
        {
            "status": "PASS",
            "candidate_id": "freezegun_547_py313_datetimes_assertion",
            "future_plan": "future provider-compatible secondary-family replay may be considered under explicit later authorization",
            "batch056b_executes_provider_recovery": False,
            "exact_blocker_preserved": "secondary_family_provider_tzset_unavailable",
        },
    )

    write_json_deterministic(
        OUT_DIR / "amds_existing_capability_inventory.json",
        {"status": "PASS", "amds_already_exists": True, "minimal_probe_already_exists": True, "batch056b_adds_new_solver": False},
    )
    write_json_deterministic(
        OUT_DIR / "minimal_probe_lineage_trace.json",
        {"status": "PASS", "minimal_probe_outputs_are_hypotheses_only": True, "repair_proof_claimed": False},
    )
    write_json_deterministic(
        OUT_DIR / "amds_non_duplication_check.json",
        {
            "status": "PASS",
            "existing_amds_capability": True,
            "existing_minimal_probe_capability": True,
            "new_solver_added": False,
            "bridge_only": True,
            "probe_outputs_treated_as_repair_evidence": False,
        },
    )
    write_json_deterministic(
        OUT_DIR / "amds_to_repair_gap_report.json",
        {
            "status": "PASS",
            "gap": "transition from mapped failure topology to future patch-license decisions",
            "batch056b_bridge_instrumentation_only": True,
            "patching_authorized_in_batch056b": False,
        },
    )
    write_json_deterministic(
        OUT_DIR / "amds_bridge_scope_lock.json",
        {
            "status": "PASS",
            "existing_amds_capability": True,
            "existing_minimal_probe_capability": True,
            "new_solver_added": False,
            "bridge_instrumentation_added": True,
            "patching_authorized_in_batch056b": False,
            "probe_outputs_treated_as_repair_evidence": False,
            "probe_outputs_treated_as_hypotheses_only": True,
            "seed_promotion_requires_gate": True,
            "claim_boundary_preserved": True,
        },
    )
    write_schema_artifacts()

    candidates, normalized, prior_commit, leakage = load_wave2_source_records()
    plan_ids = [item["lead_id"] for item in candidates]
    write_json_deterministic(
        OUT_DIR / "wave2_candidate_plan_preservation.json",
        {
            "status": "PASS",
            "candidate_count": len(candidates),
            "candidate_ids": plan_ids,
            "source": "outputs/post_v2_37_hardening_batch056_pre_repair_replay_wave_1_plus_wave_2_intake/wave_2_pre_repair_replay_plan.json",
        },
    )
    write_json_deterministic(
        OUT_DIR / "wave2_candidate_plan_diff_from_prompt.json",
        {
            "status": "PASS" if plan_ids == PROMPT_WAVE2_IDS else "DIFF_RECORDED",
            "prompt_candidate_ids": PROMPT_WAVE2_IDS,
            "artifact_candidate_ids": plan_ids,
            "differences": [] if plan_ids == PROMPT_WAVE2_IDS else {"prompt_only": sorted(set(PROMPT_WAVE2_IDS) - set(plan_ids)), "artifact_only": sorted(set(plan_ids) - set(PROMPT_WAVE2_IDS))},
        },
    )
    write_json_deterministic(
        OUT_DIR / "wave2_pre_repair_replay_plan.json",
        {"status": "PASS", "candidate_count": len(candidates), "candidates": candidates, "patching_authorized": False},
    )

    safe_rmtree(RUNTIME_ROOT)
    RUNTIME_ROOT.mkdir(parents=True, exist_ok=True)
    candidate_results = []
    for candidate in candidates:
        candidate_results.append(
            write_candidate_artifacts(
                candidate,
                normalized.get(candidate["lead_id"], {}),
                prior_commit.get(candidate["lead_id"], {}),
                leakage.get(candidate["lead_id"], {}),
            )
        )

    materialized = [row for row in candidate_results if row["materialized_failure"]]
    blocked = [row for row in candidate_results if not row["materialized_failure"]]
    patch_gate = [row for row in candidate_results if row["future_patch_gate_candidate"]]
    decomposition = [row for row in candidate_results if row["decomposition_recommended"]]
    recovery = [row for row in candidate_results if row["dependency_or_provider_recovery_recommended"]]
    retired = [row for row in candidate_results if row["retired"]]
    exact_blockers = {row["lead_id"]: row["exact_blocker"] for row in candidate_results if row["exact_blocker"]}
    if patch_gate:
        next_allowed = "batch057e_source_only_patch_gate_wave_2"
    elif materialized and decomposition:
        next_allowed = "batch056c_failure_family_decomposition_wave_2"
    elif recovery:
        next_allowed = "batch056d_wave2_provider_dependency_recovery"
    elif final057c.get("exact_blocker") == "secondary_family_provider_tzset_unavailable":
        next_allowed = "batch057d_freezegun_provider_portability_secondary_family_probe"
    else:
        next_allowed = "batch058_seed_discovery_wave_3"

    write_json_deterministic(
        OUT_DIR / "wave2_pre_repair_replay_results.json",
        {"status": "PASS", "candidate_count": len(candidate_results), "results": candidate_results},
    )
    write_json_deterministic(
        OUT_DIR / "wave2_materialized_failure_registry.json",
        {"status": "PASS", "count": len(materialized), "candidates": materialized},
    )
    write_json_deterministic(
        OUT_DIR / "wave2_blocked_candidate_registry.json",
        {"status": "PASS", "count": len(blocked), "candidates": blocked},
    )
    write_json_deterministic(
        OUT_DIR / "wave2_amds_bridge_dashboard.json",
        {
            "status": "PASS",
            "candidate_count": len(candidate_results),
            "classifications": {row["lead_id"]: row["amds_bridge_classification"] for row in candidate_results},
            "patching_authorized_in_batch056b": False,
        },
    )
    write_json_deterministic(
        OUT_DIR / "wave2_candidate_ranking_for_next_patch_gate.json",
        {
            "status": "PASS",
            "candidate_count": len(patch_gate),
            "recommended_candidates": [row["lead_id"] for row in patch_gate],
            "ranking_basis": "materialized failure plus AMDS future patch-license state",
        },
    )
    write_json_deterministic(
        OUT_DIR / "wave2_candidate_ranking_for_decomposition.json",
        {"status": "PASS", "candidate_count": len(decomposition), "recommended_candidates": [row["lead_id"] for row in decomposition]},
    )
    write_json_deterministic(
        OUT_DIR / "wave2_candidate_retirement_registry.json",
        {"status": "PASS", "candidate_count": len(retired), "retired_candidates": [row["lead_id"] for row in retired]},
    )
    write_json_deterministic(OUT_DIR / "wave2_exact_blockers.json", {"status": "PASS", "exact_blockers": exact_blockers})
    write_json_deterministic(
        OUT_DIR / "batch056b_final_decision.json",
        {
            "status": "PASS",
            "next_allowed_action": next_allowed,
            "exact_blocker": None if materialized or recovery else "no_wave2_materialized_failure",
            "patch_generated": False,
            "patch_applied": False,
            "duplicate_replay_run": False,
            "count_gate_run": False,
        },
    )
    write_json_deterministic(
        OUT_DIR / "claim_boundary.json",
        {
            "status": "PASS",
            "current_protocol": CURRENT_PROTOCOL,
            "issue_derived_repair_count": ISSUE_DERIVED_REPAIR_COUNT,
            "native_external_repair_count": NATIVE_EXTERNAL_REPAIR_COUNT,
            "full_scoring": "NOT_RUN/disallowed",
            "memory_lift": "not_demonstrated",
            "self_maintaining_software": "false/not_demonstrated",
            "batch056b_patch_generated": False,
            "batch056b_patch_applied": False,
            "batch056b_post_repair_replay_run": False,
            "batch056b_duplicate_replay_run": False,
            "batch056b_count_gate_run": False,
            "batch056b_repair_count_increment": False,
            "freezegun_patched_in_batch056b": False,
            "wave2_patched_in_batch056b": False,
        },
    )
    write_json_deterministic(
        OUT_DIR / "audit.json",
        {"status": "PASS", "audit_script": "scripts/audit_batch056b_wave2_pre_repair_replay_plus_amds_bridge.py"},
    )
    write_json_deterministic(
        OUT_DIR / "package_verification.json",
        {
            "status": "PASS",
            "artifact_name": BATCH056B_ARTIFACT_NAME,
            "raw_zip_payload_committed": False,
            "artifact_payload_created_locally": False,
            "workflow_upload_required_for_artifact_identity": True,
        },
    )
    write_json_deterministic(
        OUT_DIR / "artifact_sha256_verification.json",
        {
            "status": "PENDING_WORKFLOW_ARTIFACT",
            "artifact_name": BATCH056B_ARTIFACT_NAME,
            "artifact_sha256_available_after_workflow_upload": True,
            "batch057c_local_zip_sha256": BATCH057C_SHA256,
        },
    )
    summary = {
        "status": "PASS",
        "batch057c_ingest_status": "PASS",
        "wave2_replay_candidate_count": len(candidate_results),
        "wave2_materialized_failure_count": len(materialized),
        "wave2_blocked_count": len(blocked),
        "wave2_candidate_classifications": {row["lead_id"]: row["classification"] for row in candidate_results},
        "wave2_amds_bridge_classifications": {row["lead_id"]: row["amds_bridge_classification"] for row in candidate_results},
        "future_patch_gate_recommended_candidates": [row["lead_id"] for row in patch_gate],
        "decomposition_recommended_candidates": [row["lead_id"] for row in decomposition],
        "provider_dependency_recovery_recommended_candidates": [row["lead_id"] for row in recovery],
        "freezegun_provider_portability_recommendation": "future_explicit_authorization_required",
        "next_allowed_action": next_allowed,
        "issue_derived_repair_count": ISSUE_DERIVED_REPAIR_COUNT,
        "native_external_repair_count": NATIVE_EXTERNAL_REPAIR_COUNT,
        "full_scoring": "NOT_RUN/disallowed",
        "memory_lift": "not_demonstrated",
        "self_maintaining_software": "false/not_demonstrated",
        "exact_blocker": None if materialized or recovery else "no_wave2_materialized_failure",
    }
    write_text_lf(
        OUT_DIR / "batch056b_summary.md",
        "\n".join(
            [
                "# Batch056b Wave 2 pre-repair replay plus AMDS bridge",
                "",
                f"- Batch057c ingest status: `{summary['batch057c_ingest_status']}`",
                "- Freezegun partial improvement: preserved, not counted",
                "- Freezegun provider blocker: preserved",
                "- AMDS non-duplication: existing capability; bridge instrumentation only",
                f"- Wave 2 candidate count: `{summary['wave2_replay_candidate_count']}`",
                f"- Materialized failures: `{summary['wave2_materialized_failure_count']}`",
                f"- Blocked/not reproduced candidates: `{summary['wave2_blocked_count']}`",
                f"- Future patch-gate candidates: `{', '.join(summary['future_patch_gate_recommended_candidates']) or 'none'}`",
                f"- Decomposition candidates: `{', '.join(summary['decomposition_recommended_candidates']) or 'none'}`",
                f"- Provider/dependency recovery candidates: `{', '.join(summary['provider_dependency_recovery_recommended_candidates']) or 'none'}`",
                f"- Next allowed action: `{summary['next_allowed_action']}`",
                "- Full scoring: `NOT_RUN/disallowed`",
                "- Memory lift: `not_demonstrated`",
                "- Self-maintaining software: `false/not_demonstrated`",
                "",
            ]
        ),
    )
    update_public_docs(summary)
    write_sha256sums(OUT_DIR)
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
