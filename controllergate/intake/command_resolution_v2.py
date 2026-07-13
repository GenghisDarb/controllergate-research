from __future__ import annotations

from pathlib import Path
from typing import Any

from controllergate.core.command_authority_resolver import resolve_command_authority
from controllergate.core.evidence import hash_record


def resolve_command_v2(source_root: Path, target: str) -> dict[str, Any]:
    result = resolve_command_authority(source_root, target)
    metadata = [name for name in ("pyproject.toml", "pytest.ini", "tox.ini", "setup.cfg", "setup.py") if (source_root / name).is_file()]
    passed = result.get("status") == "PASS" and bool(result.get("selected")) and bool(metadata)
    record = {
        **result,
        "status": "PASS" if passed else "BLOCK",
        "project_metadata_inspected": metadata,
        "resolver_executed_against_project_metadata": bool(metadata),
        "command_authority": "project_local_metadata" if passed else "NOT_ESTABLISHED",
    }
    if not passed:
        record["blocker"] = "project_local_command_authority_unresolved"
    record["resolution_hash"] = hash_record(record)
    return record
