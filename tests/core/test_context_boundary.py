from __future__ import annotations

from controllergate.core.context_boundary import build_context_boundary_map, no_candidate_source_interlock, validate_patch_context


def test_context_boundary_map_and_patch_guard():
    boundary = build_context_boundary_map(
        target_source_files=["src/a.py"],
        imported_source_files=[],
        traceback_source_files=["src/b.py"],
        support_files=["tests/data.txt"],
        environment_files=["pyproject.toml"],
    )
    assert boundary["status"] == "PASS"
    assert not no_candidate_source_interlock(boundary)
    assert validate_patch_context(["src/a.py"])["status"] == "PASS"
    assert validate_patch_context(["tests/test_a.py"])["blocker"] == "no_candidate_source_interlock_invariant"
