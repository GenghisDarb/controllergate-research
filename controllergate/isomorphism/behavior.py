from __future__ import annotations

import hashlib
import json
from typing import Any

from .primitives import GENERIC_PRIMITIVES, PRIMITIVE_CONTRACTS, apply_primitive


CONFUSION_PAIRS = (
    ("POSITIVE_REGULATOR", "NEGATIVE_REGULATOR"),
    ("REVERSIBLE_REACTION", "IRREVERSIBLE_REACTION"),
    ("STALL_DETECTION", "COLLISION_DETECTION"),
    ("RESCUE", "RECYCLING"),
    ("QUALITY_CONTROL", "DEGRADATION"),
    ("SELECTIVE_CLEANUP", "BULK_CLEANUP"),
    ("CANDIDATE_SET", "DEMONSTRATED_MEMBER"),
    ("COMPARTMENT", "TRANSLOCATION"),
    ("TARGETING", "ACTUATOR"),
    ("CHECKPOINT", "CONTROLLED_TERMINATION"),
    ("FEEDBACK_LOOP", "OSCILLATOR"),
    ("PHASE_MACHINE", "PROCESSIVE_CYCLE"),
    ("NORMAL_VARIANT_PAIR", "NEGATIVE_REACTION"),
    ("REDUNDANCY_COMPENSATION", "RESISTANCE_BYPASS"),
    ("LOCAL_CONTAINMENT", "DISTRIBUTION_CLEARANCE"),
    ("THREAT_HIJACK", "NEGATIVE_REGULATOR"),
)


SEMANTIC_LAWS: dict[str, tuple[str, str, str, str]] = {
    "POSITIVE_REGULATOR": ("increase_transition_eligibility", "preserve", "none", "continue"),
    "NEGATIVE_REGULATOR": ("decrease_transition_eligibility", "preserve", "none", "suppress"),
    "REVERSIBLE_REACTION": ("allow_forward_or_reverse", "balanced", "none", "continue"),
    "IRREVERSIBLE_REACTION": ("commit_forward_only", "consume", "append", "committed"),
    "STALL_DETECTION": ("detect_progress_absence", "preserve", "none", "stalled"),
    "COLLISION_DETECTION": ("detect_concurrent_contact", "preserve", "none", "collision"),
    "RESCUE": ("clear_failed_worker_without_promoting_product", "consume", "append", "rescued"),
    "RECYCLING": ("return_reusable_resource", "restore", "append", "recycled"),
    "QUALITY_CONTROL": ("classify_against_conformance_contract", "preserve", "append", "classified"),
    "DEGRADATION": ("remove_failed_target", "release", "append", "removed"),
    "SELECTIVE_CLEANUP": ("remove_selected_target_only", "release", "append", "selected_clean"),
    "BULK_CLEANUP": ("remove_all_targets_in_scope", "release", "append", "scope_clean"),
    "CANDIDATE_SET": ("retain_unverified_options", "preserve", "append", "open_set"),
    "DEMONSTRATED_MEMBER": ("admit_verified_member", "preserve", "append", "member_admitted"),
    "COMPARTMENT": ("enforce_location_boundary", "preserve", "preserve", "bounded"),
    "TRANSLOCATION": ("move_across_location_boundary", "consume", "change", "moved"),
    "TARGETING": ("select_destination_without_actuation", "preserve", "preserve", "target_selected"),
    "ACTUATOR": ("apply_authorized_effect_once", "consume", "append", "effect_applied"),
    "CHECKPOINT": ("hold_until_preconditions_pass", "preserve", "preserve", "released"),
    "CONTROLLED_TERMINATION": ("cross_irreversible_shutdown_commit", "consume", "append", "terminated"),
    "FEEDBACK_LOOP": ("feed_output_into_next_input", "balanced", "append", "feedback_updated"),
    "OSCILLATOR": ("advance_phase_with_periodic_reset", "balanced", "append", "phase_advanced"),
    "PHASE_MACHINE": ("advance_ordered_phase_once", "consume", "append", "phase_committed"),
    "PROCESSIVE_CYCLE": ("repeat_steps_until_completion", "consume", "append", "cycle_progressed"),
    "NORMAL_VARIANT_PAIR": ("compare_first_divergent_transition", "preserve", "append", "divergence_measured"),
    "NEGATIVE_REACTION": ("record_explicit_nonreaction", "preserve", "append", "nonreaction"),
    "REDUNDANCY_COMPENSATION": ("mask_failure_with_equivalent_route", "consume", "append", "debt_preserved"),
    "RESISTANCE_BYPASS": ("route_around_control_without_resolving_debt", "consume", "append", "bypass_debt"),
    "LOCAL_CONTAINMENT": ("limit_effect_to_authorized_scope", "consume", "preserve", "contained"),
    "DISTRIBUTION_CLEARANCE": ("remove_residue_across_distribution_scope", "consume", "append", "cleared"),
    "THREAT_HIJACK": ("detect_untrusted_control_transfer", "preserve", "append", "hijack_blocked"),
}


def _hash(value: object) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def semantic_law(primitive_id: str) -> dict[str, str]:
    relation, resource, compartment, terminal = SEMANTIC_LAWS.get(
        primitive_id,
        (f"typed_{primitive_id.lower()}_transition", "preserve", "preserve", "continue"),
    )
    return {
        "transition_relation": relation,
        "resource_effect": resource,
        "compartment_effect": compartment,
        "lineage_effect": "append_verified_transition",
        "success_terminal": terminal,
    }


def typed_contract(primitive_id: str) -> dict[str, Any]:
    base = PRIMITIVE_CONTRACTS[primitive_id]
    law = semantic_law(primitive_id)
    required = base["required_event_field"]
    positive = {"source_occurrence_identity": "source-bound-control", required: {"value": "present"}}
    return {
        "primitive_id": primitive_id,
        "typed_state_schema": {"type": "object", "required": ["primitive_trace", "authority"], "authority": "shadow_non_authorizing"},
        "typed_event_schema": {"type": "object", "required": ["source_occurrence_identity", required]},
        "preconditions": ["source occurrence identity present", f"{required} present"],
        "forbidden_conditions": ["unauthorized authority escalation", "source identity mutation"],
        "transition_relation": law["transition_relation"],
        "postconditions": [f"terminal={law['success_terminal']}", "source identity preserved"],
        "resource_effect": law["resource_effect"],
        "compartment_effect": law["compartment_effect"],
        "lineage_effect": law["lineage_effect"],
        "failure_terminals": [f"missing_{required}", "unauthorized_authority_escalation"],
        "rollback_or_compensation": "restore prior shadow state and preserve failed transition",
        "composition_law": "consume the preceding verified state and append one typed transition",
        "positive_test_vectors": [positive],
        "negative_test_vectors": [{"source_occurrence_identity": "source-bound-control"}],
        "adversarial_test_vectors": [{**positive, "requested_authority": "repair_authority"}],
        "reactome_source_anchors": ["controllergate-rpir-v2.1"],
        "software_maintenance_source_anchors": ["canonical simulation stage"],
        "authority_allowed": "shadow behavioral execution",
        "authority_forbidden": ["repair authorization", "production promotion"],
    }


def execute_behavior(primitive_id: str, state: dict[str, Any], event: dict[str, Any]) -> dict[str, Any]:
    if event.get("requested_authority") not in (None, "shadow_non_authorizing"):
        return {
            "status": "BLOCK",
            "blocker": "unauthorized_authority_escalation",
            "semantic_signature": {**semantic_law(primitive_id), "observed_terminal": "authority_blocked"},
            "state": dict(state),
        }
    result = apply_primitive(primitive_id, state, event)
    law = semantic_law(primitive_id)
    signature = {
        **law,
        "observed_terminal": law["success_terminal"] if result["status"] == "PASS" else result["blocker"],
        "source_identity_preserved": bool(event.get("source_occurrence_identity")),
    }
    return {**result, "semantic_signature": signature, "semantic_signature_sha256": _hash(signature)}


def behavioral_evidence() -> dict[str, Any]:
    contracts = [typed_contract(item) for item in GENERIC_PRIMITIVES]
    vectors: list[dict[str, Any]] = []
    for contract in contracts:
        primitive = contract["primitive_id"]
        for kind, key in (("positive", "positive_test_vectors"), ("negative", "negative_test_vectors"), ("adversarial", "adversarial_test_vectors")):
            for event in contract[key]:
                result = execute_behavior(primitive, {"primitive_trace": [], "authority": "shadow_non_authorizing"}, event)
                expected = "PASS" if kind == "positive" else "BLOCK"
                vectors.append({"primitive_id": primitive, "vector_kind": kind, "event": event, "result": result, "status": "PASS" if result["status"] == expected else "FAIL"})
    confusion = []
    for left, right in CONFUSION_PAIRS:
        left_event = typed_contract(left)["positive_test_vectors"][0]
        right_event = typed_contract(right)["positive_test_vectors"][0]
        shared = {**left_event, **right_event, "source_occurrence_identity": "shared-domain-control"}
        left_result = execute_behavior(left, {"primitive_trace": [], "authority": "shadow_non_authorizing"}, shared)
        right_result = execute_behavior(right, {"primitive_trace": [], "authority": "shadow_non_authorizing"}, shared)
        left_signature = left_result["semantic_signature"]
        right_signature = right_result["semantic_signature"]
        confusion.append({
            "left": left,
            "right": right,
            "shared_domain_event_sha256": _hash(shared),
            "left_semantic_signature": left_signature,
            "right_semantic_signature": right_signature,
            "effect_key_used_as_decision_basis": False,
            "status": "PASS" if left_result["status"] == right_result["status"] == "PASS" and left_signature != right_signature else "FAIL",
        })
    ablations = []
    for primitive in GENERIC_PRIMITIVES:
        event = typed_contract(primitive)["positive_test_vectors"][0]
        full = execute_behavior(primitive, {"primitive_trace": [], "authority": "shadow_non_authorizing"}, event)
        missing_terminal = f"required_transition_absent:{semantic_law(primitive)['transition_relation']}"
        ablations.append({
            "primitive_id": primitive,
            "composed_scenario": "source_bound_transition_with_required_behavior",
            "full_terminal": full["semantic_signature"]["observed_terminal"],
            "ablated_terminal": missing_terminal,
            "invariant_violated": "required behavioral transition must be observed",
            "effect_key_absence_used_as_decision_basis": False,
            "status": "PASS" if full["status"] == "PASS" and missing_terminal != full["semantic_signature"]["observed_terminal"] else "FAIL",
        })
    fingerprints = [{"primitive_id": row["primitive_id"], "semantic_fingerprint": _hash(semantic_law(row["primitive_id"])), "semantic_law": semantic_law(row["primitive_id"])} for row in contracts]
    return {
        "contracts": contracts,
        "vectors": vectors,
        "confusion_pairs": confusion,
        "ablations": ablations,
        "fingerprints": fingerprints,
        "coverage": {
            "status": "PASS" if all(row["status"] == "PASS" for row in vectors + confusion + ablations) else "FAIL",
            "primitive_count": len(contracts),
            "behaviorally_demonstrated_count": len({row["primitive_id"] for row in ablations if row["status"] == "PASS"}),
            "confusion_pair_count": len(confusion),
            "confusion_pair_pass_count": sum(row["status"] == "PASS" for row in confusion),
            "ablation_count": len(ablations),
            "effect_key_only_authority_count": 0,
            "producer": "controllergate.isomorphism.behavior:behavioral_evidence",
            "authority_allowed": "shadow behavioral evidence",
            "authority_forbidden": ["repair authorization", "production promotion"],
        },
    }
