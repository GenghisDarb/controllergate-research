from __future__ import annotations

import hashlib
import json
import time
import zipfile
from pathlib import Path, PurePosixPath
from typing import Any


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: str | Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _unsafe_zip_name(name: str) -> bool:
    pure = PurePosixPath(name)
    return name.startswith("/") or "\\" in name or any(part in {"", ".", ".."} for part in pure.parts)


def safe_zip_paths(zip_path: str | Path) -> list[str]:
    with zipfile.ZipFile(zip_path) as archive:
        return [name for name in archive.namelist() if not _unsafe_zip_name(name)]


def duplicate_zip_paths(zip_path: str | Path) -> list[str]:
    seen: set[str] = set()
    duplicates: list[str] = []
    with zipfile.ZipFile(zip_path) as archive:
        for name in archive.namelist():
            lowered = name.lower()
            if lowered in seen:
                duplicates.append(name)
            seen.add(lowered)
    return duplicates


def verify_internal_sha256sums(zip_path: str | Path, manifest_path: str, base_prefix: str = "") -> dict[str, Any]:
    checked = missing = malformed = failures = 0
    with zipfile.ZipFile(zip_path) as archive:
        names = set(archive.namelist())
        text = archive.read(manifest_path).decode("utf-8")
        for line in text.splitlines():
            if not line.strip():
                continue
            parts = line.split(maxsplit=1)
            if len(parts) != 2:
                malformed += 1
                continue
            expected, rel = parts
            rel = rel.strip().lstrip("*")
            while rel.startswith("./"):
                rel = rel[2:]
            target = f"{base_prefix.rstrip('/')}/{rel}" if base_prefix else rel
            if len(expected) != 64 or _unsafe_zip_name(rel):
                malformed += 1
            elif target not in names:
                missing += 1
            else:
                checked += 1
                if sha256_bytes(archive.read(target)) != expected:
                    failures += 1
    return {"checked": checked, "missing": missing, "malformed": malformed, "failures": failures}


def verify_zip_artifact(zip_path: str | Path, *, expected_size: int | None = None, expected_sha256: str | None = None) -> dict[str, Any]:
    path = Path(zip_path)
    with zipfile.ZipFile(path) as archive:
        names = archive.namelist()
    actual_sha = sha256_file(path)
    unsafe_count = len(names) - len(safe_zip_paths(path))
    duplicate_count = len(duplicate_zip_paths(path))
    return {
        "status": "PASS"
        if (expected_size is None or path.stat().st_size == expected_size)
        and (expected_sha256 is None or actual_sha == expected_sha256)
        and unsafe_count == 0
        and duplicate_count == 0
        else "FAIL",
        "size": path.stat().st_size,
        "sha256": actual_sha,
        "entry_count": len(names),
        "unsafe_path_count": unsafe_count,
        "duplicate_path_count": duplicate_count,
    }


def _write_bytes_retrying(target: Path, data: bytes, *, attempts: int = 3) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    temp = target.with_name(f"{target.name}.tmp_write")
    last_error: OSError | None = None
    for attempt in range(1, attempts + 1):
        try:
            temp.write_bytes(data)
            temp.replace(target)
            return
        except OSError as exc:
            last_error = exc
            if temp.exists():
                try:
                    temp.unlink()
                except OSError:
                    pass
            if attempt < attempts:
                time.sleep(0.1 * attempt)
    if last_error is not None:
        raise last_error


def write_json_deterministic(path: str | Path, value: Any) -> None:
    target = Path(path)
    _write_bytes_retrying(target, (json.dumps(value, indent=2, sort_keys=True) + "\n").encode("utf-8"))


def write_text_lf(path: str | Path, value: str) -> None:
    target = Path(path)
    _write_bytes_retrying(target, (value.rstrip() + "\n").encode("utf-8"))


def hash_record(value: Any) -> str:
    return sha256_bytes(json.dumps(value, sort_keys=True, default=str).encode("utf-8"))
