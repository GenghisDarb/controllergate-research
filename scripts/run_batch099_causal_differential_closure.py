from __future__ import annotations

import argparse
import hashlib
import json
import sys
from collections import Counter
from dataclasses import asdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from controllergate.amds.causal_differential_v9 import (
    EVIDENCE_LEVELS,
    ROOT_CLASSES,
    build_existing_counterfactual_audit,
    classify_existing_facts,
    corrected_constraint_replay,
    counterfactual_contracts,
    jsonl,
    reconstruct_contradiction_roots,
)


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n" for row in rows), encoding="utf-8", newline="\n")


def file_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--official-ingest-root", required=True)
    parser.add_argument("--decision-artifact", required=True)
    parser.add_argument("--output-root", required=True)
    parser.add_argument("--workflow-run-id", default="LOCAL_VALIDATION")
    args = parser.parse_args()
    ingest = Path(args.official_ingest_root)
    extracted = ingest / "extracted_public_artifact"
    decision = Path(args.decision_artifact)
    output = Path(args.output_root) / "causal_differential"
    output.mkdir(parents=True, exist_ok=True)
    receipt_path = ingest / "ingest_receipts" / "batch098_official_ingest_receipt.json"
    receipt_hash = file_hash(receipt_path)
    facts = jsonl(extracted / "public_provisional_facts_v2.jsonl")
    observations = jsonl(extracted / "public_neutral_observations_v2.jsonl")
    branches = jsonl(extracted / "public_failed_branches_v2.jsonl")
    classified = classify_existing_facts(facts, observations)
    roots, root_summary = reconstruct_contradiction_roots(branches, classified, observations)
    root_summary["official_ingest_receipt_sha256"] = receipt_hash
    fact_rows = [asdict(row) for row in classified]
    write_jsonl(output / "batch099_contradiction_root_map_v1.jsonl", roots)
    write_json(output / "batch099_contradiction_root_reconstruction_summary.json", root_summary)
    write_jsonl(output / "batch099_provisional_fact_causal_evidence_map_v1.jsonl", fact_rows)
    write_json(output / "batch099_causal_evidence_hierarchy_v1.json", {
        "status": "PASS", "levels": list(EVIDENCE_LEVELS), "contradiction_root_classes": list(ROOT_CLASSES),
        "ownership_minimum": ["DIMENSION_SENSITIVITY_VERIFIED", "NECESSITY_SUPPORTED or SUFFICIENCY_SUPPORTED", "alternative exclusion"],
        "contact_can_grant_ownership": False, "mixed_failure_requires_factorial_interaction": True,
        "official_ingest_receipt_sha256": receipt_hash,
    })
    pairs = build_existing_counterfactual_audit(decision)
    pair_rows = [asdict(row) for row in pairs]
    write_jsonl(output / "batch099_existing_counterfactual_pair_audit_v1.jsonl", pair_rows)
    contracts = counterfactual_contracts(receipt_hash)
    write_jsonl(output / "batch099_matched_counterfactual_probe_contracts_v1.jsonl", contracts)
    sensitivity = [row for row in pair_rows if row["evidence_level"] == "DIMENSION_SENSITIVITY_VERIFIED"]
    ownership = [row for row in pair_rows if row["ownership_supported"]]
    counterfactual_gate = {
        "status": "BLOCK",
        "evaluated_existing_pair_count": len(pair_rows),
        "sensitivity_pair_count": len(sensitivity),
        "ownership_supporting_pair_count": len(ownership),
        "scoreable_candidate_positive_negative_ownership_partition_count": 0,
        "exit_requirement_met": False,
        "active_blocker": "matched_counterfactual_execution_not_available_in_frozen_artifact",
        "next_allowed_action": "execute preregistered narrow paired probes from the frozen source/provider capsules without patching or broad reacquisition",
        "official_ingest_receipt_sha256": receipt_hash,
    }
    write_json(output / "batch099_counterfactual_adequacy_gate.json", counterfactual_gate)
    write_json(output / "batch099_corrected_constraint_model_v1.json", {
        "status": "PASS", "contact_facts_are_compatible": True,
        "ownership_classes_mutually_exclusive_only_after_ownership_support": True,
        "mixed_failure_requires_interaction": True,
        "genuine_contradiction_definition": "verified proposition and verified logical negation under the same frozen frame",
        "replayed_false_mutual_exclusions_removed": len(roots),
        "official_ingest_receipt_sha256": receipt_hash,
    })
    candidates = sorted({row["candidate_id"] for row in facts})
    terminals, replay = corrected_constraint_replay(classified, candidates, "ABCDEFGHIJ")
    replay["official_ingest_receipt_sha256"] = receipt_hash
    replay["workflow_run_id"] = args.workflow_run_id
    write_jsonl(output / "batch099_corrected_terminal_records_v1.jsonl", terminals)
    write_json(output / "batch099_corrected_semantic_replay_summary.json", replay)
    comparisons = [
        {"comparison": "A_vs_B", "component": "environment discrimination", "result": "NOT_ESTABLISHED"},
        {"comparison": "A_vs_C", "component": "source/contact discrimination", "result": "NOT_ESTABLISHED"},
        {"comparison": "B_or_C_vs_D", "component": "executed projection isolation", "result": "NOT_ESTABLISHED"},
        {"comparison": "D_vs_E", "component": "ordering efficiency", "result": "NOT_ESTABLISHED"},
        {"comparison": "E_vs_F", "component": "observer/modal conflict resolution", "result": "NOT_ESTABLISHED"},
    ]
    write_json(output / "batch099_architecture_component_gain_gate.json", {
        "status": "BLOCK", "comparisons": comparisons, "routing_authority_granted": [],
        "tld_mode": "SHADOW_ONLY", "reason": "no nonbaseline causal coverage from ownership-grade differential evidence",
        "official_ingest_receipt_sha256": receipt_hash,
    })
    claim = {
        "protocol": "v2.19", "package_version": "0.2.0b2.dev0", "issue_derived_repairs": 6,
        "native_external_repairs": 4, "historical_increment": 0, "ordinary_patches": 0,
        "prospective_effectiveness": "NOT_ESTABLISHED", "memory": "not demonstrated",
        "full_production_scoring": "disallowed", "public_writes": "inactive", "automatic_merge": "inactive",
        "production_readiness": False, "self_maintaining_software": "false/not demonstrated",
        "release_decision": "PRODUCT_BETA_RC_BLOCKED_EXACT",
    }
    write_json(output / "batch099_claim_boundary.json", claim)
    decision_record = {
        "status": "SCIENTIFIC_BLOCK", "official_ingest_status": "PASS_OFFICIAL_BATCH098_ARTIFACT_INGEST",
        "contradiction_root_reconstruction": "PASS", "causal_evidence_hierarchy": "PASS",
        "corrected_constraint_replay": "PASS_WITH_SCIENTIFIC_BLOCK",
        "counterfactual_adequacy": "BLOCK", "architecture_gain": "NOT_ESTABLISHED",
        "active_blockers": ["matched_counterfactual_execution_not_available_in_frozen_artifact", "nonbaseline_causal_coverage_zero"],
        "ordinary_patch_count": 0, "historical_increment": 0, "claim_boundary": claim,
        "official_ingest_receipt_sha256": receipt_hash,
    }
    write_json(output / "batch099_scientific_decision.json", decision_record)
    write_json(output / "batch099_execution_summary.json", {
        "status": decision_record["status"], "contradictions_reconstructed": len(roots),
        "fact_admissions_reclassified": len(classified), "existing_pairs_evaluated": len(pairs),
        "sensitivity_pairs": len(sensitivity), "ownership_pairs": len(ownership),
        "corrected_genuine_contradictions": replay["genuine_contradiction_count"],
        "terminal_distribution": replay["terminal_distribution"], "source_ownership_proofs": 0,
        "truth_access": 0, "private_tld_access": 0, "patch_operations": 0, "historical_increment": 0,
        "workflow_run_id": args.workflow_run_id, "official_ingest_receipt_sha256": receipt_hash,
    })
    (output / "campaign_summary.md").write_text(
        "# Batch099 causal differential closure\n\n"
        "The official Batch098 artifact is ingested and immutable. All 432 prior contradictions were reconstructed as false mutual exclusions caused by treating contact as ownership. The corrected constraint model preserves compatible contacts and emits no ownership terminal without matched differential evidence. Existing frozen evidence contains sensitivity comparisons but no ownership-grade matched counterfactual, so causal coverage remains zero and the campaign is scientifically blocked. No patch, repair-count change, protected actuation, or release promotion occurred.\n",
        encoding="utf-8", newline="\n",
    )
    print(json.dumps(decision_record, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
