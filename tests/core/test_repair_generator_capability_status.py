from __future__ import annotations

from controllergate.core.clean_repair import classify_repair_generator_capability


def test_generator_no_op_triggers_not_implemented_blocker() -> None:
    status = classify_repair_generator_capability(subset={"patchable_source_files": ["src/a.py"]}, patch=None, generator_invoked=False)
    assert status["capability_classification"] == "repair_generator_not_implemented"
    assert status["blocker"] == "clean_repair_generator_not_implemented"


def test_no_safe_patch_after_real_attempt_has_distinct_blocker() -> None:
    status = classify_repair_generator_capability(
        subset={"patchable_source_files": ["src/a.py"]},
        patch={"patch_candidate_generated": False, "blocker": "clean_repair_no_safe_source_patch_generated"},
        generator_invoked=True,
    )
    assert status["capability_classification"] == "safe_patch_generation_attempted_no_patch_found"
    assert status["blocker"] == "clean_repair_no_safe_source_patch_generated"


def test_empty_subset_has_derivation_blocker() -> None:
    status = classify_repair_generator_capability(subset={"patchable_source_files": []}, patch=None, generator_invoked=True)
    assert status["capability_classification"] == "patchable_source_subset_empty"
    assert status["blocker"] == "patchable_source_subset_derivation_failed"
