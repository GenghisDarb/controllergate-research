from __future__ import annotations

FORBIDDEN_PATCH_PREFIXES = (
    "tests/",
    "test/",
    "configs/",
    ".github/",
    "scripts/",
    "outputs/",
    "docs/",
)


def build_context_boundary_map(
    *,
    target_source_files: list[str],
    imported_source_files: list[str],
    traceback_source_files: list[str],
    support_files: list[str],
    environment_files: list[str],
) -> dict[str, object]:
    candidate_paths = sorted(set(target_source_files) | set(imported_source_files) | set(traceback_source_files))
    patchable = [path for path in candidate_paths if validate_patch_context([path])["status"] == "PASS"]
    excluded = sorted(set(support_files) | set(environment_files))
    return {
        "status": "PASS" if patchable else "BLOCK",
        "patchable_source_files": patchable,
        "read_only_support_files": sorted(set(support_files)),
        "read_only_environment_files": sorted(set(environment_files)),
        "excluded_files": excluded,
    }


def no_candidate_source_interlock(boundary: dict[str, object]) -> bool:
    return not boundary.get("patchable_source_files")


def validate_patch_context(paths: list[str]) -> dict[str, object]:
    forbidden = [path for path in paths if path.startswith(FORBIDDEN_PATCH_PREFIXES)]
    return {
        "status": "PASS" if not forbidden else "BLOCK",
        "forbidden_paths": forbidden,
        "blocker": "no_candidate_source_interlock_invariant" if forbidden else None,
    }


def validate_context_state_lock_reads(read_paths: list[str], allowed_source_files: list[str], target_test_path: str) -> dict[str, object]:
    allowed = set(allowed_source_files) | {target_test_path}
    outside = [path for path in read_paths if path not in allowed]
    return {
        "status": "PASS" if not outside else "BLOCK",
        "outside_lock_paths": outside,
        "blocker": None if not outside else "pre_generation_context_state_lock_violation",
    }


def patch_context_aligned_with_subset(patch_paths: list[str], allowed_source_files: list[str]) -> bool:
    allowed = set(allowed_source_files)
    return bool(patch_paths) and all(path in allowed for path in patch_paths)
