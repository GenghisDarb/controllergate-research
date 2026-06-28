from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from controllergate.protocols.clean_replication import validate_clean_replication_config


REQUIRED_CONFIG_FIELDS = {
    "batch_id",
    "candidate_source_mode",
    "max_candidates_to_verify",
    "max_repairs_to_attempt",
    "max_successful_repairs_target",
    "provenance_level",
    "full_scoring",
}


def main() -> int:
    config_path = Path("configs/clean_replication_batch_001.json")
    if not config_path.is_file():
        print("FAIL: missing clean replication config")
        return 1
    config = json.loads(config_path.read_text(encoding="utf-8"))
    missing = sorted(REQUIRED_CONFIG_FIELDS - set(config))
    status = validate_clean_replication_config(config)
    if missing or status["status"] != "PASS":
        print(f"FAIL: clean replication config invalid; missing={missing}; status={status}")
        return 1
    if config.get("full_scoring") is not False:
        print("FAIL: full scoring must remain disabled")
        return 1
    print("clean replication protocol audit PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
