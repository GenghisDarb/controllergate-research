from __future__ import annotations

import argparse
import json
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--candidate", choices=("aifc", "imp"), required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    candidate_id = f"{args.candidate}-removal"
    value = {
        "candidate_id": candidate_id,
        "complete": False,
        "decision_time_project_level_identity_resolution_attempted": True,
        "exact_blocker": f"{args.candidate}_complete_project_level_reproducer_capsule_not_available",
        "historical_non_counting": True,
        "repair_count_increment": 0,
        "repair_license": False,
        "replacement_after_outcome": False,
        "safe_abstention": True,
        "status": "BLOCK",
    }
    args.output.mkdir(parents=True, exist_ok=True)
    (args.output / f"{args.candidate}_non_source_lifecycle.json").write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(value, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
