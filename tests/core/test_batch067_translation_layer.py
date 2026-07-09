from __future__ import annotations

from controllergate.core.candidate_seed_classes import classify_seed_for_repair, seed_promotion_policy
from controllergate.core.cross_family_homology import validate_homology_record
from controllergate.core.environment_orthology import FORBIDDEN_USES, validate_orthology_record
from controllergate.core.failure_translation import signature_hash, validate_failure_signature
from controllergate.core.source_approval import evaluate_source_approval


def test_orthology_record_is_routing_only() -> None:
    record = {
        "source_failure_id": "s",
        "target_failure_id": "t",
        "source_candidate_id": "a",
        "target_candidate_id": "b",
        "source_project": "p1",
        "target_project": "p2",
        "source_environment": "env1",
        "target_environment": "env2",
        "source_python_version": "3.11",
        "target_python_version": "3.11",
        "source_os": "ubuntu",
        "target_os": "ubuntu",
        "source_runner": "pytest",
        "target_runner": "pytest",
        "source_command_manifest_hash": "1" * 64,
        "target_command_manifest_hash": "2" * 64,
        "source_provider_capsule_hash": "3" * 64,
        "target_provider_capsule_hash": "4" * 64,
        "source_harness_origin_hash": "5" * 64,
        "target_harness_origin_hash": "6" * 64,
        "source_failure_signature_hash": "7" * 64,
        "target_failure_signature_hash": "8" * 64,
        "shared_structural_features": ["runner-target boundary"],
        "different_structural_features": ["version origin"],
        "constraint_type": "environment_constraint_map",
        "transfer_class": "same_project_different_environment",
        "allowed_use": ["routing_memory_only", "command_translation_hint"],
        "forbidden_use": FORBIDDEN_USES,
        "decision_time_safe": True,
        "requires_manual_review": True,
        "reopen_condition": "new_manifest_hashes",
        "audit_status": "PASS",
    }
    assert validate_orthology_record(record)["status"] == "PASS"


def test_orthology_transfer_seed_cannot_patch_until_promoted() -> None:
    seed = {
        "seed_id": "seed",
        "candidate_id": "candidate",
        "source_type": "orthology_transfer",
        "source_url_or_path": "registry",
        "source_hash": "1" * 64,
        "custody_status": "hash_pinned",
        "discovered_by": "routing_memory",
        "decision_time_safe": True,
        "label_blind": True,
        "gold_patch_excluded": True,
        "future_evidence_excluded": True,
        "approval_status": "not_promoted",
        "approval_requirements": ["manual_custody_review"],
        "allowed_next_actions": ["preflight_probe_selection"],
        "forbidden_next_actions": ["patch_generation"],
        "promotion_required_before_repair": True,
        "exact_blocker_if_not_approved": "blocked_unpromoted_orthology_seed_used_for_patch_generation",
    }
    result = classify_seed_for_repair(seed)
    assert result["repair_generation_allowed"] is False
    assert result["blocker"] == "blocked_unpromoted_orthology_seed_used_for_patch_generation"
    assert seed_promotion_policy()["probe_only_sources_do_not_enter_candidate_inventory"] is True


def test_failure_signature_separates_provider_from_source_failure() -> None:
    signature = {
        "exception_type": "ModuleNotFoundError",
        "returncode": 1,
        "command_kind": "pre_repair_replay",
        "runner_package": "pytest",
        "target_package": "target",
        "working_directory": "/tmp/work",
        "python_version": "3.11",
        "os": "ubuntu",
        "dependency_state": "missing",
        "missing_module_or_fixture": "missing_pkg",
        "failing_test_path": "tests/test_x.py",
        "failing_test_symbol": "test_x",
        "source_contact_files": [],
        "provider_surface": ["requirements.txt"],
        "source_surface": [],
        "harness_surface": [],
        "workspace_surface": [],
        "classification": "provider_failure",
    }
    signature["signature_hash"] = signature_hash(signature)
    result = validate_failure_signature(signature)
    assert result["status"] == "PASS"
    assert result["classification"] == "provider_failure"


def test_cross_family_homology_is_not_repair_authority() -> None:
    record = {
        "source_candidate": "a",
        "target_candidate": "b",
        "family": "command_boundary",
        "shared_features": ["returncode"],
        "non_shared_features": ["provider"],
        "evidence_files": ["file.json"],
        "decision_time_safe": True,
        "routing_use_allowed": True,
        "patch_authority_allowed": False,
        "repair_proof_allowed": False,
        "memory_lift_evidence_allowed": False,
        "count_gate_evidence_allowed": False,
        "audit_status": "PASS",
    }
    assert validate_homology_record(record)["status"] == "PASS"


def test_probe_only_source_is_not_candidate_inventory() -> None:
    result = evaluate_source_approval({"source_class": "probe_only", "approval_status": "not_approved", "probe_only": True})
    assert result["approved_for_candidate_inventory"] is False
    assert result["blocker"] == "manual_artifact_custody_or_external_source_approval_required_for_new_unused_candidate_seed"
