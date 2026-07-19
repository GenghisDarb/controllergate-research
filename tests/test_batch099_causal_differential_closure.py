from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

from controllergate.amds.causal_differential_v9 import EVIDENCE_LEVELS, ROOT_CLASSES
from controllergate.evidence.batch098_official_ingest import private_content_scan


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs" / "post_v2_37_hardening_batch099_causal_differential_intervention_contradiction_root_closure_master_completion_ledger"
CAUSAL = OUT / "causal_differential"


def rows(name: str) -> list[dict]:
    return [json.loads(line) for line in (CAUSAL / name).read_text().splitlines() if line.strip()]


def value(name: str) -> dict:
    return json.loads((CAUSAL / name).read_text())


def test_all_432_contradiction_roots_reconstructed() -> None:
    roots = rows("batch099_contradiction_root_map_v1.jsonl")
    assert len(roots) == 432
    assert {row["root_classification"] for row in roots} == {"false_mutual_exclusion"}
    assert all(row["evidence_parents"] and not row["ownership_fact_survives"] for row in roots)
    assert set(Counter(row["candidate_id"] for row in roots).values()) == {54}


def test_fact_admissions_are_contact_not_ownership() -> None:
    facts = rows("batch099_provisional_fact_causal_evidence_map_v1.jsonl")
    assert len(facts) == 504
    assert {row["evidence_level"] for row in facts} == {"CONTACT_VERIFIED"}
    assert not any(row["ownership_supported"] for row in facts)


def test_causal_evidence_hierarchy_separates_levels() -> None:
    hierarchy = value("batch099_causal_evidence_hierarchy_v1.json")
    assert hierarchy["levels"] == list(EVIDENCE_LEVELS)
    assert hierarchy["contradiction_root_classes"] == list(ROOT_CLASSES)
    assert hierarchy["contact_can_grant_ownership"] is False
    assert hierarchy["mixed_failure_requires_factorial_interaction"] is True


def test_counterfactual_contracts_bind_changed_dimension_and_invariants() -> None:
    contracts = rows("batch099_matched_counterfactual_probe_contracts_v1.jsonl")
    assert len(contracts) == 8
    assert all(row["changed_dimension"] and row["held_invariants_required"] and row["required_records"] for row in contracts)


def test_existing_evidence_is_not_overpromoted() -> None:
    pairs = rows("batch099_existing_counterfactual_pair_audit_v1.jsonl")
    assert len(pairs) == 15
    assert sum(row["evidence_level"] == "DIMENSION_SENSITIVITY_VERIFIED" for row in pairs) == 2
    assert not any(row["ownership_supported"] for row in pairs)
    gate = value("batch099_counterfactual_adequacy_gate.json")
    assert gate["status"] == "BLOCK"
    assert gate["ownership_supporting_pair_count"] == 0


def test_corrected_constraints_remove_false_contradictions_without_claiming_ownership() -> None:
    summary = value("batch099_corrected_semantic_replay_summary.json")
    terminals = rows("batch099_corrected_terminal_records_v1.jsonl")
    assert summary["false_mutual_exclusion_count_after_correction"] == 0
    assert summary["genuine_contradiction_count"] == 0
    assert summary["ownership_fact_count"] == 0
    assert len(terminals) == 80
    assert {row["terminal_class"] for row in terminals} == {"INSUFFICIENT_EVIDENCE"}


def test_architecture_gain_and_tld_authority_remain_blocked() -> None:
    gate = value("batch099_architecture_component_gain_gate.json")
    assert gate["status"] == "BLOCK"
    assert gate["routing_authority_granted"] == []
    assert gate["tld_mode"] == "SHADOW_ONLY"


def test_claim_boundary_and_no_actuation() -> None:
    decision = value("batch099_scientific_decision.json")
    claim = value("batch099_claim_boundary.json")
    assert decision["status"] == "SCIENTIFIC_BLOCK"
    assert decision["ordinary_patch_count"] == 0
    assert decision["historical_increment"] == 0
    assert claim["release_decision"] == "PRODUCT_BETA_RC_BLOCKED_EXACT"
    assert claim["prospective_effectiveness"] == "NOT_ESTABLISHED"
    assert claim["memory"] == "not demonstrated"


def test_all_outputs_bind_official_ingest_receipt() -> None:
    expected = value("../batch098_official_ingest/ingest_receipts/batch098_official_ingest_index.json")["receipt_sha256"]
    bound = 0
    for path in CAUSAL.glob("*.json"):
        data = json.loads(path.read_text())
        if "official_ingest_receipt_sha256" in data:
            assert data["official_ingest_receipt_sha256"] == expected
            bound += 1
    assert bound >= 8


def test_public_causal_outputs_have_no_private_content() -> None:
    assert private_content_scan(CAUSAL)["status"] == "PASS"


def test_workflow_binds_official_ingest_gate() -> None:
    workflow = (ROOT / ".github" / "workflows" / "post_v2_37_hardening_batch099_causal_differential_intervention_contradiction_root_closure.yml").read_text()
    assert "batch098_official_ingest_custody:" in workflow
    assert "needs: batch098_official_ingest_custody" in workflow
    assert "run-id: 29677246896" in workflow
    assert "run-id: 29671958790" in workflow
    assert "ingest_receipt_sha256" in workflow
    assert "*.zip" in workflow
