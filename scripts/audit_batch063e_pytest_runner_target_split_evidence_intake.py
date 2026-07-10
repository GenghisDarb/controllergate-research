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
from controllergate.core.runner_target_models import validate_runner_target_model

OUT_NAME = "post_v2_37_hardening_batch063e_pytest_runner_target_split_evidence_intake"
OUT_DIR = ROOT / "outputs" / OUT_NAME

REQUIRED_FILES = [
    "batch063d_artifact_ingestion_summary.json",
    "batch063d_artifact_sha256_verification.json",
    "batch063d_result_preservation.json",
    "batch063d_tag_authority_preservation.json",
    "batch063d_boundary_preservation.json",
    "pytest_version_origin_preservation_batch063e.json",
    "pytest_runner_target_model_registry_batch063e.json",
    "pytest_runner_target_model_decision_policy_batch063e.json",
    "pytest_runner_target_model_selection_batch063e.json",
    "pytest_runner_target_model_forbidden_shortcuts_batch063e.json",
    "pytest_project_local_test_metadata_inventory_batch063e.json",
    "pytest_project_local_command_authority_batch063e.json",
    "pytest_declared_self_testing_evidence_batch063e.json",
    "pytest_external_runner_metadata_evidence_batch063e.json",
    "pytest_command_source_authority_batch063e.json",
    "pytest_self_hosted_runner_probe_plan_batch063e.json",
    "pytest_self_hosted_runner_import_origin_probe_batch063e.py",
    "pytest_self_hosted_runner_import_origin_result_batch063e.json",
    "pytest_self_hosted_runner_command_manifest_batch063e.json",
    "pytest_external_runner_identity_plan_batch063e.json",
    "pytest_external_runner_provider_capsule_batch063e.json",
    "pytest_external_runner_import_origin_probe_batch063e.py",
    "pytest_external_runner_import_origin_result_batch063e.json",
    "pytest_external_runner_target_contact_probe_batch063e.json",
    "pytest_external_runner_command_manifest_batch063e.json",
    "pytest_runner_target_model_selection_result_batch063e.json",
    "pytest_pre_repair_replay_gate_batch063e.json",
    "pytest_pre_repair_replay_command_batch063e.json",
    "pytest_pre_repair_replay_log_batch063e.txt",
    "pytest_pre_repair_replay_result_batch063e.json",
    "pytest_command_boundary_final_status_batch063e.json",
    "pytest_runner_target_reward_signal_batch063e.json",
    "pytest_runner_target_blocker_reopen_condition_batch063e.json",
    "pytest_runner_target_parking_record_batch063e.json",
    "seed_harvest_authorization_after_batch063e_batch063e.json",
    "batch063e_final_decision.json",
    "batch063e_summary.md",
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
        expect(errors, "Batch063e evaluates Pytest runner-target import origin" in text, f"missing Batch063e public section in {rel}")
        hits = [term for term in FORBIDDEN_PUBLIC_TERMS if term.lower() in text.lower()]
        expect(errors, not hits, f"public doc {rel} contains forbidden internal terms: {hits}")
        expect(errors, audit_public_summary_text(text).get("status") == "PASS", f"public language audit failed for {rel}")


def main() -> int:
    errors: list[str] = []
    expect(errors, OUT_DIR.is_dir(), "missing Batch063e output directory")
    for rel in REQUIRED_FILES:
        expect(errors, (OUT_DIR / rel).is_file(), f"missing Batch063e output {rel}")
    for rel in [
        "controllergate/core/runner_target_models.py",
        "configs/pytest_runner_target_model_schema.json",
        "configs/runner_target_model_decision_policy.json",
    ]:
        expect(errors, (ROOT / rel).is_file(), f"missing Batch063e source/config {rel}")
    if errors:
        print("FAIL:")
        for error in errors:
            print(f"- {error}")
        return 1

    manifest = verify_manifest(OUT_DIR)
    expect(errors, manifest.get("status") == "PASS", f"SHA256SUMS failed: {manifest}")

    artifact = read_json("batch063d_artifact_sha256_verification.json")
    expect(errors, artifact.get("status") in {"PASS", "batch063d_artifact_absent_for_local_ingest"}, f"unexpected Batch063d artifact status {artifact.get('status')}")
    if artifact.get("status") == "PASS":
        expect(errors, artifact.get("outer", {}).get("size_bytes") == 53920, "Batch063d artifact size mismatch")
        expect(errors, artifact.get("outer", {}).get("sha256") == "940334f539d6cc7bdd81cc580e0f40c02df9bafc5acc25a5c8034194816f7b4f", "Batch063d artifact SHA mismatch")
        expect(errors, artifact.get("entries", {}).get("unsafe_path_count") == 0, "Batch063d unsafe artifact paths")
        expect(errors, artifact.get("entries", {}).get("duplicate_path_count") == 0, "Batch063d duplicate artifact paths")
        expect(errors, artifact.get("nested_archive_cache_venv_pyc_payload_count") == 0, "Batch063d nested/cache payloads")

    tag = read_json("batch063d_tag_authority_preservation.json")
    expect(errors, tag.get("status") == "PASS", "Batch063d tag authority not preserved")
    expect(errors, tag.get("safe_tag_authority_status") == "predeclared_ancestor_tag_authority_manifest_PASS", "safe tag authority status changed")
    expect(errors, tag.get("tag_authority_lifecycle_status") == "PASS", "tag authority lifecycle not preserved")
    expect(errors, tag.get("future_tag_refs_used") is False, "future tag refs used")
    expect(errors, tag.get("tag_source_bytes_read") is False, "tag source bytes read")
    expect(errors, tag.get("pytest_version_origin_status") == "pytest_version_origin_normalized_from_predeclared_ancestor_tag_authority", "version origin not preserved")

    boundary = read_json("batch063d_boundary_preservation.json")
    for key in ["patch_generated", "patch_applied", "duplicate_replay_run", "count_gate_run", "repair_count_increment"]:
        expect(errors, boundary.get(key) is False, f"Batch063d boundary {key} changed")

    registry = read_json("pytest_runner_target_model_registry_batch063e.json")
    models = registry.get("models", [])
    model_ids = {model.get("model_id") for model in models}
    expect(errors, {"declared_self_hosted_runner_model", "external_runner_target_split_model", "blocked_unproven_runner_target_model"}.issubset(model_ids), "runner-target registry missing required models")
    for model in models:
        expect(errors, validate_runner_target_model(model).get("status") == "PASS", f"runner-target model invalid: {model.get('model_id')}")

    metadata = read_json("pytest_project_local_test_metadata_inventory_batch063e.json")
    command = read_json("pytest_project_local_command_authority_batch063e.json")
    expect(errors, metadata.get("status") == "PASS", "metadata inventory did not pass")
    expect(errors, command.get("decision_time_safe") is True, "command authority not decision-time safe")
    expect(errors, command.get("declares_self_hosted_pytest_runner_pattern") is True, "self-hosted Pytest pattern not detected")
    expect(errors, command.get("declares_external_runner_requirement") is False, "unexpected external runner requirement declared")

    self_result = read_json("pytest_self_hosted_runner_import_origin_result_batch063e.json")
    external_result = read_json("pytest_external_runner_import_origin_result_batch063e.json")
    selection = read_json("pytest_runner_target_model_selection_result_batch063e.json")
    expect(errors, self_result.get("classification") in {"declared_self_hosted_runner_import_origin_proven", "declared_self_hosted_runner_unproven"}, "invalid self-hosted classification")
    expect(errors, external_result.get("classification") in {"external_runner_target_import_origin_proven", "external_runner_target_import_origin_unproven"}, "invalid external classification")
    expect(errors, external_result.get("external_runner_selected") is False, "blind external runner selected")
    expect(errors, selection.get("selected_model") in {"declared_self_hosted_runner_model", "external_runner_target_split_model", "blocked_unproven_runner_target_model"}, "invalid selected runner-target model")

    replay_gate = read_json("pytest_pre_repair_replay_gate_batch063e.json")
    replay = read_json("pytest_pre_repair_replay_result_batch063e.json")
    if selection.get("selected_model") == "blocked_unproven_runner_target_model":
        expect(errors, replay_gate.get("pre_repair_replay_allowed") is False, "replay allowed despite blocked model")
        expect(errors, replay.get("status") == "NOT_RUN", "replay ran despite blocked model")
        expect(errors, replay.get("classification") == "pytest_runner_target_model_unproven", "blocked replay classification mismatch")
    else:
        expect(errors, replay_gate.get("pre_repair_replay_allowed") is True, "proven model did not open replay gate")

    reward = read_json("pytest_runner_target_reward_signal_batch063e.json")
    expect(errors, reward.get("status") == "PASS", "reward signal missing/pass failed")
    expect(errors, reward.get("graded_signal") == 0.0, "reward signal should be zero")
    expect(errors, reward.get("repair_skill_memory_update_allowed") is False, "repair memory update allowed")
    expect(errors, reward.get("routing_memory_update_allowed") is True, "routing memory update not allowed")

    final = read_json("batch063e_final_decision.json")
    expect(errors, final.get("status") == "PASS", "final status not PASS")
    expect(errors, final.get("current_protocol") == "v2.14", "current protocol changed")
    expect(errors, final.get("issue_derived_repair_count") == 4, "issue-derived count changed")
    expect(errors, final.get("native_external_repair_count") == 4, "native external count changed")
    for key in ["patch_generated", "patch_applied", "source_mutated", "tests_mutated", "fixtures_mutated", "pyproject_mutated", "duplicate_replay_run", "count_gate_run", "repair_count_increment"]:
        expect(errors, final.get(key) is False, f"final expected {key}=false")
    expect(errors, final.get("full_scoring") == "NOT_RUN/disallowed", "full scoring changed")
    expect(errors, final.get("memory_lift") == "not_demonstrated", "memory lift changed")
    expect(errors, final.get("self_maintaining_software") == "false/not_demonstrated", "self-maintaining status changed")
    expect(errors, final.get("runner_target_model_selected") == selection.get("selected_model"), "final selected model mismatch")
    expect(errors, final.get("reward_signal_status") == "PASS", "final reward signal status not PASS")
    if final.get("runner_target_model_selected") == "blocked_unproven_runner_target_model":
        expect(errors, final.get("next_allowed_action") == "batch068_multi_seed_harvest_for_5th_issue_repair_with_batch067_063c_063d_063e_controls", "blocked model should authorize Batch068 harvest")
        expect(errors, final.get("seed_harvest_authorization_status") == "AUTHORIZED", "seed harvest not authorized for blocked model")
    else:
        expect(errors, final.get("next_allowed_action") == "batch063f_pytest_source_topology_and_patch_license_gate", "materialized model should progress to Batch063f")

    audit_public_docs(errors)
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
    print("Batch063e Pytest runner-target split evidence intake audit PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
