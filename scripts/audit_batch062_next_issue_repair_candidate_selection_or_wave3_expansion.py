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


OUT_DIR = ROOT / "outputs" / "post_v2_37_hardening_batch062_next_issue_repair_candidate_selection_or_wave3_expansion"
CURRENT_PROTOCOL = "v2.14"
BATCH061_SHA = "badd42e12343fd56d9797a1779f785a946993693fbb592a9dd4775f087083bc3"
BATCH061_SIZE = 40738
BATCH061_ENTRY_COUNT = 81
BATCH061_ARTIFACT_MANIFEST_CHECKED = 80
BATCH061_OUTPUT_MANIFEST_CHECKED = 79
EXPECTED_NEXT_ACTION = "batch058b_seed_discovery_wave_3_expansion"

REQUIRED_FILES = [
    "batch061_artifact_ingestion_summary.json",
    "batch061_artifact_sha256_verification.json",
    "batch061_result_preservation.json",
    "batch061_cloudpickle_counted_repair_preservation.json",
    "batch061_proof_ledger_preservation.json",
    "batch061_project_health_preservation.json",
    "batch061_claim_boundary_preservation.json",
    "batch061_next_action_boundary.json",
    "candidate_pool_inventory_after_batch061.json",
    "counted_repair_registry_after_batch061.json",
    "parked_candidate_registry_after_batch061.json",
    "retired_candidate_registry_after_batch061.json",
    "future_seed_pool_registry_after_batch061.json",
    "candidate_status_consistency_check.json",
    "highest_impact_path_analysis.json",
    "next_candidate_selection_matrix.json",
    "candidate_expected_value_ranking.json",
    "candidate_risk_ranking.json",
    "candidate_provider_complexity_ranking.json",
    "candidate_proof_distance_ranking.json",
    "self_maintenance_runtime_progress_review_batch062.json",
    "self_maintenance_gap_closure_plan.json",
    "autonomic_capability_readiness_matrix.json",
    "manual_intervention_reduction_report.json",
    "repeat_bottleneck_elimination_plan.json",
    "project_health_review_batch062.json",
    "capability_maturity_scorecard_batch062.json",
    "version_progress_grade_batch062.json",
    "strategic_direction_check_batch062.json",
    "proof_milestone_distance_report_batch062.json",
    "regression_and_drift_watch_batch062.json",
    "recurring_bottleneck_trend_report_batch062.json",
    "next_highest_impact_action_report_batch062.json",
    "cloudpickle_count_gate_pattern_update.json",
    "provider_screened_seed_success_pattern.json",
    "duplicate_replay_count_gate_success_pattern.json",
    "issue_derived_repair_increment_pattern.json",
    "public_language_guard_pattern_update.json",
    "amds_full_bug_tree_pattern_update.json",
    "reactome_provider_capsule_pattern_update.json",
    "tld_governance_pattern_update.json",
    "batch062_final_decision.json",
    "batch063_recommended_prompt_plan.json",
    "batch060f_audioread_provider_backend_capsule_replay_recommendation.json",
    "batch058b_seed_discovery_wave_3_expansion_recommendation.json",
    "batch062b_repo_hygiene_utility_consolidation_planning_recommendation.json",
    "batch057d_freezegun_provider_portability_recommendation.json",
    "wave1_wave2_salvage_inventory.json",
    "wave1_wave2_original_blocker_registry.json",
    "wave1_wave2_new_capability_reassessment.json",
    "wave1_wave2_reopen_candidate_queue.json",
    "wave1_wave2_retirement_confirmation.json",
    "wave1_wave2_manual_review_queue.json",
    "universal_bug_processing_policy.json",
    "self_maintaining_bug_terminal_state_policy.json",
    "bug_unrecoverability_explanation_policy.json",
    "autonomous_bug_route_contract.json",
    "self_maintaining_wrapper_function_gap_audit.json",
    "self_maintaining_wrapper_required_function_matrix.json",
    "missing_or_partial_self_maintenance_functions.json",
    "self_maintenance_function_roadmap.json",
    "salvage_vs_new_seed_tradeoff_analysis.json",
    "wave1_wave2_salvage_expected_value_ranking.json",
    "wave1_wave2_salvage_risk_ranking.json",
    "best_parked_candidate_reopen_recommendation.json",
    "batch062_summary.md",
    "claim_boundary.json",
    "audit.json",
    "package_verification.json",
    "artifact_sha256_verification.json",
    "SHA256SUMS.txt",
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


def public_batch062_block(path: Path) -> str:
    text = path.read_text(encoding="utf-8")
    start = text.find("Batch062 is the latest strategic selection boundary.")
    end = text.find("Batch061 is the latest validation-path boundary.")
    if start == -1:
        return ""
    return text[start:end if end != -1 else len(text)]


def audit_public_summary(errors: list[str]) -> None:
    required = [
        "Batch062",
        "Wave 1/Wave 2 salvage review",
        "A self-maintaining wrapper should process every encountered bug into an auditable route or terminal state, but it should not claim it can fix every bug.",
        "Some bugs may be unrecoverable under current policy because they require forbidden evidence, unbounded providers, unavailable runtimes, or test mutation.",
        "Workflow success is not equivalent to repair success.",
        "Provider/runtime recovery is not repair success.",
        "Partial improvement is not repair success.",
        "Repair count increments require duplicate clean replay and count gate.",
        "Self-maintaining software remains false/not_demonstrated.",
    ]
    forbidden_in_new_block = ["TLD", "TORUS", "chromosomal", "biological", "ToT-BULB", "metrological immune system"]
    for rel in [
        "README.md",
        "docs/current_status.md",
        "controllergate_v1_7_beta/reports/critic_review_package/shareable_summary.md",
    ]:
        block = public_batch062_block(ROOT / rel)
        expect(errors, bool(block), f"missing Batch062 public summary block in {rel}")
        for phrase in required:
            expect(errors, phrase in block, f"Batch062 public summary missing {phrase!r} in {rel}")
        for term in forbidden_in_new_block:
            expect(errors, term.lower() not in block.lower(), f"Batch062 public summary contains internal term {term!r} in {rel}")


def main() -> int:
    errors: list[str] = []
    if not OUT_DIR.is_dir():
        print(f"FAIL: missing output directory {OUT_DIR.relative_to(ROOT)}")
        return 1
    for rel in REQUIRED_FILES:
        if not (OUT_DIR / rel).is_file():
            errors.append(f"missing required Batch062 output: {rel}")
    if not errors:
        manifest = verify_manifest(OUT_DIR)
        if manifest.get("status") != "PASS":
            errors.append(f"Batch062 SHA256SUMS verification failed: {manifest}")
    if errors:
        print("FAIL:")
        for error in errors:
            print(f"- {error}")
        return 1

    artifact = read_json(OUT_DIR / "batch061_artifact_sha256_verification.json")
    ingest = read_json(OUT_DIR / "batch061_artifact_ingestion_summary.json")
    preserved = read_json(OUT_DIR / "batch061_result_preservation.json")
    counted = read_json(OUT_DIR / "batch061_cloudpickle_counted_repair_preservation.json")
    ledger = read_json(OUT_DIR / "batch061_proof_ledger_preservation.json")
    claim061 = read_json(OUT_DIR / "batch061_claim_boundary_preservation.json")
    next061 = read_json(OUT_DIR / "batch061_next_action_boundary.json")
    pool = read_json(OUT_DIR / "candidate_pool_inventory_after_batch061.json")
    counted_registry = read_json(OUT_DIR / "counted_repair_registry_after_batch061.json")
    parked = read_json(OUT_DIR / "parked_candidate_registry_after_batch061.json")
    retired = read_json(OUT_DIR / "retired_candidate_registry_after_batch061.json")
    future = read_json(OUT_DIR / "future_seed_pool_registry_after_batch061.json")
    consistency = read_json(OUT_DIR / "candidate_status_consistency_check.json")
    path_analysis = read_json(OUT_DIR / "highest_impact_path_analysis.json")
    selection = read_json(OUT_DIR / "next_candidate_selection_matrix.json")
    salvage = read_json(OUT_DIR / "wave1_wave2_salvage_inventory.json")
    reassessment = read_json(OUT_DIR / "wave1_wave2_new_capability_reassessment.json")
    reopen = read_json(OUT_DIR / "wave1_wave2_reopen_candidate_queue.json")
    terminal = read_json(OUT_DIR / "universal_bug_processing_policy.json")
    terminal_policy = read_json(OUT_DIR / "self_maintaining_bug_terminal_state_policy.json")
    unrecoverable = read_json(OUT_DIR / "bug_unrecoverability_explanation_policy.json")
    wrapper_gap = read_json(OUT_DIR / "self_maintaining_wrapper_function_gap_audit.json")
    function_matrix = read_json(OUT_DIR / "self_maintaining_wrapper_required_function_matrix.json")
    missing = read_json(OUT_DIR / "missing_or_partial_self_maintenance_functions.json")
    tradeoff = read_json(OUT_DIR / "salvage_vs_new_seed_tradeoff_analysis.json")
    best_parked = read_json(OUT_DIR / "best_parked_candidate_reopen_recommendation.json")
    health = read_json(OUT_DIR / "project_health_review_batch062.json")
    scorecard = read_json(OUT_DIR / "capability_maturity_scorecard_batch062.json")
    proof_distance = read_json(OUT_DIR / "proof_milestone_distance_report_batch062.json")
    next_report = read_json(OUT_DIR / "next_highest_impact_action_report_batch062.json")
    public_guard = read_json(OUT_DIR / "public_language_guard_pattern_update.json")
    amds = read_json(OUT_DIR / "amds_full_bug_tree_pattern_update.json")
    reactome = read_json(OUT_DIR / "reactome_provider_capsule_pattern_update.json")
    tld = read_json(OUT_DIR / "tld_governance_pattern_update.json")
    final = read_json(OUT_DIR / "batch062_final_decision.json")
    claim = read_json(OUT_DIR / "claim_boundary.json")
    package = read_json(OUT_DIR / "package_verification.json")

    expect(errors, artifact.get("status") == "PASS", "Batch061 artifact verification did not pass")
    expect(errors, artifact.get("zip_sha256") == BATCH061_SHA, "Batch061 artifact SHA mismatch")
    expect(errors, artifact.get("zip_size_bytes") == BATCH061_SIZE, "Batch061 artifact size mismatch")
    expect(errors, artifact.get("zip_entry_count") == BATCH061_ENTRY_COUNT, "Batch061 artifact entry count mismatch")
    expect(errors, artifact.get("artifact_manifest", {}).get("checked") == BATCH061_ARTIFACT_MANIFEST_CHECKED, "Batch061 artifact manifest checked count mismatch")
    expect(errors, artifact.get("output_manifest", {}).get("checked") == BATCH061_OUTPUT_MANIFEST_CHECKED, "Batch061 output manifest checked count mismatch")
    expect(errors, artifact.get("artifact_manifest", {}).get("status") == "PASS", "Batch061 artifact manifest failed")
    expect(errors, artifact.get("output_manifest", {}).get("status") == "PASS", "Batch061 output manifest failed")
    for key in ["unsafe_path_count", "duplicate_path_count", "zip_pycache_entries", "zip_pyc_entries"]:
        expect(errors, artifact.get(key) == 0, f"Batch061 artifact has non-zero {key}")
    expect(errors, ingest.get("status") == "PASS" and ingest.get("official_output_ingest", {}).get("status") == "PASS", "Batch061 official ingest failed")

    expect(errors, preserved.get("batch061_final_decision_status") == "PASS", "Batch061 final decision not preserved as PASS")
    expect(errors, preserved.get("issue_derived_repair_count_before_batch061") == 2, "Batch061 before count mismatch")
    expect(errors, preserved.get("issue_derived_repair_count_after_batch061") == 3, "Batch061 after count mismatch")
    expect(errors, preserved.get("native_external_repair_count") == 4, "Native external count changed")
    expect(errors, preserved.get("full_scoring") == "NOT_RUN/disallowed", "Full scoring status changed")
    expect(errors, preserved.get("memory_lift") == "not_demonstrated", "Memory lift status changed")
    expect(errors, preserved.get("self_maintaining_software") == "false/not_demonstrated", "Self-maintaining status changed")
    expect(errors, preserved.get("duplicate_replay_outcome") == "duplicate_clean_replay_pass", "Duplicate replay outcome not preserved")
    expect(errors, preserved.get("count_gate_status") == "PASS", "Count gate status not preserved")
    expect(errors, preserved.get("provider_runtime_recovery_counted_as_repair") is False, "Provider/runtime recovery counted as repair")
    expect(errors, counted.get("counted_as_issue_derived") is True, "Cloudpickle counted issue-derived record not preserved")
    expect(errors, counted.get("counted_as_native_external") is False, "Cloudpickle polluted native count")
    expect(errors, ledger.get("status") == "PASS" and ledger.get("transition") == "issue_derived_repair_count_increment", "Proof ledger preservation invalid")
    expect(errors, claim061.get("full_scoring") == "NOT_RUN/disallowed", "Batch061 claim full scoring changed")
    expect(errors, claim061.get("memory_lift") == "not_demonstrated", "Batch061 claim memory lift changed")
    expect(errors, claim061.get("self_maintaining_software") == "false/not_demonstrated", "Batch061 claim self-maintaining changed")
    expect(errors, next061.get("observed_next_allowed_action") == "batch062_next_issue_repair_candidate_selection_or_wave3_expansion", "Batch061 next action boundary mismatch")

    expect(errors, pool.get("status") == "PASS" and pool.get("wave1_wave2_salvage_review_count") >= 10, "Candidate pool/salvage inventory incomplete")
    expect(errors, counted_registry.get("issue_derived_repair_count") == 3, "Counted registry issue count mismatch")
    expect(errors, parked.get("status") == "PASS" and len(parked.get("records", [])) >= 4, "Parked registry incomplete")
    expect(errors, retired.get("status") == "PASS" and len(retired.get("records", [])) >= 6, "Retired registry incomplete")
    expect(errors, future.get("status") == "PASS", "Future seed pool registry missing")
    expect(errors, consistency.get("repair_counts_preserved_in_batch062") is True, "Candidate consistency does not preserve counts")
    expect(errors, path_analysis.get("selected_path") == EXPECTED_NEXT_ACTION, "Highest-impact selected path mismatch")
    expect(errors, selection.get("selected_path") == EXPECTED_NEXT_ACTION, "Selection matrix selected path mismatch")
    expect(errors, any(item.get("candidate_id") == "freezegun_547_py313_datetimes_assertion" for item in salvage.get("records", [])), "Freezegun salvage record missing")
    expect(errors, any(item.get("candidate_id") == "pairtools_250_py313_pipes_removed" for item in salvage.get("records", [])), "Pairtools salvage record missing")
    expect(errors, reassessment.get("status") == "PASS", "Wave1/Wave2 reassessment missing")
    expect(errors, reopen.get("batch062_reopens_now") is False, "Batch062 reopened candidates despite strategic-only scope")
    expect(errors, terminal.get("fix_every_bug_claimed") is False, "Universal bug policy claims every bug can be fixed")
    expect(errors, terminal.get("must_route_to_terminal_or_next_action", True) is True or "terminal_states" in terminal, "Universal routing principle missing")
    expect(errors, len(terminal_policy.get("terminal_state_records", [])) >= 15, "Terminal-state policy incomplete")
    expect(errors, "unbounded provider" in unrecoverable.get("public_language", ""), "Unrecoverability explanation missing provider wording")
    expect(errors, wrapper_gap.get("self_maintaining_software_demonstrated") is False, "Wrapper gap audit overclaims self-maintenance")
    expect(errors, len(function_matrix.get("functions", [])) == 30, "Wrapper function matrix must cover 30 functions")
    expect(errors, len(missing.get("top_three", [])) == 3, "Missing/partial top-three function summary missing")
    expect(errors, tradeoff.get("new_seed_expansion_selected") is True, "Tradeoff analysis did not select new seed expansion")
    expect(errors, best_parked.get("highest_ranked_parked_candidate") == "audioread_144_py313_aifc_removed", "Best parked candidate mismatch")

    expect(errors, health.get("advisory_diagnostic_only") is True and health.get("does_not_override_audits") is True, "Health review is not advisory")
    expect(errors, scorecard.get("self_maintenance_readiness") == "not_demonstrated", "Scorecard overclaims self-maintenance")
    expect(errors, proof_distance.get("distance_to_self_maintaining_claim") == "far", "Self-maintaining distance mismatch")
    expect(errors, next_report.get("recommended_next_action") == EXPECTED_NEXT_ACTION, "Next highest-impact report mismatch")
    expect(errors, public_guard.get("operational_rules_unchanged") is True, "Public language pattern changes operational rules")
    expect(errors, amds.get("claim_boundary_preserved") is True, "AMDS pattern boundary not preserved")
    expect(errors, reactome.get("operational_rules_unchanged") is True, "Reactome pattern changes operational rules")
    expect(errors, tld.get("claim_boundary_preserved") is True, "TLD pattern boundary not preserved")

    expect(errors, final.get("status") == "PASS", "Batch062 final status not PASS")
    expect(errors, final.get("current_protocol") == CURRENT_PROTOCOL, "Current protocol changed")
    expect(errors, final.get("issue_derived_repair_count") == 3, "Batch062 issue-derived count changed")
    expect(errors, final.get("native_external_repair_count") == 4, "Batch062 native external count changed")
    expect(errors, final.get("highest_impact_next_path") == EXPECTED_NEXT_ACTION, "Batch062 next path mismatch")
    expect(errors, final.get("next_allowed_action") == EXPECTED_NEXT_ACTION, "Batch062 next allowed action mismatch")
    expect(errors, final.get("full_scoring") == "NOT_RUN/disallowed", "Batch062 full scoring changed")
    expect(errors, final.get("memory_lift") == "not_demonstrated", "Batch062 memory lift changed")
    expect(errors, final.get("self_maintaining_software") == "false/not_demonstrated", "Batch062 self-maintaining changed")
    expect(errors, final.get("exact_blocker") is None, "Batch062 exact blocker should be None")
    for key in ["patch_generated", "patch_applied", "pre_repair_replay_run", "post_repair_replay_run", "duplicate_replay_run", "count_gate_run", "repair_count_increment"]:
        expect_false(errors, final, key, "Batch062 final decision")
        expect_false(errors, claim, key, "Batch062 claim boundary")
    expect_false(errors, claim, "repo_refactor_performed", "Batch062 claim boundary")
    expect_false(errors, claim, "source_behavior_changed", "Batch062 claim boundary")
    expect_false(errors, claim, "tests_mutated", "Batch062 claim boundary")
    for key in ["raw_zip_payload_committed", "runtime_workspaces_committed", "source_checkouts_committed", "venvs_committed", "caches_committed"]:
        expect_false(errors, package, key, "Batch062 package verification")

    current_cfg = (ROOT / "configs" / "controllergate_current.yaml").read_text(encoding="utf-8")
    expect(errors, "protocol_version: v2.14" in current_cfg, "Current protocol is not v2.14")
    audit_public_summary(errors)
    audit_git_status(errors)

    if errors:
        print("FAIL:")
        for error in errors:
            print(f"- {error}")
        return 1
    print("Batch062 next issue repair candidate selection audit PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
