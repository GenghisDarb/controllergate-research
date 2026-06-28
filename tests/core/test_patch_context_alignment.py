from __future__ import annotations

from controllergate.core.clean_repair import patch_context_alignment_audit
from controllergate.core.context_boundary import patch_context_aligned_with_subset
from controllergate.core.patch_safety import forbidden_patch_target_reason


def test_patch_context_alignment_fails_on_forbidden_file_modification():
    audit = patch_context_alignment_audit(
        {"candidate_id": "candidate", "patch_candidate_generated": True, "patch_file_paths": ["tests/test_a.py"]},
        {"candidate_id": "candidate", "allowed_source_files": ["src/a.py"]},
    )

    assert audit["blocker"] == "patch_context_alignment_failed"
    assert forbidden_patch_target_reason("tests/test_a.py") == "forbidden_patch_target"


def test_patch_context_alignment_requires_structural_subset():
    assert patch_context_aligned_with_subset(["src/a.py"], ["src/a.py"])
    assert not patch_context_aligned_with_subset(["src/b.py"], ["src/a.py"])
