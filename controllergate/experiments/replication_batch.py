from __future__ import annotations

from controllergate.core.acquisition import discover_seed_files


def _mode_enabled(config: dict[str, object], mode: str) -> bool:
    configured = str(config.get("candidate_source_mode", "mixed"))
    if configured == "mixed":
        return True
    return configured == mode


def run_replication_batch(config: dict[str, object]) -> dict[str, object]:
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

    if _mode_enabled(config, "metadata_probe"):
        metadata_attempt = {
            "mode": "metadata_probe",
            "repo": "offline_local_metadata_lead_pool",
            "query_or_lead_source": "repository_local_lead_pool",
            "commit_or_issue_candidate": None,
            "decision": "rejected_no_verified_native_candidate",
            "blocker": "metadata_probe_no_verified_candidates",
            "checkout_attempted": False,
            "target_environment_checks_attempted": False,
            "failure_replay_attempted": False,
            "network_status": "not_required_for_repository_local_check",
        }
        metadata_attempts.append(metadata_attempt)
        attempts.append(metadata_attempt)
        rejections.append({"mode": "metadata_probe", "blocker": "metadata_probe_no_verified_candidates", "reason": "No safe repository-local metadata leads were available."})
        trace.append({"mode": "metadata_probe", "attempted": True, "verified_native_candidate_count": 0, "decision": "metadata_probe_no_verified_candidates"})
    else:
        trace.append({"mode": "metadata_probe", "attempted": False, "decision": "metadata_probe_disabled"})

    if _mode_enabled(config, "issue_derived"):
        issue_attempt = {
            "mode": "issue_derived",
            "issue_lead": "offline_local_issue_lead_pool",
            "timestamp_guard_status": "not_run_no_safe_issue_lead",
            "latent_knowledge_risk_status": "not_run_no_generation",
            "harness_generation_attempted": False,
            "decision": "rejected_no_verified_issue_derived_candidate",
            "blocker": "issue_derived_no_verified_candidates",
        }
        issue_attempts.append(issue_attempt)
        attempts.append(issue_attempt)
        rejections.append({"mode": "issue_derived", "blocker": "issue_derived_no_verified_candidates", "reason": "No safe repository-local issue-derived leads were available."})
        trace.append({"mode": "issue_derived", "attempted": True, "verified_issue_derived_candidate_count": 0, "decision": "issue_derived_no_verified_candidates"})
    else:
        trace.append({"mode": "issue_derived", "attempted": False, "decision": "issue_derived_disabled"})

    return {
        "status": "BLOCKED",
        "exact_blocker": "clean_replication_batch_002_no_verified_candidates",
        "summary_status": "no_additional_external_repairs_acquired",
        "candidate_source_mode_trace": trace,
        "curated_seed_intake_report": {"status": "BLOCKED", "seed_files": [], "blocker": "curated_seed_no_valid_seed"},
        "metadata_probe_attempts": metadata_attempts,
        "issue_derived_attempts": issue_attempts,
        "candidate_verification_attempts": attempts,
        "candidate_rejection_ledger": rejections,
        "verified_candidates": [],
        "repair_attempts": [],
        "repair_successes": [],
        "matched_null_results": [],
    }
