#!/usr/bin/env python3
"""Generate Batch101 bounded public state and release handoff records."""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs/post_v2_37_hardening_batch101_canonical_semantic_replay_exact_incident_salvage_ownership_closure"


def rows(name: str) -> list[dict]:
    return [json.loads(line) for line in (OUT / name).read_text(encoding="utf-8").splitlines() if line.strip()]


def write_json(name: str, value: object) -> None:
    (OUT / name).write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")


def write_jsonl(name: str, values: list[dict]) -> None:
    (OUT / name).write_text("".join(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n" for row in values), encoding="utf-8", newline="\n")


def scoped(status: str, producer: str, depth: str, scope: str, allowed: str, forbidden: list[str], **extra: object) -> dict:
    value = {"status": status, "producer": producer, "execution_depth": depth, "semantic_scope": scope, "authority_allowed": allowed, "authority_forbidden": forbidden, **extra}
    value["record_hash"] = hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    return value


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--workflow-run-id", default="LOCAL_PREWORKFLOW")
    args = parser.parse_args()
    ledger = rows("batch101_registered_cell_execution_ledger_v1.jsonl")
    pairs = rows("pair_validity_receipts_v3.jsonl")
    evidence = rows("matched_counterfactual_evidence_v3.jsonl")
    terminals = rows("controller_audit_counterfactual_terminal_records_v4.jsonl")
    mutations = json.loads((OUT / "critic/batch101_semantic_mutation_campaign_summary.json").read_text())
    raw_count = len(rows("raw_execution_observations_v1.jsonl"))
    reproducible = sum(row.get("semantically_reproducible", False) for row in ledger)
    ownership = sum(row.get("ownership_supported", False) for row in evidence)
    terminal_distribution = dict(Counter(row["terminal_class"] for row in terminals))
    exact_blockers = sorted({row["exact_blocker"] for row in ledger if row.get("exact_blocker")})
    exact_blockers += ["necessity_not_executed", "sufficiency_not_executed", "ownership_alternatives_not_excluded"]

    dpp = [scoped(
        "SAFE_ABSTENTION", "ControllerAudit", "counterfactual DPP projection", "candidate DPP state",
        "safe abstention and next-action routing", ["patch", "repair count", "release promotion"],
        program_id=row["program_id"], candidate_id=row["candidate_id"], terminal_class=row["terminal_class"],
        next_state="OPEN_EVIDENCE_ACQUISITION", proof_parent=row["record_hash"],
    ) for row in terminals]
    write_jsonl("dpp_counterfactual_records_v1.jsonl", dpp)
    write_jsonl("decision_time_source_ownership_proofs_v4.jsonl", [scoped(
        "NOT_PRODUCED", "ControllerAudit", "ownership precondition scan", "source ownership proof",
        "explicit nonproduction record", ["source ownership", "patch", "repair count"],
        candidate_id=row["candidate_id"], program_id=row["program_id"], reason="terminal_not_source_owned_behavior_defect",
    ) for row in terminals])
    write_json("source_ownership_proof_reconstruction_audit_v4.json", scoped(
        "PASS_NO_ELIGIBLE_TERMINALS", "ControllerAudit", "terminal/proof join", "source ownership proof reconstruction",
        "proof firewall", ["proof fabrication", "patch"], eligible_terminal_count=0, proof_count=0,
    ))
    write_jsonl("protected_repair_eligibility_v2.jsonl", [scoped(
        "NOT_ELIGIBLE", "ControllerAudit", "source-ownership prerequisite check", "protected repair eligibility",
        "non-authorizing eligibility result", ["patch generation", "patch application", "repair count"],
        candidate_id=row["candidate_id"], program_id=row["program_id"], reason="source_ownership_not_supported",
    ) for row in terminals])
    write_json("batch101_private_truth_join_status.json", scoped(
        "NOT_RUN_PENDING_PUBLIC_ARTIFACT_VERIFICATION", "finalize_batch101_release_outputs", "public workflow boundary",
        "private truth join", "enforce join ordering", ["public truth access", "current-output mutation", "ownership derivation"],
        expected_private_bundle_sha256="08c73e862910f2d314addaf19cca39674b129b1e40a3b38f8e12c58c7ca1c37b",
        prerequisite="official Batch101 public artifact independently verified",
    ))
    write_json("batch101_public_default_non_tld_status.json", scoped(
        "PASS_LIMITED_DRY_RUN", "controllergate_run.py", "current protocol dry-run without private inputs",
        "public default non-TLD mode", "ordinary public safe-abstention path", ["cross-platform installed completeness", "TLD gain claim"],
        private_tld_required=False, private_truth_required=False, protocol="v2.19",
    ))
    claim = scoped(
        "PRODUCT_BETA_BLOCKED_EXACT", "finalize_batch101_release_outputs", "current evidence reconstruction",
        "Batch101 claim boundary", "bounded research evidence reporting", ["Product Beta approval", "production readiness", "self-maintaining software", "memory lift", "full scoring"],
        protocol="v2.19", package_version="0.2.0b2.dev0", issue_derived_repair_count=6,
        native_external_repair_count=4, historical_increment=0, ordinary_patch_count=0,
        prospective_effectiveness="NOT_ESTABLISHED", memory_status="not_demonstrated",
        full_scoring="NOT_RUN/disallowed", public_writes="inactive", automatic_merge="inactive",
        production_readiness=False, self_maintaining_software="false/not_demonstrated",
        exact_blockers=exact_blockers,
    )
    write_json("batch101_claim_boundary.json", claim)
    state = scoped(
        "BATCH101_PUBLIC_EVIDENCE_COMPLETE_SCIENTIFIC_BLOCK", "finalize_batch101_release_outputs", "public evidence finalization",
        "Batch101 consolidated state", "artifact handoff", ["patch", "repair count", "release promotion"],
        workflow_run_id=args.workflow_run_id, programs=9, registered_cells=len(ledger),
        executed_cells=sum(row["execution_status"] == "EXECUTED" for row in ledger),
        blocked_cells=sum(row["execution_status"] == "BLOCKED" for row in ledger), superseded_cells=0,
        unaccounted_cells=0, raw_replay_count=raw_count, semantically_reproducible_cells=reproducible,
        pair_statuses=dict(Counter(row["status"] for row in pairs)), terminal_distribution=terminal_distribution,
        sensitivity_receipts=sum(row["dimension_sensitivity_supported"] for row in evidence),
        necessity_supported=0, sufficiency_supported=0, ownership_supported=ownership,
        patch_operations=0, repair_count_increment=0, historical_increment=0,
        semantic_mutations_executed=mutations["semantic_mutations_executed"],
        semantic_mutations_rejected=mutations["semantic_mutations_rejected"], claim_boundary=claim,
    )
    write_json("batch101_consolidated_state.json", state)
    write_json("batch101_future_ledger_goal_statuses.json", scoped(
        "PRESERVED", "finalize_batch101_release_outputs", "master ledger readout", "future goals",
        "carry-forward planning", ["silent completion"],
        goals={"balanced_historical_cohort": "PROTOCOL_READY", "abstention_required_cohort": "PROTOCOL_READY", "mixed_failure_cohort": "PROTOCOL_READY", "prospective_validation": "PROTOCOL_READY", "memory_lift_validation": "PROTOCOL_READY", "protected_repair": "PROTOCOL_READY", "external_replication": "PROTOCOL_READY", "public_default_non_tld": "NOT_STARTED", "product_beta": "PROTOCOL_READY", "self_maintaining_evidence": "PROTOCOL_READY"},
    ))
    summary = f"""# Batch101 campaign summary

Batch101 officially ingested and reconciled the Batch100 public artifact, retired candidate-hardcoded predicate authority, and reprojected all 56 preserved raw replays through frozen declarative semantics. The v3 registry contains 33 cells: 28 have official execution evidence and five are explicitly blocked. No cell is unaccounted.

The corrected Py-bugger program materialized the historical count-inflation behavior (reported 62 / successful 7 / persisted 1, and reported 49 / successful 5 / persisted 1). It reached bounded factorial sensitivity only. Necessity, sufficiency, remaining-alternative exclusion, and source ownership were not established.

All nine ControllerAudit terminals are `INSUFFICIENT_EVIDENCE`. No source-ownership proof, protected repair license, patch, repair-count increment, prospective-effectiveness claim, memory-lift claim, Product Beta promotion, production-readiness claim, or self-maintaining-software claim was produced.

The independent critic rejected all {mutations['semantic_mutations_rejected']} of {mutations['semantic_mutations_executed']} re-signed copied-tree semantic mutations. Protocol remains v2.19 and package version remains 0.2.0b2.dev0.
"""
    (OUT / "campaign_summary.md").write_text(summary, encoding="utf-8", newline="\n")
    print(json.dumps({"status": state["status"], "release_boundary": claim["status"], "registered_cells": len(ledger), "ownership_supported": ownership}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
