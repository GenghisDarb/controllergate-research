from __future__ import annotations

import json
from pathlib import Path

import pytest

from controllergate.amds.causal_closure_v2 import validate_closure
from controllergate.amds.historical_challenge_v2 import persisted_permutation, seal_arm
from controllergate.amds.hypothesis_space_v2 import HYPOTHESES
from controllergate.amds.likelihood_calibration import calibrate_likelihoods
from controllergate.amds.minimal_probe_v2 import run_sequence, select_probe
from controllergate.amds.probe_registry_v2 import default_registry
from controllergate.diagnosis.contact_topology_signature import contact_topology_signature
from controllergate.diagnosis.cross_family_homology_ledger_v2 import CrossFamilyHomologyLedger
from controllergate.diagnosis.homology_retrieval_v2 import retrieve_structural


def test_minimal_probe_uses_explicit_deterministic_fallback_and_two_probes():
    probes = default_registry()[:3]
    model = calibrate_likelihoods([], "holdout")
    selected = select_probe(probes, {probe.evidence_contact for probe in probes}, model)
    assert selected["selection_method"] == "deterministic_constraint_elimination"
    assert selected["predicted_information_gain"] is None
    observations = iter([
        {"observation_class": "artifact_custody_verified", "direct_evidence": ["hash-ok"]},
        {"observation_class": "source_identity_verified", "direct_evidence": ["sha-ok"], "terminal_class": "source_owned_behavior_defect"},
    ])
    result = run_sequence(
        probes,
        lambda _probe: next(observations),
        {"artifact_custody_verified": {"network_or_transport_owned"}, "source_identity_verified": {"provider_owned"}},
        budget=3,
        likelihood_model=model,
    )
    assert result["probe_count"] == 2
    assert result["terminal_class"] == "source_owned_behavior_defect"
    assert validate_closure(result["observations"], result["terminal_class"])["status"] == "PASS"


def test_probe_contracts_have_distinct_contacts_and_no_hardcoded_priors():
    probes = default_registry()
    assert len(probes) == 12
    assert len({probe.evidence_contact for probe in probes}) == 12
    assert all(probe.expected_information_value is None for probe in probes)
    assert set(HYPOTHESES) == set(probes[0].hypotheses_distinguished)


def test_shuffled_memory_is_a_persisted_permutation_and_blinded():
    order = [probe.probe_id for probe in default_registry()[:6]]
    shuffled = persisted_permutation(order, 8402)
    assert shuffled != order
    assert sorted(shuffled) == sorted(order)
    assert persisted_permutation(order, 8402) == shuffled
    assert seal_arm("episode", "SHUFFLED_MEMORY_AMDS", shuffled)["truth_visible"] is False


def test_cross_family_homology_excludes_identity_labels_and_patch_content():
    ledger = CrossFamilyHomologyLedger()
    record = {
        "ast_node_family_pattern": ["Call", "Raise"],
        "call_graph_pattern": ["a->b"],
        "exception_propagation_pattern": ["ValueError"],
        "provider_topology": ["wheelhouse"],
        "harness_topology": ["pytest-node"],
        "compartment_transitions": ["source->provider"],
        "normal_incident_divergence_pattern": ["return-code"],
        "failed_reaction_pattern": ["provider"],
        "rollback_proof_topology": ["fork->rollback"],
        "probe_cost_history": [1, 2],
    }
    ledger.append("family-a", "proof-a", record)
    query = contact_topology_signature(record)
    result = retrieve_structural(ledger.rows, query, holdout_family="family-b", excluded_proof_groups=set())
    assert result["retrieved_structural_records"]
    assert result["excluded_repositories"] == ["family-b"]
    with pytest.raises(ValueError, match="forbidden_homology_fields"):
        contact_topology_signature({"candidate_id": "forbidden"})


def test_cumulative_maturity_has_three_distinct_views():
    model = json.loads((Path(__file__).parents[2] / "configs/controllergate_capability_maturity_model_v2.json").read_text(encoding="utf-8"))
    assert set(model["views"]) == {"CUMULATIVE_HISTORICAL_MATURITY", "CURRENT_BATCH_EVIDENCE_DELTA", "PRODUCTION_READINESS_MATURITY"}
    historical = model["views"]["CUMULATIVE_HISTORICAL_MATURITY"]
    assert historical["AMDS diagnosis"]["level"] == "LEVEL_2_CONTROLLED_FIXTURE_VALIDATED"
    assert historical["autonomous self-maintenance"]["level"] == "LEVEL_0_ABSENT"
