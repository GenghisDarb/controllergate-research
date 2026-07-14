from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs/post_v2_37_hardening_batch086_historical_lifecycle_dpp14_product_beta_rc"


def read(name: str) -> dict:
    return json.loads((OUT / name).read_text(encoding="utf-8"))


def test_both_historical_providers_are_reconstructed_not_exact():
    records = read("historical_provider_reconstruction_results.json")["providers"]
    assert set(records) == {"cloudpickle_507_py313_typevar_distutils", "freezegun_547_py313_datetimes_assertion"}
    assert all(item["classification"] == "HISTORICAL_PROVIDER_RECONSTRUCTED_EQUIVALENT" for item in records.values())
    assert all(item["called_exact"] is False for item in records.values())


def test_complete_repair_lifecycles_use_preserved_patches_and_real_targets():
    expected = {
        "cloudpickle_507_py313_typevar_distutils_historical_lifecycle.json": "a06b5343f41a49daaa9d6902513966c6796e44124640ba29fcf80ede99d06e63",
        "freezegun_547_py313_datetimes_assertion_historical_lifecycle.json": "8daf31c4d59ead1832aa3bdc6260bae3c92a1052f140c9f0442a550c4ebf3247",
    }
    for name, patch in expected.items():
        result = read(name)
        assert result["complete"] and result["patch_sha256"] == patch
        assert result["validation"]["returncode"] == result["duplicate_clean_replay"]["returncode"] == 0
        assert all(item["returncode"] == 0 for item in result["canary_runs"])
        assert result["health"]["status"] == result["rollback"]["status"] == "PASS"
        assert result["repair_count_increment"] == 0


def test_two_non_source_terminals_abstain_without_license():
    results = read("historical_non_source_lifecycle_results.json")["results"]
    assert [(item["candidate_id"], item["terminal"]) for item in results] == [
        ("audioread_144_py313_aifc_removed", "provider_owned"),
        ("prospective_yxyxy_hordeforge_issue_39", "harness_owned"),
    ]
    assert all(item["complete"] and item["safe_abstention"] and not item["repair_license"] for item in results)


def test_dpp14_quality_and_interlock_boundaries():
    quality = read("dpp14_quality_gate.json")
    assert quality["status"] == "PASS" and quality["wrong_repair_authorization"] == 0
    assert quality["safe_abstention_accuracy"] >= 0.8 and len(quality["terminal_classes"]) >= 3
    assert read("historical_interlock_audit.json")["interlocks_can_authorize_patch"] is False
    assert read("causal_elbow_audit.json")["numeric_threshold_authority"] is False


def test_failed_branches_and_counts_are_preserved():
    branches = read("failed_reaction_branch_lineage.json")["branches"]
    assert branches and all(item["count_increment"] == 0 for item in branches)
    claims = read("batch086_claim_boundary.json")
    assert (claims["issue_derived_repair_count"], claims["native_external_repair_count"]) == (6, 4)
    assert claims["historical_replay_count_increment"] == 0


def test_product_beta_rc_pass_is_bounded():
    decision = read("batch086_product_beta_rc_decision.json")
    claims = read("batch086_claim_boundary.json")
    assert decision["status"] == "PRODUCT_BETA_RC_PASS" and decision["package_version"] == "0.2.0b1"
    assert claims["production_readiness"] is False
    assert claims["self_maintaining_software"] == "false/not demonstrated"
    assert claims["full_scoring"] == "NOT_RUN/disallowed"
