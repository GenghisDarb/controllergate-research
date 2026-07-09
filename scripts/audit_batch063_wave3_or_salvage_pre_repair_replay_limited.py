from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from controllergate.core.manifests import verify_manifest


OUT_DIR = ROOT / "outputs" / "post_v2_37_hardening_batch063_wave3_or_salvage_pre_repair_replay_limited"
CURRENT_PROTOCOL = "v2.14"
EXPECTED_CANDIDATES = {
    "pytest_13895_pytest9_skiptest_behavior",
    "freezegun_547_py313_datetimes_assertion",
}

PUBLIC_FORBIDDEN_TERMS = [
    "TLD",
    "TORUS",
    "chromosomal",
    "biological",
    "ToT-BULB",
    "metrological immune system",
    "replisome",
    "nuclear pore",
    "MCM",
    "6-set",
    "14-set",
    "196-set",
]

FORBIDDEN_STATUS_FRAGMENTS = [
    ".zip",
    ".tar",
    ".tgz",
    ".7z",
    ".pyc",
    "__pycache__",
    "ControllerGate_runtime",
    "artifact_payload",
    ".venv",
    "/venv/",
    "\\venv\\",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
]

REQUIRED_COMMON_FILES = [
    "batch058c_artifact_ingestion_summary.json",
    "batch058c_artifact_sha256_verification.json",
    "batch058c_result_preservation.json",
    "batch058c_approved_replay_candidate_preservation.json",
    "batch058c_audioread_terminal_state_preservation.json",
    "batch058c_salvage_reassessment_preservation.json",
    "batch058c_claim_boundary_preservation.json",
    "batch058c_next_action_boundary.json",
    "batch063_candidate_scope.json",
    "batch063_candidate_scope_audit.json",
    "batch063_excluded_candidate_registry.json",
    "batch063_decision_time_input_manifest.json",
    "batch063_forbidden_evidence_audit.json",
    "batch063_issue_body_leakage_boundary.json",
    "batch063_label_blindness_check.json",
    "batch063_gold_patch_exclusion_check.json",
    "batch063_future_evidence_exclusion_check.json",
    "batch063_amds_full_bug_tree_state.json",
    "batch063_amds_candidate_node_registry.json",
    "batch063_amds_candidate_edge_registry.json",
    "batch063_amds_secondary_bug_registry.json",
    "batch063_amds_tertiary_bug_registry.json",
    "batch063_amds_provider_dependency_branch_registry.json",
    "batch063_amds_interpreter_behavior_branch_registry.json",
    "batch063_amds_test_expectation_branch_registry.json",
    "batch063_amds_unrecoverable_branch_registry.json",
    "batch063_amds_repairable_branch_registry.json",
    "batch063_amds_next_action_frontier.json",
    "batch063_materialization_results.json",
    "batch063_candidate_routing_matrix.json",
    "batch063_future_patch_gate_candidates.json",
    "batch063_future_decomposition_candidates.json",
    "batch063_future_provider_recovery_candidates.json",
    "batch063_retired_or_unrecoverable_candidates.json",
    "batch063_manual_review_candidates.json",
    "pre_repair_replay_limited_pattern_library.json",
    "wave3_or_salvage_replay_route_pattern.json",
    "materialized_failure_to_patch_license_route.json",
    "failure_not_reproduced_terminal_pattern.json",
    "provider_runtime_block_to_capsule_route.json",
    "salvage_candidate_replay_pattern_update.json",
    "pytest_candidate_pattern_update.json",
    "freezegun_salvage_pattern_update.json",
    "project_health_review_batch063.json",
    "capability_maturity_scorecard_batch063.json",
    "version_progress_grade_batch063.json",
    "strategic_direction_check_batch063.json",
    "proof_milestone_distance_report_batch063.json",
    "regression_and_drift_watch_batch063.json",
    "recurring_bottleneck_trend_report_batch063.json",
    "self_maintenance_readiness_review_batch063.json",
    "next_highest_impact_action_report_batch063.json",
    "tld_governance_boundary_batch063.json",
    "reactome_provider_capsule_boundary_batch063.json",
    "internal_theory_to_engineering_translation_batch063.json",
    "public_language_neutrality_check_batch063.json",
    "public_summary_claim_safety_check_batch063.json",
    "batch063_final_decision.json",
    "batch064_patch_gate_recommendation.json",
    "batch064_failure_decomposition_recommendation.json",
    "batch063b_provider_runtime_recovery_recommendation.json",
    "batch057d_freezegun_provider_portability_recommendation.json",
    "batch058d_seed_discovery_expansion_recommendation.json",
    "batch063_summary.md",
    "claim_boundary.json",
    "audit.json",
    "package_verification.json",
    "artifact_sha256_verification.json",
    "SHA256SUMS.txt",
]

CANDIDATE_FILE_SUFFIXES = [
    "workspace_manifest.json",
    "commit_verification.json",
    "workspace_custody_check.json",
    "baseline_source_hashes.json",
    "command_context.json",
    "command_normalization.json",
    "declared_dependency_map.json",
    "declared_runtime_map.json",
    "declared_test_command_map.json",
    "provider_runtime_capsule_plan.json",
    "provider_runtime_precondition_check.json",
    "provider_install_attempt.json",
    "provider_runtime_setup_result.json",
    "prerepair_replay_command.txt",
    "prerepair_replay_log_raw.txt",
    "prerepair_replay_result.json",
    "prerepair_failure_signature_extract.json",
    "prerepair_outcome_classification.json",
    "diagnostic_probe_budget.json",
    "amds_bug_tree_state.json",
    "amds_node_registry.json",
    "amds_next_action_frontier.json",
    "patch_license_from_amds.json",
    "source_contact_prior_or_replay_map.json",
    "provider_dependency_replay_map.json",
    "interpreter_behavior_replay_map.json",
]

DIAGNOSTIC_SUFFIXES = [
    "diagnostic_minimal_replay_plan",
    "diagnostic_minimal_replay_results",
    "diagnostic_traceback_roots",
    "diagnostic_failure_signature_extract",
    "diagnostic_failed_node_registry",
]

PRIOR_AUDITS = [
    "scripts/audit_batch058c_seed_discovery_expansion_or_salvage_reassessment.py",
    "scripts/audit_batch060f_audioread_provider_backend_capsule_replay.py",
    "scripts/audit_batch058b_seed_discovery_wave_3_expansion.py",
    "scripts/audit_batch062_next_issue_repair_candidate_selection_or_wave3_expansion.py",
    "scripts/audit_batch061_duplicate_clean_replay_count_gate_cloudpickle_wave_3.py",
    "scripts/audit_batch060d_cloudpickle_class_dict_patch_gate_with_amds_health_review.py",
    "scripts/audit_batch060c_cloudpickle_provider_runtime_recovery.py",
    "scripts/audit_batch060b_cloudpickle_decomposition_audioread_provider_preservation.py",
    "scripts/audit_batch060_source_only_patch_gate_wave_3.py",
    "scripts/audit_batch059_pre_repair_replay_wave_3_limited.py",
    "scripts/audit_batch058_seed_discovery_wave_3_provider_prescreen.py",
    "scripts/audit_batch056f_timeout_split_replay_wave_2.py",
    "scripts/audit_batch056e_timeout_candidate_decomposition_wave_2_provider_capsules.py",
    "scripts/audit_batch056d_wave2_provider_dependency_recovery.py",
    "scripts/audit_batch056b_wave2_pre_repair_replay_plus_amds_bridge.py",
    "scripts/audit_batch057c_layered_source_only_patch_recovery_freezegun.py",
    "scripts/audit_batch057b_failure_family_decomposition_elbow_recovery.py",
    "scripts/audit_batch057_source_only_patch_gate_wave_1.py",
    "scripts/audit_batch056_pre_repair_replay_wave_1_plus_wave_2_intake.py",
    "scripts/audit_batch055_seed_discovery_wave_1.py",
    "scripts/audit_post_v2_37_hardening_and_batch002.py",
]


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def expect(errors: list[str], condition: bool, message: str) -> None:
    if not condition:
        errors.append(message)


def git_lines(*args: str) -> list[str]:
    proc = subprocess.run(["git", *args], cwd=ROOT, text=True, capture_output=True, check=False)
    return proc.stdout.splitlines()


def run_python_script(rel: str, errors: list[str]) -> None:
    proc = subprocess.run([sys.executable, rel], cwd=ROOT, text=True, capture_output=True, check=False)
    if proc.returncode != 0:
        errors.append(f"{rel} failed: {proc.stdout[-1000:]} {proc.stderr[-1000:]}")


def audit_git_status(errors: list[str]) -> None:
    for line in git_lines("status", "--short"):
        normalized = line[3:].replace("\\", "/") if len(line) > 3 else line.replace("\\", "/")
        if line.startswith("?? incoming_artifacts/"):
            continue
        for fragment in FORBIDDEN_STATUS_FRAGMENTS:
            if fragment in normalized:
                errors.append(f"forbidden path appears in git status: {line}")
                break


def public_batch063_block(path: Path) -> str:
    text = path.read_text(encoding="utf-8")
    marker = "Batch063 is the latest limited pre-repair replay boundary."
    start = text.find(marker)
    if start == -1:
        return ""
    next_marker = text.find("Batch058c is the latest seed-discovery and salvage-reassessment boundary.", start)
    if next_marker == -1:
        next_marker = min(len(text), start + 4500)
    return text[start:next_marker]


def audit_public_summary(errors: list[str]) -> None:
    for rel in [
        "README.md",
        "docs/current_status.md",
        "controllergate_v1_7_beta/reports/critic_review_package/shareable_summary.md",
    ]:
        block = public_batch063_block(ROOT / rel)
        expect(errors, bool(block), f"missing Batch063 public summary block in {rel}")
        for phrase in [
            "Workflow success is not equivalent to repair success.",
            "Pre-repair replay is not repair success.",
            "Diagnostic replay is not repair success.",
            "Provider/runtime setup is not repair success.",
            "Future patch license is not repair success.",
            "Repair count increments require duplicate clean replay and count gate.",
            "Self-maintaining software remains false/not_demonstrated.",
        ]:
            expect(errors, phrase in block, f"Batch063 public summary missing {phrase!r} in {rel}")
        lowered = block.lower()
        for term in PUBLIC_FORBIDDEN_TERMS:
            expect(errors, term.lower() not in lowered, f"Batch063 public summary contains internal term {term!r} in {rel}")


def main() -> int:
    errors: list[str] = []
    if not OUT_DIR.is_dir():
        print(f"FAIL: missing output directory: {OUT_DIR.relative_to(ROOT)}")
        return 1
    for rel in REQUIRED_COMMON_FILES:
        expect(errors, (OUT_DIR / rel).is_file(), f"missing required Batch063 output: {rel}")
    for candidate_id in EXPECTED_CANDIDATES:
        for suffix in CANDIDATE_FILE_SUFFIXES:
            expect(errors, (OUT_DIR / f"{candidate_id}_{suffix}").is_file(), f"missing {candidate_id}_{suffix}")
        for suffix in DIAGNOSTIC_SUFFIXES:
            regular = OUT_DIR / f"{candidate_id}_{suffix}.json"
            not_run = OUT_DIR / f"{candidate_id}_{suffix}_not_run_reason.json"
            expect(errors, regular.is_file() or not_run.is_file(), f"missing diagnostic artifact for {candidate_id}_{suffix}")
        install_log = OUT_DIR / f"{candidate_id}_provider_install_log_raw.txt"
        install_skip = OUT_DIR / f"{candidate_id}_provider_install_not_run_reason.txt"
        expect(errors, install_log.is_file() or install_skip.is_file(), f"missing provider install log or not-run reason for {candidate_id}")
    if errors:
        print("FAIL:")
        for error in errors:
            print(f"- {error}")
        return 1

    manifest = verify_manifest(OUT_DIR)
    expect(errors, manifest.get("status") == "PASS", f"Batch063 SHA256SUMS verification failed: {manifest}")

    final = read_json(OUT_DIR / "batch063_final_decision.json")
    claim = read_json(OUT_DIR / "claim_boundary.json")
    ingest = read_json(OUT_DIR / "batch058c_artifact_ingestion_summary.json")
    artifact = read_json(OUT_DIR / "batch058c_artifact_sha256_verification.json")
    preservation = read_json(OUT_DIR / "batch058c_result_preservation.json")
    candidates = read_json(OUT_DIR / "batch063_candidate_scope.json")
    scope_audit = read_json(OUT_DIR / "batch063_candidate_scope_audit.json")
    forbidden = read_json(OUT_DIR / "batch063_forbidden_evidence_audit.json")
    materialization = read_json(OUT_DIR / "batch063_materialization_results.json")
    routing = read_json(OUT_DIR / "batch063_candidate_routing_matrix.json")
    public_language = read_json(OUT_DIR / "public_language_neutrality_check_batch063.json")
    tld = read_json(OUT_DIR / "tld_governance_boundary_batch063.json")
    reactome = read_json(OUT_DIR / "reactome_provider_capsule_boundary_batch063.json")
    package = read_json(OUT_DIR / "package_verification.json")

    expect(errors, ingest.get("status") == "PASS", "Batch058c artifact ingest did not pass")
    expect(errors, artifact.get("status") == "PASS", "Batch058c artifact verification did not pass")
    expect(errors, artifact.get("zip_sha256") == "72bdb40847f50d7a6e752eaea622ed9c34543d58d4b7aa5747f5a298b4f0ab3c", "Batch058c artifact SHA mismatch")
    expect(errors, artifact.get("zip_size_bytes") == 76982, "Batch058c artifact size mismatch")
    expect(errors, artifact.get("zip_entry_count") == 73, "Batch058c artifact entry count mismatch")
    expect(errors, artifact.get("artifact_manifest", {}).get("status") == "PASS", "Batch058c artifact manifest failed")
    expect(errors, artifact.get("output_manifest", {}).get("status") == "PASS", "Batch058c output manifest failed")
    expect(errors, preservation.get("issue_derived_repair_count") == 3, "Issue-derived repair count not preserved at 3")
    expect(errors, preservation.get("native_external_repair_count") == 4, "Native external repair count not preserved at 4")
    expect(errors, preservation.get("full_scoring") == "NOT_RUN/disallowed", "Full scoring boundary changed")
    expect(errors, preservation.get("memory_lift") == "not_demonstrated", "Memory lift boundary changed")
    expect(errors, preservation.get("self_maintaining_software") == "false/not_demonstrated", "Self-maintaining boundary changed")
    expect(errors, set(candidates.get("allowed_candidate_ids", [])) == EXPECTED_CANDIDATES, "Batch063 candidate scope is not exactly Pytest and Freezegun")
    expect(errors, scope_audit.get("operated_only_on_allowed_candidates") is True, "Batch063 scope audit did not pass")
    expect(errors, scope_audit.get("audioread_reopened") is False, "Audioread was reopened")
    expect(errors, scope_audit.get("cloudpickle_reopened") is False, "Cloudpickle counted repair was reopened")
    for key in ["fixed_commit_used", "future_commit_used", "pr_patch_used", "gold_patch_used", "issue_body_fix_or_workaround_text_used", "hidden_label_used", "test_modification_used", "synthetic_test_used"]:
        expect(errors, forbidden.get(key) is False, f"Forbidden evidence audit expected {key}=false")

    expect(errors, final.get("status") == "PASS", "Batch063 final decision did not pass")
    expect(errors, final.get("current_protocol") == CURRENT_PROTOCOL, "Current protocol is not v2.14")
    expect(errors, final.get("issue_derived_repair_count") == 3, "Final issue-derived repair count changed")
    expect(errors, final.get("native_external_repair_count") == 4, "Final native external repair count changed")
    expect(errors, final.get("full_scoring") == "NOT_RUN/disallowed", "Final full scoring changed")
    expect(errors, final.get("memory_lift") == "not_demonstrated", "Final memory lift changed")
    expect(errors, final.get("self_maintaining_software") == "false/not_demonstrated", "Final self-maintaining changed")
    for key in ["patch_generated", "patch_applied", "post_repair_replay_run", "duplicate_replay_run", "count_gate_run", "repair_count_increment"]:
        expect(errors, final.get(key) is False, f"Batch063 final expected {key}=false")
        expect(errors, claim.get(key) is False, f"Batch063 claim boundary expected {key}=false")
    expect(errors, materialization.get("status") == "PASS", "Materialization results missing")
    expect(errors, routing.get("status") == "PASS", "Candidate routing matrix missing")
    expect(errors, public_language.get("status") == "PASS", "Public language neutrality check failed")
    expect(errors, tld.get("internal_governance_audit_logic_only") is True, "TLD boundary must remain internal governance/audit only")
    expect(errors, reactome.get("provider_capsule_step_gating_pattern_only") is True, "Reactome boundary must remain provider-capsule pattern only")
    expect(errors, package.get("raw_zip_payload_committed") is False, "Raw ZIP payload must not be committed")
    expect(errors, package.get("runtime_workspaces_committed") is False, "Runtime workspaces must not be committed")
    expect(errors, package.get("source_checkouts_committed") is False, "Source checkouts must not be committed")
    expect(errors, package.get("venvs_committed") is False, "Venvs must not be committed")
    expect(errors, package.get("caches_committed") is False, "Caches must not be committed")

    for candidate_id in EXPECTED_CANDIDATES:
        commit = read_json(OUT_DIR / f"{candidate_id}_commit_verification.json")
        custody = read_json(OUT_DIR / f"{candidate_id}_workspace_custody_check.json")
        provider = read_json(OUT_DIR / f"{candidate_id}_provider_runtime_setup_result.json")
        replay = read_json(OUT_DIR / f"{candidate_id}_prerepair_replay_result.json")
        outcome = read_json(OUT_DIR / f"{candidate_id}_prerepair_outcome_classification.json")
        amds = read_json(OUT_DIR / f"{candidate_id}_amds_bug_tree_state.json")
        license_ = read_json(OUT_DIR / f"{candidate_id}_patch_license_from_amds.json")
        expect(errors, commit.get("status") == "PASS", f"{candidate_id} commit verification did not pass")
        expect(errors, custody.get("status") == "PASS", f"{candidate_id} workspace custody did not pass")
        expect(errors, provider.get("classification") in {"provider_runtime_ready", "provider_runtime_recovered_from_declared_metadata", "provider_runtime_partial", "blocked_no_declared_provider_setup", "blocked_dependency_install_failure", "blocked_python_version_unavailable", "blocked_unbounded_provider", "blocked_forbidden_evidence_risk", "manual_review_needed"}, f"{candidate_id} provider classification invalid")
        expect(errors, replay.get("outcome_classification") in {"pre_repair_failure_materialized", "failure_not_reproduced", "blocked_provider_runtime", "blocked_dependency_install_failure", "blocked_python_version_unavailable", "blocked_target_command_invalid", "blocked_native_test_path_missing", "blocked_unbounded_runtime", "blocked_manual_review_needed"}, f"{candidate_id} replay classification invalid")
        expect(errors, outcome.get("classification") == replay.get("outcome_classification"), f"{candidate_id} outcome classification mismatch")
        expect(errors, amds.get("status") == "PASS", f"{candidate_id} AMDS state missing")
        expect(errors, license_.get("future_only") is True, f"{candidate_id} patch license must be future-only")
        expect(errors, license_.get("batch063_patch_authorized") is False, f"{candidate_id} patch must not be authorized in Batch063")
        if replay.get("outcome_classification") == "pre_repair_failure_materialized":
            expect(errors, (OUT_DIR / f"{candidate_id}_diagnostic_minimal_replay_plan.json").is_file(), f"{candidate_id} materialized but diagnostic plan missing")
        else:
            expect(errors, (OUT_DIR / f"{candidate_id}_diagnostic_minimal_replay_plan_not_run_reason.json").is_file(), f"{candidate_id} diagnostic must be not-run when original failure does not materialize")

    audit_public_summary(errors)
    audit_git_status(errors)
    for rel in PRIOR_AUDITS:
        run_python_script(rel, errors)
    proc = subprocess.run([sys.executable, "scripts/controllergate_audit.py", "--protocol", "current"], cwd=ROOT, text=True, capture_output=True, check=False)
    expect(errors, proc.returncode == 0, f"current protocol audit failed: {proc.stdout[-1000:]} {proc.stderr[-1000:]}")
    proc = subprocess.run([sys.executable, "scripts/controllergate_run.py", "--protocol", "current", "--dry-run"], cwd=ROOT, text=True, capture_output=True, check=False)
    expect(errors, proc.returncode == 0, f"current protocol dry-run failed: {proc.stdout[-1000:]} {proc.stderr[-1000:]}")

    if errors:
        print("FAIL:")
        for error in errors:
            print(f"- {error}")
        return 1
    print("Batch063 wave3/salvage pre-repair replay limited audit PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
