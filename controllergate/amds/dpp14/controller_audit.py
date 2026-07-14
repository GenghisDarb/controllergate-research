from .state import DPP14State


SOURCE_REQUIREMENTS = ("direct_source_divergence", "shared_provider_runtime_command", "provider_alternative_excluded", "environment_platform_alternative_excluded", "harness_target_alternative_excluded", "expectation_checked", "ast_contact_domain", "repair_interlocks_pass")


def controller_audit_commit_or_abstain(state: DPP14State) -> DPP14State:
    direct = [item.get("classification") for item in state.observations if item.get("verified") and item.get("direct")]
    proposed = direct[0] if len(set(direct)) == 1 and direct else "insufficient_evidence"
    if proposed == "source_owned_behavior_defect" and not all(state.frozen_frame.get(key) is True for key in SOURCE_REQUIREMENTS):
        proposed = "insufficient_evidence"
    if state.contradictions or proposed not in state.hypotheses:
        proposed = "insufficient_evidence"
    state.terminal = proposed
    state.trace.append({"transition": "ControllerAuditCommitOrAbstain", "status": "PASS", "sole_merged_state_writer": True, "terminal": proposed})
    return state
