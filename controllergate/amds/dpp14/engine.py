from __future__ import annotations

from .seed import seed
from .normalize_evidence import normalize_evidence
from .freeze_frame import freeze_frame
from .decompose_contacts import decompose_contacts
from .expand_frontier import expand_frontier
from .materialize_requirements import materialize_requirements
from .select_minimal_probe import select_minimal_probe
from .execute_probe import execute_probe
from .verify_observation import verify_observation
from .update_constraints import update_constraints
from .mark_certain import mark_certain
from .backtrack import detect_contradiction_and_backtrack
from .interlock_elbow import interlock_and_elbow_audit
from .controller_audit import controller_audit_commit_or_abstain


TRANSITIONS = (
    "Seed", "NormalizeEvidence", "FreezeFrame", "DecomposeContacts", "ExpandFrontier",
    "MaterializeRequirements", "SelectMinimalProbe", "ExecuteProbe", "VerifyObservation",
    "UpdateConstraints", "MarkCertain", "DetectContradictionAndBacktrack",
    "InterlockAndElbowAudit", "ControllerAuditCommitOrAbstain",
)


def run_dpp14(candidate_id: str, evidence: dict) -> dict:
    state = seed(candidate_id, evidence)
    for transition in (normalize_evidence, freeze_frame, decompose_contacts, expand_frontier,
                       materialize_requirements, select_minimal_probe, execute_probe,
                       verify_observation, update_constraints, mark_certain,
                       detect_contradiction_and_backtrack, interlock_and_elbow_audit,
                       controller_audit_commit_or_abstain):
        state = transition(state)
    return state.record()
