from __future__ import annotations

from typing import Any, Iterable, Mapping


SHADOW_KEYS = {"shadow_hint", "tld_shadow_state", "tld_projection_result", "winner_N", "numerical_elbow", "T_e", "S_e", "NSS", "UI"}


def assert_transition_input_safe(transition_input: Mapping[str, Any]) -> None:
    found = sorted(SHADOW_KEYS.intersection(transition_input))
    if found:
        raise ValueError(f"TLD shadow cannot write or alter canonical cell state: {found}")


def rank_legal_probes(probes: Iterable[Mapping[str, Any]], advisories: Mapping[str, float], *, tld_arm_enabled: bool) -> list[Mapping[str, Any]]:
    rows = list(probes)
    if not tld_arm_enabled:
        return rows
    identities = {row["probe_id"] for row in rows}
    ranked = sorted(rows, key=lambda row: (-float(advisories.get(str(row["probe_id"]), 0.0)), str(row["probe_id"])))
    if {row["probe_id"] for row in ranked} != identities or len(ranked) != len(rows):
        raise ValueError("TLD adapter may not create or remove a legal probe")
    return ranked


def disabled_arm_terminal_invariance(builder: Any, frame: Mapping[str, Any], original_shadow: Mapping[str, Any], mutated_shadow: Mapping[str, Any]) -> dict[str, Any]:
    first = builder(frame, tld_arm_enabled=False, tld_shadow=original_shadow)
    second = builder(frame, tld_arm_enabled=False, tld_shadow=mutated_shadow)
    return {"status": "PASS" if first == second else "BLOCK", "original_terminal": first, "mutated_terminal": second, "TLD_disabled_terminal_mutation_count": int(first != second)}


def direct_fact_parent_rule(*, claim_scope: str, executed_observation_count: int, independent_verifier_count: int, independent_parent_count: int) -> dict[str, Any]:
    if claim_scope == "local_deterministic":
        allowed = executed_observation_count == 1 and independent_verifier_count >= 1
    else:
        allowed = independent_parent_count >= 2 and independent_verifier_count >= 1
    return {"status": "PASS" if allowed else "BLOCK", "claim_scope": claim_scope, "single_parent_local_exception": claim_scope == "local_deterministic", "universal_two_parent_rule": False}
