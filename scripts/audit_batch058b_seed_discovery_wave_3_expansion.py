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


OUT_DIR = ROOT / "outputs" / "post_v2_37_hardening_batch058b_seed_discovery_wave_3_expansion"
CURRENT_PROTOCOL = "v2.14"
EXPECTED_BATCH062_SHA = "fd740abec40cd0e5ee80cd0a153b883d51b4d07093b9ab59037067d5b809ca5d"
EXPECTED_BATCH062_SIZE = 50832
EXPECTED_BATCH062_ENTRY_COUNT = 72

REQUIRED_OUTPUTS = [
    "batch062_artifact_ingestion_summary.json",
    "batch062_artifact_sha256_verification.json",
    "batch062_result_preservation.json",
    "batch062_candidate_selection_preservation.json",
    "batch062_salvage_review_preservation.json",
    "batch062_self_maintenance_gap_preservation.json",
    "batch062_claim_boundary_preservation.json",
    "batch062_next_action_boundary.json",
    "wave3_expansion_scope.json",
    "wave3_seed_source_manifest.json",
    "wave3_seed_search_plan.json",
    "wave3_candidate_category_policy.json",
    "wave3_disfavored_candidate_policy.json",
    "provider_screened_seed_intake_hardening.json",
    "candidate_deduplication_hardening.json",
    "provider_runtime_prescreen_hardening.json",
    "candidate_terminal_state_hardening.json",
    "seed_expected_value_scoring_hardening.json",
    "permanent_intake_fix_summary.json",
    "wave3_raw_lead_registry.json",
    "wave3_normalized_lead_registry.json",
    "wave3_deduplicated_lead_registry.json",
    "wave3_duplicate_rejection_registry.json",
    "wave3_counted_repair_overlap_check.json",
    "wave3_parked_candidate_overlap_check.json",
    "wave3_retired_candidate_overlap_check.json",
    "wave3_issue_body_leakage_precheck.json",
    "wave3_fixed_future_gold_precheck.json",
    "wave3_provider_runtime_prescreen_results.json",
    "wave3_provider_capsule_readiness_registry.json",
    "wave3_declared_dependency_map.json",
    "wave3_declared_runtime_map.json",
    "wave3_declared_test_command_map.json",
    "wave3_provider_risk_registry.json",
    "wave3_provider_rejection_registry.json",
    "wave3_amds_precondition_board.json",
    "wave3_failure_family_prior_map.json",
    "wave3_bug_tree_prior_registry.json",
    "wave3_source_contact_prior_map.json",
    "wave3_provider_dependency_prior_map.json",
    "wave3_interpreter_behavior_prior_map.json",
    "wave3_replay_license_precondition.json",
    "wave3_candidate_expected_value_scores.json",
    "wave3_candidate_proof_distance_scores.json",
    "wave3_candidate_provider_risk_scores.json",
    "wave3_candidate_self_maintenance_value_scores.json",
    "wave3_candidate_selection_matrix.json",
    "wave3_approved_for_future_replay_registry.json",
    "wave3_rejected_or_parked_registry.json",
    "wave3_manual_review_registry.json",
    "seed_intake_recurring_issue_update.json",
    "provider_capsule_reuse_registry_update.json",
    "candidate_discovery_friction_update.json",
    "manual_intervention_reduction_update.json",
    "shared_utility_candidate_update.json",
    "future_repo_hygiene_queue_update.json",
    "wave1_wave2_salvage_preservation_in_batch058b.json",
    "parked_candidate_preservation_in_batch058b.json",
    "audioread_branch_preservation_in_batch058b.json",
    "freezegun_branch_preservation_in_batch058b.json",
    "datasette_branch_preservation_in_batch058b.json",
    "project_health_review_batch058b.json",
    "capability_maturity_scorecard_batch058b.json",
    "version_progress_grade_batch058b.json",
    "strategic_direction_check_batch058b.json",
    "proof_milestone_distance_report_batch058b.json",
    "regression_and_drift_watch_batch058b.json",
    "recurring_bottleneck_trend_report_batch058b.json",
    "self_maintenance_readiness_review_batch058b.json",
    "next_highest_impact_action_report_batch058b.json",
    "tld_governance_boundary_batch058b.json",
    "reactome_provider_capsule_boundary_batch058b.json",
    "internal_theory_to_engineering_translation_batch058b.json",
    "public_language_neutrality_check_batch058b.json",
    "public_summary_claim_safety_check_batch058b.json",
    "batch058b_final_decision.json",
    "batch059b_or_batch063_pre_repair_replay_recommendation.json",
    "batch060f_audioread_provider_backend_capsule_replay_recommendation.json",
    "batch062c_wave1_wave2_salvage_replay_selection_recommendation.json",
    "batch062b_repo_hygiene_utility_consolidation_planning_recommendation.json",
    "batch058b_summary.md",
    "claim_boundary.json",
    "audit.json",
    "package_verification.json",
    "artifact_sha256_verification.json",
    "SHA256SUMS.txt",
]

REQUIRED_ROOT_FILES = [
    "configs/provider_screened_seed_intake_policy.json",
    "configs/candidate_deduplication_policy.json",
    "configs/provider_runtime_prescreen_policy.json",
    "configs/wave_candidate_terminal_state_policy.json",
    "configs/seed_expected_value_scoring_policy.json",
    "docs/controllergate_provider_screened_seed_intake.md",
    "docs/controllergate_candidate_terminal_state_policy.md",
    ".github/workflows/post_v2_37_hardening_batch058b_seed_discovery_wave_3_expansion.yml",
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

FORBIDDEN_PUBLIC_TERMS = [
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


def public_batch058b_block(path: Path) -> str:
    text = path.read_text(encoding="utf-8")
    start = text.find("Batch058b is the latest seed-discovery boundary.")
    end = text.find("Batch062 is the latest strategic selection boundary.", start)
    if start == -1:
        return ""
    return text[start:end if end != -1 else len(text)]


def audit_public_summary(errors: list[str]) -> None:
    required = [
        "Batch058b",
        "Issue-derived repair count preserved at `3`.",
        "Native external repair count preserved at `4`.",
        "Workflow success is not equivalent to repair success.",
        "Seed discovery is not repair success.",
        "Provider/runtime pre-screening is not repair success.",
        "Repair count increments require duplicate clean replay and count gate.",
        "The project health grade is advisory and does not constitute proof.",
        "Self-maintaining software remains false/not_demonstrated.",
    ]
    for rel in [
        "README.md",
        "docs/current_status.md",
        "controllergate_v1_7_beta/reports/critic_review_package/shareable_summary.md",
    ]:
        block = public_batch058b_block(ROOT / rel)
        expect(errors, bool(block), f"missing Batch058b public summary block in {rel}")
        for phrase in required:
            expect(errors, phrase in block, f"Batch058b public summary missing {phrase!r} in {rel}")
        lowered = block.lower()
        for term in FORBIDDEN_PUBLIC_TERMS:
            expect(errors, term.lower() not in lowered, f"Batch058b public summary contains internal term {term!r} in {rel}")


def main() -> int:
    errors: list[str] = []
    if not OUT_DIR.is_dir():
        print(f"FAIL: missing output directory {OUT_DIR.relative_to(ROOT)}")
        return 1
    for rel in REQUIRED_OUTPUTS:
        if not (OUT_DIR / rel).is_file():
            errors.append(f"missing required Batch058b output: {rel}")
    for rel in REQUIRED_ROOT_FILES:
        if not (ROOT / rel).is_file():
            errors.append(f"missing required Batch058b root file: {rel}")
    if not errors:
        manifest = verify_manifest(OUT_DIR)
        if manifest.get("status") != "PASS":
            errors.append(f"Batch058b SHA256SUMS verification failed: {manifest}")
    if errors:
        print("FAIL:")
        for error in errors:
            print(f"- {error}")
        return 1

    artifact = read_json(OUT_DIR / "batch062_artifact_sha256_verification.json")
    ingest = read_json(OUT_DIR / "batch062_artifact_ingestion_summary.json")
    preservation = read_json(OUT_DIR / "batch062_result_preservation.json")
    candidate_preservation = read_json(OUT_DIR / "batch062_candidate_selection_preservation.json")
    salvage = read_json(OUT_DIR / "batch062_salvage_review_preservation.json")
    self_gap = read_json(OUT_DIR / "batch062_self_maintenance_gap_preservation.json")
    claim062 = read_json(OUT_DIR / "batch062_claim_boundary_preservation.json")
    next062 = read_json(OUT_DIR / "batch062_next_action_boundary.json")
    scope = read_json(OUT_DIR / "wave3_expansion_scope.json")
    source_manifest = read_json(OUT_DIR / "wave3_seed_source_manifest.json")
    hardening = read_json(OUT_DIR / "permanent_intake_fix_summary.json")
    normalized = read_json(OUT_DIR / "wave3_normalized_lead_registry.json")
    dedup = read_json(OUT_DIR / "wave3_deduplicated_lead_registry.json")
    duplicates = read_json(OUT_DIR / "wave3_duplicate_rejection_registry.json")
    counted = read_json(OUT_DIR / "wave3_counted_repair_overlap_check.json")
    parked = read_json(OUT_DIR / "wave3_parked_candidate_overlap_check.json")
    retired = read_json(OUT_DIR / "wave3_retired_candidate_overlap_check.json")
    leakage = read_json(OUT_DIR / "wave3_issue_body_leakage_precheck.json")
    forbidden = read_json(OUT_DIR / "wave3_fixed_future_gold_precheck.json")
    provider = read_json(OUT_DIR / "wave3_provider_runtime_prescreen_results.json")
    amds = read_json(OUT_DIR / "wave3_amds_precondition_board.json")
    selection = read_json(OUT_DIR / "wave3_candidate_selection_matrix.json")
    approved = read_json(OUT_DIR / "wave3_approved_for_future_replay_registry.json")
    manual_review = read_json(OUT_DIR / "wave3_manual_review_registry.json")
    preservation_salvage = read_json(OUT_DIR / "wave1_wave2_salvage_preservation_in_batch058b.json")
    audioread = read_json(OUT_DIR / "audioread_branch_preservation_in_batch058b.json")
    tld = read_json(OUT_DIR / "tld_governance_boundary_batch058b.json")
    reactome = read_json(OUT_DIR / "reactome_provider_capsule_boundary_batch058b.json")
    language = read_json(OUT_DIR / "public_language_neutrality_check_batch058b.json")
    final = read_json(OUT_DIR / "batch058b_final_decision.json")
    claim = read_json(OUT_DIR / "claim_boundary.json")
    package = read_json(OUT_DIR / "package_verification.json")

    expect(errors, artifact.get("status") == "PASS", "Batch062 artifact verification did not pass")
    expect(errors, artifact.get("zip_sha256") == EXPECTED_BATCH062_SHA, "Batch062 artifact SHA mismatch")
    expect(errors, artifact.get("zip_size_bytes") == EXPECTED_BATCH062_SIZE, "Batch062 artifact size mismatch")
    expect(errors, artifact.get("zip_entry_count") == EXPECTED_BATCH062_ENTRY_COUNT, "Batch062 artifact entry count mismatch")
    expect(errors, artifact.get("artifact_manifest", {}).get("checked") == 71, "Batch062 artifact manifest checked count mismatch")
    expect(errors, artifact.get("output_manifest", {}).get("checked") == 70, "Batch062 output manifest checked count mismatch")
    expect(errors, artifact.get("artifact_manifest", {}).get("status") == "PASS", "Batch062 artifact manifest failed")
    expect(errors, artifact.get("output_manifest", {}).get("status") == "PASS", "Batch062 output manifest failed")
    for key in ["unsafe_path_count", "duplicate_path_count", "zip_pycache_entries", "zip_pyc_entries"]:
        expect(errors, artifact.get(key) == 0, f"Batch062 artifact has non-zero {key}")
    expect(errors, ingest.get("status") == "PASS" and ingest.get("official_output_ingest", {}).get("status") == "PASS", "Batch062 official ingest failed")

    expect(errors, preservation.get("batch062_final_decision_status") == "PASS", "Batch062 final decision not preserved")
    expect(errors, preservation.get("issue_derived_repair_count") == 3, "Issue-derived repair count changed")
    expect(errors, preservation.get("native_external_repair_count") == 4, "Native external repair count changed")
    expect(errors, preservation.get("full_scoring") == "NOT_RUN/disallowed", "Full scoring changed")
    expect(errors, preservation.get("memory_lift") == "not_demonstrated", "Memory lift changed")
    expect(errors, preservation.get("self_maintaining_software") == "false/not_demonstrated", "Self-maintaining status changed")
    expect(errors, candidate_preservation.get("batch062_selected_batch058b") is True, "Batch062 selection not preserved")
    expect(errors, salvage.get("highest_ranked_parked_candidate") == "audioread_144_py313_aifc_removed", "Audioread parked preservation missing")
    expect(errors, salvage.get("wave1_wave2_salvage_review_count") == 10, "Wave 1/Wave 2 salvage count mismatch")
    expect(errors, self_gap.get("self_maintaining_software_demonstrated") is False, "Self-maintenance gap overclaimed")
    expect(errors, claim062.get("current_protocol") == CURRENT_PROTOCOL, "Batch062 current protocol changed")
    expect(errors, next062.get("observed_next_allowed_action") == "batch058b_seed_discovery_wave_3_expansion", "Batch062 next action boundary mismatch")

    expect(errors, scope.get("may_generate_patches") is False, "Batch058b scope permits patch generation")
    expect(errors, scope.get("may_run_pre_repair_replay") is False, "Batch058b scope permits pre-repair replay")
    expect(errors, source_manifest.get("external_search_performed") is False, "Batch058b used external broad search")
    expect(errors, hardening.get("repo_refactor_performed") is False, "Batch058b performed repo refactor")
    expect(errors, normalized.get("lead_count") == final.get("leads_screened"), "Normalized lead count does not match final")
    expect(errors, dedup.get("deduplicated_count") == final.get("deduplicated_leads"), "Deduplicated count mismatch")
    expect(errors, duplicates.get("duplicate_count") >= 1, "Duplicate rejection registry missing counted/parked duplicates")
    expect(errors, any(item.get("duplicate_status") == "counted_duplicate" for item in counted.get("overlaps", [])), "Counted duplicate overlap missing")
    expect(errors, any(item.get("duplicate_status") == "parked_duplicate" for item in parked.get("overlaps", [])), "Parked duplicate overlap missing")
    expect(errors, retired.get("status") == "PASS", "Retired overlap check missing")
    expect(errors, leakage.get("issue_body_fix_text_excluded_for_all_records") is True, "Issue-body leakage check failed")
    expect(errors, forbidden.get("fixed_commit_used") is False and forbidden.get("future_commit_used") is False and forbidden.get("gold_patch_used") is False, "Forbidden evidence precheck failed")
    expect(errors, provider.get("provider_replay_run") is False, "Provider prescreen ran replay")
    expect(errors, amds.get("replay_run") is False, "AMDS precondition map ran replay")
    expect(errors, selection.get("approved_count") == final.get("approved_future_replay_candidate_count"), "Selection approved count mismatch")
    expect(errors, approved.get("approved_count") == final.get("approved_future_replay_candidate_count"), "Approved registry count mismatch")
    expect(errors, approved.get("approved_count") <= 5, "More than five candidates approved without justification")
    if approved.get("approved_count") == 0:
        expect(errors, final.get("next_allowed_action") == "batch060f_audioread_provider_backend_capsule_replay", "Zero approved candidates must route to Audioread fallback")
    if 2 <= approved.get("approved_count") <= 5:
        expect(errors, final.get("next_allowed_action") == "batch063_wave3_expansion_pre_repair_replay_limited", "2-5 approved candidates must route to Batch063")
    expect(errors, manual_review.get("status") == "PASS", "Manual-review registry missing")
    expect(errors, preservation_salvage.get("salvage_reopened") is False, "Salvage reopened during Batch058b")
    expect(errors, audioread.get("replayed") is False, "Audioread replayed during Batch058b")
    expect(errors, tld.get("not_repair_evidence") is True, "TLD boundary treats internal metadata as repair evidence")
    expect(errors, reactome.get("not_repair_evidence") is True, "Reactome boundary treats pattern as repair evidence")
    expect(errors, language.get("status") == "PASS", "Public language neutrality check failed")

    expect(errors, final.get("status") == "PASS", "Batch058b final status is not PASS")
    expect(errors, final.get("current_protocol") == CURRENT_PROTOCOL, "Current protocol changed")
    expect(errors, final.get("issue_derived_repair_count") == 3, "Final issue-derived count changed")
    expect(errors, final.get("native_external_repair_count") == 4, "Final native count changed")
    expect(errors, final.get("full_scoring") == "NOT_RUN/disallowed", "Final full scoring changed")
    expect(errors, final.get("memory_lift") == "not_demonstrated", "Final memory lift changed")
    expect(errors, final.get("self_maintaining_software") == "false/not_demonstrated", "Final self-maintaining changed")
    for key in ["patch_generated", "patch_applied", "pre_repair_replay_run", "post_repair_replay_run", "duplicate_replay_run", "count_gate_run", "repair_count_increment"]:
        expect_false(errors, final, key, "Batch058b final decision")
        expect_false(errors, claim, key, "Batch058b claim boundary")
    expect_false(errors, claim, "repo_refactor_performed", "Batch058b claim boundary")
    expect_false(errors, claim, "workflow_deleted", "Batch058b claim boundary")
    expect_false(errors, claim, "source_behavior_changed", "Batch058b claim boundary")
    expect_false(errors, claim, "tests_mutated", "Batch058b claim boundary")
    for key in ["raw_zip_payload_committed", "runtime_workspaces_committed", "source_checkouts_committed", "venvs_committed", "caches_committed"]:
        expect_false(errors, package, key, "Batch058b package verification")

    current_cfg = (ROOT / "configs" / "controllergate_current.yaml").read_text(encoding="utf-8")
    expect(errors, "protocol_version: v2.14" in current_cfg, "Current protocol is not v2.14")
    audit_public_summary(errors)
    audit_git_status(errors)

    if errors:
        print("FAIL:")
        for error in errors:
            print(f"- {error}")
        return 1
    print("Batch058b seed discovery wave 3 expansion audit PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
