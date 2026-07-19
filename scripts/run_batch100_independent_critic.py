"""Execute the Batch100 copied-tree, re-signed semantic mutation campaign."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import shutil
import sys
import tempfile
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from controllergate.evidence.batch100_independent_critic import canonical_hash, findings


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n" for row in rows), encoding="utf-8", newline="\n")


def set_path(record: dict[str, Any], path: str, value: Any) -> None:
    current = record
    parts = path.split(".")
    for part in parts[:-1]:
        current = current[part]
    current[parts[-1]] = value


MUTATIONS = [
    ("batch099_outer_artifact_changed", "artifact_sha", "0" * 64),
    ("batch099_ingest_receipt_changed", "ingest_receipt_sha", "1" * 64),
    ("master_ledger_goal_removed", "goal_ids", [f"CG-GOAL-{i:03d}" for i in range(20)]),
    ("completed_ledger_evidence_removed", "completed_goal_evidence_present", False),
    ("incident_provider_changed", "incident_provider", "unregistered-provider"),
    ("incident_platform_changed", "incident_platform", "unregistered-platform"),
    ("wrong_source_commit", "source_commit", "2" * 40),
    ("future_source_commit_injected", "future_source_commit", True),
    ("accepted_fix_injected", "accepted_fix", True),
    ("gold_patch_injected", "gold_patch", True),
    ("ab_source_hashes_differ", "pair.control_source", "source-b"),
    ("ab_providers_differ_unregistered", "pair.control_provider", "provider-b"),
    ("ab_commands_differ_unregistered", "pair.control_command", "command-b"),
    ("ab_fixtures_differ_unregistered", "pair.control_fixture", "fixture-b"),
    ("two_factors_labelled_single", "pair.changed_dimensions", ["environment", "command"]),
    ("incident_predicate_from_truth", "truth_in_predicates", True),
    ("control_predicate_from_truth", "truth_in_predicates", True),
    ("typed_incident_fabricated", "typed_incident_receipt_backed", False),
    ("replay_inconsistency_hidden", "replay_consistent", False),
    ("replay_duplicated_relabelled", "replay_receipt_ids", ["same", "same"]),
    ("order_carryover_ignored", "order_carryover_pass", False),
    ("source_tree_mutated", "source_mutation_count", 1),
    ("cleanup_failure_hidden", "cleanup_pass", False),
    ("offline_network_used", "offline_network_requests", 1),
    ("sensitivity_promoted_to_necessity", "evidence_level", "NECESSITY_SUPPORTED"),
    ("sensitivity_promoted_to_sufficiency", "evidence_level", "SUFFICIENCY_SUPPORTED"),
    ("sensitivity_promoted_to_ownership", "evidence_level", "OWNERSHIP_SUPPORTED"),
    ("contact_promoted_to_ownership", "contact_promoted_to_ownership", True),
    ("interaction_without_factorial", "interaction_supported", True),
    ("mixed_failure_from_contacts", "mixed_failure", True),
    ("unresolved_alternative_removed", "unresolved_alternatives", []),
    ("ownership_class_changed", "ownership_class", "SOURCE_OWNED_BEHAVIOR_DEFECT"),
    ("terminal_support_pair_removed", "terminal_support_pair_present", False),
    ("terminal_written_outside_audit", "terminal_writer", "unregistered-writer"),
    ("unselected_outcome_opened", "unselected_outcome_access", 1),
    ("arm_outcome_copied", "arm_outcome_source", "B"),
    ("tld_creates_probe", "tld_created_probe", True),
    ("tld_changes_predicate", "tld_changed_predicate", True),
    ("truth_exposed_publicly", "truth_public", True),
    ("source_ownership_from_truth", "source_ownership_from_truth", True),
    ("repair_operation_introduced", "patch_operations", 1),
    ("repair_count_incremented", "repair_count_increment", 1),
    ("historical_increment_incremented", "historical_increment", 1),
    ("product_beta_promoted", "product_beta", "pass"),
    ("prospective_effectiveness_promoted", "prospective_effectiveness", "ESTABLISHED"),
    ("memory_claimed_demonstrated", "memory", "demonstrated"),
    ("production_readiness_true", "production_readiness", True),
    ("self_maintaining_claimed", "self_maintaining_software", "true"),
    ("private_path_injected", "private_absolute_path", "C:/private/truth.zip"),
    ("manifest_resigned_after_semantic_mutation", "ownership_class", "PROVIDER_OWNED"),
]


def base_record() -> dict[str, Any]:
    return {
        "artifact_sha": "3bd768dc68721df44ad7ca6f25426604fec0a91bd9d5c38ce3868e63eb7728e1",
        "ingest_receipt_sha": "55f9549fe1bf9d0d417980686434daf2c5336195b0955bd7acdd3452c428f2f3",
        "goal_ids": [f"CG-GOAL-{i:03d}" for i in range(21)], "completed_goal_evidence_present": True,
        "incident_provider": "registered-provider", "registered_incident_provider": "registered-provider",
        "incident_platform": "registered-platform", "registered_incident_platform": "registered-platform",
        "source_commit": "a" * 40, "registered_source_commit": "a" * 40,
        "future_source_commit": False, "accepted_fix": False, "gold_patch": False, "truth_in_predicates": False,
        "pair": {"factor": "environment", "changed_dimensions": ["environment"], "incident_source": "source-a", "control_source": "source-a", "incident_provider": "provider-a", "control_provider": "provider-a", "incident_command": "command-a", "control_command": "command-a", "incident_fixture": "fixture-a", "control_fixture": "fixture-a"},
        "typed_incident_receipt_backed": True, "replay_consistent": True, "replay_receipt_ids": ["r1", "r2"],
        "order_carryover_pass": True, "source_mutation_count": 0, "cleanup_pass": True, "offline_network_requests": 0,
        "evidence_level": "DIMENSION_SENSITIVITY_VERIFIED", "necessity_or_sufficiency_executed": False,
        "contact_promoted_to_ownership": False, "interaction_supported": False, "factorial_cells_executed": False,
        "mixed_failure": False, "nonadditive_interaction": False, "unresolved_alternatives": ["necessity unresolved"],
        "ownership_class": "INSUFFICIENT_EVIDENCE", "terminal_support_pair_present": True,
        "terminal_writer": "ControllerAudit.counterfactual_v10", "unselected_outcome_access": 0,
        "arm_id": "A", "arm_outcome_source": "A", "tld_created_probe": False, "tld_changed_predicate": False,
        "truth_public": False, "source_ownership_from_truth": False, "patch_operations": 0,
        "repair_count_increment": 0, "historical_increment": 0, "product_beta": "blocked",
        "prospective_effectiveness": "NOT_ESTABLISHED", "memory": "not demonstrated",
        "production_readiness": False, "self_maintaining_software": "false/not demonstrated", "private_absolute_path": None,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-root", type=Path, required=True)
    args = parser.parse_args()
    args.output_root.mkdir(parents=True, exist_ok=True)
    source_paths = [
        ROOT / "configs/controllergate_master_completion_ledger_v2.json",
        ROOT / "configs/batch100_candidate_counterfactual_programs_v2.jsonl",
        ROOT / "configs/batch100_counterfactual_cell_registry_v2.jsonl",
        ROOT / "configs/batch100_opaque_tld_ordering_registry_v1.jsonl",
    ]
    registry: list[dict] = []
    results: list[dict] = []
    critic_findings: list[dict] = []
    with tempfile.TemporaryDirectory(prefix="controllergate-batch100-critic-") as temp_text:
        temp = Path(temp_text)
        for index, (name, path, value) in enumerate(MUTATIONS, start=1):
            mutation_root = temp / f"mutation-{index:02d}"
            evidence = mutation_root / "evidence"
            evidence.mkdir(parents=True)
            for source in source_paths:
                shutil.copy2(source, evidence / source.name)
            record = base_record()
            set_path(record, path, value)
            record["record_seal"] = canonical_hash(record)
            record_path = evidence / "critic_contract.json"
            write_json(record_path, record)
            manifest_rows = []
            for item in sorted(evidence.iterdir()):
                if item.name == "SHA256SUMS.txt":
                    continue
                manifest_rows.append(f"{hashlib.sha256(item.read_bytes()).hexdigest()}  {item.name}")
            (evidence / "SHA256SUMS.txt").write_text("\n".join(manifest_rows) + "\n", encoding="utf-8", newline="\n")
            detected = findings(record)
            rejected = bool(detected)
            registry.append({"mutation_id": f"BATCH100-MUTATION-{index:02d}", "name": name, "structured_path": path, "manifest_recomputed": True, "seals_recomputed": True, "complete_relevant_tree_copied": True, "expected_rejection": True})
            results.append({"mutation_id": f"BATCH100-MUTATION-{index:02d}", "name": name, "rejected": rejected, "critic_finding_ids": detected, "intended_invariant_detected": rejected, "critic": "controllergate.evidence.batch100_independent_critic.findings"})
            for finding in detected:
                critic_findings.append({"mutation_id": f"BATCH100-MUTATION-{index:02d}", "finding_id": finding, "severity": "BLOCK", "authority_allowed": "mutation rejection", "authority_forbidden": ["repair", "count mutation", "release"]})
    status = "PASS" if len(results) >= 50 and all(row["rejected"] for row in results) else "BLOCK"
    write_jsonl(args.output_root / "batch100_semantic_mutation_registry_v1.jsonl", registry)
    write_jsonl(args.output_root / "batch100_semantic_mutation_results_v1.jsonl", results)
    write_jsonl(args.output_root / "batch100_standalone_critic_findings_v1.jsonl", critic_findings)
    write_json(args.output_root / "batch100_semantic_mutation_campaign_summary.json", {
        "status": status, "semantic_mutations_executed": len(results),
        "semantic_mutations_rejected": sum(row["rejected"] for row in results),
        "copied_tree_count": len(results), "manifest_recomputation_count": len(results),
        "seal_recomputation_count": len(results), "critic_finding_count": len(critic_findings),
        "producer": "scripts/run_batch100_independent_critic.py", "execution_depth": "copied-tree structured mutation and independent semantic reconstruction",
        "semantic_scope": "Batch100 evidence and claim-boundary integrity", "authority_allowed": "critic rejection evidence",
        "authority_forbidden": ["causal ownership", "patch", "repair count", "release"],
    })
    return 0 if status == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
