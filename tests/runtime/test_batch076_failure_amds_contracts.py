from __future__ import annotations

from datetime import datetime, timedelta, timezone

from controllergate.amds.observation_contract_v2 import REQUIRED, validate_observation
from controllergate.amds.posterior_state_v3 import HYPOTHESES, apply_observation, entropy, initialize_posterior
from controllergate.amds.probe_execution_ledger import ProbeLedger, authorize_probe
from controllergate.runtime.failure_contract import classify_failure, duplicate_failure_contract
from controllergate.runtime.failure_signature_v2 import EMPTY_OUTPUT_HASH, semantic_failure_signature
from controllergate.runtime.timeout_diagnostics import classify_timeout_evidence, timeout_stage_plan


def test_empty_output_is_labeled_not_promoted() -> None:
    result = semantic_failure_signature("", target="tests/test_x.py::test_x")
    assert result["signature_label"] == "EMPTY_OUTPUT_HASH"
    assert result["normalized_output_sha256"] == EMPTY_OUTPUT_HASH
    assert result["semantic_failure_signature"] is None


def test_nonempty_candidate_failure_requires_ownership() -> None:
    without = classify_failure(returncode=1, output="AssertionError: bad", target="t")
    with_owner = classify_failure(returncode=1, output="Traceback\nAssertionError: bad", target="t", ownership_events=["/source/pkg.py:10"])
    assert without["classification"] != "CANDIDATE_FAILURE_REPRODUCED"
    assert with_owner["classification"] == "CANDIDATE_FAILURE_REPRODUCED"
    assert with_owner["signature"]["semantic_failure_signature"]


def test_duplicate_timeout_is_not_candidate_failure() -> None:
    first = classify_failure(returncode=124, output="", target="t", timed_out=True)
    second = classify_failure(returncode=124, output="", target="t", timed_out=True)
    result = duplicate_failure_contract(first, second)
    assert result["terminal_classification"] == "RESOURCE_TIMEOUT_REPRODUCED"
    assert result["candidate_failure_reproduced"] is False


def test_process_signal_is_distinct() -> None:
    result = classify_failure(returncode=-9, output="terminated", target="t", process_signal=9)
    assert result["classification"] == "PROCESS_SIGNAL_REPRODUCED"


def test_timeout_classifier_is_causal_and_bounded() -> None:
    assert [item["timeout_seconds"] for item in timeout_stage_plan()] == [60, 180, 600]
    assert classify_timeout_evidence(stacks=["/source/pkg.py"], subprocesses=[], last_step="loop", fixture_completed=True, direct_invocation_stalled=True) == "SOURCE_LOOP_OR_DEADLOCK"
    assert classify_timeout_evidence(stacks=[], subprocesses=[], last_step=None, fixture_completed=False, direct_invocation_stalled=None) == "HARNESS_FIXTURE_STALL"


def _observation() -> dict:
    return {key: "value" for key in REQUIRED} | {
        "probe_id": "p1", "executor_id": "e1", "semantic_fact": True,
        "custody_verification": "PASS", "semantic_verification": "PASS",
        "input_evidence_hashes": ["a" * 64], "supported_hypotheses": ["source_owned_behavior_defect"],
        "refuted_hypotheses": [], "unchanged_hypotheses": [],
    }


def test_null_and_mismatched_observations_reject() -> None:
    record = _observation(); record["semantic_fact"] = None
    assert validate_observation(record)["accepted"] is False
    assert validate_observation(_observation(), expected_probe_id="other")["accepted"] is False
    assert validate_observation(_observation(), expected_executor_id="other")["accepted"] is False


def test_semantic_verifier_failure_rejects() -> None:
    record = _observation(); record["semantic_verification"] = "BLOCK"
    assert "semantic_verifier_failed" in validate_observation(record)["reasons"]


def test_posterior_initializes_all_hypotheses() -> None:
    state = initialize_posterior()
    assert set(state["hypotheses"]) == set(HYPOTHESES)
    assert entropy(state) > 0


def test_deterministic_elimination_is_informative() -> None:
    state = initialize_posterior()
    result = apply_observation(state, evidence_hash="a" * 64, supported=["source_owned_behavior_defect"], refuted=["environment_owned"], likelihood_basis="DETERMINISTIC_CONTRACT")
    assert result["informative"] and result["state"]["hypotheses"]["environment_owned"]["posterior_value"] == 0


def test_symbolic_unknown_can_preserve_explicitly() -> None:
    state = initialize_posterior()
    result = apply_observation(state, evidence_hash="b" * 64, supported=[], refuted=[], likelihood_basis="NOT_ESTABLISHED")
    assert result["noninformative_preservation"] and result["likelihood_basis"] == "NOT_ESTABLISHED"


def test_probe_nonce_event_and_repeated_probe_guards() -> None:
    ledger = ProbeLedger(); expires = (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat()
    auth = authorize_probe(candidate_id="c", candidate_sha="a" * 40, board_hash="b" * 64, probe_id="p", executor_id="e", nonce="n1", resource_budget={"seconds": 1}, expires_at=expires)
    first = ledger.spend(auth, probe_id="p", executor_id="e", board_hash="b" * 64)
    assert first["status"] == "PASS" and len(ledger.events) == 1 and len(ledger.spent_nonces) == 1
    assert ledger.spend(auth, probe_id="p", executor_id="e", board_hash="b" * 64)["status"] == "REJECT"
    auth2 = authorize_probe(candidate_id="c", candidate_sha="a" * 40, board_hash="b" * 64, probe_id="p", executor_id="e", nonce="n2", resource_budget={"seconds": 1}, expires_at=expires)
    assert ledger.spend(auth2, probe_id="p", executor_id="e", board_hash="b" * 64)["status"] == "REJECT"
    assert ledger.spend(auth2, probe_id="p", executor_id="e", board_hash="b" * 64, replay_reason="independent_duplicate")["status"] == "PASS"


def test_probe_authorization_identity_guards() -> None:
    ledger = ProbeLedger(); expires = (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat()
    auth = authorize_probe(candidate_id="c", candidate_sha="a" * 40, board_hash="b" * 64, probe_id="p", executor_id="e", nonce="n", resource_budget={}, expires_at=expires)
    assert ledger.spend(auth, probe_id="wrong", executor_id="e", board_hash="b" * 64)["status"] == "REJECT"
    assert ledger.spend(auth, probe_id="p", executor_id="wrong", board_hash="b" * 64)["status"] == "REJECT"
    assert ledger.spend(auth, probe_id="p", executor_id="e", board_hash="wrong")["status"] == "REJECT"
