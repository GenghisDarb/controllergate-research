from __future__ import annotations

import argparse
import json
from pathlib import Path


def rows(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    planning = rows(args.output / "amds_probe_planning_registry.jsonl")
    terminals = rows(args.output / "amds_terminal_registry.jsonl")
    observations = rows(args.output / "amds_semantic_observation_registry.jsonl")
    adversarial = json.loads((args.output / "amds_contradiction_backtrack_audit.json").read_text(encoding="utf-8"))
    selected = [row for row in planning if row["status"] == "SELECTED"]
    minimax = [row for row in selected if row["selection_method"] == "deterministic_minimax_partition"]
    valid = (
        len(terminals) == 8
        and bool(selected)
        and len(minimax) == len(selected)
        and observations
        and all(row["status"] == "DIRECT_VERIFIED" for row in observations)
        and all(not row["patch_authority"] for row in terminals)
        and adversarial["status"] == "PASS"
        and adversarial["contradictions"] >= 2
        and adversarial["backtracks"] >= 2
    )
    result = {
        "active_episode_count": len(terminals),
        "active_selection_executed": bool(selected),
        "information_gain_records": sum(row["selection_method"] == "expected_information_gain" for row in selected),
        "minimax_records": len(minimax),
        "no_forced_guess": all(row["terminal"] != "source_owned_behavior_defect" for row in terminals),
        "safe_abstention_count": sum(row["safe_abstention"] for row in terminals),
        "semantic_verification_count": len(observations),
        "status": "PASS" if valid else "FAIL",
    }
    (args.output / "amds_active_inference_audit.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(result, sort_keys=True))
    return 0 if valid else 1


if __name__ == "__main__":
    raise SystemExit(main())
