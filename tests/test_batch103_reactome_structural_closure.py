import json
from collections import Counter
from pathlib import Path

import pytest

from controllergate.amds.reactome_planner_v1 import plan_intervention
from controllergate.isomorphism.canonical_stack_v3 import (
    CANONICAL_ORDER,
    REJECTED_INTERPRETATIONS,
    build_contact_ledger,
    stack_contract,
)
from controllergate.isomorphism.primitives import PRIMITIVE_CONTRACTS
from controllergate.isomorphism.reactome_source_grounded_scenarios_v2 import (
    OPERATION_FAMILIES,
    compile_source_grounded_scenario,
)


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs/post_v2_37_hardening_batch103_reactome_isomorphism_causal_planning_gain_exact_materialization"
SOURCE = ROOT / "outputs/post_v2_37_hardening_batch094_value_bound_rpir_fresh_amds_cohort_historical_closure"


def jsonl(path: Path):
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                yield json.loads(line)


def test_canonical_isomorphism_registry_has_complete_authority_fields():
    rows = list(jsonl(ROOT / "configs/controllergate_isomorphism_registry_v3.jsonl"))
    required = {
        "isomorphism_id",
        "source_domain",
        "source_document",
        "source_hash",
        "source_location",
        "source_statement",
        "target_software_domain",
        "operational_translation",
        "implementation_paths",
        "current_tests",
        "current_evidence",
        "evidence_level",
        "completion_level",
        "authority_allowed",
        "authority_forbidden",
        "known_errors",
        "reopen_conditions",
        "last_verified_commit",
    }
    assert len(rows) == 69
    assert all(required == set(row) for row in rows)
    levels = Counter(row["evidence_level"] for row in rows)
    assert levels["EXECUTABLE_SHADOW"] == 46
    assert levels["CONTRADICTED"] == 10
    assert levels["DEPRECATED"] == 1
    assert all("biological proof" in row["authority_forbidden"] for row in rows)


def test_corrected_stack_order_contact_slots_and_claim_rejections():
    config = json.loads((ROOT / "configs/controllergate_5_14_6_196_stack_v3.json").read_text())
    assert config == stack_contract()
    assert config["order"] == list(CANONICAL_ORDER)
    assert config["rejected_interpretations"] == list(REJECTED_INTERPRETATIONS)
    ledger = build_contact_ledger({1: "evidence:a", 14: "evidence:n"}, not_applicable={7})
    assert len(ledger) == 14
    assert Counter(row["status"] for row in ledger) == {
        "PRESENT": 2,
        "MISSING": 11,
        "NOT_APPLICABLE": 1,
    }
    assert "six-subunit" in config["mcm_boundary"]
    assert "no exact fourteen-nucleosome" in config["mcm_boundary"]


def test_brot_terminology_is_classified_without_unsupported_usage():
    boundary = json.loads((ROOT / "configs/brot_tot_brot_tot_bulb_boundary_v2.json").read_text())
    assert boundary["active_classifications"] == {
        "TORUS-BROT": "CANONICAL_TORUS_BROT",
        "ToT-BROT": "CANONICAL_TOT_BROT",
        "ToT-BULB": "CANONICAL_TOT_BULB",
    }
    audit = json.loads((OUT / "brot_tot_brot_tot_bulb_terminology_audit_v2.json").read_text())
    assert audit["status"] == "PASS"
    assert audit["ambiguous_or_unsupported_count"] == 0
    assert audit["historical_translation_receipt_count"] > 0
    audit_source = (ROOT / "scripts/audit_brot_tot_brot_tot_bulb_terminology.py").read_text()
    assert '"--others"' not in audit_source
    assert 'relative.startswith("incoming_artifacts/")' in audit_source


def test_reactome_mapping_covers_locked_source_without_defaults():
    summary = json.loads((OUT / "reactome_mapping_completeness_v2.json").read_text())
    assert summary["pathways"] == 2916
    assert summary["reactions"] == 16814
    assert summary["primitive_classes"] == 46 == len(PRIMITIVE_CONTRACTS)
    assert summary["chapter_source_families"] == 29
    assert summary["field_assessments"] == 403536
    assert summary["silent_omissions"] == 0
    assert summary["unclassified_fields"] == 0
    assert set(summary["field_origin_distribution"]) == {
        "DIRECT_REACTOME_VALUE",
        "DERIVED_REACTOME_VALUE",
        "RPIR_STRUCTURAL_RELATION",
    }
    defaults = json.loads((OUT / "reactome_default_value_audit_v1.json").read_text())
    synthetic = json.loads((OUT / "reactome_claim_bearing_synthetic_value_audit_v1.json").read_text())
    assert defaults["claim_bearing_default_count"] == 0
    assert synthetic["synthetic_or_default_fields_with_causal_authority"] == 0


def test_all_29_requested_chapter_families_are_present():
    registry = json.loads((OUT / "reactome_normalized_chapter_family_registry_v1.json").read_text())
    assert registry["status"] == "PASS"
    assert len(registry["families"]) == len(set(registry["families"])) == 29
    assert registry["biological_equivalence_claimed"] is False


def test_field_grounding_registry_covers_every_reaction_and_field():
    count = 0
    assessments = 0
    for row in jsonl(OUT / "reactome_field_grounding_registry_v1.jsonl"):
        count += 1
        assessments += len(row["field_origins"])
        assert "UNKNOWN" not in row["field_origins"].values()
        assert row["default_rule"] is None
        assert row["claim_bearing_status"] is False
    assert count == 16814
    assert assessments == 403536


def test_source_grounded_scenarios_have_no_round_robin_authority():
    scenario_count = 0
    observed_operations = set()
    for row in jsonl(OUT / "source_grounded_scenario_registry_v2.jsonl"):
        scenario_count += 1
        assert row["round_robin_authority"] is False
        assert row["primitive_ids"][0] == "EVENT_CONTRACT"
        observed_operations.update(row["operation_families"])
    assert scenario_count == 16814
    assert observed_operations == set(OPERATION_FAMILIES)
    retirement = json.loads((OUT / "legacy_round_robin_authority_retirement_audit.json").read_text())
    assert retirement["legacy_classification"] == "HISTORICAL_SYNTHETIC_COVERAGE_FIXTURE"
    assert retirement["current_authority_round_robin_mappings"] == 0


def test_scenario_compiler_derives_from_source_relations():
    source_record = next(jsonl(SOURCE / "rpir_v2_1_reactions.jsonl"))
    scenario = compile_source_grounded_scenario(source_record)
    assert scenario["source_hash"] == source_record["source_graph_hash"]
    assert scenario["round_robin_authority"] is False
    assert "COMPLEX_ASSEMBLY" in scenario["primitive_ids"]
    assert "MODIFICATION_CODE" in scenario["primitive_ids"]


def test_translation_registry_has_typed_losses_and_counterfactuals():
    rows = list(jsonl(OUT / "reactome_translation_registry_v2.jsonl"))
    assert len(rows) == 18
    assert all(row["losses"] and row["uncertainty"] for row in rows)
    assert all("proof by metaphor" in row["authority_boundary"]["forbidden"] for row in rows)
    counterfactuals = list(jsonl(OUT / "reactome_counterfactual_semantics_v1.jsonl"))
    assert len(counterfactuals) == 18
    assert all(row["held_invariants_required"] and row["truth_access"] == 0 for row in counterfactuals)


def test_reaction_specific_shadow_receipts_are_nonauthorizing():
    registry = list(jsonl(OUT / "reactome_shadow_operation_registry_v2.jsonl"))
    assert {row["operation_family"] for row in registry} == set(OPERATION_FAMILIES)
    count = 0
    operation_count = 0
    observed = set()
    for row in jsonl(OUT / "reactome_shadow_execution_receipts_v2.jsonl"):
        count += 1
        operation_count += row["operation_count"]
        observed.update(row["operation_families"])
        assert row["terminal_written"] is False
        assert row["causal_fact_created"] is False
        assert row["patch_authorized"] is False
        assert row["repair_count_changed"] is False
        assert row["truth_access"] == 0
        assert row["release_promoted"] is False
    assert count == 16814
    assert operation_count == 167292
    assert observed == set(OPERATION_FAMILIES)
    assert sum(1 for _ in jsonl(OUT / "reactome_shadow_verification_receipts_v2.jsonl")) == 16814


def test_reactome_planner_selects_only_legal_truth_blind_actions():
    decision = plan_intervention(
        candidate="candidate-a",
        maintenance_state={"blocked_branches": ["old-route"]},
        public_rpir_relations=[
            {
                "source_hash": "a" * 64,
                "reaction": "R-HSA-1",
                "blocked": True,
                "missing_prerequisites": ["provider"],
                "alternative_pathways": ["registered-route"],
            }
        ],
        legal_interventions=[
            {"intervention_id": "legal-low", "legal": True, "cost": 1, "expected_information_gain": 0.2},
            {"intervention_id": "legal-high", "legal": True, "cost": 2, "expected_information_gain": 0.8},
        ],
        budget=2,
    )
    assert decision.selected_intervention == "legal-high"
    assert decision.truth_access == 0
    assert decision.tld_access == 0
    assert decision.selected_intervention in decision.legal_reaction_analogues
    assert "patch" in decision.authority_forbidden
    with pytest.raises(ValueError, match="forbidden planner input"):
        plan_intervention(
            candidate="candidate-a",
            maintenance_state={"sealed_truth": "owner"},
            public_rpir_relations=[],
            legal_interventions=[],
            budget=1,
        )
    with pytest.raises(ValueError, match="illegal intervention"):
        plan_intervention(
            candidate="candidate-a",
            maintenance_state={},
            public_rpir_relations=[],
            legal_interventions=[{"intervention_id": "illegal-probe", "legal": False}],
            budget=1,
        )


def test_completion_model_stops_before_causal_gain():
    status = json.loads((OUT / "reactome_completion_status_v1.json").read_text())
    assert status["R0_SOURCE_CUSTODY"] == "PASS"
    assert status["R3_EXECUTABLE_SHADOW"] == "PASS_NONAUTHORIZING_SHADOW"
    assert status["R4_CAUSAL_PLANNING_GAIN"] == "NOT_ESTABLISHED"
    assert status["R5_CROSS_CANDIDATE_GENERALIZATION"] == "NOT_ESTABLISHED"
    assert status["R6_PROSPECTIVE_VALIDATION"] == "NOT_RUN"
    assert status["reactome_isomorphism_complete"] is False
