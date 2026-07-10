from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from .evidence import hash_record

Handler = Callable[[dict[str, Any]], dict[str, Any]]
Verifier = Callable[[dict[str, Any]], bool]


def passthrough_handler(context: dict[str, Any]) -> dict[str, Any]:
    return dict(context.get("step_payload") or {})


def nonempty_output_verifier(output: dict[str, Any]) -> bool:
    return isinstance(output, dict) and bool(output)


HANDLERS: dict[str, Handler] = {"passthrough_handler": passthrough_handler}
VERIFIERS: dict[str, Verifier] = {"nonempty_output_verifier": nonempty_output_verifier}


@dataclass(frozen=True)
class StaticStep:
    step_id: str
    handler: str
    verifier: str


def resolve_registry(steps: list[dict[str, Any]]) -> dict[str, Any]:
    unresolved_handlers = sorted({str(step["handler"]) for step in steps if str(step["handler"]) not in HANDLERS})
    unresolved_verifiers = sorted({str(step["verifier"]) for step in steps if str(step["verifier"]) not in VERIFIERS})
    return {
        "status": "PASS" if not unresolved_handlers and not unresolved_verifiers else "FAIL",
        "unresolved_handlers": unresolved_handlers,
        "unresolved_verifiers": unresolved_verifiers,
        "handler_count": len(HANDLERS),
        "verifier_count": len(VERIFIERS),
    }


def execute_static_graph(candidate_id: str, steps: list[dict[str, Any]], payloads: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    prior_hash = "GENESIS"
    upstream_blocker: str | None = None
    for spec in steps:
        step_id = str(spec["step_id"])
        if upstream_blocker:
            output = {"skipped": True, "upstream_blocker": upstream_blocker}
            status = "block"
            blocker = upstream_blocker
        else:
            handler = HANDLERS[str(spec["handler"])]
            verifier = VERIFIERS[str(spec["verifier"])]
            output = handler({"candidate_id": candidate_id, "step_payload": payloads.get(step_id, {})})
            passed = verifier(output) and output.get("status") not in {"BLOCK", "FAIL"}
            status = "pass" if passed else ("manual_review" if output.get("status") == "MANUAL_REVIEW" else "block")
            blocker = output.get("blocker") if status != "pass" else None
            if status == "block":
                upstream_blocker = str(blocker or f"{step_id.lower()}_blocked")
                blocker = upstream_blocker
        record = {
            "stable_step_id": step_id,
            "candidate_id": candidate_id,
            "input_hashes": output.get("input_hashes", []),
            "decision_time_evidence_used": output.get("decision_time_evidence_used", []),
            "forbidden_evidence_checked": True,
            "handler_name": spec["handler"],
            "verifier_name": spec["verifier"],
            "output_hash": hash_record(output),
            "status": status,
            "blocker_code": blocker,
            "blocker_reason": output.get("blocker_reason") if blocker else None,
            "next_allowed_action": output.get("next_allowed_action", "continue_static_frontier_graph" if not blocker else "supply_decision_time_safe_evidence"),
            "reopen_conditions": output.get("reopen_conditions", [] if not blocker else ["new_decision_time_safe_evidence"]),
            "prior_state_hash": prior_hash,
        }
        record["post_state_hash"] = hash_record(record)
        prior_hash = record["post_state_hash"]
        records.append(record)
    return records
