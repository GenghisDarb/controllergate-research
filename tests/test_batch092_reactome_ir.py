from __future__ import annotations

import json
from pathlib import Path

from controllergate.reactome_ir.schema import RPIR_VERSION, maturity_for, rpir_schema


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "outputs" / "post_v2_37_hardening_batch092_reactome_complete_pathway_ir_external_review_correction"


def _json(name: str) -> dict:
    return json.loads((OUTPUT / name).read_text(encoding="utf-8"))


def _jsonl_count(name: str) -> int:
    with (OUTPUT / name).open(encoding="utf-8") as stream:
        return sum(1 for line in stream if line.strip())


def test_batch091_expected_red_and_manifest_defect_are_preserved() -> None:
    expected_red = _json("batch092_pre_fix_external_review_expected_failure.json")
    manifest = _json("batch091_artifact_manifest_verification.json")
    assert expected_red["status"] == "BATCH092_PRE_FIX_EXTERNAL_REVIEW_FAIL_EXPECTED"
    assert expected_red["finding_count"] == 24
    assert manifest["outer_manifest"]["nonself_checked"] == 107
    assert manifest["outer_manifest"]["self_entry_count"] == 1
    assert manifest["status"] == "PASS_WITH_RECONCILED_OUTER_SELF_MANIFEST_DEFECT"


def test_complete_release_97_document_and_event_coverage() -> None:
    coverage = _json("reactome_source_coverage.json")
    documents = _json("reactome_source_documents.json")
    assert coverage["status"] == "PASS"
    assert coverage["unique_chapter_count"] == 29
    assert coverage["duplicate_chapter_count"] == 0
    assert coverage["observed_pathway_count"] == 2916
    assert coverage["observed_reaction_count"] == 16814
    assert coverage["silent_omission_count"] == 0
    assert coverage["stable_id_conflict_count"] == 0
    assert len(documents["documents"]) == 30
    assert _jsonl_count("reactome_pathways.jsonl") == 2916
    assert _jsonl_count("reactome_reactions.jsonl") == 16814


def test_shared_stable_ids_preserve_every_chapter_occurrence() -> None:
    coverage = _json("reactome_source_coverage.json")
    audit = _json("rpir_stable_identity_audit.json")
    assert coverage["shared_event_occurrence_count"] > 0
    assert audit["source_occurrence_count"] == 2916 + 16814
    assert audit["stable_id_count"] < audit["source_occurrence_count"]
    assert audit["conflicts"] == []


def test_rpir_keeps_uncertain_and_omitted_states_non_authorizing() -> None:
    schema = rpir_schema()
    assert schema["$id"] == RPIR_VERSION == "controllergate-rpir-v1"
    assert "uncertain" in schema["source_event_types"]
    assert "omitted" in schema["source_event_types"]
    assert maturity_for(event_type="uncertain", inferred_from=None, chapter="Disease", text="") == "UNCERTAIN_BLACK_BOX"
    assert maturity_for(event_type="omitted", inferred_from=None, chapter="Disease", text="") == "OMITTED_DETAIL"
    assert "never grants repair or product authority" in schema["authority_rule"]
