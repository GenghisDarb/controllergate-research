from __future__ import annotations

from controllergate.reactions.stable_identity import stable_hash


def pair_pathways(normal: dict[str, object], incident: dict[str, object]) -> dict[str, object]:
    for key in ("provider", "platform_runtime", "command"):
        if normal.get(key) != incident.get(key):
            raise ValueError(f"normal_incident_pair_mismatch:{key}")
    value = {
        "normal_pathway": normal,
        "incident_pathway": incident,
        "shared_inputs": normal.get("inputs", []),
        "shared_provider": normal.get("provider"),
        "shared_platform_runtime": normal.get("platform_runtime"),
        "shared_command_reproducer": normal.get("command"),
    }
    return {**value, "pair_hash": stable_hash(value)}
