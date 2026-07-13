from __future__ import annotations

import hashlib
import json
from pathlib import Path

from controllergate.amds.observation_contract_v2 import validate_observation

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs" / "post_v2_37_hardening_batch076_amds_causal_memory_calibration"


def load(name: str) -> dict:
    return json.loads((OUT / name).read_text(encoding="utf-8"))


def test_batch075_byte_custody_and_authority() -> None:
    ingest = load("batch075_artifact_ingest.json")
    assert ingest["status"] == "PASS"
    assert ingest["observed_size_bytes"] == 617_959
    assert ingest["observed_sha256"] == "0ec3b1da7452e21662275b97ca804d486965805e9efa1e09663425101c2c3c2a"
    assert ingest["raw_zip_committed"] is False
    reconciliation = load("batch075_provider_hash_reconciliation.json")
    assert reconciliation["scientific_authority"] == "official_workflow"
    assert all(row["local_promoted"] is False for row in reconciliation["records"])


def test_historical_nulls_and_empty_posteriors_are_not_promoted() -> None:
    value = load("batch075_amds_evidence_depth_reconciliation.json")
    assert value["preserved_raw_probe_records"] == 24
    assert value["accepted_observations_under_v2"] == 14
    assert value["rejected_null_observations"] == 10
    assert value["informative_posterior_updates_under_v3"] == 0
    assert value["empty_reported_posterior_maps"] == 24


def test_hordeforge_timeout_has_no_patch_authority() -> None:
    value = load("hordeforge_corrected_admission_decision.json")
    assert value["corrected_admission"] == "QUARANTINED_RESOURCE_TIMEOUT"
    assert value["candidate_failure_reproduced"] is False
    assert value["repair_authority"] is False


def test_every_probe_has_a_valid_observation_event_and_nonce() -> None:
    summary = load("batch076_arm_execution_summary.json")
    assert summary["arm_count"] == 6
    observations = [observation for arm in summary["records"] for observation in arm["observations"]]
    events = [event for arm in summary["records"] for event in arm["probe_events"]]
    nonces = [nonce for arm in summary["records"] for nonce in arm["spent_nonces"]]
    assert len(observations) == len(events) == len(nonces) == 48
    assert len(set(nonces)) == 48
    assert all(validate_observation(observation)["status"] == "PASS" for observation in observations)
    for arm in summary["records"]:
        assert len(set(arm["executed_probe_sequence"])) == len(arm["executed_probe_sequence"])
        assert arm["posterior"]
        assert arm["patch_authority"] is False


def test_routing_memory_is_proof_bound_and_repair_free() -> None:
    records = [json.loads(line) for line in (OUT / "routing_memory_corpus_v1.jsonl").read_text(encoding="utf-8").splitlines()]
    assert len(records) == 9
    for record in records:
        proof = ROOT / record["proof_evidence_path"]
        assert proof.is_file()
        assert hashlib.sha256(proof.read_bytes()).hexdigest() == record["proof_evidence_sha256"]
        serialized = json.dumps(record).lower()
        assert "patch_bytes" not in serialized
        assert "gold_patch" not in serialized


def test_claim_boundary_remains_conservative() -> None:
    final = load("batch076_final_decision.json")
    repair = load("batch076_authoritative_repair_decision.json")
    assert final["AMDS_PROSPECTIVE_EFFECTIVENESS"] == "NOT_ESTABLISHED"
    assert final["memory_lift"] == "not_demonstrated"
    assert final["issue_derived_repair_count"] == 5
    assert final["native_external_repair_count"] == 4
    assert final["full_scoring"] == "NOT_RUN/disallowed"
    assert final["self_maintaining_software"] == "false/not_demonstrated"
    assert repair["status"] == "NOT_RUN_NO_SAFE_GENERIC_PATCH_PLAN"
    assert repair["attempts"] == 0


def test_manifest_matches_bytes() -> None:
    lines = (OUT / "SHA256SUMS.txt").read_text(encoding="utf-8").splitlines()
    assert len(lines) >= 30
    for line in lines:
        digest, relative = line.split(maxsplit=1)
        assert hashlib.sha256((OUT / relative.strip().lstrip("*")).read_bytes()).hexdigest() == digest
