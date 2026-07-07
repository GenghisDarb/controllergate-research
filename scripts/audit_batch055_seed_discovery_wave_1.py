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


OUT_DIR = ROOT / "outputs" / "post_v2_37_hardening_batch055_seed_discovery_wave_1"
BATCH054_DIR = ROOT / "outputs" / "clean_replication_batch_054"
EXPECTED_BATCH054_STATUS = "PASS_WITH_BATCH054_ISSUE_DERIVED_REPAIR_COUNT_LOCKED"
EXPECTED_ARTIFACT = "post_v2_37_hardening_batch055_seed_discovery_wave_1_artifacts"
NEXT_ACTION = "batch056_pre_repair_replay_wave_1"

REQUIRED_FILES = [
    "batch054_artifact_ingestion_summary.json",
    "batch054_artifact_sha256_verification.json",
    "batch054_result_preservation.json",
    "batch054_count_gate_preservation.json",
    "batch054_issue_derived_count_lock_report.md",
    "batch054_next_action_boundary.json",
    "seed_lead_registry.json",
    "seed_lead_registry_normalized.json",
    "lead_augmentation_search_report.md",
    "issue_body_leakage_screen.json",
    "candidate_commit_resolution_audit.json",
    "duplicate_seed_rejection_audit.json",
    "candidate_approval_gate_results.json",
    "pre_repair_replay_wave_plan.json",
    "seed_discovery_wave_1_results.json",
    "twenty_seed_campaign_dashboard.json",
    "campaign_summary.md",
    "claim_boundary.json",
    "audit.json",
    "package_verification.json",
    "artifact_sha256_verification.json",
    "SHA256SUMS.txt",
]

def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def git_lines(*args: str) -> list[str]:
    result = subprocess.run(
        ["git", *args],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or result.stdout.strip())
    return [line.strip() for line in result.stdout.splitlines() if line.strip()]


def main() -> int:
    errors: list[str] = []
    for name in REQUIRED_FILES:
        if not (OUT_DIR / name).is_file():
            errors.append(f"missing required Batch055 output: {name}")
    if errors:
        print("FAIL:", errors)
        return 1
    manifest = verify_manifest(OUT_DIR)
    if manifest.get("status") != "PASS":
        errors.append(f"Batch055 SHA256SUMS mismatch: {manifest}")

    ingest = read_json(OUT_DIR / "batch054_artifact_ingestion_summary.json")
    artifact_verification = read_json(OUT_DIR / "batch054_artifact_sha256_verification.json")
    result_preservation = read_json(OUT_DIR / "batch054_result_preservation.json")
    count_preservation = read_json(OUT_DIR / "batch054_count_gate_preservation.json")
    next_boundary = read_json(OUT_DIR / "batch054_next_action_boundary.json")
    registry = read_json(OUT_DIR / "seed_lead_registry.json")
    normalized_registry = read_json(OUT_DIR / "seed_lead_registry_normalized.json")
    leakage = read_json(OUT_DIR / "issue_body_leakage_screen.json")
    resolution = read_json(OUT_DIR / "candidate_commit_resolution_audit.json")
    duplicates = read_json(OUT_DIR / "duplicate_seed_rejection_audit.json")
    approvals = read_json(OUT_DIR / "candidate_approval_gate_results.json")
    plan = read_json(OUT_DIR / "pre_repair_replay_wave_plan.json")
    results = read_json(OUT_DIR / "seed_discovery_wave_1_results.json")
    dashboard = read_json(OUT_DIR / "twenty_seed_campaign_dashboard.json")
    claim = read_json(OUT_DIR / "claim_boundary.json")
    package = read_json(OUT_DIR / "package_verification.json")
    artifact_sha = read_json(OUT_DIR / "artifact_sha256_verification.json")

    batch054_state = read_json(BATCH054_DIR / "consolidated_state_clean_replication_batch_054.json")
    if batch054_state.get("status") != EXPECTED_BATCH054_STATUS:
        errors.append("existing Batch054 committed state is not preserved")
    if ingest.get("status") != "PASS" or artifact_verification.get("status") != "PASS":
        errors.append("Batch054 official artifact ingest/verification did not PASS")
    if artifact_verification.get("zip_sha256") != "4fa4d5a47cf09f781165c6922b4e2910ad3363a7a6eb033f90f7a5c9ee9ca095":
        errors.append("Batch054 local ZIP SHA mismatch")
    if artifact_verification.get("zip_entry_count") != 166:
        errors.append("Batch054 ZIP entry count mismatch")
    if artifact_verification.get("artifact_manifest", {}).get("checked") != 165:
        errors.append("Batch054 artifact manifest coverage mismatch")
    if artifact_verification.get("output_manifests", {}).get("clean_replication_batch_054", {}).get("checked") != 21:
        errors.append("Batch054 output manifest coverage mismatch")
    if artifact_verification.get("output_manifests", {}).get("post_v2_37_hardening_001", {}).get("checked") != 142:
        errors.append("Batch054 post output manifest coverage mismatch")
    for field in ["raw_zip_bytes_ingested", "zip_payload_committed"]:
        if ingest.get(field) is not False or artifact_verification.get(field) is not False:
            errors.append(f"raw artifact boundary failed: {field}")

    if result_preservation.get("issue_derived_repair_count") != 2 or count_preservation.get("issue_derived_repair_count_after") != 2:
        errors.append("Issue-derived repair count is not preserved at 2")
    if result_preservation.get("native_external_repair_count") != 4 or count_preservation.get("native_external_repair_count") != 4:
        errors.append("Native external repair count is not preserved at 4")
    if result_preservation.get("next_seed_fastlane") != "WAITING_FOR_FRESH_SEED":
        errors.append("Batch054 next seed fastlane boundary not preserved")
    if result_preservation.get("next_allowed_action") != "batch055_next_patch_seed_gate":
        errors.append("Batch054 next action boundary not preserved")
    if next_boundary.get("batch055_next_allowed_action") != NEXT_ACTION:
        errors.append("Batch055 next allowed action mismatch")

    leads = registry.get("leads", [])
    normalized_leads = normalized_registry.get("leads", [])
    if len(leads) < 20 or len(normalized_leads) != len(leads):
        errors.append("Seed lead registry does not contain the required normalized lead volume")
    if registry.get("codex_augmented_lead_count", 0) <= 0:
        errors.append("Codex-augmented lead count missing")
    if not all(item.get("lead_is_seed") is False and item.get("helper_provided_sha_trusted") is False for item in normalized_leads):
        errors.append("Lead registry conflates leads with seeds or trusts helper SHAs")

    leakage_records = leakage.get("records", [])
    if len(leakage_records) != len(leads):
        errors.append("Leakage screen does not cover every lead")
    if any(item.get("fix_text_persisted") is True or item.get("repair_decision_time_evidence_uses_issue_body") is True for item in leakage_records):
        errors.append("Issue body leakage screen persisted fix text or used body as repair evidence")

    duplicate_records = duplicates.get("records", [])
    if not any(item.get("lead_id") == "lemon24_reader_355_duplicate_regression_check" and item.get("approval_status") == "rejected_duplicate_or_already_counted" for item in duplicate_records):
        errors.append("lemon24_reader_355 duplicate-sensitive regression check is missing")

    resolution_records = resolution.get("records", [])
    approved = [item for item in resolution_records if item.get("approval_status") == "approved_for_pre_repair_replay_wave"]
    if len(approved) < 5 or len(approved) > 10:
        errors.append("Approved candidate count is outside the required 5-10 range")
    for item in approved:
        if item.get("sha_resolves") is not True or item.get("git_cat_file_e_commit_verified") is not True:
            errors.append(f"approved candidate SHA not independently resolved: {item.get('lead_id')}")
        if item.get("native_test_exists") is not True:
            errors.append(f"approved candidate lacks native test proof: {item.get('lead_id')}")
        if item.get("helper_provided_sha_trusted") is not False:
            errors.append(f"approved candidate trusted helper SHA: {item.get('lead_id')}")
        if item.get("fixed_or_future_evidence_used") is not False or item.get("patch_or_fix_text_used") is not False:
            errors.append(f"approved candidate used forbidden evidence: {item.get('lead_id')}")
    if approvals.get("status") != "PASS" or approvals.get("no_patch_generated") is not True:
        errors.append("Candidate approval gate did not PASS or patch boundary changed")
    for key in ["no_repair_attempt_run", "no_duplicate_replay_run", "no_count_gate_run"]:
        if approvals.get(key) is not True:
            errors.append(f"Batch055 forbidden action boundary failed: {key}")

    planned = plan.get("planned_batch056_candidates", [])
    if plan.get("status") != "PASS" or len(planned) < 3 or len(planned) > 5:
        errors.append("Pre-repair replay wave plan must contain 3-5 planned candidates")
    if results.get("next_allowed_action") != NEXT_ACTION or dashboard.get("planned_batch056_candidates") != len(planned):
        errors.append("Batch055 result/plan next-action mismatch")
    if dashboard.get("issue_derived_repair_count_preserved") != 2 or dashboard.get("native_external_repair_count_preserved") != 4:
        errors.append("Dashboard repair counts changed")
    if dashboard.get("full_scoring") != "NOT_RUN/disallowed" or dashboard.get("memory_lift") != "not_demonstrated":
        errors.append("Dashboard overclaims scoring or memory lift")

    if claim.get("issue_derived_repair_count") != 2 or claim.get("native_external_repair_count") != 4:
        errors.append("Claim boundary repair counts changed")
    if claim.get("batch055_count_increment") is not False:
        errors.append("Batch055 count incremented unexpectedly")
    for field, expected in {
        "full_scoring": "NOT_RUN/disallowed",
        "memory_lift": "not_demonstrated",
        "self_maintaining_software": "false/not_demonstrated",
        "current_protocol": "v2.14",
    }.items():
        if claim.get(field) != expected:
            errors.append(f"Claim boundary mismatch: {field}")

    if package.get("artifact_name") != EXPECTED_ARTIFACT or package.get("status") != "PASS":
        errors.append("Package verification failed")
    if artifact_sha.get("status") != "PENDING_WORKFLOW_ARTIFACT":
        errors.append("Artifact SHA record should remain pending until workflow upload")

    tracked = git_lines("ls-files")
    forbidden_tracked = [
        path for path in tracked
        if path.startswith("incoming_artifacts/")
        or (
            path.startswith("outputs/post_v2_37_hardening_batch055_seed_discovery_wave_1/")
            and (
                path.endswith((".zip", ".tar", ".tar.gz", ".tgz", ".whl", ".pyc", ".pyo"))
                or "/__pycache__/" in path
                or "/.pytest_cache/" in path
                or "/.venv/" in path
                or "/venv/" in path
            )
        )
    ]
    if forbidden_tracked:
        errors.append(f"forbidden tracked payloads: {forbidden_tracked[:5]}")
    staged = git_lines("diff", "--cached", "--name-only")
    if any(path.startswith("incoming_artifacts/") or path.endswith((".zip", ".tar", ".tar.gz", ".tgz")) for path in staged):
        errors.append("incoming artifacts or archives are staged")

    if errors:
        print("FAIL:", errors)
        return 1
    print("Batch055 seed discovery wave 1 audit PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
