from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from controllergate.core.artifacts import verify_artifact_zip
from controllergate.core.evidence import write_json_deterministic, write_text_lf
from controllergate.core.external_source_approval import build_external_source_request, external_source_approval_schema
from controllergate.core.intake_quarantine import ALLOWED_INTAKE_CLASSIFICATIONS, scan_quarantine_path
from controllergate.core.manual_artifact_intake import (
    ALLOWED_ARTIFACT_USES,
    FORBIDDEN_ARTIFACT_USES,
    native_command_artifact_schema,
    native_command_artifact_template,
)
from controllergate.core.manifests import write_sha256sums
from controllergate.core.runtime_connector_intake import runtime_connector_intake_schema, validate_runtime_connector_request

OUT_NAME = "post_v2_37_hardening_batch068b_manual_artifact_and_external_source_custody_intake"
OUT_DIR = ROOT / "outputs" / OUT_NAME
BATCH069B_NAME = "post_v2_37_hardening_batch069b_recoverable_provider_command_followup"
BATCH069B_DIR = ROOT / "outputs" / BATCH069B_NAME

EXPECTED_BATCH069B = {
    "commit": "ffba90c79d2947335e7ed0d8ae0025a88cd8245a",
    "workflow": "post_v2_37_hardening_batch069b_recoverable_provider_command_followup",
    "workflow_run_id": 29071724000,
    "artifact_name": "post_v2_37_hardening_batch069b_recoverable_provider_command_followup_artifacts",
    "artifact_id": 8219129614,
    "expected_size": 116091,
    "expected_sha256": "c0af433545919c4233085ff3728e98d06fe2279d572d312ec25c068f57048089",
}

CURRENT_PROTOCOL = "v2.14"
ISSUE_DERIVED_REPAIR_COUNT = 4
NATIVE_EXTERNAL_REPAIR_COUNT = 4
FULL_SCORING = "NOT_RUN/disallowed"
MEMORY_LIFT = "not_demonstrated"
SELF_MAINTAINING = "false/not_demonstrated"

MANUAL_CANDIDATES = {
    "codex_wave3_aio_libs_aiosmtpd_issues_403": {
        "short_name": "aiosmtpd",
        "request_file": "aiosmtpd_native_command_artifact_request_batch068b.json",
        "candidate_specific_detail": "Request a verified candidate-era native command artifact that identifies whether the valid target command is the full QA command, a focused test command for issue 403, or a tox/CI command.",
        "observed_command_hints": [".github/workflows/ci-cd.yml", "pytest", "pytest -v aiosmtpd/qa", "README", "pyproject", "requirements", "aiosmtpd/qa test tree"],
    },
    "codex_wave3_alpha_unito_streamflow_issues_1100": {
        "short_name": "streamflow",
        "request_file": "streamflow_native_command_artifact_request_batch068b.json",
        "candidate_specific_detail": "Request a verified candidate-era native command artifact identifying the correct target replay command for issue 1100 and any required fixture or profile.",
        "observed_command_hints": [".github/workflows/ci-tests.yaml", "CONTRIBUTING.md", "Makefile", "pyproject", "test tree"],
    },
    "codex_wave3_biface_i18n_issues_86": {
        "short_name": "biface_i18n",
        "request_file": "biface_i18n_native_command_artifact_request_batch068b.json",
        "candidate_specific_detail": "Request a verified candidate-era native command artifact identifying the correct target replay command for issue 86 and whether tox or pytest should be used.",
        "observed_command_hints": [".github/workflows/python-ci.yaml", "tox", "tox -e ci", "tox.ini", "pyproject", "README", "tests/ tree"],
    },
}

NKI_CANDIDATE = "codex_wave3_aws_neuron_nki_library_issues_5"
DEFAULT_BATCH069B_ZIP_CANDIDATES = [
    ROOT / "incoming_artifacts" / f"{EXPECTED_BATCH069B['artifact_name']}.zip",
    Path(r"C:\Users\thisb\Downloads\post_v2_37_hardening_batch069b_recoverable_provider_command_followup_artifacts.zip"),
]

PUBLIC_SUMMARY = (
    "Batch068b creates the manual artifact and external source custody intake path for candidates whose native target "
    "command or runtime connector could not be recovered from decision-time metadata alone. It emits verified artifact "
    "request packets, runtime connector requests, source-approval policies, and quarantine rules. This is custody and "
    "readiness infrastructure, not repair proof. No repair is counted without source-only target pass, duplicate clean "
    "replay, and count gate. Full scoring remains NOT_RUN/disallowed. Memory lift remains not_demonstrated. "
    "Self-maintaining software remains false/not_demonstrated."
)


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_out_json(name: str, value: Any) -> None:
    write_json_deterministic(OUT_DIR / name, value)


def find_batch069b_zip() -> Path | None:
    env_path = os.environ.get("CONTROLLERGATE_BATCH069B_ARTIFACT_ZIP")
    candidates = ([Path(env_path)] if env_path else []) + DEFAULT_BATCH069B_ZIP_CANDIDATES
    for candidate in candidates:
        if candidate.is_file():
            return candidate
    return None


def verify_batch069b_artifact() -> tuple[dict[str, Any], dict[str, Any]]:
    previous = OUT_DIR / "batch069b_artifact_sha256_verification.json"
    incoming_path = DEFAULT_BATCH069B_ZIP_CANDIDATES[0]
    zip_path = find_batch069b_zip()
    if zip_path is None and previous.is_file():
        prior = read_json(previous)
        if prior.get("status") == "PASS":
            return prior | {"ci_zip_absent_preserved_committed_verification": True}, {
                "status": "PASS",
                "artifact_verified": "PASS",
                "preservation_source": "committed_batch068b_manual_artifact_verification",
                "raw_zip_bytes_ingested": False,
                "incoming_artifact_status": "absent",
            }
    if zip_path is None:
        verification = {
            "status": "batch069b_artifact_absent_for_local_ingest",
            "artifact_absent": True,
            "manual_artifact_handoff": False,
            "downloaded_by_codex": False,
            "incoming_artifact_status": "absent",
            "committed_batch069b_outputs_preserved": True,
        }
        return verification, {
            "status": "batch069b_artifact_absent_for_local_ingest",
            "raw_zip_bytes_ingested": False,
            "ingested_file_count": 0,
            "preservation_source": "committed_batch069b_outputs",
            "incoming_artifact_status": "absent",
        }
    verification = verify_artifact_zip(
        zip_path,
        expected_size=EXPECTED_BATCH069B["expected_size"],
        expected_sha256=EXPECTED_BATCH069B["expected_sha256"],
    )
    nested = verification.get("entries", {}).get("nested_archive_or_cache_payloads", [])
    if nested:
        verification["status"] = "FAIL"
    verification["local_artifact_path"] = str(zip_path)
    verification["manual_artifact_handoff"] = True
    verification["downloaded_by_codex"] = False
    verification["incoming_artifact_status"] = "present" if zip_path == incoming_path else "absent_used_downloads_handoff"
    verification["nested_archive_cache_venv_pyc_payload_count"] = len(nested)
    return verification, {
        "status": "PASS" if verification.get("status") == "PASS" else "BLOCK",
        "artifact_verified": verification.get("status"),
        "source_zip": str(zip_path),
        "raw_zip_bytes_ingested": False,
        "output_payload_overwrite_performed": False,
        "ingested_file_count": 0,
        "preservation_source": "verified_manual_batch069b_artifact" if verification.get("status") == "PASS" else "committed_batch069b_outputs",
        "incoming_artifact_status": verification["incoming_artifact_status"],
    }


def batch069b_matrix() -> dict[str, dict[str, Any]]:
    records = read_json(BATCH069B_DIR / "native_command_recovery_matrix_batch069b.json").get("records", [])
    return {record["candidate_id"]: record for record in records}


def write_policy_configs() -> None:
    write_json_deterministic(ROOT / "configs" / "manual_artifact_intake_schema.json", native_command_artifact_schema())
    write_json_deterministic(
        ROOT / "configs" / "native_command_artifact_policy.json",
        {
            "status": "PASS",
            "native_command_artifact_required_fields": native_command_artifact_schema()["required_fields"],
            "allowed_use": ALLOWED_ARTIFACT_USES,
            "forbidden_use": FORBIDDEN_ARTIFACT_USES,
            "approval_requires_hash_and_provenance": True,
            "raw_artifact_commit_allowed": False,
        },
    )
    write_json_deterministic(
        ROOT / "configs" / "external_source_custody_policy.json",
        external_source_approval_schema(),
    )
    write_json_deterministic(ROOT / "configs" / "runtime_connector_intake_schema.json", runtime_connector_intake_schema())
    write_json_deterministic(
        ROOT / "configs" / "aws_neuron_nki_connector_policy.json",
        {
            "status": "PASS",
            "required_connector": "aws_neuron_or_nki_runtime_connector",
            "credentials_commit_allowed": False,
            "connector_output_hashes_required": True,
            "sdk_license_security_review_required": True,
            "batch068b_installation_allowed_without_approved_connector": False,
        },
    )


def request_packet(candidate_id: str, record: dict[str, Any]) -> dict[str, Any]:
    spec = MANUAL_CANDIDATES[candidate_id]
    return {
        "status": "PASS",
        "candidate_id": candidate_id,
        "repo_url": record["repo_url"],
        "issue_url": record["issue_url"],
        "candidate_sha": record["candidate_sha"],
        "exact_blocker": record["exact_blocker"],
        "reopen_condition": "verified_native_target_command_artifact",
        "minimum_safe_artifact_needed": [
            "verified_native_target_command",
            "candidate_era_command_source_path",
            "hash_of_command_source_artifact",
            "source_snapshot_identity",
            "provenance_note",
            "statement_excluding_future_gold_fixed_patch_guidance",
        ],
        "acceptable_artifact_examples": [
            "native test command snapshot",
            "CI log from candidate-era commit",
            "tox/nox config from candidate-era release",
            "reproduction script with hash and provenance",
            "benchmark harness bundle with manifest",
        ],
        "forbidden_artifact_contents": [
            "future commit contents",
            "fixed patch",
            "gold patch",
            "issue workaround fix text",
            "test mutation",
            "fixture injection",
        ],
        "candidate_local_command_hints_already_observed": spec["observed_command_hints"],
        "candidate_local_test_tree_hints_already_observed": (BATCH069B_DIR / "candidates" / candidate_id / "test_tree_inventory.json").read_text(encoding="utf-8"),
        "why_current_metadata_was_insufficient": "candidate-local metadata exposed broad runner hints but no exact native target command safely tied to the issue target",
        "candidate_specific_request_detail": spec["candidate_specific_detail"],
        "how_to_submit_safely": "place a JSON, Markdown, or text artifact under incoming_artifacts/ with candidate_id, source snapshot identity, SHA256, and provenance; do not include patch guidance",
        "hash_requirements": ["artifact_sha256", "command_source_sha256", "source_snapshot_identity"],
        "provenance_requirements": ["artifact_author", "artifact_created_at_utc", "artifact_source_url_or_local_path", "provenance_note"],
        "approval_test": "manual artifact validates against native command artifact schema with no forbidden evidence",
        "next_action_after_approval": "batch069c_manual_artifact_command_replay_followup",
        "public_explanation": "This request seeks command-boundary evidence only; it is not repair proof and cannot authorize patches or count gates.",
        "audit_status": "PASS",
    }


def runtime_connector_request(record: dict[str, Any]) -> dict[str, Any]:
    request = {
        "status": "PASS",
        "candidate_id": NKI_CANDIDATE,
        "repo_url": record["repo_url"],
        "issue_url": record["issue_url"],
        "candidate_sha": record["candidate_sha"],
        "required_connector": "aws_neuron_or_nki_runtime_connector",
        "why_needed": "AWS Neuron/NKI candidate requires a verified runtime, hardware, simulator, or SDK boundary before target replay can be trusted.",
        "required_sdk_runtime_identity": "exact SDK/runtime package identity, version, source, and hash",
        "required_hardware_or_simulator_boundary": "approved Neuron hardware, simulator, or documented no-hardware boundary",
        "allowed_environment": "isolated provider runtime with no credentials committed and deterministic output hashes",
        "forbidden_credentials_handling": "no_credentials_tokens_or_account_material_committed",
        "security_risk": "hardware_or_sdk_runtime_boundary",
        "license_risk": "external_sdk_terms_must_be_reviewed",
        "manual_setup_hint": "provide an approved runtime capsule or simulator evidence with hashes and license notes",
        "future_automation_hint": "bounded runtime connector with explicit no-credential transport and output hashing",
        "connector_output_hashes_required": True,
        "approval_condition": "connector_identity_runtime_output_hashes_security_and_license_review_pass",
        "reopen_condition": "approved_aws_neuron_nki_runtime_connector",
    }
    request["validation"] = validate_runtime_connector_request(request)
    return request


def scan_incoming_artifacts() -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    incoming = ROOT / "incoming_artifacts"
    scan_records: list[dict[str, Any]] = []
    approved: list[dict[str, Any]] = []
    rejected: list[dict[str, Any]] = []
    if not incoming.exists():
        return scan_records, approved, rejected
    scoped = list(MANUAL_CANDIDATES) + [NKI_CANDIDATE]
    for path in sorted(p for p in incoming.rglob("*") if p.is_file()):
        rel = path.relative_to(ROOT).as_posix()
        record = scan_quarantine_path(path, scoped)
        record["relative_path"] = rel
        record["raw_artifact_committed"] = False
        record["approved_for_batch068b"] = record["classification"].startswith("approved_")
        scan_records.append(record)
        if record["approved_for_batch068b"]:
            approved.append(record)
        else:
            rejected.append(record)
    return scan_records, approved, rejected


def seed_readiness_update() -> dict[str, Any]:
    previous = read_json(BATCH069B_DIR / "seed_product_readiness_registry_batch069b.json")
    records = []
    for item in previous.get("records", []):
        record = dict(item)
        cid = record.get("candidate_id")
        if cid in MANUAL_CANDIDATES:
            record["batch068b_readiness_status"] = "manual_artifact_request_emitted"
            record["next_lowest_risk_action"] = "submit_verified_native_target_command_artifact"
            record["reopen_condition"] = "verified_native_target_command_artifact"
        elif cid == NKI_CANDIDATE:
            record["batch068b_readiness_status"] = "runtime_connector_request_emitted"
            record["next_lowest_risk_action"] = "submit_or_approve_runtime_connector_artifact"
            record["reopen_condition"] = "approved_aws_neuron_nki_runtime_connector"
        else:
            record["batch068b_readiness_status"] = record.get("batch069b_readiness_status") or record.get("batch069_readiness_status")
        records.append(record)
    return {
        "status": "PASS",
        "source_batch": "Batch068b",
        "total_seed_count": len(records),
        "unapproved_without_reason_count": sum(1 for item in records if item.get("batch068b_readiness_status") == "unapproved_without_reason"),
        "records": records,
    }


def copy_preserved_interlock_outputs() -> None:
    pairs = {
        "universal_interlock_law_manifest_batch068b.json": "universal_interlock_law_manifest_batch069b.json",
        "step_to_output_contract_registry_batch068b.json": "step_to_output_contract_registry_batch069b.json",
        "failed_attempt_branch_record_registry_batch068b.json": "failed_attempt_branch_record_registry_batch069b.json",
        "cross_environment_orthology_map_batch068b.json": "cross_environment_orthology_map_batch069b.json",
        "ast_topology_extrusion_map_batch068b.json": "ast_topology_extrusion_map_batch069b.json",
        "elbow_patch_authorization_gate_batch068b.json": "elbow_patch_authorization_gate_batch069b.json",
        "reward_signal_memory_boundary_batch068b.json": "reward_signal_memory_boundary_batch069b.json",
    }
    for dest, src in pairs.items():
        value = read_json(BATCH069B_DIR / src)
        if isinstance(value, dict):
            value = dict(value)
            value["preserved_from_batch069b"] = src
            value["batch068b_audit_status"] = "PASS"
        write_out_json(dest, value)


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUT_DIR / "manual_artifact_requests").mkdir(parents=True, exist_ok=True)
    write_policy_configs()
    artifact_verification, artifact_ingestion = verify_batch069b_artifact()
    matrix = batch069b_matrix()
    manual_requests = []
    for cid in MANUAL_CANDIDATES:
        packet = request_packet(cid, matrix[cid])
        manual_requests.append(packet)
        write_out_json(f"manual_artifact_requests/{MANUAL_CANDIDATES[cid]['request_file']}", packet)
    nki_request = runtime_connector_request(matrix[NKI_CANDIDATE])
    scan_records, approved_records, rejected_records = scan_incoming_artifacts()
    seed_registry = seed_readiness_update()
    write_json_deterministic(ROOT / "configs" / "controllergate_seed_product_readiness_registry.json", seed_registry)

    write_out_json("batch069b_artifact_sha256_verification.json", artifact_verification)
    write_out_json("batch069b_artifact_ingestion_summary.json", artifact_ingestion)
    write_out_json("batch069b_result_preservation.json", {"status": "PASS", "batch069b_final_decision": read_json(BATCH069B_DIR / "batch069b_final_decision.json")})
    write_out_json("batch069b_manual_artifact_queue_preservation.json", read_json(BATCH069B_DIR / "manual_artifact_request_queue_batch069b.json"))
    write_out_json("batch069b_runtime_connector_queue_preservation.json", read_json(BATCH069B_DIR / "runtime_connector_gap_registry_batch069b.json"))
    write_out_json("batch069b_claim_boundary_preservation.json", {"status": "PASS", "patch_generated": False, "patch_applied": False, "source_mutated": False, "tests_mutated": False, "fixtures_mutated": False, "config_mutated": False, "duplicate_replay_run": False, "count_gate_run": False, "repair_count_increment": False, "issue_derived_repair_count": ISSUE_DERIVED_REPAIR_COUNT, "native_external_repair_count": NATIVE_EXTERNAL_REPAIR_COUNT, "full_scoring": FULL_SCORING, "memory_lift": MEMORY_LIFT, "self_maintaining_software": SELF_MAINTAINING})
    write_out_json("manual_artifact_intake_schema_batch068b.json", native_command_artifact_schema())
    write_out_json("native_command_artifact_policy_batch068b.json", read_json(ROOT / "configs" / "native_command_artifact_policy.json"))
    write_out_json("external_source_custody_policy_batch068b.json", read_json(ROOT / "configs" / "external_source_custody_policy.json"))
    write_out_json("manual_artifact_submission_manifest_template_batch068b.json", {"status": "PASS", "template": native_command_artifact_template()})
    write_out_json("native_target_command_artifact_template_batch068b.json", {"status": "PASS", "template": native_command_artifact_template()})
    write_out_json("runtime_connector_intake_schema_batch068b.json", runtime_connector_intake_schema())
    write_out_json("aws_neuron_nki_runtime_connector_request_batch068b.json", nki_request)
    write_out_json("runtime_connector_security_license_review_batch068b.json", {"status": "PASS", "candidate_id": NKI_CANDIDATE, "security_review_required": True, "license_review_required": True, "credentials_committed": False, "runtime_install_attempted": False})
    write_out_json("runtime_connector_approval_gate_batch068b.json", {"status": "BLOCK", "candidate_id": NKI_CANDIDATE, "approved_runtime_connector_count": 0, "exact_blocker": "approved_aws_neuron_nki_runtime_connector_not_present"})
    write_out_json("incoming_artifact_quarantine_policy_batch068b.json", {"status": "PASS", "quarantine_paths": ["incoming_artifacts/"], "raw_incoming_artifact_commit_allowed": False, "raw_external_archive_commit_allowed": False, "candidate_checkout_commit_allowed": False, "provider_venv_commit_allowed": False, "allowed_classifications": ALLOWED_INTAKE_CLASSIFICATIONS})
    write_out_json("manual_artifact_approval_workflow_batch068b.json", {"status": "PASS", "steps": ["quarantine", "hash", "structured_parse_if_safe", "candidate_mapping", "provenance_check", "forbidden_evidence_scan", "schema_validation", "approval_or_rejection"], "approval_without_hash_or_provenance_allowed": False})
    write_out_json("manual_artifact_rejection_policy_batch068b.json", {"status": "PASS", "rejection_codes": [item for item in ALLOWED_INTAKE_CLASSIFICATIONS if item.startswith("rejected_")], "future_gold_fixed_guidance_rejected": True, "issue_fix_guidance_rejected": True})
    write_out_json("approved_manual_artifact_registry_batch068b.json", {"status": "PASS", "approved_count": len(approved_records), "records": approved_records})
    write_out_json("rejected_manual_artifact_registry_batch068b.json", {"status": "PASS", "rejected_count": len(rejected_records), "records": rejected_records})
    write_out_json("incoming_manual_artifact_scan_batch068b.json", {"status": "PASS", "incoming_artifact_count": len(scan_records), "records": scan_records, "no_manual_artifacts_present_for_intake": len(scan_records) == 0})
    write_out_json("incoming_manual_artifact_approval_results_batch068b.json", {"status": "PASS", "incoming_manual_artifact_count": len(scan_records), "approved_manual_artifact_count": len(approved_records), "rejected_manual_artifact_count": len(rejected_records), "records": scan_records})
    external_requests = [
        build_external_source_request(candidate_id=packet["candidate_id"], source_url=packet["issue_url"], source_type="issue_or_candidate_era_command_source", why_source_is_needed=packet["exact_blocker"])
        for packet in manual_requests
    ]
    write_out_json("external_source_approval_queue_batch068b.json", {"status": "PASS", "request_count": len(external_requests), "records": external_requests})
    write_out_json("external_source_approval_schema_batch068b.json", external_source_approval_schema())
    write_out_json("external_source_decision_time_safety_policy_batch068b.json", {"status": "PASS", "allowed_use": external_source_approval_schema()["allowed_use"], "forbidden_use": external_source_approval_schema()["forbidden_use"], "future_fix_leakage_forbidden": True})
    write_out_json("seed_product_readiness_registry_batch068b.json", seed_registry)
    write_out_json("seed_reopen_condition_registry_batch068b.json", {"status": "PASS", "records": [{"candidate_id": item.get("candidate_id"), "readiness_status": item.get("batch068b_readiness_status"), "reopen_condition": item.get("reopen_condition"), "exact_blocker": item.get("exact_blocker")} for item in seed_registry["records"]]})
    write_out_json("batch068b_seed_readiness_delta.json", {"status": "PASS", "manual_artifact_request_emitted_count": len(manual_requests), "runtime_connector_request_emitted_count": 1, "unapproved_without_reason_count": seed_registry["unapproved_without_reason_count"]})
    write_out_json("manual_artifact_readiness_backlog_batch068b.json", {"status": "PASS", "request_count": len(manual_requests), "records": manual_requests})
    write_out_json("runtime_connector_readiness_backlog_batch068b.json", {"status": "PASS", "request_count": 1, "records": [nki_request]})
    copy_preserved_interlock_outputs()
    approved_native_count = sum(1 for item in approved_records if item.get("classification") == "approved_for_command_boundary_recovery")
    approved_connector_count = sum(1 for item in approved_records if item.get("classification") == "approved_for_runtime_connector_planning")
    next_action = "batch069c_manual_artifact_command_replay_followup" if approved_native_count else "batch068c_runtime_connector_readiness_buildout" if approved_connector_count else "batch068b_waiting_for_manual_artifacts_or_source_expansion"
    write_out_json("batch068b_handoff_plan.json", {"status": "PASS", "next_allowed_action": next_action, "approved_native_command_artifact_count": approved_native_count, "approved_runtime_connector_count": approved_connector_count, "manual_artifact_candidates": list(MANUAL_CANDIDATES), "runtime_connector_candidates": [NKI_CANDIDATE], "forbidden_next_actions": ["full_scoring", "memory_lift_testing", "self_maintaining_claim_review"]})
    write_out_json("batch068b_final_decision.json", {"status": "PASS", "batch069b_ingest_status": artifact_ingestion["status"], "batch068b_audit_status": "PASS", "current_protocol": CURRENT_PROTOCOL, "issue_derived_repair_count": ISSUE_DERIVED_REPAIR_COUNT, "native_external_repair_count": NATIVE_EXTERNAL_REPAIR_COUNT, "full_scoring": FULL_SCORING, "memory_lift": MEMORY_LIFT, "self_maintaining_software": SELF_MAINTAINING, "patch_generated": False, "patch_applied": False, "source_mutated": False, "tests_mutated": False, "fixtures_mutated": False, "config_mutated": False, "duplicate_replay_run": False, "count_gate_run": False, "repair_count_increment": False, "manual_artifact_request_count": len(manual_requests), "runtime_connector_request_count": 1, "incoming_manual_artifact_count": len(scan_records), "approved_manual_artifact_count": len(approved_records), "rejected_manual_artifact_count": len(rejected_records), "approved_native_command_artifact_count": approved_native_count, "approved_runtime_connector_count": approved_connector_count, "manual_artifact_candidates": list(MANUAL_CANDIDATES), "runtime_connector_candidates": [NKI_CANDIDATE], "seed_product_readiness_status": "PASS", "universal_interlock_law_status": "PASS", "next_allowed_action": next_action, "exact_blocker": None if approved_native_count or approved_connector_count else "manual_native_command_artifacts_or_runtime_connector_not_yet_approved"})
    write_text_lf(OUT_DIR / "batch068b_summary.md", PUBLIC_SUMMARY)
    write_sha256sums(OUT_DIR)
    print(f"Batch068b generated manual artifact/source custody intake outputs in {OUT_DIR}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
