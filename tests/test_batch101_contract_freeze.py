import json
from pathlib import Path

from controllergate.amds.matched_counterfactual_v11 import validate_pair
from controllergate.evidence.provider_identity_v3 import ProviderIdentityV3, classify_provider


ROOT = Path(__file__).resolve().parents[1]


def rows(name):
    return [json.loads(line) for line in (ROOT / "configs" / name).read_text().splitlines() if line.strip()]


def test_all_programs_use_declarative_predicates_and_are_frozen():
    programs = rows("batch101_candidate_counterfactual_programs_v3.jsonl")
    semantics = rows("batch101_outcome_semantic_registry_v3.jsonl")
    assert len(programs) == 9 == len(semantics)
    assert all(row["predicate_language_id"] == "DeclarativePredicateV1" for row in programs)
    assert all(row["frozen_before_execution"] and not row["truth_derived"] for row in semantics)


def test_registered_cell_accounting_includes_completed_cloudpickle_factorial():
    cells = rows("batch101_counterfactual_cell_registry_v3.jsonl")
    assert len(cells) == 33
    assert any(row["cell_id"].endswith("python311-with-setuptools") for row in cells)


def test_provider_prefix_does_not_establish_exact_parity():
    required = ProviderIdentityV3("cpython", 3, 13, 0, "b1", "linux", "x86_64", "cp313", "cpython-313-x86_64-linux-gnu")
    observed = ProviderIdentityV3("cpython", 3, 13, 0, "b2", "linux", "x86_64", "cp313", "cpython-313-x86_64-linux-gnu")
    result = classify_provider(required, observed)
    assert result["mode"] == "SERIES_LIMITED_PROVIDER"
    assert result["exact_incident_authority"] is False


def test_pair_receipt_presence_is_not_pair_validity():
    program = rows("batch101_candidate_counterfactual_programs_v3.jsonl")[0]
    incident = {"execution_status": "EXECUTED", "provider_mode": "EXACT_PROVIDER", "predicate_result": False, "semantically_reproducible": True}
    control = {"execution_status": "EXECUTED", "provider_mode": "EXACT_PROVIDER", "predicate_result": True, "semantically_reproducible": True}
    result = validate_pair(program, incident, control, held_invariants_verified=True, factorial_complete=True)
    assert result["status"] == "INCIDENT_NOT_MATERIALIZED"
    assert result["ownership_supported"] is False
