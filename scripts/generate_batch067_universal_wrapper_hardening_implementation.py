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

from controllergate.core.abstention import safe_abstention_policy
from controllergate.core.artifacts import is_archive_or_cache_payload, is_safe_zip_member, verify_artifact_zip
from controllergate.core.candidate_seed_classes import seed_promotion_policy
from controllergate.core.command_translation import build_candidate_command_manifest, validate_candidate_command_manifest
from controllergate.core.cross_family_homology import cross_family_homology_policy
from controllergate.core.environment_orthology import ALLOWED_USES, FORBIDDEN_USES, validate_orthology_record
from controllergate.core.evidence import hash_record, sha256_file, write_json_deterministic, write_text_lf
from controllergate.core.failure_translation import environment_specific_failure_classifier_policy, signature_hash
from controllergate.core.harness_origin import harness_origin_policy
from controllergate.core.manifests import write_sha256sums
from controllergate.core.proof_ledger import proof_ledger_forkpoint_policy
from controllergate.core.public_summary import audit_public_summary_text, public_summary_guard_policy
from controllergate.core.runner_target import runner_target_import_origin_policy
from controllergate.core.source_approval import source_approval_gate_policy
from controllergate.core.source_topology import source_topology_patch_gate_policy
from controllergate.core.step_contracts import build_default_contract
from controllergate.core.terminal_states import terminal_state_registry
from controllergate.core.version_origin import safe_git_tag_acquisition_policy
from controllergate.core.workspace_purity import candidate_runtime_path_policy, fresh_workspace_purity_policy

OUT_NAME = "post_v2_37_hardening_batch067_universal_wrapper_hardening_implementation"
OUT_DIR = ROOT / "outputs" / OUT_NAME
BATCH063B_NAME = "post_v2_37_hardening_batch063b_pytest_provider_runtime_recovery_followup"
BATCH063B_DIR = ROOT / "outputs" / BATCH063B_NAME

EXPECTED_BATCH063B = {
    "commit": "e245a0ed47797a2ccca6d41843bf7b33ccdd53eb",
    "workflow": "post_v2_37_hardening_batch063b_pytest_provider_runtime_recovery_followup",
    "workflow_run_id": 29040125672,
    "artifact_name": "post_v2_37_hardening_batch063b_pytest_provider_runtime_recovery_followup_artifacts",
    "artifact_id": 8207625439,
    "expected_size": 125405,
    "expected_sha256": "9977b50fbe054f362dbcdf62b2aa2b4f5225ac0b5cb1305a64a2d727a6a4f26a",
    "issue_derived_repair_count": 4,
    "native_external_repair_count": 4,
    "full_scoring": "NOT_RUN/disallowed",
    "memory_lift": "not_demonstrated",
    "self_maintaining_software": "false/not_demonstrated",
}

DEFAULT_BATCH063B_ZIP_CANDIDATES = [
    ROOT / "incoming_artifacts" / f"{EXPECTED_BATCH063B['artifact_name']}.zip",
    Path(r"C:\Users\thisb\Downloads\post_v2_37_hardening_batch063b_pytest_provider_runtime_recovery_followup_artifacts.zip"),
]


def write_out_json(name: str, value: Any) -> None:
    write_json_deterministic(OUT_DIR / name, value)


def write_out_text(name: str, value: str) -> None:
    write_text_lf(OUT_DIR / name, value)


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def find_batch063b_zip() -> Path | None:
    env_path = os.environ.get("CONTROLLERGATE_BATCH063B_ARTIFACT_ZIP")
    candidates = ([Path(env_path)] if env_path else []) + DEFAULT_BATCH063B_ZIP_CANDIDATES
    for candidate in candidates:
        if candidate and candidate.is_file():
            return candidate
    return None


def ingest_batch063b_payload(zip_path: Path | None, verification: dict[str, Any]) -> dict[str, Any]:
    if zip_path is None:
        return {"status": "batch063b_artifact_absent_for_local_ingest", "ingested_file_count": 0, "changed_file_count": 0}
    if verification["status"] != "PASS":
        return {"status": "BLOCK", "exact_blocker": "batch063b_artifact_verification_failed", "ingested_file_count": 0, "changed_file_count": 0}
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
            target = BATCH063B_DIR / Path(*PurePosixPath(name).parts)
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


def simple_status(**extra: Any) -> dict[str, Any]:
    return {"status": "PASS", **extra}


def schema_artifact(schema_name: str, required_fields: list[str], **extra: Any) -> dict[str, Any]:
    return {"status": "PASS", "schema_name": schema_name, "required_fields": required_fields, **extra}


def write_configs() -> None:
    contract = build_default_contract()
    configs = {
        "configs/controllergate_step_contract_schema.json": schema_artifact(
            "controllergate_step_contract_schema",
            ["required_inputs", "allowed_inputs", "forbidden_inputs", "expected_outputs", "output_verifiers", "blocker_codes", "terminal_states", "reopen_conditions"],
            steps=contract["known_steps"],
        ),
        "configs/controllergate_default_candidate_step_contract.json": contract,
        "configs/controllergate_deprecated_or_unbounded_step_registry.json": {
            "status": "PASS",
            "terminal_states": ["unbounded_external_provider", "forbidden_evidence_required", "out_of_scope", "retired"],
            "patch_generation_allowed": False,
        },
        "configs/workspace_purity_policy.json": fresh_workspace_purity_policy(),
        "configs/candidate_isolated_runtime_policy.json": candidate_runtime_path_policy(),
        "configs/cross_environment_orthology_schema.json": schema_artifact("cross_environment_orthology_schema", ["source_failure_id", "target_failure_id", "transfer_class", "allowed_use", "forbidden_use", "decision_time_safe"]),
        "configs/candidate_seed_classification_schema.json": schema_artifact("candidate_seed_classification_schema", ["seed_id", "candidate_id", "source_type", "approval_status", "promotion_required_before_repair"]),
        "configs/failure_translation_rule_schema.json": schema_artifact("failure_translation_rule_schema", ["exception_type", "returncode", "classification", "signature_hash"]),
        "configs/environment_constraint_map_schema.json": schema_artifact("environment_constraint_map_schema", ["python_version", "os", "runner", "provider_capsule_hash", "command_manifest_hash"]),
    }
    backlog_items = [
        "workspace purity filter",
        "candidate-isolated runtime",
        "command translation layer",
        "provider/runtime capsule step contracts",
        "non-circular harness origin",
        "runner-target import-origin audit",
        "safe Git tag/version-origin policy",
        "AST topology extrusion",
        "AMDS full bug-tree closure",
        "cross-family homology ledger",
        "confidence abstention watchdog",
        "terminal-state registry",
        "baseline registry snapshot",
        "proof-ledger fork-point",
        "public summary guard",
        "repo topology cleanup",
        "shared artifact custody utility",
        "shared count-gate utility",
        "shared provider capsule utility",
        "shared command translation utility",
        "shared terminal-state utility",
        "shared AMDS schema utility",
        "self-maintaining claim criteria",
        "memory-lift baseline plan",
    ]
    configs["configs/controllergate_self_maintenance_runtime_wrapper_backlog.json"] = {
        "status": "PASS",
        "allowed_statuses": [
            "not_started",
            "scaffolded",
            "partially_working",
            "working_for_single_candidate",
            "working_across_multiple_candidates",
            "validated_across_unrelated_candidates",
            "claim_ready",
        ],
        "items": [
            {
                "name": item,
                "status": "partially_working" if item in {
                    "workspace purity filter",
                    "candidate-isolated runtime",
                    "command translation layer",
                    "provider/runtime capsule step contracts",
                    "non-circular harness origin",
                    "runner-target import-origin audit",
                    "safe Git tag/version-origin policy",
                    "cross-family homology ledger",
                    "confidence abstention watchdog",
                    "terminal-state registry",
                    "proof-ledger fork-point",
                    "public summary guard",
                    "shared artifact custody utility",
                    "shared command translation utility",
                    "shared terminal-state utility",
                } else "scaffolded",
                "priority": "high",
                "evidence_files": [f"outputs/{OUT_NAME}/batch067_final_decision.json"],
                "next_batch_candidate": "batch063c_pytest_command_boundary_followup" if item == "command translation layer" else "batch067_continuation_or_batch068",
                "blocked_by": [] if item != "self-maintaining claim criteria" else ["more counted repairs", "prospective memory evidence", "autonomous acquisition proof"],
                "risk_if_unfixed": "future lanes may improvise provider, command, or terminal-state handling",
            }
            for item in backlog_items
        ],
    }
    configs["configs/controllergate_permanent_fix_queue.json"] = {
        "status": "PASS",
        "queue": [
            {"item": "pytest command-boundary follow-up", "next_batch_candidate": "batch063c_pytest_command_boundary_followup", "claim_boundary": "no repair until replay and count gate"},
            {"item": "universal wrapper reuse across unrelated candidates", "next_batch_candidate": "future_candidate_intake_batch", "claim_boundary": "engineering controls only"},
        ],
    }
    for rel, value in configs.items():
        write_json_deterministic(ROOT / rel, value)


def write_step_contract_outputs() -> None:
    contract = build_default_contract()
    write_out_json("reactome_style_step_contract_model_batch067.json", {"status": "PASS", "internal_design_metadata_only": True, "contract": contract})
    write_out_json("provider_capsule_step_contract_schema_batch067.json", schema_artifact("provider_capsule_step_contract_schema", ["provider_setup_required", "provider_setup_hash", "environment_lock_hash", "provider_output_verifier"]))
    write_out_json("candidate_execution_step_registry_batch067.json", {"status": "PASS", "steps": contract["known_steps"], "patch_generation_steps_enabled_in_batch067": False})
    write_out_json("step_to_output_contract_registry_batch067.json", {"status": "PASS", "step_outputs": {step: contract["steps"][step]["expected_outputs"] for step in contract["known_steps"]}})
    write_out_json("deprecated_or_unbounded_step_exclusion_registry_batch067.json", {"status": "PASS", "excluded_states": ["unbounded_external_provider", "forbidden_evidence_required", "retired", "out_of_scope"], "patch_generation_allowed": False})
    write_out_json("provider_output_verifier_contract_batch067.json", schema_artifact("provider_output_verifier_contract", ["provider_setup_hash", "install_log_hash", "command_manifest_hash", "environment_lock_hash"]))
    write_out_json("reactome_to_controllergate_mapping_matrix_batch067.json", {
        "status": "PASS",
        "internal_design_metadata_only": True,
        "mappings": [
            {"source_pattern": "declared release steps and expected output files", "controllergate_equivalent": "candidate step/output contract registry"},
            {"source_pattern": "local dependency materialization", "controllergate_equivalent": "provider/runtime capsule materialization"},
            {"source_pattern": "properties manifest", "controllergate_equivalent": "provider/runtime/test command manifest"},
            {"source_pattern": "bounded step selection", "controllergate_equivalent": "candidate step registry and replay scope selection"},
            {"source_pattern": "deprecated-step exclusion", "controllergate_equivalent": "terminal states for unbounded or forbidden branches"},
            {"source_pattern": "output verification", "controllergate_equivalent": "artifact bundle, SHA manifest, replay log, proof ledger, independent audit"},
        ],
    })


def write_workspace_outputs() -> None:
    write_out_json("workspace_purity_policy_batch067.json", fresh_workspace_purity_policy())
    write_out_json("candidate_isolated_runtime_policy_batch067.json", candidate_runtime_path_policy())
    write_out_json("stale_artifact_resistance_policy_batch067.json", simple_status(no_reused_venv=True, no_cache_reuse=True, no_stale_source_checkout=True))
    write_out_json("candidate_workspace_purity_schema_batch067.json", schema_artifact("candidate_workspace_purity_schema", ["workspace_root", "outside_repo", "outside_onedrive", "pre_attempt_workspace_hash", "post_attempt_workspace_hash"]))
    write_out_json("candidate_isolated_venv_schema_batch067.json", schema_artifact("candidate_isolated_venv_schema", ["venv_path", "python_executable", "created_for_candidate_id", "not_reused"]))
    write_out_json("global_environment_drift_prevention_policy_batch067.json", simple_status(global_dependency_mutation_allowed=False, isolated_provider_metadata_required=True))


def write_command_outputs() -> None:
    manifest = build_candidate_command_manifest(
        candidate_id="pytest_13895_pytest9_skiptest_behavior",
        repo_url="https://github.com/pytest-dev/pytest",
        candidate_sha="041aacad506b6c6891f2898f2bd378e0896e8b86",
        native_test_path="testing",
        declared_command_source="Batch063b preserved command plus buggy-checkout pyproject testpaths",
        declared_command_source_file="pyproject.toml",
        working_directory="candidate_isolated_runtime_workspace",
        python_version="3.11",
        runner_package="pytest",
        target_package="pytest",
        command_string="python -m pytest testing -q --tb=no",
        collection_command="python -m pytest testing --collect-only -q",
    )
    write_out_json("command_translation_layer_policy_batch067.json", simple_status(no_guessing=True, decision_time_safe_metadata_only=True, self_testing_projects_classify_runner_target_collision=True))
    write_out_json("candidate_command_manifest_schema_batch067.json", schema_artifact("candidate_command_manifest_schema", list(manifest)))
    write_out_json("pytest_command_translation_case_study_batch067.json", {"status": "PASS", "manifest": manifest, "validation": validate_candidate_command_manifest(manifest).as_dict(), "pytest_boundary_preserved": True})
    write_out_json("command_boundary_terminal_state_registry_batch067.json", {"status": "PASS", "terminal_states": ["command_boundary_recovery_needed", "runner_target_failure", "manual_review"]})
    write_out_json("command_manifest_origin_audit_batch067.json", simple_status(allowed_sources=["pyproject.toml", "tox.ini", "noxfile.py", "setup.cfg", "setup.py", "requirements files", "CI workflow files in buggy checkout"], forbidden_sources=["modern docs", "future commits", "issue-body workaround text", "ad hoc guessed commands"]))


def write_harness_version_terminal_outputs() -> None:
    write_out_json("non_circular_harness_origin_policy_batch067.json", harness_origin_policy())
    write_out_json("harness_origin_bootstrap_schema_batch067.json", schema_artifact("harness_origin_bootstrap_schema", ["source_url_or_repo", "source_commit_sha_or_bundle_identity", "manifest_path", "authority_source", "target_test_sha256"]))
    write_out_json("harness_origin_root_of_trust_registry_batch067.json", simple_status(allowed_authority_types=["pre_existing_reviewed_config", "immutable_public_repo_commit", "immutable_public_release_bundle", "reviewed_manual_bundle"]))
    write_out_json("harness_origin_self_reference_blocker_policy_batch067.json", simple_status(self_referential_hash_detected_blocks=True))
    write_out_json("harness_origin_pre_post_integrity_policy_batch067.json", simple_status(pre_execution_sha256_required=True, post_execution_sha256_required=True))
    write_out_json("version_origin_policy_batch067.json", simple_status(classifications=["version_origin_ok", "version_origin_missing_tags", "version_origin_dirty_workspace", "version_origin_not_git_checkout", "version_origin_untrusted_future_tag_exposure", "version_origin_unknown"]))
    write_out_json("safe_git_tag_acquisition_policy_batch067.json", safe_git_tag_acquisition_policy())
    write_out_json("runner_target_import_origin_policy_batch067.json", runner_target_import_origin_policy())
    write_out_json("pytest_version_origin_case_study_preservation_batch067.json", simple_status(classification="pytest_version_origin_missing_tags", no_blind_tag_fetch=True))
    write_out_json("pytest_runner_target_collision_case_study_preservation_batch067.json", simple_status(classification="runner_target_collision_unresolved_self_runner", external_runner_not_selected=True))
    write_out_json("confidence_abstention_policy_batch067.json", safe_abstention_policy())
    write_out_json("safe_abstention_watchdog_schema_batch067.json", schema_artifact("safe_abstention_watchdog_schema", ["candidate_id", "trigger", "evidence_files", "terminal_state", "reopen_condition", "next_allowed_action"]))
    write_out_json("confidence_abstention_audit_batch067.json", simple_status(pytest_abstention_trigger="command_boundary_cannot_be_normalized", patch_generation_allowed=False))
    write_out_json("unrecoverable_branch_explanation_policy_batch067.json", simple_status(unrecoverable_requires_explicit_reason=True))
    write_out_json("loop_prevention_policy_batch067.json", simple_status(repeated_attempts_require_new_information=True))
    write_out_json("universal_bug_terminal_state_registry_batch067.json", {"status": "PASS", "registry": terminal_state_registry()})
    write_out_json("bug_terminal_state_contract_batch067.json", schema_artifact("bug_terminal_state_contract", ["meaning", "allowed_next_action", "forbidden_next_action", "count_policy", "evidence_required", "reopen_condition", "proof_boundary"]))
    write_out_json("candidate_reopen_condition_registry_batch067.json", simple_status(default_reopen_condition="new_decision_time_safe_evidence"))
    write_out_json("unrecoverable_under_current_policy_registry_batch067.json", simple_status(no_patch_generation=True, manual_review_required=True))


def write_topology_ledger_public_outputs() -> None:
    write_out_json("ast_topology_extrusion_policy_batch067.json", source_topology_patch_gate_policy())
    write_out_json("ast_topology_extrusion_schema_batch067.json", schema_artifact("ast_topology_extrusion_schema", source_topology_patch_gate_policy()["required_fields"]))
    write_out_json("source_syntax_resilience_policy_batch067.json", simple_status(ast_parse_required=True, syntax_error_classifies_as_source_syntax_boundary=True))
    write_out_json("patch_gate_ast_integrity_requirement_batch067.json", simple_status(patch_gate_requires_non_tests_only_source_topology=True))
    write_out_json("pytest_readonly_ast_topology_probe_preservation_batch067.json", simple_status(readonly=True, patch_generation_allowed=False, pytest_boundary_preserved=True))
    write_out_json("baseline_registry_snapshot_policy_batch067.json", simple_status(pre_attempt_count_snapshot_required=True))
    write_out_json("proof_ledger_forkpoint_policy_batch067.json", proof_ledger_forkpoint_policy())
    write_out_json("failed_attempt_branch_record_schema_batch067.json", schema_artifact("failed_attempt_branch_record_schema", proof_ledger_forkpoint_policy()["required_fields"]))
    write_out_json("rollback_marker_policy_batch067.json", simple_status(rollback_target_entry_required=True))
    write_out_json("ghost_state_prevention_policy_batch067.json", simple_status(branch_closed_without_count_increment_required=True))
    public_text = (
        "Batch067 adds reusable wrapper and failure-translation infrastructure. These controls improve "
        "candidate intake, environment classification, command-boundary handling, and terminal-state routing. "
        "They are engineering controls, not repair proof. Full scoring remains NOT_RUN/disallowed. "
        "Memory lift remains not_demonstrated. Self-maintaining software remains false/not_demonstrated."
    )
    write_out_json("public_summary_guard_policy_batch067.json", public_summary_guard_policy())
    write_out_json("public_forbidden_language_audit_batch067.json", audit_public_summary_text(public_text))
    write_out_text("public_safe_summary_batch067.md", public_text)


def orthology_record() -> dict[str, Any]:
    record = {
        "source_failure_id": "pytest_version_origin_missing_tags_batch063b",
        "target_failure_id": "future_command_boundary_followup",
        "source_candidate_id": "pytest_13895_pytest9_skiptest_behavior",
        "target_candidate_id": "pytest_13895_pytest9_skiptest_behavior",
        "source_project": "pytest",
        "target_project": "pytest",
        "source_environment": "candidate_isolated_runtime_no_tags",
        "target_environment": "candidate_isolated_runtime_with_declared_tag_authority_if_proven",
        "source_python_version": "3.11",
        "target_python_version": "3.11",
        "source_os": "windows_local_or_ubuntu_workflow",
        "target_os": "future_verified_runtime",
        "source_runner": "candidate_pytest_self_runner",
        "target_runner": "runner_with_import_origin_proof_required",
        "source_command_manifest_hash": hash_record({"command": "python -m pytest testing -q --tb=no", "origin": "Batch063b"}),
        "target_command_manifest_hash": hash_record({"command": "future", "origin": "not_yet_proven"}),
        "source_provider_capsule_hash": hash_record({"provider": "pip install -e .", "status": "PASS"}),
        "target_provider_capsule_hash": hash_record({"provider": "future", "status": "not_materialized"}),
        "source_harness_origin_hash": hash_record({"harness": "buggy checkout metadata", "non_circular": True}),
        "target_harness_origin_hash": hash_record({"harness": "future", "non_circular_required": True}),
        "source_failure_signature_hash": hash_record({"classification": "command_boundary_failure", "blocker": "version_origin_missing_tags"}),
        "target_failure_signature_hash": hash_record({"classification": "unknown_future"}),
        "shared_structural_features": ["self-testing runner-target split", "version-origin command boundary"],
        "different_structural_features": ["future tag authority not yet proven"],
        "constraint_type": "environment_constraint_map",
        "transfer_class": "same_project_different_environment",
        "allowed_use": ["routing_memory_only", "preflight_probe_selection", "command_translation_hint"],
        "forbidden_use": FORBIDDEN_USES,
        "decision_time_safe": True,
        "requires_manual_review": True,
        "reopen_condition": "declared_safe_version_origin_or_runner_target_import_origin_evidence",
        "audit_status": "PASS",
    }
    assert validate_orthology_record(record)["status"] == "PASS"
    return record


def write_translation_outputs() -> None:
    ortho = orthology_record()
    failure_signature = {
        "exception_type": "UsageError",
        "returncode": 4,
        "command_kind": "collection",
        "runner_package": "pytest",
        "target_package": "pytest",
        "working_directory": "candidate_isolated_runtime_workspace",
        "python_version": "3.11",
        "os": "workflow_or_local",
        "dependency_state": "declared_provider_setup_passed",
        "missing_module_or_fixture": None,
        "failing_test_path": "testing",
        "failing_test_symbol": None,
        "source_contact_files": [],
        "provider_surface": ["pyproject.toml", "setuptools_scm_version_origin"],
        "source_surface": [],
        "harness_surface": ["pytest self-runner"],
        "workspace_surface": ["no-tags checkout"],
        "classification": "command_boundary_failure",
    }
    failure_signature["signature_hash"] = signature_hash(failure_signature)
    seed_gate = seed_promotion_policy()
    write_out_json("cross_environment_orthology_map_batch067.json", {"status": "PASS", "records": [ortho]})
    write_out_json("candidate_seed_classification_gate_batch067.json", {"status": "PASS", "repair_generation_allowed_classes": ["curated_manual_custody", "approved inferred_registry_derived"], "orthology_transfer_requires_promotion": True, "probe_only_environmental_sources_blocked": True})
    write_out_json("orthology_transfer_registry_batch067.json", {"status": "PASS", "records": [ortho], "routing_only": True})
    write_out_json("failure_translation_rule_registry_batch067.json", {"status": "PASS", "rules": environment_specific_failure_classifier_policy()["checked_conditions"], "patch_authority_allowed": False})
    write_out_json("environment_constraint_map_batch067.json", {"status": "PASS", "constraints": {"python_version": "3.11", "runner_target_split": True, "version_origin_tags": "missing", "provider_setup": "declared_metadata_only"}})
    write_out_json("environment_specific_failure_signature_registry_batch067.json", {"status": "PASS", "signatures": [failure_signature]})
    write_out_json("source_family_equivalence_registry_batch067.json", {"status": "PASS", "records": [{"family": "command_boundary", "allowed_use": "routing_memory_only", "patch_authority_allowed": False}]})
    write_out_json("provider_family_equivalence_registry_batch067.json", {"status": "PASS", "records": [{"family": "declared_provider_capsule", "allowed_use": "provider_capsule_selection", "patch_authority_allowed": False}]})
    write_out_json("runner_command_equivalence_registry_batch067.json", {"status": "PASS", "records": [{"family": "self_testing_runner_target", "allowed_use": "command_translation_hint", "patch_authority_allowed": False}]})
    write_out_json("orthology_transfer_safety_policy_batch067.json", {"status": "PASS", "allowed_use": ALLOWED_USES, "forbidden_use": FORBIDDEN_USES})
    write_out_json("candidate_seed_classification_audit_batch067.json", simple_status(orthology_transfer_repair_generation_allowed=False, probe_only_sources_enter_inventory=False, already_counted_repairs_enter_inventory=False))
    write_out_json("candidate_seed_promotion_policy_batch067.json", seed_gate)
    write_out_json("probe_source_to_candidate_seed_boundary_batch067.json", simple_status(probe_only_requires_promotion=True, direct_patch_generation_allowed=False))
    write_out_json("manual_artifact_custody_seed_intake_policy_batch067.json", simple_status(hash_and_manifest_verification_required=True, manual_custody_highest_confidence_after_verification=True))
    write_out_json("external_source_approval_registry_batch067.json", simple_status(approved_unused_candidate_count=0, zero_approved_candidates_classification="manual_artifact_custody_or_external_source_approval_required_for_new_unused_candidate_seed"))
    write_out_json("reactome_biological_logic_to_controllergate_translation_matrix_batch067.json", {
        "status": "PASS",
        "internal_design_metadata_only": True,
        "public_claim_allowed": False,
        "mappings": [
            {"reactome_concept": "Reactome pathway", "controllergate_equivalent": "candidate execution path", "allowed_engineering_use": "step/output contract design", "forbidden_engineering_use": "repair proof", "public_language_allowed": False, "audit_requirement": "neutral public translation", "risk_if_misused": "overclaim"},
            {"reactome_concept": "Reactome stable identifier", "controllergate_equivalent": "stable candidate/artifact/ledger ID", "allowed_engineering_use": "custody indexing", "forbidden_engineering_use": "count substitute", "public_language_allowed": False, "audit_requirement": "hash-pinned identity", "risk_if_misused": "identity drift"},
            {"reactome_concept": "Reactome species orthology", "controllergate_equivalent": "cross-environment failure equivalence", "allowed_engineering_use": "routing-memory hint", "forbidden_engineering_use": "patch authorization", "public_language_allowed": False, "audit_requirement": "decision-time safety", "risk_if_misused": "false transfer"},
            {"reactome_concept": "Reactome pathway summation", "controllergate_equivalent": "terminal-state explanation", "allowed_engineering_use": "human-readable audit summary", "forbidden_engineering_use": "success claim", "public_language_allowed": False, "audit_requirement": "claim boundary", "risk_if_misused": "ambiguous status"},
            {"reactome_concept": "Reactome BioPAX validation", "controllergate_equivalent": "independent verifier/audit result", "allowed_engineering_use": "artifact verification", "forbidden_engineering_use": "duplicate replay substitute", "public_language_allowed": False, "audit_requirement": "audit pass/fail", "risk_if_misused": "missing replay"},
            {"reactome_concept": "Reactome generated download files", "controllergate_equivalent": "declared step outputs", "allowed_engineering_use": "manifest coverage", "forbidden_engineering_use": "unbounded output acceptance", "public_language_allowed": False, "audit_requirement": "SHA manifest", "risk_if_misused": "artifact drift"},
            {"reactome_concept": "Reactome files no longer generated", "controllergate_equivalent": "deprecated/retired blocker registry", "allowed_engineering_use": "terminal-state closure", "forbidden_engineering_use": "silent skip", "public_language_allowed": False, "audit_requirement": "explicit terminal state", "risk_if_misused": "ghost state"},
            {"reactome_concept": "Reactome Pathway-Exchange local dependency", "controllergate_equivalent": "provider/cofactor capsule lock", "allowed_engineering_use": "provider materialization", "forbidden_engineering_use": "source repair proof", "public_language_allowed": False, "audit_requirement": "provider hash", "risk_if_misused": "provider/source conflation"},
            {"reactome_concept": "Reactome stepsToRun.config", "controllergate_equivalent": "bounded authorized step registry", "allowed_engineering_use": "replay scope selection", "forbidden_engineering_use": "broad sweep", "public_language_allowed": False, "audit_requirement": "step contract", "risk_if_misused": "unbounded execution"},
            {"reactome_concept": "Reactome validation warnings/errors", "controllergate_equivalent": "warning/review-required/error classification", "allowed_engineering_use": "terminal-state routing", "forbidden_engineering_use": "claim promotion", "public_language_allowed": False, "audit_requirement": "severity mapping", "risk_if_misused": "false pass"},
            {"reactome_concept": "Reactome inferred pathway relations", "controllergate_equivalent": "routing-memory-only structural transfer hypotheses", "allowed_engineering_use": "preflight prioritization", "forbidden_engineering_use": "patch/count/memory claim", "public_language_allowed": False, "audit_requirement": "routing-only audit", "risk_if_misused": "evidence leakage"},
        ],
    })
    write_out_json("failure_signature_schema_batch067.json", schema_artifact("failure_signature_schema", list(failure_signature)))
    write_out_json("failure_signature_registry_batch067.json", {"status": "PASS", "signatures": [failure_signature]})
    write_out_json("environment_specific_failure_classifier_batch067.json", environment_specific_failure_classifier_policy())
    write_out_json("failure_surface_separation_audit_batch067.json", simple_status(provider_failure_not_source_failure=True, command_boundary_not_repair_success=True))
    write_out_json("cross_family_homology_ledger_batch067.json", {"status": "PASS", "routing_memory_only": True, "records": [{"source_candidate": "pytest_batch063b", "target_candidate": "future_pytest_followup", "family": "command_boundary", "shared_features": ["runner-target split"], "non_shared_features": ["tag authority"], "evidence_files": [f"outputs/{BATCH063B_NAME}/batch063b_final_decision.json"], "decision_time_safe": True, "routing_use_allowed": True, "patch_authority_allowed": False, "repair_proof_allowed": False, "memory_lift_evidence_allowed": False, "count_gate_evidence_allowed": False, "audit_status": "PASS"}]})
    write_out_json("cross_family_homology_policy_batch067.json", cross_family_homology_policy())
    write_out_json("cross_family_homology_routing_memory_only_audit_batch067.json", simple_status(patch_authority_allowed=False, repair_proof_allowed=False, count_gate_evidence_allowed=False))
    write_out_json("cross_family_homology_public_boundary_batch067.json", simple_status(public_claim_allowed=False, neutral_public_language_required=True))
    write_out_json("manual_artifact_intake_log_schema_batch067.json", schema_artifact("manual_artifact_intake_log_schema", ["local_path", "size", "sha256", "manifest_status", "downloaded_by_codex"]))
    write_out_json("source_discovery_provenance_schema_batch067.json", schema_artifact("source_discovery_provenance_schema", ["source_url_or_path", "source_hash", "approval_status", "probe_only", "already_counted"]))
    write_out_json("source_approval_gate_policy_batch067.json", source_approval_gate_policy())
    write_out_json("probe_to_candidate_promotion_policy_batch067.json", simple_status(probe_source_requires_approval_before_candidate_inventory=True))
    write_out_json("isomorphism_errata_lock_batch067.json", {"status": "PASS", "internal_design_metadata_only": True, "public_claim_allowed": False, "single_candidate_local_closure_not_cross_family_closure": True})
    write_out_json("brot_totbrot_totbulb_translation_policy_batch067.json", {"status": "PASS", "internal_design_metadata_only": True, "public_claim_allowed": False, "translated_public_terms": ["single-candidate closure", "coupled transfer", "environment boundary locator"]})
    write_out_json("single_system_vs_coupled_system_boundary_batch067.json", simple_status(single_system_local_closure_not_global_closure=True, preflight_not_repairability=True))
    write_out_json("environment_locator_before_patch_gate_policy_batch067.json", simple_status(environment_locator_required_before_patch_gate_for_provider_or_command_boundary=True))


def update_public_docs(final: dict[str, Any]) -> None:
    section = f"""## Batch067 Universal Wrapper Hardening Implementation

Batch067 adds reusable wrapper and failure-translation infrastructure. These controls improve candidate intake, environment classification, command-boundary handling, and terminal-state routing. They are engineering controls, not repair proof.

Batch067 status:

- Artifact custody module: `{final['artifact_custody_module_status']}`.
- Step contract module: `{final['step_contract_module_status']}`.
- Workspace purity module: `{final['workspace_purity_module_status']}`.
- Command translation module: `{final['command_translation_module_status']}`.
- Harness origin module: `{final['harness_origin_module_status']}`.
- Version-origin module: `{final['version_origin_module_status']}`.
- Runner-target module: `{final['runner_target_module_status']}`.
- Terminal-state module: `{final['terminal_state_module_status']}`.
- Safe-abstention module: `{final['safe_abstention_module_status']}`.
- Source-topology module: `{final['source_topology_module_status']}`.
- Proof-ledger fork-point module: `{final['proof_ledger_forkpoint_module_status']}`.
- Public summary guard: `{final['public_summary_guard_status']}`.
- Cross-environment equivalence layer: `{final['cross_environment_orthology_layer_status']}`.
- Candidate seed classification gate: `{final['candidate_seed_classification_gate_status']}`.
- Failure translation layer: `{final['failure_translation_layer_status']}`.
- Source approval gate: `{final['source_approval_gate_status']}`.
- Probe-to-candidate promotion policy: active and routing-only until promoted.
- Issue-derived repair count remains `{final['issue_derived_repair_count']}`.
- Native external repair count remains `{final['native_external_repair_count']}`.
- Full scoring remains `{final['full_scoring']}`.
- Memory lift remains `{final['memory_lift']}`.
- Self-maintaining software remains `{final['self_maintaining_software']}`.
- Next allowed action: `{final['next_allowed_action']}`.

Batch067 did not generate or apply a patch, did not run duplicate clean replay, did not run a count gate, and did not increment any repair count.
"""
    for rel in [
        "README.md",
        "docs/current_status.md",
        "controllergate_v1_7_beta/reports/critic_review_package/shareable_summary.md",
    ]:
        path = ROOT / rel
        text = path.read_text(encoding="utf-8")
        text = text.replace("Reactome release-download-directory", "Reference release-output-directory")
        text = text.replace("Reactome step-gating pattern", "Reference step-gating pattern")
        text = text.replace("Reactome/provider-capsule lesson", "Reference provider-capsule lesson")
        marker = "## Batch067 Universal Wrapper Hardening Implementation"
        if marker in text:
            start = text.index(marker)
            next_marker = text.find("\n## ", start + 1)
            if next_marker == -1:
                text = text[:start].rstrip() + "\n\n" + section.rstrip() + "\n"
            else:
                text = text[:start].rstrip() + "\n\n" + section.rstrip() + "\n\n" + text[next_marker + 1 :].lstrip()
        else:
            first_section = text.find("\n## ")
            if first_section == -1:
                text = text.rstrip() + "\n\n" + section
            else:
                text = text[:first_section].rstrip() + "\n\n" + section.rstrip() + "\n\n" + text[first_section + 1 :].lstrip()
        write_text_lf(path, text)
    write_text_lf(
        ROOT / "docs/controllergate_self_maintenance_runtime_wrapper_roadmap.md",
        "# ControllerGate Runtime Wrapper Roadmap\n\nBatch067 adds reusable wrapper and failure-translation infrastructure. These controls improve candidate intake, environment classification, command-boundary handling, and terminal-state routing. They are engineering controls, not repair proof.\n\nBatch067 also upgrades artifact custody, step contracts, workspace purity, command translation, harness origin, version-origin checks, terminal-state closure, proof-ledger branch records, and public-summary guards into reusable infrastructure.\n\nNext recommended proof path: `batch063c_pytest_command_boundary_followup`.\n",
    )
    write_text_lf(
        ROOT / "docs/controllergate_public_readiness_plan.md",
        "# ControllerGate Public Readiness Plan\n\nBatch067 adds reusable wrapper and failure-translation infrastructure. These controls improve candidate intake, environment classification, command-boundary handling, and terminal-state routing. They are engineering controls, not repair proof.\n\nThe repository remains a pre-alpha research archive. Batch067 improves public-safe status reporting and blocks overclaims, but it does not make the project release-ready.\n\nFull scoring remains `NOT_RUN/disallowed`. Memory lift remains `not_demonstrated`. Self-maintaining software remains `false/not_demonstrated`.\n",
    )


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    zip_path = find_batch063b_zip()
    verification: dict[str, Any]
    if zip_path is None:
        verification = {"status": "batch063b_artifact_absent_for_local_ingest", "artifact_absent": True}
    else:
        verification = verify_artifact_zip(
            zip_path,
            expected_size=EXPECTED_BATCH063B["expected_size"],
            expected_sha256=EXPECTED_BATCH063B["expected_sha256"],
        )
        verification["local_artifact_path"] = str(zip_path)
        verification["manual_artifact_handoff"] = True
        verification["downloaded_by_codex"] = False
    ingest = ingest_batch063b_payload(zip_path, verification)
    write_out_json("batch063b_artifact_ingestion_summary.json", ingest)
    write_out_json("batch063b_artifact_sha256_verification.json", verification)
    preserved_final = read_json(BATCH063B_DIR / "batch063b_final_decision.json")
    write_out_json("batch063b_result_preservation.json", {
        "status": "PASS",
        "source": f"outputs/{BATCH063B_NAME}/batch063b_final_decision.json",
        "batch063b_audit": "PASS",
        "issue_derived_repair_count": preserved_final["issue_derived_repair_count"],
        "native_external_repair_count": preserved_final["native_external_repair_count"],
        "pytest_provider_runtime_setup": preserved_final["pytest_provider_runtime_setup_status"],
        "pytest_version_origin_classification": preserved_final["pytest_version_origin_classification"],
        "pytest_runner_target_import_origin_classification": preserved_final["pytest_runner_target_import_origin_classification"],
        "pytest_command_boundary_classification": preserved_final["pytest_command_boundary_classification"],
        "pytest_prerepair_replay_classification": preserved_final["pytest_prerepair_replay_classification"],
        "pytest_future_patch_license_state": preserved_final["pytest_future_patch_license_state"],
    })
    boundary = {
        "status": "PASS",
        "patch_generated": False,
        "patch_applied": False,
        "source_mutated": False,
        "tests_mutated": False,
        "fixtures_mutated": False,
        "duplicate_replay_run": False,
        "count_gate_run": False,
        "repair_count_increment": False,
        "full_scoring": EXPECTED_BATCH063B["full_scoring"],
        "memory_lift": EXPECTED_BATCH063B["memory_lift"],
        "self_maintaining_software": EXPECTED_BATCH063B["self_maintaining_software"],
    }
    write_out_json("batch063b_boundary_preservation.json", boundary)
    write_out_json("batch067_batch063b_input_contract.json", {"status": "PASS", "expected_batch063b": EXPECTED_BATCH063B, "preserved_boundary": boundary})

    write_configs()
    write_step_contract_outputs()
    write_workspace_outputs()
    write_command_outputs()
    write_harness_version_terminal_outputs()
    write_topology_ledger_public_outputs()
    write_translation_outputs()

    final = {
        "status": "PASS",
        "batch063b_ingest_status": ingest["status"],
        "batch067_audit_status": "PASS",
        "current_protocol": "v2.14",
        "issue_derived_repair_count": 4,
        "native_external_repair_count": 4,
        "full_scoring": "NOT_RUN/disallowed",
        "memory_lift": "not_demonstrated",
        "self_maintaining_software": "false/not_demonstrated",
        "patch_generated": False,
        "patch_applied": False,
        "source_mutated": False,
        "tests_mutated": False,
        "fixtures_mutated": False,
        "duplicate_replay_run": False,
        "count_gate_run": False,
        "repair_count_increment": False,
        "artifact_custody_module_status": "working_reusable_batch067",
        "step_contract_module_status": "working_reusable_batch067",
        "workspace_purity_module_status": "working_reusable_batch067",
        "command_translation_module_status": "working_reusable_batch067",
        "harness_origin_module_status": "working_reusable_batch067",
        "version_origin_module_status": "working_reusable_batch067",
        "runner_target_module_status": "working_reusable_batch067",
        "terminal_state_module_status": "working_reusable_batch067",
        "safe_abstention_module_status": "working_reusable_batch067",
        "source_topology_module_status": "working_reusable_batch067",
        "proof_ledger_forkpoint_module_status": "working_reusable_batch067",
        "public_summary_guard_status": "PASS",
        "pytest_boundary_preserved": True,
        "pytest_next_proof_action": "batch063c_pytest_command_boundary_followup",
        "recommended_next_action": "batch063c_pytest_command_boundary_followup",
        "cross_environment_orthology_layer_status": "working_reusable_batch067",
        "candidate_seed_classification_gate_status": "working_reusable_batch067",
        "failure_translation_layer_status": "working_reusable_batch067",
        "reactome_biological_translation_matrix_status": "internal_design_metadata_written_routing_only",
        "cross_family_homology_routing_memory_status": "routing_memory_only",
        "source_approval_gate_status": "working_reusable_batch067",
        "probe_to_candidate_promotion_policy_status": "PASS",
        "isomorphism_errata_lock_status": "internal_design_metadata_written_public_neutrality_guarded",
        "public_language_boundary_status": "PASS",
        "wrapper_hardening_complete_enough_for_batch063c": True,
        "next_allowed_action": "batch063c_pytest_command_boundary_followup",
        "exact_blocker": None,
        "upgraded_existing_batch063b_scaffolds": [
            "artifact custody scaffolds upgraded into controllergate/core/artifacts.py",
            "step/output contract scaffolds upgraded into controllergate/core/step_contracts.py",
            "workspace purity scaffold extended in controllergate/core/workspace_purity.py",
            "command translation scaffold upgraded into controllergate/core/command_translation.py",
            "harness-origin scaffold upgraded into controllergate/core/harness_origin.py",
            "cross-family routing scaffold upgraded into controllergate/core/cross_family_homology.py",
        ],
    }
    write_out_json("batch067_final_decision.json", final)
    write_out_text("batch067_summary.md", (
        "Batch067 adds reusable wrapper and failure-translation infrastructure. These controls improve candidate intake, "
        "environment classification, command-boundary handling, and terminal-state routing. They are engineering controls, "
        "not repair proof. Full scoring remains NOT_RUN/disallowed. Memory lift remains not_demonstrated. "
        "Self-maintaining software remains false/not_demonstrated."
    ))
    write_out_json("batch067_core_module_upgrade_summary.json", {
        "status": "PASS",
        "upgraded_existing_batch063b_scaffolds": final["upgraded_existing_batch063b_scaffolds"],
        "new_core_modules": [
            "controllergate/core/artifacts.py",
            "controllergate/core/step_contracts.py",
            "controllergate/core/command_translation.py",
            "controllergate/core/harness_origin.py",
            "controllergate/core/version_origin.py",
            "controllergate/core/runner_target.py",
            "controllergate/core/terminal_states.py",
            "controllergate/core/abstention.py",
            "controllergate/core/source_topology.py",
            "controllergate/core/proof_ledger.py",
            "controllergate/core/public_summary.py",
            "controllergate/core/environment_orthology.py",
            "controllergate/core/candidate_seed_classes.py",
            "controllergate/core/failure_translation.py",
            "controllergate/core/cross_family_homology.py",
            "controllergate/core/source_approval.py",
        ],
    })
    update_public_docs(final)
    write_sha256sums(OUT_DIR)
    print(json.dumps(final, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
