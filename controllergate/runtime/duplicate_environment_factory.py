from __future__ import annotations

from pathlib import Path
from typing import Any


def duplicate_environment_specs(
    source: Path,
    wheelhouse: Path,
    target: str,
    provider_lock_hash: str,
    strategy: dict[str, Any],
) -> list[dict[str, Any]]:
    pythonpath = "/source" if strategy.get("strategy") == "source_on_pythonpath" else None
    base = {
        "source_mount": str(source),
        "source_mount_mode": "read_only",
        "provider_store": str(wheelhouse),
        "provider_store_mode": "read_only",
        "provider_lock_hash": provider_lock_hash,
        "target": target,
        "network": "none",
        "PYTHONPATH": pythonpath,
        "install_mode": "--no-index --find-links /wheelhouse",
    }
    return [{**base, "environment": "env1"}, {**base, "environment": "env2"}]
