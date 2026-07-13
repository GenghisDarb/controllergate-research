from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from controllergate.core.evidence import sha256_file, write_json_deterministic, write_text_lf


def append_jsonl(path: Path, record: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(record, sort_keys=True, separators=(",", ":")) + "\n")


def tree_hash(root: Path, *, excluded_parts: set[str] | None = None) -> str:
    excluded_parts = excluded_parts or {".git", "__pycache__", ".pytest_cache"}
    digest = hashlib.sha256()
    if not root.exists():
        return digest.hexdigest()
    for path in sorted(item for item in root.rglob("*") if item.is_file() and not excluded_parts.intersection(item.parts)):
        rel = path.relative_to(root).as_posix()
        digest.update(rel.encode())
        digest.update(b"\0")
        digest.update(bytes.fromhex(sha256_file(path)))
        digest.update(b"\n")
    return digest.hexdigest()


def write_sha256sums(root: Path) -> None:
    rows = []
    for path in sorted(item for item in root.rglob("*") if item.is_file() and item.name != "SHA256SUMS.txt"):
        rows.append(f"{sha256_file(path)}  {path.relative_to(root).as_posix()}")
    write_text_lf(root / "SHA256SUMS.txt", "\n".join(rows) + "\n")


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def record_block(path: Path, *, candidate_id: str, blocker: str, stage: str, reopen: str) -> dict[str, Any]:
    record = {"status": "BLOCKED_EXACT", "candidate_id": candidate_id, "stage": stage,
              "exact_blocker": blocker, "reopen_condition": reopen, "repair_license": False}
    write_json_deterministic(path, record)
    return record
