from __future__ import annotations

import json
from pathlib import Path


MATRIX_PATH = Path("configs/notebooklm_advice_traceability_matrix.json")

REQUIRED_IDS = {
    "artifact_byte_custody",
    "workspace_transport_integrity",
    "external_candidate_registry",
    "baseline_registry_snapshot",
    "semantic_failure_signature",
    "structural_navigation_map",
    "active_probe_router",
    "candidate_admission_decision_map",
    "coupled_dependency_projection_map",
    "interlock_invariant_map",
    "source_commit_environment_lock",
    "target_command_manifest",
    "fresh_workspace_purity_gate",
    "baseline_registry_drift_precheck",
    "rollback_block_ledger",
    "global_curvature_logic_enforcement",
    "curvature_feature_vector",
    "basin_stability_check",
    "two_winner_global_policy",
    "curvature_memory_routing",
    "curvature_fragment_planning",
    "null_ensemble_curvature_fairness",
    "curvature_claim_boundary",
    "batch013_gate_chain_binding",
    "targeted_seed_git_tracking",
    "active_context_filtering",
    "curvature_heuristic_freeze",
    "five_locks_curvature_cross_gate",
    "issue_derived_temporal_classification",
    "issue_derived_harness",
    "issue_text_temporal_guard",
    "issue_derived_latent_risk",
    "matched_null_comparison_arms",
    "matched_null_ensemble",
    "failure_memory_weighting",
    "duplicate_clean_replay",
    "no_overreach_validation",
    "bounded_micro_reversal",
    "bounded_exploration_budget",
    "execution_environment_normalization",
    "context_boundary_pinning",
    "public_claim_boundary_audit",
    "bugsinpy_global_block",
    "cryptographic_evidence_ledger_sealing",
    "public_release_readiness_gate",
    "v3_readiness_gate",
}


def _matrix() -> dict[str, object]:
    return json.loads(MATRIX_PATH.read_text(encoding="utf-8"))


def test_every_required_advice_id_is_present() -> None:
    entries = _matrix()["entries"]
    present = {entry["advice_id"] for entry in entries}
    assert REQUIRED_IDS <= present


def test_issue_derived_harness_cannot_be_active_when_unexercised() -> None:
    entries = {entry["advice_id"]: entry for entry in _matrix()["entries"]}
    assert entries["issue_derived_harness"]["status"] == "implemented_partial"
    assert "issue_derived_path_not_exercised" in entries["issue_derived_harness"]["blockers"]
