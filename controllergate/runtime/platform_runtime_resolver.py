from __future__ import annotations

import platform
import sys
from typing import Any

from controllergate.core.evidence import hash_record


def resolve_platform_runtime(*, requested_os: str | None = None, requested_arch: str | None = None) -> dict[str, Any]:
    observed_os = platform.system().lower()
    observed_arch = platform.machine().lower()
    compatible = (not requested_os or requested_os.lower() == observed_os) and (not requested_arch or requested_arch.lower() == observed_arch)
    record: dict[str, Any] = {
        "status": "PASS" if compatible else "BLOCK",
        "operating_system": observed_os,
        "architecture": observed_arch,
        "python_implementation": platform.python_implementation().lower(),
        "python_version": platform.python_version(),
        "python_abi": getattr(sys, "abiflags", "") or f"cp{sys.version_info.major}{sys.version_info.minor}",
        "requested_os": requested_os,
        "requested_arch": requested_arch,
        "outcome_used_for_selection": False,
    }
    record["identity_hash"] = hash_record(record)
    return record
