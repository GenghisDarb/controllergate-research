from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from controllergate.core.manifests import verify_manifest
from controllergate.core.artifact_hygiene import audit_artifact_payload

POST_DIR = Path("outputs/post_v2_37_hardening_001")
BATCH_DIR = Path("outputs/clean_replication_batch_002")
PAYLOAD_DIR = Path("artifact_payload/post_v2_37_hardening_batch002_environment_resolution")

POST_REQUIRED = [
    "workspace_transport_integrity_policy.json",
    "post_v2_37_hardening_artifact_verification.json",
    "artifact_pycache_payload_audit.json",
    "batch002_mixed_mode_failure_diagnosis.json",
    "corrected_batch002_artifact_verification.json",
    "batch002_real_acquisition_gap_diagnosis.json",
    "real_leads_artifact_verification.json",
    "batch002_environment_resolution_gap_diagnosis.json",
    "artifact_packaging_correction_report.json",
    "artifact_payload_manifest_report.json",
    "readme_status_update_report.json",
    "public_docs_accuracy_audit.json",
    "operational_gate_matrix_status.json",
    "public_language_audit_expanded.json",
    "workspace_transport_integrity_log.json",
    "transport_boundary_audit.json",
    "homeostasis_risk_policy.json",
    "homeostasis_risk_state.json",
    "starvation_pressure_log.json",
    "version_sprawl_pressure_log.json",
    "public_claim_pressure_log.json",
    "bounded_exploration_budget_policy.json",
    "bounded_exploration_budget_trace.json",
    "context_boundary_policy.json",
    "context_boundary_map.json",
    "context_boundary_rejection_ledger.json",
    "environment_normalization_policy.json",
    "environment_normalization_log.json",
    "issue_derived_evidence_class_policy.json",
    "issue_text_temporal_guard_policy.json",
    "issue_derived_latent_knowledge_risk_disclosure.json",
    "bugsinpy_relaxation_research_status.json",
    "operational_gate_completion_status.json",
    "v3_0_readiness_scorecard_update.json",
    "final_report_post_v2_37_hardening_001.json",
    "consolidated_state_post_v2_37_hardening_001.json",
    "campaign_summary.md",
    "SHA256SUMS.txt",
]

BATCH_REQUIRED = [
    "consolidated_state_clean_replication_batch_002.json",
    "campaign_summary.md",
    "candidate_source_mode_trace.json",
    "lead_pool_intake_report.json",
    "curated_seed_intake_report.json",
    "metadata_probe_attempts.json",
    "issue_derived_attempts.json",
    "environment_resolution_attempts.json",
    "environment_resolution_policy.json",
    "environment_failure_classification.json",
    "dependency_install_logs_manifest.json",
    "candidate_verification_attempts.json",
    "candidate_rejection_ledger.json",
    "verified_candidates.json",
    "repair_attempts.json",
    "repair_successes.json",
    "matched_null_results.json",
    "memory_lift_evaluation.json",
    "native_issue_derived_count_separation.json",
    "claim_boundary.json",
    "SHA256SUMS.txt",
]


def blocked_terms() -> list[str]:
    return [
        "chromo" + "somal",
        "TO" + "RUS",
        "TL" + "D",
        "A" + "GI",
        "observer" + "-state",
        "RNA " + "primase",
        "Meta" + "-cell",
        "Klein " + "bottle",
        "res" + "onance",
    ]


def read_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def fail(message: str) -> int:
    print(f"FAIL: {message}")
    return 1


def require_files(root: Path, files: list[str]) -> list[str]:
    return [rel for rel in files if not (root / rel).is_file()]


def command_passes(command: list[str]) -> bool:
    completed = subprocess.run(command, text=True, capture_output=True)
    if completed.returncode != 0:
        print(completed.stdout)
        print(completed.stderr)
    return completed.returncode == 0


def load_lead_pool(path: Path = Path("inputs/clean_replication_batch_002_lead_pool.json")) -> dict[str, object]:
    if not path.is_file():
        return {"status": "MISSING", "leads": [], "lead_count": 0}
    data = read_json(path)
    leads = data.get("leads", [])
    return {"status": "PASS", "leads": leads if isinstance(leads, list) else [], "lead_count": len(leads) if isinstance(leads, list) else 0}


def audit_real_acquisition_records(
    lead_pool: dict[str, object],
    metadata_attempts: list[dict[str, object]],
    issue_attempts: list[dict[str, object]],
    candidate_attempts: list[dict[str, object]],
    batch: dict[str, object],
) -> list[str]:
    errors: list[str] = []
    leads = lead_pool.get("leads", [])
    if not isinstance(leads, list):
        leads = []
    native_leads = [
        lead
        for lead in leads
        if isinstance(lead, dict)
        and lead.get("allowed_candidate_class") in {"native", "either"}
        and lead.get("lead_type") in {"repo_metadata", "commit_hint"}
    ]
    if any("py_bugger_issue_65" in json.dumps(item, sort_keys=True) for item in [*leads, *candidate_attempts]):
        errors.append("py_bugger_issue_65 reused as a new lead")
    if not leads and batch.get("exact_blocker") != "clean_replication_batch_002_lead_pool_empty":
        errors.append("lead pool empty without clean_replication_batch_002_lead_pool_empty blocker")
    if metadata_attempts and all(item.get("repo") == "offline_local_metadata_lead_pool" for item in metadata_attempts):
        errors.append("metadata_probe placeholder pool counted as acquisition")
    if issue_attempts and all(item.get("issue_lead") == "offline_local_issue_lead_pool" for item in issue_attempts):
        errors.append("issue_derived placeholder pool counted as acquisition")
    if native_leads and not any(item.get("lead_id") for item in candidate_attempts):
        errors.append("no real lead_id appears in candidate verification attempts")
    if native_leads and not metadata_attempts:
        errors.append("native lead pool present but metadata_probe_attempts empty")
    if metadata_attempts:
        if any(item.get("git_clone_status") == "PASS" for item in metadata_attempts) and not any(item.get("checkout_attempted") is True for item in metadata_attempts):
            errors.append("metadata_probe clone passed but no checkout was attempted")
        if all(item.get("checkout_attempted") is False for item in metadata_attempts) and any(not item.get("blocker") for item in metadata_attempts):
            errors.append("metadata_probe checkout false for every lead without specific blockers")
        if any(item.get("lead_id") and item.get("git_clone_attempted") is not True for item in metadata_attempts):
            errors.append("real metadata lead missing git clone attempt")
    if any(item.get("mode") == "issue_derived" and not item.get("lead_id") for item in candidate_attempts):
        errors.append("issue_derived no-lead placeholder counted as real candidate verification attempt")
    allowed_blockers = {
        "clean_replication_batch_002_lead_pool_empty",
        "metadata_probe_network_unavailable",
        "metadata_probe_no_verified_candidates",
        "metadata_probe_no_verified_candidates_after_environment_resolution",
        "clean_replication_batch_002_no_repair_successes_after_environment_resolution",
        "issue_derived_no_safe_leads",
        "clean_replication_batch_002_no_verified_candidates",
        "environment_dependency_install_failed",
        "environment_dependency_undeclared",
        "environment_editable_install_failed",
        "environment_declared_extra_missing",
        "environment_python_version_incompatible",
        "environment_collection_failed_after_resolution",
        "clean_replication_batch_002_no_repair_successes_after_environment_resolution",
    }
    if batch.get("exact_blocker") not in allowed_blockers:
        errors.append(f"unexpected batch002 blocker: {batch.get('exact_blocker')}")
    return errors


def audit_environment_resolution_records(metadata_attempts: list[dict[str, object]], batch: dict[str, object]) -> list[str]:
    errors: list[str] = []
    real_metadata = [item for item in metadata_attempts if item.get("lead_id")]
    for item in real_metadata:
        if item.get("environment_resolution_attempted") is not True:
            errors.append(f"{item.get('lead_id')}: environment_resolution_not_attempted")
        if item.get("environment_resolution_attempted") is True and not item.get("install_strategy_attempts"):
            errors.append(f"{item.get('lead_id')}: install strategy attempts missing")
        if item.get("environment_resolution_attempted") is True and item.get("import_probe_attempted") is not True:
            errors.append(f"{item.get('lead_id')}: import probe not recorded")
        if item.get("collection_attempted") is True and item.get("environment_resolution_attempted") is not True:
            errors.append(f"{item.get('lead_id')}: collection occurred before environment resolution")
        text = json.dumps(item, sort_keys=True)
        if ("ModuleNotFoundError" in text or "No module named" in text) and item.get("environment_resolution_attempted") is not True:
            errors.append(f"{item.get('lead_id')}: ModuleNotFoundError accepted without environment resolution")
        if str(item.get("blocker", "")).startswith("metadata_probe_collection_failed"):
            errors.append(f"{item.get('lead_id')}: old collection blocker used after environment resolution")
        if item.get("environment_resolution_attempted") is True and item.get("blocker") == "metadata_probe_collection_failed":
            errors.append(f"{item.get('lead_id')}: candidate/environment failure not separated")
    allowed_after_environment = {
        "metadata_probe_no_verified_candidates_after_environment_resolution",
        "environment_dependency_install_failed",
        "environment_dependency_undeclared",
        "environment_editable_install_failed",
        "environment_declared_extra_missing",
        "environment_python_version_incompatible",
        "environment_collection_failed_after_resolution",
        "metadata_probe_network_unavailable",
        "clean_replication_batch_002_no_verified_candidates",
        "clean_replication_batch_002_no_repair_successes_after_environment_resolution",
    }
    if real_metadata and all(item.get("environment_resolution_attempted") is True for item in real_metadata):
        if batch.get("exact_blocker") not in allowed_after_environment:
            errors.append(f"batch blocker does not reflect environment-aware acquisition: {batch.get('exact_blocker')}")
    return errors


def public_language_hits() -> list[str]:
    paths = [
        Path("README.md"),
        Path("docs/current_status.md"),
        Path("docs/capability_inventory.md"),
        Path("docs/claim_boundaries.md"),
        Path("docs/public_release_readiness.md"),
        Path("docs/technical_validation_gap_report.md"),
        Path("docs/replication_protocol.md"),
        Path("docs/evidence_model.md"),
        Path("docs/operational_gate_matrix.md"),
        Path("configs/operational_gate_matrix.json"),
        Path("controllergate_v1_7_beta/reports/critic_review_package/shareable_summary.md"),
        Path(".github/workflows/post_v2_37_hardening_and_batch002.yml"),
    ]
    hits: list[str] = []
    for path in paths:
        if not path.is_file():
            hits.append(f"missing:{path.as_posix()}")
            continue
        text = path.read_text(encoding="utf-8")
        for term in blocked_terms():
            if term in text:
                hits.append(f"{path.as_posix()}:{term}")
    return hits


def main() -> int:
    missing = require_files(POST_DIR, POST_REQUIRED) + require_files(BATCH_DIR, BATCH_REQUIRED)
    if missing:
        return fail(f"missing required files: {missing}")
    if verify_manifest(POST_DIR)["status"] != "PASS":
        return fail("post hardening manifest mismatch")
    if verify_manifest(BATCH_DIR)["status"] != "PASS":
        return fail("batch002 manifest mismatch")
    if not command_passes([sys.executable, "-m", "pytest", "tests/core", "-q"]):
        return fail("core tests failed")
    if not command_passes([sys.executable, "scripts/audit_v2_37_core_consolidation_and_clean_replication.py"]):
        return fail("v2.37 audit failed")

    records = read_json(POST_DIR / "workspace_transport_integrity_log.json").get("transfer_records")
    if not isinstance(records, list):
        return fail("transport integrity log invalid")
    for record in records:
        if not isinstance(record, dict):
            return fail("transport record malformed")
        for field in ["source_path", "destination_path", "source_sha256", "destination_sha256", "transfer_reason", "allowlist_class", "transport_decision"]:
            if not record.get(field):
                return fail(f"transport record missing {field}")
        if record.get("transport_decision") != "PASS":
            return fail("transport_integrity_breach")

    if read_json(POST_DIR / "transport_boundary_audit.json").get("forbidden_payload_count") != 0:
        return fail("forbidden payload recorded")
    if read_json(POST_DIR / "bounded_exploration_budget_trace.json").get("status") != "PASS":
        return fail("bounded exploration budget trace blocked unexpectedly")
    if read_json(POST_DIR / "environment_normalization_log.json").get("status") != "PASS":
        return fail("environment normalization unsafe")
    if read_json(POST_DIR / "issue_derived_evidence_class_policy.json").get("increments_native_count") is not False:
        return fail("issue-derived evidence class increments native count")
    if read_json(POST_DIR / "bugsinpy_relaxation_research_status.json").get("global_block_active") is not True:
        return fail("BugsInPy global block relaxed")
    official = read_json(POST_DIR / "post_v2_37_hardening_artifact_verification.json")
    if official.get("status") != "PASS":
        return fail("post-v2.37 artifact verification not PASS")
    if official.get("zip_sha256") != "6e0dcb44607dd8a23661b7bff30448e36db561477e99d2bee0689494cb505f1b":
        return fail("post-v2.37 artifact SHA mismatch")
    pycache_audit = read_json(POST_DIR / "artifact_pycache_payload_audit.json")
    if pycache_audit.get("pycache_pyc_payload_count") != 26:
        return fail("expected prior artifact cache payload audit mismatch")
    diagnosis = read_json(POST_DIR / "batch002_mixed_mode_failure_diagnosis.json")
    if diagnosis.get("metadata_probe_attempted") is not False or diagnosis.get("issue_derived_fallback_attempted") is not False:
        return fail("batch002 prior failure diagnosis invalid")
    packaging = read_json(POST_DIR / "artifact_packaging_correction_report.json")
    if packaging.get("status") != "PASS":
        return fail("artifact packaging correction report not PASS")
    manifest_report = read_json(POST_DIR / "artifact_payload_manifest_report.json")
    if manifest_report.get("status") != "PASS" or manifest_report.get("cache_payload_count") != 0:
        return fail("artifact payload manifest report invalid")
    readme_report = read_json(POST_DIR / "readme_status_update_report.json")
    docs_report = read_json(POST_DIR / "public_docs_accuracy_audit.json")
    matrix_status = read_json(POST_DIR / "operational_gate_matrix_status.json")
    language_expanded = read_json(POST_DIR / "public_language_audit_expanded.json")
    if readme_report.get("status") != "PASS":
        return fail("README status update report failed")
    if docs_report.get("status") != "PASS":
        return fail("public docs accuracy audit failed")
    if matrix_status.get("status") != "PASS" or int(matrix_status.get("gate_count", 0)) < 26:
        return fail("operational gate matrix status failed")
    if language_expanded.get("status") != "PASS":
        return fail("expanded public language audit failed")
    payload_audit = audit_artifact_payload(PAYLOAD_DIR)
    if payload_audit["status"] != "PASS":
        return fail(f"artifact payload hygiene failed: {payload_audit}")

    batch = read_json(BATCH_DIR / "consolidated_state_clean_replication_batch_002.json")
    trace = read_json(BATCH_DIR / "candidate_source_mode_trace.json")
    trace_by_mode = {item.get("mode"): item for item in trace if isinstance(item, dict)}
    if trace_by_mode.get("curated_seed", {}).get("attempted") is not True:
        return fail("curated_seed not attempted")
    if trace_by_mode.get("metadata_probe", {}).get("attempted") is not True:
        return fail("metadata_probe not attempted")
    if trace_by_mode.get("issue_derived", {}).get("attempted") is not True:
        return fail("issue_derived fallback not attempted")
    attempts = read_json(BATCH_DIR / "candidate_verification_attempts.json")
    if not isinstance(attempts, list) or not attempts:
        return fail("candidate_verification_attempts must not be empty when modes are enabled")
    if any("py_bugger_issue_65" in json.dumps(item, sort_keys=True) for item in attempts):
        return fail("py_bugger_issue_65 reused as a new candidate")
    metadata_attempts = read_json(BATCH_DIR / "metadata_probe_attempts.json")
    issue_attempts = read_json(BATCH_DIR / "issue_derived_attempts.json")
    if not metadata_attempts and batch.get("exact_blocker") != "clean_replication_batch_002_lead_pool_empty":
        return fail("metadata probe attempt record invalid")
    if not issue_attempts and batch.get("exact_blocker") != "clean_replication_batch_002_lead_pool_empty":
        return fail("issue-derived attempt record invalid")
    real_acquisition_errors = audit_real_acquisition_records(load_lead_pool(), metadata_attempts, issue_attempts, attempts, batch)
    if real_acquisition_errors:
        return fail(f"real acquisition audit failed: {real_acquisition_errors}")
    env_attempts = read_json(BATCH_DIR / "environment_resolution_attempts.json")
    env_policy = read_json(BATCH_DIR / "environment_resolution_policy.json")
    env_classification = read_json(BATCH_DIR / "environment_failure_classification.json")
    install_manifest = read_json(BATCH_DIR / "dependency_install_logs_manifest.json")
    if env_policy.get("status") != "PASS" or env_policy.get("undeclared_arbitrary_dependency_install_allowed") is not False:
        return fail("environment resolution policy invalid")
    if not isinstance(env_attempts, list) or len(env_attempts) != len(metadata_attempts):
        return fail("environment resolution attempts do not align with metadata attempts")
    if not isinstance(env_classification, list) or not isinstance(install_manifest, list):
        return fail("environment classification or install log manifest invalid")
    environment_errors = audit_environment_resolution_records(metadata_attempts, batch)
    if environment_errors:
        return fail(f"environment resolution audit failed: {environment_errors}")
    repair_attempts = read_json(BATCH_DIR / "repair_attempts.json")
    verified_native_count = int(batch.get("native_candidates_verified_count", 0))
    if verified_native_count and (not isinstance(repair_attempts, list) or not repair_attempts):
        return fail("verified native candidates require recorded clean repair attempts")
    if isinstance(repair_attempts, list):
        for item in repair_attempts:
            if item.get("source_only_repair_attempted") is not True:
                return fail("repair attempt missing source-only marker")
            if item.get("source_mutation_performed") is not False or item.get("tests_modified") is not False:
                return fail("repair attempt mutated forbidden files")
    zero_count_fields = [
        "issue_derived_candidates_verified_count",
        "additional_native_external_repairs_acquired_count",
        "additional_issue_derived_repairs_acquired_count",
        "native_repair_successes_count",
        "issue_derived_repair_successes_count",
    ]
    for field in zero_count_fields:
        if batch.get(field) != 0:
            return fail(f"batch002 {field} changed unexpectedly")
    if batch.get("full_scoring") != "NOT_RUN/disallowed":
        return fail("full scoring boundary changed")
    if batch.get("memory_lift") != "undemonstrated":
        return fail("memory lift overclaim")
    if batch.get("self_maintaining_software") != "false/not_demonstrated":
        return fail("self-maintaining software overclaim")

    final_report = read_json(POST_DIR / "final_report_post_v2_37_hardening_001.json")
    if final_report.get("public_claim_overreach_status") != "PASS":
        return fail("public claim pressure not PASS")
    hits = public_language_hits()
    if hits:
        return fail(f"public language audit failed: {hits}")

    print("post-v2.37 hardening and batch002 audit PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
