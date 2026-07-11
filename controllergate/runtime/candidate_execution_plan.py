from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from controllergate.core.evidence import hash_record


@dataclass(frozen=True)
class CandidatePhase:
    phase_id: str
    binding: str
    depends_on: tuple[str, ...] = ()
    network_mode: str = "none"
    source_mutation_allowed: bool = False
    test_mutation_allowed: bool = False


@dataclass(frozen=True)
class CandidateExecutionPlan:
    plan_id: str
    candidate_id: str
    candidate_sha: str
    current_state_hash: str
    output_root: str
    phases: tuple[CandidatePhase, ...]
    context_path: str
    plan_hash: str = ""

    def unsigned(self) -> dict[str, Any]:
        value = asdict(self)
        value.pop("plan_hash", None)
        return value


def seal_candidate_plan(plan: CandidateExecutionPlan) -> dict[str, Any]:
    value = plan.unsigned()
    value["plan_hash"] = hash_record(value)
    return value


def parse_candidate_plan(value: dict[str, Any]) -> CandidateExecutionPlan:
    phases = tuple(CandidatePhase(**item) for item in value["phases"])
    return CandidateExecutionPlan(**{**value, "phases": phases})


def verify_candidate_plan(value: dict[str, Any], *, allowed_output_root: str | Path | None = None) -> dict[str, Any]:
    try:
        plan = parse_candidate_plan(value)
    except Exception as exc:
        return {"status": "BLOCK", "blocker": "candidate_execution_plan_schema_invalid", "error": type(exc).__name__}
    if plan.plan_hash != hash_record(plan.unsigned()):
        return {"status": "BLOCK", "blocker": "candidate_execution_plan_hash_invalid"}
    if len(plan.candidate_sha) != 40 or any(ch not in "0123456789abcdef" for ch in plan.candidate_sha.lower()):
        return {"status": "BLOCK", "blocker": "candidate_execution_plan_sha_invalid"}
    seen: set[str] = set()
    for phase in plan.phases:
        if phase.phase_id in seen:
            return {"status": "BLOCK", "blocker": "candidate_execution_plan_duplicate_phase"}
        if any(parent not in seen for parent in phase.depends_on):
            return {"status": "BLOCK", "blocker": "candidate_execution_plan_phase_skip"}
        if phase.test_mutation_allowed:
            return {"status": "BLOCK", "blocker": "candidate_execution_plan_test_mutation_forbidden"}
        if phase.network_mode not in {"none", "bounded_read_only"}:
            return {"status": "BLOCK", "blocker": "candidate_execution_plan_network_mode_invalid"}
        seen.add(phase.phase_id)
    output = Path(plan.output_root).resolve()
    if allowed_output_root is not None:
        allowed = Path(allowed_output_root).resolve()
        if output != allowed and allowed not in output.parents:
            return {"status": "BLOCK", "blocker": "candidate_execution_output_root_outside_authority"}
    return {"status": "PASS", "plan_hash": plan.plan_hash, "phase_count": len(plan.phases)}
