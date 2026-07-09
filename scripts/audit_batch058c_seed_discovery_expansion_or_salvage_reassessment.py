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


OUT_DIR = ROOT / "outputs" / "post_v2_37_hardening_batch058c_seed_discovery_expansion_or_salvage_reassessment"
CURRENT_PROTOCOL = "v2.14"
EXPECTED_BATCH060F_SHA = "c1af9205b77e0c18e3c80dd10e529f8f3665832239f7afd2db6ba6383ae6d606"
EXPECTED_BATCH060F_SIZE = 56312
EXPECTED_BATCH060F_ENTRY_COUNT = 98
EXPECTED_BATCH060F_ARTIFACT_MANIFEST_CHECKED = 97
EXPECTED_BATCH060F_OUTPUT_MANIFEST_CHECKED = 96
EXPECTED_NEXT_ACTION = "batch063_wave3_or_salvage_pre_repair_replay_limited"

REQUIRED_FILES = [
    "batch060f_artifact_ingestion_summary.json",
    "batch060f_artifact_sha256_verification.json",
    "batch060f_result_preservation.json",
    "batch060f_audioread_branch_preservation.json",
    "batch060f_provider_backend_lesson_preservation.json",
    "batch060f_claim_boundary_preservation.json",
    "batch060f_next_action_boundary.json",
    "audioread_terminal_state_closure_batch058c.json",
    "audioread_reopen_condition_policy.json",
    "audioread_do_not_reprocess_without_provider_change.json",
    "audioread_provider_unavailable_pattern_update.json",
    "negative_seed_pattern_registry_batch058c.json",
    "provider_risk_rejection_pattern_update.json",
    "optional_backend_unavailable_terminal_pattern.json",
    "unbounded_provider_filter_update.json",
    "seed_discovery_negative_learning_summary.json",
    "seed_source_strategy_batch058c.json",
    "clean_candidate_profile_policy.json",
    "provider_light_candidate_profile.json",
    "candidate_source_diversification_plan.json",
    "twenty_seed_campaign_manager.json",
    "batch058c_raw_lead_registry.json",
    "batch058c_normalized_lead_registry.json",
    "batch058c_deduplicated_lead_registry.json",
    "batch058c_duplicate_rejection_registry.json",
    "batch058c_counted_overlap_check.json",
    "batch058c_parked_overlap_check.json",
    "batch058c_retired_overlap_check.json",
    "batch058c_issue_body_leakage_precheck.json",
    "batch058c_fixed_future_gold_precheck.json",
    "batch058c_provider_runtime_prescreen_results.json",
    "batch058c_candidate_expected_value_scores.json",
    "batch058c_candidate_proof_distance_scores.json",
    "batch058c_candidate_selection_matrix.json",
    "batch058c_approved_for_future_replay_registry.json",
    "batch058c_rejected_or_parked_registry.json",
    "batch058c_manual_review_registry.json",
    "wave1_wave2_salvage_reassessment_batch058c.json",
    "salvage_candidate_expected_value_batch058c.json",
    "salvage_candidate_risk_batch058c.json",
    "salvage_candidate_reopen_queue_batch058c.json",
    "salvage_candidate_retirement_update_batch058c.json",
    "self_maintaining_wrapper_function_gap_audit_batch058c.json",
    "autonomic_candidate_intake_readiness_batch058c.json",
    "autonomic_terminal_state_readiness_batch058c.json",
    "manual_intervention_reduction_report_batch058c.json",
    "repeat_bottleneck_elimination_plan_batch058c.json",
    "project_health_review_batch058c.json",
    "capability_maturity_scorecard_batch058c.json",
    "version_progress_grade_batch058c.json",
    "strategic_direction_check_batch058c.json",
    "proof_milestone_distance_report_batch058c.json",
    "regression_and_drift_watch_batch058c.json",
    "recurring_bottleneck_trend_report_batch058c.json",
    "next_highest_impact_action_report_batch058c.json",
    "tld_governance_boundary_batch058c.json",
    "reactome_provider_capsule_boundary_batch058c.json",
    "internal_theory_to_engineering_translation_batch058c.json",
    "public_language_neutrality_check_batch058c.json",
    "public_summary_claim_safety_check_batch058c.json",
    "batch058c_final_decision.json",
    "batch063_wave3_or_salvage_pre_repair_replay_recommendation.json",
    "batch058d_seed_discovery_expansion_recommendation.json",
    "batch062c_wave1_wave2_salvage_replay_selection_recommendation.json",
    "batch062b_repo_hygiene_utility_consolidation_planning_recommendation.json",
    "batch060f_audioread_future_reopen_recommendation.json",
    "batch058c_summary.md",
    "claim_boundary.json",
    "audit.json",
    "package_verification.json",
    "artifact_sha256_verification.json",
    "SHA256SUMS.txt",
]

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


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def expect(errors: list[str], condition: bool, message: str) -> None:
    if not condition:
        errors.append(message)


def expect_false(errors: list[str], obj: dict[str, Any], key: str, label: str) -> None:
    if obj.get(key) is not False:
        errors.append(f"{label} expected {key}=false, observed {obj.get(key)!r}")


def git_lines(*args: str) -> list[str]:
    proc = subprocess.run(["git", *args], cwd=ROOT, text=True, capture_output=True, check=False)
    return proc.stdout.splitlines()


def audit_git_status(errors: list[str]) -> None:
    for line in git_lines("status", "--short"):
        normalized = line[3:].replace("\\", "/") if len(line) > 3 else line.replace("\\", "/")
        if line.startswith("?? incoming_artifacts/"):
            continue
        for fragment in FORBIDDEN_STATUS_FRAGMENTS:
            if fragment in normalized:
                errors.append(f"forbidden path appears in git status: {line}")
                break


def public_batch058c_block(path: Path) -> str:
    text = path.read_text(encoding="utf-8")
    marker = "Batch058c is the latest seed-discovery and salvage-reassessment boundary."
    start = text.find(marker)
    if start == -1:
        return ""
    next_marker = text.find("Batch060f is the latest Audioread branch-replay boundary.", start)
    if next_marker == -1:
        next_marker = min(len(text), start + 4000)
    return text[start:next_marker]


def audit_public_summary(errors: list[str]) -> None:
    for rel in [
        "README.md",
        "docs/current_status.md",
        "controllergate_v1_7_beta/reports/critic_review_package/shareable_summary.md",
    ]:
        block = public_batch058c_block(ROOT / rel)
        expect(errors, bool(block), f"missing Batch058c public summary block in {rel}")
        for phrase in [
            "Workflow success is not equivalent to repair success.",
            "Seed discovery is not repair success.",
            "Provider/runtime pre-screening is not repair success.",
            "Repair count increments require duplicate clean replay and count gate.",
            "Self-maintaining software remains false/not_demonstrated.",
        ]:
            expect(errors, phrase in block, f"Batch058c public summary missing {phrase!r} in {rel}")
        lowered = block.lower()
        for term in PUBLIC_FORBIDDEN_TERMS:
            expect(errors, term.lower() not in lowered, f"Batch058c public summary contains internal term {term!r} in {rel}")


def main() -> int:
    errors: list[str] = []
    if not OUT_DIR.is_dir():
        print(f"FAIL: missing output directory: {OUT_DIR.relative_to(ROOT)}")
        return 1
    for rel in REQUIRED_FILES:
        if not (OUT_DIR / rel).is_file():
            errors.append(f"missing required Batch058c output: {rel}")
    if not errors:
        manifest = verify_manifest(OUT_DIR)
        if manifest.get("status") != "PASS":
            errors.append(f"Batch058c SHA256SUMS verification failed: {manifest}")
    if errors:
        print("FAIL:")
        for error in errors:
            print(f"- {error}")
        return 1

    artifact = read_json(OUT_DIR / "batch060f_artifact_sha256_verification.json")
    ingest = read_json(OUT_DIR / "batch060f_artifact_ingestion_summary.json")
    preservation = read_json(OUT_DIR / "batch060f_result_preservation.json")
    branch = read_json(OUT_DIR / "batch060f_audioread_branch_preservation.json")
    lesson = read_json(OUT_DIR / "batch060f_provider_backend_lesson_preservation.json")
    claim060f = read_json(OUT_DIR / "batch060f_claim_boundary_preservation.json")
    next060f = read_json(OUT_DIR / "batch060f_next_action_boundary.json")
    terminal = read_json(OUT_DIR / "audioread_terminal_state_closure_batch058c.json")
    reopen = read_json(OUT_DIR / "audioread_reopen_condition_policy.json")
    do_not = read_json(OUT_DIR / "audioread_do_not_reprocess_without_provider_change.json")
    patterns = read_json(OUT_DIR / "negative_seed_pattern_registry_batch058c.json")
    provider_filter = read_json(OUT_DIR / "provider_risk_rejection_pattern_update.json")
    strategy = read_json(OUT_DIR / "seed_source_strategy_batch058c.json")
    manager = read_json(OUT_DIR / "twenty_seed_campaign_manager.json")
    raw = read_json(OUT_DIR / "batch058c_raw_lead_registry.json")
    dedup = read_json(OUT_DIR / "batch058c_deduplicated_lead_registry.json")
    selection = read_json(OUT_DIR / "batch058c_candidate_selection_matrix.json")
    approved = read_json(OUT_DIR / "batch058c_approved_for_future_replay_registry.json")
    rejected = read_json(OUT_DIR / "batch058c_rejected_or_parked_registry.json")
    leakage = read_json(OUT_DIR / "batch058c_issue_body_leakage_precheck.json")
    fixed = read_json(OUT_DIR / "batch058c_fixed_future_gold_precheck.json")
    provider = read_json(OUT_DIR / "batch058c_provider_runtime_prescreen_results.json")
    salvage = read_json(OUT_DIR / "wave1_wave2_salvage_reassessment_batch058c.json")
    salvage_queue = read_json(OUT_DIR / "salvage_candidate_reopen_queue_batch058c.json")
    gap = read_json(OUT_DIR / "self_maintaining_wrapper_function_gap_audit_batch058c.json")
    health = read_json(OUT_DIR / "project_health_review_batch058c.json")
    tld = read_json(OUT_DIR / "tld_governance_boundary_batch058c.json")
    reactome = read_json(OUT_DIR / "reactome_provider_capsule_boundary_batch058c.json")
    translation = read_json(OUT_DIR / "internal_theory_to_engineering_translation_batch058c.json")
    public_language = read_json(OUT_DIR / "public_language_neutrality_check_batch058c.json")
    public_claim = read_json(OUT_DIR / "public_summary_claim_safety_check_batch058c.json")
    final = read_json(OUT_DIR / "batch058c_final_decision.json")
    batch063 = read_json(OUT_DIR / "batch063_wave3_or_salvage_pre_repair_replay_recommendation.json")
    audioread_reopen = read_json(OUT_DIR / "batch060f_audioread_future_reopen_recommendation.json")
    claim = read_json(OUT_DIR / "claim_boundary.json")
    package = read_json(OUT_DIR / "package_verification.json")

    expect(errors, artifact.get("status") == "PASS", "Batch060f artifact verification did not pass")
    expect(errors, artifact.get("zip_sha256") == EXPECTED_BATCH060F_SHA, "Batch060f artifact SHA mismatch")
    expect(errors, artifact.get("zip_size_bytes") == EXPECTED_BATCH060F_SIZE, "Batch060f artifact size mismatch")
    expect(errors, artifact.get("zip_entry_count") == EXPECTED_BATCH060F_ENTRY_COUNT, "Batch060f artifact entry count mismatch")
    expect(errors, artifact.get("artifact_manifest", {}).get("checked") == EXPECTED_BATCH060F_ARTIFACT_MANIFEST_CHECKED, "Batch060f artifact manifest checked count mismatch")
    expect(errors, artifact.get("output_manifest", {}).get("checked") == EXPECTED_BATCH060F_OUTPUT_MANIFEST_CHECKED, "Batch060f output manifest checked count mismatch")
    expect(errors, artifact.get("artifact_manifest", {}).get("status") == "PASS", "Batch060f artifact manifest failed")
    expect(errors, artifact.get("output_manifest", {}).get("status") == "PASS", "Batch060f output manifest failed")
    for key in ["unsafe_path_count", "duplicate_path_count", "zip_pycache_entries", "zip_pyc_entries"]:
        expect(errors, artifact.get(key) == 0, f"Batch060f artifact has non-zero {key}")
    expect_false(errors, artifact, "raw_zip_bytes_ingested", "Batch060f artifact")
    expect_false(errors, artifact, "zip_payload_committed", "Batch060f artifact")
    expect(errors, ingest.get("status") == "PASS" and ingest.get("official_output_ingest", {}).get("status") == "PASS", "Batch060f official output ingest did not pass")
    expect(errors, preservation.get("batch060f_final_decision_status") == "PASS", "Batch060f result preservation missing PASS")
    expect(errors, preservation.get("issue_derived_repair_count") == 3, "issue-derived repair count not preserved from Batch060f")
    expect(errors, preservation.get("native_external_repair_count") == 4, "native external repair count not preserved from Batch060f")
    expect(errors, preservation.get("full_scoring") == "NOT_RUN/disallowed", "full scoring boundary changed from Batch060f")
    expect(errors, preservation.get("memory_lift") == "not_demonstrated", "memory lift boundary changed from Batch060f")
    expect(errors, preservation.get("self_maintaining_software") == "false/not_demonstrated", "self-maintaining boundary changed from Batch060f")
    expect(errors, branch.get("audioread_prerepair_reproduction") == "pre_repair_failure_reproduced_module_aifc_missing", "Audioread pre-repair reproduction not preserved")
    expect(errors, branch.get("audioread_exact_prior_patch_identity") == "PASS", "Audioread prior patch identity not preserved")
    expect(errors, branch.get("audioread_provider_backend_capsule_classification") == "provider_backend_capsule_unavailable", "Audioread provider classification mismatch")
    expect(errors, branch.get("audioread_replay_matrix_outcome") == "audioread_provider_backend_unavailable_declared", "Audioread replay outcome mismatch")
    expect(errors, branch.get("audioread_target_pass_after_exact_prior_patch_plus_provider_capsule") is False, "Audioread target pass unexpectedly true")
    expect(errors, lesson.get("repeated_patching_for_provider_boundary_forbidden") is True, "provider lesson did not forbid repeated patching")
    expect(errors, claim060f.get("current_protocol") == CURRENT_PROTOCOL, "Batch060f current protocol not preserved")
    expect(errors, next060f.get("status") == "PASS", "Batch060f next action boundary did not pass")

    expect(errors, terminal.get("terminal_or_parked_state") == "provider_backend_unavailable_declared", "Audioread terminal state mismatch")
    expect(errors, terminal.get("reprocess_now") is False, "Audioread was marked for reprocessing")
    expect(errors, terminal.get("selected_for_batch058c_replay") is False, "Audioread selected for Batch058c replay")
    expect(errors, len(reopen.get("reopen_conditions", [])) >= 5, "Audioread reopen conditions incomplete")
    expect(errors, do_not.get("do_not_reprocess_without_provider_change") is True, "Audioread do-not-reprocess rule missing")
    expect(errors, audioread_reopen.get("recommended") is False, "Audioread reopen was recommended immediately")

    required_patterns = {
        "optional_backend_unavailable",
        "declared_external_provider_missing",
        "provider_capsule_unavailable",
        "provider_install_not_allowed_by_workflow_policy",
        "audio_video_system_binary_backend_risk",
        "network_model_external_service_risk",
        "compiled_dependency_high_risk_boundary",
        "issue_body_fix_leakage_risk",
        "missing_candidate_sha",
        "missing_native_test_command",
        "high_artifact_growth_low_proof_distance_value",
    }
    observed_patterns = {item.get("pattern_id") for item in patterns.get("patterns", [])}
    expect(errors, required_patterns.issubset(observed_patterns), "negative seed pattern registry missing required patterns")
    expect(errors, provider_filter.get("status") == "PASS", "provider-risk filter update missing")
    expect(errors, strategy.get("status") == "PASS", "seed source strategy missing")
    expect(errors, manager.get("current_raw_leads_seen") == raw.get("lead_count"), "campaign manager raw lead count mismatch")
    expect(errors, manager.get("current_screened_leads_seen") == dedup.get("deduplicated_count"), "campaign manager screened lead count mismatch")

    expect(errors, raw.get("lead_count", 0) >= 40, "Batch058c did not screen expanded lead/salvage inventory")
    expect(errors, dedup.get("deduplicated_count", 0) >= 40, "Batch058c deduplicated lead count too low")
    expect(errors, selection.get("approved_count") == approved.get("approved_count"), "selection approved count mismatch")
    expect(errors, 2 <= approved.get("approved_count", 0) <= 5, "approved future replay count outside 2 to 5")
    approved_ids = {item.get("candidate_id") for item in approved.get("records", [])}
    expect(errors, "audioread_144_py313_aifc_removed" not in approved_ids, "Audioread approved for immediate future replay")
    expect(errors, {"pytest_13895_pytest9_skiptest_behavior", "freezegun_547_py313_datetimes_assertion"}.issubset(approved_ids), "expected future replay candidates missing")
    for item in approved.get("records", []):
        for key in [
            "candidate_id",
            "repo_url",
            "issue_url_or_reference",
            "candidate_sha",
            "native_test_path",
            "declared_test_command",
            "python_version_target",
            "provider_capsule_status",
            "expected_failure_family",
            "expected_provider_risk",
            "expected_proof_distance",
            "evidence_boundary_summary",
            "future_replay_command",
            "reason_for_approval",
        ]:
            expect(errors, bool(item.get(key)), f"approved candidate {item.get('candidate_id')} missing {key}")
    expect(errors, len(rejected.get("records", [])) > approved.get("approved_count", 0), "rejected/parked registry too small")
    expect(errors, leakage.get("issue_body_fix_text_used") is False, "issue body fix text used")
    for key in ["fixed_commit_used", "future_commit_used", "gold_patch_used", "pr_patch_used"]:
        expect_false(errors, fixed, key, "fixed/future/gold precheck")
    expect(errors, provider.get("provider_replay_run") is False, "provider replay ran in Batch058c")

    expect(errors, salvage.get("status") == "PASS", "salvage reassessment missing")
    salvage_ids = {item.get("candidate_id") for item in salvage.get("records", [])}
    for cid in [
        "datasette_2461_async_event_loop_cli_tests",
        "freezegun_547_py313_datetimes_assertion",
        "venusian_91_py313_frameinfo_callinfo",
        "pexpect_699_replwrap_bash_assertions",
        "pyramid_3761_py313_test_util",
        "pairtools_250_py313_pipes_removed",
        "pytest_13480_wdefault_unraisable_threadexception",
        "snapshottest_177_py312_imp_removed",
        "wave2_hermes_nousresearch_timeout_class",
        "genia_timeout_manual_review_class",
    ]:
        expect(errors, cid in salvage_ids, f"missing salvage reassessment for {cid}")
    expect(errors, salvage_queue.get("queue_count") == 1, "salvage reopen queue should contain one candidate")

    expect(errors, gap.get("self_maintaining_software_demonstrated") is False, "self-maintaining software was claimed")
    expect(errors, not gap.get("claim_ready_functions"), "claim-ready functions were asserted")
    expect(errors, health.get("project_health_grade") == "B", "project health grade mismatch")
    expect(errors, health.get("traffic_light_status") == "yellow", "traffic-light status mismatch")
    expect(errors, tld.get("internal_metadata_only") is True and tld.get("not_repair_evidence") is True, "TLD boundary invalid")
    expect(errors, reactome.get("provider_capsule_step_gating_only") is True and reactome.get("not_repair_evidence") is True, "Reactome boundary invalid")
    expect(errors, translation.get("internal_labels_do_not_change_proof_rules") is True, "internal labels changed proof rules")
    expect(errors, public_language.get("status") == "PASS", "public language neutrality check failed")
    expect(errors, public_claim.get("status") == "PASS", "public summary claim safety check failed")

    expect(errors, final.get("status") == "PASS", "Batch058c final status not PASS")
    expect(errors, final.get("batch060f_ingest_status") == "PASS", "Batch060f ingest not PASS in final")
    expect(errors, final.get("current_protocol") == CURRENT_PROTOCOL, "current protocol changed")
    expect(errors, final.get("issue_derived_repair_count") == 3, "issue-derived repair count changed")
    expect(errors, final.get("native_external_repair_count") == 4, "native external repair count changed")
    expect(errors, final.get("audioread_terminal_state_status") == "provider_backend_unavailable_declared", "final Audioread terminal state mismatch")
    expect(errors, final.get("approved_future_replay_candidates") == approved.get("approved_count"), "final approved count mismatch")
    expect(errors, final.get("next_allowed_action") == EXPECTED_NEXT_ACTION, "Batch058c next allowed action mismatch")
    expect(errors, batch063.get("recommended") is True and batch063.get("next_allowed_action") == EXPECTED_NEXT_ACTION, "Batch063 recommendation invalid")
    for key in ["patch_generated", "patch_applied", "pre_repair_replay_run", "duplicate_replay_run", "count_gate_run", "repair_count_increment"]:
        expect_false(errors, final, key, "Batch058c final decision")
        expect_false(errors, claim, key, "Batch058c claim boundary")
    expect(errors, final.get("full_scoring") == "NOT_RUN/disallowed", "full scoring changed")
    expect(errors, final.get("memory_lift") == "not_demonstrated", "memory lift changed")
    expect(errors, final.get("self_maintaining_software") == "false/not_demonstrated", "self-maintaining claim changed")
    expect_false(errors, claim, "repo_refactor_performed", "claim boundary")
    expect_false(errors, claim, "workflow_deleted", "claim boundary")
    expect_false(errors, claim, "source_behavior_changed", "claim boundary")
    expect_false(errors, claim, "audioread_selected_for_replay", "claim boundary")
    expect(errors, package.get("status") == "PASS", "package verification did not pass")
    for key in ["raw_zip_payload_committed", "runtime_workspaces_committed", "source_checkouts_committed", "venvs_committed", "caches_committed"]:
        expect_false(errors, package, key, "package verification")

    audit_public_summary(errors)
    audit_git_status(errors)

    if errors:
        print("FAIL:")
        for error in errors:
            print(f"- {error}")
        return 1
    print("Batch058c seed discovery expansion / salvage reassessment audit PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
