"""Build Batch100 protocol-ready records and synchronize the permanent goal ledger."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs/post_v2_37_hardening_batch100_matched_counterfactual_execution_causal_ownership_architecture_gain_master_roadmap_lock"
LEDGER = ROOT / "configs/controllergate_master_completion_ledger_v2.json"
FORBIDDEN = ["validation completion", "repair authority", "repair count mutation", "release promotion"]


PROTOCOLS = {
    "historical_cohort_expansion_protocol_v1.json": {
        "goal_id": "CG-GOAL-011-BALANCED-HISTORICAL-COHORT",
        "requirements": ["at least 24 total episodes", "multiple repositories per causal class", "multiple providers", "multiple operating systems where relevant", "negative controls", "unresolved cases", "no single class dominating", "selection frozen before outcome evaluation"],
        "blockers": ["historical_cohort_below_24_episodes"],
    },
    "abstention_required_cohort_protocol_v1.json": {
        "goal_id": "CG-GOAL-012-ABSTENTION-REQUIRED-COHORT",
        "requirements": ["genuine cases where unique causal ownership is not supportable", "no manufactured abstention labels"],
        "blockers": ["abstention_required_cohort_missing"],
    },
    "mixed_failure_cohort_protocol_v1.json": {
        "goal_id": "CG-GOAL-013-MIXED-FAILURE-COHORT",
        "requirements": ["preregistered factorial interactions", "multiple contacts do not imply mixed failure"],
        "blockers": ["preregistered_mixed_failure_cohort_missing"],
    },
    "prospective_validation_protocol_v1.json": {
        "goal_id": "CG-GOAL-014-PROSPECTIVE-VALIDATION",
        "requirements": ["fresh issues", "candidate freeze before diagnosis", "no future fix access", "sealed truth", "preregistered budgets", "independent review", "held-out evaluation"],
        "blockers": ["prospective_held_out_validation_not_run"],
    },
    "memory_lift_validation_protocol_v1.json": {
        "goal_id": "CG-GOAL-015-MEMORY-LIFT-VALIDATION",
        "requirements": ["matched memory/no-memory planners", "same evidence", "same budget", "fresh candidates", "irrelevant-memory control", "shuffled-memory control", "leakage control"],
        "blockers": ["memory_lift_not_demonstrated"],
    },
    "protected_repair_protocol_v1.json": {
        "goal_id": "CG-GOAL-016-PROTECTED-REPAIR-ACTUATION",
        "requirements": ["source-owned terminal", "human authorization", "source-only patch", "no test mutation", "target validation", "regression validation", "clean replay", "rollback", "external review"],
        "blockers": ["protected_repair_prerequisites_not_met"],
    },
    "external_replication_protocol_v1.json": {
        "goal_id": "CG-GOAL-017-EXTERNAL-REPLICATION",
        "requirements": ["outside operator or clean independent environment", "reproduce custody", "reproduce typed incident", "reproduce matched intervention", "reproduce terminal", "reproduce scores"],
        "blockers": ["external_replication_not_run"],
    },
    "product_beta_exit_criteria_v1.json": {
        "goal_id": "CG-GOAL-019-PRODUCT-BETA",
        "requirements": ["ordinary public non-TLD default mode", "stable install", "quick start", "supported-project boundaries", "clear abstention reports", "schema stability", "security review", "external replication", "prospective effectiveness", "no private-corpus dependency"],
        "blockers": ["prospective_effectiveness_not_established", "external_replication_not_run", "product_beta_exit_criteria_not_met"],
    },
    "self_maintaining_software_evidence_protocol_v1.json": {
        "goal_id": "CG-GOAL-020-SELF-MAINTAINING-SOFTWARE-EVIDENCE",
        "requirements": ["safe update discovery", "causal diagnosis", "repair proposal", "authorization separation", "validation", "rollback", "drift monitoring", "memory integrity", "long-horizon maintenance"],
        "blockers": ["self_maintaining_software_not_demonstrated"],
    },
}


def canonical_hash(value: object) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")


def main() -> int:
    protocol_index = []
    for filename, definition in PROTOCOLS.items():
        record = {
            "protocol_id": filename.removesuffix(".json"),
            "protocol_version": "v1",
            "status": "PROTOCOL_READY",
            "goal_id": definition["goal_id"],
            "requirements": definition["requirements"],
            "active_blockers": definition["blockers"],
            "completion_rule": "all requirements must be evidenced by independent executed receipts",
            "authority_allowed": ["preregistration", "future evidence planning", "audit enforcement"],
            "authority_forbidden": FORBIDDEN,
            "producer": "scripts/build_batch100_future_protocols.py",
            "execution_depth": "schema and blocker implementation",
            "semantic_scope": "future ControllerGate validation protocol",
        }
        record["protocol_hash"] = canonical_hash(record)
        path = ROOT / "configs" / filename
        write_json(path, record)
        protocol_index.append({"path": str(path.relative_to(ROOT)).replace("\\", "/"), "goal_id": definition["goal_id"], "status": "PROTOCOL_READY", "sha256": hashlib.sha256(path.read_bytes()).hexdigest()})

    ledger = json.loads(LEDGER.read_text(encoding="utf-8"))
    by_goal = {row["goal_id"]: row for row in ledger["goals"]}
    for filename, definition in PROTOCOLS.items():
        goal = by_goal[definition["goal_id"]]
        rel = f"configs/{filename}"
        path = ROOT / rel
        goal["status"] = "PROTOCOL_READY"
        goal["current_evidence"] = sorted(set([*goal.get("current_evidence", []), rel]))
        goal.setdefault("evidence_hashes", {})[rel] = hashlib.sha256(path.read_bytes()).hexdigest()
        goal["active_blockers"] = definition["blockers"]
        goal["last_updated_commit"] = "BATCH100_IMPLEMENTATION_PENDING"
        goal["last_updated_timestamp"] = "2026-07-19T00:00:00Z"

    evidence_updates = {
        "CG-GOAL-005-INCIDENT-IDENTITY-AND-PARITY": [
            "configs/batch100_incident_identity_registry_v2.jsonl",
            "configs/batch100_incident_provider_registry_v2.jsonl",
            "configs/batch100_candidate_contract_supersession_registry_v1.jsonl",
        ],
        "CG-GOAL-006-TYPED-INCIDENT-REMATERIALIZATION": ["configs/batch100_candidate_counterfactual_programs_v2.jsonl"],
        "CG-GOAL-007-MATCHED-COUNTERFACTUAL-EXECUTION": ["configs/batch100_counterfactual_cell_registry_v2.jsonl"],
        "CG-GOAL-010-TLD-ROUTING-GAIN": ["configs/batch100_opaque_tld_ordering_registry_v1.jsonl"],
    }
    for goal_id, paths in evidence_updates.items():
        goal = by_goal[goal_id]
        goal["status"] = "IN_PROGRESS"
        goal["current_evidence"] = sorted(set([*goal.get("current_evidence", []), *paths]))
        for rel in paths:
            goal.setdefault("evidence_hashes", {})[rel] = hashlib.sha256((ROOT / rel).read_bytes()).hexdigest()
        goal["last_updated_commit"] = "BATCH100_IMPLEMENTATION_PENDING"
        goal["last_updated_timestamp"] = "2026-07-19T00:00:00Z"
    by_goal["CG-GOAL-005-INCIDENT-IDENTITY-AND-PARITY"]["active_blockers"] = ["exact_incident_provider_parity_limited_for_registered_candidates"]
    by_goal["CG-GOAL-006-TYPED-INCIDENT-REMATERIALIZATION"]["active_blockers"] = ["typed_incident_workflow_execution_pending"]
    by_goal["CG-GOAL-007-MATCHED-COUNTERFACTUAL-EXECUTION"]["active_blockers"] = ["public_counterfactual_workflow_execution_pending"]
    by_goal["CG-GOAL-010-TLD-ROUTING-GAIN"]["active_blockers"] = ["private_truth_calibration_pending"]
    ledger["last_updated_batch"] = "Batch100"
    ledger["last_updated_timestamp"] = "2026-07-19T00:00:00Z"
    ledger["goal_count"] = len(ledger["goals"])
    write_json(LEDGER, ledger)
    write_json(OUT / "future_protocol_readiness.json", {
        "status": "PASS_PROTOCOLS_READY_VALIDATION_NOT_COMPLETE",
        "protocols": protocol_index,
        "protocol_ready_count": len(protocol_index),
        "validation_complete_count": 0,
        "authority_allowed": "future protocol enforcement",
        "authority_forbidden": FORBIDDEN,
        "producer": "scripts/build_batch100_future_protocols.py",
        "execution_depth": "generated protocol records and synchronized ledger",
        "semantic_scope": "Batch100 future-goal retention",
    })
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
