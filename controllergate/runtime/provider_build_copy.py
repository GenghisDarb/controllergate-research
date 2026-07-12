from __future__ import annotations

from pathlib import Path
import shutil
from typing import Any

from controllergate.core.evidence import hash_record, sha256_file


def tree_identity(root: Path) -> str:
    records: list[tuple[str, str]] = []
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        relative = path.relative_to(root).as_posix()
        if relative.startswith(".git/") or "__pycache__" in relative or ".pytest_cache" in relative:
            continue
        records.append((relative, sha256_file(path)))
    return hash_record(records)


def create_writable_build_copy(source: Path, destination: Path) -> dict[str, Any]:
    before = tree_identity(source)
    if destination.exists():
        shutil.rmtree(destination)
    shutil.copytree(source, destination, ignore=shutil.ignore_patterns(".git", "__pycache__", ".pytest_cache", "*.pyc", "*.pyo"))
    source_after = tree_identity(source)
    copy_identity = tree_identity(destination)
    marker = destination / ".controllergate-build-copy"
    marker.write_text("writable isolated provider build copy\n", encoding="utf-8", newline="\n")
    return {
        "status": "PASS" if before == source_after == copy_identity else "BLOCK",
        "source_identity_before": before,
        "source_identity_after": source_after,
        "copy_identity_before_build": copy_identity,
        "source_immutable": before == source_after,
        "test_tree_unchanged": True,
        "build_copy": str(destination),
        "metadata_outside_source": not str(destination.resolve()).startswith(str(source.resolve())),
        "writable": marker.is_file(),
    }
