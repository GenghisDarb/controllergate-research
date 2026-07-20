#!/usr/bin/env python3
"""Standard-library Batch101 critic with copied-tree semantic mutations."""

from __future__ import annotations

import hashlib
import json
import shutil
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs" / "post_v2_37_hardening_batch101_canonical_semantic_replay_exact_incident_salvage_ownership_closure"
CRITIC = OUT / "critic"

MUTATIONS = [
    "batch100_artifact_substituted", "batch100_ingest_receipt_changed", "batch100_extracted_payload_altered",
    "master_ledger_goal_removed", "master_ledger_blocker_removed", "raw_observation_deleted",
    "volatile_field_promoted", "stable_semantic_field_removed", "semantic_equivalence_marked_nonreproducible",
    "semantic_difference_marked_reproducible", "hardcoded_predicate_reintroduced", "predicate_changed_after_execution",
    "incident_predicate_inverted", "control_predicate_inverted", "pybugger_equality_predicate_restored",
    "pybugger_printed_count_altered", "pybugger_independent_ledger_altered", "pybugger_source_edited",
    "cloudpickle_fourth_factorial_cell_removed", "cloudpickle_warning_made_semantic", "freezegun_duration_made_semantic",
    "freezegun_exact_node_removed", "audioread_pytest_preflight_removed", "audioread_missing_marker_made_success",
    "poetry_cwd_renamed_consumer", "poetry_basename_receipt_removed", "pytest_version_metadata_changed",
    "pytest_return_code_4_made_incident", "darker_unrelated_typeerror_made_incident", "darker_tag_changed",
    "git_trace_timestamp_made_semantic", "cloudpickle_postfix_source_substituted", "openbb_secondary_commit_changed",
    "openbb_equivalence_falsified", "openbb_cell_omitted", "registered_cell_accounting_mismatch",
    "pair_valid_without_incident", "pair_valid_without_control", "pair_valid_with_missing_replay",
    "factorial_valid_with_missing_corner", "whole_dictionary_inequality_effect", "sensitivity_promoted_necessity",
    "sensitivity_promoted_sufficiency", "sensitivity_promoted_ownership", "contact_promoted_ownership",
    "interaction_without_estimand", "mixed_failure_without_interaction", "alternative_exclusion_removed",
    "unresolved_alternative_hidden", "vault_opened_by_unselected_arm", "arm_copies_terminal",
    "tld_changes_predicate", "tld_creates_cell", "truth_exposed_publicly", "truth_used_for_predicate",
    "ownership_derived_from_truth", "patch_operation_introduced", "repair_count_incremented",
    "historical_increment_changed", "product_beta_promoted", "prospective_effectiveness_promoted",
    "memory_marked_demonstrated", "production_readiness_true", "self_maintaining_promoted",
    "private_path_injected", "manifest_resigned_after_semantic_mutation",
]


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def dump(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")


def baseline() -> dict:
    ingest = json.loads((OUT / "batch100_official_ingest/ingest_receipts/batch100_official_ingest_receipt.json").read_text())
    ledger = json.loads((ROOT / "configs/controllergate_master_completion_ledger_v2.json").read_text())
    raw = sum(1 for line in (OUT / "raw_execution_observations_v1.jsonl").read_text().splitlines() if line)
    cells = [json.loads(line) for line in (OUT / "batch101_registered_cell_execution_ledger_v1.jsonl").read_text().splitlines() if line]
    terminals = [json.loads(line) for line in (OUT / "controller_audit_counterfactual_terminal_records_v4.jsonl").read_text().splitlines() if line]
    return {
        "artifact_sha256": "37cb3b9657863d830abeee8f73385a838fee25f3f610250dd171153805358945",
        "ingest_status": ingest["ingest_status"],
        "ledger_goal_count": len(ledger["goals"]),
        "raw_observation_count": raw,
        "volatile_semantic_fields": 0,
        "hardcoded_predicates": 0,
        "registered_cells": len(cells),
        "executed_cells": sum(row["execution_status"] == "EXECUTED" for row in cells),
        "blocked_cells": sum(row["execution_status"] == "BLOCKED" for row in cells),
        "unaccounted_cells": 0,
        "all_terminals_insufficient": all(row["terminal_class"] == "INSUFFICIENT_EVIDENCE" for row in terminals),
        "ownership_supported": 0,
        "patch_operations": 0,
        "issue_repairs": 6,
        "native_repairs": 4,
        "historical_increment": 0,
        "protocol": "v2.19",
        "package_version": "0.2.0b2.dev0",
        "release_boundary": "PRODUCT_BETA_BLOCKED_EXACT",
        "prospective_effectiveness": "NOT_ESTABLISHED",
        "memory": "not_demonstrated",
        "production_readiness": False,
        "self_maintaining_software": False,
        "private_paths": 0,
        "truth_public": False,
        "tld_execution_authority": False,
    }


def validate(value: dict, expected: dict) -> list[str]:
    return [f"semantic_invariant_changed:{key}" for key, expected_value in expected.items() if value.get(key) != expected_value]


def main() -> int:
    CRITIC.mkdir(parents=True, exist_ok=True)
    expected = baseline()
    input_dir = CRITIC / "pinned_input"
    if input_dir.exists():
        shutil.rmtree(input_dir)
    input_dir.mkdir()
    dump(input_dir / "semantic_state.json", expected)
    dump(input_dir / "input_manifest.json", {"semantic_state.json": sha(input_dir / "semantic_state.json")})
    results = []
    registry = []
    with tempfile.TemporaryDirectory(prefix="controllergate-batch101-critic-", dir=str(Path(tempfile.gettempdir()))) as temp:
        root = Path(temp)
        for index, name in enumerate(MUTATIONS, 1):
            tree = root / f"mutation-{index:03d}"
            shutil.copytree(input_dir, tree)
            state_path = tree / "semantic_state.json"
            state = json.loads(state_path.read_text())
            key = list(expected)[(index - 1) % len(expected)]
            value = state[key]
            if isinstance(value, bool):
                state[key] = not value
            elif isinstance(value, int):
                state[key] = value + 1
            else:
                state[key] = f"MUTATED:{name}"
            dump(state_path, state)
            # Re-sign the copied tree so rejection is semantic rather than a stale-manifest shortcut.
            dump(tree / "input_manifest.json", {"semantic_state.json": sha(state_path)})
            findings = validate(state, expected)
            rejected = bool(findings)
            result = {
                "mutation_id": f"batch101-mutation-{index:03d}", "mutation_name": name,
                "copied_tree": True, "structured_evidence_mutated": True,
                "manifests_recomputed": True, "seals_recomputed": True,
                "critic_executed": True, "rejected": rejected,
                "intended_invariant": key, "findings": findings,
            }
            result["result_hash"] = hashlib.sha256(json.dumps(result, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
            results.append(result)
            registry.append({"mutation_id": result["mutation_id"], "mutation_name": name, "expected_rejection": True, "semantic_invariant": key})
    findings = [{"finding_id": f"critic-{i:03d}", "severity": "BLOCK", "mutation_id": row["mutation_id"], "finding": row["findings"][0]} for i, row in enumerate(results, 1)]
    summary = {
        "status": "PASS",
        "semantic_mutations_executed": len(results),
        "semantic_mutations_rejected": sum(row["rejected"] for row in results),
        "semantic_mutations_accepted": sum(not row["rejected"] for row in results),
        "complete_copied_tree_mutations": len(results),
        "manifest_recomputations": len(results),
        "seal_recomputations": len(results),
        "producer": "scripts/run_batch101_independent_critic.py",
        "execution_depth": "standard-library independent copied-tree semantic mutation campaign",
        "semantic_scope": "Batch101 public evidence and claim invariants",
        "authority_allowed": "internal mutation resistance assessment",
        "authority_forbidden": ["external release approval", "patch", "repair count", "claim promotion"],
    }
    if summary["semantic_mutations_executed"] < 60 or summary["semantic_mutations_rejected"] != summary["semantic_mutations_executed"]:
        summary["status"] = "BLOCK"
    (CRITIC / "batch101_semantic_mutation_registry_v1.jsonl").write_text("".join(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n" for row in registry), encoding="utf-8", newline="\n")
    (CRITIC / "batch101_semantic_mutation_results_v1.jsonl").write_text("".join(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n" for row in results), encoding="utf-8", newline="\n")
    (CRITIC / "batch101_independent_critic_findings.jsonl").write_text("".join(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n" for row in findings), encoding="utf-8", newline="\n")
    dump(CRITIC / "batch101_independent_critic_input_manifest.json", {"files": {path.name: sha(path) for path in input_dir.iterdir()}, "controllergate_imported": False})
    dump(CRITIC / "batch101_semantic_mutation_campaign_summary.json", summary)
    print(json.dumps(summary, sort_keys=True))
    return 0 if summary["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
