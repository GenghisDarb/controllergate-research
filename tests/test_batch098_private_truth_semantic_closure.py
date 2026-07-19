from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

from controllergate.amds.historical_scoring_v8 import classify_join
from controllergate.amds.semantic_closure_v8 import ARM_COMPONENTS, compile_arm_frame, run_iterative_dpp14
from controllergate.evidence.private_truth_v2 import CandidateTruthRecordV2, build_deterministic_bundle, verify_deterministic_bundle
from controllergate.evidence.probe_executor_v2 import resolve_observed_partition


def probe(kind: str, number: int = 1) -> dict:
    subject = f"cell:{number}"
    return {
        "probe_id": f"probe:{kind}:{number}", "candidate_id": "candidate", "run_id": "run",
        "exact_argv": ["{python}", "-c", f"import json;print(json.dumps({{'kind':'{kind}','subject':'{subject}','subject_hash':'x','diagnosis_label_present':False}}))"],
        "cwd_compartment": "TRUTH_BLIND_PROBE_WORKSPACE", "single_use_nonce": f"nonce-{kind}-{number}",
        "semantic_verifier_id": "structured-v2", "predicted_neutral_partitions": {
            f"{kind}_not_observed": [f"hypothesis:{kind}:negative"],
            f"{kind}_observed": [f"hypothesis:{kind}:positive"],
        },
        "structured_result_schema": {"type":"object","required":["kind","subject","subject_hash","diagnosis_label_present"]},
        "probe_kind": kind, "source_cell_or_edge_or_region": subject,
        "partition_rule": {"rule_id":f"{kind}-v2","subject":subject,"positive_when":"kind matches","negative_when":"kind differs"},
    }


def frame() -> dict:
    probes = [probe(kind, index) for index, kind in enumerate(("contact_edge","provider_variation","boundary_dimension","runner_variation","harness_variation","service_variation","expectation_relation","modality_conflict"), 1)]
    return {"candidate_id":"candidate","run_id":"run","frame_id":"frame","legal_probes":probes,"board_cells":[],"board_edges":[],"topology_constraints":[]}


def truth(**updates) -> dict:
    value = {
        "truth_record_id":"truth-v2:x","candidate_id":"candidate","repository":"repo","issue_or_incident_id":"issue:1",
        "frozen_buggy_commit":"1"*40,"candidate_contract_hash":"2"*64,"truth_status":"VERIFIED",
        "scoreability":"SCOREABLE_CAUSAL","causal_class":"SOURCE_OWNED_BEHAVIOR_DEFECT","abstention_expected":False,
        "accepted_fix_identity":"fix","accepted_fix_commit":"3"*40,"accepted_fix_pr":"1","accepted_release":None,
        "primary_truth_sources":("issue",),"supporting_truth_sources":("pr",),"truth_source_hashes":("4"*64,),
        "executed_before_after_differential":True,"regression_test_identity":"test","direct_causal_contact":True,
        "alternative_exclusions":("provider excluded",),"mixed_failure_members":(),"truth_scope":"local",
        "ambiguities":(),"adjudication_required":False,"producer":"producer","independent_verifier":"verifier",
        "producer_receipt":"producer:r","verifier_receipt":"verifier:r","terminal_commitment_hash":"5"*64,
        "truth_created_after_terminal":True,"authority_allowed":"calibration","authority_forbidden":("repair",),
        "reopen_condition":"new evidence",
    }
    value.update(updates)
    return value


def test_partition_key_is_observation_bound_not_first_declared() -> None:
    contract = probe("contact_edge")
    result = resolve_observed_partition(contract, {"kind":"contact_edge","subject":"cell:1","subject_hash":"x"}, "PASS")
    assert list(contract["predicted_neutral_partitions"])[0].endswith("not_observed")
    assert result["partition_key"] == "contact_edge_observed"


def test_unmatched_partition_does_not_propose_fact() -> None:
    result = resolve_observed_partition(probe("contact_edge"), {"kind":"other","subject":"other"}, "BLOCK")
    assert result["partition_key"] is None
    assert result["positive_fact_proposals"] == []


def test_all_arms_compile_independent_distinct_frames() -> None:
    frames = {arm: compile_arm_frame(frame(), arm, [row["probe_id"] for row in frame()["legal_probes"]]) for arm in "ABCDEF"}
    assert len({value["frame_hash"] for value in frames.values()}) == 6
    assert all(tuple(value["component_registry"]) == ARM_COMPONENTS[arm] for arm, value in frames.items())
    assert len(frames["A"]["legal_probes"]) < len(frames["F"]["legal_probes"])


def test_iterative_runtime_executes_one_probe_per_round() -> None:
    value = compile_arm_frame(frame(), "B")
    result = run_iterative_dpp14(value)
    assert result["metrics"]["round_count"] == len(value["legal_probes"])
    assert result["metrics"]["selected_probe_count"] == result["metrics"]["executed_probe_count"]
    assert result["metrics"]["all_probes_preexecuted_before_first_update"] is False
    assert result["metrics"]["selection_update_interleaving"] == "PASS"
    assert result["terminal"]["terminal_class"] == "INSUFFICIENT_EVIDENCE"


def test_constant_baseline_executes_no_probe() -> None:
    value = compile_arm_frame(frame(), "J")
    result = run_iterative_dpp14(value)
    assert result["metrics"]["executed_probe_count"] == 0
    assert result["terminal"]["terminal_class"] == "INSUFFICIENT_EVIDENCE"


def test_truth_record_rejects_forced_unresolved_scoreability() -> None:
    record = CandidateTruthRecordV2(**truth(scoreability="SCOREABLE_CAUSAL", causal_class="UNRESOLVED_TRUTH"))
    with pytest.raises(ValueError):
        record.validate()


def test_deterministic_truth_bundle_rebuild(tmp_path: Path) -> None:
    members = {"candidate_truth_records_v2.jsonl": (json.dumps(truth(), sort_keys=True) + "\n").encode(), "other.json": b"{}\n"}
    first, second = tmp_path / "first.zip", tmp_path / "second.zip"
    assert build_deterministic_bundle(first, members)["sha256"] == build_deterministic_bundle(second, members)["sha256"]
    assert first.read_bytes() == second.read_bytes()
    assert verify_deterministic_bundle(first)["status"] == "PASS"


def test_scoring_distinguishes_abstention_and_unresolved_truth() -> None:
    causal = classify_join("INSUFFICIENT_EVIDENCE", truth())
    assert causal["scoring_outcome"] == "SAFE_BUT_CAUSALLY_INCORRECT_ABSTENTION"
    assert causal["correct"] is False
    unresolved = classify_join("RUNNER_OWNED", truth(scoreability="NOT_SCOREABLE", causal_class="UNRESOLVED_TRUTH", truth_status="UNRESOLVED"))
    assert unresolved["scoring_outcome"] == "TRUTH_UNRESOLVED"
    assert unresolved["correct"] is None


def test_flat_truth_dictionary_is_not_supported_by_finalizer() -> None:
    text = (Path(__file__).parents[1] / "scripts/finalize_batch098_hybrid_private_run.py").read_text(encoding="utf-8")
    assert "expected_by_candidate" not in text
    assert 'parser.add_argument("--sealed-truth-bundle", required=True)' in text


def test_semantic_mutation_campaign_has_thirty_families() -> None:
    namespace: dict = {}
    exec((Path(__file__).parents[1] / "scripts/batch098_semantic_mutations_v2.py").read_text(encoding="utf-8"), namespace)
    assert len(namespace["MUTATIONS"]) >= 30
    assert len(set(namespace["MUTATIONS"])) == len(namespace["MUTATIONS"])
