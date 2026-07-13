from __future__ import annotations

from pathlib import Path
from typing import Any

from controllergate.core.evidence import hash_record


def build_native_working_directory_adapter(
    *, source_root: Path, scratch_root: Path, target: str
) -> dict[str, Any]:
    """Bind native relative resources to the candidate root, not runtime scratch."""
    source = source_root.resolve()
    scratch = scratch_root.resolve()
    record = {
        "status": "PASS" if source.is_dir() and source != scratch else "BLOCK",
        "command_working_directory": str(source),
        "subprocess_working_directory": str(source),
        "project_configuration_root": str(source),
        "relative_resource_root": str(source),
        "runtime_scratch": str(scratch),
        "home": str(scratch / "home"),
        "cache": str(scratch / "cache"),
        "target": target,
        "candidate_source_read_only": True,
        "candidate_tests_read_only": True,
    }
    record["adapter_hash"] = hash_record(record)
    return record
