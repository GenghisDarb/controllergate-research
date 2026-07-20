"""Append Batch103 goals 026-033 to the persistent completion ledger."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
LEDGER = ROOT / "configs/controllergate_master_completion_ledger_v2.json"
OUT = ROOT / "outputs/post_v2_37_hardening_batch103_reactome_isomorphism_causal_planning_gain_exact_materialization"
INGEST_COMMIT = "ba8631281b75bff89a6b881fb19c0a972a4c8bfb"
FREEZE_COMMIT = "261fd73e"
STAMP = "2026-07-20T23:00:00Z"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def rel(name: str) -> str:
    return (OUT / name).relative_to(ROOT).as_posix()


def goal(
    goal_id: str,
    title: str,
    status: str,
    prerequisites: list[str],
    required_evidence: list[str],
    evidence_names: list[str],
    blockers: list[str],
    *,
    complete: bool = False,
) -> dict:
    evidence = [rel(name) for name in evidence_names]
    return {
        "goal_id": goal_id,
        "title": title,
        "status": status,
        "prerequisites": prerequisites,
        "required_evidence": required_evidence,
        "current_evidence": evidence,
        "evidence_hashes": {path: sha256(ROOT / path) for path in evidence},
        "completion_commit": INGEST_COMMIT if complete else None,
        "completion_batch": "Batch103" if complete else None,
        "active_blockers": blockers,
        "reopen_conditions": ["independently verified custody, grounding, execution, or claim-boundary defect"],
        "authority_allowed": ["evidence acquisition", "nonauthorizing structural and causal evaluation"],
        "authority_forbidden": ["candidate patch", "repair count mutation", "historical rewrite", "release promotion"],
        "last_updated_commit": FREEZE_COMMIT,
        "last_updated_timestamp": STAMP,
    }


def main() -> int:
    ledger = json.loads(LEDGER.read_text(encoding="utf-8"))
    additions = [
        goal(
            "CG-GOAL-026-OFFICIAL-BATCH102-INGEST",
            "Official Batch102 artifact ingest",
            "COMPLETE",
            ["CG-GOAL-025-REAL-ARCHITECTURE-ARM-EVALUATION"],
            ["exact outer ZIP custody", "139-entry manifest verification", "semantic reconciliation"],
            [
                "batch102_official_ingest/artifact_identity/batch102_official_outer_artifact_custody.json",
                "batch102_official_ingest/custody/batch102_official_manifest_verification.json",
                "batch102_official_ingest/reconciliation/batch102_official_semantic_reconciliation.json",
                "batch102_official_ingest/ingest_receipts/batch102_official_ingest_receipt.json",
            ],
            [],
            complete=True,
        ),
        goal(
            "CG-GOAL-027-CANONICAL-ISOMORPHISM-RECONCILIATION",
            "Canonical isomorphism reconciliation",
            "IN_PROGRESS",
            ["CG-GOAL-026-OFFICIAL-BATCH102-INGEST"],
            ["full registry audit", "current-authority errata pass", "terminology preservation"],
            [
                "canonical_isomorphism_errata_lock_v3.json",
                "canonical_isomorphism_stack_v3_audit.json",
                "brot_tot_brot_tot_bulb_terminology_audit_v2.json",
            ],
            ["external architecture validation not performed", "cross-source semantic equivalence remains bounded"],
        ),
        goal(
            "CG-GOAL-028-REACTOME-RPIR-SOURCE-GROUNDING",
            "Reactome RPIR source grounding",
            "IN_PROGRESS",
            ["CG-GOAL-027-CANONICAL-ISOMORPHISM-RECONCILIATION"],
            ["all source chapters", "all pathways and reactions", "field origin classification", "zero claim-bearing defaults"],
            [
                "reactome_mapping_completeness_v2.json",
                "reactome_default_value_audit_v1.json",
                "reactome_cross_chapter_fallback_audit_v1.json",
                "batch103_reactome_structural_closure_summary.json",
            ],
            ["semantic grounding is structural, not causal planning gain", "external replication not performed"],
        ),
        goal(
            "CG-GOAL-029-REACTOME-EXECUTABLE-MAINTENANCE-MAPPING",
            "Reactome executable maintenance mapping",
            "IN_PROGRESS",
            ["CG-GOAL-028-REACTOME-RPIR-SOURCE-GROUNDING"],
            ["reaction-specific operations", "independent verification", "nonauthorizing shadow boundary"],
            [
                "single_plan_maturation_retirement_audit.json",
                "legacy_round_robin_authority_retirement_audit.json",
                "reactome_completion_status_v1.json",
            ],
            ["shadow execution remains nonauthorizing", "causal gain ablation not yet joined"],
        ),
        goal(
            "CG-GOAL-030-REACTOME-CAUSAL-PLANNING-GAIN",
            "Reactome causal planning gain",
            "IN_PROGRESS",
            ["CG-GOAL-029-REACTOME-EXECUTABLE-MAINTENANCE-MAPPING"],
            ["frozen matched ablation", "fresh candidate outcomes", "private post-terminal false-attribution evaluation"],
            [
                "batch103_planner_contract_freeze_receipt_v1.json",
                "reactome_planner_outcome_vault_registry_v1.json",
            ],
            ["fresh Batch103 workflow execution pending", "private truth join pending", "R4 not established"],
        ),
        goal(
            "CG-GOAL-031-REACTOME-CROSS-CANDIDATE-GENERALIZATION",
            "Reactome cross-candidate generalization",
            "NOT_STARTED",
            ["CG-GOAL-030-REACTOME-CAUSAL-PLANNING-GAIN"],
            ["replication on three candidates", "two causal families", "multiple repository/provider classes"],
            ["reactome_completion_status_v1.json"],
            ["R4 local gain not established", "R5 replication campaign not run"],
        ),
        goal(
            "CG-GOAL-032-ISOMORPHIC-ARCHITECTURE-EXTERNAL-VALIDATION",
            "Isomorphic architecture external validation",
            "NOT_STARTED",
            ["CG-GOAL-031-REACTOME-CROSS-CANDIDATE-GENERALIZATION"],
            ["independent external study", "preregistered architecture comparison"],
            ["reactome_completion_status_v1.json"],
            ["no independent external validation study has been run"],
        ),
        goal(
            "CG-GOAL-033-REACTOME-PROSPECTIVE-VALIDATION",
            "Reactome prospective validation",
            "NOT_STARTED",
            ["CG-GOAL-032-ISOMORPHIC-ARCHITECTURE-EXTERNAL-VALIDATION"],
            ["future preregistered held-out prospective campaign"],
            ["reactome_completion_status_v1.json"],
            ["R6 requires a future held-out campaign", "prospective effectiveness remains not established"],
        ),
    ]
    existing = {row["goal_id"]: index for index, row in enumerate(ledger["goals"])}
    for row in additions:
        if row["goal_id"] not in existing:
            ledger["goals"].append(row)
        else:
            ledger["goals"][existing[row["goal_id"]]] = row
    transitions = {row["transition_id"] for row in ledger.get("supersession_receipts", [])}
    for row in additions:
        transition_id = f"batch103:{row['goal_id']}:initial-registration"
        if transition_id not in transitions:
            ledger.setdefault("supersession_receipts", []).append(
                {
                    "transition_id": transition_id,
                    "goal_id": row["goal_id"],
                    "previous_status": None,
                    "new_status": row["status"],
                    "transition_reason": "Batch103 append-only goal registration at the pre-outcome contract boundary.",
                    "evidence_paths": row["current_evidence"],
                    "evidence_sha256s": row["evidence_hashes"],
                    "transition_commit": FREEZE_COMMIT,
                    "active_blockers": row["active_blockers"],
                    "reopen_conditions": row["reopen_conditions"],
                    "authority_allowed": ["append-only completion-ledger expansion"],
                    "authority_forbidden": ["historical rewrite", "silent blocker removal", "completion without evidence"],
                }
            )
        else:
            transition = next(
                value for value in ledger["supersession_receipts"]
                if value["transition_id"] == transition_id
            )
            transition["evidence_paths"] = row["current_evidence"]
            transition["evidence_sha256s"] = row["evidence_hashes"]
            transition["active_blockers"] = row["active_blockers"]
    ledger["goal_count"] = len(ledger["goals"])
    ledger.setdefault("batch_output_links", {})["Batch103"] = OUT.relative_to(ROOT).as_posix()
    ledger["last_updated_batch"] = "Batch103"
    ledger["last_updated_commit"] = FREEZE_COMMIT
    ledger["last_updated_timestamp"] = STAMP
    LEDGER.write_text(json.dumps(ledger, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({"status": "PASS", "goal_count": len(ledger["goals"]), "ledger_sha256": sha256(LEDGER)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
