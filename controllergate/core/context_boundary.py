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
    patchable = sorted(set(target_source_files) | set(imported_source_files) | set(traceback_source_files))
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
