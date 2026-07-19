from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--decision-root", required=True)
    parser.add_argument("--candidate", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    root = Path(args.decision_root)
    output = Path(args.output)
    output.mkdir(parents=True, exist_ok=True)
    frames = []
    for path in root.rglob("pre_tld_decision_frame_v1.json"):
        row = json.loads(path.read_text(encoding="utf-8"))
        if row.get("candidate_id") == args.candidate:
            frames.append((path, row))
    if not frames:
        for path in root.rglob("pre_tld_decision_frames_v1.jsonl"):
            for line in path.read_text(encoding="utf-8").splitlines():
                row = json.loads(line)
                if row.get("candidate_id") == args.candidate:
                    frames.append((path, row))
    if not frames:
        raise SystemExit("candidate pre-TLD frame missing")
    (output / "pre_tld_decision_frame_v1.json").write_text(json.dumps(frames[0][1], indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({"candidate_id": args.candidate, "matching_frame_copies": len(frames), "status": "PASS"}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
