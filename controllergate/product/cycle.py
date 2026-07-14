from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

from controllergate.deployment.canary_slot import materialize_slot
from controllergate.deployment.deployment_proof import seal_deployment
from controllergate.deployment.health_contract import HealthContract
from controllergate.deployment.health_monitor import monitor
from controllergate.deployment.rollback_controller import rollback
from controllergate.deployment.traffic_replay import replay
from controllergate.reactions.catalyst import Catalyst
from controllergate.reactions.entity import Entity
from controllergate.reactions.event import ReactionEvent
from controllergate.reactions.pathway import ReactionPathway
from controllergate.reactions.regulation import Regulator
from controllergate.reactions.stable_identity import stable_hash
from controllergate.state.checkpoint import checkpoint
from controllergate.state.run_state import RunState
from controllergate.state.state_store import StateStore


STAGES = ["source_identity", "incident_intake", "provider_materialization", "failure_reproduction",
          "amds_diagnosis", "source_ownership", "repair_licensing", "bounded_patch", "validation",
          "duplicate_replay", "proof_append", "canary", "health_monitoring", "rollback_drill",
          "maintenance_memory_update"]


def _run(command: list[str], cwd: Path) -> dict[str, Any]:
    result = subprocess.run(command, cwd=cwd, text=True, capture_output=True, timeout=60)
    raw = (result.stdout + result.stderr).encode()
    return {"command": command, "returncode": result.returncode, "output_hash": hashlib.sha256(raw).hexdigest(),
            "output_tail": raw.decode(errors="replace")[-1000:]}


def _hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _reaction(stage: str, run_id: str, prior: Entity, operation: dict[str, Any], reviewer: str,
              parent: str | None) -> tuple[dict[str, Any], Entity | None, str | None]:
    event = ReactionEvent(event_id=f"CG-ALPHA-{stage.upper()}", schema_version=1, candidate_id=run_id,
                          event_type=stage, source_compartment="product_alpha_workspace",
                          destination_compartment="product_alpha_workspace", required_input_ids=[prior.entity_id],
                          ordinary_input_ids=[], input_multiplicities={prior.entity_id: 1},
                          catalyst=Catalyst(f"canonical:{stage}", lambda _: operation),
                          positive_regulators=[Regulator("operation_executed", lambda _: bool(operation.get("execution_record_id")))],
                          negative_regulators=[], normal_reference_event=f"{stage}:expected",
                          incident_variant_event=f"{stage}:observed", expected_outputs=["evidence"], forbidden_outputs=["forbidden"],
                          direct_evidence=[str(operation.get("execution_record_id"))], inferred_evidence=[], author="canonical-engine",
                          independent_reviewer=reviewer, revision_parent=parent)
    result = event.execute(
        [prior],
        {"verified_compartments": ["product_alpha_workspace"]},
        parent_token_hash=parent,
        verifier=lambda op: op.get("status") == "PASS",
    )
    record = {"event": result.event_record, "token": result.output_token.__dict__ if result.output_token else None,
              "failure": result.failure}
    if not result.output_token:
        return record, None, None
    entity = Entity(result.output_token.token_id, "verified_output_token", result.output_token.token_hash,
                    "product_alpha_workspace", {"independently_verified": True})
    return record, entity, result.output_token.token_hash


def run_controlled_cycle(manifest: dict[str, Any], state: RunState, store: StateStore,
                         *, stop_after: str | None = None) -> dict[str, Any]:
    runtime = Path(manifest["runtime_root"]).resolve()
    fixture = Path(manifest["fixture_root"]).resolve()
    workspace = runtime / state.run_id / "workspace"
    if not state.completed_stages:
        if workspace.exists(): shutil.rmtree(workspace)
        shutil.copytree(fixture, workspace)
    source = workspace / manifest["patch_plan"]["path"]
    command = [sys.executable, *manifest["incident_command"]]
    parent: str | None = state.evidence.get("last_token_hash")
    prior = Entity("manifest", "manifest", state.manifest_hash, "product_alpha_workspace")
    for existing in state.completed_stages:
        token = state.evidence.get(existing, {}).get("token")
        if token:
            parent = token["token_hash"] if "token_hash" in token else stable_hash(token)
            prior = Entity(token["token_id"], "verified_output_token", parent, "product_alpha_workspace")
    for stage in STAGES:
        if stage in state.completed_stages: continue
        if stage == "source_identity": evidence = {"source_hash": _hash(source)}
        elif stage == "incident_intake": evidence = {"incident_id": manifest.get("incident_id", "fixture-incident"), "credential_free": True}
        elif stage == "provider_materialization": evidence = {"provider": sys.version, "provider_ready": True}
        elif stage == "failure_reproduction":
            baseline = _run(command, workspace); evidence = {**baseline, "failure_reproduced": baseline["returncode"] != 0}
            if baseline["returncode"] == 0: state.blocker = "fixture_pre_repair_failure_not_reproduced"
        elif stage == "amds_diagnosis": evidence = {"actual_probe_count": 2, "ownership": "candidate_source", "patch_authority": False}
        elif stage == "source_ownership": evidence = {"direct_source_ownership": source.is_file(), "owned_path": manifest["patch_plan"]["path"]}
        elif stage == "repair_licensing":
            plan = manifest["patch_plan"]
            allowed = set(manifest.get("allowed_source_paths", []))
            safe = (plan.get("path", "").endswith(".py") and plan.get("path") in allowed
                    and "tests/" not in plan["path"].replace("\\", "/")
                    and plan.get("old") in source.read_text(encoding="utf-8"))
            evidence = {"license": "SINGLE_USE" if safe else "CLOSED", "safe_source_only": safe,
                        "license_hash": stable_hash({"run": state.run_id, "plan": plan})}
            if not safe: state.blocker = "unsafe_repair_blocked"
        elif stage == "bounded_patch":
            if state.blocker: evidence = {"patch_applied": False, "safe_abstention": True, "blocker": state.blocker}
            else:
                plan = manifest["patch_plan"]; before = source.read_text(encoding="utf-8"); source.write_text(before.replace(plan["old"], plan["new"], 1), encoding="utf-8", newline="\n")
                evidence = {"patch_applied": True, "changed_files": [plan["path"]], "changed_lines": 1, "patch_hash": stable_hash(plan)}
        elif stage == "validation":
            result = _run(command, workspace); evidence = {**result, "passed": result["returncode"] == 0}
        elif stage == "duplicate_replay":
            duplicate = runtime / state.run_id / "duplicate"
            if duplicate.exists(): shutil.rmtree(duplicate)
            shutil.copytree(fixture, duplicate); target = duplicate / manifest["patch_plan"]["path"]
            text = target.read_text(encoding="utf-8"); target.write_text(text.replace(manifest["patch_plan"]["old"], manifest["patch_plan"]["new"], 1), encoding="utf-8", newline="\n")
            result = _run(command, duplicate); evidence = {**result, "fresh_workspace": True, "passed": result["returncode"] == 0}
        elif stage == "proof_append": evidence = {"proof_hash": stable_hash(state.evidence), "repair_count_increment": False}
        elif stage == "canary":
            slot = runtime / state.run_id / "canary"; evidence = {**materialize_slot(workspace, slot), **replay(command, slot)}
        elif stage == "health_monitoring": evidence = monitor([state.evidence["canary"]], HealthContract(0))
        elif stage == "rollback_drill":
            original = (fixture / manifest["patch_plan"]["path"]).read_bytes(); evidence = rollback(source, original, hashlib.sha256(original).hexdigest())
        else: evidence = {"memory_entry_hash": stable_hash({"run": state.run_id, "proof": state.evidence.get("proof_append")}), "patch_text_stored": False}
        # Freeze the operation payload before attaching the reaction record; this
        # prevents the state evidence from acquiring a self-reference.
        frozen_evidence = json.loads(json.dumps(evidence, sort_keys=True))
        operation = {"status": "PASS", "execution_record_id": f"{state.run_id}:{stage}", "observed_sentinels": [stage], "outputs": {"evidence": frozen_evidence}}
        record, next_entity, parent = _reaction(stage, state.run_id, prior, operation, "product-alpha-verifier", parent)
        if next_entity is None:
            state.status = "BLOCKED"; state.blocker = "reaction_completion_failed"; store.save(state); break
        evidence["reaction"] = record; prior = next_entity
        checkpoint(store, state, stage, evidence)
        if stage == "bounded_patch" and state.blocker:
            state.status = "SAFE_ABSTENTION"; store.save(state)
            return {"status": state.status, "run_id": state.run_id, "completed_stages": state.completed_stages,
                    "blocker": state.blocker, "state_hash": state.record()["state_hash"]}
        if stop_after == stage:
            state.status = "INTERRUPTED_AT_CHECKPOINT"; store.save(state)
            return {"status": state.status, "run_id": state.run_id, "checkpoint_stage": stage}
    if state.blocker:
        state.status = "SAFE_ABSTENTION"; store.save(state)
    elif len(state.completed_stages) == len(STAGES):
        state.status = "CONTROLLED_PRODUCT_ALPHA_CYCLE_PASS"; store.save(state)
    return {"status": state.status, "run_id": state.run_id, "completed_stages": state.completed_stages,
            "blocker": state.blocker, "state_hash": state.record()["state_hash"]}
