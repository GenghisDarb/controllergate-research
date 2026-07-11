from __future__ import annotations

from dataclasses import asdict, replace
from typing import Any

from controllergate.core.evidence import hash_record
from .types import AmdsBoard, AmdsCell, AmdsEdge, AmdsConstraint, BoardUpdate


def _seal_cell(cell: AmdsCell) -> dict[str, Any]:
    value = asdict(cell); value.pop("state_hash", None); value["state_hash"] = hash_record(value); return value


def build_board(candidate_id: str, cells: list[AmdsCell], edges: list[AmdsEdge], constraints: list[AmdsConstraint]) -> dict[str, Any]:
    value = {"board_id": f"amds-{candidate_id}", "candidate_id": candidate_id, "cells": [_seal_cell(c) for c in cells], "edges": [asdict(e) for e in edges], "constraints": [asdict(c) for c in constraints]}
    value["board_hash"] = hash_record(value); return value


def validate_board(board: dict[str, Any]) -> dict[str, Any]:
    unsigned = dict(board); claimed = unsigned.pop("board_hash", None)
    ids = [c.get("cell_id") for c in board.get("cells", [])]
    valid_cells = all(c.get("state_hash") == hash_record({k: v for k, v in c.items() if k != "state_hash"}) for c in board.get("cells", []))
    valid = claimed == hash_record(unsigned) and len(ids) == len(set(ids)) and valid_cells
    return {"status": "PASS" if valid else "BLOCK", "board_hash_valid": claimed == hash_record(unsigned), "cell_hashes_valid": valid_cells}


def update_board(board: dict[str, Any], state_updates: dict[str, str], event_id: str) -> tuple[dict[str, Any], BoardUpdate]:
    before = board["board_hash"]; cells = []
    for value in board["cells"]:
        raw = {k: v for k, v in value.items() if k != "state_hash"}
        if value["cell_id"] in state_updates:
            raw["state"] = state_updates[value["cell_id"]]; raw["last_update_event"] = event_id
        raw["state_hash"] = hash_record(raw); cells.append(raw)
    result = {**board, "cells": cells}; result.pop("board_hash", None); result["board_hash"] = hash_record(result)
    return result, BoardUpdate(event_id, tuple(sorted(state_updates)), before, result["board_hash"])
