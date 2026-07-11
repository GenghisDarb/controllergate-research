from __future__ import annotations

from controllergate.core.evidence import hash_record


def update_volume(volume: dict[str, object], probe: dict[str, object], result: dict[str, object]) -> dict[str, object]:
    updated = dict(volume); history = list(updated.get("measurement_history") or []); history.append({"probe_id": probe["probe_id"], "result_hash": hash_record(result), "result": result}); updated["measurement_history"] = history; updated["volume_hash"] = hash_record(updated); return updated
