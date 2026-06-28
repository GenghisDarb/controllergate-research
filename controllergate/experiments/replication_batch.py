from __future__ import annotations

from controllergate.core.acquisition import discover_seed_files


def run_replication_batch(config: dict[str, object]) -> dict[str, object]:
    seed_files = discover_seed_files(["external_seeds_pending", "inputs/external_candidate_seed_drafts"])
    if not seed_files:
        return {
            "status": "BLOCKED",
            "exact_blocker": "no_additional_external_repairs_acquired",
            "candidate_verification_attempts": [],
            "verified_candidates": [],
            "repair_attempts": [],
            "repair_successes": [],
            "matched_null_results": [],
        }
    return {
        "status": "NOT_RUN",
        "exact_blocker": "clean_replication_batch_requires_manual_review_before_execution",
        "candidate_verification_attempts": [{"seed_file": path, "status": "pending_manual_review"} for path in seed_files],
        "verified_candidates": [],
        "repair_attempts": [],
        "repair_successes": [],
        "matched_null_results": [],
    }
