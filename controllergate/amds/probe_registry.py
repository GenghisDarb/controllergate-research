from __future__ import annotations

PROBE_TYPES = (
    "dependency_lock_probe", "issue_timestamp_probe", "target_intent_probe", "command_variant_probe", "source_commit_window_probe", "native_test_presence_probe", "issue_derived_harness_firewall_probe", "runtime_incident_probe", "ast_excision_probe", "null_comparability_probe", "curvature_route_diversity_probe", "interlock_invariant_probe", "seed_replacement_probe",
)


def probe_contracts() -> dict[str,dict]:
    return {name:{"input_schema":"candidate-scoped-v1","authorization_required":True,"output_schema":"probe-observation-v1","mutation_policy":"none","network_policy":"declared_by_probe","resource_policy":"bounded","stop_behavior":"stop_on_block_or_manual_review","independent_verifier":"verify_probe_observation"} for name in PROBE_TYPES}
