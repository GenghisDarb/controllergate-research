from __future__ import annotations

from pathlib import Path

from controllergate.core.evidence import hash_record, sha256_file


def resolve_build_toolchain(source_root: Path) -> dict:
    records = []
    for name in ("pyproject.toml", "setup.py", "setup.cfg"):
        path = source_root / name
        if path.is_file():
            records.append({"path": name, "sha256": sha256_file(path)})
    record = {"status": "PASS" if records else "BLOCK", "build_roots": records, "tool_versions": {}, "source_metadata_only": True}
    record["toolchain_hash"] = hash_record(record)
    return record
