from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from controllergate.core.evidence import write_json_deterministic
from controllergate.experiments.replication_batch import run_replication_batch
from controllergate.protocols.clean_replication import validate_clean_replication_config


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the maintained clean replication protocol.")
    parser.add_argument("--config", default="configs/clean_replication_batch_001.json")
    parser.add_argument("--output", default="outputs/clean_replication_batch_001/consolidated_state_clean_replication_batch_001.json")
    args = parser.parse_args()

    config = json.loads(Path(args.config).read_text(encoding="utf-8"))
    config_status = validate_clean_replication_config(config)
    if config_status["status"] != "PASS":
        write_json_deterministic(args.output, {"status": "FAILED", "exact_blocker": "clean_protocol_adapter_failed", "config_status": config_status})
        return 1

    result = run_replication_batch(config)
    result["batch_id"] = config.get("batch_id")
    result["candidate_source_mode"] = config.get("candidate_source_mode", "mixed")
    result["full_scoring"] = "NOT_RUN/disallowed"
    result["memory_lift"] = "undemonstrated"
    result["self_maintaining_software"] = "false/not_demonstrated"
    write_json_deterministic(args.output, result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
