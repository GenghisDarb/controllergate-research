"""Independent semantic critic for the Batch100 public evidence contract."""

from __future__ import annotations

import hashlib
import json
from typing import Any


REQUIRED_GOALS = {f"CG-GOAL-{index:03d}" for index in range(21)}


def canonical_hash(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def findings(record: dict[str, Any]) -> list[str]:
    """Reconstruct safety findings without trusting status, seal, or manifest fields."""
    found: list[str] = []
    expect = {
        "artifact_sha": "3bd768dc68721df44ad7ca6f25426604fec0a91bd9d5c38ce3868e63eb7728e1",
        "ingest_receipt_sha": "55f9549fe1bf9d0d417980686434daf2c5336195b0955bd7acdd3452c428f2f3",
    }
    for key, value in expect.items():
        if record.get(key) != value:
            found.append(f"{key}_identity_mismatch")
    if set(record.get("goal_ids", [])) != REQUIRED_GOALS:
        found.append("master_ledger_goal_set_changed")
    if not record.get("completed_goal_evidence_present"):
        found.append("completed_ledger_evidence_removed")
    if record.get("incident_provider") != record.get("registered_incident_provider"):
        found.append("incident_provider_changed")
    if record.get("incident_platform") != record.get("registered_incident_platform"):
        found.append("incident_platform_changed")
    if record.get("source_commit") != record.get("registered_source_commit"):
        found.append("wrong_or_future_source_commit")
    for key in ("future_source_commit", "accepted_fix", "gold_patch", "truth_in_predicates"):
        if record.get(key):
            found.append(f"forbidden_{key}")
    pair = record.get("pair", {})
    factor = pair.get("factor")
    allowed_change = {
        "provider": {"provider"}, "command": {"command"}, "fixture": {"fixture"},
        "environment": {"environment"}, "input": {"input"}, "platform": {"platform"},
    }.get(factor, {factor})
    changed = set(pair.get("changed_dimensions", []))
    if not changed or not changed.issubset(allowed_change):
        found.append("pair_changed_dimensions_confounded")
    for invariant in ("source", "provider", "command", "fixture"):
        if invariant != factor and pair.get(f"incident_{invariant}") != pair.get(f"control_{invariant}"):
            found.append(f"pair_{invariant}_mismatch")
    if not record.get("typed_incident_receipt_backed"):
        found.append("typed_incident_fabricated")
    if not record.get("replay_consistent"):
        found.append("replay_inconsistency_hidden")
    if record.get("replay_receipt_ids", [None, None])[0] == record.get("replay_receipt_ids", [None, None])[1]:
        found.append("duplicate_replay_relabelled")
    if not record.get("order_carryover_pass"):
        found.append("order_carryover_ignored")
    if record.get("source_mutation_count", 0):
        found.append("source_tree_mutated")
    if not record.get("cleanup_pass"):
        found.append("cleanup_failure_hidden")
    if record.get("offline_network_requests", 0):
        found.append("offline_network_used")
    level = record.get("evidence_level")
    if level in {"NECESSITY_SUPPORTED", "SUFFICIENCY_SUPPORTED", "OWNERSHIP_SUPPORTED"} and not record.get("necessity_or_sufficiency_executed"):
        found.append("sensitivity_evidence_overpromoted")
    if record.get("contact_promoted_to_ownership"):
        found.append("contact_promoted_to_ownership")
    if record.get("interaction_supported") and not record.get("factorial_cells_executed"):
        found.append("interaction_without_factorial_cells")
    if record.get("mixed_failure") and not record.get("nonadditive_interaction"):
        found.append("mixed_failure_without_interaction")
    if not record.get("unresolved_alternatives"):
        found.append("unresolved_alternative_removed")
    if record.get("ownership_class") != "INSUFFICIENT_EVIDENCE":
        found.append("ownership_class_unsupported")
    if not record.get("terminal_support_pair_present"):
        found.append("terminal_support_pair_removed")
    if record.get("terminal_writer") != "ControllerAudit.counterfactual_v10":
        found.append("terminal_writer_unauthorized")
    if record.get("unselected_outcome_access", 0):
        found.append("unselected_outcome_opened")
    if record.get("arm_outcome_source") != record.get("arm_id"):
        found.append("arm_outcome_copied")
    if record.get("tld_created_probe"):
        found.append("tld_created_probe")
    if record.get("tld_changed_predicate"):
        found.append("tld_changed_semantics")
    if record.get("truth_public") or record.get("source_ownership_from_truth"):
        found.append("private_truth_authority_leak")
    if record.get("patch_operations", 0):
        found.append("repair_operation_introduced")
    if record.get("repair_count_increment", 0):
        found.append("repair_count_incremented")
    if record.get("historical_increment", 0):
        found.append("historical_increment_incremented")
    if record.get("product_beta") != "blocked":
        found.append("product_beta_promoted")
    if record.get("prospective_effectiveness") != "NOT_ESTABLISHED":
        found.append("prospective_effectiveness_promoted")
    if record.get("memory") != "not demonstrated":
        found.append("memory_overclaim")
    if record.get("production_readiness") is not False:
        found.append("production_readiness_overclaim")
    if record.get("self_maintaining_software") != "false/not demonstrated":
        found.append("self_maintaining_overclaim")
    if record.get("private_absolute_path"):
        found.append("private_path_injected")
    return sorted(set(found))
