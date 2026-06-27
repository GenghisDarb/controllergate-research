#!/usr/bin/env python3
"""Preflight SHA256SUMS byte custody before workflow dispatch.

The script verifies output manifests against canonical checkout bytes.  On
Windows, UTF-8 text files may appear with CRLF in the working tree even though
GitHub Actions will check them out as LF because of .gitattributes.  To catch
that class before dispatch, manifest hashes are computed over LF-canonical text
bytes while binary files retain exact bytes.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
REPORT_PATH = REPO_ROOT / "outputs" / "byte_custody_preflight_report.json"
ARCHIVE_SUFFIXES = {".zip", ".tar", ".gz", ".tgz", ".7z"}
MIN_DEFAULT_OUTPUT_VERSION = 12
SKIP_DIRS = {
    ".git",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    ".venv",
    "venv",
    "env",
    "node_modules",
    "ControllerGate-Artifacts",
}


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def git_config(key: str) -> str | None:
    result = subprocess.run(
        ["git", "config", "--get", key],
        cwd=str(REPO_ROOT),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        check=False,
    )
    return result.stdout.strip() if result.returncode == 0 and result.stdout.strip() else None


def is_safe_relative(path: str) -> bool:
    pure = PurePosixPath(path)
    return not path.startswith("/") and "\\" not in path and all(part not in {"", ".", ".."} for part in pure.parts)


def should_skip_path(path: Path) -> bool:
    rel_parts = path.relative_to(REPO_ROOT).parts if path.is_relative_to(REPO_ROOT) else path.parts
    if any(part in SKIP_DIRS for part in rel_parts):
        return True
    lower = path.name.lower()
    return any(lower.endswith(suffix) for suffix in ARCHIVE_SUFFIXES)


def canonical_bytes(path: Path) -> tuple[bytes, bool]:
    data = path.read_bytes()
    try:
        data.decode("utf-8")
    except UnicodeDecodeError:
        return data, False
    return data.replace(b"\r\n", b"\n"), True


def canonical_sha256(path: Path) -> tuple[str, bool]:
    data, text_mode = canonical_bytes(path)
    return hashlib.sha256(data).hexdigest(), text_mode


def actual_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def discover_manifests(explicit: list[str]) -> list[Path]:
    if explicit:
        return sorted({(REPO_ROOT / item).resolve() for item in explicit})
    manifests: list[Path] = []
    outputs_root = REPO_ROOT / "outputs"
    if outputs_root.is_dir():
        for path in outputs_root.glob("*/SHA256SUMS.txt"):
            rel = path.relative_to(outputs_root).as_posix()
            match = re.match(r"v2_(\d+)(?:_|[a-zA-Z])", rel)
            if match and int(match.group(1)) < MIN_DEFAULT_OUTPUT_VERSION:
                continue
            if not should_skip_path(path):
                manifests.append(path.resolve())
    return sorted(set(manifests))


def parse_manifest(manifest: Path) -> tuple[list[tuple[str, str]], list[str], list[str]]:
    entries: list[tuple[str, str]] = []
    malformed: list[str] = []
    duplicates: list[str] = []
    seen: set[str] = set()
    for line_no, line in enumerate(manifest.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        parts = line.split(maxsplit=1)
        if len(parts) != 2 or not re.fullmatch(r"[0-9a-f]{64}", parts[0]):
            malformed.append(f"{manifest}:{line_no}: malformed")
            continue
        digest, rel = parts
        if not is_safe_relative(rel):
            malformed.append(f"{manifest}:{line_no}: unsafe path {rel}")
            continue
        if rel in seen:
            duplicates.append(rel)
            continue
        seen.add(rel)
        entries.append((digest, rel))
    return entries, malformed, duplicates


def manifest_rows_for_root(root: Path) -> tuple[list[tuple[str, str]], int]:
    rows: list[tuple[str, str]] = []
    skipped_binary_count = 0
    for path in sorted(root.rglob("*")):
        if not path.is_file() or path.name == "SHA256SUMS.txt" or should_skip_path(path):
            if path.is_file() and should_skip_path(path):
                skipped_binary_count += 1
            continue
        rel = path.relative_to(root).as_posix()
        if not is_safe_relative(rel):
            continue
        digest, _ = canonical_sha256(path)
        rows.append((digest, rel))
    return rows, skipped_binary_count


def write_manifest(manifest: Path) -> int:
    rows, _ = manifest_rows_for_root(manifest.parent)
    manifest.write_bytes("".join(f"{digest}  {rel}\n" for digest, rel in rows).encode("utf-8"))
    return len(rows)


def verify_manifest(manifest: Path) -> dict[str, Any]:
    root = manifest.parent
    entries, malformed, duplicates = parse_manifest(manifest)
    mismatches: list[dict[str, Any]] = []
    missing: list[str] = []
    checked = 0
    skipped_binary_count = 0
    for expected, rel in entries:
        path = root / PurePosixPath(rel)
        if not path.is_file():
            missing.append(rel)
            continue
        if should_skip_path(path):
            skipped_binary_count += 1
            continue
        checked += 1
        actual = actual_sha256(path)
        canonical, text_mode = canonical_sha256(path)
        if expected != canonical:
            mismatches.append(
                {
                    "path": rel,
                    "expected": expected,
                    "actual_sha256": actual,
                    "canonical_lf_sha256": canonical,
                    "text_mode": text_mode,
                    "line_ending_sensitive": actual != canonical,
                }
            )
    expected_rows, expected_skipped = manifest_rows_for_root(root)
    expected_rels = {rel for _, rel in expected_rows}
    manifest_rels = {rel for _, rel in entries}
    for rel in sorted(expected_rels - manifest_rels):
        mismatches.append({"path": rel, "issue": "manifest_missing_entry"})
    for rel in sorted(manifest_rels - expected_rels):
        if not (root / PurePosixPath(rel)).is_file():
            continue
        mismatches.append({"path": rel, "issue": "manifest_extra_entry"})
    return {
        "manifest_path": manifest.relative_to(REPO_ROOT).as_posix() if manifest.is_relative_to(REPO_ROOT) else str(manifest),
        "checked_file_count": checked,
        "mismatch_count": len(mismatches),
        "missing_count": len(missing),
        "malformed_count": len(malformed),
        "duplicate_manifest_path_count": len(duplicates),
        "unsafe_path_count": sum(1 for item in malformed if "unsafe path" in item),
        "skipped_binary_count": skipped_binary_count + expected_skipped,
        "mismatches": mismatches,
        "missing": missing,
        "malformed": malformed,
        "duplicates": duplicates,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--fix", action="store_true", help="rewrite SHA256SUMS.txt with canonical LF checkout hashes")
    parser.add_argument("--manifest", action="append", default=[], help="explicit manifest path relative to repo root")
    args = parser.parse_args()

    manifests = discover_manifests(args.manifest)
    fixed_count = 0
    fix_records: list[dict[str, Any]] = []
    if args.fix:
        for manifest in manifests:
            if manifest.is_file():
                entries = write_manifest(manifest)
                fixed_count += 1
                fix_records.append(
                    {
                        "manifest_path": manifest.relative_to(REPO_ROOT).as_posix(),
                        "entry_count": entries,
                    }
                )

    manifest_reports = [verify_manifest(manifest) for manifest in manifests if manifest.is_file()]
    mismatch_count = sum(item["mismatch_count"] + item["missing_count"] + item["malformed_count"] for item in manifest_reports)
    duplicate_count = sum(item["duplicate_manifest_path_count"] for item in manifest_reports)
    unsafe_count = sum(item["unsafe_path_count"] for item in manifest_reports)
    checked_file_count = sum(item["checked_file_count"] for item in manifest_reports)
    skipped_binary_count = sum(item["skipped_binary_count"] for item in manifest_reports)
    status = "PASS" if mismatch_count == 0 and duplicate_count == 0 and unsafe_count == 0 else "FAIL"
    report = {
        "status": status,
        "generated_at_utc": utc_now(),
        "checked_manifest_count": len(manifest_reports),
        "checked_file_count": checked_file_count,
        "mismatch_count": mismatch_count,
        "fixed_count": fixed_count,
        "skipped_binary_count": skipped_binary_count,
        "unsafe_path_count": unsafe_count,
        "duplicate_manifest_path_count": duplicate_count,
        "platform": platform.platform(),
        "git_core_autocrlf": git_config("core.autocrlf"),
        "git_core_eol": git_config("core.eol"),
        "recommendation": "PASS" if status == "PASS" else "run python scripts/byte_custody_preflight.py --fix, review manifest-only changes, and rerun preflight",
        "fix_records": fix_records,
        "manifest_reports": manifest_reports,
    }
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_bytes((json.dumps(report, indent=2, sort_keys=True) + "\n").encode("utf-8"))
    print(f"byte_custody_preflight_status={status}")
    print(f"checked_manifest_count={report['checked_manifest_count']}")
    print(f"checked_file_count={report['checked_file_count']}")
    print(f"mismatch_count={report['mismatch_count']}")
    print(f"fixed_count={report['fixed_count']}")
    return 0 if status == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
