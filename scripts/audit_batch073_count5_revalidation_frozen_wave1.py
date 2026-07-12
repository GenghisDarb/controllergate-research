from __future__ import annotations

from datetime import datetime
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from controllergate.core.batch073_count5_frozen_wave1 import BATCH, CANDIDATE_ID, CANDIDATE_SHA, CUTOFF, EXPECTED_SHA, EXPECTED_SIZE, H71, H72, PATCH_SHA
from controllergate.core.evidence import hash_record
from controllergate.runtime.count_gate import existing_count_hardening_gate, new_repair_count_gate

OUT = ROOT / "outputs" / BATCH


def load(name: str) -> dict:
    return json.loads((OUT / name).read_text(encoding="utf-8"))


def jsonl(name: str) -> list[dict]:
    return [json.loads(line) for line in (OUT / name).read_text(encoding="utf-8").splitlines() if line.strip()]


def manifest_valid(directory: Path) -> tuple[bool, int]:
    manifest = directory / "SHA256SUMS.txt"
    if not manifest.is_file():
        return False, 0
    checked = 0
    for line in manifest.read_text(encoding="utf-8").splitlines():
        parts = line.split(maxsplit=1)
        if len(parts) != 2:
            return False, checked
        expected, relative = parts
        target = directory / relative.strip().lstrip("*")
        if not target.is_file() or hashlib.sha256(target.read_bytes()).hexdigest() != expected:
            return False, checked
        checked += 1
    return True, checked


def main() -> int:
    errors: list[str] = []
    required = {
        "amds_live_contact_evidence_quality_batch073.json", "amds_semantic_recomputation_batch073.json",
        "batch072_artifact_ingest.json", "batch072_claim_boundary_preservation.json",
        "batch072_lead_frame_vs_cohort_reconciliation.json", "batch072_state_preservation.json",
        "batch072_wave1_execution_reconciliation.json", "batch073_admitted_cohort.json",
        "batch073_admitted_cohort_freeze.json", "batch073_arm_sealing_ground_truth_metrics.json",
        "batch073_authoritative_repair_decisions.json", "batch073_claim_boundary.json",
        "batch073_commit_resolution_registry.jsonl", "batch073_completion_decisions.json",
        "batch073_duplicate_failure_registry.jsonl", "batch073_final_decision.json",
        "batch073_issue_contamination_registry.jsonl", "batch073_lead_execution_registry.jsonl",
        "batch073_prospective_arm_execution.json", "batch073_provider_admission_registry.jsonl",
        "batch073_summary.md", "batch073_target_command_registry.jsonl", "batch074_cold_start_handoff.json",
        "batch074_exact_next_actions.json", "connexion_count5_hardening_decision.json",
        "connexion_cutoff_provider_lock.json", "connexion_cutoff_provider_verification.json",
        "connexion_duplicate_replay_and_rollback.json", "connexion_exact_patch_challenge.json",
        "connexion_hardened_root_requirements.json", "connexion_hardened_sbom.json",
        "connexion_hardened_wheelhouse_manifest.json", "connexion_historical_release_catalog.jsonl",
        "connexion_provider_arm_registry_batch073.json", "connexion_two_capsule_pre_repair_challenge.json",
        "connexion_two_capsule_registry_batch073.json", "existing_count_hardening_gate_batch073.json",
        "terminal_count_hardening_proof_event.json", "v2_19_authorization_live_demonstration_batch073.json",
        "v2_19_checkpoint_resume_live_demonstration_batch073.json",
        "v2_19_network_enforcement_live_demonstration_batch073.json", "SHA256SUMS.txt",
    }
    missing = sorted(name for name in required if not (OUT / name).is_file())
    if missing:
        errors.append("missing:" + ",".join(missing))
    if missing:
        print("Batch073 audit: FAIL")
        print("errors:", ", ".join(errors))
        return 1

    ingest = load("batch072_artifact_ingest.json")
    if ingest.get("status") != "PASS" or ingest.get("observed_size_bytes") != EXPECTED_SIZE or ingest.get("observed_sha256") != EXPECTED_SHA or ingest.get("file_count") != 74:
        errors.append("batch072_artifact_identity")
    if ingest.get("entry_audit", {}).get("status") != "PASS" or ingest.get("outer_manifest", {}).get("checked") != 73:
        errors.append("batch072_outer_custody")
    h71_ok, h71_count = manifest_valid(ROOT / "outputs" / H71)
    h72_ok, h72_count = manifest_valid(ROOT / "outputs" / H72)
    if not h71_ok or h71_count != 25 or not h72_ok or h72_count != 38:
        errors.append("batch072_internal_manifests")

    reconciliation = load("batch072_wave1_execution_reconciliation.json")
    frame_reconciliation = load("batch072_lead_frame_vs_cohort_reconciliation.json")
    frozen_frame = [json.loads(line) for line in (ROOT / "outputs" / H72 / "batch072_weak_lead_registry.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()]
    frozen_ids = [item["candidate_id"] for item in frozen_frame]
    if reconciliation.get("H72_admitted_cohort_status") != "NOT_YET_DERIVED" or reconciliation.get("commit_resolution_attempts_completed_in_H72") != 0 or reconciliation.get("not_twenty_failed_admissions") is not True:
        errors.append("h72_admission_semantics")
    if frame_reconciliation.get("lead_ids_in_order") != frozen_ids or len(frozen_ids) != 20 or frame_reconciliation.get("replacement_or_replenishment") is not False:
        errors.append("frozen_lead_frame")

    dispositions = jsonl("batch073_lead_execution_registry.jsonl")
    issues = {item["candidate_id"]: item for item in jsonl("batch073_issue_contamination_registry.jsonl")}
    commits = jsonl("batch073_commit_resolution_registry.jsonl")
    if [item["candidate_id"] for item in dispositions] != frozen_ids or [item["position"] for item in dispositions] != list(range(20)):
        errors.append("lead_execution_order")
    if any(item.get("admitted") or item.get("replacement_used") or not item.get("terminal_blocker") for item in dispositions):
        errors.append("lead_terminal_dispositions")
    screened_ids = {item["candidate_id"] for item in dispositions if item["terminal_blocker"] not in {"prior_controllergate_outcome_or_count_excluded", "issue_identity_missing"}}
    if any(not issues[item].get("body_read") or not issues[item].get("comments_read") for item in screened_ids):
        errors.append("issue_content_not_screened")
    for item in commits:
        if item.get("status") == "PASS":
            if item.get("reported_sha_trusted") is not False or item.get("reachable_by_fetch") is not True or item.get("commit_object") != "commit" or len(str(item.get("tree_hash", ""))) != 40:
                errors.append("commit_resolution_integrity")
                break
            if datetime.fromisoformat(item["commit_timestamp"].replace("Z", "+00:00")) > datetime.fromisoformat(item["cutoff"].replace("Z", "+00:00")):
                errors.append("commit_after_cutoff")
                break

    cohort = load("batch073_admitted_cohort.json")
    freeze = load("batch073_admitted_cohort_freeze.json")
    if cohort.get("status") != "EXECUTED_EMPTY_COHORT" or cohort.get("admission_attempts") != 20 or cohort.get("candidate_count") != 0 or sum(cohort.get("terminal_blocker_counts", {}).values()) != 20:
        errors.append("executed_empty_cohort")
    if freeze.get("cohort_hash") != hash_record(cohort) or not freeze.get("frozen_after_all_dispositions") or freeze.get("replacement_forbidden") is not True:
        errors.append("cohort_freeze")

    provider = load("connexion_cutoff_provider_verification.json")
    wheelhouse = load("connexion_hardened_wheelhouse_manifest.json")
    cutoff_evidence = ROOT / provider.get("cutoff_evidence_path", "missing")
    if provider.get("status") != "PASS" or provider.get("package_count") != 63 or provider.get("decision_time_cutoff") != CUTOFF or provider.get("cutoff_record_matches") is not True or not cutoff_evidence.is_file() or hashlib.sha256(cutoff_evidence.read_bytes()).hexdigest() != provider.get("cutoff_evidence_sha256") or provider.get("post_cutoff_selected_artifact_count") != 0 or provider.get("all_expected_hashes_verified") is not True:
        errors.append("connexion_provider_lock")
    if len(wheelhouse.get("artifacts", [])) != 63 or any(len(item.get("sha256", "")) != 64 or not item.get("cutoff_eligible") for item in wheelhouse.get("artifacts", [])):
        errors.append("connexion_artifact_hashes")
    sbom = load("connexion_hardened_sbom.json")
    if sbom.get("temporary_provider_paths_recorded") is not False or any("artifact_path" in item for item in sbom.get("nodes", {}).values()):
        errors.append("temporary_provider_path_leak")
    capsules = load("connexion_two_capsule_registry_batch073.json")
    if capsules.get("status") != "PASS" or capsules.get("same_provider_store") is not True or len(capsules.get("capsules", [])) != 4:
        errors.append("connexion_capsule_registry")
    if any(item.get("source_sha") != CANDIDATE_SHA or item.get("provider_lock_hash") != wheelhouse.get("provider_lock_hash") or item.get("network") != "none" or item.get("source_test_immutable") is not True or item.get("import_origins_verified") is not True for item in capsules.get("capsules", [])):
        errors.append("connexion_capsule_identity")
    patch = load("connexion_exact_patch_challenge.json")
    duplicate = load("connexion_duplicate_replay_and_rollback.json")
    if patch.get("status") != "PASS" or patch.get("patch_sha256") != PATCH_SHA or patch.get("changed_files") != ["connexion/utils.py"] or duplicate.get("status") != "PASS":
        errors.append("connexion_patch_challenge")

    hardening = load("existing_count_hardening_gate_batch073.json")
    if hardening.get("status") != "PASS" or hardening.get("count_increment") != 0 or hardening.get("mode") != "existing_count_hardening_gate":
        errors.append("count_hardening_recount")
    record = {"candidate_id": CANDIDATE_ID, "candidate_sha": CANDIDATE_SHA, "patch_sha256": PATCH_SHA}
    if new_repair_count_gate(record=record, registry=[record], prerequisites={"replay": True})["status"] != "BLOCK":
        errors.append("count_uniqueness_not_required")
    if existing_count_hardening_gate(record={**record, "patch_sha256": "0" * 64}, registry=[record], prerequisites={"replay": True})["status"] != "BLOCK":
        errors.append("count_identity_tamper")
    terminal = load("terminal_count_hardening_proof_event.json")
    unsigned = dict(terminal); supplied = unsigned.pop("event_hash", None)
    if supplied != hash_record(unsigned) or terminal.get("decision_hash") != hash_record(hardening):
        errors.append("terminal_proof_event")

    authorization = load("v2_19_authorization_live_demonstration_batch073.json")
    expected_negative = {"missing_authorization", "expired", "spent_nonce", "wrong_candidate", "wrong_state", "phase_skipping", "unauthorized_destination", "network_in_execution", "output_root", "test_mutation"}
    if authorization.get("status") != "PASS" or authorization.get("source_string_inspection_used") is not False:
        errors.append("live_authorization")
    for demonstration in (authorization.get("connexion", {}), authorization.get("frozen_lead", {})):
        if demonstration.get("live_result", {}).get("status") != "PASS" or demonstration.get("checkpoint_resume", {}).get("status") != "PASS" or set(demonstration.get("negative_rejections", {})) != expected_negative or not all(demonstration.get("negative_rejections", {}).values()):
            errors.append("authorization_negative_controls")
            break
    if load("v2_19_network_enforcement_live_demonstration_batch073.json").get("status") != "PASS":
        errors.append("network_enforcement")
    contacts = load("amds_live_contact_evidence_quality_batch073.json")
    semantic = load("amds_semantic_recomputation_batch073.json")
    if contacts.get("contact_count") != 14 or contacts.get("real_evidence_record_hashes") is not True or contacts.get("rollback_contact_requires_verified_records") is not True:
        errors.append("contact_evidence_quality")
    if semantic.get("AST_probe") != "real_ast_parse" or semantic.get("dependency_probe") != "artifact_hash_reverification" or semantic.get("unknown_likelihoods") != "NOT_ESTABLISHED":
        errors.append("semantic_recomputation")

    arms = load("batch073_prospective_arm_execution.json")
    metrics = load("batch073_arm_sealing_ground_truth_metrics.json")
    if arms.get("status") != "NOT_RUN_EXECUTED_EMPTY_COHORT" or any(arms.get(key) for key in ("candidate_arms_executed", "probe_executions", "posterior_updates", "backtracking_components", "semantic_verifications")):
        errors.append("empty_cohort_arm_boundary")
    if metrics.get("TLD_NSS_imported") or metrics.get("unverified_elbow_gate_used") or metrics.get("status") != "NOT_RUN_EXECUTED_EMPTY_COHORT":
        errors.append("ground_truth_boundary")
    final = load("batch073_final_decision.json")
    if final.get("historical_issue_derived_repair_count") != 5 or final.get("native_external_count") != 4 or final.get("AMDS_PROSPECTIVE_EFFECTIVENESS") != "NOT_ESTABLISHED" or final.get("memory_lift") != "not_demonstrated" or final.get("full_scoring") != "NOT_RUN/disallowed" or final.get("self_maintaining_software") != "false/not_demonstrated" or final.get("live_connectors") != "inactive":
        errors.append("claim_boundary")
    manifest_ok, manifest_count = manifest_valid(OUT)
    if not manifest_ok or manifest_count != len([path for path in OUT.iterdir() if path.is_file()]) - 1:
        errors.append("sha256_manifest")
    if len([path for path in OUT.iterdir() if path.is_file()]) > 45:
        errors.append("evidence_compaction")

    print("Batch073 audit:", "PASS" if not errors else "FAIL")
    if errors:
        print("errors:", ", ".join(errors))
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
