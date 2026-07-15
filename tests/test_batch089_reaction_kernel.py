from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from controllergate.reactions.access import AccessLease, AccessState, SourceRegionAccessController, normalize_coordinate
from controllergate.reactions.authority_tokens import REPAIR_LICENSE_REQUIREMENTS, SOURCE_OWNERSHIP_REQUIREMENTS, mint_authority_token
from controllergate.reactions.checkpoint_engine import Checkpoint, CheckpointEngine, Phase
from controllergate.reactions.constitution import classify_variant, conditional_manifestation, deduplicate_symptoms, environmental_mimic_exclusions
from controllergate.reactions.junction import JunctionClass, JunctionContract
from controllergate.reactions.lineage import LineageGraph, LineageNode, inherited_state_handover
from controllergate.reactions.resource_ledger import ResourceLedger, classify_residue
from controllergate.reactions.truth_maintenance import Constraint, EpistemicState, Fact, TruthMaintenanceSystem


def lease(operation: str = "READ") -> AccessLease:
    return AccessLease("l", "c", "r", "s", "t", operation, "source.py", (datetime.now(timezone.utc) + timedelta(minutes=1)).isoformat(), "budget", "parent")


def test_diagnostic_access_is_read_only() -> None:
    controller = SourceRegionAccessController()
    assert controller.diagnostic(lease()).state is AccessState.READ_ONLY_DIAGNOSTIC


def test_write_access_requires_all_tokens() -> None:
    with pytest.raises(ValueError, match="evidence incomplete"):
        SourceRegionAccessController().license_write(lease("WRITE"), ["SOURCE_OWNERSHIP_TOKEN"], human_approval=True, rollback_ready=True)


def test_write_access_is_single_use() -> None:
    controller = SourceRegionAccessController(); value = lease("WRITE")
    controller.license_write(value, ["SOURCE_OWNERSHIP_TOKEN", "REPAIR_LICENSE_TOKEN", "TEST_TREE_IMMUTABLE_TOKEN"], human_approval=True, rollback_ready=True)
    controller.consume(value.lease_id)
    with pytest.raises(ValueError, match="already consumed"):
        controller.consume(value.lease_id)


def test_coordinate_normalization_rejects_invalid_line() -> None:
    with pytest.raises(ValueError):
        normalize_coordinate(0, 0, ast_identity="a", source_hash="h")


def test_unresolved_checkpoint_globally_blocks_transition() -> None:
    engine = CheckpointEngine(); checkpoint = Checkpoint("c", Phase.LICENSING, "s", "r", "t", "e", "INTERVENTION", "condition", "rollback", "proof", "new evidence")
    engine.register(checkpoint)
    assert engine.transition_allowed("INTERVENTION")["status"] == "BLOCK"
    engine.resolve("c", "proof")
    assert engine.transition_allowed("INTERVENTION")["status"] == "PASS"


def test_once_only_authorization_rejects_reuse() -> None:
    engine = CheckpointEngine(); engine.consume_once("a")
    with pytest.raises(ValueError):
        engine.consume_once("a")


def test_junction_blocks_wrong_identity_and_forbidden_field() -> None:
    contract = JunctionContract("j", JunctionClass.BOUNDED_MESSAGE_CHANNEL, "p", "c", "v1", frozenset({"value"}), frozenset({"secret"}), 200, 1, 0, True)
    result = contract.verify({"secret": "x"}, producer="wrong", consumer="c")
    assert result["status"] == "BLOCK"
    assert "junction_identity_mismatch" in result["errors"]


def test_resource_ledger_does_not_commit_over_budget_request() -> None:
    limits = {name: 0 for name in ("wall_time_ms", "cpu_ms", "memory_bytes", "disk_bytes", "network_requests", "network_bytes", "subprocesses", "probes", "retries", "workers", "artifacts", "log_bytes", "temporary_workspaces")}; limits["probes"] = 1
    ledger = ResourceLedger(limits)
    assert ledger.consume("one", {"probes": 1})["status"] == "PASS"
    assert ledger.consume("two", {"probes": 1})["status"] == "BLOCK"
    assert ledger.consumed["probes"] == 1


def test_proof_residue_is_retained() -> None:
    assert classify_residue("proof_record", active_reference=False, evidence_required=False, rebuildable=False) == "RETAIN_EVIDENCE"


def test_lineage_rejects_missing_parent() -> None:
    graph = LineageGraph()
    with pytest.raises(ValueError, match="parent missing"):
        graph.add(LineageNode("child", "decision", ("missing",), "e", "s", "d", "direct", "a", "r", "reason"))


def test_lineage_handover_retains_protocol_and_degrades_cache() -> None:
    result = inherited_state_handover([{"type": "protocol"}, {"type": "cache"}])
    assert result["committed_state"] == "AUTHORITY_HANDOVER_COMMITTED"
    assert len(result["retained"]) == 1 and len(result["degraded_or_quarantined"]) == 1


def test_implication_false_antecedent_does_not_infer_false_consequent() -> None:
    facts = [Fact("a", "c", "r", "f", EpistemicState.FALSE_DIRECT), Fact("b", "c", "r", "f", EpistemicState.UNKNOWN)]
    result = TruthMaintenanceSystem(facts, [Constraint("i", "implication", ("a", "b"))]).fixed_point()
    assert result["status"] == "PASS"
    assert next(row for row in result["facts"] if row["fact_id"] == "b")["state"] == "UNKNOWN"


@pytest.mark.parametrize("kind,k,states,expected", [
    ("exactly_k", 1, (EpistemicState.TRUE_DIRECT, EpistemicState.UNKNOWN), "FALSE_INFERRED"),
    ("at_least_k", 2, (EpistemicState.TRUE_DIRECT, EpistemicState.UNKNOWN), "TRUE_INFERRED"),
    ("at_most_k", 0, (EpistemicState.UNKNOWN, EpistemicState.UNKNOWN), "FALSE_INFERRED"),
])
def test_cardinality_fixed_point(kind: str, k: int, states: tuple[EpistemicState, ...], expected: str) -> None:
    facts = [Fact(str(index), "c", "r", "f", state) for index, state in enumerate(states)]
    result = TruthMaintenanceSystem(facts, [Constraint("k", kind, ("0", "1"), k)]).fixed_point()
    assert any(row["state"] == expected for row in result["facts"])


def test_contradiction_learns_nogood_and_preserves_direct_on_backtrack() -> None:
    facts = [Fact("a", "c", "r", "f", EpistemicState.TRUE_DIRECT), Fact("b", "c", "r", "f", EpistemicState.TRUE_DIRECT)]
    system = TruthMaintenanceSystem(facts, [Constraint("m", "mutual_exclusion", ("a", "b"))])
    assert system.fixed_point()["status"] == "CONTRADICTED"
    assert system.backtrack()["direct_evidence_preserved"] is True


def test_authority_token_requires_each_named_evidence_item() -> None:
    with pytest.raises(ValueError, match="candidate_identity"):
        mint_authority_token("SOURCE_OWNERSHIP_TOKEN", candidate_id="c", run_id="r", frame_hash="f", evidence={}, verifier="v", expires_at="x", nonce="n")


def test_source_and_repair_tokens_have_distinct_requirements() -> None:
    source_evidence = {name: name for name in SOURCE_OWNERSHIP_REQUIREMENTS}
    source = mint_authority_token("SOURCE_OWNERSHIP_TOKEN", candidate_id="c", run_id="r", frame_hash="f", evidence=source_evidence, verifier="v", expires_at="x", nonce="n1")
    repair_evidence = {name: name for name in REPAIR_LICENSE_REQUIREMENTS}; repair_evidence["source_ownership_token"] = source.token_hash
    repair = mint_authority_token("REPAIR_LICENSE_TOKEN", candidate_id="c", run_id="r", frame_hash="f", evidence=repair_evidence, verifier="v", expires_at="x", nonce="n2")
    assert source.token_type != repair.token_type and source.token_hash != repair.token_hash


def test_environmental_mimic_and_variant_helpers() -> None:
    assert environmental_mimic_exclusions({"provider": True})["status"] == "BLOCK"
    assert conditional_manifestation([True, False])["causal_authority"] is False
    assert classify_variant(source_changed=True, tests_changed=True).value == "TEST_ONLY_FORBIDDEN"
    assert deduplicate_symptoms([{"causal_event_hash": "a", "patch_hash": "b", "symptom_id": "x"}])["causal_episode_count"] == 1
