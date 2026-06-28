from __future__ import annotations

from controllergate.core.clean_repair import build_pre_generation_context_state_lock
from controllergate.core.context_boundary import validate_context_state_lock_reads
from controllergate.core.replay import pre_repair_replay_allows_patch_generation


def test_patch_generation_requires_pre_repair_replay_signature():
    assert pre_repair_replay_allows_patch_generation({"status": "PRE_PATCH_FAILURE_OBSERVED", "semantic_failure_signature_hash": "s" * 64})
    assert not pre_repair_replay_allows_patch_generation({"status": "PASSING_PRE_PATCH_NOT_A_FAILURE"})


def test_context_state_lock_blocks_outside_reads():
    lock = build_pre_generation_context_state_lock(
        {"candidate_id": "candidate", "repo_url": "https://example.invalid/repo.git", "commit_sha": "1" * 40},
        {
            "target_command": ["python", "-m", "pytest"],
            "target_test_path": "tests/test_a.py",
            "target_test_sha256": "t" * 64,
            "environment_files": [{"path": "pyproject.toml", "sha256": "e" * 64}],
            "semantic_failure_signature_hash": "s" * 64,
            "pre_repair_replay_hash": "r" * 64,
            "context_capsule_hash": "c" * 64,
        },
        {"patchable_source_files": ["src/a.py"]},
        {"candidate_id": "candidate"},
    )

    assert lock["allowed_source_files"] == ["src/a.py"]
    assert validate_context_state_lock_reads(["src/a.py", "tests/test_a.py"], ["src/a.py"], "tests/test_a.py")["status"] == "PASS"
    assert validate_context_state_lock_reads(["docs/notes.md"], ["src/a.py"], "tests/test_a.py")["blocker"] == "pre_generation_context_state_lock_violation"
