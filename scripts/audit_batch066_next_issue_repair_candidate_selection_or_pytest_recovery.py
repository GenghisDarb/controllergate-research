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


OUT_DIR = ROOT / "outputs" / "post_v2_37_hardening_batch066_next_issue_repair_candidate_selection_or_pytest_recovery"
CURRENT_PROTOCOL = "v2.14"

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
    ".venv",
    "/venv/",
    "\\venv\\",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
]

REQUIRED_FILES = [
    "batch065_artifact_ingestion_summary.json",
    "batch065_artifact_sha256_verification.json",
    "batch065_result_preservation.json",
    "batch065_freezegun_counted_repair_preservation.json",
    "batch065_proof_ledger_preservation.json",
    "batch065_post_count_acceleration_preservation.json",
    "batch065_public_readiness_preservation.json",
    "batch065_repo_topology_preservation.json",
    "batch065_claim_boundary_preservation.json",
    "batch065_next_action_boundary.json",
    "batch066_strategic_path_review.json",
    "batch066_next_count_opportunity_queue.json",
    "batch066_candidate_path_comparison.json",
    "batch066_next_best_proof_path.json",
    "batch066_repo_hygiene_pressure_check.json",
    "batch066_public_readiness_pressure_check.json",
    "pytest_command_boundary_recovery_plan.json",
    "pytest_command_boundary_evidence_manifest.json",
    "pytest_command_boundary_forbidden_evidence_audit.json",
    "pytest_command_boundary_scope.json",
    "pytest_command_boundary_non_repair_boundary.json",
    "pytest_workspace_manifest.json",
    "pytest_commit_verification.json",
    "pytest_workspace_custody_check.json",
    "pytest_baseline_source_hashes.json",
    "pytest_declared_dependency_map.json",
    "pytest_declared_runtime_map.json",
    "pytest_declared_test_command_map.json",
    "pytest_project_config_map.json",
    "pytest_command_context_batch066.json",
    "pytest_command_boundary_probe_plan.json",
    "pytest_command_boundary_probe_results.json",
    "pytest_command_boundary_log_raw.txt",
    "pytest_collect_only_result.json",
    "pytest_command_config_error_extract.json",
    "pytest_command_boundary_classification.json",
    "pytest_provider_runtime_capsule_plan.json",
    "pytest_provider_install_attempt.json",
    "pytest_provider_install_log_raw.txt",
    "pytest_provider_runtime_setup_result.json",
    "pytest_prerepair_not_run_reason.json",
    "pytest_prerepair_replay_plan_batch066.json",
    "pytest_prerepair_replay_command.txt",
    "pytest_prerepair_replay_log_raw.txt",
    "pytest_prerepair_replay_result.json",
    "pytest_prerepair_failure_signature_extract.json",
    "pytest_prerepair_outcome_classification.json",
    "pytest_diagnostic_not_run_reason.json",
    "pytest_diagnostic_minimal_replay_plan.json",
    "pytest_diagnostic_minimal_replay_results.json",
    "pytest_diagnostic_failed_node_registry.json",
    "pytest_diagnostic_traceback_roots.json",
    "pytest_diagnostic_failure_signature_extract.json",
    "pytest_amds_full_bug_tree_state_batch066.json",
    "pytest_amds_node_registry_batch066.json",
    "pytest_amds_next_action_frontier_batch066.json",
    "pytest_patch_license_from_amds_batch066.json",
    "pytest_source_contact_prior_or_replay_map_batch066.json",
    "pytest_provider_dependency_replay_map_batch066.json",
    "pytest_interpreter_behavior_replay_map_batch066.json",
    "batch066_permanent_fix_queue_review.json",
    "batch066_repo_hygiene_priority_matrix.json",
    "batch066_duplicate_function_risk_review.json",
    "batch066_shared_utility_extraction_recommendation.json",
    "batch066_public_readiness_recommendation.json",
    "batch066_reactome_provider_capsule_utilization_plan.json",
    "batch066_tld_governance_utilization_plan.json",
    "batch066_isomorphic_logic_to_engineering_gap_closure_plan.json",
    "batch066_public_safe_engineering_translation_plan.json",
    "project_health_review_batch066.json",
    "capability_maturity_scorecard_batch066.json",
    "version_progress_grade_batch066.json",
    "strategic_direction_check_batch066.json",
    "proof_milestone_distance_report_batch066.json",
    "regression_and_drift_watch_batch066.json",
    "self_maintenance_readiness_review_batch066.json",
    "next_highest_impact_action_report_batch066.json",
    "batch066_final_decision.json",
    "batch067_or_batch063b_next_prompt_plan.json",
    "batch063b_pytest_provider_runtime_recovery_followup_recommendation.json",
    "batch067_pytest_source_only_patch_gate_recommendation.json",
    "batch058d_seed_discovery_expansion_recommendation.json",
    "batch062b_repo_hygiene_utility_consolidation_planning_recommendation.json",
    "memory_lift_future_plan_recommendation.json",
    "batch066_summary.md",
    "claim_boundary.json",
    "audit.json",
    "package_verification.json",
    "artifact_sha256_verification.json",
    "SHA256SUMS.txt",
]


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def expect(errors: list[str], condition: bool, message: str) -> None:
    if not condition:
        errors.append(message)


def run_python_script(rel: str, errors: list[str]) -> None:
    proc = subprocess.run([sys.executable, rel], cwd=ROOT, text=True, capture_output=True, check=False)
    if proc.returncode != 0:
        errors.append(f"{rel} failed: {proc.stdout[-1000:]} {proc.stderr[-1000:]}")


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


def public_batch066_block(path: Path) -> str:
    text = path.read_text(encoding="utf-8")
    marker = "Batch066 is the latest strategic transition and Pytest command-boundary recovery boundary."
    start = text.find(marker)
    if start == -1:
        return ""
    next_marker = text.find("Batch065 is the latest duplicate clean replay", start)
    if next_marker == -1:
        next_marker = min(len(text), start + 5000)
    return text[start:next_marker]


def audit_public_summary(errors: list[str]) -> None:
    for rel in [
        "README.md",
        "docs/current_status.md",
        "controllergate_v1_7_beta/reports/critic_review_package/shareable_summary.md",
    ]:
        block = public_batch066_block(ROOT / rel)
        expect(errors, bool(block), f"missing Batch066 public summary block in {rel}")
        for phrase in [
            "Workflow success is not equivalent to repair success.",
            "Command-boundary normalization is not repair success.",
            "Provider/runtime setup is not repair success.",
            "Pre-repair replay is not repair success.",
            "A repair is counted only after source-only target pass, duplicate clean replay, and count gate.",
            "The project health grade is advisory and does not constitute proof.",
            "Self-maintaining software remains false/not_demonstrated.",
        ]:
            expect(errors, phrase in block, f"Batch066 public summary missing {phrase!r} in {rel}")
        lowered = block.lower()
        for term in PUBLIC_FORBIDDEN_TERMS:
            expect(errors, term.lower() not in lowered, f"Batch066 public summary contains internal term {term!r} in {rel}")


def main() -> int:
    errors: list[str] = []
    if not OUT_DIR.is_dir():
        print(f"FAIL: missing output directory: {OUT_DIR.relative_to(ROOT)}")
        return 1
    for rel in REQUIRED_FILES:
        expect(errors, (OUT_DIR / rel).is_file(), f"missing required Batch066 output: {rel}")
    if errors:
        print("FAIL:")
        for error in errors:
            print(f"- {error}")
        return 1

    manifest = verify_manifest(OUT_DIR)
    expect(errors, manifest.get("status") == "PASS", f"Batch066 SHA256SUMS verification failed: {manifest}")

    artifact = read_json(OUT_DIR / "batch065_artifact_sha256_verification.json")
    preservation = read_json(OUT_DIR / "batch065_result_preservation.json")
    counted = read_json(OUT_DIR / "batch065_freezegun_counted_repair_preservation.json")
    ledger = read_json(OUT_DIR / "batch065_proof_ledger_preservation.json")
    claim_preserve = read_json(OUT_DIR / "batch065_claim_boundary_preservation.json")
    scope = read_json(OUT_DIR / "pytest_command_boundary_scope.json")
    forbidden = read_json(OUT_DIR / "pytest_command_boundary_forbidden_evidence_audit.json")
    workspace = read_json(OUT_DIR / "pytest_workspace_custody_check.json")
    commit = read_json(OUT_DIR / "pytest_commit_verification.json")
    classification = read_json(OUT_DIR / "pytest_command_boundary_classification.json")
    provider = read_json(OUT_DIR / "pytest_provider_runtime_setup_result.json")
    prerepair = read_json(OUT_DIR / "pytest_prerepair_outcome_classification.json")
    diagnostic = read_json(OUT_DIR / "pytest_diagnostic_not_run_reason.json")
    license_ = read_json(OUT_DIR / "pytest_patch_license_from_amds_batch066.json")
    permanent = read_json(OUT_DIR / "batch066_permanent_fix_queue_review.json")
    hygiene = read_json(OUT_DIR / "batch066_repo_hygiene_priority_matrix.json")
    shared = read_json(OUT_DIR / "batch066_shared_utility_extraction_recommendation.json")
    provider_plan = read_json(OUT_DIR / "batch066_reactome_provider_capsule_utilization_plan.json")
    governance_plan = read_json(OUT_DIR / "batch066_tld_governance_utilization_plan.json")
    final = read_json(OUT_DIR / "batch066_final_decision.json")
    claim = read_json(OUT_DIR / "claim_boundary.json")
    package = read_json(OUT_DIR / "package_verification.json")

    expect(errors, artifact.get("status") == "PASS", "Batch065 artifact verification did not pass")
    expect(errors, artifact.get("zip_sha256") == "b07f7f793ede2f61fdc6a5f692efe2b0735e53d1effdd466f3df2fba8288f5a8", "Batch065 artifact SHA mismatch")
    expect(errors, artifact.get("zip_size_bytes") == 75863, "Batch065 artifact size mismatch")
    expect(errors, artifact.get("zip_entry_count") == 120, "Batch065 artifact entry count mismatch")
    expect(errors, artifact.get("artifact_manifest", {}).get("status") == "PASS", "Batch065 artifact manifest failed")
    expect(errors, artifact.get("output_manifest", {}).get("status") == "PASS", "Batch065 output manifest failed")
    expect(errors, preservation.get("issue_derived_repair_count_after_batch065") == 4, "Issue-derived repair count 4 not preserved")
    expect(errors, preservation.get("native_external_repair_count") == 4, "Native external repair count changed")
    expect(errors, preservation.get("full_scoring") == "NOT_RUN/disallowed", "Full scoring changed")
    expect(errors, preservation.get("memory_lift") == "not_demonstrated", "Memory lift changed")
    expect(errors, preservation.get("self_maintaining_software") == "false/not_demonstrated", "Self-maintaining status changed")
    expect(errors, counted.get("freezegun_counted_repair") is True, "Freezegun counted repair not preserved")
    expect(errors, ledger.get("status") == "PASS", "Proof ledger preservation missing")
    expect(errors, claim_preserve.get("no_batch066_count_increment") is True, "Batch066 count increment boundary not preserved")
    expect(errors, scope.get("patching_allowed") is False and scope.get("duplicate_replay_allowed") is False and scope.get("count_gate_allowed") is False, "Batch066 Pytest scope overreached")
    for key in ["fixed_commit_used", "future_commit_used", "pr_patch_used", "gold_patch_used", "issue_body_fix_or_workaround_text_used", "modern_fixed_source_used", "source_patched", "test_modified", "fixture_modified", "synthetic_test_used"]:
        expect(errors, forbidden.get(key) is False, f"Forbidden evidence expected {key}=false")
    expect(errors, workspace.get("status") == "PASS" and workspace.get("testing_exists") is True and workspace.get("project_config_exists") is True, "Pytest workspace custody failed")
    expect(errors, workspace.get("patch_applied") is False, "Pytest workspace was patched")
    expect(errors, commit.get("status") == "PASS" and commit.get("resolved_head") == "041aacad506b6c6891f2898f2bd378e0896e8b86", "Pytest commit verification failed")
    expect(errors, classification.get("classification") in {"pytest_command_boundary_blocked_config_minversion", "pytest_command_boundary_normalized", "pytest_command_boundary_invalid_preserved_command", "pytest_command_boundary_blocked_unavailable_runner"}, "Invalid Pytest command-boundary classification")
    expect(errors, provider.get("provider_setup_is_repair_success") is False, "Provider setup must not be repair success")
    if classification.get("classification") != "pytest_command_boundary_normalized":
        expect(errors, prerepair.get("status") == "NOT_RUN", "Pre-repair replay should not run while command boundary remains blocked")
        expect(errors, diagnostic.get("status") == "NOT_RUN", "Diagnostics should not run without materialized pre-repair failure")
        expect(errors, license_.get("future_only") is True and license_.get("patch_generation_allowed_in_batch066") is False, "Pytest patch license must be future-only and closed in Batch066")
    expect(errors, permanent.get("status") == "PASS", "Permanent-fix queue review missing")
    expect(errors, hygiene.get("status") == "PASS", "Repo hygiene priority matrix missing")
    expect(errors, shared.get("do_not_implement_in_batch066") is True, "Batch066 must not implement shared utility extraction")
    expect(errors, provider_plan.get("not_repair_evidence") is True, "Provider-capsule plan must not be repair evidence")
    expect(errors, governance_plan.get("not_public_proof_language") is True, "Governance plan must not be public proof language")
    expect(errors, final.get("status") == "PASS", "Final decision did not pass")
    expect(errors, final.get("current_protocol") == CURRENT_PROTOCOL, "Current protocol changed")
    expect(errors, final.get("issue_derived_repair_count") == 4, "Final issue-derived repair count not preserved at 4")
    expect(errors, final.get("native_external_repair_count") == 4, "Final native external repair count changed")
    expect(errors, final.get("patch_generated") is False and final.get("patch_applied") is False, "Batch066 generated or applied a patch")
    expect(errors, final.get("source_mutated") is False and final.get("tests_mutated") is False and final.get("fixtures_mutated") is False, "Batch066 mutated source/tests/fixtures")
    expect(errors, final.get("duplicate_replay_run") is False and final.get("count_gate_run") is False and final.get("repair_count_increment") is False, "Batch066 ran duplicate replay/count gate or incremented count")
    expect(errors, final.get("full_scoring") == "NOT_RUN/disallowed", "Full scoring changed")
    expect(errors, final.get("memory_lift") == "not_demonstrated", "Memory lift changed")
    expect(errors, final.get("self_maintaining_software") == "false/not_demonstrated", "Self-maintaining status changed")
    expect(errors, final.get("next_allowed_action") in {"batch067_pytest_source_only_patch_gate", "batch067_pytest_failure_family_decomposition", "batch063b_pytest_provider_runtime_recovery_followup", "batch058d_seed_discovery_expansion", "batch062b_repo_hygiene_utility_consolidation_planning"}, "Invalid next allowed action")
    expect(errors, claim.get("repair_count_increment") is False and claim.get("full_scoring") == "NOT_RUN/disallowed", "Claim boundary overreached")
    for key in ["raw_zip_payload_committed", "runtime_workspaces_committed", "source_checkouts_committed", "venvs_committed", "caches_committed"]:
        expect(errors, package.get(key) is False, f"Package verification expected {key}=false")

    audit_public_summary(errors)
    audit_git_status(errors)
    run_python_script("scripts/audit_batch065_duplicate_clean_replay_count_gate_freezegun.py", errors)
    proc = subprocess.run([sys.executable, "scripts/controllergate_audit.py", "--protocol", "current"], cwd=ROOT, text=True, capture_output=True, check=False)
    expect(errors, proc.returncode == 0, f"current protocol audit failed: {proc.stdout[-1000:]} {proc.stderr[-1000:]}")
    proc = subprocess.run([sys.executable, "scripts/controllergate_run.py", "--protocol", "current", "--dry-run"], cwd=ROOT, text=True, capture_output=True, check=False)
    expect(errors, proc.returncode == 0, f"current protocol dry-run failed: {proc.stdout[-1000:]} {proc.stderr[-1000:]}")

    if errors:
        print("FAIL:")
        for error in errors:
            print(f"- {error}")
        return 1
    print("Batch066 next issue-repair candidate selection Pytest recovery audit PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
