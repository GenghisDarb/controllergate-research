from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs/post_v2_37_hardening_batch094_value_bound_rpir_fresh_amds_cohort_historical_closure"


def load(name: str) -> dict:
    return json.loads((OUT / name).read_text(encoding="utf-8"))


def test_critic_reconstructs_actual_blocked_evidence() -> None:
    reconstruction = load("standalone_critic_reconstruction_v3.json")
    assert reconstruction["status"] == "PASS"
    assert reconstruction["reconstructed"]["frozen_candidates"] == 8
    assert reconstruction["reconstructed"]["materialized_candidates"] == 6
    assert reconstruction["reconstructed"]["patch_operation_count"] == 0


def test_critic_reports_blockers_instead_of_empty_success() -> None:
    findings = [json.loads(line) for line in (OUT / "standalone_critic_findings_v3.jsonl").read_text(encoding="utf-8").splitlines() if line]
    assert len(findings) >= 7
    blockers = {row.get("blocker") for row in findings}
    assert "BLOCK_MINIMUM_COHORT_NOT_MET" in blockers
    assert "HUMAN_AUTHORIZATION_BLOCKED_EXACT" in blockers


def test_physical_mutations_are_rejected() -> None:
    seal = load("seal_breaking_mutation_results_v3.json")
    semantic = load("resigned_actual_evidence_mutation_results.json")
    assert seal["status"] == "PASS"
    assert seal["executed"] == seal["rejected"] >= 2
    assert semantic["status"] == "PASS"
    assert semantic["executed"] == semantic["rejected"] >= 12


def test_claim_boundary_preserves_counts_and_disabled_authority() -> None:
    claim = load("batch094_claim_boundary.json")
    assert claim["status"] == "PRODUCT_BETA_RC_BLOCKED_EXACT"
    assert claim["protocol"] == "v2.19"
    assert claim["package_version"] == "0.2.0b2.dev0"
    assert (claim["issue_derived_repair_count"], claim["native_external_repair_count"], claim["historical_increment"]) == (6, 4, 0)
    assert claim["full_scoring"] == "NOT_RUN/disallowed"
    assert claim["public_writes"] == claim["automatic_merge"] == "inactive"
    assert claim["production_readiness"] is False


def test_portable_manifests_have_no_self_entries() -> None:
    for name in ("ARTIFACT_SHA256SUMS.txt", "PORTABLE_ARTIFACT_SHA256SUMS.txt", "SHA256SUMS.txt"):
        paths = [line.split("  ", 1)[1] for line in (OUT / name).read_text(encoding="utf-8").splitlines() if line]
        assert name not in paths


def test_public_state_is_current_not_promoted() -> None:
    sync = load("public_state_sync_audit.json")
    assert sync["status"] == "PASS"
    for path in (ROOT / "README.md", ROOT / "docs/current_status.md", ROOT / "docs/capability_inventory.md", ROOT / "docs/public_release_readiness.md"):
        text = path.read_text(encoding="utf-8")
        assert "Batch094" in text
        assert "PRODUCT_BETA_RC_BLOCKED_EXACT" in text
