from __future__ import annotations

from pathlib import Path


def allowed_source_patch_paths(paths: list[str]) -> bool:
    forbidden = ("tests/", "test/", "src/darker/tests/", "configs/", ".github/", "outputs/", "scripts/audit_", "docs/")
    return all(not path.startswith(forbidden) for path in paths)


def forbidden_file_modification_guard(paths: list[str]) -> bool:
    return allowed_source_patch_paths(paths)


def patch_size_caps(diff_text: str, max_lines: int = 200) -> bool:
    return len(diff_text.splitlines()) <= max_lines


def source_only_patch_validation(paths: list[str], diff_text: str) -> dict[str, object]:
    return {"status": "PASS" if allowed_source_patch_paths(paths) and patch_size_caps(diff_text) else "FAIL"}


def target_validation(log_path: str | Path, exit_code: int) -> dict[str, object]:
    return {"status": "PASS" if exit_code == 0 else "FAIL", "log_path": str(log_path), "exit_code": exit_code}


def duplicate_clean_replay(results: list[int]) -> dict[str, object]:
    return {"status": "PASS" if results and all(code == 0 for code in results) else "FAIL", "passes": sum(code == 0 for code in results), "total": len(results)}


def target_validation_requires_exit_zero(exit_code: int) -> bool:
    return exit_code == 0


def duplicate_replay_requires_three_of_three(results: list[int]) -> bool:
    return len(results) == 3 and all(code == 0 for code in results)


def forbidden_patch_target_reason(path: str) -> str | None:
    if allowed_source_patch_paths([path]):
        return None
    return "forbidden_patch_target"
