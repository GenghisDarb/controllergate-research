from __future__ import annotations

from datetime import datetime, timedelta, timezone
import json
from pathlib import Path

from controllergate.runtime.execution_authorization import ExecutionAuthorization, ExecutionScope, seal_authorization, verify_authorization
from controllergate.runtime.execution_checkpoint import RuntimeCheckpoint, load_checkpoint, write_checkpoint
from controllergate.runtime.execution_plan import ExecutionPlan, PhaseAuthorization, seal_plan, verify_plan


def authorization(**overrides):
    now = datetime.now(timezone.utc)
    value = ExecutionAuthorization("a", ExecutionScope("candidate", "a" * 40, ("one",), "outputs", ()), "state", "plan", now.isoformat(), (now + timedelta(hours=1)).isoformat(), "nonce", "plan.json", "events.jsonl")
    record = seal_authorization(value); record.update(overrides)
    if overrides: record["authorization_hash"] = record.get("authorization_hash")
    return record


def test_authorization_hash_and_scope_pass() -> None:
    result = verify_authorization(authorization(), candidate_id="candidate", candidate_sha="a" * 40, current_state_hash="state", plan_hash="plan", spent_nonces=set())
    assert result["status"] == "PASS"


def test_candidate_state_and_spent_nonce_block() -> None:
    assert verify_authorization(authorization(), candidate_id="other", candidate_sha="a" * 40, current_state_hash="state", plan_hash="plan", spent_nonces=set())["blocker"] == "authorization_candidate_mismatch"
    assert verify_authorization(authorization(), candidate_id="candidate", candidate_sha="a" * 40, current_state_hash="stale", plan_hash="plan", spent_nonces=set())["blocker"] == "authorization_state_hash_stale"
    assert verify_authorization(authorization(), candidate_id="candidate", candidate_sha="a" * 40, current_state_hash="state", plan_hash="plan", spent_nonces={"nonce"})["blocker"] == "authorization_nonce_spent"


def test_overbroad_authorization_blocks() -> None:
    now = datetime.now(timezone.utc); value = ExecutionAuthorization("a", ExecutionScope("candidate", "a" * 40, ("one",), "outputs", (), patch_authority=True), "state", "plan", now.isoformat(), (now + timedelta(hours=1)).isoformat(), "nonce", "plan.json", "events.jsonl")
    record = seal_authorization(value)
    assert verify_authorization(record, candidate_id="candidate", candidate_sha="a" * 40, current_state_hash="state", plan_hash="plan", spent_nonces=set())["blocker"] == "authorization_scope_overbroad"


def test_plan_rejects_phase_skipping() -> None:
    plan = ExecutionPlan("p", "c", "a" * 40, (PhaseAuthorization("two", "batch068h4_phase", ("one",)),), "context.json")
    assert verify_plan(seal_plan(plan))["blocker"] == "execution_plan_phase_skip"


def test_checkpoint_roundtrip_and_tamper(tmp_path: Path) -> None:
    path = tmp_path / "checkpoint.json"; write_checkpoint(path, RuntimeCheckpoint("c", "p", ("one",), "BLOCK", "x", ("nonce",), "e"))
    assert load_checkpoint(path)["status"] == "PASS"
    value = json.loads(path.read_text()); value["completed_phases"] = ["tampered"]; path.write_text(json.dumps(value), encoding="utf-8")
    assert load_checkpoint(path)["blocker"] == "runtime_checkpoint_hash_invalid"
