from __future__ import annotations

import zipfile
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from typing import Iterable

from .evidence import sha256_file, verify_zip_artifact, write_json_deterministic


def verify_manual_artifact_boundary(zip_path: str | Path, repo_root: str | Path) -> dict[str, object]:
    path = Path(zip_path).resolve()
    root = Path(repo_root).resolve()
    return {
        "status": "PASS" if root not in path.parents and path != root else "FAIL",
        "local_artifact_path_outside_git": str(path),
        "downloaded_by_codex": False,
    }


def ingest_non_archive_outputs(zip_path: str | Path, repo_root: str | Path, prefix: str) -> int:
    count = 0
    root = Path(repo_root)
    with zipfile.ZipFile(zip_path) as archive:
        for name in archive.namelist():
            if not name.startswith(prefix) or name.lower().endswith((".zip", ".tar", ".tgz", ".tar.gz")):
                continue
            target = root / Path(*PurePosixPath(name).parts)
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(archive.read(name))
            count += 1
    return count


def compare_repo_snapshot_files(zip_path: str | Path, repo_root: str | Path, paths: Iterable[str]) -> list[dict[str, object]]:
    root = Path(repo_root)
    comparisons = []
    with zipfile.ZipFile(zip_path) as archive:
        names = set(archive.namelist())
        for rel in paths:
            repo_path = root / rel
            if rel not in names:
                comparisons.append({"path": rel, "artifact_present": False, "status": "artifact_missing_not_updated"})
                continue
            artifact_data = archive.read(rel)
            repo_sha = sha256_file(repo_path) if repo_path.is_file() else None
            artifact_sha = __import__("hashlib").sha256(artifact_data).hexdigest()
            comparisons.append({
                "path": rel,
                "artifact_present": True,
                "repo_present": repo_path.is_file(),
                "repo_sha256": repo_sha,
                "artifact_sha256": artifact_sha,
                "status": "match" if repo_sha == artifact_sha else "differs",
            })
    return comparisons


def create_official_ingest_record(path: str | Path, zip_path: str | Path, repo_root: str | Path, **extra: object) -> dict[str, object]:
    record = {
        "status": "PASS",
        "artifact": verify_zip_artifact(zip_path),
        "manual_boundary": verify_manual_artifact_boundary(zip_path, repo_root),
        "verification_timestamp_utc": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        **extra,
    }
    write_json_deterministic(path, record)
    return record
