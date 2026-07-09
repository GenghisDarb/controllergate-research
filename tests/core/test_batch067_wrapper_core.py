from __future__ import annotations

from pathlib import Path

from controllergate.core.abstention import make_abstention_record
from controllergate.core.command_translation import build_candidate_command_manifest, validate_candidate_command_manifest
from controllergate.core.harness_origin import validate_harness_origin_record
from controllergate.core.proof_ledger import make_failed_attempt_branch_record, validate_failed_attempt_branch_record
from controllergate.core.runner_target import classify_runner_target
from controllergate.core.source_topology import source_topology_patch_gate_policy, validate_source_topology_map
from controllergate.core.step_contracts import build_default_contract, validate_step_contract
from controllergate.core.terminal_states import terminal_state_registry, validate_terminal_state_record
from controllergate.core.version_origin import classify_version_origin
from controllergate.core.workspace_purity import audit_candidate_runtime_workspace


def test_default_step_contract_validates() -> None:
    assert validate_step_contract(build_default_contract()).status == "PASS"


def test_step_contract_rejects_missing_verifier() -> None:
    contract = build_default_contract()
    contract["steps"]["source_acquisition_step"]["output_verifiers"] = []
    result = validate_step_contract(contract)
    assert result.status == "FAIL"


def test_workspace_purity_rejects_workspace_inside_repo(tmp_path: Path) -> None:
    workspace = tmp_path / "repo" / "runtime"
    workspace.mkdir(parents=True)
    result = audit_candidate_runtime_workspace(workspace, repo_root=tmp_path / "repo")
    assert result["status"] == "BLOCK"
    assert "workspace_inside_repo_blocked" in result["blockers"]


def test_command_manifest_classifies_self_runner_collision() -> None:
    manifest = build_candidate_command_manifest(
        candidate_id="pytest_case",
        repo_url="https://example.invalid/pytest",
        candidate_sha="a" * 40,
        native_test_path="testing",
        declared_command_source="pyproject",
        declared_command_source_file="pyproject.toml",
        working_directory="/tmp/work",
        python_version="3.11",
        runner_package="pytest",
        target_package="pytest",
        command_string="python -m pytest testing",
    )
    assert manifest["command_boundary_status"] == "runner_target_collision_unresolved_self_runner"
    assert validate_candidate_command_manifest(manifest).status == "PASS"


def test_harness_origin_blocks_self_reference() -> None:
    record = {
        "source_url_or_repo": "https://example.invalid/repo",
        "source_commit_sha_or_bundle_identity": "a" * 40,
        "manifest_path": "manifest.json",
        "expected_manifest_sha256": "1" * 64,
        "observed_manifest_sha256": "1" * 64,
        "authority_source": "immutable_public_repo_commit",
        "authority_created_before_runtime": True,
        "self_referential_hash_detected": True,
        "target_test_path": "tests/test_x.py",
        "target_test_sha256": "2" * 64,
        "harness_topology_files": [],
        "pre_execution_sha256": "3" * 64,
        "post_execution_sha256": "3" * 64,
        "integrity_status": "PASS",
        "blocker_if_fail": "harness_origin_needed",
    }
    assert validate_harness_origin_record(record)["status"] == "FAIL"


def test_version_and_runner_classifiers() -> None:
    assert classify_version_origin(is_git_checkout=True, has_reachable_tags=False, dirty_workspace=False) == "version_origin_missing_tags"
    assert classify_runner_target(runner_package="pytest", target_package="pytest") == "runner_target_collision_unresolved_self_runner"


def test_terminal_state_and_safe_abstention_records() -> None:
    registry = terminal_state_registry()
    assert validate_terminal_state_record(registry["command_boundary_recovery_needed"])["status"] == "PASS"
    abstention = make_abstention_record(
        candidate_id="c",
        trigger="command_boundary_cannot_be_normalized",
        evidence_files=["evidence.json"],
        attempt_count=1,
        new_information_since_last_attempt=False,
        terminal_state="command_boundary_recovery_needed",
        reopen_condition="new_decision_time_safe_evidence",
        next_allowed_action="command_boundary_followup",
    )
    assert abstention["status"] == "PASS"


def test_source_topology_blocks_tests_only_contact() -> None:
    topology = {field: [] for field in source_topology_patch_gate_policy()["required_fields"]}
    topology["source_contact_to_failure_trace"] = "tests_only"
    assert validate_source_topology_map(topology)["status"] == "FAIL"


def test_failed_branch_record_validates() -> None:
    record = make_failed_attempt_branch_record(
        parent_evidence_entry="p",
        pre_attempt_source_head="a" * 40,
        pre_attempt_workspace_hash="1" * 64,
        pre_attempt_environment_hash="2" * 64,
        attempt_type="provider_setup",
        patch_sha256="NOT_APPLICABLE",
        provider_setup_hash="3" * 64,
        command_manifest_hash="4" * 64,
        attempt_status="BLOCK",
        failure_classification="command_boundary_failure",
        rollback_required=True,
        rollback_target_entry="p",
        branch_closed_without_count_increment=True,
        hash_chain_valid=True,
    )
    assert validate_failed_attempt_branch_record(record)["status"] == "PASS"
