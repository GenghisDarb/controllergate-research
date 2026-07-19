"""Append the official Batch100 ingest and execution-semantic defects to project memory."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
LEDGER = ROOT / "configs/controllergate_master_completion_ledger_v2.json"
OUTPUT = ROOT / "outputs/post_v2_37_hardening_batch101_canonical_semantic_replay_exact_incident_salvage_ownership_closure"
INGEST_COMMIT = "ffb74368beeb0b4e85b1bf0288d91f9a0a169a97"
STAMP = "2026-07-19T23:40:00Z"


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    ledger = json.loads(LEDGER.read_text(encoding="utf-8"))
    by_id = {row["goal_id"]: row for row in ledger["goals"]}
    ingest_relpaths = [
        "batch100_official_ingest/artifact_identity/batch100_official_outer_artifact_custody.json",
        "batch100_official_ingest/custody/batch100_official_manifest_verification.json",
        "batch100_official_ingest/custody/batch100_official_private_content_scan.json",
        "batch100_official_ingest/reconciliation/batch100_official_semantic_reconciliation.json",
        "batch100_official_ingest/reconciliation/batch100_official_claim_boundary_reconciliation.json",
        "batch100_official_ingest/ingest_receipts/batch100_official_ingest_receipt.json",
    ]
    evidence = [(OUTPUT / rel).relative_to(ROOT).as_posix() for rel in ingest_relpaths]
    hashes = {rel: sha256_file(ROOT / rel) for rel in evidence}
    goal_id = "CG-GOAL-021-OFFICIAL-BATCH100-INGEST"
    if goal_id not in by_id:
        goal = {
            "active_blockers": [],
            "authority_allowed": ["authoritative public Batch100 input for Batch101"],
            "authority_forbidden": ["historical rewrite", "candidate patch", "repair count mutation", "release promotion"],
            "completion_batch": "Batch101",
            "completion_commit": INGEST_COMMIT,
            "current_evidence": evidence,
            "evidence_hashes": hashes,
            "goal_id": goal_id,
            "last_updated_commit": INGEST_COMMIT,
            "last_updated_timestamp": STAMP,
            "prerequisites": ["CG-GOAL-004-OFFICIAL-BATCH099-INGEST"],
            "reopen_conditions": ["outer artifact identity, extracted-tree identity, or semantic reconciliation defect"],
            "required_evidence": [
                "outer artifact identity",
                "manifest verification",
                "semantic reconciliation",
                "claim-boundary reconciliation",
                "private-content scan",
                "ingest checkpoint commit",
                "ingest receipt SHA256",
            ],
            "status": "COMPLETE",
            "title": "Official Batch100 artifact ingest",
        }
        ledger["goals"].append(goal)
        by_id[goal_id] = goal
    defects = {
        "CG-GOAL-005-INCIDENT-IDENTITY-AND-PARITY": [
            "candidate_source_and_provider_identity_not_exact_for_all_programs",
            "prefix_provider_match_conflated_exact_and_series_limited_parity",
            "git_derived_build_version_metadata_not_preserved",
        ],
        "CG-GOAL-006-TYPED-INCIDENT-REMATERIALIZATION": [
            "batch100_predicate_authority_hardcoded_by_candidate",
            "py_bugger_reproducible_count_inflation_misclassified",
            "six_of_eight_candidate_incidents_not_materialized",
        ],
        "CG-GOAL-007-MATCHED-COUNTERFACTUAL-EXECUTION": [
            "raw_and_semantic_replay_identity_not_separated",
            "volatile_output_fields_drove_nonreproducibility",
            "four_openbb_registered_cells_unexecuted",
            "pair_validity_did_not_require_both_predicates_and_all_invariants",
        ],
        "CG-GOAL-008-CAUSAL-OWNERSHIP-CLOSURE": [
            "sensitivity_necessity_sufficiency_interaction_and_ownership_not_reconstructed",
            "ownership_grade_differential_evidence_missing",
        ],
        "CG-GOAL-009-ARCHITECTURE-GAIN": [
            "architecture_arms_operated_on_zero_coverage_terminals",
            "architecture_gain_not_established",
        ],
        "CG-GOAL-010-TLD-ROUTING-GAIN": [
            "tld_ordering_operated_on_incomplete_registered_cell_execution",
            "tld_ordering_gain_not_established",
        ],
        "CG-GOAL-018-PUBLIC-DEFAULT-NON-TLD-MODE": [
            "ordinary_public_non_tld_default_mode_not_established",
        ],
    }
    transition_ids = {row.get("transition_id") for row in ledger.get("supersession_receipts", [])}
    for inherited_id, blockers in defects.items():
        goal = by_id[inherited_id]
        previous = goal["status"]
        goal["active_blockers"] = sorted(set([*goal.get("active_blockers", []), *blockers]))
        goal["last_updated_commit"] = INGEST_COMMIT
        goal["last_updated_timestamp"] = STAMP
        transition_id = f"batch101:{inherited_id}:official-batch100-defect-carryforward"
        if transition_id not in transition_ids:
            ledger.setdefault("supersession_receipts", []).append(
                {
                    "transition_id": transition_id,
                    "goal_id": inherited_id,
                    "previous_status": previous,
                    "new_status": goal["status"],
                    "transition_reason": "Official Batch100 ingest preserved exact execution-semantic defects for Batch101 correction.",
                    "evidence_paths": evidence,
                    "evidence_sha256s": hashes,
                    "transition_commit": INGEST_COMMIT,
                    "reopen_condition": goal["reopen_conditions"],
                }
            )
    goal_transition = f"batch101:{goal_id}:official-ingest-complete"
    if goal_transition not in transition_ids:
        ledger.setdefault("supersession_receipts", []).append(
            {
                "transition_id": goal_transition,
                "goal_id": goal_id,
                "previous_status": "NOT_STARTED",
                "new_status": "COMPLETE",
                "transition_reason": "Exact Batch100 artifact passed outer custody, all three manifests, semantic reconciliation, claim reconciliation, and private-content scan.",
                "evidence_paths": evidence,
                "evidence_sha256s": hashes,
                "transition_commit": INGEST_COMMIT,
                "reopen_condition": ["independently verified custody or reconciliation defect"],
            }
        )
    ledger["goal_count"] = len(ledger["goals"])
    ledger.setdefault("batch_output_links", {})["Batch101"] = OUTPUT.relative_to(ROOT).as_posix()
    ledger["last_updated_batch"] = "Batch101"
    ledger["last_updated_commit"] = INGEST_COMMIT
    ledger["last_updated_timestamp"] = STAMP
    LEDGER.write_text(json.dumps(ledger, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({"status": "PASS", "goal_count": len(ledger["goals"]), "transition_count": len(ledger["supersession_receipts"]), "ledger_sha256": sha256_file(LEDGER)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
