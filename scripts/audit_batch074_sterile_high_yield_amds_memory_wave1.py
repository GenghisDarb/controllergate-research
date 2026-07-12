from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from controllergate.core.batch074_sterile_high_yield_wave1 import BATCH, EXPECTED_SHA, EXPECTED_SIZE, H72, H73
from controllergate.intake.contamination_classifier import classify_contamination

OUT = ROOT / "outputs" / BATCH


def load(name: str) -> dict:
    return json.loads((OUT / name).read_text(encoding="utf-8"))


def manifest_valid(directory: Path) -> tuple[bool, int]:
    manifest = directory / "SHA256SUMS.txt"
    if not manifest.is_file():
        return False, 0
    checked = 0
    for line in manifest.read_text(encoding="utf-8").splitlines():
        parts = line.split(maxsplit=1)
        if len(parts) != 2:
            return False, checked
        digest, relative = parts
        target = directory / relative.strip().lstrip("*")
        if not target.is_file() or hashlib.sha256(target.read_bytes()).hexdigest() != digest:
            return False, checked
        checked += 1
    return True, checked


def main() -> int:
    errors: list[str] = []
    required = {
        "batch074_interrupted_worktree_audit.json",
        "batch074_background_process_reconciliation.json",
        "batch073_artifact_ingest.json",
        "batch073_state_preservation.json",
        "batch073_claim_boundary_preservation.json",
        "batch073_count5_hardening_preservation.json",
        "batch074_intake_engine_validation.json",
        "batch074_target_command_validation.json",
        "batch074_admission_diagnostic_separation.json",
        "batch074_arm_isolation_validation.json",
        "batch075_static_candidate_allowlist.json",
        "batch075_manual_review_checklist.json",
        "batch075_execution_scope.json",
        "batch075_cold_start_handoff.json",
        "batch074_final_decision.json",
        "batch074_summary.md",
        "SHA256SUMS.txt",
    }
    missing = sorted(name for name in required if not (OUT / name).is_file())
    if missing:
        errors.append("missing:" + ",".join(missing))
        print("Batch074 recovery audit: FAIL")
        print("errors:", ", ".join(errors))
        return 1
    ingest = load("batch073_artifact_ingest.json")
    if ingest.get("status") != "PASS" or ingest.get("observed_size_bytes") != EXPECTED_SIZE or ingest.get("observed_sha256") != EXPECTED_SHA or ingest.get("file_count") != 91:
        errors.append("batch073_artifact_identity")
    if ingest.get("outer_manifest", {}).get("checked") != 90 or ingest.get("batch072_manifest", {}).get("checked") != 38 or ingest.get("batch073_manifest", {}).get("checked") != 41:
        errors.append("batch073_manifest_counts")
    entry_audit = ingest.get("entry_audit", {})
    if entry_audit.get("status") != "PASS" or entry_audit.get("unsafe_paths") or entry_audit.get("duplicate_paths") or ingest.get("forbidden_payloads"):
        errors.append("batch073_custody")
    h72_ok, h72_count = manifest_valid(ROOT / "outputs" / H72)
    h73_ok, h73_count = manifest_valid(ROOT / "outputs" / H73)
    if not h72_ok or h72_count != 38 or not h73_ok or h73_count != 41:
        errors.append("ingested_internal_manifests")
    state = load("batch073_state_preservation.json")
    claims = load("batch073_claim_boundary_preservation.json")
    hardening = load("batch073_count5_hardening_preservation.json")
    if state.get("COUNT_5_HARDENING") != "PASS" or state.get("issue_derived_repair_count") != 5 or state.get("native_external_repair_count") != 4 or state.get("Batch073_cohort") != "EXECUTED_EMPTY_COHORT" or state.get("validated_protocol") != "v2.19":
        errors.append("batch073_state_preservation")
    if claims.get("AMDS_PROSPECTIVE_EFFECTIVENESS") != "NOT_ESTABLISHED" or claims.get("memory_lift") != "not_demonstrated" or hardening.get("count_increment") != 0 or hardening.get("cohort_reopened"):
        errors.append("claim_boundary")
    for name in ("batch074_intake_engine_validation.json", "batch074_target_command_validation.json", "batch074_admission_diagnostic_separation.json", "batch074_arm_isolation_validation.json"):
        if load(name).get("status") != "PASS":
            errors.append("local_validation:" + name)
    arm = load("batch074_arm_isolation_validation.json")
    if arm.get("arm_count") != 8 or not all(arm.get(key) for key in ("separate_authorization_state", "separate_nonce_stores", "separate_checkpoints", "separate_posterior_stores", "separate_event_ledgers", "separate_network_ledgers", "all_arm_outputs_sealed")) or arm.get("patch_authority_count") != 0 or arm.get("observation_sharing"):
        errors.append("diagnostic_arm_isolation")
    separation = load("batch074_admission_diagnostic_separation.json")
    if not separation.get("cohort_frozen_before_diagnostics") or separation.get("diagnostics_in_admission_plan") or separation.get("external_candidate_execution"):
        errors.append("admission_diagnostic_boundary")
    if classify_contamination("```python\nraise TypeError('repro')\n```")["classification"] == "HARD_REJECT" or classify_contamination("solution patch workaround")["classification"] == "HARD_REJECT" or classify_contamination("diff --git a/x.py b/x.py")["classification"] != "HARD_REJECT":
        errors.append("typed_contamination")
    allowlist = load("batch075_static_candidate_allowlist.json")
    candidates = allowlist.get("candidates", [])
    if len(candidates) > 3 or len(candidates) != allowlist.get("candidate_count") or any(not item.get("manual_review_required") or item.get("execution_authorized") for item in candidates):
        errors.append("batch075_allowlist")
    if allowlist.get("raw_issue_repair_instructions_included") or allowlist.get("patch_text_included") or allowlist.get("private_repository_information_included") or allowlist.get("secret_values_included"):
        errors.append("batch075_handoff_firewall")
    scope = load("batch075_execution_scope.json")
    if not scope.get("public_repositories_only") or not scope.get("software_tests_only") or scope.get("security_testing") or scope.get("vulnerability_research") or scope.get("exploit_work") or scope.get("credential_access") or scope.get("broad_discovery") or scope.get("maximum_repositories") != 3 or scope.get("repositories_executed_at_a_time") != 1 or not scope.get("manual_workflow_dispatch") or scope.get("patching_before_duplicate_failure_and_source_ownership"):
        errors.append("batch075_scope")
    final = load("batch074_final_decision.json")
    if final.get("status") != "LOCAL_IMPLEMENTATION_RECOVERY_COMPLETE" or final.get("external_prospective_cohort_execution") != "DEFERRED_TO_MANUALLY_REVIEWED_BATCH075" or final.get("prospective_candidate_wave_executed") or final.get("prospective_AMDS_evidence_created") or final.get("AMDS_PROSPECTIVE_EFFECTIVENESS") != "NOT_ESTABLISHED" or final.get("memory_lift") != "not_demonstrated" or final.get("issue_derived_repair_count") != 5 or final.get("native_external_repair_count") != 4:
        errors.append("final_recovery_boundary")
    workflow = (ROOT / ".github" / "workflows" / "post_v2_37_hardening_batch074_sterile_high_yield_amds_memory_wave1.yml").read_text(encoding="utf-8")
    forbidden_workflow = ("search/issues", "gh search issues", "gh api", "git clone", "pip wheel", "--artifact", "GH_TOKEN", "GITHUB_TOKEN")
    if any(value in workflow for value in forbidden_workflow):
        errors.append("workflow_external_operation")
    intake_text = "\n".join(path.read_text(encoding="utf-8") for path in sorted((ROOT / "controllergate" / "intake").glob("*.py")))
    if "prospective_yxyxy" in intake_text or "prospective_cognicore" in intake_text:
        errors.append("candidate_specific_universal_intake")
    ok, count = manifest_valid(OUT)
    if not ok or count != len([path for path in OUT.iterdir() if path.is_file()]) - 1:
        errors.append("sha256_manifest")
    if len([path for path in OUT.iterdir() if path.is_file()]) > 50:
        errors.append("evidence_compaction")
    print("Batch074 recovery audit:", "PASS" if not errors else "FAIL")
    if errors:
        print("errors:", ", ".join(errors))
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
