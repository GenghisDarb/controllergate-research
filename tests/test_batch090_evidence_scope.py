from __future__ import annotations

import json
from pathlib import Path

import pytest

from controllergate.execution.scoped_evidence import ClaimBinding, ExecutionReceipt, claim_graph


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs" / "post_v2_37_hardening_batch090_evidence_delaundering_installed_vertical_closure"


def receipt(tmp_path: Path) -> ExecutionReceipt:
    raw = tmp_path / "raw.log"
    raw.write_text("observed\n", encoding="utf-8")
    import hashlib
    return ExecutionReceipt.create(
        producer_component="producer", producer_version="1", operation_or_reaction_id="op",
        candidate_id="candidate-a", run_id="run-a", frame_hash="f" * 64,
        input_evidence_hashes={"input": "a" * 64}, raw_output_hashes={"raw.log": hashlib.sha256(raw.read_bytes()).hexdigest()},
        mechanism_observed_status="BLOCK", test_assertion_status="TEST_PASS",
        execution_depth="IN_PROCESS_INTEGRATION_FIXTURE", broker_record_hashes=(),
        sqlite_transaction_identity="t" * 64, verifier_identity="independent-verifier",
        semantic_scopes_allowed=("fixture_claim",), semantic_scopes_forbidden=("installed_claim",),
    )


def test_mechanism_block_is_not_laundered_by_passing_assertion(tmp_path: Path) -> None:
    value = receipt(tmp_path)
    assert value.mechanism_observed_status == "BLOCK"
    assert value.test_assertion_status == "TEST_PASS"


def test_execution_depth_and_semantic_scope_are_enforced(tmp_path: Path) -> None:
    value = receipt(tmp_path)
    binding = ClaimBinding("c", "installed_claim", "candidate-a", "run-a", "f" * 64, "producer", value.receipt_id, "INSTALLED_CLI_EXECUTION", "independent-verifier", ("raw.log",))
    with pytest.raises(ValueError):
        binding.validate(value, tmp_path)


def test_candidate_substitution_and_missing_raw_output_are_rejected(tmp_path: Path) -> None:
    value = receipt(tmp_path)
    wrong = ClaimBinding("c", "fixture_claim", "candidate-b", "run-a", "f" * 64, "producer", value.receipt_id, "IN_PROCESS_INTEGRATION_FIXTURE", "independent-verifier", ("raw.log",))
    with pytest.raises(ValueError):
        wrong.validate(value, tmp_path)
    (tmp_path / "raw.log").unlink()
    missing = ClaimBinding("d", "fixture_claim", "candidate-a", "run-a", "f" * 64, "producer", value.receipt_id, "IN_PROCESS_INTEGRATION_FIXTURE", "independent-verifier", ("raw.log",))
    with pytest.raises(ValueError):
        missing.validate(value, tmp_path)


def test_claim_graph_and_batch089_reconciliation_are_scoped() -> None:
    graph = json.loads((OUT / "claim_to_evidence_graph.json").read_text(encoding="utf-8"))
    scope = json.loads((OUT / "evidence_scope_audit.json").read_text(encoding="utf-8"))
    depth = json.loads((OUT / "batch089_evidence_depth_reconciliation.json").read_text(encoding="utf-8"))
    assert graph["status"] == "PASS" and graph["release_authority_edges"] == 0
    assert scope["mechanism_test_status_separated"] and scope["missing_raw_output_count"] == 0
    assert depth["batch089_scenario_count"] == 60
    assert depth["batch089_scenario_corrected_classification"] == "IN_PROCESS_INTEGRATION_FIXTURE"


def test_claim_graph_rejects_missing_receipt(tmp_path: Path) -> None:
    value = receipt(tmp_path)
    binding = ClaimBinding("missing", "fixture_claim", "candidate-a", "run-a", "f" * 64, "producer", "0" * 64, "IN_PROCESS_INTEGRATION_FIXTURE", "independent-verifier", ("raw.log",))
    assert claim_graph([value], [binding])["status"] == "BLOCK"
