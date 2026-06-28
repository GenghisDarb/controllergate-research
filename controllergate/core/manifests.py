from __future__ import annotations

import re
from pathlib import Path, PurePosixPath
from typing import Iterable

from .evidence import sha256_file, write_text_lf


def reject_unsafe_paths(paths: Iterable[str]) -> list[str]:
    unsafe: list[str] = []
    for rel in paths:
        pure = PurePosixPath(rel)
        if rel.startswith("/") or "\\" in rel or any(part in {"", ".", ".."} for part in pure.parts):
            unsafe.append(rel)
    return unsafe


def read_sha256sums(path: str | Path) -> dict[str, str]:
    entries: dict[str, str] = {}
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        digest, rel = line.split(maxsplit=1)
        rel = rel.strip().lstrip("*")
        if not re.fullmatch(r"[0-9a-f]{64}", digest):
            raise ValueError(f"malformed digest for {rel}")
        if reject_unsafe_paths([rel]):
            raise ValueError(f"unsafe manifest path {rel}")
        entries[rel] = digest
    return entries


def write_sha256sums(root: str | Path, manifest_name: str = "SHA256SUMS.txt") -> Path:
    root_path = Path(root)
    rows = []
    for path in sorted(root_path.rglob("*")):
        if path.is_file() and path.name != manifest_name:
            rows.append(f"{sha256_file(path)}  {path.relative_to(root_path).as_posix()}")
    manifest = root_path / manifest_name
    write_text_lf(manifest, "\n".join(rows))
    return manifest


def resolve_manifest_paths_relative_to_manifest(manifest_path: str | Path) -> Path:
    return Path(manifest_path).parent


def verify_manifest(root: str | Path, manifest_name: str = "SHA256SUMS.txt") -> dict[str, object]:
    root_path = Path(root)
    entries = read_sha256sums(root_path / manifest_name)
    mismatches = []
    missing = []
    for rel, expected in entries.items():
        path = root_path / rel
        if not path.is_file():
            missing.append(rel)
        elif sha256_file(path) != expected:
            mismatches.append(rel)
    expected_files = {
        path.relative_to(root_path).as_posix()
        for path in root_path.rglob("*")
        if path.is_file() and path.name != manifest_name
    }
    extra = sorted(set(entries) - expected_files)
    uncovered = sorted(expected_files - set(entries))
    return {
        "status": "PASS" if not mismatches and not missing and not extra and not uncovered else "FAIL",
        "checked": len(entries),
        "mismatches": mismatches,
        "missing": missing,
        "extra": extra,
        "uncovered": uncovered,
    }
