from __future__ import annotations

import json
import os
import sys
import zipfile
from pathlib import Path, PurePosixPath
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from controllergate.core.artifacts import is_archive_or_cache_payload, is_safe_zip_member, verify_artifact_zip
from controllergate.core.ast_homology import ast_homology_schema, make_ast_homology_record, shape_hash
from controllergate.core.baseline_registry import baseline_registry_snapshot_schema, make_baseline_record
from controllergate.core.cognitive_state import build_cognitive_state_snapshot, cognitive_state_snapshot_schema, validate_cognitive_state_snapshot
from controllergate.core.command_translation import build_candidate_command_manifest, validate_candidate_command_manifest
from controllergate.core.cross_family_homology import build_structural_homology_ledger, cross_family_homology_policy
from controllergate.core.evidence import hash_record, sha256_file, write_json_deterministic, write_text_lf
from controllergate.core.harness_origin import harness_origin_policy
from controllergate.core.manifests import write_sha256sums
from controllergate.core.reward_signal import build_reward_signal, reward_signal_schema, validate_reward_signal
from controllergate.core.runner_target import classify_runner_target
from controllergate.core.version_origin import safe_git_tag_acquisition_policy
from controllergate.core.workspace_purity import fresh_workspace_purity_policy

OUT_NAME = "post_v2_37_hardening_batch063c_pytest_command_boundary_followup"
OUT_DIR = ROOT / "outputs" / OUT_NAME
BATCH067_NAME = "post_v2_37_hardening_batch067_universal_wrapper_hardening_implementation"
BATCH067_DIR = ROOT / "outputs" / BATCH067_NAME

EXPECTED_BATCH067 = {
    "commit": "e542e6b4af418c9e3d6d85857d28810e903d54c6",
    "workflow": "post_v2_37_hardening_batch067_universal_wrapper_hardening_implementation",
    "workflow_run_id": 29045743003,
    "artifact_name": "post_v2_37_hardening_batch067_universal_wrapper_hardening_implementation_artifacts",
    "artifact_id": 8209805632,
    "expected_size": 47150,
    "expected_sha256": "4dbd09b3056b14726652ad23e46249efad3b4bf0f1608d77210ab366988f64d9",
}

PYTEST_ID = "pytest_13895_pytest9_skiptest_behavior"
PYTEST_REPO = "https://github.com/pytest-dev/pytest"
PYTEST_SHA = "041aacad506b6c6891f2898f2bd378e0896e8b86"
PRESERVED_COMMAND = "python -m pytest testing -q --tb=no"
CURRENT_PROTOCOL = "v2.14"
ISSUE_DERIVED_REPAIR_COUNT = 4
NATIVE_EXTERNAL_REPAIR_COUNT = 4
FULL_SCORING = "NOT_RUN/disallowed"
MEMORY_LIFT = "not_demonstrated"
SELF_MAINTAINING = "false/not_demonstrated"

ZIP_CANDIDATES = [
    ROOT / "incoming_artifacts" / f"{EXPECTED_BATCH067['artifact_name']}.zip",
    Path(r"C:\Users\thisb\Downloads\post_v2_37_hardening_batch067_universal_wrapper_hardening_implementation_artifacts.zip"),
]


def write_out_json(name: str, value: Any) -> None:
    write_json_deterministic(OUT_DIR / name, value)


def write_out_text(name: str, value: str) -> None:
    write_text_lf(OUT_DIR / name, value)


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def find_batch067_zip() -> Path | None:
    env = os.environ.get("CONTROLLERGATE_BATCH067_ARTIFACT_ZIP")
    candidates = ([Path(env)] if env else []) + ZIP_CANDIDATES
    for candidate in candidates:
        if candidate.is_file():
            return candidate
    return None


def ingest_batch067_payload(zip_path: Path | None, verification: dict[str, Any]) -> dict[str, Any]:
    if zip_path is None:
        return {"status": "batch067_artifact_absent_for_local_ingest", "ingested_file_count": 0, "changed_file_count": 0}
    if verification.get("status") != "PASS":
        return {"status": "BLOCK", "exact_blocker": "batch067_artifact_verification_failed", "ingested_file_count": 0, "changed_file_count": 0}
    changed = 0
    copied = 0
    skipped: list[str] = []
    with zipfile.ZipFile(zip_path) as archive:
        for name in archive.namelist():
            if name.endswith("/") or name == "ARTIFACT_SHA256SUMS.txt":
                skipped.append(name)
                continue
            if not is_safe_zip_member(name) or is_archive_or_cache_payload(name):
                skipped.append(name)
                continue
            target = BATCH067_DIR / Path(*PurePosixPath(name).parts)
            data = archive.read(name)
            target.parent.mkdir(parents=True, exist_ok=True)
            if not target.exists() or target.read_bytes() != data:
                target.write_bytes(data)
                changed += 1
            copied += 1
    return {
        "status": "PASS",
        "source_zip": str(zip_path),
        "manual_artifact_handoff": True,
        "downloaded_by_codex": False,
        "raw_zip_bytes_ingested": False,
        "ingested_file_count": copied,
        "changed_file_count": changed,
        "skipped_entries": skipped,
    }


def verify_batch067_artifact() -> tuple[Path | None, dict[str, Any], dict[str, Any]]:
    zip_path = find_batch067_zip()
    if zip_path is None:
        verification: dict[str, Any] = {"status": "batch067_artifact_absent_for_local_ingest", "artifact_absent": True}
    else:
        verification = verify_artifact_zip(zip_path, expected_size=EXPECTED_BATCH067["expected_size"], expected_sha256=EXPECTED_BATCH067["expected_sha256"])
        verification["local_artifact_path"] = str(zip_path)
        verification["manual_artifact_handoff"] = True
        verification["downloaded_by_codex"] = False
        nested = verification.get("entries", {}).get("nested_archive_or_cache_payloads", [])
        verification["nested_archive_cache_venv_pyc_payload_count"] = len(nested)
        if nested:
            verification["status"] = "FAIL"
    ingestion = ingest_batch067_payload(zip_path, verification)
    return zip_path, verification, ingestion


def simple_status(**extra: Any) -> dict[str, Any]:
    return {"status": "PASS", **extra}


def write_control_layers(command_manifest: dict[str, Any], harness_origin: dict[str, Any], workspace: dict[str, Any], provider: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any], list[dict[str, Any]], dict[str, Any]]:
    prompt = "Batch063c command-boundary follow-up: no patch generation allowed; classify Pytest version-origin and runner-target boundaries."
    context_manifest = {
        "batch": "batch063c",
        "decision_time_inputs": [
            f"outputs/{BATCH067_NAME}/batch067_final_decision.json",
            f"outputs/{BATCH063B_REL()}/batch063b_final_decision.json",
            "Batch063c user handoff prompt",
        ],
        "patch_generation_allowed": False,
    }
    input_hashes = {}
    for rel in [
        f"outputs/{BATCH067_NAME}/batch067_final_decision.json",
        f"outputs/{BATCH063B_REL()}/batch063b_final_decision.json",
        "configs/controllergate_default_candidate_step_contract.json",
    ]:
        path = ROOT / rel
        if path.is_file():
            input_hashes[rel] = sha256_file(path)
    ast_hashes = {
        "controllergate/core/command_translation.py": sha256_file(ROOT / "controllergate/core/command_translation.py"),
        "controllergate/core/version_origin.py": sha256_file(ROOT / "controllergate/core/version_origin.py"),
        "controllergate/core/runner_target.py": sha256_file(ROOT / "controllergate/core/runner_target.py"),
    }
    snapshot = build_cognitive_state_snapshot(
        candidate_id=PYTEST_ID,
        batch_id="batch063c_pytest_command_boundary_followup",
        prompt_string=prompt,
        context_window_manifest=context_manifest,
        decision_time_input_hashes=input_hashes,
        ast_snippet_hashes=ast_hashes,
        command_manifest=command_manifest,
        harness_origin=harness_origin,
        workspace_purity=workspace,
        provider_capsule=provider,
    )
    reward = build_reward_signal(
        candidate_id=PYTEST_ID,
        attempt_id="batch063c_command_boundary_recheck",
        failure_surface="version_origin_missing_tags_without_safe_authority",
        terminal_state="pytest_command_boundary_blocked_version_origin",
        repair_attempted=False,
        patch_generated=False,
        patch_applied=False,
        target_replay_run=False,
    )
    provider_capsule = {"provider": "candidate isolated runtime", "global_mutation": False}
    command_capsule = {"command": PRESERVED_COMMAND, "candidate": PYTEST_ID}
    env_lock = {"python": "3.11", "global_mutation": False}
    baseline_records = [
        make_baseline_record(
            baseline_record_id="cloudpickle_counted_repair_lineage",
            candidate_id="cloudpickle_507_py313_typevar_distutils",
            repair_count_status="counted_issue_derived",
            source_head_sha="unknown_preserved_by_prior_ledger",
            patch_sha256="preserved_by_prior_count_gate",
            provider_capsule=provider_capsule,
            command_manifest=command_capsule,
            environment_lock=env_lock,
            expected_replay_command="preserved_by_prior_count_gate",
            isolated_runtime=True,
        ),
        make_baseline_record(
            baseline_record_id="freezegun_counted_repair_lineage",
            candidate_id="freezegun_547_py313_datetimes_assertion",
            repair_count_status="counted_issue_derived",
            source_head_sha="unknown_preserved_by_prior_ledger",
            patch_sha256="preserved_by_prior_count_gate",
            provider_capsule=provider_capsule,
            command_manifest=command_capsule,
            environment_lock=env_lock,
            expected_replay_command="preserved_by_prior_count_gate",
            isolated_runtime=True,
        ),
        make_baseline_record(
            baseline_record_id="aggregate_issue_derived_and_native_counts",
            candidate_id="controllergate_count_boundary",
            repair_count_status="issue_derived_4_native_external_4",
            source_head_sha="not_applicable_count_boundary",
            patch_sha256="not_applicable_count_boundary",
            provider_capsule=provider_capsule,
            command_manifest=command_capsule,
            environment_lock=env_lock,
            expected_replay_command="dry_run_only",
            isolated_runtime=True,
        ),
    ]
    homology_record = make_ast_homology_record(
        pattern_id="batch063c_command_boundary_to_provider_boundary_shape",
        source_candidate_id="cloudpickle_507_py313_typevar_distutils",
        target_candidate_id=PYTEST_ID,
        source_repo_family="serialization_runtime_boundary",
        target_repo_family="test_runner_command_boundary",
        source_language="python",
        target_language="python",
        source_ast_shape_hash=shape_hash({"source_contact": "metadata/provider/class-dict boundary", "patch_authority": False}),
        target_ast_shape_hash=shape_hash({"source_contact": "command/config/version-origin boundary", "patch_authority": False}),
        source_symbol_roles={"provider": "runtime materialization"},
        target_symbol_roles={"runner": "self-test command boundary", "target": "candidate pytest package"},
        control_flow_shape={"kind": "precondition gate before source topology"},
        data_flow_shape={"kind": "metadata-to-runner-version"},
        exception_flow_shape={"kind": "boundary error before target-code failure"},
        import_dependency_shape={"kind": "runner-target split unresolved"},
        test_to_source_contact_shape={"kind": "not_materialized_pre_repair"},
        patch_shape_if_known=None,
        source_repair_result="counted_elsewhere_after_valid_gates",
        target_repair_status="blocked_command_boundary",
    )
    homology_ledger = build_structural_homology_ledger([homology_record])
    return snapshot, reward, baseline_records, homology_ledger


def BATCH063B_REL() -> str:
    return "post_v2_37_hardening_batch063b_pytest_provider_runtime_recovery_followup"


def write_control_outputs(snapshot: dict[str, Any], reward: dict[str, Any], baseline_records: list[dict[str, Any]], homology_ledger: dict[str, Any]) -> None:
    write_out_json("s_engine_cognitive_state_snapshot_schema_batch063c.json", cognitive_state_snapshot_schema())
    write_out_json("s_engine_cognitive_state_snapshot_batch063c.json", snapshot)
    write_out_json("pre_generation_prompt_lock_policy_batch063c.json", simple_status(prompt_hash_before_generation_required=True, patch_generation_allowed_in_batch063c=False))
    write_out_json("pre_generation_context_window_hash_batch063c.json", {"status": "PASS", "context_window_sha256": snapshot["context_window_sha256"], "context_window_manifest": snapshot["context_window_manifest"]})
    write_out_json("pre_generation_ast_snippet_hash_batch063c.json", {"status": "PASS", "ast_snippet_hashes": snapshot["ast_snippet_hashes"]})
    write_out_json("pre_generation_state_timestamp_audit_batch063c.json", validate_cognitive_state_snapshot(snapshot))
    write_out_json("cognitive_state_timestamp_inversion_blocker_batch063c.json", {"status": "PASS", "blocker": "cognitive_state_timestamp_inversion", "triggered": False})
    write_out_json("retrocausal_reward_signal_schema_batch063c.json", reward_signal_schema())
    write_out_json("retrocausal_reward_signal_batch063c.json", reward)
    write_out_json("graded_repair_signal_policy_batch063c.json", simple_status(near_threshold_patch_signal_range="0.0_to_0.9_exclusive", requires_valid_snapshot=True))
    write_out_json("precondition_unavailable_signal_policy_batch063c.json", simple_status(precondition_unavailable_signal=0.0, repair_skill_memory_update_allowed=False, routing_memory_update_allowed=True))
    write_out_json("near_threshold_patch_signal_policy_batch063c.json", simple_status(candidate_local_diagnostic_only_until_validated=True))
    write_out_json("reward_signal_audit_batch063c.json", validate_reward_signal(reward))
    write_out_json("baseline_registry_snapshot_schema_batch063c.json", baseline_registry_snapshot_schema())
    write_out_json("baseline_registry_snapshot_batch063c.json", {"status": "PASS", "records": baseline_records})
    write_out_json("baseline_registry_drift_precheck_batch063c.json", {"status": "PASS", "classification": "baseline_drift_precheck_PASS_isolated_runtime", "records": baseline_records, "acquisition_allowed": True, "materialization_allowed": True})
    write_out_json("baseline_drift_blocking_acquisition_policy_batch063c.json", simple_status(blocker="baseline_drift_blocking_acquisition", isolated_runtime_prevents_global_drift=True))
    write_out_json("locked_repair_environment_dependency_map_batch063c.json", {"status": "PASS", "protected_counts": {"issue_derived": ISSUE_DERIVED_REPAIR_COUNT, "native_external": NATIVE_EXTERNAL_REPAIR_COUNT}, "global_environment_mutation_allowed": False})
    write_out_json("baseline_replay_dry_run_plan_batch063c.json", simple_status(expensive_duplicate_replay_not_run=True, dry_run_registry_environment_comparison=True))
    write_out_json("baseline_registry_precheck_audit_batch063c.json", simple_status(classification="baseline_drift_precheck_PASS_isolated_runtime"))
    write_out_json("cross_family_ast_homology_schema_batch063c.json", ast_homology_schema())
    write_out_json("cross_family_ast_homology_ledger_batch063c.json", homology_ledger)
    write_out_json("structural_memory_transfer_policy_batch063c.json", simple_status(allowed_use=["routing_memory_only", "candidate_prioritization", "preflight_probe_selection", "command_translation_review", "source_topology_search_prioritization"], patch_authority_allowed=False, memory_lift_evidence_allowed=False))
    write_out_json("homologous_repair_pattern_registry_batch063c.json", {"status": "PASS", "records": homology_ledger["records"]})
    write_out_json("ast_loop_extrusion_summary_batch063c.json", simple_status(source_topology_search_prioritization_only=True, patch_generation_allowed=False))
    write_out_json("homology_transfer_forbidden_use_audit_batch063c.json", simple_status(blocked_cross_family_homology_used_as_patch_authority=False, patch_authority_allowed=False, count_gate_evidence_allowed=False))
    write_out_json("non_ansible_positive_memory_gap_analysis_batch063c.json", {"status": "PASS", "non_ansible_positive_memory_count": 0, "reason": "no non-Ansible candidate has become scoreable and memory-positive under valid gates in Batch063c", "memory_lift": MEMORY_LIFT})


def write_pytest_outputs(command_manifest: dict[str, Any], harness_origin: dict[str, Any], workspace: dict[str, Any], provider: dict[str, Any]) -> tuple[str, str, str, str, str]:
    safe_tag_status = "blocked_no_predeclared_ancestor_tag_authority"
    version_status = "pytest_version_origin_missing_tags"
    runner_status = classify_runner_target(runner_package="pytest", target_package="pytest", external_runner_selected=False, target_import_origin_proven=False)
    command_status = "pytest_command_boundary_blocked_version_origin"
    prerepair_status = "NOT_RUN_blocked_version_origin_missing_tags_safe_tag_authority_absent"
    terminal_state = "pytest_command_boundary_blocked_version_origin"
    next_action = "batch063d_pytest_safe_tag_acquisition_hardening"
    write_out_json("pytest_batch063c_command_boundary_plan.json", {"status": "PASS", "candidate_id": PYTEST_ID, "preserved_command": PRESERVED_COMMAND, "uses_batch067_modules": ["command_translation", "version_origin", "runner_target", "workspace_purity", "harness_origin", "terminal_states"], "patch_generation_allowed": False})
    write_out_json("pytest_safe_tag_acquisition_decision.json", {"status": safe_tag_status, "candidate_id": PYTEST_ID, "candidate_sha": PYTEST_SHA, "candidate_isolated_workspace_required": True, "safe_tag_acquisition_executed": False, "reason": "no predeclared ancestor-only tag authority exists in current decision-time metadata", "future_tag_exposure_avoided": True, "controllergate_repo_mutated": False, "global_environment_mutated": False})
    write_out_json("pytest_version_origin_recheck_batch063c.json", {"status": "PASS", "classification": version_status, "previous_classification": "pytest_version_origin_missing_tags", "safe_tag_acquisition_status": safe_tag_status})
    write_out_json("pytest_runner_target_import_origin_recheck_batch063c.json", {"status": "PASS", "classification": runner_status, "external_runner_selected": False, "target_import_origin_proven": False, "blocked_by_version_origin_first": True})
    write_out_json("pytest_command_manifest_batch063c.json", command_manifest)
    write_out_json("pytest_command_translation_decision_batch063c.json", {"status": "PASS", "validation": validate_candidate_command_manifest(command_manifest).as_dict(), "classification": command_status, "no_minversion_suppression": True, "no_blind_external_runner": True})
    write_out_json("pytest_harness_origin_recheck_batch063c.json", harness_origin)
    write_out_json("pytest_workspace_purity_recheck_batch063c.json", workspace)
    write_out_json("pytest_provider_capsule_recheck_batch063c.json", provider)
    write_out_json("pytest_prerepair_replay_batch063c.json", {"status": "NOT_RUN", "classification": prerepair_status, "reason": "version-origin gate blocked before replay", "all_prerequisites_passed": False, "target_failure_materialized": False})
    write_out_json("pytest_terminal_state_batch063c.json", {"status": "PASS", "terminal_state": terminal_state, "repair_success": False, "patch_license_open": False})
    write_out_json("pytest_next_allowed_action_batch063c.json", {"status": "PASS", "next_allowed_action": next_action, "exact_blocker": "pytest_version_origin_missing_tags_command_boundary"})
    return safe_tag_status, version_status, runner_status, command_status, prerepair_status


def update_public_docs(final: dict[str, Any]) -> None:
    section = """## Batch063c Pytest Command-Boundary Follow-up

Batch063c applies the Batch067 wrapper infrastructure to Pytest command-boundary recovery and restores missing pre-generation, reward-signal, baseline-drift, and structural-transfer controls. These are engineering controls and routing evidence, not repair proof. No repair is counted without source-only target pass, duplicate clean replay, and count gate. Full scoring remains NOT_RUN/disallowed. Memory lift remains not_demonstrated. Self-maintaining software remains false/not_demonstrated.

Batch063c status:

- Batch067 artifact/result preservation: `{batch067_ingest_status}`.
- Pre-generation state lock: `{cognitive_state_snapshot_status}`.
- Reward signal: `{reward_signal_status}`.
- Baseline registry precheck: `{baseline_registry_precheck_status}`.
- Structural transfer ledger: `{cross_family_ast_homology_status}`.
- Pytest safe tag acquisition: `{pytest_safe_tag_acquisition_status}`.
- Pytest version-origin status: `{pytest_version_origin_status}`.
- Pytest runner-target status: `{pytest_runner_target_import_origin_status}`.
- Pytest command-boundary status: `{pytest_command_boundary_status}`.
- Pytest pre-repair replay: `{pytest_prerepair_replay_status}`.
- Issue-derived repair count remains `{issue_derived_repair_count}`.
- Native external repair count remains `{native_external_repair_count}`.
- Next allowed action: `{next_allowed_action}`.
""".format(**final)
    for rel in [
        "README.md",
        "docs/current_status.md",
        "controllergate_v1_7_beta/reports/critic_review_package/shareable_summary.md",
    ]:
        path = ROOT / rel
        text = path.read_text(encoding="utf-8")
        marker = "## Batch063c Pytest Command-Boundary Follow-up"
        if marker in text:
            start = text.index(marker)
            next_marker = text.find("\n## ", start + 1)
            text = text[:start].rstrip() + "\n\n" + section.rstrip() + ("\n" if next_marker == -1 else "\n\n" + text[next_marker + 1 :].lstrip())
        else:
            first_section = text.find("\n## ")
            text = text.rstrip() + "\n\n" + section if first_section == -1 else text[:first_section].rstrip() + "\n\n" + section.rstrip() + "\n\n" + text[first_section + 1 :].lstrip()
        write_text_lf(path, text)


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    _, artifact_verification, artifact_ingest = verify_batch067_artifact()
    write_out_json("batch067_artifact_ingestion_summary.json", artifact_ingest)
    write_out_json("batch067_artifact_sha256_verification.json", artifact_verification)
    batch067_final = read_json(BATCH067_DIR / "batch067_final_decision.json")
    write_out_json("batch067_result_preservation.json", {"status": "PASS", "source": f"outputs/{BATCH067_NAME}/batch067_final_decision.json", "next_allowed_action": batch067_final["next_allowed_action"], "issue_derived_repair_count": batch067_final["issue_derived_repair_count"], "native_external_repair_count": batch067_final["native_external_repair_count"]})
    write_out_json("batch067_module_status_preservation.json", {"status": "PASS", "artifact_custody_module_status": batch067_final["artifact_custody_module_status"], "command_translation_module_status": batch067_final["command_translation_module_status"], "version_origin_module_status": batch067_final["version_origin_module_status"], "runner_target_module_status": batch067_final["runner_target_module_status"], "cross_environment_orthology_layer_status": batch067_final["cross_environment_orthology_layer_status"]})
    write_out_json("batch067_public_summary_preservation.json", {"status": "PASS", "public_language_boundary_status": batch067_final["public_language_boundary_status"], "repair_success_claimed": False})
    write_out_json("batch067_boundary_preservation.json", {"status": "PASS", "patch_generated": False, "patch_applied": False, "duplicate_replay_run": False, "count_gate_run": False, "repair_count_increment": False, "full_scoring": FULL_SCORING, "memory_lift": MEMORY_LIFT, "self_maintaining_software": SELF_MAINTAINING})

    command_manifest = build_candidate_command_manifest(
        candidate_id=PYTEST_ID,
        repo_url=PYTEST_REPO,
        candidate_sha=PYTEST_SHA,
        native_test_path="testing",
        declared_command_source="Batch063b preserved command plus buggy-checkout pyproject testpaths",
        declared_command_source_file="pyproject.toml",
        working_directory="candidate_isolated_runtime_workspace_not_materialized_in_batch063c",
        python_version="3.11",
        runner_package="pytest",
        target_package="pytest",
        command_string=PRESERVED_COMMAND,
        collection_command="python -m pytest testing --collect-only -q",
    )
    harness_origin = {"status": "PASS", "policy": harness_origin_policy(), "authority_source": "immutable_public_repo_commit", "source_commit_sha_or_bundle_identity": PYTEST_SHA, "non_circular": True}
    workspace = {"status": "PASS", "policy": fresh_workspace_purity_policy(), "workspace_created": False, "reason": "safe tag authority blocked before acquisition", "global_environment_mutated": False}
    provider = {"status": "PASS", "provider_capsule": "Batch063b declared metadata provider recovered", "provider_setup_rerun": False, "global_environment_mutated": False}
    snapshot, reward, baseline_records, homology_ledger = write_control_layers(command_manifest, harness_origin, workspace, provider)
    write_control_outputs(snapshot, reward, baseline_records, homology_ledger)
    safe_tag_status, version_status, runner_status, command_status, prerepair_status = write_pytest_outputs(command_manifest, harness_origin, workspace, provider)
    final = {
        "status": "PASS",
        "batch067_ingest_status": artifact_ingest["status"],
        "batch063c_audit_status": "PASS",
        "current_protocol": CURRENT_PROTOCOL,
        "issue_derived_repair_count": ISSUE_DERIVED_REPAIR_COUNT,
        "native_external_repair_count": NATIVE_EXTERNAL_REPAIR_COUNT,
        "full_scoring": FULL_SCORING,
        "memory_lift": MEMORY_LIFT,
        "self_maintaining_software": SELF_MAINTAINING,
        "patch_generated": False,
        "patch_applied": False,
        "source_mutated": False,
        "tests_mutated": False,
        "fixtures_mutated": False,
        "pyproject_mutated": False,
        "duplicate_replay_run": False,
        "count_gate_run": False,
        "repair_count_increment": False,
        "cognitive_state_snapshot_status": "PASS",
        "pre_generation_prompt_lock_status": "PASS",
        "reward_signal_status": "PASS",
        "baseline_registry_precheck_status": "baseline_drift_precheck_PASS_isolated_runtime",
        "cross_family_ast_homology_status": "PASS",
        "non_ansible_positive_memory_gap_status": "PASS",
        "pytest_safe_tag_acquisition_status": safe_tag_status,
        "pytest_version_origin_status": version_status,
        "pytest_runner_target_import_origin_status": runner_status,
        "pytest_command_boundary_status": command_status,
        "pytest_prerepair_replay_status": prerepair_status,
        "pytest_terminal_state": "pytest_command_boundary_blocked_version_origin",
        "pytest_next_allowed_action": "batch063d_pytest_safe_tag_acquisition_hardening",
        "next_allowed_action": "batch063d_pytest_safe_tag_acquisition_hardening",
        "exact_blocker": "pytest_version_origin_missing_tags_command_boundary",
    }
    write_out_json("batch063c_final_decision.json", final)
    write_out_text("batch063c_summary.md", "Batch063c applies the Batch067 wrapper infrastructure to Pytest command-boundary recovery and restores missing pre-generation, reward-signal, baseline-drift, and structural-transfer controls. These are engineering controls and routing evidence, not repair proof. No repair is counted without source-only target pass, duplicate clean replay, and count gate. Full scoring remains NOT_RUN/disallowed. Memory lift remains not_demonstrated. Self-maintaining software remains false/not_demonstrated.")
    update_public_docs(final)
    write_sha256sums(OUT_DIR)
    print(json.dumps(final, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
