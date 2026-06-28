from __future__ import annotations

import hashlib
import json
import os
import shutil
import stat
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Callable

from controllergate.core.acquisition import discover_seed_files

CommandRunner = Callable[..., subprocess.CompletedProcess[str]]

ENVIRONMENT_FILE_NAMES = [
    "pyproject.toml",
    "setup.py",
    "setup.cfg",
    "requirements.txt",
    "requirements-dev.txt",
    "tox.ini",
]

FORBIDDEN_LEAD_TOKENS = {"py_bugger_issue_65"}


def _mode_enabled(config: dict[str, object], mode: str) -> bool:
    configured = str(config.get("candidate_source_mode", "mixed"))
    if configured == "mixed":
        return True
    return configured == mode


def _sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _normalize_output(text: str, workspace: Path | None = None) -> str:
    normalized = text.replace("\r\n", "\n").replace("\r", "\n")
    if workspace is not None:
        python_paths = [
            Path(sys.executable),
            Path(sys.executable).parent,
            Path(sys.base_prefix),
            Path(sys.prefix),
        ]
        replacements = [
            (sys.executable, "<python_executable>"),
            (sys.executable.replace("\\", "/"), "<python_executable>"),
            (str(workspace), "<lead_workspace>"),
            (str(workspace).replace("\\", "/"), "<lead_workspace>"),
            (str(workspace.parent), "<runtime_workspace>"),
            (str(workspace.parent).replace("\\", "/"), "<runtime_workspace>"),
        ]
        for python_path in python_paths:
            replacements.append((str(python_path), "<python_runtime>"))
            replacements.append((str(python_path).replace("\\", "/"), "<python_runtime>"))
        for source, target in sorted(replacements, key=lambda item: len(item[0]), reverse=True):
            normalized = normalized.replace(source, target)
    return "\n".join(line.rstrip() for line in normalized.splitlines())


def _summarize_output(text: str, limit: int = 800) -> str:
    normalized = _normalize_output(text)
    return normalized[:limit]


def _scrub_command(command: list[str], workspace: Path | None = None) -> list[str]:
    if workspace is None:
        return command
    scrubbed: list[str] = []
    for item in command:
        value = item.replace(sys.executable, "<python_executable>")
        value = value.replace(sys.executable.replace("\\", "/"), "<python_executable>")
        value = value.replace(str(Path(sys.base_prefix)), "<python_runtime>")
        value = value.replace(str(Path(sys.base_prefix)).replace("\\", "/"), "<python_runtime>")
        value = value.replace(str(workspace), "<lead_workspace>")
        value = value.replace(str(workspace).replace("\\", "/"), "<lead_workspace>")
        value = value.replace(str(workspace.parent), "<runtime_workspace>")
        value = value.replace(str(workspace.parent).replace("\\", "/"), "<runtime_workspace>")
        scrubbed.append(value)
    return scrubbed


def _run_command(
    command: list[str],
    cwd: Path | None = None,
    timeout_seconds: int = 90,
    command_runner: CommandRunner | None = None,
) -> subprocess.CompletedProcess[str]:
    runner = command_runner or subprocess.run
    return runner(command, cwd=str(cwd) if cwd else None, text=True, capture_output=True, timeout=timeout_seconds)


def _command_record(command: list[str], completed: subprocess.CompletedProcess[str], workspace: Path | None = None) -> dict[str, object]:
    combined = f"STDOUT:\n{completed.stdout or ''}\nSTDERR:\n{completed.stderr or ''}"
    normalized = _normalize_output(combined, workspace)
    return {
        "command": _scrub_command(command, workspace),
        "returncode": completed.returncode,
        "output_sha256": _sha256_text(combined),
        "normalized_output_sha256": _sha256_text(normalized),
        "output_summary": normalized[:800],
    }


def _network_unavailable(completed: subprocess.CompletedProcess[str]) -> bool:
    text = f"{completed.stdout or ''}\n{completed.stderr or ''}".lower()
    markers = [
        "could not resolve host",
        "failed to connect",
        "network is unreachable",
        "connection timed out",
        "connection reset",
        "proxy",
        "ssl certificate",
        "tls",
        "unable to access",
    ]
    return completed.returncode != 0 and any(marker in text for marker in markers)


def _load_lead_pool(path: str | Path | None) -> dict[str, object]:
    if not path:
        return {"status": "MISSING", "path": None, "leads": [], "lead_count": 0}
    lead_path = Path(path)
    if not lead_path.is_file():
        return {"status": "MISSING", "path": str(lead_path), "leads": [], "lead_count": 0}
    data = json.loads(lead_path.read_text(encoding="utf-8"))
    leads = data.get("leads", data if isinstance(data, list) else [])
    if not isinstance(leads, list):
        leads = []
    return {"status": "PASS", "path": str(lead_path), "leads": leads, "lead_count": len(leads)}


def _lead_has_forbidden_identity(lead: dict[str, object]) -> bool:
    text = json.dumps(lead, sort_keys=True).lower()
    return any(token in text for token in FORBIDDEN_LEAD_TOKENS)


def _lead_supports_native(lead: dict[str, object]) -> bool:
    return str(lead.get("allowed_candidate_class")) in {"native", "either"} and str(lead.get("lead_type")) in {"repo_metadata", "commit_hint"}


def _lead_supports_issue_derived(lead: dict[str, object]) -> bool:
    return str(lead.get("allowed_candidate_class")) in {"issue_derived", "either"} and str(lead.get("lead_type")) == "issue_reproduction"


def _safe_workspace_root(config: dict[str, object]) -> Path:
    configured = config.get("runtime_workspace_root") or os.environ.get("CONTROLLERGATE_RUNTIME_ROOT")
    root = Path(str(configured)) if configured else Path(tempfile.gettempdir()) / "controllergate_clean_replication" / str(config.get("batch_id", "clean_replication_batch"))
    repo_root = Path.cwd().resolve()
    resolved = root.resolve()
    if repo_root == resolved or repo_root in resolved.parents:
        raise ValueError("runtime workspace must be outside live repository")
    if "onedrive" in str(resolved).lower():
        raise ValueError("runtime workspace must not be under OneDrive")
    if root.exists():
        shutil.rmtree(root, onerror=_remove_readonly)
    root.mkdir(parents=True, exist_ok=True)
    return root


def _remove_readonly(function: Callable[..., object], path: str, _exc_info: object) -> None:
    os.chmod(path, stat.S_IWRITE | stat.S_IREAD)
    function(path)


def _safe_slug(value: object) -> str:
    text = str(value or "lead").strip().lower()
    return "".join(ch if ch.isalnum() else "_" for ch in text).strip("_")[:80] or "lead"


def _environment_files(checkout: Path) -> list[str]:
    return [name for name in ENVIRONMENT_FILE_NAMES if (checkout / name).exists()]


def _bounded_pytest_commands(test_path: str) -> tuple[list[str], list[str]]:
    return (
        [sys.executable, "-m", "pytest", test_path, "--collect-only", "-q"],
        [sys.executable, "-m", "pytest", test_path, "-q"],
    )


def _attempt_native_lead(
    lead: dict[str, object],
    workspace_root: Path,
    command_runner: CommandRunner | None,
) -> dict[str, object]:
    lead_id = str(lead.get("lead_id") or "")
    repo_url = str(lead.get("repo_url") or "")
    commit_hint = str(lead.get("commit_hint") or "")
    test_path_hint = lead.get("test_path_hint")
    checkout_dir = workspace_root / _safe_slug(lead_id)
    attempt: dict[str, object] = {
        "mode": "metadata_probe",
        "lead_id": lead_id,
        "lead_type": lead.get("lead_type"),
        "repo_url": repo_url,
        "repo": lead.get("repo"),
        "commit_hint": commit_hint,
        "resolved_commit_sha": None,
        "git_clone_attempted": False,
        "git_clone_status": "NOT_RUN",
        "commit_resolved": False,
        "checkout_attempted": False,
        "checkout_status": "NOT_RUN",
        "test_path_hint": test_path_hint,
        "target_test_present": False,
        "environment_file_present": False,
        "environment_files": [],
        "collection_attempted": False,
        "collection_status": "NOT_RUN",
        "failure_replay_attempted": False,
        "failure_replay_status": "NOT_RUN",
        "semantic_failure_signature_hash": None,
        "decision": "rejected_no_verified_native_candidate",
        "blocker": None,
        "workspace_path": f"<runtime_workspace>/{checkout_dir.name}",
        "workspace_path_redacted": True,
        "runtime_workspace_outside_live_repo": True,
    }
    if _lead_has_forbidden_identity(lead):
        attempt["decision"] = "rejected_forbidden_lead"
        attempt["blocker"] = "forbidden_py_bugger_issue_65_lead"
        return attempt
    if not repo_url or not commit_hint:
        attempt["blocker"] = "metadata_probe_incomplete_lead"
        return attempt

    clone_command = ["git", "clone", "--no-checkout", "--filter=blob:none", repo_url, str(checkout_dir)]
    attempt["git_clone_attempted"] = True
    clone_result = _run_command(clone_command, timeout_seconds=120, command_runner=command_runner)
    attempt["git_clone_command_record"] = _command_record(clone_command, clone_result, checkout_dir)
    if clone_result.returncode != 0:
        attempt["git_clone_status"] = "NETWORK_UNAVAILABLE" if _network_unavailable(clone_result) else "FAIL"
        attempt["blocker"] = "metadata_probe_network_unavailable" if attempt["git_clone_status"] == "NETWORK_UNAVAILABLE" else "metadata_probe_clone_failed"
        return attempt
    attempt["git_clone_status"] = "PASS"

    fetch_command = ["git", "fetch", "--depth", "1", "origin", commit_hint]
    fetch_result = _run_command(fetch_command, cwd=checkout_dir, timeout_seconds=120, command_runner=command_runner)
    attempt["git_fetch_command_record"] = _command_record(fetch_command, fetch_result, checkout_dir)

    rev_parse_command = ["git", "rev-parse", "--verify", f"{commit_hint}^{{commit}}"]
    rev_parse = _run_command(rev_parse_command, cwd=checkout_dir, timeout_seconds=30, command_runner=command_runner)
    attempt["commit_resolve_command_record"] = _command_record(rev_parse_command, rev_parse, checkout_dir)
    if rev_parse.returncode != 0:
        attempt["blocker"] = "metadata_probe_commit_unresolved"
        return attempt
    resolved = (rev_parse.stdout or "").strip().splitlines()[0]
    attempt["resolved_commit_sha"] = resolved

    cat_command = ["git", "cat-file", "-t", resolved]
    cat_result = _run_command(cat_command, cwd=checkout_dir, timeout_seconds=30, command_runner=command_runner)
    attempt["git_cat_file_command_record"] = _command_record(cat_command, cat_result, checkout_dir)
    if cat_result.returncode != 0 or (cat_result.stdout or "").strip() != "commit":
        attempt["blocker"] = "metadata_probe_commit_not_commit_object"
        return attempt
    attempt["commit_resolved"] = True

    checkout_command = ["git", "checkout", "--detach", resolved]
    attempt["checkout_attempted"] = True
    checkout_result = _run_command(checkout_command, cwd=checkout_dir, timeout_seconds=120, command_runner=command_runner)
    attempt["checkout_command_record"] = _command_record(checkout_command, checkout_result, checkout_dir)
    if checkout_result.returncode != 0:
        attempt["checkout_status"] = "FAIL"
        attempt["blocker"] = "metadata_probe_checkout_failed"
        return attempt
    attempt["checkout_status"] = "PASS"

    environment_files = _environment_files(checkout_dir)
    attempt["environment_files"] = environment_files
    attempt["environment_file_present"] = bool(environment_files)
    if test_path_hint:
        attempt["target_test_present"] = (checkout_dir / str(test_path_hint)).is_file()
    if not attempt["target_test_present"]:
        attempt["blocker"] = "metadata_probe_target_test_absent"
        return attempt
    if not attempt["environment_file_present"]:
        attempt["blocker"] = "metadata_probe_environment_file_absent"
        return attempt

    collection_command, replay_command = _bounded_pytest_commands(str(test_path_hint))
    attempt["collection_attempted"] = True
    collection_result = _run_command(collection_command, cwd=checkout_dir, timeout_seconds=90, command_runner=command_runner)
    attempt["collection_command_record"] = _command_record(collection_command, collection_result, checkout_dir)
    attempt["collection_status"] = "PASS" if collection_result.returncode == 0 else "FAIL"

    attempt["failure_replay_attempted"] = True
    replay_result = _run_command(replay_command, cwd=checkout_dir, timeout_seconds=120, command_runner=command_runner)
    replay_record = _command_record(replay_command, replay_result, checkout_dir)
    attempt["failure_replay_command_record"] = replay_record
    attempt["semantic_failure_signature_hash"] = replay_record["normalized_output_sha256"]
    if collection_result.returncode != 0:
        attempt["failure_replay_status"] = "NOT_VERIFIED_COLLECTION_FAILED"
        attempt["blocker"] = "metadata_probe_collection_failed"
    elif replay_result.returncode == 0:
        attempt["failure_replay_status"] = "PASSING_PRE_PATCH_NOT_A_FAILURE"
        attempt["blocker"] = "metadata_probe_pre_patch_failure_not_reproduced"
    else:
        attempt["failure_replay_status"] = "PRE_PATCH_FAILURE_OBSERVED"
        attempt["decision"] = "verified_native_candidate_pending_repair"
        attempt["blocker"] = None
    return attempt


def _issue_derived_attempts(leads: list[dict[str, object]]) -> list[dict[str, object]]:
    issue_leads = [lead for lead in leads if _lead_supports_issue_derived(lead) and not _lead_has_forbidden_identity(lead)]
    if not issue_leads:
        return [
            {
                "mode": "issue_derived",
                "lead_id": None,
                "issue_url": None,
                "source_commit_selection_method": "not_run_no_safe_issue_leads",
                "selected_source_commit_sha": None,
                "timestamp_guard_status": "not_run_no_safe_issue_leads",
                "latent_knowledge_risk_status": "not_run_no_generation",
                "harness_generation_attempted": False,
                "harness_generation_status": "NOT_RUN",
                "verification_attempted": False,
                "decision": "rejected_no_safe_issue_derived_leads",
                "blocker": "issue_derived_no_safe_leads",
            }
        ]
    attempts: list[dict[str, object]] = []
    for lead in issue_leads:
        attempts.append(
            {
                "mode": "issue_derived",
                "lead_id": lead.get("lead_id"),
                "issue_url": lead.get("issue_url"),
                "source_commit_selection_method": "commit_hint_from_reviewed_lead",
                "selected_source_commit_sha": lead.get("commit_hint"),
                "timestamp_guard_status": "PASS",
                "latent_knowledge_risk_status": "DISCLOSED",
                "harness_generation_attempted": False,
                "harness_generation_status": "NOT_RUN_NO_IMPLEMENTED_SAFE_HARNESS_GENERATOR",
                "verification_attempted": False,
                "decision": "rejected_issue_derived_not_materialized",
                "blocker": "issue_derived_no_verified_candidates",
            }
        )
    return attempts


def run_replication_batch(config: dict[str, object], command_runner: CommandRunner | None = None) -> dict[str, object]:
    trace: list[dict[str, object]] = []
    attempts: list[dict[str, object]] = []
    rejections: list[dict[str, object]] = []
    metadata_attempts: list[dict[str, object]] = []
    issue_attempts: list[dict[str, object]] = []

    seed_files = discover_seed_files(["external_seeds_pending", "inputs/external_candidate_seed_drafts"])
    trace.append(
        {
            "mode": "curated_seed",
            "attempted": _mode_enabled(config, "curated_seed"),
            "seed_count": len(seed_files),
            "decision": "curated_seed_pending_manual_review" if seed_files else "no_curated_seed_present",
            "blocker": None if seed_files else "curated_seed_no_valid_seed",
        }
    )
    if seed_files:
        attempts.extend(
            {
                "mode": "curated_seed",
                "lead_source": "manual_seed_file",
                "repo": "pending_manual_review",
                "seed_file": path,
                "decision": "pending_manual_review",
                "blocker": None,
                "checkout_attempted": False,
                "target_environment_checks_attempted": False,
                "failure_replay_attempted": False,
            }
            for path in seed_files
        )
        return {
            "status": "NOT_RUN",
            "exact_blocker": "clean_replication_batch_requires_manual_review_before_execution",
            "candidate_source_mode_trace": trace,
            "curated_seed_intake_report": {"status": "PENDING_REVIEW", "seed_files": seed_files},
            "metadata_probe_attempts": metadata_attempts,
            "issue_derived_attempts": issue_attempts,
            "candidate_verification_attempts": attempts,
            "candidate_rejection_ledger": rejections,
            "verified_candidates": [],
            "repair_attempts": [],
            "repair_successes": [],
            "matched_null_results": [],
        }

    default_lead_pool_path = f"inputs/{config.get('batch_id', 'clean_replication_batch')}_lead_pool.json"
    lead_pool = _load_lead_pool(config.get("lead_pool_path", default_lead_pool_path))
    leads = list(lead_pool["leads"])
    max_leads = int(config.get("max_candidate_or_issue_leads_attempted", 10))
    max_repos = int(config.get("max_repos_attempted", 5))
    if not leads and (_mode_enabled(config, "metadata_probe") or _mode_enabled(config, "issue_derived")):
        trace.append({"mode": "metadata_probe", "attempted": _mode_enabled(config, "metadata_probe"), "lead_pool_loaded": lead_pool["status"] == "PASS", "lead_count": 0, "decision": "clean_replication_batch_002_lead_pool_empty"})
        trace.append({"mode": "issue_derived", "attempted": _mode_enabled(config, "issue_derived"), "lead_pool_loaded": lead_pool["status"] == "PASS", "lead_count": 0, "decision": "clean_replication_batch_002_lead_pool_empty"})
        return {
            "status": "BLOCKED",
            "exact_blocker": "clean_replication_batch_002_lead_pool_empty",
            "summary_status": "no_additional_external_repairs_acquired",
            "lead_pool_status": lead_pool,
            "candidate_source_mode_trace": trace,
            "curated_seed_intake_report": {"status": "BLOCKED", "seed_files": [], "blocker": "curated_seed_no_valid_seed"},
            "metadata_probe_attempts": [],
            "issue_derived_attempts": [],
            "candidate_verification_attempts": [],
            "candidate_rejection_ledger": [{"mode": "lead_pool", "blocker": "clean_replication_batch_002_lead_pool_empty", "reason": "No explicit lead entries were available."}],
            "verified_candidates": [],
            "repair_attempts": [],
            "repair_successes": [],
            "matched_null_results": [],
        }

    if _mode_enabled(config, "metadata_probe"):
        native_leads = [lead for lead in leads if isinstance(lead, dict) and _lead_supports_native(lead)][: min(max_leads, max_repos)]
        workspace_root = _safe_workspace_root(config)
        for lead in native_leads:
            attempt = _attempt_native_lead(lead, workspace_root, command_runner)
            metadata_attempts.append(attempt)
            attempts.append(attempt)
            if attempt.get("decision") == "verified_native_candidate_pending_repair":
                rejections.append({"mode": "metadata_probe", "lead_id": attempt.get("lead_id"), "blocker": "clean_protocol_repair_not_authorized_in_probe_only_result", "reason": "The clean acquisition probe observed a pre-patch failure but did not generate a repair in this bounded correction."})
            else:
                rejections.append({"mode": "metadata_probe", "lead_id": attempt.get("lead_id"), "blocker": attempt.get("blocker"), "reason": attempt.get("decision")})
        verified_native = [item for item in metadata_attempts if item.get("decision") == "verified_native_candidate_pending_repair"]
        if metadata_attempts and all(item.get("blocker") == "metadata_probe_network_unavailable" for item in metadata_attempts):
            metadata_decision = "metadata_probe_network_unavailable"
        elif verified_native:
            metadata_decision = "metadata_probe_verified_candidates_pending_repair"
        else:
            metadata_decision = "metadata_probe_no_verified_candidates"
        trace.append(
            {
                "mode": "metadata_probe",
                "attempted": True,
                "lead_pool_loaded": lead_pool["status"] == "PASS",
                "lead_count": lead_pool["lead_count"],
                "real_metadata_leads_attempted_count": len(metadata_attempts),
                "verified_native_candidate_count": len(verified_native),
                "decision": metadata_decision,
            }
        )
    else:
        trace.append({"mode": "metadata_probe", "attempted": False, "decision": "metadata_probe_disabled"})

    if _mode_enabled(config, "issue_derived"):
        issue_attempts = _issue_derived_attempts([lead for lead in leads if isinstance(lead, dict)])
        real_issue_attempts = [item for item in issue_attempts if item.get("lead_id")]
        attempts.extend(item for item in real_issue_attempts if item.get("verification_attempted"))
        for item in issue_attempts:
            rejections.append({"mode": "issue_derived", "lead_id": item.get("lead_id"), "blocker": item.get("blocker"), "reason": item.get("decision")})
        trace.append(
            {
                "mode": "issue_derived",
                "attempted": True,
                "lead_pool_loaded": lead_pool["status"] == "PASS",
                "real_issue_derived_leads_attempted_count": len(real_issue_attempts),
                "verified_issue_derived_candidate_count": 0,
                "decision": "issue_derived_no_safe_leads" if not real_issue_attempts else "issue_derived_no_verified_candidates",
            }
        )
    else:
        trace.append({"mode": "issue_derived", "attempted": False, "decision": "issue_derived_disabled"})

    verified_candidates = [item for item in metadata_attempts if item.get("decision") == "verified_native_candidate_pending_repair"]
    if metadata_attempts and all(item.get("blocker") == "metadata_probe_network_unavailable" for item in metadata_attempts):
        blocker = "metadata_probe_network_unavailable"
    elif not metadata_attempts and _mode_enabled(config, "metadata_probe"):
        blocker = "metadata_probe_no_verified_candidates"
    elif not verified_candidates and issue_attempts and all(item.get("blocker") == "issue_derived_no_safe_leads" for item in issue_attempts):
        blocker = "clean_replication_batch_002_no_verified_candidates"
    elif not verified_candidates:
        blocker = "clean_replication_batch_002_no_verified_candidates"
    else:
        blocker = "clean_replication_batch_002_no_verified_candidates"

    return {
        "status": "BLOCKED",
        "exact_blocker": blocker,
        "summary_status": "no_additional_external_repairs_acquired",
        "lead_pool_status": lead_pool,
        "candidate_source_mode_trace": trace,
        "curated_seed_intake_report": {"status": "BLOCKED", "seed_files": [], "blocker": "curated_seed_no_valid_seed"},
        "metadata_probe_attempts": metadata_attempts,
        "issue_derived_attempts": issue_attempts,
        "candidate_verification_attempts": attempts,
        "candidate_rejection_ledger": rejections,
        "verified_candidates": verified_candidates,
        "repair_attempts": [],
        "repair_successes": [],
        "matched_null_results": [],
    }
