from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import Any

from controllergate.amds.mandatory_invariant_interlock import validate_mandatory_invariants


TERMINAL_REQUIREMENTS: dict[str, frozenset[str]] = {
    "source_owned_behavior_defect": frozenset(
        {
            "candidate_failure_reproduced",
            "candidate_source_causal_frame_or_output_divergence",
            "provider_environment_alternative_excluded",
            "test_expectation_checked",
            "source_locality_established",
        }
    ),
    "environment_owned": frozenset(
        {
            "provider_runtime_causal_evidence",
            "source_not_independently_implicated",
            "environment_correction_changes_outcome",
        }
    ),
    "provider_owned": frozenset(
        {
            "provider_runtime_causal_evidence",
            "provider_identity_reproduced",
            "source_not_independently_implicated",
        }
    ),
    "test_expectation_fragility": frozenset(
        {
            "source_consistent_with_project_invariants",
            "native_expectation_inconsistent_or_stale",
            "provider_runtime_excluded",
        }
    ),
    "interpreter_behavior_change": frozenset(
        {
            "interpreter_identity_reproduced",
            "behavior_changes_across_runtime_boundary",
            "source_not_independently_implicated",
        }
    ),
    "harness_owned": frozenset(
        {
            "harness_causal_evidence",
            "source_not_independently_implicated",
            "harness_correction_changes_outcome",
        }
    ),
    "mixed_failure": frozenset(
        {
            "candidate_failure_reproduced",
            "multiple_causal_owners_directly_supported",
            "legal_action_is_safe_abstention",
        }
    ),
    "insufficient_evidence": frozenset({"unresolved_edges_can_change_legal_action"}),
}


def evaluate_causal_closure(
    terminal_class: str,
    *,
    invariant_states: Mapping[str, Any],
    resolved_edges: Iterable[str],
    optional_edges: Iterable[str] = (),
    excluded_alternatives: Iterable[str] = (),
    memory_condition: str | None = None,
) -> dict[str, Any]:
    interlock = validate_mandatory_invariants(invariant_states, memory_condition=memory_condition)
    requirements = TERMINAL_REQUIREMENTS.get(terminal_class)
    if requirements is None:
        return {
            "status": "BLOCK",
            "blocker": "unknown_terminal_class",
            "terminal_class": terminal_class,
            "mandatory_invariant_interlock": interlock,
        }
    resolved = set(resolved_edges)
    missing = sorted(requirements - resolved)
    excluded = sorted(set(excluded_alternatives))
    essential_alternatives_unresolved = terminal_class != "insufficient_evidence" and not excluded
    closed = interlock["status"] == "PASS" and not missing and not essential_alternatives_unresolved
    terminal_action = (
        "patch_authorization_may_be_considered"
        if closed and terminal_class == "source_owned_behavior_defect"
        else "safe_abstention"
        if closed
        else "continue_bounded_diagnosis"
    )
    return {
        "status": "PASS" if closed else "OPEN",
        "terminal_class": terminal_class,
        "closure_point": len(resolved),
        "required_edges": sorted(requirements),
        "required_edges_resolved": sorted(requirements & resolved),
        "missing_required_edges": missing,
        "optional_edges_unresolved": sorted(set(optional_edges) - resolved),
        "excluded_alternatives": excluded,
        "essential_alternatives_unresolved": essential_alternatives_unresolved,
        "terminal_action": terminal_action,
        "mandatory_invariant_interlock": interlock,
        "memory_can_supply_missing_evidence": False,
    }
