from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from controllergate.core.manifests import verify_manifest
from controllergate.core.public_summary import FORBIDDEN_PUBLIC_TERMS, audit_public_summary_text
from controllergate.core.tag_authority import validate_tag_authority_record

OUT_NAME = "post_v2_37_hardening_batch063d_pytest_safe_tag_acquisition_hardening"
OUT_DIR = ROOT / "outputs" / OUT_NAME

REQUIRED_FILES = [
    "batch063c_artifact_sha256_verification_batch063d.json",
    "batch063c_artifact_ingestion_boundary_batch063d.json",
    "batch063c_artifact_evidence_reconciliation_batch063d.json",
    "artifact_evidence_reconciliation_status_batch063d.json",
    "batch063c_result_preservation_batch063d.json",
    "batch067_result_preservation_batch063d.json",
    "safe_tag_authority_model_batch063d.json",
    "pytest_ancestor_tag_authority_plan_batch063d.json",
    "pytest_tag_ref_exposure_policy_batch063d.json",
    "pytest_tag_acquisition_preflight_batch063d.json",
    "pytest_tag_authority_decision_batch063d.json",
    "pytest_reachable_tag_set_batch063d.json",
    "pytest_future_tag_exposure_audit_batch063d.json",
    "baseline_registry_pre_tag_acquisition_snapshot_batch063d.json",
    "baseline_registry_pre_tag_acquisition_drift_check_batch063d.json",
    "tag_acquisition_isolated_runtime_proof_batch063d.json",
    "pytest_candidate_workspace_tag_acquisition_log_batch063d.txt",
    "pytest_setuptools_scm_before_after_batch063d.json",
    "pytest_version_origin_normalization_result_batch063d.json",
    "pytest_version_origin_terminal_state_batch063d.json",
    "pytest_runner_target_split_plan_batch063d.json",
    "pytest_runner_target_import_origin_probe_batch063d.json",
    "pytest_external_runner_selection_decision_batch063d.json",
    "pytest_runner_target_import_origin_result_batch063d.json",
    "pytest_command_manifest_batch063d.json",
    "pytest_harness_origin_batch063d.json",
    "pytest_workspace_purity_batch063d.json",
    "pytest_provider_capsule_batch063d.json",
    "pytest_prerepair_replay_batch063d.json",
    "pytest_prerepair_replay_log_batch063d.txt",
    "pytest_command_boundary_final_classification_batch063d.json",
    "pytest_blocker_reopen_condition_batch063d.json",
    "pytest_blocker_parking_record_batch063d.json",
    "seed_harvest_authorization_after_pytest_block_batch063d.json",
    "multi_seed_harvest_readiness_plan_batch063d.json",
    "fifth_issue_repair_seed_requirements_batch063d.json",
    "seed_source_approval_contract_batch063d.json",
    "seed_inventory_minimum_viable_batch068_contract.json",
    "pytest_tag_authority_lifecycle_policy_batch063d.json",
    "pytest_tag_authority_discovery_transcript_batch063d.txt",
    "pytest_tag_authority_discovery_hash_batch063d.json",
    "pytest_tag_metadata_custody_manifest_batch063d.json",
    "pytest_ancestor_only_tag_filter_result_batch063d.json",
    "pytest_predeclared_ancestor_tag_authority_manifest_batch063d.json",
    "pytest_predeclared_ancestor_tag_authority_manifest.sha256",
    "pytest_tag_authority_self_audit_batch063d.json",
    "pytest_tag_authority_use_decision_batch063d.json",
    "pytest_version_origin_recheck_from_frozen_tag_manifest_batch063d.json",
    "batch063d_final_decision.json",
    "batch063d_summary.md",
    "SHA256SUMS.txt",
]


def read_json(name: str) -> dict[str, object]:
    return json.loads((OUT_DIR / name).read_text(encoding="utf-8"))


def expect(errors: list[str], condition: bool, message: str) -> None:
    if not condition:
        errors.append(message)


def run_check(args: list[str], errors: list[str], label: str) -> None:
    proc = subprocess.run(args, cwd=ROOT, text=True, capture_output=True, check=False)
    expect(errors, proc.returncode == 0, f"{label} failed: {proc.stdout[-1200:]} {proc.stderr[-1200:]}")


def audit_public_docs(errors: list[str]) -> None:
    for rel in [
        "README.md",
        "docs/current_status.md",
        "controllergate_v1_7_beta/reports/critic_review_package/shareable_summary.md",
    ]:
        text = (ROOT / rel).read_text(encoding="utf-8")
        expect(errors, "Batch063d adds a predeclared ancestor-tag authority lifecycle" in text, f"missing Batch063d public section in {rel}")
        hits = [term for term in FORBIDDEN_PUBLIC_TERMS if term.lower() in text.lower()]
        expect(errors, not hits, f"public doc {rel} contains forbidden internal terms: {hits}")
        expect(errors, audit_public_summary_text(text).get("status") == "PASS", f"public language audit failed for {rel}")


def main() -> int:
    errors: list[str] = []
    expect(errors, OUT_DIR.is_dir(), "missing Batch063d output directory")
    for rel in REQUIRED_FILES:
        expect(errors, (OUT_DIR / rel).is_file(), f"missing Batch063d output {rel}")
    for rel in [
        "controllergate/core/tag_authority.py",
        "configs/safe_tag_authority_schema.json",
        "configs/ancestor_tag_authority_policy.json",
    ]:
        expect(errors, (ROOT / rel).is_file(), f"missing Batch063d source/config {rel}")
    if errors:
        print("FAIL:")
        for error in errors:
            print(f"- {error}")
        return 1

    manifest = verify_manifest(OUT_DIR)
    expect(errors, manifest.get("status") == "PASS", f"SHA256SUMS failed: {manifest}")

    artifact = read_json("batch063c_artifact_sha256_verification_batch063d.json")
    reconciliation = read_json("batch063c_artifact_evidence_reconciliation_batch063d.json")
    expect(
        errors,
        reconciliation.get("status")
        in {
            "PASS",
            "committed_vs_workflow_artifact_ingest_status_divergence_recorded",
            "batch063c_artifact_absent_for_local_reconciliation",
        },
        f"unexpected artifact reconciliation status {reconciliation.get('status')}",
    )
    if artifact.get("status") not in {"batch063c_artifact_absent_for_local_reconciliation", "PASS"}:
        errors.append(f"Batch063c artifact verification failed: {artifact.get('status')}")
    if artifact.get("status") == "PASS":
        expect(errors, artifact.get("outer", {}).get("size_bytes") == 26318, "Batch063c artifact size mismatch")
        expect(errors, artifact.get("outer", {}).get("sha256") == "99bf40cfed72485c94fcb989ef5b1d882c01f4b210058495c6014907ef6ffd30", "Batch063c artifact SHA mismatch")
        expect(errors, artifact.get("entries", {}).get("unsafe_path_count") == 0, "Batch063c artifact unsafe paths")
        expect(errors, artifact.get("entries", {}).get("duplicate_path_count") == 0, "Batch063c artifact duplicate paths")

    batch063c = read_json("batch063c_result_preservation_batch063d.json")
    batch067 = read_json("batch067_result_preservation_batch063d.json")
    expect(errors, batch063c.get("next_allowed_action") == "batch063d_pytest_safe_tag_acquisition_hardening", "Batch063c next action not preserved")
    expect(errors, batch063c.get("patch_generated") is False, "Batch063c patch boundary not preserved")
    expect(errors, batch067.get("issue_derived_repair_count") == 4, "Batch067 issue-derived count not preserved")
    expect(errors, batch067.get("native_external_repair_count") == 4, "Batch067 native count not preserved")

    baseline = read_json("baseline_registry_pre_tag_acquisition_drift_check_batch063d.json")
    expect(errors, baseline.get("classification") == "baseline_pre_tag_acquisition_PASS", "baseline pre-tag acquisition did not pass")
    runtime = read_json("tag_acquisition_isolated_runtime_proof_batch063d.json")
    expect(errors, runtime.get("controllergate_repo_mutated") is False, "ControllerGate repo mutated by tag acquisition")
    expect(errors, runtime.get("global_environment_mutated") is False, "global environment mutated by tag acquisition")

    metadata = read_json("pytest_tag_metadata_custody_manifest_batch063d.json")
    ancestor_filter = read_json("pytest_ancestor_only_tag_filter_result_batch063d.json")
    tag_manifest = read_json("pytest_predeclared_ancestor_tag_authority_manifest_batch063d.json")
    self_audit = read_json("pytest_tag_authority_self_audit_batch063d.json")
    use_decision = read_json("pytest_tag_authority_use_decision_batch063d.json")
    version_recheck = read_json("pytest_version_origin_recheck_from_frozen_tag_manifest_batch063d.json")
    for label, record in [
        ("metadata", metadata),
        ("ancestor_filter", ancestor_filter),
        ("tag_manifest", tag_manifest),
        ("self_audit", self_audit),
        ("use_decision", use_decision),
        ("version_recheck", version_recheck),
    ]:
        expect(errors, record.get("tag_source_bytes_read") is not True, f"{label} read tag source bytes")
        expect(errors, record.get("future_tag_refs_used") is not True, f"{label} used future tag refs")
    expect(errors, tag_manifest.get("manifest_created_before_version_recheck") is True, "tag manifest not created before version recheck")
    expect(errors, tag_manifest.get("allowed_use") == "version_origin_reconstruction_only", "tag manifest allowed use changed")
    expect(errors, "patch_authority" in tag_manifest.get("forbidden_use", []), "tag manifest does not forbid patch authority")
    expect(errors, read_json("pytest_future_tag_exposure_audit_batch063d.json").get("future_tag_refs_used") is False, "future tag refs used")

    final = read_json("batch063d_final_decision.json")
    expect(errors, final.get("status") == "PASS", "final status not PASS")
    expect(errors, final.get("current_protocol") == "v2.14", "current protocol changed")
    expect(errors, final.get("issue_derived_repair_count") == 4, "issue-derived count changed")
    expect(errors, final.get("native_external_repair_count") == 4, "native external count changed")
    for key in ["patch_generated", "patch_applied", "source_mutated", "tests_mutated", "fixtures_mutated", "pyproject_mutated", "duplicate_replay_run", "count_gate_run", "repair_count_increment"]:
        expect(errors, final.get(key) is False, f"final expected {key}=false")
    expect(errors, final.get("full_scoring") == "NOT_RUN/disallowed", "full scoring changed")
    expect(errors, final.get("memory_lift") == "not_demonstrated", "memory lift changed")
    expect(errors, final.get("self_maintaining_software") == "false/not_demonstrated", "self-maintaining status changed")
    expect(errors, final.get("tag_source_bytes_read") is False, "final tag_source_bytes_read not false")
    expect(errors, final.get("future_tag_refs_used") is False, "final future_tag_refs_used not false")
    expect(errors, final.get("pytest_prerepair_replay_status", "").startswith("NOT_RUN"), "pre-repair replay should not run in Batch063d")
    expect(errors, final.get("next_allowed_action") in {"batch063e_pytest_tag_authority_evidence_intake", "batch063e_pytest_runner_target_split_evidence_intake", "batch068_multi_seed_harvest_for_5th_issue_repair_with_batch067_063c_controls"}, "unexpected next action")

    if final.get("safe_tag_authority_status") == "predeclared_ancestor_tag_authority_manifest_PASS":
        expect(errors, final.get("tag_authority_lifecycle_status") == "PASS", "tag authority lifecycle did not pass with safe manifest")
        expect(errors, ancestor_filter.get("reachable_ancestor_tag_count", 0) > 0, "safe manifest had no reachable ancestor tags")
        expect(errors, self_audit.get("status") == "PASS", "tag self-audit failed")
        tag_record = self_audit.get("tag_authority_record", {})
        expect(errors, validate_tag_authority_record(tag_record).get("status") == "PASS", "tag authority record invalid")
        expect(errors, final.get("pytest_version_origin_status") == "pytest_version_origin_normalized_from_predeclared_ancestor_tag_authority", "version origin did not normalize from safe manifest")
        expect(errors, final.get("version_origin_recheck_from_frozen_manifest_status") == "PASS", "frozen manifest version recheck failed")
        expect(errors, final.get("next_allowed_action") == "batch063e_pytest_runner_target_split_evidence_intake", "safe manifest should progress to runner-target evidence intake")
    else:
        expect(errors, final.get("tag_authority_lifecycle_status") == "BLOCK", "blocked safe tag authority did not record BLOCK lifecycle")
        expect(errors, final.get("pytest_version_origin_status") != "pytest_version_origin_normalized_from_predeclared_ancestor_tag_authority", "blocked authority cannot normalize version origin")

    audit_public_docs(errors)
    run_check([sys.executable, "scripts/audit_batch063c_pytest_command_boundary_followup.py"], errors, "Batch063c audit")
    run_check([sys.executable, "scripts/audit_batch067_universal_wrapper_hardening_implementation.py"], errors, "Batch067 audit")
    run_check([sys.executable, "scripts/controllergate_audit.py", "--protocol", "current"], errors, "current protocol audit")
    run_check([sys.executable, "scripts/controllergate_run.py", "--protocol", "current", "--dry-run"], errors, "current protocol dry-run")

    if errors:
        print("FAIL:")
        for error in errors:
            print(f"- {error}")
        return 1
    print("Batch063d Pytest safe tag acquisition hardening audit PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
