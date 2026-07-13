from __future__ import annotations

import sys
import sysconfig

from controllergate.core.evidence import hash_record


def resolve_python_abi(version: str | None = None) -> dict:
    observed = f"{sys.version_info.major}.{sys.version_info.minor}"
    record = {
        "status": "PASS" if version in {None, observed, sys.version.split()[0]} else "BLOCK",
        "requested_version": version,
        "observed_version": sys.version.split()[0],
        "implementation_cache_tag": sys.implementation.cache_tag,
        "soabi": sysconfig.get_config_var("SOABI"),
        "platform_tag": sysconfig.get_platform(),
    }
    record["abi_identity_hash"] = hash_record(record)
    return record
