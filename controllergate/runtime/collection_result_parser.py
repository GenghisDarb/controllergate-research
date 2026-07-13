from __future__ import annotations

import json
from typing import Any


def parse_collection_result(stdout: str, stderr: str) -> dict[str, Any]:
    nodes: list[str] = []
    structured = False
    for line in stdout.splitlines():
        if not line.startswith("CONTROLLERGATE_COLLECTION_JSON="):
            continue
        structured = True
        try:
            payload = json.loads(line.split("=", 1)[1])
            nodes.extend(item for item in payload.get("nodes", []) if isinstance(item, str))
        except json.JSONDecodeError:
            structured = False
    return {"nodes": nodes, "structured_json_present": structured, "internal_error": "INTERNALERROR" in stdout or "INTERNALERROR" in stderr}
