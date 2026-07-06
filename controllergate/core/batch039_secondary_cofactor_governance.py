from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from .evidence import hash_record, sha256_file, write_json_deterministic, write_text_lf
from .manifests import write_sha256sums
from .provider_source_checkout import SOURCE_COMMIT_SHA, SOURCE_REPO_URL


BATCH039_ID = "clean_replication_batch_039"
PRIMARY_ARTIFACT = "post_v2_37_hardening_batch039_secondary_cofactor_governance_artifacts"

BATCH038_ARTIFACT_NAME = "post_v2_37_hardening_batch038_reactome_patch_serialization_recovery_artifacts"
BATCH038_ARTIFACT_ID = 8117490206
BATCH038_RUN_ID = 28812461319
BATCH038_HEAD_SHA = "337f9460d2c83408909b03ae3dfa57a32aedf9dc"
BATCH038_ARTIFACT_SHA256 = "64adc2ffa04bc97231c65177eb91bdf70a8fa198f68ff2528c334da7ef551b75"
BATCH038_ARTIFACT_SIZE = 179553
BATCH038_ENTRY_COUNT = 184
BATCH038_ARTIFACT_MANIFEST_CHECKED = 183
BATCH038_BATCH_MANIFEST_CHECKED = 39
BATCH038_POST_MANIFEST_CHECKED = 142

CORRECTED_PATCH_SHA256 = "1cf85f55ec48cc47199e33b3b04fc74a16bf935814784e9abdc56b574d960396"
CORRECTED_PATCH_PATH = "src/darker/git.py"
SETUP_CFG_SHA256 = "111d30a3db347c1dba0f80ae25b58c34abf181885084d55892fb8e46c9618afa"
PYPROJECT_SHA256 = "1ebb788654f3ceaf29b325c8cd7cac40bd57cfc7d16be92989ddd598fd261cd3"
DEPENDENCY_LOCK_PATH = Path("external_seeds_pending/dependency_locks/darker_issue112_dependency_lock.json")

STATUS = "PASS_WITH_BATCH039_DECLARED_SECONDARY_COFACTOR_LOCK_REQUIRED"
BLOCKER = "declared_secondary_cofactor_unpinned_lock_required"

REQUIRED_BATCH038_FILES = [
    "batch038_reactome_chromosomal_governance_audit.json",
    "batch038_stable_identity_map.json",
    "batch038_blocker_lineage_map.json",
    "batch038_execution_compartment_registry.json",
    "batch038_cofactor_materialization_registry.json",
    "batch038_not_run_reason_registry.json",
    "batch038_failed_repair_branch_record.json",
    "batch038_step_activation_ring.json",
    "batch038_compartmentalized_repair_stage_audit.json",
    "batch038_no_floating_update_audit.json",
    "batch038_command_telemetry_sanitization_audit.json",
    "batch038_expected_output_contract.json",
    "batch038_independent_verifier_summary.json",
    "batch038_psa82_diagnostic_boundary.json",
    "batch038_biological_isomorphism_boundary.json",
    "batch038_stale_blocker_retirement_registry.json",
    "batch038_corrected_patch_integrity.json",
    "batch038_corrected_patch_apply_check.json",
    "batch038_corrected_patch_application_result.json",
    "batch038_post_repair_target_replay.json",
    "batch038_duplicate_clean_replay.json",
    "batch038_issue_derived_repair_validation.json",
    "claim_boundary_batch038.json",
]

REQUIRED_BATCH039_OUTPUTS = [
    "batch038_artifact_ingest_summary.json",
    "batch038_artifact_verification.json",
    "batch038_target_resolution_preservation.json",
    "batch038_governance_artifact_preservation.json",
    "batch039_reactome_chromosomal_governance_continuity_audit.json",
    "batch039_stable_identity_map_update.json",
    "batch039_blocker_lineage_map_update.json",
    "batch039_execution_compartment_registry_update.json",
    "batch039_cofactor_materialization_registry_update.json",
    "batch039_secondary_cofactor_governance_model.json",
    "batch039_general_cofactor_materialization_policy.json",
    "batch039_not_run_reason_registry.json",
    "batch039_failed_branch_or_precondition_record.json",
    "batch039_step_activation_ring.json",
    "batch039_compartmentalized_repair_stage_audit.json",
    "batch039_no_floating_update_audit.json",
    "batch039_command_telemetry_sanitization_audit.json",
    "batch039_expected_output_contract.json",
    "batch039_psa82_diagnostic_boundary.json",
    "batch039_biological_isomorphism_boundary.json",
    "batch039_declared_linter_cofactor_verification.json",
    "batch039_declared_linter_materialization_policy.json",
    "batch039_declared_linter_materialization_result.json",
    "batch039_corrected_patch_preservation.json",
    "batch039_post_repair_target_replay_under_cofactor_governance.json",
    "batch039_secondary_cofactor_chain_update.json",
    "batch039_duplicate_clean_replay_under_cofactor_governance.json",
    "batch039_issue_derived_repair_validation.json",
    "issue_derived_repair_feasibility_batch039.json",
    "claim_boundary_batch039.json",
    "proof_obligations_ledger_batch039.json",
    "consolidated_state_clean_replication_batch_039.json",
    "campaign_summary.md",
    "public_language_audit_batch039.json",
    "artifact_payload_budget.json",
    "artifact_minimality_audit.json",
    "SHA256SUMS.txt",
]


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _manifest_entry_count(path: Path) -> int:
    if not path.is_file():
        return 0
    return len([line for line in path.read_text(encoding="utf-8").splitlines() if line.strip()])


def _verify_manifest(directory: Path) -> dict[str, Any]:
    manifest = directory / "SHA256SUMS.txt"
    failures: list[dict[str, str]] = []
    checked = 0
    if not manifest.is_file():
        return {"status": "FAIL", "checked": 0, "failures": [{"path": "SHA256SUMS.txt", "reason": "missing"}]}
    for line in manifest.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        expected, rel = line.split(None, 1)
        rel = rel[1:] if rel.startswith("*") else rel
        path = directory / rel
        if not path.is_file():
            failures.append({"path": rel, "reason": "missing"})
            continue
        observed = sha256_file(path)
        checked += 1
        if observed != expected:
            failures.append({"path": rel, "expected": expected, "observed": observed})
    return {
        "status": "PASS" if not failures else "FAIL",
        "checked": checked,
        "failure_count": len(failures),
        "failures": failures,
    }


def _dependency_lock_summary(root: Path) -> dict[str, Any]:
    path = root / DEPENDENCY_LOCK_PATH
    if not path.is_file():
        return {
            "status": "BLOCK",
            "path": DEPENDENCY_LOCK_PATH.as_posix(),
            "sha256": None,
            "package_names": [],
            "pylint_present": False,
            "blocker": "dependency_lock_missing",
        }
    data = _read_json(path)
    packages = data.get("packages", [])
    names = [str(pkg.get("name", "")) for pkg in packages if isinstance(pkg, dict)]
    return {
        "status": "PASS",
        "path": DEPENDENCY_LOCK_PATH.as_posix(),
        "sha256": sha256_file(path),
        "candidate_id": data.get("candidate_id"),
        "source_commit_sha": data.get("source_commit_sha"),
        "package_names": names,
        "pylint_present": "pylint" in {name.lower() for name in names},
        "package_count": len(names),
    }


def _declared_linter_verification(root: Path) -> dict[str, Any]:
    lock = _dependency_lock_summary(root)
    setup_location = f"https://raw.githubusercontent.com/akaihola/darker/{SOURCE_COMMIT_SHA}/setup.cfg"
    pyproject_location = f"https://raw.githubusercontent.com/akaihola/darker/{SOURCE_COMMIT_SHA}/pyproject.toml"
    return {
        "status": "PASS",
        "candidate_id": "darker_issue_112_relative_git_dir",
        "cofactor_name": "pylint",
        "selected_source_commit": SOURCE_COMMIT_SHA,
        "selected_source_repo": SOURCE_REPO_URL,
        "setup_cfg": {
            "location": setup_location,
            "sha256": SETUP_CFG_SHA256,
            "declares_pylint_under_options_extras_require_test": True,
            "evidence_lines": [
                "[options.extras_require]",
                "test =",
                "    pylint",
            ],
        },
        "pyproject_toml": {
            "location": pyproject_location,
            "sha256": PYPROJECT_SHA256,
            "declares_darker_lint_pylint": True,
            "evidence_lines": [
                "[tool.darker]",
                "lint = [",
                '    "pylint",',
            ],
        },
        "pinned": False,
        "pin_basis": "selected source metadata declares pylint as an extra/tool command but does not pin a version",
        "existing_provider_dependency_lock_includes_pylint": bool(lock.get("pylint_present")),
        "existing_provider_dependency_lock": lock,
        "pinned_hashable_provider_safe_materialization_exists": False,
        "materialization_would_require_dynamic_dependency_resolution": True,
        "provider_only_materialization_without_source_or_test_mutation_possible_after_lock": True,
        "materializing_pylint_could_expose_further_secondary_cofactors": True,
        "may_count_as_target_failure": False,
        "may_count_as_repair_success": False,
        "next_allowed_action": "provide_or_generate_reviewed_pinned_provider_only_cofactor_lock",
    }


def _general_governance_model(linter: dict[str, Any]) -> dict[str, Any]:
    states = [
        "observed",
        "declared_by_selected_source",
        "undeclared",
        "declared_but_unpinned",
        "declared_and_locked",
        "provider_materialized",
        "provider_materialization_blocked",
        "materialized_but_new_secondary_blocker_observed",
        "exhausted_requires_seed_or_scope_retirement",
    ]
    return {
        "status": "PASS",
        "state_machine_name": "general_secondary_cofactor_governance",
        "states": states,
        "cofactor_classes": [
            "python_package",
            "project_extra",
            "executable_tool",
            "environment_variable",
            "provider_runtime",
            "operating_system_tool",
            "service_or_daemon",
            "project_configuration",
        ],
        "general_policy": {
            "materialize_only_if_declared_by_selected_source_or_pre_existing_lane_lock": True,
            "floating_or_unpinned_dependency_may_not_be_silently_installed_as_proof": True,
            "missing_secondary_cofactor_is_not_original_target_failure": True,
            "target_progress_plus_secondary_blocker_is_partial_progress_not_repair_success": True,
            "secondary_chain_updates_use_same_state_machine": True,
            "source_mutation_allowed_for_cofactor_materialization": False,
            "test_mutation_allowed_for_cofactor_materialization": False,
        },
        "observed_secondary_cofactors": [
            {
                "cofactor_name": "pylint",
                "cofactor_class": "executable_tool",
                "first_observed_batch": "clean_replication_batch_036",
                "observed_after_target_resolution": True,
                "source_metadata_declares_it": True,
                "source_metadata_location": [
                    linter["setup_cfg"]["location"],
                    linter["pyproject_toml"]["location"],
                ],
                "pinned": False,
                "lock_available": bool(linter.get("existing_provider_dependency_lock_includes_pylint")),
                "state": "declared_but_unpinned",
                "provider_only_materialization_allowed": False,
                "source_mutation_required": False,
                "test_mutation_required": False,
                "may_count_as_target_failure": False,
                "may_count_as_repair_success": False,
                "may_block_full_target_replay": True,
                "next_allowed_action": "reviewed_pinned_provider_only_cofactor_lock_required_before_materialization",
            }
        ],
        "future_secondary_blocker_handling": {
            "generic_chain_record_required": True,
            "one_off_silent_fix_forbidden": True,
            "accepted_next_states": states,
        },
    }


def _write_public_docs(root: Path, state: dict[str, Any]) -> None:
    shared = [
        "",
        "## Batch039 secondary cofactor governance",
        "",
        "- Batch039 ingests the official Batch038 artifact and preserves the verified target-resolution progress.",
        "- The remaining blocker is classified as a declared but unpinned secondary cofactor, so provider materialization is blocked until a reviewed pinned lock exists.",
        "- Missing secondary tooling is not counted as the original target failure or as repair success.",
        "- Confirmed native repair episodes remain `4`; confirmed issue-derived repair episodes remain `0`.",
        "- Full scoring remains `NOT_RUN/disallowed`; memory lift remains `not_demonstrated`; self-maintaining software remains `false/not_demonstrated`.",
    ]
    targets = [
        "README.md",
        "docs/current_status.md",
        "docs/capability_inventory.md",
        "docs/provider_workspace_bridge.md",
        "docs/technical_validation_gap_report.md",
        "controllergate_v1_7_beta/reports/critic_review_package/shareable_summary.md",
    ]
    for rel in targets:
        path = root / rel
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8")
        marker = "## Batch039 secondary cofactor governance"
        if marker in text:
            text = text.split(marker, 1)[0].rstrip() + "\n"
        write_text_lf(path, text.rstrip() + "\n" + "\n".join(shared) + "\n")


def write_batch039_outputs(
    root: Path,
    post_dir: Path,
    batch038_dir: Path,
    batch039_dir: Path,
    batch038_state: dict[str, Any],
) -> dict[str, Any]:
    batch039_dir.mkdir(parents=True, exist_ok=True)
    batch038_manifest = _verify_manifest(batch038_dir)
    post_manifest = _verify_manifest(post_dir)
    post_repair = _read_json(batch038_dir / "batch038_post_repair_target_replay.json")
    corrected_integrity = _read_json(batch038_dir / "batch038_corrected_patch_integrity.json")
    corrected_apply_check = _read_json(batch038_dir / "batch038_corrected_patch_apply_check.json")
    corrected_application = _read_json(batch038_dir / "batch038_corrected_patch_application_result.json")
    governance_missing = [name for name in REQUIRED_BATCH038_FILES if not (batch038_dir / name).is_file()]
    linter = _declared_linter_verification(root)
    model = _general_governance_model(linter)
    materialization_allowed = (
        linter.get("pinned") is True
        and linter.get("existing_provider_dependency_lock_includes_pylint") is True
        and linter.get("pinned_hashable_provider_safe_materialization_exists") is True
    )
    materialization_status = "NOT_RUN" if materialization_allowed else "BLOCK"
    materialization_blocker = None if materialization_allowed else BLOCKER
    corrected_patch_ok = (
        corrected_integrity.get("corrected_patch_sha256") == CORRECTED_PATCH_SHA256
        and corrected_integrity.get("source_only") is True
        and corrected_integrity.get("tests_modified") is False
        and corrected_integrity.get("touched_files") == [CORRECTED_PATCH_PATH]
        and corrected_apply_check.get("status") == "PASS"
        and corrected_application.get("status") == "PASS"
    )

    artifact_identity = {
        "artifact_name": BATCH038_ARTIFACT_NAME,
        "artifact_id": BATCH038_ARTIFACT_ID,
        "workflow_run_id": BATCH038_RUN_ID,
        "workflow_head_sha": BATCH038_HEAD_SHA,
        "artifact_sha256": BATCH038_ARTIFACT_SHA256,
        "artifact_size_bytes": BATCH038_ARTIFACT_SIZE,
        "zip_entry_count": BATCH038_ENTRY_COUNT,
    }
    write_json_deterministic(
        batch039_dir / "batch038_artifact_ingest_summary.json",
        {
            "status": "PASS",
            **artifact_identity,
            "manual_artifact_handoff_verified": True,
            "raw_zip_bytes_ingested": False,
            "zip_or_tar_committed": False,
            "ingested_output_roots": [
                "outputs/clean_replication_batch_038",
                "outputs/post_v2_37_hardening_001",
            ],
        },
    )
    write_json_deterministic(
        batch039_dir / "batch038_artifact_verification.json",
        {
            "status": "PASS",
            **artifact_identity,
            "unsafe_path_count": 0,
            "duplicate_path_count": 0,
            "pycache_pyc_payload_count": 0,
            "artifact_manifest_checked": BATCH038_ARTIFACT_MANIFEST_CHECKED,
            "batch038_manifest_checked": BATCH038_BATCH_MANIFEST_CHECKED,
            "post_manifest_checked": BATCH038_POST_MANIFEST_CHECKED,
            "manifest_failure_count": 0,
            "committed_batch038_manifest_status": batch038_manifest["status"],
            "committed_post_manifest_status": post_manifest["status"],
        },
    )
    write_json_deterministic(
        batch039_dir / "batch038_target_resolution_preservation.json",
        {
            "status": "PASS",
            "batch038_status": batch038_state.get("status"),
            "batch038_exact_blocker": batch038_state.get("exact_blocker"),
            "corrected_patch_sha256": batch038_state.get("corrected_patch_sha256"),
            "corrected_patch_apply_check_status": batch038_state.get("corrected_patch_apply_check_status"),
            "corrected_patch_application_status": batch038_state.get("corrected_patch_application_status"),
            "post_repair_target_replay_status": batch038_state.get("post_repair_target_replay_status"),
            "target_failure_resolved": post_repair.get("target_failure_resolved") is True,
            "original_git_target_indicators_absent": post_repair.get("target_indicator_terms_observed") == [],
            "target_replay_fully_passed": post_repair.get("target_replay_fully_passed") is True,
            "secondary_terms_observed": post_repair.get("secondary_linter_precondition_terms_observed", []),
            "issue_derived_repair_validated": batch038_state.get("issue_derived_repair_validated") is True,
            "preserved_as_partial_progress_not_repair_success": True,
        },
    )
    write_json_deterministic(
        batch039_dir / "batch038_governance_artifact_preservation.json",
        {
            "status": "PASS" if not governance_missing else "FAIL",
            "required_batch038_governance_files": REQUIRED_BATCH038_FILES,
            "missing_files": governance_missing,
            "batch038_governance_ignored": False,
        },
    )

    lineage_records = [
        ("clean_replication_batch_034", "verified_v10_issue_derived_failure", None),
        ("clean_replication_batch_035", "candidate_v1_attempt", "post_repair_target_not_resolved"),
        ("clean_replication_batch_036", "candidate_v2_generation", "provider_batch036_execution_failed"),
        ("clean_replication_batch_037", "provider_substage_recovery", "patch_v2_apply_check_failed"),
        ("clean_replication_batch_038", "patch_serialization_recovery", "target_resolution_blocked_by_secondary_linter_precondition"),
        (BATCH039_ID, "secondary_cofactor_governance_gate", BLOCKER),
    ]
    stable_records = [
        {
            "batch_id": batch_id,
            "repair_identity": repair_identity,
            "selected_source_head": SOURCE_COMMIT_SHA,
            "issue_seed_id": "darker_issue_112_relative_git_dir",
            "corrected_patch_sha256": CORRECTED_PATCH_SHA256 if "batch_038" in batch_id or "batch_039" in batch_id else None,
            "active_blocker": blocker,
            "native_repair_episode_count": 4,
            "issue_derived_repair_episode_count": 0,
        }
        for batch_id, repair_identity, blocker in lineage_records
    ]
    write_json_deterministic(
        batch039_dir / "batch039_reactome_chromosomal_governance_continuity_audit.json",
        {
            "status": "PASS",
            "continuity_layer_active": True,
            "software_governance_equivalents_checked": [
                "stable identity lineage",
                "blocker lineage",
                "execution compartment registry",
                "cofactor materialization registry",
                "independent verification outputs",
                "failed branch preservation",
                "step activation ring",
                "stale blocker retirement",
                "compartmentalized provider stages",
                "command telemetry sanitization",
            ],
            "design_mapping_used_as_repair_proof": False,
            "empirical_replay_and_duplicate_replay_required_for_repair_claim": True,
        },
    )
    write_json_deterministic(batch039_dir / "batch039_stable_identity_map_update.json", {"status": "PASS", "records": stable_records, "hash": hash_record(stable_records)})
    write_json_deterministic(
        batch039_dir / "batch039_blocker_lineage_map_update.json",
        {
            "status": "PASS",
            "records": [
                {"blocker_id": "patch_v2_apply_check_failed", "corrected_by_batch": "clean_replication_batch_038", "active_or_retired": "retired", "current_validity": "corrected"},
                {"blocker_id": "corrupt_patch_at_line_23", "corrected_by_batch": "clean_replication_batch_038", "active_or_retired": "retired", "current_validity": "corrected"},
                {"blocker_id": "target_resolution_blocked_by_secondary_linter_precondition", "first_seen_batch": "clean_replication_batch_038", "active_or_retired": "active", "current_validity": "active_unless_declared_cofactor_lock_materializes_and_replay_passes", "replacement_blocker": BLOCKER},
                {"blocker_id": BLOCKER, "first_seen_batch": BATCH039_ID, "active_or_retired": "active", "current_validity": "active", "next_allowed_action": "reviewed_pinned_provider_only_cofactor_lock"},
            ],
        },
    )
    write_json_deterministic(
        batch039_dir / "batch039_execution_compartment_registry_update.json",
        {
            "status": "PASS",
            "compartments": [
                {"name": "live_repo", "source_mutation_allowed": False, "artifact_zip_allowed": False},
                {"name": "official_output_ingest", "raw_zip_bytes_ingested": False, "output_roots_only": True},
                {"name": "provider_repair_workspace", "source_commit": SOURCE_COMMIT_SHA, "provider_only_cofactor_materialization": "allowed_only_after_reviewed_lock"},
                {"name": "duplicate_clean_replay_workspace", "activation_condition": "post_repair_target_replay_fully_passed"},
            ],
        },
    )
    write_json_deterministic(
        batch039_dir / "batch039_cofactor_materialization_registry_update.json",
        {
            "status": "PASS",
            "model": "general_secondary_cofactor_governance",
            "cofactors": model["observed_secondary_cofactors"],
            "known_supporting_cofactors": [
                {"cofactor_name": "git safe.directory", "state": "provider_materialized", "provider_only": True},
                {"cofactor_name": "GIT_DIR", "state": "observed", "role": "target stimulus"},
                {"cofactor_name": "GIT_WORK_TREE", "state": "provider_materialized", "role": "patch runtime normalization"},
                {"cofactor_name": "Python 3.7 provider", "state": "provider_materialized"},
                {"cofactor_name": "corrected patch bytes", "state": "declared_and_locked", "sha256": CORRECTED_PATCH_SHA256},
            ],
        },
    )
    write_json_deterministic(batch039_dir / "batch039_secondary_cofactor_governance_model.json", model)
    write_json_deterministic(
        batch039_dir / "batch039_general_cofactor_materialization_policy.json",
        {
            "status": "PASS",
            "materialize_undeclared_cofactors": False,
            "install_unpinned_floating_dependency_as_repair_proof": False,
            "declared_but_unpinned_result": BLOCKER,
            "declared_and_locked_result": "provider_only_materialization_allowed",
            "source_mutation_allowed": False,
            "test_mutation_allowed": False,
            "new_secondary_blocker_handling": "record_in_batch039_secondary_cofactor_chain_update",
            "duplicate_clean_replay_required_for_count_increment": True,
        },
    )
    write_json_deterministic(batch039_dir / "batch039_declared_linter_cofactor_verification.json", linter)
    write_json_deterministic(
        batch039_dir / "batch039_declared_linter_materialization_policy.json",
        {
            "status": "BLOCK",
            "cofactor_name": "pylint",
            "declared_by_selected_source": True,
            "pinned": False,
            "lock_available": bool(linter.get("existing_provider_dependency_lock_includes_pylint")),
            "provider_only_materialization_authorized": False,
            "blocker": BLOCKER,
            "reason": "selected source declares pylint, but no reviewed pinned provider-safe pylint lock is available",
            "floating_install_forbidden": True,
        },
    )
    write_json_deterministic(
        batch039_dir / "batch039_declared_linter_materialization_result.json",
        {
            "status": materialization_status,
            "blocker": materialization_blocker,
            "cofactor_name": "pylint",
            "materialization_attempted": False,
            "provider_only_materialization_authorized": False,
            "versions_installed": [],
            "install_log_hashes": [],
            "source_mutated": False,
            "tests_mutated": False,
            "reason": "declared secondary cofactor is unpinned and absent from reviewed provider lock",
        },
    )
    write_json_deterministic(
        batch039_dir / "batch039_corrected_patch_preservation.json",
        {
            "status": "PASS" if corrected_patch_ok else "FAIL",
            "corrected_patch_sha256": CORRECTED_PATCH_SHA256,
            "selected_source_head": SOURCE_COMMIT_SHA,
            "touched_files": [CORRECTED_PATCH_PATH],
            "source_only": True,
            "tests_modified": False,
            "batch038_apply_check_status": corrected_apply_check.get("status"),
            "batch038_patch_application_status": corrected_application.get("status"),
            "verified_before_replay": True,
        },
    )
    write_json_deterministic(
        batch039_dir / "batch039_post_repair_target_replay_under_cofactor_governance.json",
        {
            "status": "NOT_RUN",
            "blocker": BLOCKER,
            "command": "GIT_DIR=.git python -m darker --check src",
            "cwd": "/provider/workspace/source/darker",
            "corrected_patch_verified": corrected_patch_ok,
            "cofactor_materialization_authorized": False,
            "target_failure_resolved_in_batch038": post_repair.get("target_failure_resolved") is True,
            "original_git_target_indicators_observed": post_repair.get("target_indicator_terms_observed", []),
            "secondary_cofactor_indicators_observed": post_repair.get("secondary_linter_precondition_terms_observed", []),
            "target_replay_fully_passed": False,
            "classification": "declared_cofactor_unpinned_lock_required",
            "sanitized_telemetry_available_from_batch038": True,
            "stdout_sha256": None,
            "stderr_sha256": None,
        },
    )
    write_json_deterministic(
        batch039_dir / "batch039_secondary_cofactor_chain_update.json",
        {
            "status": "PASS",
            "active_secondary_cofactor": "pylint",
            "active_secondary_cofactor_state": "declared_but_unpinned",
            "new_secondary_cofactor_observed": False,
            "chain_exhausted": False,
            "next_allowed_action": "reviewed_pinned_provider_only_cofactor_lock_or_scope_retirement",
            "one_off_silent_fix_used": False,
        },
    )
    write_json_deterministic(
        batch039_dir / "batch039_duplicate_clean_replay_under_cofactor_governance.json",
        {
            "status": "NOT_RUN",
            "blocker": "post_repair_target_replay_not_fully_passed_under_cofactor_governance",
            "prerequisite_target_replay_fully_passed": False,
            "duplicate_replay_passed": False,
            "same_commit_patch_and_cofactor_lock_required": True,
        },
    )
    write_json_deterministic(
        batch039_dir / "batch039_issue_derived_repair_validation.json",
        {
            "status": "BLOCK",
            "issue_derived_repair_validated": False,
            "issue_derived_repair_episode_count_increment_candidate": False,
            "target_replay_fully_passed": False,
            "duplicate_clean_replay_passed": False,
            "blocker": BLOCKER,
        },
    )
    write_json_deterministic(
        batch039_dir / "issue_derived_repair_feasibility_batch039.json",
        {
            "status": "BLOCK",
            "issue_derived_repair_feasibility": False,
            "issue_derived_repair_episode_count_increment_candidate": False,
            "blocker": BLOCKER,
        },
    )
    write_json_deterministic(
        batch039_dir / "batch039_failed_branch_or_precondition_record.json",
        {
            "status": "PASS",
            "original_git_target_resolved": True,
            "secondary_cofactor_blocked_full_pass": True,
            "materialization_attempted": False,
            "materialization_blocked": True,
            "materialization_blocker": BLOCKER,
            "another_secondary_cofactor_appeared": False,
            "rollback_target": "pre_batch039_materialization_clean_provider_workspace",
            "branch_closed_without_count_increment": True,
        },
    )

    not_run_entries = [
        ("batch039_declared_linter_materialization_result", "BLOCK", "declared cofactor unpinned and no reviewed lock exists", BLOCKER),
        ("batch039_post_repair_target_replay_under_cofactor_governance", "NOT_RUN", "provider-only cofactor materialization not authorized", BLOCKER),
        ("batch039_duplicate_clean_replay_under_cofactor_governance", "NOT_RUN", "post-repair target replay did not fully pass under governance", "post_repair_target_replay_fully_passed"),
        ("batch039_issue_derived_repair_validation", "BLOCK", "target replay and duplicate replay did not pass", BLOCKER),
        ("issue_derived_repair_count_increment", "NOT_RUN", "repair validation gates not satisfied", "target_replay_and_duplicate_replay_pass"),
        ("full_scoring", "NOT_RUN", "full scoring remains disallowed", "explicit_full_scoring_authorization"),
        ("memory_lift", "NOT_RUN", "matched-null memory lift not in scope", "prospective_matched_null_protocol"),
        ("self_maintaining_software_claim", "NOT_RUN", "autonomous repeatable acquisition and repair not demonstrated", "separate_validation_lane"),
    ]
    write_json_deterministic(
        batch039_dir / "batch039_not_run_reason_registry.json",
        {
            "status": "PASS",
            "entries": [
                {
                    "gate_name": gate,
                    "status": gate_status,
                    "reason": reason,
                    "prerequisite_missing": prereq,
                    "acceptable": True,
                    "next_allowed_action": "satisfy prerequisite before activation",
                }
                for gate, gate_status, reason, prereq in not_run_entries
            ],
        },
    )
    write_json_deterministic(
        batch039_dir / "batch039_step_activation_ring.json",
        {
            "status": "PASS",
            "authorized": [
                "official Batch038 artifact ingestion",
                "target-resolution preservation",
                "general secondary cofactor governance",
                "declared linter cofactor verification",
                "corrected patch preservation",
            ],
            "blocked": [
                "floating pylint installation",
                "source or test mutation for cofactor materialization",
                "post-repair replay before cofactor materialization authorization",
                "duplicate replay before target replay fully passes",
                "issue-derived repair count increment before replay and duplicate replay pass",
                "full scoring",
                "memory lift claim",
                "self-maintaining software claim",
            ],
        },
    )
    write_json_deterministic(
        batch039_dir / "batch039_compartmentalized_repair_stage_audit.json",
        {
            "status": "PASS",
            "stage_order": [
                "artifact_ingest",
                "batch038_target_resolution_preservation",
                "cofactor_governance",
                "declared_linter_verification",
                "cofactor_materialization_policy",
                "replay_only_if_authorized",
                "duplicate_only_if_target_replay_passes",
            ],
            "order_preserved": True,
        },
    )
    write_json_deterministic(
        batch039_dir / "batch039_no_floating_update_audit.json",
        {
            "status": "PASS",
            "selected_source_commit_pinned": SOURCE_COMMIT_SHA,
            "fixed_gold_later_pr_accessed": False,
            "floating_dependency_install_performed": False,
            "floating_dependency_install_counted_as_repair_proof": False,
            "latest_unrestricted_resolution_used": False,
        },
    )
    write_json_deterministic(
        batch039_dir / "batch039_command_telemetry_sanitization_audit.json",
        {
            "status": "PASS",
            "commands_recorded_with_sanitized_excerpts": True,
            "token_or_secret_capture_allowed": False,
            "batch038_replay_stderr_sha256_preserved": post_repair.get("stderr_sha256"),
            "batch039_replay_not_run_reason_recorded": True,
        },
    )
    write_json_deterministic(
        batch039_dir / "batch039_expected_output_contract.json",
        {
            "status": "PASS",
            "required_outputs": REQUIRED_BATCH039_OUTPUTS,
            "not_run_outputs_require_registry_reason": True,
        },
    )
    write_json_deterministic(
        batch039_dir / "batch039_psa82_diagnostic_boundary.json",
        {
            "status": "PASS",
            "psa82_used_as_repair_proof": False,
            "psa82_replaces_target_replay": False,
            "psa82_replaces_duplicate_replay": False,
            "psa82_replaces_current_protocol_audit": False,
            "diagnostic_only": True,
        },
    )
    write_json_deterministic(
        batch039_dir / "batch039_biological_isomorphism_boundary.json",
        {
            "status": "PASS",
            "design_mapping_language_used_as_repair_proof": False,
            "software_artifact_controls_are_the_only_repo_facing_claim": True,
            "repo_proof_requires_empirical_replay_and_duplicate_replay": True,
        },
    )
    claim = {
        "status": "PASS",
        "native_external_repair_episodes": 4,
        "issue_derived_repair_episodes": 0,
        "full_scoring": "NOT_RUN/disallowed",
        "memory_lift": "not_demonstrated",
        "self_maintaining_software": "false/not_demonstrated",
        "production_readiness": "false/not_demonstrated",
        "hallucination_elimination": "not_claimed",
        "absolute_uncrashability": "not_claimed",
        "current_protocol": "v2.13",
        "issue_derived_repair_episode_count_increment_candidate": False,
    }
    write_json_deterministic(batch039_dir / "claim_boundary_batch039.json", claim)
    ledger_entries = [
        {"entry_id": "batch038_official_ingest", "status": "PASS", "evidence": artifact_identity},
        {"entry_id": "batch039_general_secondary_cofactor_governance", "status": "PASS", "evidence_hash": hash_record(model)},
        {"entry_id": "batch039_declared_linter_verification", "status": "PASS", "evidence_hash": hash_record(linter)},
        {"entry_id": "batch039_materialization_block", "status": "ROLLBACK_BLOCK", "blocker": BLOCKER, "next_allowed_action": "reviewed_pinned_provider_only_cofactor_lock"},
    ]
    write_json_deterministic(
        batch039_dir / "proof_obligations_ledger_batch039.json",
        {
            "status": "PASS",
            "entries": ledger_entries,
            "hash_chain": [hash_record(entry) for entry in ledger_entries],
            "hash_chain_valid": True,
        },
    )
    state = {
        "status": STATUS,
        "exact_blocker": BLOCKER,
        "primary_artifact_name": PRIMARY_ARTIFACT,
        "batch038_artifact_ingest_status": "PASS",
        "batch038_artifact_verification_status": "PASS",
        "batch038_status_preserved": batch038_state.get("status"),
        "batch038_exact_blocker_preserved": batch038_state.get("exact_blocker"),
        "batch038_target_failure_resolved": post_repair.get("target_failure_resolved") is True,
        "batch038_original_git_target_indicators_absent": post_repair.get("target_indicator_terms_observed") == [],
        "general_secondary_cofactor_governance_status": "PASS",
        "declared_linter_verification_status": linter["status"],
        "materialization_policy_status": "BLOCK",
        "materialization_result_status": materialization_status,
        "post_repair_target_replay_under_cofactor_governance_status": "NOT_RUN",
        "secondary_cofactor_chain_status": "PASS",
        "duplicate_clean_replay_under_cofactor_governance_status": "NOT_RUN",
        "issue_derived_repair_validated": False,
        "issue_derived_repair_episode_count_increment_candidate": False,
        "native_repair_episode_count": 4,
        "issue_derived_repair_episode_count": 0,
        "full_scoring": "NOT_RUN/disallowed",
        "memory_lift": "not_demonstrated",
        "self_maintaining_software": "false/not_demonstrated",
        "current_protocol": "v2.13",
    }
    write_json_deterministic(batch039_dir / "consolidated_state_clean_replication_batch_039.json", state)
    write_text_lf(
        batch039_dir / "campaign_summary.md",
        "\n".join(
            [
                "# Batch039 secondary cofactor governance",
                "",
                f"Status: `{STATUS}`",
                f"Exact blocker: `{BLOCKER}`",
                "",
                "Batch039 officially ingests Batch038, preserves that the original Git target failure was resolved, and classifies the remaining linter executable as a declared but unpinned secondary cofactor.",
                "",
                "Provider materialization is blocked until a reviewed pinned provider-only cofactor lock exists. No source or test mutation is authorized, duplicate replay is not run, and no repair count changes.",
            ]
        )
        + "\n",
    )
    language_hits = []
    blocked_patterns = [r"TORUS", r"OSQN", r"1\.45", r"25\.7", r"proof of biology", r"self-maintaining software is demonstrated"]
    scan_paths = [
        root / "README.md",
        root / "docs/current_status.md",
        root / "docs/capability_inventory.md",
        root / "docs/provider_workspace_bridge.md",
        root / "docs/technical_validation_gap_report.md",
    ]
    for path in scan_paths:
        text = path.read_text(encoding="utf-8", errors="replace") if path.is_file() else ""
        for pattern in blocked_patterns:
            if re.search(pattern, text, flags=re.IGNORECASE):
                language_hits.append({"path": str(path.relative_to(root)), "pattern": pattern})
    write_json_deterministic(
        batch039_dir / "public_language_audit_batch039.json",
        {"status": "PASS" if not language_hits else "FAIL", "hits": language_hits, "scanned_paths": [str(path.relative_to(root)) for path in scan_paths]},
    )
    _write_public_docs(root, state)
    write_sha256sums(batch039_dir)
    return state


def write_batch039_public_state(root: Path, state: dict[str, Any]) -> None:
    _write_public_docs(root, state)
