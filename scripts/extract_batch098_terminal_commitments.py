from __future__ import annotations

import argparse
import json
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--truth-blind-artifact", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--commitment-timestamp", default="2026-07-19T03:59:17Z")
    args = parser.parse_args()
    root = Path(args.truth_blind_artifact)
    rows = []
    for path in sorted(root.glob("evidence/batch098-truth-candidate-*/public_truth_blind_terminal_v1.json")):
        value = json.loads(path.read_text(encoding="utf-8"))
        rows.append({
            "candidate_id": value["candidate_id"],
            "terminal_commitment_hash": value["terminal_seal"],
            "terminal_commitment_timestamp": args.commitment_timestamp,
            "terminal_value_fields_included": [],
            "authority_allowed": "timing proof only",
            "authority_forbidden": ["terminal class", "arm result", "probe observation", "score"],
        })
    if len(rows) != 8:
        raise SystemExit("terminal commitment registry requires eight candidates")
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("".join(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n" for row in rows), encoding="utf-8", newline="\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
