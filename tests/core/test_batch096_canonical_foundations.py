from pathlib import Path

import pytest

from controllergate.governance.repository_genome import coverage, discover_identifiers
from controllergate.runtime.materialization_compartments_v2 import enforce_disjoint
from controllergate.topology.canonical_v2 import ObserverPhase, ObserverStateContractV1, ProvisionalEvidenceBufferV1, verify_modalities


def test_history_denominator_has_no_silent_omission():
    rows = discover_identifiers({"a": "batch095 v2.19", "doc": "batch096"}, ["doc"])
    result = coverage(rows, {r.historical_id: "MIGRATED" for r in rows})
    assert result["status"] == "PASS"


def test_compartments_must_be_disjoint(tmp_path: Path):
    with pytest.raises(ValueError): enforce_disjoint([tmp_path, tmp_path / "nested"])


def test_observer_truth_access_is_rejected():
    state = ObserverStateContractV1("c", "r", "f", ObserverPhase.DIAGNOSIS, (), (), truth_access=True)
    with pytest.raises(ValueError): state.validate()


def test_provisional_fact_needs_controller_audit():
    buffer = ProvisionalEvidenceBufferV1("c", "f"); buffer.add("b", {"fact":"x"})
    with pytest.raises(ValueError): buffer.promote("b", 0, None)


def test_five_modalities_need_independent_verifiers():
    rows = [{"modality": m, "producer": "p", "verifier": "v", "value": "supported"} for m in ("STRUCTURAL","RUNTIME","SEMANTIC","PROVENANCE","COUNTERFACTUAL")]
    assert verify_modalities(rows)["status"] == "PASS"
