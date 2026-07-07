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


OUT_DIR = ROOT / "outputs" / "post_v2_37_hardening_batch056_pre_repair_replay_wave_1_plus_wave_2_intake"
BATCH055_DIR = ROOT / "outputs" / "post_v2_37_hardening_batch055_seed_discovery_wave_1"
CURRENT_PROTOCOL = "v2.14"
EXPECTED_ARTIFACT = "post_v2_37_hardening_batch056_pre_repair_replay_wave_1_plus_wave_2_intake_artifacts"
WAVE_1_IDS = {
    "datasette_2461_async_event_loop_cli_tests",
    "freezegun_547_py313_datetimes_assertion",
    "venusian_91_py313_frameinfo_callinfo",
    "pexpect_699_replwrap_bash_assertions",
    "pyramid_3761_py313_test_util",
}
ALLOWED_CLASSIFICATIONS = {
    "pre_repair_failure_materialized",
    "failure_not_reproduced",
    "blocked_dependency_install_failure",
    "blocked_python_version_unavailable",
    "blocked_tox_env_unavailable",
    "blocked_native_test_missing",
    "blocked_repo_checkout_failure",
    "blocked_commit_unresolved",
    "blocked_command_ambiguous",
    "blocked_environment_unclear",
    "blocked_timeout",
    "blocked_network_required",
    "blocked_compiled_dependency",
    "blocked_provider_precondition",
    "blocked_decision_time_leakage_risk",
    "blocked_issue_mismatch",
    "probe_only_needs_manual_review",
}
REQUIRED_TOP_LEVEL = [
    "batch055_artifact_ingestion_summary.json",
    "batch055_artifact_sha256_verification.json",
    "batch055_result_preservation.json",
    "batch055_candidate_plan_preservation.json",
    "batch055_claim_boundary_preservation.json",
    "batch055_next_action_boundary.json",
    "pre_repair_replay_wave_1_plan.json",
    "pre_repair_replay_wave_1_results.json",
    "pre_repair_replay_wave_1_summary.md",
    "materialized_failure_candidates_for_batch057.json",
    "wave_1_blocked_candidate_registry.json",
    "wave_1_replay_dashboard.json",
    "wave_1_exact_blockers.json",
    "batch057_patch_gate_recommendation.json",
    "seed_lead_registry_wave_2.json",
    "seed_lead_registry_wave_2_normalized.json",
    "issue_body_leakage_screen_wave_2.json",
    "candidate_commit_resolution_audit_wave_2.json",
    "candidate_approval_gate_results_wave_2.json",
    "duplicate_seed_rejection_audit_wave_2.json",
    "wave_2_pre_repair_replay_plan.json",
    "wave_2_campaign_dashboard.json",
    "combined_campaign_summary.md",
    "twenty_seed_campaign_dashboard_v2.json",
    "claim_boundary.json",
    "audit.json",
    "package_verification.json",
    "artifact_sha256_verification.json",
    "SHA256SUMS.txt",
]
REQUIRED_CANDIDATE_FILES = [
    "candidate_replay_plan.json",
    "candidate_commit_verification.json",
    "candidate_workspace_manifest.json",
    "candidate_dependency_plan.json",
    "candidate_command_context.json",
    "candidate_command_normalization.json",
    "pre_repair_replay_command.txt",
    "pre_repair_replay_log_raw.txt",
    "pre_repair_replay_result.json",
    "failure_signature_extract.txt",
    "decision_time_input_manifest.json",
    "issue_body_leakage_boundary.json",
    "label_blindness_check.json",
    "gold_patch_exclusion_check.json",
    "future_evidence_exclusion_check.json",
    "workspace_custody_check.json",
    "provider_precondition_check.json",
    "classification.json",
]


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def git_lines(*args: str) -> list[str]:
    result = subprocess.run(
        ["git", *args],
        cwd=ROOT,
        text=True,
        encoding="utf-8",
        errors="replace",
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or result.stdout.strip())
    return [line.strip() for line in result.stdout.splitlines() if line.strip()]


def main() -> int:
    errors: list[str] = []
    for rel in REQUIRED_TOP_LEVEL:
        if not (OUT_DIR / rel).is_file():
            errors.append(f"missing required Batch056 output: {rel}")
    if errors:
        print("FAIL:", errors)
        return 1

    manifest = verify_manifest(OUT_DIR)
    if manifest.get("status") != "PASS":
        errors.append(f"Batch056 SHA256SUMS mismatch: {manifest}")

    ingest = read_json(OUT_DIR / "batch055_artifact_ingestion_summary.json")
    artifact_verification = read_json(OUT_DIR / "batch055_artifact_sha256_verification.json")
    result_preservation = read_json(OUT_DIR / "batch055_result_preservation.json")
    plan_preservation = read_json(OUT_DIR / "batch055_candidate_plan_preservation.json")
    claim_preservation = read_json(OUT_DIR / "batch055_claim_boundary_preservation.json")
    next_boundary = read_json(OUT_DIR / "batch055_next_action_boundary.json")
    wave1_plan = read_json(OUT_DIR / "pre_repair_replay_wave_1_plan.json")
    wave1_results = read_json(OUT_DIR / "pre_repair_replay_wave_1_results.json")
    materialized = read_json(OUT_DIR / "materialized_failure_candidates_for_batch057.json")
    blocked = read_json(OUT_DIR / "wave_1_blocked_candidate_registry.json")
    blockers = read_json(OUT_DIR / "wave_1_exact_blockers.json")
    recommendation = read_json(OUT_DIR / "batch057_patch_gate_recommendation.json")
    wave2_registry = read_json(OUT_DIR / "seed_lead_registry_wave_2.json")
    wave2_normalized = read_json(OUT_DIR / "seed_lead_registry_wave_2_normalized.json")
    wave2_leakage = read_json(OUT_DIR / "issue_body_leakage_screen_wave_2.json")
    wave2_resolution = read_json(OUT_DIR / "candidate_commit_resolution_audit_wave_2.json")
    wave2_approval = read_json(OUT_DIR / "candidate_approval_gate_results_wave_2.json")
    wave2_plan = read_json(OUT_DIR / "wave_2_pre_repair_replay_plan.json")
    wave2_dashboard = read_json(OUT_DIR / "wave_2_campaign_dashboard.json")
    dashboard = read_json(OUT_DIR / "twenty_seed_campaign_dashboard_v2.json")
    claim = read_json(OUT_DIR / "claim_boundary.json")
    package = read_json(OUT_DIR / "package_verification.json")
    artifact_sha = read_json(OUT_DIR / "artifact_sha256_verification.json")

    batch055_results = read_json(BATCH055_DIR / "seed_discovery_wave_1_results.json")
    if ingest.get("status") != "PASS" or artifact_verification.get("status") != "PASS":
        errors.append("Batch055 artifact ingest/verification did not PASS")
    if artifact_verification.get("zip_sha256") != "f4d05c2814e7f7c23b74e046b02c1af915979907a9c8acd6046c622149fbe77c":
        errors.append("Batch055 artifact SHA mismatch")
    if artifact_verification.get("zip_entry_count") != 23:
        errors.append("Batch055 ZIP entry count mismatch")
    if artifact_verification.get("artifact_manifest", {}).get("checked") != 22:
        errors.append("Batch055 artifact-level manifest coverage mismatch")
    if artifact_verification.get("output_manifests", {}).get("post_v2_37_hardening_batch055_seed_discovery_wave_1", {}).get("checked") != 21:
        errors.append("Batch055 internal manifest coverage mismatch")
    if ingest.get("raw_zip_bytes_ingested") is not False or ingest.get("zip_payload_committed") is not False:
        errors.append("Batch055 raw artifact boundary failed")

    if result_preservation.get("issue_derived_repair_count") != 2:
        errors.append("Issue-derived repair count not preserved at 2")
    if result_preservation.get("native_external_repair_count") != 4:
        errors.append("Native external repair count not preserved at 4")
    if result_preservation.get("approved_for_pre_repair_replay") != 8 or result_preservation.get("planned_batch056_candidates") != 5:
        errors.append("Batch055 replay plan counts not preserved")
    if result_preservation.get("next_allowed_action") != "batch056_pre_repair_replay_wave_1":
        errors.append("Batch055 next action boundary changed")
    if plan_preservation.get("status") != "PASS":
        errors.append("Batch055 candidate plan preservation failed")
    if claim_preservation.get("status") != "PASS" or claim_preservation.get("batch056_count_increment") is not False:
        errors.append("Batch055 claim boundary preservation failed")
    if next_boundary.get("patching_allowed") is not False or next_boundary.get("duplicate_replay_allowed") is not False or next_boundary.get("count_gate_allowed") is not False:
        errors.append("Batch056 next-action boundary allows a forbidden action")
    if batch055_results.get("issue_derived_repair_count") != 2 or batch055_results.get("native_external_repair_count") != 4:
        errors.append("Committed Batch055 results do not preserve repair counts")

    if wave1_plan.get("candidate_count") != 5:
        errors.append("Wave 1 plan does not cover exactly five candidates")
    result_rows = wave1_results.get("results", [])
    if {row.get("lead_id") for row in result_rows} != WAVE_1_IDS:
        errors.append("Wave 1 results do not cover the exact planned candidate set")
    materialized_ids = {row.get("lead_id") for row in materialized.get("candidates", [])}
    blocked_ids = {row.get("lead_id") for row in blocked.get("candidates", [])}
    if materialized.get("count", 0) + blocked.get("count", 0) != 5:
        errors.append("Wave 1 materialized + blocked counts do not equal five")
    for row in result_rows:
        lead_id = row.get("lead_id")
        classification = row.get("classification")
        if classification not in ALLOWED_CLASSIFICATIONS:
            errors.append(f"Wave 1 candidate has invalid classification: {lead_id}={classification}")
        candidate_dir = OUT_DIR / "wave_1_candidates" / lead_id
        for rel in REQUIRED_CANDIDATE_FILES:
            if not (candidate_dir / rel).is_file():
                errors.append(f"missing candidate output for {lead_id}: {rel}")
        if not errors:
            commit = read_json(candidate_dir / "candidate_commit_verification.json")
            command = read_json(candidate_dir / "candidate_command_context.json")
            replay = read_json(candidate_dir / "pre_repair_replay_result.json")
            decision = read_json(candidate_dir / "decision_time_input_manifest.json")
            leakage = read_json(candidate_dir / "issue_body_leakage_boundary.json")
            label = read_json(candidate_dir / "label_blindness_check.json")
            gold = read_json(candidate_dir / "gold_patch_exclusion_check.json")
            future = read_json(candidate_dir / "future_evidence_exclusion_check.json")
            workspace = read_json(candidate_dir / "workspace_custody_check.json")
            provider = read_json(candidate_dir / "provider_precondition_check.json")
            class_record = read_json(candidate_dir / "classification.json")
            if commit.get("git_cat_file_e_commit_verified") is not True:
                errors.append(f"Wave 1 commit verification failed: {lead_id}")
            if command.get("selected_command") is None:
                errors.append(f"Wave 1 command context missing selected command: {lead_id}")
            if replay.get("patch_generated") is not False or replay.get("patch_attempted") is not False:
                errors.append(f"Wave 1 replay generated or attempted a patch: {lead_id}")
            if decision.get("fixed_gold_future_evidence_used") is not False or decision.get("issue_body_repair_evidence_used") is not False:
                errors.append(f"Wave 1 decision-time firewall failed: {lead_id}")
            if leakage.get("issue_body_persisted_as_repair_evidence") is not False or leakage.get("patch_or_workaround_text_used") is not False:
                errors.append(f"Wave 1 issue body leakage boundary failed: {lead_id}")
            if label.get("hidden_labels_used") is not False or gold.get("gold_patch_used") is not False or future.get("future_evidence_used") is not False:
                errors.append(f"Wave 1 hidden/fixed/future evidence exclusion failed: {lead_id}")
            if workspace.get("raw_workspace_committed") is not False:
                errors.append(f"Wave 1 workspace custody failed: {lead_id}")
            if provider.get("environment_or_provider_failure_classified_as_repair_failure") is not False:
                errors.append(f"Wave 1 provider precondition classification failed: {lead_id}")
            if class_record.get("patch_generated") is not False or class_record.get("repair_attempted") is not False or class_record.get("count_gate_run") is not False:
                errors.append(f"Wave 1 classification boundary failed: {lead_id}")
        if classification == "pre_repair_failure_materialized" and lead_id not in materialized_ids:
            errors.append(f"materialized Wave 1 candidate missing from materialized registry: {lead_id}")
        if classification != "pre_repair_failure_materialized" and lead_id not in blocked_ids:
            errors.append(f"blocked/non-materialized Wave 1 candidate missing from blocked registry: {lead_id}")

    rec_ids = {row.get("lead_id") for row in recommendation.get("recommended_candidates", [])}
    if rec_ids != materialized_ids:
        errors.append("Batch057 patch-gate recommendation does not exactly match materialized failures")
    if any(row.get("lead_id") in blocked_ids for row in recommendation.get("recommended_candidates", [])):
        errors.append("Batch057 patch-gate recommendation includes blocked/non-materialized candidates")
    if blockers.get("status") != "PASS":
        errors.append("Wave 1 exact blocker registry missing PASS status")

    wave2_leads = wave2_registry.get("leads", [])
    normalized = wave2_normalized.get("leads", [])
    if not wave2_leads or len(wave2_leads) != len(normalized):
        errors.append("Wave 2 registry normalization does not cover all leads")
    if wave2_dashboard.get("leads_screened") != len(normalized):
        errors.append("Wave 2 dashboard lead count mismatch")
    if len(wave2_leakage.get("records", [])) != len(normalized):
        errors.append("Wave 2 leakage screen does not cover every lead")
    if len(wave2_resolution.get("records", [])) != len(normalized):
        errors.append("Wave 2 commit-resolution audit does not cover every lead")
    if len(wave2_approval.get("records", [])) != len(normalized):
        errors.append("Wave 2 approval gate does not cover every lead")
    if wave2_approval.get("pre_repair_replay_run_in_batch056") is not False or wave2_plan.get("batch056_pre_repair_replay_run_for_wave_2") is not False:
        errors.append("Wave 2 ran pre-repair replay in Batch056")
    for key in ["patch_generated_in_batch056", "count_gate_run_in_batch056"]:
        if wave2_approval.get(key) is not False:
            errors.append(f"Wave 2 forbidden action boundary failed: {key}")
    for row in normalized:
        if row.get("lead_is_seed") is not False or row.get("helper_provided_sha_trusted") is not False:
            errors.append(f"Wave 2 lead treated as trusted seed/helper SHA: {row.get('lead_id')}")
    for row in wave2_leakage.get("records", []):
        if row.get("issue_body_persisted") is not False or row.get("issue_body_used_as_repair_evidence") is not False or row.get("fix_or_workaround_text_persisted") is not False:
            errors.append(f"Wave 2 leakage screen persisted issue repair evidence: {row.get('lead_id')}")
    for row in wave2_resolution.get("records", []):
        if row.get("helper_provided_sha_trusted") is not False or row.get("fixed_or_future_evidence_used") is not False or row.get("patch_or_fix_text_used") is not False:
            errors.append(f"Wave 2 resolution used forbidden evidence: {row.get('lead_id')}")
        if row.get("wave_2_pre_repair_replay_run") is not False or row.get("patch_generated") is not False or row.get("count_gate_run") is not False:
            errors.append(f"Wave 2 resolution performed forbidden action: {row.get('lead_id')}")

    if dashboard.get("issue_derived_repair_count") != 2 or dashboard.get("native_external_repair_count") != 4:
        errors.append("Combined dashboard repair counts changed")
    if dashboard.get("full_scoring") != "NOT_RUN/disallowed" or dashboard.get("memory_lift") != "not_demonstrated" or dashboard.get("self_maintaining_software") != "false/not_demonstrated":
        errors.append("Combined dashboard claim boundary overclaim")
    if dashboard.get("wave_1_materialized_failure_count") != len(materialized_ids):
        errors.append("Combined dashboard Wave 1 materialized count mismatch")
    if dashboard.get("wave_2_approved_for_future_replay_count") != wave2_approval.get("approved_for_future_pre_repair_replay_count"):
        errors.append("Combined dashboard Wave 2 approval count mismatch")
    if claim.get("current_protocol") != CURRENT_PROTOCOL:
        errors.append("Current protocol boundary changed")
    for key in ["batch056_patch_generated", "batch056_source_only_repair_run", "batch056_duplicate_replay_run", "batch056_count_gate_run"]:
        if claim.get(key) is not False:
            errors.append(f"Claim boundary says forbidden action ran: {key}")
    if claim.get("issue_derived_repair_count") != 2 or claim.get("native_external_repair_count") != 4:
        errors.append("Claim boundary repair counts changed")
    if package.get("status") != "PASS" or package.get("artifact_name") != EXPECTED_ARTIFACT:
        errors.append("Package verification failed")
    if artifact_sha.get("status") != "PENDING_WORKFLOW_ARTIFACT":
        errors.append("Artifact SHA should remain pending until workflow upload")

    tracked = git_lines("ls-files")
    forbidden_tracked = [
        path for path in tracked
        if path.startswith("incoming_artifacts/")
        or path.startswith("artifact_payload/")
        or path.startswith("outputs/post_v2_37_hardening_batch056_pre_repair_replay_wave_1_plus_wave_2_intake/") and (
            path.endswith((".zip", ".tar", ".tar.gz", ".tgz", ".7z", ".whl", ".pyc", ".pyo"))
            or "/__pycache__/" in path
            or "/.pytest_cache/" in path
            or "/.venv/" in path
            or "/venv/" in path
        )
        or "/ControllerGate_runtime/" in path
    ]
    if forbidden_tracked:
        errors.append(f"forbidden tracked payloads: {forbidden_tracked[:10]}")
    staged = git_lines("diff", "--cached", "--name-only")
    if any(path.startswith("incoming_artifacts/") or path.startswith("artifact_payload/") or path.endswith((".zip", ".tar", ".tar.gz", ".tgz", ".7z")) for path in staged):
        errors.append("incoming artifacts, payload directories, or archives are staged")

    if errors:
        print("FAIL:", errors)
        return 1
    print("Batch056 pre-repair replay wave 1 plus wave 2 intake audit PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
