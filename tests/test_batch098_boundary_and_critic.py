from __future__ import annotations

import importlib.util
import json
from pathlib import Path

from controllergate.amds.batch098_diagnose import diagnose_batch098
from controllergate.cli import main


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs" / "post_v2_37_hardening_batch098_causal_hypergraph_real_materialization_topology_probe_closure"


def _critic_module():
    path = ROOT / "scripts" / "batch098_standalone_critic_v7.py"
    spec = importlib.util.spec_from_file_location("batch098_standalone_critic", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_read_only_cli_inspects_contracts_without_actuation(capsys) -> None:
    result = main(["evidence", "inspect-contracts", "--contracts", str(ROOT / "configs" / "candidate_execution_contracts_v2.jsonl")])
    assert result == 0
    value = json.loads(capsys.readouterr().out)
    assert value["status"] == "PASS"
    assert value["candidate_count"] == 8
    assert value["read_only"] is True
    assert value["patch_operation_count"] == 0


def test_amds_subtree_stops_at_frozen_eight_gate(tmp_path: Path) -> None:
    result = diagnose_batch098(tmp_path / "evidence", tmp_path / "topology", ROOT / "configs" / "candidate_execution_contracts_v2.jsonl", tmp_path / "out")
    assert result["status"] == "SCIENTIFIC_BLOCK"
    assert result["exact_blocker"] == "batch098_frozen_eight_materialization_gate_not_met"
    assert (tmp_path / "out" / "eight_episode_materialization_gate_v2.json").is_file()
    assert not (tmp_path / "out" / "role_measurement_execution_receipts_v6.jsonl").exists()


def test_standalone_critic_rejects_semantic_mutation(tmp_path: Path) -> None:
    critic = _critic_module()
    clean = tmp_path / "clean"; clean.mkdir()
    (clean / "evidence.json").write_text(json.dumps({"patch_operation_count": 0, "caller_supplied_decisive_input_count": 0}), encoding="utf-8")
    assert critic.scan_tree(clean)["status"] == "PASS"
    (clean / "evidence.json").write_text(json.dumps({"patch_operation_count": 1}), encoding="utf-8")
    result = critic.scan_tree(clean)
    assert result["status"] == "BLOCK"
    assert result["findings"][0]["finding"] == "ORDINARY_RUN_ACTUATION_OR_COUNT"


def test_tld_private_direct_source_custody_is_not_a_ci_claim() -> None:
    coverage = json.loads((OUT / "tld_direct_source_coverage_v1.json").read_text(encoding="utf-8"))
    identity = json.loads((OUT / "tld_direct_bundle_canonical_identity_v1.json").read_text(encoding="utf-8"))
    status = json.loads((OUT / "batch098_tld_direct_source_current_status.json").read_text(encoding="utf-8"))
    assert coverage["status"] == "PASS_44_OF_44"
    assert identity["status"] == "PASS_BYTE_IDENTICAL_REBUILD"
    assert status["github_raw_tld_custody"] == "NOT_APPLICABLE_PRIVATE_DIRECT_SOURCE_MODE"
    assert status["github_scientific_workflow"] == "NOT_RUN_PRIVATE_SOURCE_MODE"


def test_public_boundary_preserves_locked_claims() -> None:
    decision = json.loads((OUT / "batch098_internal_release_decision.json").read_text(encoding="utf-8"))
    claims = json.loads((OUT / "batch098_claim_boundary.json").read_text(encoding="utf-8"))
    assert decision["status"] == "PRODUCT_BETA_RC_BLOCKED_EXACT"
    assert decision["exact_blockers"] == ["BATCH098_LOCAL_PROVIDER_INTERPRETER_PARITY_BLOCKED_EXACT"]
    assert claims["protocol"] == "v2.19"
    assert claims["package_version"] == "0.2.0b2.dev0"
    assert claims["issue_derived_repairs"] == 6
    assert claims["native_external_repairs"] == 4
    assert claims["historical_increment"] == 0


def test_public_workflow_cannot_acquire_private_tld_sources() -> None:
    workflow = (ROOT / ".github" / "workflows" / "post_v2_37_hardening_batch098_causal_hypergraph_real_materialization_topology_probe_closure.yml").read_text(encoding="utf-8")
    assert "CONTROLLERGATE_TLD_BUNDLE_URL" not in workflow
    assert "tld_source_artifact_id" not in workflow
    assert "PUBLIC_REGRESSION_NO_PRIVATE_TLD" in workflow
    assert "if: ${{ false }}" in workflow
    assert not (ROOT / ".github" / "workflows" / "controllergate_batch098_tld_source_custody_bridge.yml").exists()
    assert "materialize-candidate" in workflow
    assert "truth_blind_amds_candidate_groups" in workflow
    assert "retention-days: 30" in workflow
