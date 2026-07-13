from __future__ import annotations

from pathlib import Path
from typing import Any

from .target_collision_detector import find_symbol_locations
from .target_provenance import target_provenance


def verify_native_target(source_root: Path, target_path: str, node: str, *, evidence_path: str | None = None) -> dict[str, Any]:
    provenance = target_provenance(source_root, target_path, node)
    symbol = node.split("::")[-1]
    locations = find_symbol_locations(source_root, symbol)
    collision = len(locations) > 1 or (evidence_path is not None and evidence_path != target_path)
    return {
        **provenance,
        "status": "BLOCK" if collision or provenance["status"] != "PASS" else "PASS",
        "symbol_locations": locations,
        "target_mapping": "SYMBOL_NAME_COLLISION" if collision else "EXACT_NODE_PROVENANCE",
        "correct_lane": "ISSUE_DERIVED_REPRODUCER_LANE" if collision else "NATIVE_TARGET_LANE",
    }
