from __future__ import annotations

import time
import zipfile
from pathlib import Path, PurePosixPath
from typing import Any

from .evidence import sha256_bytes, sha256_file


ARCHIVE_SUFFIXES = (".zip", ".tar", ".tar.gz", ".tgz", ".7z", ".pyc", ".pyo", ".whl")


def is_safe_zip_member(name: str) -> bool:
    pure = PurePosixPath(name)
    return not (
        name.startswith("/")
        or "\\" in name
        or any(part in {"", ".", ".."} for part in pure.parts)
    )


def verify_zip_manifest(
    archive: zipfile.ZipFile,
    manifest_name: str,
    *,
    base_prefix: str | None = None,
) -> dict[str, Any]:
    names = set(archive.namelist())
    if manifest_name not in names:
        return {"status": "MISSING", "manifest": manifest_name, "checked": 0, "failures": 1, "missing": [manifest_name]}
    checked = 0
    failures: list[str] = []
    missing: list[str] = []
    malformed: list[str] = []
    for line in archive.read(manifest_name).decode("utf-8").splitlines():
        if not line.strip():
            continue
        parts = line.split(maxsplit=1)
        if len(parts) != 2:
            malformed.append(line)
            continue
        expected, rel = parts
        rel = rel.strip().lstrip("*")
        while rel.startswith("./"):
            rel = rel[2:]
        target = f"{base_prefix.rstrip('/')}/{rel}" if base_prefix else rel
        if len(expected) != 64 or not is_safe_zip_member(rel):
            malformed.append(rel)
            continue
        if target not in names:
            missing.append(target)
            continue
        checked += 1
        if sha256_bytes(archive.read(target)) != expected:
            failures.append(target)
    return {
        "status": "PASS" if not failures and not missing and not malformed else "FAIL",
        "manifest": manifest_name,
        "checked": checked,
        "failures": len(failures),
        "failure_paths": failures,
        "missing": missing,
        "malformed": malformed,
    }


def verify_official_zip(
    zip_path: str | Path,
    *,
    artifact_name: str,
    artifact_id: int,
    workflow_run_id: int,
    workflow_head_sha: str,
    expected_sha256: str,
    expected_size: int,
    expected_entry_count: int,
    artifact_manifest_checked: int,
    output_manifests: dict[str, tuple[str, int]],
) -> dict[str, Any]:
    path = Path(zip_path)
    digest = sha256_file(path) if path.is_file() else None
    size = path.stat().st_size if path.is_file() else None
    if not path.is_file():
        return {
            "status": "BLOCK",
            "artifact_name": artifact_name,
            "artifact_id": artifact_id,
            "workflow_run_id": workflow_run_id,
            "workflow_head_sha": workflow_head_sha,
            "exact_blocker": "manual_official_artifact_zip_missing",
        }
    with zipfile.ZipFile(path) as archive:
        names = archive.namelist()
        unsafe = [name for name in names if not is_safe_zip_member(name)]
        duplicates = len(names) - len(set(names))
        pycache_entries = [name for name in names if "__pycache__" in PurePosixPath(name).parts]
        pyc_entries = [name for name in names if name.endswith((".pyc", ".pyo"))]
        nested_archives = [name for name in names if name.lower().endswith((".zip", ".tar", ".tar.gz", ".tgz", ".7z"))]
        wheel_entries = [name for name in names if name.lower().endswith(".whl")]
        compiled_python_entries = [name for name in names if name.lower().endswith((".pyc", ".pyo", ".so", ".pyd", ".dll", ".dylib"))]
        cache_entries = [name for name in names if any(part in {"__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache"} for part in PurePosixPath(name).parts)]
        virtualenv_entries = [name for name in names if any(part in {".venv", "venv", "virtualenv"} for part in PurePosixPath(name).parts)]
        artifact_manifest = verify_zip_manifest(archive, "ARTIFACT_SHA256SUMS.txt")
        output_manifest_records = {
            key: verify_zip_manifest(archive, manifest, base_prefix=key)
            for key, (manifest, _expected) in output_manifests.items()
        }
    manifest_counts_pass = (
        artifact_manifest["status"] == "PASS"
        and artifact_manifest["checked"] == artifact_manifest_checked
        and all(
            record["status"] == "PASS" and record["checked"] == expected
            for key, record in output_manifest_records.items()
            for _manifest, expected in [output_manifests[key]]
        )
    )
    status = (
        "PASS"
        if digest == expected_sha256
        and size == expected_size
        and len(names) == expected_entry_count
        and not unsafe
        and duplicates == 0
        and not pycache_entries
        and not pyc_entries
        and not nested_archives
        and not wheel_entries
        and not compiled_python_entries
        and not cache_entries
        and not virtualenv_entries
        and manifest_counts_pass
        else "BLOCK"
    )
    return {
        "status": status,
        "verification_source": "local_manual_artifact_zip",
        "local_artifact_path": str(path),
        "artifact_name": artifact_name,
        "artifact_id": artifact_id,
        "workflow_run_id": workflow_run_id,
        "workflow_head_sha": workflow_head_sha,
        "zip_sha256": digest,
        "artifact_sha256": digest,
        "zip_size_bytes": size,
        "artifact_size_bytes": size,
        "zip_entry_count": len(names),
        "unsafe_path_count": len(unsafe),
        "duplicate_path_count": duplicates,
        "zip_pycache_entries": len(pycache_entries),
        "zip_pyc_entries": len(pyc_entries),
        "nested_archive_count": len(nested_archives),
        "wheel_payload_count": len(wheel_entries),
        "compiled_python_payload_count": len(compiled_python_entries),
        "cache_payload_count": len(cache_entries),
        "virtualenv_payload_count": len(virtualenv_entries),
        "artifact_manifest": artifact_manifest,
        "output_manifests": output_manifest_records,
        "raw_zip_bytes_ingested": False,
        "zip_payload_committed": False,
        "exact_blocker": None if status == "PASS" else "official_artifact_zip_verification_failed",
    }


def idempotent_write_bytes(target: Path, data: bytes, *, retries: int = 3) -> dict[str, Any]:
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.is_file() and target.read_bytes() == data:
        return {"status": "SKIPPED_IDENTICAL", "path": str(target), "changed": False}
    temp = target.with_name(f"{target.name}.official_ingest_tmp")
    for attempt in range(1, retries + 1):
        try:
            temp.write_bytes(data)
            temp.replace(target)
            return {"status": "WRITTEN_ATOMIC_REPLACE", "path": str(target), "attempt": attempt, "changed": True}
        except PermissionError as exc:
            if attempt == retries:
                return {
                    "status": "BLOCK",
                    "path": str(target),
                    "attempt": attempt,
                    "exact_blocker": "windows_idempotent_ingest_permission_error",
                    "error": str(exc),
                }
            time.sleep(0.25 * attempt)
    return {"status": "BLOCK", "path": str(target), "exact_blocker": "windows_idempotent_ingest_permission_error"}


def ingest_official_outputs(
    zip_path: str | Path,
    repo_root: str | Path,
    *,
    prefixes: tuple[str, ...],
) -> dict[str, Any]:
    root = Path(repo_root)
    writes: list[dict[str, Any]] = []
    skipped_archives: list[str] = []
    with zipfile.ZipFile(zip_path) as archive:
        for name in archive.namelist():
            if name.endswith("/"):
                continue
            if not any(name.startswith(f"{prefix}/") for prefix in prefixes):
                continue
            if name.endswith(ARCHIVE_SUFFIXES):
                skipped_archives.append(name)
                continue
            if not is_safe_zip_member(name):
                writes.append({"status": "BLOCK", "path": name, "exact_blocker": "unsafe_zip_member"})
                continue
            target = root / "outputs" / Path(*PurePosixPath(name).parts)
            writes.append(idempotent_write_bytes(target, archive.read(name)))
    blockers = [item for item in writes if item.get("status") == "BLOCK"]
    return {
        "status": "PASS" if not blockers else "BLOCK",
        "prefixes": list(prefixes),
        "write_records": writes,
        "written_count": sum(item.get("status") == "WRITTEN_ATOMIC_REPLACE" for item in writes),
        "skipped_identical_count": sum(item.get("status") == "SKIPPED_IDENTICAL" for item in writes),
        "skipped_archives": skipped_archives,
        "exact_blocker": blockers[0].get("exact_blocker") if blockers else None,
    }
