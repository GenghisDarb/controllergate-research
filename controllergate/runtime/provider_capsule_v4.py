from __future__ import annotations

import hashlib
from pathlib import Path

from controllergate.reactions.stable_identity import stable_hash


def seal_provider(wheel_dir: Path, dependency_graph: dict[str, object], plan_hash: str) -> dict[str, object]:
    wheels = [{"path": p.name, "sha256": hashlib.sha256(p.read_bytes()).hexdigest(), "bytes": p.stat().st_size}
              for p in sorted(wheel_dir.glob("*.whl"))]
    value = {"state": "PROVIDER_ARTIFACT_SET_SEALED", "plan_hash": plan_hash,
             "dependency_graph_hash": dependency_graph.get("graph_hash"), "wheels": wheels}
    value["provider_seal"] = stable_hash(value)
    return value
