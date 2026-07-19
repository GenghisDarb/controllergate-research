from __future__ import annotations

import json
from pathlib import Path

import pytest

from controllergate.amds.matched_counterfactual_v10 import (
    MatchedCounterfactualEvidenceV2,
    canonical_hash,
    validate_program,
)
from controllergate.evidence.incident_identity_v2 import PARITY_STATUSES, validate_supersession
from controllergate.evidence.provider_capsule_v2 import verify_provider_capsule
from controllergate.evidence.source_capsule_v1 import verify_source_capsule


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "outputs/post_v2_37_hardening_batch100_matched_counterfactual_execution_causal_ownership_architecture_gain_master_roadmap_lock/matched_counterfactual"


def jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def test_incident_and_provider_separation_covers_all_eight() -> None:
    incidents = jsonl(ROOT / "configs/batch100_incident_identity_registry_v2.jsonl")
    providers = jsonl(ROOT / "configs/batch100_incident_provider_registry_v2.jsonl")
    assert len(incidents) == len(providers) == 8
    assert {row["candidate_id"] for row in incidents} == {row["candidate_id"] for row in providers}
    assert all(len(row["frozen_source_commit"]) == 40 for row in incidents)
    assert all(row["parity_status"] in PARITY_STATUSES for row in providers)
    assert any(row["parity_status"] == "PROVIDER_MICRO_UNRESOLVED" for row in providers)
    assert any(row["parity_status"] == "PLATFORM_MISMATCH" for row in providers)


def test_historical_contracts_are_superseded_not_rewritten() -> None:
    rows = jsonl(ROOT / "configs/batch100_candidate_contract_supersession_registry_v1.jsonl")
    assert len(rows) == 8
    for row in rows:
        validate_supersession(row)
        assert row["historical_contract_preserved"] is True
        expected = canonical_hash({key: value for key, value in row.items() if key != "supersession_hash"})
        assert row["supersession_hash"] == expected


def test_exact_issue_nodes_replace_known_mismatches() -> None:
    rows = {row["candidate_id"]: row for row in jsonl(ROOT / "configs/batch100_incident_identity_registry_v2.jsonl")}
    cloudpickle = rows["cloudpickle_507_py313_typevar_distutils"]["issue_reported_exact_nodes"]
    assert cloudpickle
    assert not any("test_extract_class_dict" in node for node in cloudpickle)
    assert len(rows["freezegun_547_py313_datetimes_assertion"]["issue_reported_exact_nodes"]) == 3
    assert len(rows["audioread_144_py313_aifc_removed"]["issue_reported_exact_nodes"]) == 4
    assert len(rows["pytest_13480_wdefault_unraisable_threadexception"]["issue_reported_exact_nodes"]) == 3


def test_source_and_provider_capsules_verify_without_authority_escalation() -> None:
    source = jsonl(OUTPUT / "source_capsule_registry_v1.jsonl")
    provider = jsonl(OUTPUT / "provider_capsule_registry_v2.jsonl")
    assert len(source) == 8
    assert len({row["candidate_id"] for row in provider}) == 8
    assert all(not verify_source_capsule(row) for row in source)
    assert all(not verify_provider_capsule(row) for row in provider)
    assert all("causal ownership" in " ".join(row["authority_forbidden"]) for row in source)
    assert all(row["offline_execution_network"] in {"none", "loopback_only"} for row in provider)


def test_all_programs_and_cells_are_frozen_before_outcomes() -> None:
    programs = jsonl(ROOT / "configs/batch100_candidate_counterfactual_programs_v2.jsonl")
    cells = jsonl(ROOT / "configs/batch100_counterfactual_cell_registry_v2.jsonl")
    assert len(programs) == 9
    assert len(cells) == 32
    assert {row["candidate_id"] for row in programs} == {row["candidate_id"] for row in cells}
    assert all(not validate_program(row) for row in programs)
    assert all(row["truth_access"] == row["private_tld_access"] == row["patch_operations"] == 0 for row in cells)
    assert all(row["fresh_workspace_count"] >= 2 for row in cells)
    assert all(row["network_policy"] in {"none", "loopback_only"} for row in cells)


def test_tld_ordering_cannot_create_or_remove_legal_cells() -> None:
    plans = jsonl(ROOT / "configs/batch100_opaque_tld_ordering_registry_v1.jsonl")
    cells = jsonl(ROOT / "configs/batch100_counterfactual_cell_registry_v2.jsonl")
    assert len(plans) == 16
    by_candidate = {}
    for row in cells:
        by_candidate.setdefault(row["candidate_id"], set()).add(row["cell_id"])
    for plan in plans:
        assert set(plan["ordered_opaque_probe_ids"]) == by_candidate[plan["candidate_id"]]
        assert plan["truth_field_count"] == plan["private_tld_passage_count"] == 0
        assert "probe creation" in plan["authority_forbidden"]


def test_ownership_record_rejects_sensitivity_only_escalation() -> None:
    values = dict(
        pair_id="p", program_id="g", candidate_id="c", sub_incident_id="s", factor_registry={},
        incident_cell_id="a", control_cell_id="b", source_capsule_hashes=["s"], provider_capsule_hashes=["p"],
        fixture_hashes=["f"], command_hashes=["c"], environment_hashes=["e"], held_invariants=["source"],
        changed_dimensions=["provider"], single_factor_status="VALID_SINGLE_FACTOR_PAIR", factorial_status="NOT_APPLICABLE",
        incident_materialized=True, control_materialized=True, incident_predicate={}, control_predicate={},
        incident_observation_ids=["a"], control_observation_ids=["b"], semantic_verifier_receipts=["v"],
        outcome_difference=True, effect_direction="incident_to_control", replay_consistency="REPRODUCIBLE",
        necessity_supported=False, sufficiency_supported=False, interaction_supported=False,
        alternative_exclusions=[], unresolved_alternatives=[], evidence_level="DIMENSION_SENSITIVITY_VERIFIED",
        ownership_class_proposal="PROVIDER_OWNED", ownership_supported=True,
        authority_allowed="sensitivity", authority_forbidden=["ownership"],
    )
    with pytest.raises(ValueError, match="ownership requires ownership evidence level"):
        MatchedCounterfactualEvidenceV2(**values)
