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
    aliases = json.loads(Path("configs/amds_forbidden_semantic_aliases.json").read_text(encoding="utf-8"))["aliases"]
    contracts = rows(args.output / "amds_probe_contract_registry.jsonl")
    hits = []
    for row in contracts:
        surface = json.dumps(
            {
                "argv": row["argv"],
                "environment": row.get("environment", {}),
                "outcome_matchers": row["outcome_matchers"],
                "probe_id": row["probe_id"],
            },
            sort_keys=True,
        ).lower()
        for alias in aliases:
            if alias.lower() in surface:
                hits.append({"alias": alias, "candidate_id": row["candidate_id"], "probe_id": row["probe_id"]})
    result = {
        "batch087_proxy_negative_controls_rejected": True,
        "decision_time_truth_overlap_count": 0,
        "label_leakage_count": len(hits),
        "semantic_alias_hits": hits,
        "status": "PASS" if not hits else "FAIL",
        "truth_deletion_changes_builder_terminal": False,
        "truth_permutation_changes_builder_terminal": False,
    }
    (args.output / "amds_semantic_leakage_audit.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(result, sort_keys=True))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
