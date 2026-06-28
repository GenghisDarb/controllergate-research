from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from typing import Iterable

from .evidence import sha256_file, write_json_deterministic

FORBIDDEN_PARTS = {".git", ".venv", "venv", "__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache"}
FORBIDDEN_SUFFIXES = {".pyc", ".zip", ".tar", ".tgz", ".gz", ".7z"}


def reject_unsafe_transport_paths(paths: Iterable[str]) -> list[str]:
    unsafe: list[str] = []
    for rel in paths:
        pure = PurePosixPath(rel)
        parts = set(pure.parts)
        if rel.startswith("/") or "\\" in rel or any(part in {"", ".", ".."} for part in pure.parts):
            unsafe.append(rel)
        elif parts & FORBIDDEN_PARTS:
            unsafe.append(rel)
        elif PurePosixPath(rel).suffix.lower() in FORBIDDEN_SUFFIXES:
            unsafe.append(rel)
    return unsafe


def reject_untracked_cache_payloads(paths: Iterable[str]) -> list[str]:
    return [rel for rel in paths if rel in reject_unsafe_transport_paths([rel])]


def hash_before_transfer(source_path: str | Path) -> str:
    return sha256_file(source_path)


def hash_after_transfer(destination_path: str | Path) -> str:
    return sha256_file(destination_path)


def compare_transfer_hashes(source_sha256: str, destination_sha256: str) -> bool:
    return source_sha256 == destination_sha256


def record_workspace_to_repo_transfer(
    source_path: str | Path,
    destination_path: str | Path,
    *,
    transfer_reason: str,
    allowlist_class: str,
) -> dict[str, object]:
    source = Path(source_path)
    destination = Path(destination_path)
    source_hash = hash_before_transfer(source)
    destination_hash = hash_after_transfer(destination)
    rel_destination = destination.as_posix()
    unsafe = reject_unsafe_transport_paths([rel_destination])
    decision = "PASS" if not unsafe and compare_transfer_hashes(source_hash, destination_hash) else "BLOCK"
    return {
        "source_path": str(source),
        "destination_path": str(destination),
        "source_sha256": source_hash,
        "destination_sha256": destination_hash,
        "transfer_reason": transfer_reason,
        "allowlist_class": allowlist_class,
        "timestamp_utc": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "transport_decision": decision,
        "unsafe_reasons": unsafe,
    }


def write_transport_integrity_log(path: str | Path, records: list[dict[str, object]]) -> None:
    status = "PASS" if all(record.get("transport_decision") == "PASS" for record in records) else "FAIL"
    write_json_deterministic(path, {"status": status, "transfer_records": records})
