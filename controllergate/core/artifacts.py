from __future__ import annotations

import hashlib
import re
import shutil
import zipfile
from pathlib import Path, PurePosixPath
from typing import Iterable

from .evidence import sha256_file

ARCHIVE_OR_CACHE_SUFFIXES = (".zip", ".tar", ".tar.gz", ".tgz", ".7z", ".pyc", ".pyo", ".whl")
CACHE_PARTS = {"__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache", ".venv", "venv", "env", "ENV"}


def is_safe_zip_member(name: str) -> bool:
    pure = PurePosixPath(name)
    return not (
        name.startswith("/")
        or "\\" in name
        or any(part in {"", ".", ".."} for part in pure.parts)
    )


def duplicate_zip_members(names: Iterable[str]) -> list[str]:
    seen: set[str] = set()
    duplicates: list[str] = []
    for name in names:
        if name in seen:
            duplicates.append(name)
        seen.add(name)
    return duplicates


def is_archive_or_cache_payload(name: str) -> bool:
    pure = PurePosixPath(name)
    lowered = name.lower()
    return any(part in CACHE_PARTS for part in pure.parts) or lowered.endswith(ARCHIVE_OR_CACHE_SUFFIXES)


def audit_zip_entries(zip_path: str | Path) -> dict[str, object]:
    path = Path(zip_path)
    with zipfile.ZipFile(path) as archive:
        names = archive.namelist()
    unsafe = [name for name in names if not is_safe_zip_member(name)]
    duplicates = duplicate_zip_members(names)
    pycache = [name for name in names if "__pycache__" in PurePosixPath(name).parts]
    pyc = [name for name in names if name.endswith((".pyc", ".pyo"))]
    nested_archives = [name for name in names if is_archive_or_cache_payload(name) and name not in {"ARTIFACT_SHA256SUMS.txt", "SHA256SUMS.txt"}]
    return {
        "status": "PASS" if not unsafe and not duplicates and not pycache and not pyc else "FAIL",
        "entry_count": len(names),
        "unsafe_paths": unsafe,
        "unsafe_path_count": len(unsafe),
        "duplicate_paths": duplicates,
        "duplicate_path_count": len(duplicates),
        "pycache_payloads": pycache,
        "pycache_payload_count": len(pycache),
        "pyc_payloads": pyc,
        "pyc_payload_count": len(pyc),
        "nested_archive_or_cache_payloads": nested_archives,
    }


def verify_outer_zip_identity(
    zip_path: str | Path,
    *,
    expected_size: int | None = None,
    expected_sha256: str | None = None,
) -> dict[str, object]:
    path = Path(zip_path)
    digest = sha256_file(path)
    size = path.stat().st_size
    return {
        "status": "PASS"
        if (expected_size is None or size == expected_size)
        and (expected_sha256 is None or digest == expected_sha256.lower())
        else "FAIL",
        "path": str(path),
        "size_bytes": size,
        "sha256": digest,
        "expected_size_bytes": expected_size,
        "expected_sha256": expected_sha256.lower() if expected_sha256 else None,
    }


def _parse_manifest_line(line: str) -> tuple[str, str]:
    parts = line.split(maxsplit=1)
    if len(parts) != 2:
        raise ValueError("manifest_line_malformed")
    digest, rel = parts
    rel = rel.strip().lstrip("*")
    if not re.fullmatch(r"[0-9a-fA-F]{64}", digest):
        raise ValueError("manifest_digest_malformed")
    if not is_safe_zip_member(rel):
        raise ValueError("manifest_path_unsafe")
    return digest.lower(), rel


def verify_zip_manifest(zip_path: str | Path, manifest_name: str) -> dict[str, object]:
    checked = 0
    missing: list[str] = []
    malformed: list[str] = []
    failures: list[str] = []
    with zipfile.ZipFile(zip_path) as archive:
        names = set(archive.namelist())
        if manifest_name not in names:
            return {
                "status": "FAIL",
                "manifest": manifest_name,
                "checked": 0,
                "missing_manifest": True,
                "missing": [],
                "malformed": [],
                "failures": [],
            }
        text = archive.read(manifest_name).decode("utf-8")
        for line in text.splitlines():
            if not line.strip():
                continue
            try:
                expected, rel = _parse_manifest_line(line)
            except ValueError:
                malformed.append(line)
                continue
            if rel not in names:
                missing.append(rel)
                continue
            checked += 1
            if hashlib.sha256(archive.read(rel)).hexdigest() != expected:
                failures.append(rel)
    return {
        "status": "PASS" if not missing and not malformed and not failures else "FAIL",
        "manifest": manifest_name,
        "checked": checked,
        "missing_manifest": False,
        "missing": missing,
        "malformed": malformed,
        "failures": failures,
    }


def verify_artifact_zip(
    zip_path: str | Path,
    *,
    expected_size: int | None = None,
    expected_sha256: str | None = None,
    manifest_names: tuple[str, ...] = ("ARTIFACT_SHA256SUMS.txt", "SHA256SUMS.txt"),
) -> dict[str, object]:
    outer = verify_outer_zip_identity(zip_path, expected_size=expected_size, expected_sha256=expected_sha256)
    entries = audit_zip_entries(zip_path)
    manifests = {name: verify_zip_manifest(zip_path, name) for name in manifest_names}
    status = "PASS" if outer["status"] == "PASS" and entries["status"] == "PASS" and all(item["status"] == "PASS" for item in manifests.values()) else "FAIL"
    return {"status": status, "outer": outer, "entries": entries, "manifests": manifests}


def safe_copy_verified_payload(
    zip_path: str | Path,
    destination: str | Path,
    *,
    allowed_prefixes: tuple[str, ...] = (),
) -> dict[str, object]:
    dest = Path(destination)
    copied: list[str] = []
    skipped: list[str] = []
    if dest.exists():
        shutil.rmtree(dest)
    dest.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zip_path) as archive:
        for name in archive.namelist():
            if name.endswith("/") or name in {"ARTIFACT_SHA256SUMS.txt"}:
                skipped.append(name)
                continue
            if allowed_prefixes and not any(name == prefix or name.startswith(prefix.rstrip("/") + "/") for prefix in allowed_prefixes):
                skipped.append(name)
                continue
            if not is_safe_zip_member(name) or is_archive_or_cache_payload(name):
                skipped.append(name)
                continue
            target = dest / Path(*PurePosixPath(name).parts)
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(archive.read(name))
            copied.append(target.relative_to(dest).as_posix())
    return {"status": "PASS", "copied_files": sorted(copied), "skipped_files": sorted(skipped), "raw_zip_payload_copied": False}
