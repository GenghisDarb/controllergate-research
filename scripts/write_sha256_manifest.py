#!/usr/bin/env python3
"""Write deterministic SHA256SUMS.txt manifests for ControllerGate outputs."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_EXCLUDES = {
    ".git",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    ".venv",
    "venv",
    "env",
    "node_modules",
}
ARCHIVE_SUFFIXES = {".zip", ".tar", ".gz", ".tgz", ".7z"}


def is_safe_relative(path: str) -> bool:
    pure = PurePosixPath(path)
    return not path.startswith("/") and "\\" not in path and all(part not in {"", ".", ".."} for part in pure.parts)


def is_excluded(path: Path) -> bool:
    parts = set(path.parts)
    if parts & DEFAULT_EXCLUDES:
        return True
    lower = path.name.lower()
    return any(lower.endswith(suffix) for suffix in ARCHIVE_SUFFIXES)


def canonical_hash_bytes(path: Path) -> bytes:
    data = path.read_bytes()
    try:
        data.decode("utf-8")
    except UnicodeDecodeError:
        return data
    return data.replace(b"\r\n", b"\n")


def sha256_path(path: Path) -> str:
    return hashlib.sha256(canonical_hash_bytes(path)).hexdigest()


def write_manifest(root: Path, manifest_name: str = "SHA256SUMS.txt") -> dict[str, object]:
    root = root.resolve()
    manifest_path = root / manifest_name
    if not root.is_dir():
        raise SystemExit(f"manifest root is not a directory: {root}")
    rows: list[tuple[str, str]] = []
    unsafe_paths: list[str] = []
    duplicates: set[str] = set()
    seen: set[str] = set()
    skipped_binary_count = 0
    for path in sorted(root.rglob("*")):
        if not path.is_file() or path == manifest_path:
            continue
        rel = path.relative_to(root).as_posix()
        if is_excluded(path):
            skipped_binary_count += 1
            continue
        if not is_safe_relative(rel):
            unsafe_paths.append(rel)
            continue
        if rel in seen:
            duplicates.add(rel)
            continue
        seen.add(rel)
        rows.append((sha256_path(path), rel))
    if unsafe_paths:
        raise SystemExit(f"unsafe manifest path(s): {unsafe_paths}")
    if duplicates:
        raise SystemExit(f"duplicate manifest path(s): {sorted(duplicates)}")
    manifest_text = "".join(f"{digest}  {rel}\n" for digest, rel in rows)
    manifest_path.write_bytes(manifest_text.encode("utf-8"))
    return {
        "manifest_path": manifest_path.relative_to(REPO_ROOT).as_posix() if manifest_path.is_relative_to(REPO_ROOT) else str(manifest_path),
        "entry_count": len(rows),
        "skipped_binary_count": skipped_binary_count,
        "unsafe_path_count": len(unsafe_paths),
        "duplicate_manifest_path_count": len(duplicates),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("root", help="directory whose files should be covered by SHA256SUMS.txt")
    parser.add_argument("--manifest-name", default="SHA256SUMS.txt")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    report = write_manifest(Path(args.root), args.manifest_name)
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(f"manifest_path={report['manifest_path']}")
        print(f"entry_count={report['entry_count']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
