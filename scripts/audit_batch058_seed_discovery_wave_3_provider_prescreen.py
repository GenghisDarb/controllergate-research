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


OUT_DIR = ROOT / "outputs" / "post_v2_37_hardening_batch058_seed_discovery_wave_3_provider_prescreen"
BATCH056F_DIR = ROOT / "outputs" / "post_v2_37_hardening_batch056f_timeout_split_replay_wave_2"
CURRENT_PROTOCOL = "v2.14"
EXPECTED_BATCH056F_SHA256 = "6a5f33549f720ec88590e3bc3936a1ee229a37dddb409c41655955f6da50b2cb"
EXPECTED_BATCH056F_SIZE = 167512
EXPECTED_BATCH056F_ENTRY_COUNT = 263
EXPECTED_BATCH056F_ARTIFACT_MANIFEST_CHECKED = 262
EXPECTED_BATCH056F_OUTPUT_MANIFEST_CHECKED = 261
REQUIRED_TOP_LEVEL = [
    "batch056f_artifact_ingestion_summary.json",
    "batch056f_artifact_sha256_verification.json",
    "batch056f_result_preservation.json",
    "batch056f_timeout_split_preservation.json",
    "batch056f_amds_bridge_preservation.json",
    "batch056f_claim_boundary_preservation.json",
    "batch056f_next_action_boundary.json",
    "wave3_provider_capsule_lessons_from_wave2.json",
    "reactome_provider_capsule_pattern_preservation.json",
    "wave3_candidate_exclusion_rules.json",
    "wave3_provider_complexity_risk_model.json",
    "wave3_seed_quality_gate.json",
    "seed_lead_registry_wave_3.json",
    "seed_lead_registry_wave_3_normalized.json",
    "wave3_codex_search_queries.json",
    "wave3_codex_search_results_raw.json",
    "wave3_codex_augmented_leads.json",
    "wave3_lead_source_audit.json",
    "issue_reference_validation_wave_3.json",
    "issue_body_leakage_screen_wave_3.json",
    "duplicate_seed_rejection_audit_wave_3.json",
    "already_counted_repair_check_wave_3.json",
    "candidate_commit_resolution_audit_wave_3.json",
    "provider_capsule_prescreen_wave_3.json",
    "provider_complexity_risk_assessment_wave_3.json",
    "provider_capsule_candidate_dashboard_wave_3.json",
    "wave3_candidate_ranking.json",
    "wave3_provider_capsule_ranked_candidates.json",
    "batch059_pre_repair_replay_wave_3_plan.json",
    "wave3_rejected_candidate_registry.json",
    "wave3_probe_only_candidate_registry.json",
    "wave3_campaign_dashboard.json",
    "batch058_summary.md",
    "batch058_final_decision.json",
    "claim_boundary.json",
    "audit.json",
    "package_verification.json",
    "artifact_sha256_verification.json",
    "SHA256SUMS.txt",
]
PER_CANDIDATE_FILES = [
    "provider_materialization_capsule_prescreen.json",
    "provider_capsule_evidence_manifest.json",
    "declared_runtime_map.json",
    "declared_dependency_map.json",
    "declared_test_command_map.json",
    "declared_external_service_map.json",
    "declared_network_or_model_download_map.json",
    "declared_compiled_dependency_map.json",
    "provider_unknowns.json",
    "provider_risk_classification.json",
    "future_replay_readiness.json",
]
FORBIDDEN_STATUS_FRAGMENTS = [
    ".zip",
    ".tar",
    ".tgz",
    ".7z",
    ".whl",
    ".pyc",
    ".pyo",
    "__pycache__",
    ".pytest_cache",
    "artifact_payload/",
    "ControllerGate_runtime",
    "runtime_workspaces/",
    "venv/",
    ".venv/",
]


def read_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        value = json.load(handle)
    if not isinstance(value, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return value


def git_lines(*args: str) -> list[str]:
    completed = subprocess.run(["git", *args], cwd=ROOT, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
    return [line.rstrip("\n") for line in completed.stdout.splitlines()]


def expect_false(errors: list[str], obj: dict[str, Any], key: str, context: str) -> None:
    if obj.get(key) is not False:
        errors.append(f"{context}: expected {key}=false")


def audit_git_status(errors: list[str]) -> None:
    for line in git_lines("status", "--short"):
        normalized = line[3:].replace("\\", "/") if len(line) > 3 else line.replace("\\", "/")
        if line.startswith("?? incoming_artifacts/"):
            continue
        for fragment in FORBIDDEN_STATUS_FRAGMENTS:
            if fragment in normalized:
                errors.append(f"forbidden path appears in git status: {line}")
                break


def main() -> int:
    errors: list[str] = []
    if not OUT_DIR.is_dir():
        print(f"FAIL: missing output directory: {OUT_DIR.relative_to(ROOT)}")
        return 1
    for rel in REQUIRED_TOP_LEVEL:
        if not (OUT_DIR / rel).is_file():
            errors.append(f"missing required Batch058 output: {rel}")
    if not errors:
        manifest = verify_manifest(OUT_DIR)
        if manifest.get("status") != "PASS":
            errors.append(f"Batch058 SHA256SUMS verification failed: {manifest}")
    if errors:
        print("FAIL:")
        for error in errors:
            print(f"- {error}")
        return 1

    artifact = read_json(OUT_DIR / "batch056f_artifact_sha256_verification.json")
    ingest = read_json(OUT_DIR / "batch056f_artifact_ingestion_summary.json")
    preservation = read_json(OUT_DIR / "batch056f_result_preservation.json")
    next_boundary = read_json(OUT_DIR / "batch056f_next_action_boundary.json")
    lessons = read_json(OUT_DIR / "wave3_provider_capsule_lessons_from_wave2.json")
    reactome = read_json(OUT_DIR / "reactome_provider_capsule_pattern_preservation.json")
    risk_model = read_json(OUT_DIR / "wave3_provider_complexity_risk_model.json")
    seed_gate = read_json(OUT_DIR / "wave3_seed_quality_gate.json")
    registry = read_json(OUT_DIR / "seed_lead_registry_wave_3.json")
    normalized = read_json(OUT_DIR / "seed_lead_registry_wave_3_normalized.json")
    augmented = read_json(OUT_DIR / "wave3_codex_augmented_leads.json")
    raw_search = read_json(OUT_DIR / "wave3_codex_search_results_raw.json")
    leakage = read_json(OUT_DIR / "issue_body_leakage_screen_wave_3.json")
    commit_audit = read_json(OUT_DIR / "candidate_commit_resolution_audit_wave_3.json")
    provider = read_json(OUT_DIR / "provider_capsule_prescreen_wave_3.json")
    risk = read_json(OUT_DIR / "provider_complexity_risk_assessment_wave_3.json")
    plan = read_json(OUT_DIR / "batch059_pre_repair_replay_wave_3_plan.json")
    final = read_json(OUT_DIR / "batch058_final_decision.json")
    claim = read_json(OUT_DIR / "claim_boundary.json")
    package = read_json(OUT_DIR / "package_verification.json")

    if artifact.get("status") != "PASS":
        errors.append("Batch056f artifact verification did not pass")
    if artifact.get("zip_sha256") != EXPECTED_BATCH056F_SHA256 or artifact.get("artifact_sha256") != EXPECTED_BATCH056F_SHA256:
        errors.append("Batch056f artifact SHA mismatch")
    if artifact.get("zip_size_bytes") != EXPECTED_BATCH056F_SIZE or artifact.get("zip_entry_count") != EXPECTED_BATCH056F_ENTRY_COUNT:
        errors.append("Batch056f artifact size or entry count mismatch")
    if artifact.get("artifact_manifest", {}).get("checked") != EXPECTED_BATCH056F_ARTIFACT_MANIFEST_CHECKED:
        errors.append("Batch056f artifact manifest checked count mismatch")
    output_manifest = artifact.get("output_manifests", {}).get("post_v2_37_hardening_batch056f_timeout_split_replay_wave_2", {})
    if output_manifest.get("checked") != EXPECTED_BATCH056F_OUTPUT_MANIFEST_CHECKED or output_manifest.get("failures") != 0:
        errors.append("Batch056f internal manifest verification mismatch")
    for key in ["unsafe_path_count", "duplicate_path_count", "zip_pycache_entries", "zip_pyc_entries"]:
        if artifact.get(key) != 0:
            errors.append(f"Batch056f artifact has non-zero {key}")
    if ingest.get("status") != "PASS":
        errors.append("Batch056f official ingest did not pass")
    expect_false(errors, artifact, "raw_zip_bytes_ingested", "Batch056f artifact verification")
    expect_false(errors, artifact, "zip_payload_committed", "Batch056f artifact verification")

    if preservation.get("issue_derived_repair_count") != 2 or preservation.get("native_external_repair_count") != 4:
        errors.append("Batch056f repair counts not preserved")
    for key in ["batch056f_patch_generated", "batch056f_patch_applied", "batch056f_duplicate_replay_run", "batch056f_count_gate_run"]:
        expect_false(errors, preservation, key, "Batch056f result preservation")
    if preservation.get("target_code_failure_materialization_count") != 0 or preservation.get("future_patch_gate_candidates") not in ([], None):
        errors.append("Batch056f target failure / future patch gate boundary changed")
    if next_boundary.get("matches_expected") is not True:
        errors.append("Batch056f next action did not authorize Batch058")

    if lessons.get("repair_count_remains_unchanged") is not True:
        errors.append("Provider capsule lessons do not preserve repair count")
    if reactome.get("reactome_used_as") != "infrastructure_provider_capsule_pattern_only" or reactome.get("reactome_used_as_repair_evidence") is not False:
        errors.append("Reactome pattern used as repair evidence")
    if risk_model.get("unbounded_candidates_approved_for_batch059") is not False:
        errors.append("Risk model allows unbounded candidates")
    if seed_gate.get("seed_approval_is_repair_success") is not False:
        errors.append("Seed gate counts approval as repair success")

    if registry.get("status") != "PASS" or normalized.get("lead_count", 0) < 30:
        errors.append("Wave 3 lead registry did not reach the required 30 weak leads")
    if augmented.get("codex_augmented_leads_count", 0) <= 0:
        errors.append("Codex-augmented leads missing despite available GitHub API")
    if raw_search.get("body_omitted") is not True:
        errors.append("Raw search persisted issue bodies")
    if leakage.get("body_text_persisted") is not False:
        errors.append("Issue body text persisted in leakage screen")
    for row in leakage.get("records", []):
        if row.get("body_screen", {}).get("body_not_persisted") is not True:
            errors.append(f"issue body persistence boundary missing for {row.get('lead_id')}")

    approved_ids = [row["lead_id"] for row in provider.get("records", []) if row.get("approval_status") == "approved_for_provider_prescreen"]
    planned_ids = [row["lead_id"] for row in plan.get("planned_candidates", [])]
    if planned_ids != approved_ids[:8]:
        errors.append("Batch059 plan does not match approved provider-prescreen candidates")
    if plan.get("pre_repair_replay_run_in_batch058") is not False:
        errors.append("Batch058 ran pre-repair replay")
    if len(planned_ids) != final.get("approved_for_batch059_replay_count"):
        errors.append("Batch058 final approved count does not match plan")

    risk_by_candidate = risk.get("risk_by_candidate", {})
    if risk.get("unbounded_candidates_approved") is not False:
        errors.append("Provider risk assessment approved unbounded candidate")
    for lead_id in planned_ids:
        if risk_by_candidate.get(lead_id) not in {"provider_risk_low", "provider_risk_medium"}:
            errors.append(f"planned candidate has unacceptable provider risk: {lead_id}")
        cdir = OUT_DIR / "candidates" / lead_id
        for rel in PER_CANDIDATE_FILES:
            if not (cdir / rel).is_file():
                errors.append(f"missing provider prescreen file for {lead_id}: {rel}")
        capsule = read_json(cdir / "provider_materialization_capsule_prescreen.json")
        if capsule.get("approval_status") != "approved_for_provider_prescreen":
            errors.append(f"planned candidate not approved in capsule: {lead_id}")
        if capsule.get("git_commit_verification", {}).get("git_cat_file_commit_verified") is not True:
            errors.append(f"planned candidate commit not git cat-file verified: {lead_id}")
        if capsule.get("repair_success_claim_allowed") is not False:
            errors.append(f"planned candidate capsule allows repair success claim: {lead_id}")
        network = read_json(cdir / "declared_network_or_model_download_map.json")
        external = read_json(cdir / "declared_external_service_map.json")
        compiled = read_json(cdir / "declared_compiled_dependency_map.json")
        if network.get("network_or_model_download_required") is True or network.get("unbounded_download_allowed") is not False:
            errors.append(f"planned candidate has network/model boundary: {lead_id}")
        if external.get("external_service_required") is True:
            errors.append(f"planned candidate requires external service: {lead_id}")
        if compiled.get("compiled_dependency_risk") is True:
            errors.append(f"planned candidate has compiled-heavy dependency risk: {lead_id}")

    for row in commit_audit.get("records", []):
        if row.get("approval_status") == "approved_for_provider_prescreen":
            if row.get("git_commit_verification", {}).get("git_cat_file_commit_verified") is not True:
                errors.append(f"approved candidate SHA not git verified: {row.get('lead_id')}")

    for key in ["pre_repair_replay_run", "patch_generated", "patch_applied", "post_repair_replay_run", "duplicate_replay_run", "count_gate_run", "repair_count_increment"]:
        expect_false(errors, final, key, "Batch058 final decision")
    if claim.get("current_protocol") != CURRENT_PROTOCOL:
        errors.append("Current protocol changed from v2.14")
    if claim.get("issue_derived_repair_count") != 2 or claim.get("native_external_repair_count") != 4:
        errors.append("Repair counts changed in Batch058")
    if claim.get("full_scoring") != "NOT_RUN/disallowed" or claim.get("memory_lift") != "not_demonstrated" or claim.get("self_maintaining_software") != "false/not_demonstrated":
        errors.append("Batch058 claim boundary overclaim")
    for key in ["pre_repair_replay_run", "patch_generated", "patch_applied", "post_repair_replay_run", "duplicate_replay_run", "count_gate_run", "repair_count_increment", "seed_approval_counts_as_repair_success"]:
        expect_false(errors, claim, key, "Batch058 claim boundary")
    expect_false(errors, package, "raw_zip_payload_committed", "Batch058 package")
    expect_false(errors, package, "runtime_workspaces_committed", "Batch058 package")

    batch056f_final = read_json(BATCH056F_DIR / "batch056f_final_decision.json")
    if batch056f_final.get("next_allowed_action") != "batch058_seed_discovery_wave_3":
        errors.append("Existing Batch056f next action changed")
    audit_git_status(errors)
    if errors:
        print("FAIL:")
        for error in errors:
            print(f"- {error}")
        return 1
    print("Batch058 seed discovery wave 3 provider prescreen audit PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
