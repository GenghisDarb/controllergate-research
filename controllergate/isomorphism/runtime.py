from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from controllergate.execution.stage_registry import registered_stage
from controllergate.state.integrity import canonical_hash
from controllergate.state.repository import ControllerStateRepository

from .primitives import PRIMITIVE_CONTRACTS, apply_primitive, conformance_event


def execute_structured_scenario(scenario: dict[str, Any], database: str | Path, *, platform: str) -> dict[str, Any]:
    """Execute a non-authorizing candidate scenario through canonical state services."""
    # Candidate simulations mature a nonauthorizing plan through the existing
    # canonical stage contract; Batch093 does not expand the frozen stage set.
    stage = registered_stage("plan_maturation")
    event = dict(scenario.get("source_event") or conformance_event())
    event["source_occurrence_identity"] = scenario["source_occurrence_identity"]
    state: dict[str, Any] = {"primitive_trace": []}
    positive = []
    negative = []
    for primitive in scenario["primitive_ids"]:
        result = apply_primitive(primitive, state, event)
        positive.append(result)
        if result["status"] == "PASS":
            state = result["state"]
        malformed = dict(event)
        malformed.pop(PRIMITIVE_CONTRACTS[primitive]["required_event_field"], None)
        negative.append(apply_primitive(primitive, state, malformed))
    mechanism_status = "PASS" if all(row["status"] == "PASS" for row in positive) and all(row["status"] == "BLOCK" for row in negative) else "FAIL"
    run_id = f"reactome-{canonical_hash([scenario['scenario_id'], platform])[:24]}"
    candidate_id = str(scenario["source_stable_id"])
    repository = ControllerStateRepository(database)
    try:
        try:
            repository.create_run(run_id, candidate_id, {"scenario_id": scenario["scenario_id"], "platform": platform, "authority": "shadow_non_authorizing"})
        except Exception:
            repository.load_run(run_id)
        outcome_payload = {
            "scenario_id": scenario["scenario_id"], "source_stable_id": candidate_id, "platform": platform,
            "primitive_trace": state.get("primitive_trace", []), "mechanism_status": mechanism_status,
            "positive_execution_count": len(positive), "negative_control_count": len(negative),
            "authority": "shadow_non_authorizing",
        }
        outcome_hash = canonical_hash(outcome_payload)
        stage_event = repository.complete_stage(run_id, stage.stage_id, [], [outcome_hash], worker=stage.executor_identity)
        now = datetime.now(timezone.utc).isoformat()
        outcome_id = canonical_hash([run_id, "mechanism-outcome", outcome_hash])
        assertion_id = canonical_hash([run_id, "test-assertion", mechanism_status])
        receipt_id = canonical_hash([run_id, stage.stage_id, outcome_id, assertion_id])
        repository.connection.execute(
            "INSERT OR REPLACE INTO mechanism_outcomes VALUES (?,?,?,?,?,?,?)",
            (outcome_id, run_id, "reactome_structured_candidate", mechanism_status, None if mechanism_status == "PASS" else "primitive_contract_failed", json.dumps([outcome_hash]), now),
        )
        repository.connection.execute(
            "INSERT OR REPLACE INTO test_assertions VALUES (?,?,?,?,?,?)",
            (assertion_id, run_id, outcome_id, "PASS" if mechanism_status == "PASS" else "FAIL", "PASS", now),
        )
        receipt = {
            "receipt_id": receipt_id, "run_id": run_id, "producer_component": stage.executor_identity,
            "verifier_identity": stage.verifier_identity, "execution_depth": "canonical_stage_sqlite_execution",
            "mechanism_status": mechanism_status, "test_assertion_status": "PASS" if mechanism_status == "PASS" else "FAIL",
            "source_stable_id": candidate_id, "scenario_id": scenario["scenario_id"], "platform": platform,
            "stage_event_hash": stage_event["event_hash"], "output_hash": outcome_hash,
            "authority_allowed": "candidate simulation", "authority_forbidden": ["repair authorization", "production promotion"],
        }
        repository.connection.execute(
            "INSERT OR REPLACE INTO execution_receipts VALUES (?,?,?,?,?,?,?,?,?)",
            (receipt_id, run_id, stage.executor_identity, stage.verifier_identity, "canonical_stage_sqlite_execution", mechanism_status, receipt["test_assertion_status"], json.dumps(receipt, sort_keys=True), now),
        )
        repository.connection.commit()
        module_origin = str(Path(__file__).resolve())
        return {
            **outcome_payload, "status": mechanism_status, "run_id": run_id, "stage_id": stage.stage_id,
            "stage_event_hash": stage_event["event_hash"], "execution_receipt_id": receipt_id,
            "database": str(Path(database).resolve()), "module_origin": module_origin,
            "installed_site_packages_origin": "site-packages" in module_origin.replace("\\", "/").lower(),
            "external_operation_count": 0, "unbrokered_external_operation_count": 0,
        }
    finally:
        repository.close()
