from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from controllergate.core.cognitive_state import validate_cognitive_state_snapshot
from controllergate.core.manifests import verify_manifest
from controllergate.core.public_summary import FORBIDDEN_PUBLIC_TERMS, audit_public_summary_text
from controllergate.core.reward_signal import validate_reward_signal

OUT_NAME = "post_v2_37_hardening_batch063c_pytest_command_boundary_followup"
OUT_DIR = ROOT / "outputs" / OUT_NAME

REQUIRED_FILES = [
    "batch067_artifact_ingestion_summary.json",
    "batch067_artifact_sha256_verification.json",
    "batch067_result_preservation.json",
    "batch067_module_status_preservation.json",
    "batch067_public_summary_preservation.json",
    "batch067_boundary_preservation.json",
    "s_engine_cognitive_state_snapshot_schema_batch063c.json",
    "s_engine_cognitive_state_snapshot_batch063c.json",
    "pre_generation_prompt_lock_policy_batch063c.json",
    "pre_generation_context_window_hash_batch063c.json",
    "pre_generation_ast_snippet_hash_batch063c.json",
    "pre_generation_state_timestamp_audit_batch063c.json",
    "cognitive_state_timestamp_inversion_blocker_batch063c.json",
    "retrocausal_reward_signal_schema_batch063c.json",
    "retrocausal_reward_signal_batch063c.json",
    "graded_repair_signal_policy_batch063c.json",
    "precondition_unavailable_signal_policy_batch063c.json",
    "near_threshold_patch_signal_policy_batch063c.json",
    "reward_signal_audit_batch063c.json",
    "baseline_registry_snapshot_schema_batch063c.json",
    "baseline_registry_snapshot_batch063c.json",
    "baseline_registry_drift_precheck_batch063c.json",
    "baseline_drift_blocking_acquisition_policy_batch063c.json",
    "locked_repair_environment_dependency_map_batch063c.json",
    "baseline_replay_dry_run_plan_batch063c.json",
    "baseline_registry_precheck_audit_batch063c.json",
    "cross_family_ast_homology_schema_batch063c.json",
    "cross_family_ast_homology_ledger_batch063c.json",
    "structural_memory_transfer_policy_batch063c.json",
    "homologous_repair_pattern_registry_batch063c.json",
    "ast_loop_extrusion_summary_batch063c.json",
    "homology_transfer_forbidden_use_audit_batch063c.json",
    "non_ansible_positive_memory_gap_analysis_batch063c.json",
    "pytest_batch063c_command_boundary_plan.json",
    "pytest_safe_tag_acquisition_decision.json",
    "pytest_version_origin_recheck_batch063c.json",
    "pytest_runner_target_import_origin_recheck_batch063c.json",
    "pytest_command_manifest_batch063c.json",
    "pytest_command_translation_decision_batch063c.json",
    "pytest_harness_origin_recheck_batch063c.json",
    "pytest_workspace_purity_recheck_batch063c.json",
    "pytest_provider_capsule_recheck_batch063c.json",
    "pytest_prerepair_replay_batch063c.json",
    "pytest_terminal_state_batch063c.json",
    "pytest_next_allowed_action_batch063c.json",
    "batch063c_final_decision.json",
    "batch063c_summary.md",
    "SHA256SUMS.txt",
]

REQUIRED_CORE = [
    "controllergate/core/cognitive_state.py",
    "controllergate/core/reward_signal.py",
    "controllergate/core/baseline_registry.py",
    "controllergate/core/ast_homology.py",
    "controllergate/core/cross_family_homology.py",
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
        expect(errors, "Batch063c applies the Batch067 wrapper infrastructure" in text, f"missing Batch063c public summary in {rel}")
        hits = [term for term in FORBIDDEN_PUBLIC_TERMS if term.lower() in text.lower()]
        expect(errors, not hits, f"public doc {rel} contains forbidden internal terms: {hits}")
        expect(errors, audit_public_summary_text(text).get("status") == "PASS", f"public guard failed for {rel}")


def main() -> int:
    errors: list[str] = []
    expect(errors, OUT_DIR.is_dir(), "missing Batch063c output directory")
    for rel in REQUIRED_FILES:
        expect(errors, (OUT_DIR / rel).is_file(), f"missing Batch063c output {rel}")
    for rel in REQUIRED_CORE:
        expect(errors, (ROOT / rel).is_file(), f"missing core module {rel}")
    if errors:
        print("FAIL:")
        for error in errors:
            print(f"- {error}")
        return 1

    manifest = verify_manifest(OUT_DIR)
    expect(errors, manifest.get("status") == "PASS", f"SHA256SUMS failed: {manifest}")

    artifact = read_json("batch067_artifact_sha256_verification.json")
    ingest = read_json("batch067_artifact_ingestion_summary.json")
    if artifact.get("status") == "batch067_artifact_absent_for_local_ingest":
        expect(errors, ingest.get("status") == "batch067_artifact_absent_for_local_ingest", "artifact absence inconsistent")
    else:
        expect(errors, artifact.get("status") == "PASS", "Batch067 artifact verification failed")
        expect(errors, artifact.get("outer", {}).get("size_bytes") == 47150, "Batch067 artifact size mismatch")
        expect(errors, artifact.get("outer", {}).get("sha256") == "4dbd09b3056b14726652ad23e46249efad3b4bf0f1608d77210ab366988f64d9", "Batch067 artifact SHA mismatch")
        expect(errors, artifact.get("entries", {}).get("unsafe_path_count") == 0, "Batch067 artifact unsafe paths")
        expect(errors, artifact.get("entries", {}).get("duplicate_path_count") == 0, "Batch067 artifact duplicate paths")
        expect(errors, artifact.get("nested_archive_cache_venv_pyc_payload_count") == 0, "Batch067 artifact nested/cache payloads")
        expect(errors, ingest.get("raw_zip_bytes_ingested") is False, "raw ZIP bytes ingested")

    batch067 = read_json("batch067_result_preservation.json")
    expect(errors, batch067.get("next_allowed_action") == "batch063c_pytest_command_boundary_followup", "Batch067 did not allow Batch063c")
    expect(errors, batch067.get("issue_derived_repair_count") == 4, "Batch067 issue-derived count not preserved")
    expect(errors, batch067.get("native_external_repair_count") == 4, "Batch067 native count not preserved")
    boundary = read_json("batch067_boundary_preservation.json")
    for key in ["patch_generated", "patch_applied", "duplicate_replay_run", "count_gate_run", "repair_count_increment"]:
        expect(errors, boundary.get(key) is False, f"Batch067 boundary {key} not false")

    snapshot = read_json("s_engine_cognitive_state_snapshot_batch063c.json")
    snapshot_audit = read_json("pre_generation_state_timestamp_audit_batch063c.json")
    expect(errors, validate_cognitive_state_snapshot(snapshot).get("status") == "PASS", "cognitive-state snapshot invalid")
    expect(errors, snapshot_audit.get("status") == "PASS", "cognitive-state timestamp audit failed")
    expect(errors, snapshot.get("snapshot_written_before_generation") is True, "snapshot not written before generation")
    expect(errors, snapshot.get("generation_output_exists_at_snapshot_time") is False, "generation output existed at snapshot time")

    reward = read_json("retrocausal_reward_signal_batch063c.json")
    reward_audit = read_json("reward_signal_audit_batch063c.json")
    expect(errors, validate_reward_signal(reward).get("status") == "PASS", "reward signal invalid")
    expect(errors, reward_audit.get("status") == "PASS", "reward signal audit failed")
    expect(errors, reward.get("graded_signal") == 0.0 and reward.get("precondition_unavailable") is True, "precondition signal not zero")
    expect(errors, reward.get("memory_update_forbidden_reason") == "repair_skill_memory_forbidden_routing_abstention_only", "precondition memory boundary invalid")

    baseline = read_json("baseline_registry_drift_precheck_batch063c.json")
    expect(errors, baseline.get("classification") == "baseline_drift_precheck_PASS_isolated_runtime", "baseline precheck did not pass isolated runtime")
    for record in baseline.get("records", []):
        expect(errors, record.get("drift_detected") is False, f"baseline drift detected for {record.get('baseline_record_id')}")
        expect(errors, record.get("acquisition_allowed") is True, f"acquisition blocked for {record.get('baseline_record_id')}")

    homology = read_json("cross_family_ast_homology_ledger_batch063c.json")
    expect(errors, homology.get("status") == "PASS", "AST homology ledger did not pass")
    expect(errors, homology.get("routing_memory_only") is True, "AST homology not routing-only")
    for record in homology.get("records", []):
        expect(errors, record.get("patch_authority_allowed") is False, "homology used as patch authority")
        expect(errors, record.get("count_gate_evidence_allowed") is False, "homology used as count evidence")
        expect(errors, record.get("memory_lift_evidence_allowed") is False, "homology used as memory-lift evidence")

    pytest_tag = read_json("pytest_safe_tag_acquisition_decision.json")
    pytest_runner = read_json("pytest_runner_target_import_origin_recheck_batch063c.json")
    pytest_cmd = read_json("pytest_command_translation_decision_batch063c.json")
    prerepair = read_json("pytest_prerepair_replay_batch063c.json")
    expect(errors, pytest_tag.get("safe_tag_acquisition_executed") is False, "safe tag acquisition unexpectedly executed")
    expect(errors, pytest_tag.get("future_tag_exposure_avoided") is True, "future tag exposure not avoided")
    expect(errors, pytest_runner.get("classification") == "runner_target_collision_unresolved_self_runner", "runner-target collision not preserved")
    expect(errors, pytest_cmd.get("no_minversion_suppression") is True, "minversion suppression detected")
    expect(errors, pytest_cmd.get("no_blind_external_runner") is True, "blind external runner detected")
    expect(errors, prerepair.get("status") == "NOT_RUN" and prerepair.get("target_failure_materialized") is False, "pre-repair replay should not run while version-origin blocked")

    final = read_json("batch063c_final_decision.json")
    expect(errors, final.get("status") == "PASS", "final status not PASS")
    expect(errors, final.get("issue_derived_repair_count") == 4, "issue-derived count changed")
    expect(errors, final.get("native_external_repair_count") == 4, "native external count changed")
    for key in ["patch_generated", "patch_applied", "source_mutated", "tests_mutated", "fixtures_mutated", "pyproject_mutated", "duplicate_replay_run", "count_gate_run", "repair_count_increment"]:
        expect(errors, final.get(key) is False, f"final expected {key}=false")
    expect(errors, final.get("full_scoring") == "NOT_RUN/disallowed", "full scoring changed")
    expect(errors, final.get("memory_lift") == "not_demonstrated", "memory lift changed")
    expect(errors, final.get("self_maintaining_software") == "false/not_demonstrated", "self-maintaining status changed")
    expect(errors, final.get("pytest_version_origin_status") == "pytest_version_origin_missing_tags", "version-origin final status changed")
    expect(errors, final.get("pytest_command_boundary_status") == "pytest_command_boundary_blocked_version_origin", "command-boundary final status changed")
    expect(errors, final.get("pytest_prerepair_replay_status") == "NOT_RUN_blocked_version_origin_missing_tags_safe_tag_authority_absent", "pre-repair final status changed")
    expect(errors, final.get("next_allowed_action") == "batch063d_pytest_safe_tag_acquisition_hardening", "next action not safe tag hardening")
    expect(errors, final.get("exact_blocker") == "pytest_version_origin_missing_tags_command_boundary", "exact blocker changed")

    audit_public_docs(errors)
    run_check([sys.executable, "scripts/audit_batch067_universal_wrapper_hardening_implementation.py"], errors, "Batch067 audit")
    run_check([sys.executable, "scripts/controllergate_audit.py", "--protocol", "current"], errors, "current protocol audit")
    run_check([sys.executable, "scripts/controllergate_run.py", "--protocol", "current", "--dry-run"], errors, "current protocol dry-run")

    if errors:
        print("FAIL:")
        for error in errors:
            print(f"- {error}")
        return 1
    print("Batch063c Pytest command-boundary follow-up audit PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
