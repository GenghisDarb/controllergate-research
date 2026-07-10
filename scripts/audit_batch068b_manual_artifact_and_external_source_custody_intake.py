from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from controllergate.core.manual_artifact_intake import REQUIRED_NATIVE_COMMAND_ARTIFACT_FIELDS
from controllergate.core.manifests import verify_manifest
from controllergate.core.public_summary import FORBIDDEN_PUBLIC_TERMS, audit_public_summary_text
from controllergate.core.runtime_connector_intake import validate_runtime_connector_request

OUT_NAME = "post_v2_37_hardening_batch068b_manual_artifact_and_external_source_custody_intake"
OUT_DIR = ROOT / "outputs" / OUT_NAME

MANUAL_REQUEST_FILES = [
    "manual_artifact_requests/aiosmtpd_native_command_artifact_request_batch068b.json",
    "manual_artifact_requests/streamflow_native_command_artifact_request_batch068b.json",
    "manual_artifact_requests/biface_i18n_native_command_artifact_request_batch068b.json",
]

REQUIRED_TOP_FILES = [
    "batch069b_artifact_ingestion_summary.json",
    "batch069b_artifact_sha256_verification.json",
    "batch069b_result_preservation.json",
    "batch069b_manual_artifact_queue_preservation.json",
    "batch069b_runtime_connector_queue_preservation.json",
    "batch069b_claim_boundary_preservation.json",
    "manual_artifact_intake_schema_batch068b.json",
    "native_command_artifact_policy_batch068b.json",
    "external_source_custody_policy_batch068b.json",
    "manual_artifact_submission_manifest_template_batch068b.json",
    "native_target_command_artifact_template_batch068b.json",
    "runtime_connector_intake_schema_batch068b.json",
    "aws_neuron_nki_runtime_connector_request_batch068b.json",
    "runtime_connector_security_license_review_batch068b.json",
    "runtime_connector_approval_gate_batch068b.json",
    "incoming_artifact_quarantine_policy_batch068b.json",
    "manual_artifact_approval_workflow_batch068b.json",
    "manual_artifact_rejection_policy_batch068b.json",
    "approved_manual_artifact_registry_batch068b.json",
    "rejected_manual_artifact_registry_batch068b.json",
    "incoming_manual_artifact_scan_batch068b.json",
    "incoming_manual_artifact_approval_results_batch068b.json",
    "external_source_approval_queue_batch068b.json",
    "external_source_approval_schema_batch068b.json",
    "external_source_decision_time_safety_policy_batch068b.json",
    "seed_product_readiness_registry_batch068b.json",
    "seed_reopen_condition_registry_batch068b.json",
    "batch068b_seed_readiness_delta.json",
    "manual_artifact_readiness_backlog_batch068b.json",
    "runtime_connector_readiness_backlog_batch068b.json",
    "universal_interlock_law_manifest_batch068b.json",
    "step_to_output_contract_registry_batch068b.json",
    "failed_attempt_branch_record_registry_batch068b.json",
    "cross_environment_orthology_map_batch068b.json",
    "ast_topology_extrusion_map_batch068b.json",
    "elbow_patch_authorization_gate_batch068b.json",
    "reward_signal_memory_boundary_batch068b.json",
    "batch068b_handoff_plan.json",
    "batch068b_final_decision.json",
    "batch068b_summary.md",
    "SHA256SUMS.txt",
]


def read_json(path: str | Path) -> Any:
    target = OUT_DIR / path if isinstance(path, str) else path
    return json.loads(target.read_text(encoding="utf-8"))


def expect(errors: list[str], condition: bool, message: str) -> None:
    if not condition:
        errors.append(message)


def run_check(args: list[str], errors: list[str], label: str) -> None:
    proc = subprocess.run(args, cwd=ROOT, text=True, capture_output=True, check=False)
    expect(errors, proc.returncode == 0, f"{label} failed: {proc.stdout[-1200:]} {proc.stderr[-1200:]}")


def audit_artifact_preservation(errors: list[str]) -> None:
    artifact = read_json("batch069b_artifact_sha256_verification.json")
    expect(errors, artifact.get("status") in {"PASS", "batch069b_artifact_absent_for_local_ingest"}, f"unexpected Batch069b artifact status {artifact.get('status')}")
    if artifact.get("status") == "PASS":
        outer = artifact.get("outer", {})
        entries = artifact.get("entries", {})
        expect(errors, outer.get("size_bytes") == 116091, "Batch069b artifact size mismatch")
        expect(errors, outer.get("sha256") == "c0af433545919c4233085ff3728e98d06fe2279d572d312ec25c068f57048089", "Batch069b artifact SHA mismatch")
        expect(errors, entries.get("unsafe_path_count") == 0, "Batch069b artifact unsafe paths")
        expect(errors, entries.get("duplicate_path_count") == 0, "Batch069b artifact duplicate paths")
        expect(errors, artifact.get("nested_archive_cache_venv_pyc_payload_count") == 0, "Batch069b nested/cache payloads")
        for name, result in artifact.get("manifests", {}).items():
            expect(errors, result.get("status") == "PASS", f"Batch069b artifact manifest failed: {name}")
    preservation = read_json("batch069b_result_preservation.json")
    expect(errors, preservation.get("status") == "PASS", "Batch069b result preservation missing")


def audit_request_packets(errors: list[str]) -> None:
    schema = read_json("manual_artifact_intake_schema_batch068b.json")
    expect(errors, schema.get("required_fields") == REQUIRED_NATIVE_COMMAND_ARTIFACT_FIELDS, "manual artifact schema fields changed")
    for rel in MANUAL_REQUEST_FILES:
        packet = read_json(rel)
        expect(errors, packet.get("status") == "PASS", f"{rel} status not PASS")
        for field in [
            "candidate_id",
            "repo_url",
            "issue_url",
            "candidate_sha",
            "exact_blocker",
            "reopen_condition",
            "minimum_safe_artifact_needed",
            "forbidden_artifact_contents",
            "hash_requirements",
            "provenance_requirements",
            "approval_test",
            "next_action_after_approval",
        ]:
            expect(errors, field in packet, f"{rel} missing {field}")
        forbidden = " ".join(packet.get("forbidden_artifact_contents", []))
        expect(errors, "future" in forbidden and "gold" in forbidden and "fixed" in forbidden, f"{rel} missing forbidden evidence exclusions")
        expect(errors, packet.get("next_action_after_approval") == "batch069c_manual_artifact_command_replay_followup", f"{rel} wrong post-approval action")


def audit_runtime_connector(errors: list[str]) -> None:
    request = read_json("aws_neuron_nki_runtime_connector_request_batch068b.json")
    expect(errors, validate_runtime_connector_request(request).get("status") == "PASS", "NKI runtime connector request invalid")
    gate = read_json("runtime_connector_approval_gate_batch068b.json")
    expect(errors, gate.get("approved_runtime_connector_count") == 0, "runtime connector unexpectedly approved")
    expect(errors, gate.get("status") == "BLOCK", "runtime connector gate should remain blocked without connector artifact")


def audit_quarantine(errors: list[str]) -> None:
    policy = read_json("incoming_artifact_quarantine_policy_batch068b.json")
    expect(errors, policy.get("raw_incoming_artifact_commit_allowed") is False, "raw incoming artifact commits allowed")
    scan = read_json("incoming_manual_artifact_scan_batch068b.json")
    for record in scan.get("records", []):
        expect(errors, record.get("raw_artifact_committed") is False, f"{record.get('relative_path')} raw artifact committed")
        expect(errors, record.get("classification") != "approved_for_command_boundary_recovery", f"{record.get('relative_path')} unexpectedly approved for command recovery")
    approvals = read_json("approved_manual_artifact_registry_batch068b.json")
    expect(errors, approvals.get("approved_count") == 0, "manual artifacts unexpectedly approved")
    rejected = read_json("rejected_manual_artifact_registry_batch068b.json")
    expect(errors, rejected.get("rejected_count") == scan.get("incoming_artifact_count"), "incoming artifacts were not all rejected/quarantined for this lane")
    proc = subprocess.run(["git", "ls-files", "incoming_artifacts"], cwd=ROOT, text=True, capture_output=True, check=False)
    expect(errors, proc.returncode == 0, "git ls-files incoming_artifacts failed")
    expect(errors, proc.stdout.strip() == "", "incoming_artifacts has tracked files")


def audit_seed_and_interlocks(errors: list[str]) -> None:
    seed = read_json("seed_product_readiness_registry_batch068b.json")
    expect(errors, seed.get("status") == "PASS", "seed product readiness status not PASS")
    expect(errors, seed.get("total_seed_count", 0) >= 90, "seed product readiness lost seed coverage")
    expect(errors, seed.get("unapproved_without_reason_count") == 0, "unapproved seed without reason")
    statuses = {item.get("candidate_id"): item.get("batch068b_readiness_status") for item in seed.get("records", [])}
    expect(errors, statuses.get("codex_wave3_aio_libs_aiosmtpd_issues_403") == "manual_artifact_request_emitted", "aiosmtpd readiness not updated")
    expect(errors, statuses.get("codex_wave3_alpha_unito_streamflow_issues_1100") == "manual_artifact_request_emitted", "streamflow readiness not updated")
    expect(errors, statuses.get("codex_wave3_biface_i18n_issues_86") == "manual_artifact_request_emitted", "biface readiness not updated")
    expect(errors, statuses.get("codex_wave3_aws_neuron_nki_library_issues_5") == "runtime_connector_request_emitted", "NKI readiness not updated")
    for rel in [
        "universal_interlock_law_manifest_batch068b.json",
        "step_to_output_contract_registry_batch068b.json",
        "failed_attempt_branch_record_registry_batch068b.json",
        "cross_environment_orthology_map_batch068b.json",
        "ast_topology_extrusion_map_batch068b.json",
        "reward_signal_memory_boundary_batch068b.json",
    ]:
        value = read_json(rel)
        expect(errors, value.get("status") == "PASS", f"{rel} not PASS")
        expect(errors, value.get("batch068b_audit_status") == "PASS", f"{rel} not marked preserved for Batch068b")
    elbow = read_json("elbow_patch_authorization_gate_batch068b.json")
    expect(errors, elbow.get("patch_generation_allowed") is False, "elbow gate allowed patch generation")


def audit_final(errors: list[str]) -> None:
    final = read_json("batch068b_final_decision.json")
    expect(errors, final.get("status") == "PASS", "final status not PASS")
    expect(errors, final.get("batch068b_audit_status") == "PASS", "Batch068b audit status not PASS")
    expect(errors, final.get("current_protocol") == "v2.14", "current protocol changed")
    expect(errors, final.get("issue_derived_repair_count") == 4, "issue-derived repair count changed")
    expect(errors, final.get("native_external_repair_count") == 4, "native external repair count changed")
    for key in [
        "patch_generated",
        "patch_applied",
        "source_mutated",
        "tests_mutated",
        "fixtures_mutated",
        "config_mutated",
        "duplicate_replay_run",
        "count_gate_run",
        "repair_count_increment",
    ]:
        expect(errors, final.get(key) is False, f"{key} must remain false")
    expect(errors, final.get("manual_artifact_request_count") == 3, "manual artifact request count mismatch")
    expect(errors, final.get("runtime_connector_request_count") == 1, "runtime connector request count mismatch")
    expect(errors, final.get("approved_manual_artifact_count") == 0, "manual artifacts unexpectedly approved")
    expect(errors, final.get("approved_native_command_artifact_count") == 0, "native command artifacts unexpectedly approved")
    expect(errors, final.get("approved_runtime_connector_count") == 0, "runtime connector unexpectedly approved")
    expect(errors, final.get("full_scoring") == "NOT_RUN/disallowed", "full scoring changed")
    expect(errors, final.get("memory_lift") == "not_demonstrated", "memory lift changed")
    expect(errors, final.get("self_maintaining_software") == "false/not_demonstrated", "self-maintaining status changed")
    expect(errors, final.get("next_allowed_action") == "batch068b_waiting_for_manual_artifacts_or_source_expansion", "unexpected next allowed action")


def audit_public_summary(errors: list[str]) -> None:
    text = (OUT_DIR / "batch068b_summary.md").read_text(encoding="utf-8")
    expect(errors, audit_public_summary_text(text).get("status") == "PASS", "public summary failed neutral language audit")
    hits = [term for term in FORBIDDEN_PUBLIC_TERMS if term.lower() in text.lower()]
    expect(errors, not hits, f"public summary contains forbidden terms: {hits}")
    expect(errors, "not repair proof" in text, "public summary must state not repair proof")


def main() -> int:
    errors: list[str] = []
    expect(errors, OUT_DIR.is_dir(), "missing Batch068b output directory")
    for rel in REQUIRED_TOP_FILES + MANUAL_REQUEST_FILES:
        expect(errors, (OUT_DIR / rel).is_file(), f"missing output {rel}")
    for rel in [
        "controllergate/core/manual_artifact_intake.py",
        "controllergate/core/runtime_connector_intake.py",
        "controllergate/core/intake_quarantine.py",
        "controllergate/core/external_source_approval.py",
        "configs/manual_artifact_intake_schema.json",
        "configs/native_command_artifact_policy.json",
        "configs/external_source_custody_policy.json",
        "configs/runtime_connector_intake_schema.json",
        "configs/aws_neuron_nki_connector_policy.json",
        "scripts/generate_batch068b_manual_artifact_and_external_source_custody_intake.py",
        "scripts/audit_batch068b_manual_artifact_and_external_source_custody_intake.py",
        ".github/workflows/post_v2_37_hardening_batch068b_manual_artifact_and_external_source_custody_intake.yml",
    ]:
        expect(errors, (ROOT / rel).is_file(), f"missing implementation/config {rel}")
    if errors:
        print("FAIL:")
        for error in errors:
            print(f"- {error}")
        return 1
    manifest = verify_manifest(OUT_DIR)
    expect(errors, manifest.get("status") == "PASS", f"SHA256SUMS failed: {manifest}")
    audit_artifact_preservation(errors)
    audit_request_packets(errors)
    audit_runtime_connector(errors)
    audit_quarantine(errors)
    audit_seed_and_interlocks(errors)
    audit_final(errors)
    audit_public_summary(errors)

    run_check([sys.executable, "scripts/controllergate_audit.py", "--protocol", "current"], errors, "current protocol audit")
    run_check([sys.executable, "scripts/controllergate_run.py", "--protocol", "current", "--dry-run"], errors, "current protocol dry-run")
    if errors:
        print("FAIL:")
        for error in errors:
            print(f"- {error}")
        return 1
    print("Batch068b manual artifact and external source custody intake audit PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
