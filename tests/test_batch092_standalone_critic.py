from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "outputs" / "post_v2_37_hardening_batch092_reactome_complete_pathway_ir_external_review_correction"


def _json(name: str) -> dict:
    return json.loads((OUTPUT / name).read_text(encoding="utf-8"))


def _jsonl(name: str) -> list[dict]:
    return [json.loads(line) for line in (OUTPUT / name).read_text(encoding="utf-8").splitlines() if line.strip()]


def test_standalone_critic_reconstructs_source_and_translation_counts() -> None:
    reconstruction = _json("standalone_critic_reconstruction.json")
    assert reconstruction["status"] == "PASS"
    assert reconstruction["reconstructed"]["reactome_reactions"] == 16814
    assert reconstruction["reconstructed"]["translation_candidates"] == 16814


def test_critic_findings_are_nonempty_when_release_is_blocked() -> None:
    findings = _jsonl("standalone_critic_findings.jsonl")
    decision = _json("internal_release_evidence_decision.json")
    assert len(findings) >= 1
    assert decision["status"] == "PRODUCT_BETA_RC_BLOCKED_EXACT"
    assert decision["finding_count"] == len(findings)


def test_seal_and_resigned_semantic_mutations_are_rejected() -> None:
    seal = _json("seal_breaking_mutation_results.json")
    semantic = _json("resigned_raw_semantic_mutation_results.json")
    registry = _jsonl("resigned_raw_semantic_mutation_registry.jsonl")
    assert seal["status"] == "PASS"
    assert seal["executed"] == seal["rejected"] == 5
    assert semantic["status"] == "PASS"
    assert semantic["executed"] == semantic["rejected"] == len(registry) == 23
    assert all(row["result"] == "REJECTED_SEMANTIC" for row in semantic["results"])


def test_historical_deployment_is_not_claimed_after_amds_block() -> None:
    canary = _json("canary_and_rollback_decision.json")
    assert canary["status"] == "NOT_RUN"
    assert canary["canonical_slot_manager_unit_execution"] == "PASS"
    assert canary["real_historical_repaired_slot_switch"] == "NOT_RUN"
    assert canary["real_historical_exact_rollback"] == "NOT_RUN"
