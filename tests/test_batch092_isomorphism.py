from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from controllergate.isomorphism.compiler import compile_candidate
from controllergate.isomorphism.primitives import GENERIC_PRIMITIVES
from controllergate.isomorphism.scenarios import execute_scenario


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "outputs" / "post_v2_37_hardening_batch092_reactome_complete_pathway_ir_external_review_correction"


def _json(name: str) -> dict:
    return json.loads((OUTPUT / name).read_text(encoding="utf-8"))


def test_complete_translation_coverage_never_automatically_rejects() -> None:
    coverage = _json("reactome_translation_coverage.json")
    assert coverage["status"] == "PASS"
    assert coverage["translation_candidate_count"] == 16814
    assert coverage["disposition_coverage"] == 1.0
    assert coverage["silent_omission_count"] == 0
    assert coverage["automatic_rejection_count"] == 0
    assert coverage["rejection_without_ablation_count"] == 0


def test_uncertain_and_omitted_candidate_preserves_reopen_condition() -> None:
    candidate = compile_candidate({
        "stable_source_identity": "R-HSA-1", "source_occurrence_identity": "occ-1", "chapter_identity": "Disease",
        "source_event_type": "omitted", "source_evidence_maturity": "OMITTED_DETAIL", "title": "Unspecified source event",
        "description_excerpt": "", "compartment": [], "source_compartment": [], "destination_compartment": [],
        "positive_regulators": [], "negative_regulators": [], "reversibility": "not_stated",
        "negative_reaction_semantics": False, "orthology_status": "direct_or_not_stated",
    })
    assert candidate["translation_state"] == "BLOCKED_MISSING_SOURCE_DETAIL"
    assert candidate["reopen_condition"]
    assert "production promotion" in candidate["authority_forbidden"]


def test_every_generic_primitive_executed_in_representative_scenarios() -> None:
    coverage = _json("reactome_generic_primitive_execution_coverage.json")
    assert coverage["status"] == "PASS"
    assert coverage["executed_count"] == len(GENERIC_PRIMITIVES)
    assert coverage["missing_primitives"] == []


def test_scenario_keeps_mechanism_outcome_separate_from_assertion(tmp_path: Path) -> None:
    scenario = {
        "scenario_id": "unit-scenario", "chapter": "Unit", "source_stable_id": "R-HSA-1",
        "source_occurrence_identity": "occ-1", "primitive_ids": ["EVENT_CONTRACT", "QUALITY_CONTROL"],
        "negative_control": "missing_source_occurrence_identity", "authority": "shadow_non_authorizing",
    }
    result = execute_scenario(scenario, tmp_path / "scenario.sqlite3", platform="unit")
    assert result["mechanism_status"] == "PASS"
    connection = sqlite3.connect(tmp_path / "scenario.sqlite3")
    assert connection.execute("SELECT COUNT(*) FROM mechanism_outcomes").fetchone()[0] == 1
    assert connection.execute("SELECT COUNT(*) FROM test_assertions").fetchone()[0] == 1
    connection.close()
