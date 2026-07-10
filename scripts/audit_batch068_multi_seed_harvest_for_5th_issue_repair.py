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
from controllergate.core.public_summary import FORBIDDEN_PUBLIC_TERMS, audit_public_summary_text
from controllergate.core.seed_harvest import PARKED_PYTEST_CANDIDATE_ID, REQUIRED_BATCH068_CANDIDATE_FIELDS

OUT_NAME = "post_v2_37_hardening_batch068_multi_seed_harvest_for_5th_issue_repair_with_batch067_063c_063d_063e_controls"
OUT_DIR = ROOT / "outputs" / OUT_NAME

REQUIRED_FILES = [
    "batch063e_artifact_ingestion_summary.json",
    "batch063e_artifact_sha256_verification.json",
    "batch063e_result_preservation.json",
    "batch063e_pytest_parking_preservation.json",
    "batch063e_claim_boundary_preservation.json",
    "pytest_parked_candidate_record_batch068.json",
    "pytest_reopen_condition_registry_batch068.json",
    "pytest_no_generic_loop_policy_batch068.json",
    "batch068_seed_source_policy.json",
    "batch068_seed_harvest_scope.json",
    "batch068_candidate_seed_intake_schema.json",
    "batch068_source_approval_policy.json",
    "batch068_rejected_source_policy.json",
    "candidate_seed_inventory_batch068.json",
    "batch068_source_expansion_inventory.json",
    "batch068_existing_registry_scan.json",
    "batch068_prior_candidate_reuse_exclusion.json",
    "batch068_parked_candidate_exclusion.json",
    "batch068_already_counted_repair_exclusion.json",
    "batch068_probe_only_source_exclusion.json",
    "batch068_external_source_approval_queue.json",
    "batch068_manual_artifact_request_queue.json",
    "candidate_seed_risk_score_schema_batch068.json",
    "candidate_seed_ranking_batch068.json",
    "top_candidate_recommendation_batch068.json",
    "top_5_candidate_recommendations_batch068.json",
    "non_ansible_seed_opportunity_scan_batch068.json",
    "non_ansible_memory_transfer_opportunity_ranking_batch068.json",
    "non_ansible_positive_memory_gap_update_batch068.json",
    "memory_lift_not_demonstrated_preservation_batch068.json",
    "batch069_handoff_plan_batch068.json",
    "batch069_top_seed_contract_batch068.json",
    "batch069_multi_candidate_probe_contract_batch068.json",
    "batch068_final_decision.json",
    "batch068_summary.md",
    "SHA256SUMS.txt",
]


def read_json(name: str) -> Any:
    return json.loads((OUT_DIR / name).read_text(encoding="utf-8"))


def expect(errors: list[str], condition: bool, message: str) -> None:
    if not condition:
        errors.append(message)


def run_check(args: list[str], errors: list[str], label: str) -> None:
    proc = subprocess.run(args, cwd=ROOT, text=True, capture_output=True, check=False)
    expect(errors, proc.returncode == 0, f"{label} failed: {proc.stdout[-1200:]} {proc.stderr[-1200:]}")


def audit_candidate_records(errors: list[str]) -> None:
    inventory = read_json("candidate_seed_inventory_batch068.json")
    records = inventory.get("records", [])
    expect(errors, isinstance(records, list), "candidate inventory records must be a list")
    if not isinstance(records, list):
        return
    expect(errors, len(records) >= 10, f"at least 10 leads required or shortage; found {len(records)}")
    for record in records:
        missing = [field for field in REQUIRED_BATCH068_CANDIDATE_FIELDS if field not in record]
        expect(errors, not missing, f"{record.get('candidate_id')} missing fields {missing}")
        expect(errors, record.get("source_custody_status") is not None, f"{record.get('candidate_id')} missing custody")
        expect(errors, record.get("command_boundary_risk") is not None, f"{record.get('candidate_id')} missing command risk")
        expect(errors, record.get("harness_origin_status") is not None, f"{record.get('candidate_id')} missing harness risk")
        expect(errors, record.get("provider_capsule_risk") is not None, f"{record.get('candidate_id')} missing provider risk")
        expect(errors, record.get("runner_target_risk") is not None, f"{record.get('candidate_id')} missing runner-target risk")
        expect(errors, record.get("promotion_status") is not None, f"{record.get('candidate_id')} missing promotion status")
        active = record.get("promotion_status") in {
            "approved_for_pre_repair_replay_attempt",
            "approved_for_provider_capsule_probe",
            "approved_for_command_boundary_probe",
        }
        if active:
            expect(errors, record.get("already_counted_status") == "not_already_counted", f"already counted candidate promoted: {record.get('candidate_id')}")
            expect(errors, record.get("parked_candidate_status") == "not_parked", f"parked candidate promoted: {record.get('candidate_id')}")
            expect(errors, record.get("probe_only_status") == "not_probe_only", f"probe-only candidate promoted: {record.get('candidate_id')}")
            expect(errors, record.get("gold_fixed_future_exclusion_status") == "PASS", f"forbidden evidence exclusion failed: {record.get('candidate_id')}")
    pytest_records = [record for record in records if record.get("candidate_id") == PARKED_PYTEST_CANDIDATE_ID]
    expect(errors, len(pytest_records) == 1, "Pytest parked candidate record must appear exactly once in inventory")
    if pytest_records:
        expect(errors, pytest_records[0].get("promotion_status") == "parked_with_reopen_condition", "Pytest must be parked, not active")


def audit_public_summary(errors: list[str]) -> None:
    text = (OUT_DIR / "batch068_summary.md").read_text(encoding="utf-8")
    expect(errors, audit_public_summary_text(text).get("status") == "PASS", "Batch068 summary public language audit failed")
    hits = [term for term in FORBIDDEN_PUBLIC_TERMS if term.lower() in text.lower()]
    expect(errors, not hits, f"Batch068 summary contains forbidden public terms: {hits}")


def main() -> int:
    errors: list[str] = []
    expect(errors, OUT_DIR.is_dir(), "missing Batch068 output directory")
    for rel in REQUIRED_FILES:
        expect(errors, (OUT_DIR / rel).is_file(), f"missing Batch068 output {rel}")
    for rel in [
        "controllergate/core/seed_harvest.py",
        "controllergate/core/seed_source_approval.py",
        "controllergate/core/seed_ranking.py",
        "configs/parked_candidate_registry.json",
        "configs/batch068_seed_source_policy.json",
        "configs/batch068_seed_harvest_scope.json",
        "configs/batch068_seed_classification_schema.json",
    ]:
        expect(errors, (ROOT / rel).is_file(), f"missing Batch068 source/config {rel}")
    if errors:
        print("FAIL:")
        for error in errors:
            print(f"- {error}")
        return 1

    manifest = verify_manifest(OUT_DIR)
    expect(errors, manifest.get("status") == "PASS", f"SHA256SUMS failed: {manifest}")
    artifact = read_json("batch063e_artifact_sha256_verification.json")
    expect(errors, artifact.get("status") in {"PASS", "batch063e_artifact_absent_for_local_ingest"}, f"unexpected Batch063e artifact status {artifact.get('status')}")
    if artifact.get("status") == "PASS":
        outer = artifact.get("outer", {})
        entries = artifact.get("entries", {})
        expect(errors, outer.get("size_bytes") == 22474, "Batch063e artifact size mismatch")
        expect(errors, outer.get("sha256") == "5f92bf101cbe6829c0b5be4c7f33512d0203c4e3718f0650a672ebd32c3d3026", "Batch063e artifact SHA mismatch")
        expect(errors, entries.get("unsafe_path_count") == 0, "Batch063e unsafe artifact paths")
        expect(errors, entries.get("duplicate_path_count") == 0, "Batch063e duplicate artifact paths")
        expect(errors, artifact.get("nested_archive_cache_venv_pyc_payload_count") == 0, "Batch063e nested/cache payloads")
        for manifest_name, result in artifact.get("manifests", {}).items():
            expect(errors, result.get("status") == "PASS", f"Batch063e artifact manifest failed: {manifest_name}")

    pytest_record = read_json("pytest_parked_candidate_record_batch068.json")
    expect(errors, pytest_record.get("candidate_id") == PARKED_PYTEST_CANDIDATE_ID, "wrong parked candidate")
    expect(errors, pytest_record.get("generic_followup_forbidden") is True, "Pytest generic follow-up not forbidden")
    expect(errors, pytest_record.get("specific_evidence_required") is True, "Pytest reopen evidence not required")
    expect(errors, pytest_record.get("patch_generated") is False, "Pytest patch generated")
    expect(errors, pytest_record.get("count_increment") is False, "Pytest count incremented")

    audit_candidate_records(errors)
    top5 = read_json("top_5_candidate_recommendations_batch068.json")
    top_records = top5.get("records", [])
    expect(errors, isinstance(top_records, list), "top 5 recommendations must be a list")
    expect(errors, len(top_records) >= 5 or top5.get("status") == "SHORTAGE", "top 5 recommendations missing without shortage")
    for item in top_records:
        expect(errors, item.get("candidate_id") != PARKED_PYTEST_CANDIDATE_ID, "Pytest appeared in top recommendations")

    non_ansible = read_json("non_ansible_seed_opportunity_scan_batch068.json")
    expect(errors, non_ansible.get("status") == "PASS", "non-Ansible opportunity scan missing")
    final = read_json("batch068_final_decision.json")
    expect(errors, final.get("status") == "PASS", "final status not PASS")
    expect(errors, final.get("batch068_audit_status") == "PASS", "final audit status not PASS")
    expect(errors, final.get("current_protocol") == "v2.14", "current protocol changed")
    expect(errors, final.get("issue_derived_repair_count") == 4, "issue-derived count changed")
    expect(errors, final.get("native_external_repair_count") == 4, "native external count changed")
    for key in ["patch_generated", "patch_applied", "duplicate_replay_run", "count_gate_run", "repair_count_increment"]:
        expect(errors, final.get(key) is False, f"{key} should remain false")
    expect(errors, final.get("full_scoring") == "NOT_RUN/disallowed", "full scoring changed")
    expect(errors, final.get("memory_lift") == "not_demonstrated", "memory lift changed")
    expect(errors, final.get("self_maintaining_software") == "false/not_demonstrated", "self-maintaining status changed")
    expect(errors, final.get("seed_inventory_count", 0) >= 10, "seed inventory too small")
    expect(errors, final.get("approved_seed_count", 0) >= 5, "fewer than five approved non-parked/non-counted seed leads")
    expect(errors, final.get("next_allowed_action") in {
        "batch069_top_seed_pre_repair_replay_and_patch_license_gate",
        "batch069_multi_candidate_provider_command_probe",
        "batch068b_manual_artifact_and_external_source_custody_intake",
        "batch068b_source_expansion_registry_buildout",
        "batch063f_pytest_runner_target_specific_evidence_intake",
    }, "invalid next allowed action")
    audit_public_summary(errors)

    run_check([sys.executable, "scripts/audit_batch063e_pytest_runner_target_split_evidence_intake.py"], errors, "Batch063e audit")
    run_check([sys.executable, "scripts/audit_batch063d_pytest_safe_tag_acquisition_hardening.py"], errors, "Batch063d audit")
    run_check([sys.executable, "scripts/audit_batch063c_pytest_command_boundary_followup.py"], errors, "Batch063c audit")
    run_check([sys.executable, "scripts/audit_batch067_universal_wrapper_hardening_implementation.py"], errors, "Batch067 audit")
    run_check([sys.executable, "scripts/controllergate_audit.py", "--protocol", "current"], errors, "current protocol audit")
    run_check([sys.executable, "scripts/controllergate_run.py", "--protocol", "current", "--dry-run"], errors, "current protocol dry-run")

    if errors:
        print("FAIL:")
        for error in errors:
            print(f"- {error}")
        return 1
    print("Batch068 multi-seed harvest audit PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
