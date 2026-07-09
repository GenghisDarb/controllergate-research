from __future__ import annotations

from controllergate.core.ast_homology import make_ast_homology_record, shape_hash, validate_ast_homology_record
from controllergate.core.baseline_registry import make_baseline_record, validate_baseline_record
from controllergate.core.cognitive_state import build_cognitive_state_snapshot, validate_cognitive_state_snapshot
from controllergate.core.reward_signal import build_reward_signal, validate_reward_signal


def test_cognitive_state_snapshot_blocks_generation_inversion() -> None:
    snapshot = build_cognitive_state_snapshot(
        candidate_id="pytest_case",
        batch_id="batch063c",
        prompt_string="no patch generated in this batch",
        context_window_manifest={"inputs": ["a"]},
        decision_time_input_hashes={"a": "1" * 64},
        ast_snippet_hashes={},
        command_manifest={"command": "python -m pytest testing"},
        harness_origin={"origin": "buggy checkout"},
        workspace_purity={"status": "PASS"},
        provider_capsule={"status": "PASS"},
        generation_output_exists_at_snapshot_time=True,
    )
    result = validate_cognitive_state_snapshot(snapshot, generation_output_exists=True)
    assert result["status"] == "FAIL"
    assert "cognitive_state_timestamp_inversion" in result["errors"]


def test_valid_cognitive_state_snapshot_passes() -> None:
    snapshot = build_cognitive_state_snapshot(
        candidate_id="pytest_case",
        batch_id="batch063c",
        prompt_string="locked prompt",
        context_window_manifest={"inputs": ["a"]},
        decision_time_input_hashes={"a": "1" * 64},
        ast_snippet_hashes={},
        command_manifest={"command": "python -m pytest testing"},
        harness_origin={"origin": "buggy checkout"},
        workspace_purity={"status": "PASS"},
        provider_capsule={"status": "PASS"},
    )
    assert validate_cognitive_state_snapshot(snapshot)["status"] == "PASS"


def test_precondition_unavailable_reward_is_zero_and_routing_only() -> None:
    signal = build_reward_signal(
        candidate_id="pytest_case",
        attempt_id="batch063c",
        failure_surface="version_origin_missing_tags_without_safe_authority",
        terminal_state="pytest_command_boundary_blocked_version_origin",
        repair_attempted=False,
        patch_generated=False,
        patch_applied=False,
        target_replay_run=False,
    )
    assert signal["graded_signal"] == 0.0
    assert signal["memory_update_forbidden_reason"] == "repair_skill_memory_forbidden_routing_abstention_only"
    assert validate_reward_signal(signal)["status"] == "PASS"


def test_baseline_registry_isolated_runtime_allows_acquisition() -> None:
    record = make_baseline_record(
        baseline_record_id="cloudpickle_counted_lineage",
        candidate_id="cloudpickle",
        repair_count_status="counted",
        source_head_sha="a" * 40,
        patch_sha256="b" * 64,
        provider_capsule={"candidate": "cloudpickle"},
        command_manifest={"command": "pytest"},
        environment_lock={"python": "3.11"},
        expected_replay_command="pytest",
        isolated_runtime=True,
    )
    assert record["exact_blocker"] is None
    assert validate_baseline_record(record)["status"] == "PASS"


def test_ast_homology_record_never_authorizes_patch() -> None:
    record = make_ast_homology_record(
        pattern_id="command_boundary_shape",
        source_candidate_id="cloudpickle",
        target_candidate_id="pytest",
        source_repo_family="serialization",
        target_repo_family="test_runner",
        source_language="python",
        target_language="python",
        source_ast_shape_hash=shape_hash({"nodes": ["class", "dict"]}),
        target_ast_shape_hash=shape_hash({"nodes": ["config", "runner"]}),
        source_symbol_roles={"symbol": "source"},
        target_symbol_roles={"symbol": "runner"},
        control_flow_shape={"kind": "localized"},
        data_flow_shape={"kind": "metadata"},
        exception_flow_shape={"kind": "boundary"},
        import_dependency_shape={"kind": "runner-target"},
        test_to_source_contact_shape={"kind": "indirect"},
        patch_shape_if_known=None,
        source_repair_result="counted_elsewhere",
        target_repair_status="blocked_command_boundary",
    )
    assert validate_ast_homology_record(record)["status"] == "PASS"
    record["patch_authority_allowed"] = True
    assert validate_ast_homology_record(record)["status"] == "FAIL"
