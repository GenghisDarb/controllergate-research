from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from controllergate.core.frontier_state import verify_state_hash
FILES = (
    "outputs/current/CURRENT_PROTOCOL_STATE.json", "outputs/frontier/CURRENT_FRONTIER_STATE.json",
    "outputs/current/REPAIR_COUNT_STATE.json", "outputs/current/CAPABILITY_MATURITY_STATE.json",
)


def audit() -> dict[str, object]:
    errors = []
    values = {}
    for rel in FILES:
        path = ROOT / rel
        if not path.is_file(): errors.append(f"missing:{rel}"); continue
        values[rel] = json.loads(path.read_text(encoding="utf-8"))
        if not verify_state_hash(values[rel]): errors.append(f"state_hash:{rel}")
    protocol = values.get(FILES[0], {})
    repair = values.get(FILES[2], {})
    for field in ("issue_derived_repair_count", "native_external_repair_count"):
        if protocol.get(field) != repair.get(field): errors.append(f"count_drift:{field}")
    if protocol.get("protocol_version") != "v2.19": errors.append("protocol_drift")
    if "SQLite ControllerState" not in str(protocol.get("state_authority")): errors.append("noncanonical_state_authority")
    return {"status": "PASS" if not errors else "FAIL", "errors": errors, "view_count": len(values)}


if __name__ == "__main__":
    result = audit(); print(json.dumps(result, sort_keys=True)); raise SystemExit(result["status"] != "PASS")
