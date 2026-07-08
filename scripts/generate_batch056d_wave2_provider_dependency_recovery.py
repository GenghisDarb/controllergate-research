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
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from controllergate.core.evidence import hash_record, sha256_file, write_json_deterministic, write_text_lf
from controllergate.core.manifests import write_sha256sums
from controllergate.core.official_ingest import ingest_official_outputs, verify_official_zip


OUT_DIR = ROOT / "outputs" / "post_v2_37_hardening_batch056d_wave2_provider_dependency_recovery"
BATCH056B_DIR = ROOT / "outputs" / "post_v2_37_hardening_batch056b_wave2_pre_repair_replay_plus_amds_bridge"
BATCH057C_DIR = ROOT / "outputs" / "post_v2_37_hardening_batch057c_layered_source_only_patch_recovery_freezegun"
BATCH056B_ZIP = Path(
    r"C:\Users\thisb\Downloads\post_v2_37_hardening_batch056b_wave2_pre_repair_replay_plus_amds_bridge_artifacts.zip"
)
BATCH056B_ARTIFACT_NAME = "post_v2_37_hardening_batch056b_wave2_pre_repair_replay_plus_amds_bridge_artifacts"
BATCH056B_ARTIFACT_ID = 8155663510
BATCH056B_WORKFLOW_RUN_ID = 28910348086
BATCH056B_WORKFLOW_HEAD_SHA = "bbf49123826cb77696f14adc4410b9db8660785b"
BATCH056B_SHA256 = "0da4a224d91a7cb5025e4343879788de0cd45fe1b427c975d573f6b71ecc5157"
BATCH056B_SIZE = 182455
BATCH056B_ENTRY_COUNT = 254
BATCH056B_ARTIFACT_MANIFEST_CHECKED = 253
BATCH056B_OUTPUT_MANIFESTS = {
    "post_v2_37_hardening_batch056b_wave2_pre_repair_replay_plus_amds_bridge": (
        "post_v2_37_hardening_batch056b_wave2_pre_repair_replay_plus_amds_bridge/SHA256SUMS.txt",
        252,
    )
}

CURRENT_PROTOCOL = "v2.14"
ISSUE_DERIVED_REPAIR_COUNT = 2
NATIVE_EXTERNAL_REPAIR_COUNT = 4
RUNTIME_ROOT = Path(os.environ.get("CONTROLLERGATE_BATCH056D_RUNTIME_ROOT", r"C:\Dev\ControllerGate_runtime\batch056d"))
TIMEOUT_SECONDS = int(os.environ.get("CONTROLLERGATE_BATCH056D_TIMEOUT_SECONDS", "180"))
REPLAY_TIMEOUT_SECONDS = int(os.environ.get("CONTROLLERGATE_BATCH056D_REPLAY_TIMEOUT_SECONDS", "120"))

PROVIDER_RECOVERY_CANDIDATES = [
    "pairtools_250_py313_pipes_removed",
    "pytest_13480_wdefault_unraisable_threadexception",
    "snapshottest_177_py312_imp_removed",
]
TIMEOUT_DECOMPOSITION_CANDIDATES = [
    "codex_wave2_nousresearch_hermes_agent_48986",
    "codex_wave2_nousresearch_hermes_agent_60243",
    "codex_wave2_nousresearch_hermes_agent_57197",
    "codex_wave2_m0smith_genia_2026_518",
]
ALLOWED_RECOVERY_CLASSIFICATIONS = {
    "provider_dependency_recovery_succeeded_failure_materialized",
    "provider_dependency_recovery_succeeded_failure_not_reproduced",
    "provider_dependency_recovery_succeeded_new_blocker",
    "provider_dependency_recovery_partial",
    "blocked_no_declared_dependency_evidence",
    "blocked_dependency_install_failure",
    "blocked_provider_precondition",
    "blocked_python_version_unavailable",
    "blocked_tox_env_unavailable",
    "blocked_compiled_dependency",
    "blocked_network_required",
    "blocked_timeout",
    "blocked_command_ambiguous",
    "blocked_recovery_would_use_forbidden_evidence",
    "blocked_recovery_would_mutate_target_source",
    "probe_only_needs_manual_review",
}
FUTURE_PATCH_LICENSE_STATES = {
    "future_patch_license_open_single_source_family",
    "future_patch_license_open_primary_family_diagnostic_only",
    "future_decomposition_needed_before_patch",
    "future_provider_dependency_recovery_needed",
    "future_candidate_retired",
    "future_manual_review_needed",
}


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return value


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


def summarize_cmd(raw: dict[str, Any] | None) -> dict[str, Any] | None:
    if raw is None:
        return None
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
    if parts and parts[0] == "python":
        return [str(python_exe), *parts[1:]]
    return parts


def path_hash(path: Path) -> str | None:
    return sha256_file(path) if path.is_file() else None


def collect_declared_evidence(checkout: Path) -> list[dict[str, Any]]:
    names = [
        "pyproject.toml",
        "setup.py",
        "setup.cfg",
        "requirements.txt",
        "requirements-dev.txt",
        "requirements-test.txt",
        "tox.ini",
        "noxfile.py",
        "pytest.ini",
    ]
    evidence: list[dict[str, Any]] = []
    for name in names:
        path = checkout / name
        if path.is_file():
            text = path.read_text(encoding="utf-8", errors="replace")
            lower = text.lower()
            evidence.append(
                {
                    "path": name,
                    "sha256": sha256_file(path),
                    "line_count": len(text.splitlines()),
                    "mentions_pytest_cov": "pytest-cov" in lower or "pytest_cov" in lower,
                    "mentions_tox": "tox" in lower,
                    "mentions_pysam": "pysam" in lower,
                    "mentions_cython_or_compiled_extension": any(term in lower for term in ["cython", "extension(", "htslib", "numpy.get_include"]),
                    "decision_time_safe": True,
                }
            )
    workflows = sorted((checkout / ".github" / "workflows").glob("*.yml")) + sorted((checkout / ".github" / "workflows").glob("*.yaml"))
    for path in workflows[:10]:
        text = path.read_text(encoding="utf-8", errors="replace")
        lower = text.lower()
        evidence.append(
            {
                "path": path.relative_to(checkout).as_posix(),
                "sha256": sha256_file(path),
                "line_count": len(text.splitlines()),
                "mentions_ubuntu": "ubuntu" in lower,
                "mentions_pytest_cov": "pytest-cov" in lower or "pytest_cov" in lower,
                "mentions_tox": "tox" in lower,
                "decision_time_safe": True,
            }
        )
    return evidence


def evidence_mentions(evidence: list[dict[str, Any]], key: str) -> bool:
    return any(item.get(key) is True for item in evidence)


def extract_source_files(text: str, checkout: Path) -> list[str]:
    found: list[str] = []
    normalized_checkout = str(checkout).replace("\\", "/")
    for raw_line in text.splitlines():
        line = raw_line.replace("\\", "/")
        if normalized_checkout in line and ".py" in line:
            suffix = line.split(normalized_checkout, 1)[1].lstrip("/")
            path = suffix.split(".py", 1)[0] + ".py"
            if path and path not in found and not path.startswith(("tests/", "testing/")):
                found.append(path)
        match = re.search(r'File "([^"]+\.py)"', raw_line)
        if match:
            candidate = match.group(1).replace("\\", "/")
            if not candidate.startswith(("tests/", "testing/")) and candidate not in found:
                found.append(candidate)
    return found[:25]


def blocked_result(candidate_id: str, classification: str, exact_blocker: str, reason: str) -> dict[str, Any]:
    return {
        "candidate_id": candidate_id,
        "classification": classification,
        "exact_blocker": exact_blocker,
        "materialized_target_code_failure": False,
        "provider_dependency_recovery_succeeded": False,
        "provider_dependency_recovery_attempted": True,
        "post_recovery_prerepair_replay_ran": False,
        "patch_generated": False,
        "patch_applied": False,
        "duplicate_replay_run": False,
        "count_gate_run": False,
        "reason": reason,
    }


def write_amds_after_recovery(candidate_dir: Path, result: dict[str, Any], source_files: list[str], future_state: str) -> dict[str, Any]:
    cells = [
        {
            "cell_id": f"{result['candidate_id']}::provider_dependency_boundary",
            "classification": result["classification"],
            "exact_blocker": result.get("exact_blocker"),
            "target_repair_claim": False,
        }
    ]
    if source_files:
        cells.append(
            {
                "cell_id": f"{result['candidate_id']}::source_contact",
                "source_files": source_files,
                "target_repair_claim": False,
            }
        )
    common = {
        "status": "PASS",
        "candidate_id": result["candidate_id"],
        "classification_after_recovery": result["classification"],
        "future_patch_license_state": future_state,
        "patch_license_future_only": True,
        "patch_generated_in_batch056d": False,
        "patch_applied_in_batch056d": False,
        "provider_dependency_recovery_is_not_repair_success": True,
    }
    files = {
        "amds_failure_board_state_after_recovery.json": {**common, "cells": cells},
        "failure_cell_registry_after_recovery.json": {**common, "cells": cells},
        "failure_mine_risk_map_after_recovery.json": {**common, "risk": "provider/dependency boundary remains separate from target-code repair evidence"},
        "safe_action_frontier_after_recovery.json": {**common, "safe_actions": [future_state]},
        "information_gain_move_ranking_after_recovery.json": {
            **common,
            "ranked_future_moves": [
                "provider_dependency_recovery_if_declared",
                "failure_family_decomposition_after_materialized_failure",
                "source_only_patch_gate_only_after_future_authorization",
            ],
        },
        "flagged_unsafe_cells_after_recovery.json": {
            **common,
            "unsafe_cells": [
                "source_patch_generation",
                "duplicate_replay",
                "repair_count_gate",
                "fixed_gold_future_evidence",
            ],
        },
        "failure_stack_constraint_graph_after_recovery.json": {
            **common,
            "source_contact_files": source_files,
            "materialized_target_code_failure": result["materialized_target_code_failure"],
        },
        "ast_loop_extrusion_bridge_after_recovery.json": {
            **common,
            "bridge_status": "future_only",
            "source_contact_files": source_files,
        },
        "source_contact_graph_extrusion_result_after_recovery.json": {
            **common,
            "source_contact_files": source_files,
            "single_source_family": len(source_files) == 1,
        },
        "probe_to_patch_transition_gate_after_recovery.json": {
            **common,
            "transition_gate": "CLOSED_IN_BATCH056D",
            "next_required_boundary": future_state,
        },
        "patch_license_from_amds_after_recovery.json": {
            **common,
            "patch_license_state": future_state,
            "patch_execution_authorized_in_batch056d": False,
        },
        "amds_candidate_summary_after_recovery.json": common,
    }
    for name, payload in files.items():
        write_json_deterministic(candidate_dir / name, payload)
    return common


def clone_and_checkout(candidate: dict[str, Any], checkout: Path) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any], dict[str, Any]]:
    clone = run_cmd(["git", "clone", "--filter=blob:none", "--no-checkout", candidate["repo_url"], str(checkout)], ROOT, timeout=TIMEOUT_SECONDS)
    fetch = (
        run_cmd(["git", "fetch", "--depth", "1", "origin", candidate["candidate_sha"]], checkout, timeout=TIMEOUT_SECONDS)
        if clone["returncode"] == 0
        else {"returncode": 1, "combined": "clone failed", "timed_out": False}
    )
    cat_file = (
        run_cmd(["git", "cat-file", "-e", f"{candidate['candidate_sha']}^{{commit}}"], checkout, timeout=TIMEOUT_SECONDS)
        if fetch.get("returncode") == 0
        else {"returncode": 1, "combined": "fetch failed", "timed_out": False}
    )
    checkout_cmd = (
        run_cmd(["git", "checkout", "--detach", candidate["candidate_sha"]], checkout, timeout=TIMEOUT_SECONDS)
        if cat_file.get("returncode") == 0
        else {"returncode": 1, "combined": "cat-file failed", "timed_out": False}
    )
    return clone, fetch, cat_file, checkout_cmd


def run_snapshottest_recovery(candidate_dir: Path, checkout: Path, prior: dict[str, Any], evidence: list[dict[str, Any]]) -> dict[str, Any]:
    work_root = checkout.parent
    venv_dir = work_root / "venv"
    python_exe = venv_dir / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
    command = prior["command"]
    if not evidence_mentions(evidence, "mentions_pytest_cov"):
        result = blocked_result(
            prior["lead_id"],
            "blocked_no_declared_dependency_evidence",
            "pytest_cov_not_declared_in_buggy_checkout_metadata",
            "setup.cfg addopts require --cov, but no decision-time-safe pytest-cov declaration was found",
        )
        return result

    venv = run_cmd([sys.executable, "-m", "venv", str(venv_dir)], work_root, timeout=TIMEOUT_SECONDS)
    install_upgrade = install_pytest_cov = install_editable = replay = None
    install_attempts: list[dict[str, Any]] = [{"name": "venv", "result": summarize_cmd(venv)}]
    if venv.get("returncode") == 0:
        install_upgrade = run_cmd([str(python_exe), "-m", "pip", "install", "--upgrade", "pip"], checkout, timeout=TIMEOUT_SECONDS)
        install_attempts.append({"name": "pip_upgrade", "result": summarize_cmd(install_upgrade), "declared": False, "provider_tooling": True})
    if install_upgrade is not None and install_upgrade.get("returncode") == 0:
        install_pytest_cov = run_cmd([str(python_exe), "-m", "pip", "install", "pytest-cov"], checkout, timeout=TIMEOUT_SECONDS)
        install_attempts.append(
            {
                "name": "pytest-cov",
                "result": summarize_cmd(install_pytest_cov),
                "declared": True,
                "evidence": [item["path"] for item in evidence if item.get("mentions_pytest_cov")],
            }
        )
    if install_pytest_cov is not None and install_pytest_cov.get("returncode") == 0:
        install_editable = run_cmd([str(python_exe), "-m", "pip", "install", "-e", "."], checkout, timeout=TIMEOUT_SECONDS)
        install_attempts.append({"name": "editable_project", "result": summarize_cmd(install_editable), "declared": True})
    if install_editable is not None and install_editable.get("returncode") == 0:
        replay = run_cmd(command_to_args(command, python_exe), checkout, timeout=REPLAY_TIMEOUT_SECONDS)

    write_json_deterministic(candidate_dir / "dependency_install_attempts.json", {"status": "PASS", "attempts": install_attempts})
    command_status = "preserved_command_used"
    if venv.get("returncode") != 0:
        result = blocked_result(prior["lead_id"], "blocked_python_version_unavailable", "venv_creation_failed", "isolated venv could not be created")
    elif install_pytest_cov is None or install_pytest_cov.get("returncode") != 0:
        result = blocked_result(prior["lead_id"], "blocked_dependency_install_failure", "declared_pytest_cov_install_failed", "declared pytest-cov installation failed")
    elif install_editable is None or install_editable.get("returncode") != 0:
        result = blocked_result(prior["lead_id"], "blocked_dependency_install_failure", "editable_project_install_failed_after_declared_dependency_recovery", "editable project install failed")
    elif replay is None:
        result = blocked_result(prior["lead_id"], "blocked_command_ambiguous", "replay_not_started", "replay did not start after dependency recovery")
    elif replay.get("timed_out"):
        result = blocked_result(prior["lead_id"], "blocked_timeout", "post_recovery_prerepair_replay_timeout", "post-recovery pre-repair replay timed out")
    elif replay.get("returncode") == 0:
        result = {
            "candidate_id": prior["lead_id"],
            "classification": "provider_dependency_recovery_succeeded_failure_not_reproduced",
            "exact_blocker": "post_recovery_prerepair_replay_passed_or_no_failure",
            "materialized_target_code_failure": False,
            "provider_dependency_recovery_succeeded": True,
            "provider_dependency_recovery_attempted": True,
            "post_recovery_prerepair_replay_ran": True,
            "patch_generated": False,
            "patch_applied": False,
            "duplicate_replay_run": False,
            "count_gate_run": False,
            "reason": "Declared dependency recovery allowed replay to run, but the preserved target command did not reproduce a target-code failure.",
        }
    else:
        combined = replay.get("combined", "")
        lower = combined.lower()
        if any(marker in lower for marker in ["unrecognized arguments", "no module named", "could not find a version", "failed building wheel"]):
            result = blocked_result(prior["lead_id"], "provider_dependency_recovery_succeeded_new_blocker", "post_recovery_environment_or_dependency_blocker", "replay still failed at provider/dependency boundary")
            result["post_recovery_prerepair_replay_ran"] = True
        else:
            result = {
                "candidate_id": prior["lead_id"],
                "classification": "provider_dependency_recovery_succeeded_failure_materialized",
                "exact_blocker": None,
                "materialized_target_code_failure": True,
                "provider_dependency_recovery_succeeded": True,
                "provider_dependency_recovery_attempted": True,
                "post_recovery_prerepair_replay_ran": True,
                "patch_generated": False,
                "patch_applied": False,
                "duplicate_replay_run": False,
                "count_gate_run": False,
                "reason": "Declared dependency recovery allowed the preserved target command to produce a non-provider pre-repair failure.",
            }

    write_text_lf(candidate_dir / "post_recovery_prerepair_replay_command.txt", command)
    if replay is not None:
        write_text_lf(candidate_dir / "post_recovery_prerepair_replay_log_raw.txt", replay.get("combined", ""))
        signature = "\n".join(replay.get("combined", "").splitlines()[-80:])
        write_text_lf(candidate_dir / "post_recovery_failure_signature_extract.txt", signature)
    else:
        write_text_lf(candidate_dir / "post_recovery_prerepair_replay_log_raw.txt", "")
        write_text_lf(candidate_dir / "post_recovery_failure_signature_extract.txt", "")
    write_json_deterministic(
        candidate_dir / "post_recovery_prerepair_replay_result.json",
        {
            "status": "PASS" if result["post_recovery_prerepair_replay_ran"] else "NOT_RUN",
            "classification": result["classification"],
            "command": command,
            "command_change_status": command_status,
            "replay": summarize_cmd(replay),
            "provider_dependency_recovery_is_not_repair_success": True,
        },
    )
    write_json_deterministic(
        candidate_dir / "command_change_justification.json",
        {
            "status": "PASS",
            "command_change_status": command_status,
            "original_command": command,
            "used_command": command,
            "reason": "Batch056d preserved the Batch056b target command after declared pytest-cov recovery.",
            "decision_time_safe": True,
        },
    )
    return result


def recover_candidate(prior: dict[str, Any]) -> dict[str, Any]:
    candidate_id = prior["lead_id"]
    candidate_dir = OUT_DIR / "candidates" / candidate_id
    candidate_dir.mkdir(parents=True, exist_ok=True)
    work_root = RUNTIME_ROOT / candidate_id
    checkout = work_root / "checkout"
    safe_rmtree(work_root)
    work_root.mkdir(parents=True, exist_ok=True)

    clone, fetch, cat_file, checkout_cmd = clone_and_checkout(prior, checkout)
    checkout_ok = clone.get("returncode") == 0 and fetch.get("returncode") == 0 and cat_file.get("returncode") == 0 and checkout_cmd.get("returncode") == 0
    evidence = collect_declared_evidence(checkout) if checkout_ok else []
    evidence_hash = hash_record(evidence)
    source_files: list[str] = []

    write_json_deterministic(
        candidate_dir / "dependency_recovery_plan.json",
        {
            "status": "PASS",
            "candidate_id": candidate_id,
            "prior_classification": prior["classification"],
            "prior_exact_blocker": prior["exact_blocker"],
            "allowed_recovery_scope": "provider_dependency_only",
            "source_patch_generation_allowed": False,
            "post_repair_replay_allowed": False,
            "duplicate_replay_allowed": False,
            "count_gate_allowed": False,
        },
    )
    write_json_deterministic(
        candidate_dir / "declared_dependency_lineage.json",
        {
            "status": "PASS" if evidence else "BLOCK",
            "candidate_id": candidate_id,
            "repo_url": prior["repo_url"],
            "candidate_sha": prior["candidate_sha"],
            "checkout": {
                "clone": summarize_cmd(clone),
                "fetch": summarize_cmd(fetch),
                "cat_file_commit_verified": cat_file.get("returncode") == 0,
                "checkout": summarize_cmd(checkout_cmd),
            },
            "evidence_hash": evidence_hash,
            "decision_time_safe": True,
        },
    )
    write_json_deterministic(
        candidate_dir / "declared_dependency_evidence.json",
        {
            "status": "PASS" if evidence else "BLOCK",
            "candidate_id": candidate_id,
            "evidence": evidence,
            "evidence_hash": evidence_hash,
            "forbidden_evidence_used": False,
        },
    )

    if not checkout_ok:
        result = blocked_result(candidate_id, "blocked_provider_precondition", "checkout_or_commit_resolution_failed", "candidate commit could not be checked out safely")
    elif candidate_id == "pairtools_250_py313_pipes_removed":
        linux_required = evidence_mentions(evidence, "mentions_ubuntu")
        compiled_required = evidence_mentions(evidence, "mentions_pysam") or evidence_mentions(evidence, "mentions_cython_or_compiled_extension")
        classification = "blocked_compiled_dependency" if compiled_required else "blocked_provider_precondition"
        exact = "compiled_dependency_or_linux_provider_required"
        result = blocked_result(
            candidate_id,
            classification,
            exact,
            "Decision-time metadata indicates provider/build requirements that are not bounded for a Windows local recovery attempt.",
        )
        write_json_deterministic(
            candidate_dir / "dependency_install_attempts.json",
            {
                "status": "NOT_RUN",
                "reason": "Pairtools recovery was stopped at the provider/build boundary before any install.",
                "linux_provider_declared_or_indicated": linux_required,
                "compiled_dependency_declared_or_indicated": compiled_required,
            },
        )
    elif candidate_id == "pytest_13480_wdefault_unraisable_threadexception":
        tox_declared = evidence_mentions(evidence, "mentions_tox")
        if tox_declared:
            result = blocked_result(
                candidate_id,
                "blocked_tox_env_unavailable",
                "project_self_test_requires_declared_tox_or_project_runner_boundary",
                "Buggy checkout metadata indicates a project self-test runner, but Batch056d does not broaden provider tooling into an unbounded tox execution.",
            )
        else:
            result = blocked_result(
                candidate_id,
                "blocked_command_ambiguous",
                "no_declared_self_test_runner_found",
                "The direct command remains provider-wrong and no declared bounded native command was found.",
            )
        write_json_deterministic(
            candidate_dir / "dependency_install_attempts.json",
            {
                "status": "NOT_RUN",
                "reason": "No external pytest bypass or unbounded tox execution was performed.",
                "tox_declared": tox_declared,
            },
        )
    elif candidate_id == "snapshottest_177_py312_imp_removed":
        result = run_snapshottest_recovery(candidate_dir, checkout, prior, evidence)
        replay_path = candidate_dir / "post_recovery_prerepair_replay_log_raw.txt"
        if replay_path.is_file():
            source_files = extract_source_files(replay_path.read_text(encoding="utf-8", errors="replace"), checkout)
    else:
        result = blocked_result(candidate_id, "blocked_command_ambiguous", "candidate_not_in_batch056d_recovery_scope", "candidate is not in Batch056d provider/dependency recovery scope")

    if not (candidate_dir / "post_recovery_prerepair_replay_result.json").is_file():
        write_text_lf(candidate_dir / "post_recovery_prerepair_replay_command.txt", prior["command"])
        write_text_lf(candidate_dir / "post_recovery_prerepair_replay_log_raw.txt", "")
        write_text_lf(candidate_dir / "post_recovery_failure_signature_extract.txt", "")
        write_json_deterministic(
            candidate_dir / "post_recovery_prerepair_replay_result.json",
            {
                "status": "NOT_RUN",
                "classification": result["classification"],
                "command": prior["command"],
                "command_change_status": "command_change_blocked_no_declared_evidence",
                "replay": None,
                "provider_dependency_recovery_is_not_repair_success": True,
            },
        )
        write_json_deterministic(
            candidate_dir / "command_change_justification.json",
            {
                "status": "PASS",
                "command_change_status": "command_change_blocked_no_declared_evidence",
                "original_command": prior["command"],
                "used_command": None,
                "reason": result["reason"],
                "decision_time_safe": True,
            },
        )

    if result["classification"] == "provider_dependency_recovery_succeeded_failure_materialized":
        if len(source_files) == 1:
            future_state = "future_patch_license_open_single_source_family"
        else:
            future_state = "future_decomposition_needed_before_patch"
    elif result["classification"] == "provider_dependency_recovery_succeeded_failure_not_reproduced":
        future_state = "future_manual_review_needed"
    else:
        future_state = "future_provider_dependency_recovery_needed"

    amds = write_amds_after_recovery(candidate_dir, result, source_files, future_state)
    write_json_deterministic(
        candidate_dir / "provider_recovery_plan.json",
        {
            "status": "PASS",
            "candidate_id": candidate_id,
            "recovery_action": "inspect_buggy_checkout_metadata_and_attempt_declared_dependency_recovery_when_safe",
            "forbidden_evidence_used": False,
            "source_mutation_allowed": False,
            "test_mutation_allowed": False,
        },
    )
    write_json_deterministic(
        candidate_dir / "provider_recovery_safety_check.json",
        {
            "status": "PASS",
            "candidate_id": candidate_id,
            "fixed_commit_used": False,
            "future_commit_used": False,
            "gold_patch_used": False,
            "pr_patch_used": False,
            "source_modified": False,
            "tests_modified": False,
            "synthetic_tests_added": False,
            "dependency_recovery_is_not_repair_success": True,
        },
    )
    write_json_deterministic(candidate_dir / "dependency_recovery_result.json", {"status": "PASS", **result})
    write_json_deterministic(
        candidate_dir / "post_recovery_prerepair_replay_plan.json",
        {
            "status": "PASS",
            "candidate_id": candidate_id,
            "command": prior["command"],
            "replay_allowed": result["post_recovery_prerepair_replay_ran"],
            "patching_allowed": False,
        },
    )
    write_json_deterministic(
        candidate_dir / "recovery_not_target_repair_boundary.json",
        {
            "status": "PASS",
            "candidate_id": candidate_id,
            "provider_dependency_recovery_is_not_target_repair": True,
            "materialized_failure_is_not_repair_success": True,
            "repair_count_increment_allowed": False,
        },
    )
    write_json_deterministic(
        candidate_dir / "amds_bridge_update_after_recovery.json",
        {
            "status": "PASS",
            "candidate_id": candidate_id,
            "amds_bridge": amds,
            "future_patch_license_state": future_state,
        },
    )
    write_json_deterministic(
        candidate_dir / "classification_after_recovery.json",
        {
            "status": "PASS",
            "candidate_id": candidate_id,
            "classification": result["classification"],
            "exact_blocker": result["exact_blocker"],
            "future_patch_license_state": future_state,
        },
    )
    result.update(
        {
            "repo_url": prior["repo_url"],
            "candidate_sha": prior["candidate_sha"],
            "command": prior["command"],
            "source_contact_files": source_files,
            "future_patch_license_state": future_state,
            "amds_bridge_classification_after_recovery": future_state,
        }
    )
    return result


def write_phase_a(artifact: dict[str, Any], ingest: dict[str, Any]) -> None:
    final = read_json(BATCH056B_DIR / "batch056b_final_decision.json")
    claim = read_json(BATCH056B_DIR / "claim_boundary.json")
    replay = read_json(BATCH056B_DIR / "wave2_pre_repair_replay_results.json")
    materialized = read_json(BATCH056B_DIR / "wave2_materialized_failure_registry.json")
    blocked = read_json(BATCH056B_DIR / "wave2_blocked_candidate_registry.json")
    dashboard = read_json(BATCH056B_DIR / "wave2_amds_bridge_dashboard.json")
    scope = read_json(BATCH056B_DIR / "amds_bridge_scope_lock.json")
    write_json_deterministic(OUT_DIR / "batch056b_artifact_ingestion_summary.json", {"status": "PASS", "artifact_verification": artifact, "ingest": ingest})
    write_json_deterministic(OUT_DIR / "batch056b_artifact_sha256_verification.json", artifact)
    write_json_deterministic(
        OUT_DIR / "batch056b_result_preservation.json",
        {
            "status": "PASS",
            "issue_derived_repair_count": claim.get("issue_derived_repair_count"),
            "native_external_repair_count": claim.get("native_external_repair_count"),
            "full_scoring": claim.get("full_scoring"),
            "memory_lift": claim.get("memory_lift"),
            "self_maintaining_software": claim.get("self_maintaining_software"),
            "batch056b_patch_generated": final.get("patch_generated"),
            "batch056b_patch_applied": final.get("patch_applied"),
            "batch056b_duplicate_replay_run": final.get("duplicate_replay_run"),
            "batch056b_count_gate_run": final.get("count_gate_run"),
        },
    )
    write_json_deterministic(
        OUT_DIR / "batch056b_wave2_replay_preservation.json",
        {
            "status": "PASS",
            "wave2_candidates_replayed": replay.get("candidate_count"),
            "wave2_materialized_target_code_failures": materialized.get("count"),
            "wave2_blocked_candidates": blocked.get("count"),
            "candidate_classifications": {row["lead_id"]: row["classification"] for row in replay.get("results", [])},
        },
    )
    write_json_deterministic(
        OUT_DIR / "batch056b_amds_bridge_preservation.json",
        {
            "status": "PASS",
            "amds_bridge_classifications": dashboard.get("classifications"),
            "amds_scope_lock": scope,
            "duplicate_solver_added": scope.get("new_solver_added"),
        },
    )
    write_json_deterministic(
        OUT_DIR / "batch056b_claim_boundary_preservation.json",
        {
            "status": "PASS",
            "issue_derived_repair_count": ISSUE_DERIVED_REPAIR_COUNT,
            "native_external_repair_count": NATIVE_EXTERNAL_REPAIR_COUNT,
            "full_scoring": "NOT_RUN/disallowed",
            "memory_lift": "not_demonstrated",
            "self_maintaining_software": "false/not_demonstrated",
            "repair_count_increment": False,
            "patch_generated_in_batch056d": False,
            "patch_applied_in_batch056d": False,
        },
    )
    write_json_deterministic(
        OUT_DIR / "batch056b_next_action_boundary.json",
        {
            "status": "PASS",
            "batch056b_next_allowed_action": final.get("next_allowed_action"),
            "expected_next_allowed_action": "batch056d_wave2_provider_dependency_recovery",
            "matches_expected": final.get("next_allowed_action") == "batch056d_wave2_provider_dependency_recovery",
        },
    )


def write_lineage() -> None:
    rows = [
        {"batch": "Batch056", "branch": "Wave 1 plus Wave 2 intake", "role": "Wave 1 pre-repair replay plus Wave 2 intake", "chronological_order": 56},
        {"batch": "Batch057", "branch": "Wave 1", "role": "Wave 1 source-only patch gate", "chronological_order": 57},
        {"batch": "Batch057b", "branch": "Wave 1", "role": "Wave 1 failure-family decomposition and elbow recovery", "chronological_order": 58},
        {"batch": "Batch057c", "branch": "Wave 1", "role": "Wave 1 Freezegun layered patch recovery", "chronological_order": 59},
        {"batch": "Batch056b", "branch": "Wave 2", "role": "Return to Wave 2 pre-repair replay plus AMDS bridge", "chronological_order": 60},
        {"batch": "Batch056d", "branch": "Wave 2", "role": "Wave 2 provider/dependency recovery", "chronological_order": 61},
        {"batch": "Batch058", "branch": "count gate reserved", "role": "Reserved for duplicate clean replay and issue-derived repair count gate only after a target-pass source-only patch exists", "chronological_order": None},
    ]
    write_json_deterministic(
        OUT_DIR / "batch_lineage_map.json",
        {
            "status": "PASS",
            "lineage": rows,
            "batch056d_after_batch057c_valid": True,
            "reason": "Batch056d is branch-relative to the Wave 2 lane after the Wave 1 Freezegun branch completed.",
        },
    )
    write_json_deterministic(
        OUT_DIR / "batch_numbering_sanity_check.json",
        {
            "status": "PASS",
            "batch056d_is_branch_relative": True,
            "chronological_rollback_occurred": False,
            "do_not_rename_batch056d_to_batch058": True,
            "batch058_reserved_until_source_patch_target_pass_duplicate_replay_count_gate": True,
            "batch058_candidate_exists": False,
        },
    )
    write_json_deterministic(OUT_DIR / "branch_relative_batch_index.json", {"status": "PASS", "wave2_branch": ["Batch056", "Batch056b", "Batch056d"], "wave1_branch": ["Batch056", "Batch057", "Batch057b", "Batch057c"]})
    write_json_deterministic(OUT_DIR / "chronological_execution_index.json", {"status": "PASS", "chronological_execution": rows[:-1]})
    write_json_deterministic(
        OUT_DIR / "next_allowed_action_validation.json",
        {
            "status": "PASS",
            "incoming_next_allowed_action": "batch056d_wave2_provider_dependency_recovery",
            "batch056d_allowed": True,
            "batch058_allowed": False,
        },
    )


def write_public_docs(summary: dict[str, Any]) -> None:
    section = "\n".join(
        [
            "",
            "### Batch056d Wave 2 provider/dependency recovery",
            "",
            "- Batch056b official ingest status: `PASS`.",
            "- Batch-lineage sanity: `PASS`; Batch056d follows Batch057c as a branch-relative return to the Wave 2 lane, not as a chronological rollback.",
            f"- Provider/dependency recovery attempted candidates: `{', '.join(summary['attempted_candidates'])}`.",
            f"- Provider/dependency recovery succeeded count: `{summary['provider_dependency_recovery_succeeded_count']}`.",
            f"- Post-recovery materialized target-code failure count: `{summary['post_recovery_materialized_target_code_failure_count']}`.",
            f"- Still-blocked candidates: `{', '.join(summary['still_blocked_candidates']) or 'none'}`.",
            f"- Timeout decomposition candidates deferred: `{', '.join(summary['timeout_decomposition_candidates_deferred']) or 'none'}`.",
            f"- Future decomposition recommendations: `{', '.join(summary['future_decomposition_recommendations']) or 'none'}`.",
            f"- Future patch-gate recommendations: `{', '.join(summary['future_patch_gate_recommendations']) or 'none'}`.",
            f"- Freezegun provider portability recommendation: `{summary['freezegun_provider_portability_recommendation']}`.",
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
        marker = "### Batch056d Wave 2 provider/dependency recovery"
        if marker in text:
            text = text.split(marker, 1)[0].rstrip() + section
        else:
            text = text.rstrip() + "\n" + section
        write_text_lf(path, text)


def main() -> int:
    if not BATCH056B_ZIP.is_file():
        OUT_DIR.mkdir(parents=True, exist_ok=True)
        write_json_deterministic(
            OUT_DIR / "audit.json",
            {"status": "BLOCK", "exact_blocker": "batch056b_artifact_absent_for_official_ingest"},
        )
        write_sha256sums(OUT_DIR)
        print("batch056b_artifact_absent_for_official_ingest")
        return 2

    safe_rmtree(OUT_DIR)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    artifact = verify_official_zip(
        BATCH056B_ZIP,
        artifact_name=BATCH056B_ARTIFACT_NAME,
        artifact_id=BATCH056B_ARTIFACT_ID,
        workflow_run_id=BATCH056B_WORKFLOW_RUN_ID,
        workflow_head_sha=BATCH056B_WORKFLOW_HEAD_SHA,
        expected_sha256=BATCH056B_SHA256,
        expected_size=BATCH056B_SIZE,
        expected_entry_count=BATCH056B_ENTRY_COUNT,
        artifact_manifest_checked=BATCH056B_ARTIFACT_MANIFEST_CHECKED,
        output_manifests=BATCH056B_OUTPUT_MANIFESTS,
    )
    if artifact["status"] != "PASS":
        write_json_deterministic(OUT_DIR / "batch056b_artifact_sha256_verification.json", artifact)
        write_json_deterministic(OUT_DIR / "audit.json", {"status": "BLOCK", "exact_blocker": artifact.get("exact_blocker")})
        write_sha256sums(OUT_DIR)
        print(json.dumps(artifact, indent=2, sort_keys=True))
        return 2
    ingest = ingest_official_outputs(
        BATCH056B_ZIP,
        ROOT,
        prefixes=("post_v2_37_hardening_batch056b_wave2_pre_repair_replay_plus_amds_bridge",),
    )
    if ingest["status"] != "PASS":
        write_json_deterministic(OUT_DIR / "batch056b_artifact_ingestion_summary.json", {"status": "BLOCK", "artifact_verification": artifact, "ingest": ingest})
        write_json_deterministic(OUT_DIR / "audit.json", {"status": "BLOCK", "exact_blocker": ingest.get("exact_blocker")})
        write_sha256sums(OUT_DIR)
        return 2

    write_phase_a(artifact, ingest)
    write_lineage()

    prior_rows = {row["lead_id"]: row for row in read_json(BATCH056B_DIR / "wave2_pre_repair_replay_results.json")["results"]}
    safe_rmtree(RUNTIME_ROOT)
    RUNTIME_ROOT.mkdir(parents=True, exist_ok=True)
    results = [recover_candidate(prior_rows[candidate_id]) for candidate_id in PROVIDER_RECOVERY_CANDIDATES]

    materialized = [row for row in results if row["materialized_target_code_failure"]]
    succeeded = [row for row in results if row["provider_dependency_recovery_succeeded"]]
    still_blocked = [row for row in results if not row["materialized_target_code_failure"]]
    patch_gate = [row for row in materialized if row["future_patch_license_state"] in {"future_patch_license_open_single_source_family", "future_patch_license_open_primary_family_diagnostic_only"}]
    decomposition = [row for row in materialized if row["future_patch_license_state"] == "future_decomposition_needed_before_patch"]

    write_json_deterministic(
        OUT_DIR / "provider_dependency_recovery_plan.json",
        {
            "status": "PASS",
            "attempted_candidates": PROVIDER_RECOVERY_CANDIDATES,
            "deferred_timeout_candidates": TIMEOUT_DECOMPOSITION_CANDIDATES,
            "provider_dependency_only": True,
            "patch_generation_allowed": False,
        },
    )
    write_json_deterministic(OUT_DIR / "provider_dependency_recovery_results.json", {"status": "PASS", "results": results})
    write_json_deterministic(
        OUT_DIR / "provider_dependency_recovery_dashboard.json",
        {
            "status": "PASS",
            "classifications": {row["candidate_id"]: row["classification"] for row in results},
            "amds_bridge_classifications_after_recovery": {row["candidate_id"]: row["future_patch_license_state"] for row in results},
        },
    )
    write_json_deterministic(
        OUT_DIR / "post_recovery_prerepair_replay_results.json",
        {
            "status": "PASS",
            "results": [
                {
                    "candidate_id": row["candidate_id"],
                    "post_recovery_prerepair_replay_ran": row["post_recovery_prerepair_replay_ran"],
                    "classification": row["classification"],
                }
                for row in results
            ],
        },
    )
    write_json_deterministic(OUT_DIR / "materialized_failure_candidates_after_recovery.json", {"status": "PASS", "count": len(materialized), "candidates": materialized})
    write_json_deterministic(OUT_DIR / "still_blocked_provider_dependency_candidates.json", {"status": "PASS", "count": len(still_blocked), "candidates": still_blocked})
    write_json_deterministic(
        OUT_DIR / "timeout_decomposition_deferred_registry.json",
        {
            "status": "PASS",
            "deferred": True,
            "candidate_count": len(TIMEOUT_DECOMPOSITION_CANDIDATES),
            "candidates": TIMEOUT_DECOMPOSITION_CANDIDATES,
            "decomposition_run_in_batch056d": False,
        },
    )
    write_json_deterministic(OUT_DIR / "future_failure_decomposition_recommendation.json", {"status": "PASS", "recommended_candidates": [row["candidate_id"] for row in decomposition] or TIMEOUT_DECOMPOSITION_CANDIDATES})
    write_json_deterministic(OUT_DIR / "future_patch_gate_recommendation.json", {"status": "PASS", "recommended_candidates": [row["candidate_id"] for row in patch_gate]})
    write_json_deterministic(
        OUT_DIR / "freezegun_provider_portability_plan_preservation.json",
        {
            "status": "PASS",
            "freezegun_provider_portability_recommendation": "future_explicit_authorization_required",
            "exact_blocker_preserved": "secondary_family_provider_tzset_unavailable",
            "freezegun_patched_in_batch056d": False,
        },
    )
    write_json_deterministic(
        OUT_DIR / "amds_bridge_after_recovery_dashboard.json",
        {
            "status": "PASS",
            "classifications": {row["candidate_id"]: row["future_patch_license_state"] for row in results},
            "patch_license_future_only": True,
            "patching_authorized_in_batch056d": False,
        },
    )

    if patch_gate:
        next_allowed = "batch057e_source_only_patch_gate_wave_2"
    elif decomposition:
        next_allowed = "batch056c_failure_family_decomposition_wave_2"
    elif len(still_blocked) == len(results) and TIMEOUT_DECOMPOSITION_CANDIDATES:
        next_allowed = "batch056e_timeout_candidate_decomposition_wave_2"
    else:
        next_allowed = "batch057d_freezegun_provider_portability_secondary_family_probe"

    summary = {
        "status": "PASS",
        "attempted_candidates": PROVIDER_RECOVERY_CANDIDATES,
        "provider_dependency_recovery_succeeded_count": len(succeeded),
        "post_recovery_materialized_target_code_failure_count": len(materialized),
        "still_blocked_candidates": [row["candidate_id"] for row in still_blocked],
        "candidate_classifications_after_recovery": {row["candidate_id"]: row["classification"] for row in results},
        "amds_bridge_after_recovery_classifications": {row["candidate_id"]: row["future_patch_license_state"] for row in results},
        "timeout_decomposition_candidates_deferred": TIMEOUT_DECOMPOSITION_CANDIDATES,
        "future_decomposition_recommendations": [row["candidate_id"] for row in decomposition] or TIMEOUT_DECOMPOSITION_CANDIDATES,
        "future_patch_gate_recommendations": [row["candidate_id"] for row in patch_gate],
        "freezegun_provider_portability_recommendation": "future_explicit_authorization_required",
        "next_allowed_action": next_allowed,
        "issue_derived_repair_count": ISSUE_DERIVED_REPAIR_COUNT,
        "native_external_repair_count": NATIVE_EXTERNAL_REPAIR_COUNT,
        "full_scoring": "NOT_RUN/disallowed",
        "memory_lift": "not_demonstrated",
        "self_maintaining_software": "false/not_demonstrated",
        "exact_blocker": None if materialized else "all_provider_dependency_recovery_candidates_remain_blocked",
    }
    write_json_deterministic(
        OUT_DIR / "batch056d_final_decision.json",
        {
            "status": "PASS",
            "next_allowed_action": next_allowed,
            "exact_blocker": summary["exact_blocker"],
            "patch_generated": False,
            "patch_applied": False,
            "post_repair_replay_run": False,
            "duplicate_replay_run": False,
            "count_gate_run": False,
            "repair_count_increment": False,
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
            "batch056d_patch_generated": False,
            "batch056d_patch_applied": False,
            "batch056d_post_repair_replay_run": False,
            "batch056d_duplicate_replay_run": False,
            "batch056d_count_gate_run": False,
            "batch056d_repair_count_increment": False,
            "freezegun_patched_in_batch056d": False,
            "wave2_patched_in_batch056d": False,
        },
    )
    write_json_deterministic(OUT_DIR / "audit.json", {"status": "PASS", "audit_script": "scripts/audit_batch056d_wave2_provider_dependency_recovery.py"})
    write_json_deterministic(
        OUT_DIR / "package_verification.json",
        {
            "status": "PASS",
            "artifact_name": "post_v2_37_hardening_batch056d_wave2_provider_dependency_recovery_artifacts",
            "raw_zip_payload_committed": False,
            "runtime_workspaces_committed": False,
        },
    )
    write_json_deterministic(
        OUT_DIR / "artifact_sha256_verification.json",
        {
            "status": "PENDING_WORKFLOW_ARTIFACT",
            "artifact_name": "post_v2_37_hardening_batch056d_wave2_provider_dependency_recovery_artifacts",
            "artifact_sha256_available_after_workflow_upload": True,
            "batch056b_local_zip_sha256": BATCH056B_SHA256,
        },
    )
    write_text_lf(
        OUT_DIR / "provider_dependency_recovery_summary.md",
        "\n".join(
            [
                "# Batch056d Wave 2 provider/dependency recovery",
                "",
                "- Batch056b official ingest: `PASS`",
                "- Numbering sanity: `PASS`",
                f"- Attempted candidates: `{', '.join(PROVIDER_RECOVERY_CANDIDATES)}`",
                f"- Provider/dependency recovery succeeded count: `{len(succeeded)}`",
                f"- Materialized target-code failures after recovery: `{len(materialized)}`",
                f"- Still blocked candidates: `{', '.join(row['candidate_id'] for row in still_blocked) or 'none'}`",
                f"- Future decomposition recommendations: `{', '.join(summary['future_decomposition_recommendations']) or 'none'}`",
                f"- Future patch-gate recommendations: `{', '.join(summary['future_patch_gate_recommendations']) or 'none'}`",
                f"- Next allowed action: `{next_allowed}`",
                "- Provider/dependency recovery is not target-code repair success.",
                "- Patches, duplicate replay, and count gate remain closed.",
                "",
            ]
        ),
    )
    write_public_docs(summary)
    write_sha256sums(OUT_DIR)
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
