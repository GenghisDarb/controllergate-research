from __future__ import annotations

import json
import inspect
import importlib
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from controllergate.execution.stage_registry import registered_stage
from controllergate.pathways.canonical_maintenance import (
    execute_simulation_stage,
    execute_stage,
    freeze_anchors,
    pathway_for_mode,
    verify_simulation_stage,
)
from controllergate.state.integrity import canonical_hash
from controllergate.state.repository import ControllerStateRepository

from .behavior import execute_behavior
from .primitives import PRIMITIVE_CONTRACTS, conformance_event


def execute_structured_scenario(scenario: dict[str, Any], database: str | Path, *, platform: str) -> dict[str, Any]:
    """Execute a non-authorizing candidate scenario through canonical state services."""
    # Candidate simulations mature a nonauthorizing plan through the existing
    # canonical stage contract; Batch093 does not expand the frozen stage set.
    definition = registered_stage("plan_maturation")
    stage = pathway_for_mode("mechanism_rehearsal", ["plan_maturation"])[0]
    event = dict(scenario.get("source_event") or conformance_event())
    event["source_occurrence_identity"] = scenario["source_occurrence_identity"]
    state: dict[str, Any] = {"primitive_trace": []}
    positive = []
    negative = []
    for primitive in scenario["primitive_ids"]:
        result = execute_behavior(primitive, state, event)
        positive.append(result)
        if result["status"] == "PASS":
            state = result["state"]
        malformed = dict(event)
        malformed.pop(PRIMITIVE_CONTRACTS[primitive]["required_event_field"], None)
        negative.append(execute_behavior(primitive, state, malformed))
    adversarial_event = dict(event)
    adversarial_event["requested_authority"] = "repair_authority"
    adversarial = execute_behavior(scenario["primitive_ids"][0], state, adversarial_event)
    mechanism_status = "PASS" if all(row["status"] == "PASS" for row in positive) and all(row["status"] == "BLOCK" for row in negative) and adversarial["status"] == "BLOCK" else "FAIL"
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
            "adversarial_control_status": adversarial["status"],
            "authority": "shadow_non_authorizing",
        }
        outcome_hash = canonical_hash(outcome_payload)
        anchors = freeze_anchors({
            "candidate_incident_identity": scenario["source_occurrence_identity"],
            "source_and_test_tree_identity": scenario.get("source_graph_hash", canonical_hash(event)),
            "provider_runtime_abi_identity": f"installed:{platform}",
            "target_and_command_authority": "controllergate:reactome-run",
            "proof_claim_release_parent": "controllergate-rpir-v2.1",
        })
        execution = execute_simulation_stage(
            stage, candidate_id=candidate_id, run_id=run_id, source_event=event,
            mechanism_results=positive, anchor_hash=anchors["anchor_hash"],
        )
        verification = verify_simulation_stage(stage, execution, source_event=event, mechanism_results=positive)
        shortcut_negative = verify_simulation_stage(
            stage, {**execution, "producer_executed": False}, source_event=event, mechanism_results=positive,
        )
        direct_output = {**execution, "verified": verification["verified"], "anchor_hash": anchors["anchor_hash"]}
        token = execute_stage(stage, candidate_id=candidate_id, run_id=run_id, prior_tokens=[], anchors=anchors, direct_output=direct_output)
        stage_event = repository.commit_stage(
            run_id, stage.stage_id, [], token.record(), direct_output,
            worker=execution["producer_identity"],
        )
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
            "receipt_id": receipt_id, "run_id": run_id, "producer_component": execution["producer_identity"],
            "verifier_identity": verification["verifier_identity"], "execution_depth": "canonical_executor_verifier_sqlite_commit",
            "mechanism_status": mechanism_status, "test_assertion_status": "PASS" if mechanism_status == "PASS" else "FAIL",
            "source_stable_id": candidate_id, "scenario_id": scenario["scenario_id"], "platform": platform,
            "stage_event_hash": stage_event["event_hash"], "output_hash": outcome_hash,
            "stage_execution_receipt": execution, "stage_verification_receipt": verification,
            "authority_allowed": "candidate simulation", "authority_forbidden": ["repair authorization", "production promotion"],
        }
        repository.connection.execute(
            "INSERT OR REPLACE INTO execution_receipts VALUES (?,?,?,?,?,?,?,?,?)",
            (receipt_id, run_id, execution["producer_identity"], verification["verifier_identity"], "canonical_executor_verifier_sqlite_commit", mechanism_status, receipt["test_assertion_status"], json.dumps(receipt, sort_keys=True), now),
        )
        repository.connection.commit()
        module_origin = str(Path(__file__).resolve())
        component_modules = {
            "cli": "controllergate.cli",
            "rpir": "controllergate.reactome_ir.schema",
            "compiler": "controllergate.isomorphism.value_bound",
            "primitive_runtime": "controllergate.isomorphism.behavior",
            "state_repository": "controllergate.state.repository",
            "stage_executor_and_verifier": "controllergate.pathways.canonical_maintenance",
            "broker": "controllergate.execution.execution_broker",
        }
        component_origins = {
            name: str(Path(inspect.getsourcefile(importlib.import_module(module_name)) or "").resolve())
            for name, module_name in component_modules.items()
        }
        return {
            **outcome_payload, "status": mechanism_status, "run_id": run_id, "stage_id": stage.stage_id,
            "stage_event_hash": stage_event["event_hash"], "execution_receipt_id": receipt_id,
            "database": str(Path(database).resolve()), "module_origin": module_origin,
            "installed_site_packages_origin": "site-packages" in module_origin.replace("\\", "/").lower(),
            "component_origins": component_origins,
            "all_component_origins_site_packages": all("site-packages" in value.replace("\\", "/").lower() for value in component_origins.values()),
            "stage_execution_receipt": execution,
            "stage_verification_receipt": verification,
            "canonical_stage_shortcut_negative_control": {"status": "PASS" if shortcut_negative["status"] == "FAIL" else "FAIL", "verification": shortcut_negative},
            "external_operation_count": 0, "unbrokered_external_operation_count": 0,
        }
    finally:
        repository.close()
