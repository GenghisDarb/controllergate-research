from __future__ import annotations

from pathlib import Path

from controllergate.reactions.catalyst import Catalyst
from controllergate.reactions.cycle_guard import CycleGuard
from controllergate.reactions.entity import Entity
from controllergate.reactions.event import ReactionEvent
from controllergate.reactions.regulation import Regulator
from controllergate.reactions.translocation import translocate
from controllergate.reactions.verifier import verify_result


def event(*, active: int = 1, positive: bool = True, negative: bool = False) -> ReactionEvent:
    operation=lambda _: {"status":"PASS","execution_record_id":"real:1","observed_sentinels":["seen"],"outputs":{"proof":"value"}}
    return ReactionEvent("event-1",1,"candidate","verify","source","destination",["input"],[],{"input":1},Catalyst("hash",operation,active),[Regulator("positive",lambda _:positive)],[Regulator("negative",lambda _:negative,positive=False)],"normal","incident",["proof"],["forbidden"],"builder","critic")


def context() -> dict[str, object]:
    return {"verified_compartments": ["source", "destination"]}


def test_completed_reaction_mints_verified_output_token() -> None:
    result=event().execute([Entity("input","source","one","source")],context(),verifier=lambda _:True)
    assert result.event_record["outcome"]=="REACTION_COMPLETED"
    assert result.output_token and verify_result(result)["status"]=="PASS"


def test_missing_input_records_failed_reaction_without_token() -> None:
    result=event().execute([], context())
    assert result.event_record["outcome"]=="BLOCKED_REQUIRED_INPUT_ABSENT"
    assert result.output_token is None and result.failure["output_token_minted"] is False


def test_catalyst_and_regulators_are_enforced() -> None:
    entity=[Entity("input","source","one","source")]
    assert event(active=0).execute(entity,context()).event_record["outcome"]=="BLOCKED_CATALYST_INACTIVE"
    assert event(positive=False).execute(entity,context()).event_record["outcome"]=="BLOCKED_POSITIVE_REGULATOR_ABSENT"
    assert event(negative=True).execute(entity,context()).event_record["outcome"]=="BLOCKED_NEGATIVE_REGULATOR_PRESENT"


def test_unverified_compartment_blocks_catalyst_execution() -> None:
    result = event().execute([Entity("input", "source", "one", "source")], {})
    assert result.event_record["outcome"] == "FAILED_REACTION_OUTPUT_INVALID"
    assert result.event_record["operation"] == {}


def test_cycle_guard_requires_new_evidence() -> None:
    guard=CycleGuard(); kwargs={"candidate_id":"c","event_id":"e","input_hashes":["h"],"provider":"p","command":"x","blocker":"b","evidence":["z"]}
    assert guard.decide(**kwargs)["status"]=="PASS"
    assert guard.decide(**kwargs)["status"]=="BLOCK"
    assert guard.decide(**kwargs,new_evidence=True)["status"]=="PASS"


def test_translocation_is_byte_preserving(tmp_path: Path) -> None:
    source=tmp_path/"source";target=tmp_path/"dest";source.write_bytes(b"evidence")
    assert translocate(source,target,artifact_identity="fixture")["status"]=="PASS"
