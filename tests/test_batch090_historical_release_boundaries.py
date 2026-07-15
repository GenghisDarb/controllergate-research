from __future__ import annotations

import ast
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs/post_v2_37_hardening_batch090_evidence_delaundering_installed_vertical_closure"


def load(name: str) -> dict:
    return json.loads((OUT / name).read_text(encoding="utf-8"))


def test_historical_amds_freezes_smaller_cohort_without_fabrication() -> None:
    frame = load("amds_historical_frozen_frame.json")
    gate = load("amds_historical_quality_gate.json")
    assert frame["frozen_before_truth_access"] is True
    assert frame["frozen_cohort_size"] < frame["target_cohort_size"]
    assert gate["status"] == "BLOCK_MINIMUM_COHORT_NOT_MET"
    assert gate["prospective_effectiveness"] == "NOT_ESTABLISHED"


def test_non_source_pool_is_ordered_and_authority_is_not_minted() -> None:
    eligibility = load("non_source_episode_eligibility.json")
    results = load("non_source_historical_results.json")
    assert eligibility["bare_import_or_filename_search_accepted"] is False
    assert results["historical_increment"] == 0
    assert all(not row["source_ownership_token"] and not row["repair_license"] for row in results["records"])


def test_release_boundary_stays_exact_and_counts_are_locked() -> None:
    decision = load("batch090_internal_release_decision.json")
    claim = load("batch090_claim_boundary.json")
    assert decision["status"] in {"PRODUCT_BETA_RC_BLOCKED_EXACT", "PRODUCT_BETA_RC_EXTERNAL_REVIEW_PENDING"}
    assert decision["package_version"] == "0.2.0b2.dev0"
    assert (decision["issue_derived_repair_count"], decision["native_external_repair_count"], decision["historical_repair_increment"]) == (6, 4, 0)
    assert claim["production_readiness"] is False
    assert claim["self_maintaining_software"] == "false/not demonstrated"


def test_standalone_critic_has_no_controllergate_or_builder_imports() -> None:
    source = (ROOT / "scripts/batch090_standalone_internal_critic.py").read_text(encoding="utf-8")
    tree = ast.parse(source)
    imports = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            imports.append(node.module or "")
    assert not any(name.startswith("controllergate") or "batch089" in name or "batch090" in name for name in imports)
