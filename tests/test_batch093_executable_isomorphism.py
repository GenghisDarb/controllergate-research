from __future__ import annotations

import json
from pathlib import Path

from controllergate.isomorphism.primitives import GENERIC_PRIMITIVES, PRIMITIVE_CONTRACTS, apply_primitive, conformance_event
from controllergate.isomorphism.runtime import execute_structured_scenario


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "outputs/post_v2_37_hardening_batch093_structured_rpir_executable_isomorphism_amds_role_cohort_closure"


def _json(name: str) -> dict:
    return json.loads((OUTPUT / name).read_text(encoding="utf-8"))


def test_all_generic_primitives_have_distinct_executable_effects() -> None:
    assert len(GENERIC_PRIMITIVES) == 46
    assert len({contract["effect_key"] for contract in PRIMITIVE_CONTRACTS.values()}) == 46
    event = conformance_event()
    state = {"primitive_trace": []}
    for primitive in GENERIC_PRIMITIVES:
        result = apply_primitive(primitive, state, event)
        assert result["status"] == "PASS"
        state = result["state"]
        malformed = dict(event)
        malformed.pop(PRIMITIVE_CONTRACTS[primitive]["required_event_field"])
        blocked = apply_primitive(primitive, state, malformed)
        assert blocked["status"] == "BLOCK"
        assert PRIMITIVE_CONTRACTS[primitive]["effect_key"] in state


def test_executed_ablation_proves_nonaliasing() -> None:
    result = _json("primitive_semantic_distinctness_audit.json")
    assert result["status"] == "PASS"
    assert result["ablation_count"] == 46
    assert result["distinct_effect_count"] == 46


def test_required_primitive_laws_have_distinct_failure_and_recovery_semantics() -> None:
    base = {"source_occurrence_identity": "unit-source"}
    assert apply_primitive("CHECKPOINT", {}, {**base, "checkpoint": False})["blocker"] == "checkpoint_prerequisite_unmet"
    assert apply_primitive("IRREVERSIBLE_REACTION", {}, {**base, "commit_transition": {"reverse": True}})["status"] == "BLOCK"
    reversible = apply_primitive("REVERSIBLE_REACTION", {}, {**base, "reverse_transition": {"reverse": True}})
    assert reversible["state"]["reversible_transition"]["direction"] == "reverse"
    assert apply_primitive("RESOURCE_FLUX", {}, {**base, "resource_delta": -1})["blocker"] == "resource_budget_underflow"
    resynchronized = apply_primitive("OSCILLATOR", {}, {**base, "phase": {"drift": True, "authorized_reset": True}})
    assert resynchronized["state"]["oscillator_phase"]["resynchronized"] is True
    assert apply_primitive("THREAT_HIJACK", {}, {**base, "untrusted_controller": {"verifier_disabled": True}})["status"] == "BLOCK"
    assert apply_primitive("LOCAL_CONTAINMENT", {}, {**base, "containment_scope": {"scope": "global"}})["status"] == "BLOCK"
    residual = apply_primitive("RESIDUAL_ACTIVITY", {}, {**base, "residual_fraction": 0.4})
    assert residual["state"]["residual_activity"]["health_grade"] == "degraded"
    rescue = apply_primitive("RESCUE", {}, {**base, "rescue_route": "bounded"})
    assert rescue["state"]["rescue_state"]["incomplete_product_promoted"] is False


def test_structural_compiler_covers_all_occurrences_without_keyword_authority() -> None:
    result = _json("reactome_translation_structural_coverage.json")
    firewall = _json("reactome_translation_authority_firewall_v2.json")
    assert result["translation_candidate_count"] == 16814
    assert result["silent_omission_count"] == 0
    assert result["automatic_rejection_count"] == 0
    assert firewall["keyword_authority_count"] == 0
    assert firewall["production_promotion_count"] == 0


def test_canonical_scenario_execution_persists_stage_and_scoped_evidence(tmp_path: Path) -> None:
    scenario = _json("reactome_structured_cross_chapter_scenario.json")
    result = execute_structured_scenario(scenario, tmp_path / "state.sqlite3", platform="unit")
    assert result["status"] == "PASS"
    assert result["stage_id"] == "plan_maturation"
    assert result["unbrokered_external_operation_count"] == 0
    import sqlite3
    connection = sqlite3.connect(tmp_path / "state.sqlite3")
    assert connection.execute("SELECT COUNT(*) FROM mechanism_outcomes").fetchone()[0] == 1
    assert connection.execute("SELECT COUNT(*) FROM test_assertions").fetchone()[0] == 1
    assert connection.execute("SELECT COUNT(*) FROM execution_receipts").fetchone()[0] == 1
    connection.close()


def test_windows_installed_execution_uses_site_packages_and_all_chapters() -> None:
    rows = [json.loads(line) for line in (OUTPUT / "reactome_chapter_scenario_results_windows.jsonl").read_text(encoding="utf-8").splitlines() if line]
    assert len(rows) == 30
    assert sum(row["chapter"] != "cross_chapter_integrated" if "chapter" in row else not row["scenario_id"].endswith("integrated") for row in rows) == 29
    assert all(row["status"] == "PASS" for row in rows)
    assert all(row["installed_site_packages_origin"] is True for row in rows)
