from __future__ import annotations

from pathlib import Path
from typing import Any

from .dynamic_metadata_capsule import dynamic_metadata_capability


def plan_metadata_hook(artifact: Path, build_backend: str | None) -> dict[str, Any]:
    capability = dynamic_metadata_capability()
    return {"status": "PASS" if capability["status"] == "PASS" and build_backend else "BLOCK", "artifact": str(artifact), "build_backend": build_backend, "hook": "prepare_metadata_for_build_wheel", "tests_executed": 0, "network_mode": "none", "capability": capability, "blocker": None if capability["status"] == "PASS" and build_backend else "dynamic_metadata_build_backend_unresolved"}
