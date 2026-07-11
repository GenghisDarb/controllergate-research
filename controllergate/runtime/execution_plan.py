from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from controllergate.core.evidence import hash_record


@dataclass(frozen=True)
class PhaseAuthorization:
    phase_id: str
    binding: str
    depends_on: tuple[str, ...]
    replay_authorized: bool = False


@dataclass(frozen=True)
class ExecutionPlan:
    plan_id: str
    candidate_id: str
    candidate_sha: str
    phases: tuple[PhaseAuthorization, ...]
    context_path: str
    plan_hash: str = ""

    def unsigned(self) -> dict[str, Any]:
        value = asdict(self)
        value.pop("plan_hash", None)
        return value


def seal_plan(plan: ExecutionPlan) -> dict[str, Any]:
    record = plan.unsigned()
    record["plan_hash"] = hash_record(record)
    return record


def plan_from_dict(value: dict[str, Any]) -> ExecutionPlan:
    phases = tuple(PhaseAuthorization(**item) for item in value["phases"])
    return ExecutionPlan(**{**value, "phases": phases})


def verify_plan(value: dict[str, Any]) -> dict[str, Any]:
    try: plan = plan_from_dict(value)
    except Exception as exc: return {"status": "BLOCK", "blocker": "execution_plan_schema_invalid", "error": type(exc).__name__}
    if plan.plan_hash != hash_record(plan.unsigned()): return {"status": "BLOCK", "blocker": "execution_plan_hash_invalid"}
    seen: set[str] = set()
    for phase in plan.phases:
        if phase.phase_id in seen: return {"status": "BLOCK", "blocker": "duplicate_phase_in_plan"}
        if any(item not in seen for item in phase.depends_on): return {"status": "BLOCK", "blocker": "execution_plan_phase_skip"}
        seen.add(phase.phase_id)
    return {"status": "PASS", "phase_count": len(plan.phases), "plan_hash": plan.plan_hash}
