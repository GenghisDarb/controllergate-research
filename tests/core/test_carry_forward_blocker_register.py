from __future__ import annotations

import json
from pathlib import Path


def test_non_active_traceability_entries_have_carry_forward_blockers() -> None:
    matrix = json.loads(Path("configs/notebooklm_advice_traceability_matrix.json").read_text(encoding="utf-8"))
    register = json.loads(Path("outputs/clean_replication_batch_005/carry_forward_blocker_register.json").read_text(encoding="utf-8"))
    register_by_id = {item["advice_id"]: item for item in register}
    for entry in matrix["entries"]:
        if entry["status"] != "implemented_active":
            item = register_by_id.get(entry["advice_id"])
            assert item is not None, entry["advice_id"]
            assert item["blocker"]
            assert item["next_allowed_lane"]
            assert item["minimum_condition_to_unblock"]
