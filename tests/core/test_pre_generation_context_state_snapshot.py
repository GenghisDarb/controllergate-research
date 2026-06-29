from __future__ import annotations

from controllergate.core.clean_repair import (
    build_pre_generation_context_state_snapshot,
    build_repair_intent_lock,
    patch_generation_context_allowed,
    repair_intent_alignment,
)


def test_patch_generation_fails_if_snapshot_missing_allowed_source():
    snapshot = {"snapshot_hash": "abc", "allowed_source_files": ["src/darker/config.py"]}
    patch = {"patch_file_paths": ["src/darker/tests/test_main_stdin_filename.py"]}

    result = patch_generation_context_allowed(snapshot, patch)

    assert result["status"] == "FAIL"
    assert result["blocker"] == "pre_generation_context_state_snapshot_violation"


def test_repair_intent_alignment_requires_locked_source_scope():
    intent = {
        "arm_id": "arm_a",
        "intended_source_scope": ["src/darker/config.py"],
    }
    patch = {
        "candidate_id": "darker_stdin_filename",
        "patch_file_paths": ["src/darker/config.py"],
        "patch_rationale": "stdin filename validation stays in the selected source function",
    }

    assert repair_intent_alignment(intent, patch)["status"] == "PASS"


def test_context_snapshot_records_memory_policy():
    snapshot = build_pre_generation_context_state_snapshot(
        "arm_a",
        {"candidate_id": "darker_stdin_filename", "repo_url": "https://example.invalid", "commit_sha": "a" * 40},
        {"context_capsule_hash": "capsule"},
        {"patchable_source_files": ["src/darker/config.py"]},
        {
            "target_command": ["python", "-m", "pytest"],
            "target_test_sha256": "b" * 64,
            "environment_file_sha256": "c" * 64,
            "semantic_failure_signature_hash": "d" * 64,
            "pre_repair_replay_hash": "e" * 64,
            "structural_repair_routing_map_hash": "f" * 64,
            "patchable_source_subset_hash": "1" * 64,
            "allowed_source_files": ["src/darker/config.py"],
            "forbidden_evidence_attestation": {"fixed_commits_used": False},
        },
        "memory_enabled_clean_repair",
    )

    assert snapshot["status"] == "PASS"
    assert snapshot["memory_policy"] == "memory_enabled_clean_repair"
    assert snapshot["patch_generation_reads_outside_snapshot"] is False
