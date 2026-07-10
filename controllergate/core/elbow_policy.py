from __future__ import annotations

ELBOW_CLASSIFICATIONS = (
    "elbow_open_single_causal_family_recovery_authorized",
    "elbow_open_source_local_patch_diagnostic_authorized",
    "elbow_open_provider_local_recovery_authorized",
    "elbow_open_harness_local_recovery_authorized",
    "elbow_closed_evidence_insufficient",
    "elbow_closed_multi_family_ambiguous",
    "elbow_closed_environment_orthology",
    "elbow_closed_provider_surface",
    "elbow_closed_harness_origin",
    "elbow_closed_command_translation",
    "elbow_closed_test_expectation_or_interpreter_behavior",
    "elbow_closed_security_substrate",
    "elbow_closed_flatline_zero_observation",
    "elbow_closed_nonreproducible",
    "elbow_closed_forbidden_evidence",
)

OPEN_REQUIREMENTS = (
    "one_causal_family_isolated", "same_boundary_reproduction", "confounders_controlled",
    "intervention_is_family_local", "decision_time_evidence_support", "all_interlocks_pass",
    "rollback_exists", "next_observation_discriminating",
)
