from __future__ import annotations

from dataclasses import dataclass

from controllergate.state.integrity import canonical_hash

from .causal_board import CausalBoardController
from .state import DPP14State


TERMINAL_MAPPING = {
    "source_owned_behavior_defect": "source_owned_behavior_defect",
    "provider_owned": "provider_owned",
    "environment_owned": "environment_owned",
    "platform_owned": "platform_owned",
    "network_or_transport_owned": "network_or_transport_owned",
    "harness_owned": "harness_owned",
    "test_or_expectation_fragility": "test_or_expectation_fragility",
    "mixed_failure": "mixed_failure",
    "insufficient_evidence": "safe_abstention_insufficient_evidence",
}
SOURCE_REQUIRED_FACT_PREFIXES = ("verified_outcome:", "broker_record:", "observation:")
SOURCE_REQUIREMENTS = (
    "direct_source_divergence",
    "shared_provider_runtime_command",
    "provider_alternative_excluded",
    "environment_platform_alternative_excluded",
    "harness_target_alternative_excluded",
    "expectation_checked",
    "ast_contact_domain",
    "repair_interlocks_pass",
)


@dataclass(frozen=True)
class ControllerAuditResult:
    candidate_id: str
    frame_hash: str
    patch_authority: bool
    reason: str
    run_id: str
    terminal: str
    terminal_writer: str = "controllergate.amds.dpp14.controller_audit"

    @property
    def terminal_hash(self) -> str:
        return canonical_hash(self.record(include_hash=False))

    def record(self, *, include_hash: bool = True) -> dict[str, object]:
        value: dict[str, object] = {
            "candidate_id": self.candidate_id,
            "frame_hash": self.frame_hash,
            "patch_authority": self.patch_authority,
            "reason": self.reason,
            "run_id": self.run_id,
            "terminal": self.terminal,
            "terminal_writer": self.terminal_writer,
        }
        if include_hash:
            value["terminal_hash"] = self.terminal_hash
        return value


def commit_terminal(board: CausalBoardController) -> ControllerAuditResult:
    active = sorted(board.active_hypotheses)
    if len(active) != 1:
        return ControllerAuditResult(
            candidate_id=board.frame.candidate_id,
            frame_hash=board.frame.frame_hash,
            patch_authority=False,
            reason="multiple causal alternatives remain or evidence budget ended",
            run_id=board.frame.run_id,
            terminal="safe_abstention_insufficient_evidence",
        )
    selected = active[0]
    terminal = TERMINAL_MAPPING.get(selected, "safe_abstention_insufficient_evidence")
    if selected == "source_owned_behavior_defect":
        fact_prefixes = {fact.split(":", 1)[0] + ":" for fact in board.certain_facts}
        if not set(SOURCE_REQUIRED_FACT_PREFIXES).issubset(fact_prefixes):
            return ControllerAuditResult(
                candidate_id=board.frame.candidate_id,
                frame_hash=board.frame.frame_hash,
                patch_authority=False,
                reason="direct source-authorizing evidence incomplete",
                run_id=board.frame.run_id,
                terminal="safe_abstention_insufficient_evidence",
            )
    return ControllerAuditResult(
        candidate_id=board.frame.candidate_id,
        frame_hash=board.frame.frame_hash,
        patch_authority=False,
        reason="typed causal terminal committed; repair licensing remains separate",
        run_id=board.frame.run_id,
        terminal=terminal,
    )


def controller_audit_commit_or_abstain(state: DPP14State) -> DPP14State:
    """Compatibility transition for pre-v2.19 frozen fixtures.

    Production Batch088 diagnosis uses :func:`commit_terminal`. This transition
    remains only so historical transition-fixture tests keep their original
    evidence boundary while the public transition names stay stable.
    """
    direct = [
        item.get("classification")
        for item in state.observations
        if item.get("verified") and item.get("direct")
    ]
    proposed = direct[0] if len(set(direct)) == 1 and direct else "insufficient_evidence"
    if proposed == "source_owned_behavior_defect" and not all(
        state.frozen_frame.get(key) is True for key in SOURCE_REQUIREMENTS
    ):
        proposed = "insufficient_evidence"
    if state.contradictions or proposed not in state.hypotheses:
        proposed = "insufficient_evidence"
    state.terminal = proposed
    state.trace.append(
        {
            "sole_merged_state_writer": True,
            "status": "PASS",
            "terminal": proposed,
            "transition": "ControllerAuditCommitOrAbstain",
        }
    )
    return state
