from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import os
from pathlib import Path
import stat
from typing import Any

from controllergate.core.evidence import hash_record


def snapshot_tree(root: str | Path) -> dict[str, Any]:
    base = Path(root)
    files: list[dict[str, Any]] = []
    for path in sorted(base.rglob("*"), key=lambda item: item.relative_to(base).as_posix()):
        rel = path.relative_to(base).as_posix()
        info = path.lstat()
        record: dict[str, Any] = {"path": rel, "mode": stat.S_IMODE(info.st_mode), "size": info.st_size}
        if path.is_symlink():
            record.update({"file_type": "symlink", "symlink_target": os.readlink(path), "sha256": None})
        elif path.is_file():
            record.update({"file_type": "regular", "symlink_target": None, "sha256": hashlib.sha256(path.read_bytes()).hexdigest()})
        elif path.is_dir():
            record.update({"file_type": "directory", "symlink_target": None, "sha256": None})
        else:
            record.update({"file_type": "other", "symlink_target": None, "sha256": None})
        files.append(record)
    semantic = {"root_label": base.name, "files": files}
    return {"operation_status": "COMPLETED", "evidence_status": "ESTABLISHED", "timestamp": datetime.now(timezone.utc).isoformat(), "root": str(base), "tree_content_hash": hash_record(semantic), "files": files}


def diff_snapshots(before: dict[str, Any], after: dict[str, Any]) -> dict[str, Any]:
    old = {item["path"]: item for item in before.get("files", [])}
    new = {item["path"]: item for item in after.get("files", [])}
    added = sorted(set(new) - set(old)); removed = sorted(set(old) - set(new))
    changed = sorted(path for path in set(old) & set(new) if old[path] != new[path])
    return {"status": "PASS" if not added and not removed and not changed else "FAIL", "added": added, "removed": removed, "changed": changed, "mutation_count": len(added) + len(removed) + len(changed)}
