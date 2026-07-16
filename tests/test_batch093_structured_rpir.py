from __future__ import annotations

import json
from pathlib import Path

from controllergate.reactome_ir.schema import FIELD_STATES, RPIR_V2_VERSION, field_value, rpir_v2_schema


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "outputs/post_v2_37_hardening_batch093_structured_rpir_executable_isomorphism_amds_role_cohort_closure"


def _json(name: str) -> dict:
    return json.loads((OUTPUT / name).read_text(encoding="utf-8"))


def test_exact_structured_source_reconciles_occurrences_and_unique_events() -> None:
    result = _json("reactome_structured_count_reconciliation.json")
    assert result["status"] == "PASS"
    assert result["reaction_occurrence_count"] == 16814
    assert result["unique_reaction_stable_id_count"] == 16107
    assert result["pathway_occurrence_count"] == 2916
    assert result["unique_pathway_stable_id_count"] == 2883
    assert result["silent_omission_count"] == 0
    assert result["duplicate_inflation_count"] == 0


def test_rpir_v2_keeps_absence_states_distinct() -> None:
    schema = rpir_v2_schema()
    assert schema["$id"] == RPIR_V2_VERSION
    assert set(schema["field_states"]) == set(FIELD_STATES)
    assert field_value([], state="SOURCE_EXPLICITLY_EMPTY", source="unit")["state"] == "SOURCE_EXPLICITLY_EMPTY"
    assert field_value(None, state="SOURCE_NOT_EXPOSED_BY_FORMAT", source="unit")["state"] == "SOURCE_NOT_EXPOSED_BY_FORMAT"


def test_structured_anchor_reaction_has_machine_grounded_fields() -> None:
    anchor = None
    with (OUTPUT / "reactome_structured_rpir_v2_reactions.jsonl").open(encoding="utf-8") as stream:
        for line in stream:
            row = json.loads(line)
            if row["source_stable_id"] == "R-HSA-9912396":
                anchor = row
                break
    assert anchor is not None
    assert anchor["source_database_id"] == 9912396
    assert anchor["participants"]["state"] == "SOURCE_VALUE"
    assert len(anchor["participants"]["value"]) == 6
    assert len(anchor["catalysts"]["value"]) == 1
    assert len(anchor["compartments"]["value"]) == 1
    assert len(anchor["preceding_events"]["value"]) == 1
    assert anchor["output_profile"] == "B093_RPIR_V2_STRUCTURED_NONAUTH"


def test_batch092_depth_is_corrected_without_rewriting_history() -> None:
    result = _json("batch092_depth_reconciliation.json")
    assert result["status"] == "PASS"
    assert result["dimensions"]["documentary_occurrence_coverage"]["status"] == "PASS"
    assert result["dimensions"]["structured_semantic_graph"]["status"] == "NOT_ESTABLISHED"
    assert result["dimensions"]["primitive_semantic_distinctness"]["status"] == "NOT_ESTABLISHED"


def test_official_batch092_artifact_custody_is_exact() -> None:
    ingest = _json("batch092_artifact_ingest.json")
    manifest = _json("batch092_artifact_manifest_verification.json")
    assert ingest["status"] == "PASS"
    assert ingest["artifact"]["artifact_id"] == 8358022260
    assert ingest["artifact"]["sha256"] == "bd3f1de0e64c8d2f8de5d76eb78bc5179543239b16b47a3b594214ac2a3443c1"
    assert all(row["status"] == "PASS" for row in manifest["manifests"])
