from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from controllergate.topology.pre_tld_frame_v1 import verify_pre_tld_frame


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    source = Path(args.source)
    output = Path(args.output)
    output.mkdir(parents=True, exist_ok=True)
    frames = [json.loads(path.read_text(encoding="utf-8")) for path in sorted(source.rglob("pre_tld_decision_frame_v1.json"))]
    receipts = [verify_pre_tld_frame(frame) for frame in frames]
    candidate_ids = [str(row.get("candidate_id")) for row in frames]
    status = "PASS" if len(frames) == 8 and len(set(candidate_ids)) == 8 and all(row["status"] == "PASS" for row in receipts) else "BLOCK"
    (output / "pre_tld_decision_frames_v1.jsonl").write_text(
        "".join(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n" for row in frames),
        encoding="utf-8", newline="\n",
    )
    (output / "pre_tld_frame_verification_receipts_v1.jsonl").write_text(
        "".join(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n" for row in receipts),
        encoding="utf-8", newline="\n",
    )
    audit = {
        "status": status,
        "frame_count": len(frames),
        "unique_candidate_count": len(set(candidate_ids)),
        "private_tld_source_access_count": sum(int(row.get("private_tld_source_access_count", -1)) for row in frames),
        "truth_access_count": sum(int(row.get("truth_access_count", -1)) for row in frames),
        "final_frame_count": sum("final_complete_frame_hash" in row for row in frames),
        "authority_allowed": "private TLD continuation input",
        "authority_forbidden": ["final frame freeze", "terminal", "source ownership", "repair", "count", "release"],
        "producer": "scripts/verify_batch098_pre_tld_frames.py",
        "execution_depth": "independent_cohort_verification",
        "semantic_scope": "public pre-TLD frames",
    }
    (output / "pre_tld_frame_authority_audit.json").write_text(
        json.dumps(audit, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n"
    )
    print(json.dumps(audit, sort_keys=True))
    return 0 if status == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
