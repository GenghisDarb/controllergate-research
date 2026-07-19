from __future__ import annotations

import argparse
import json
from pathlib import Path

from controllergate.topology.pre_tld_frame_v1 import build_pre_tld_frame, verify_pre_tld_frame


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--candidate-evidence", required=True)
    parser.add_argument("--verified-topology", required=True)
    parser.add_argument("--contracts", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    output = Path(args.output)
    output.mkdir(parents=True, exist_ok=True)
    frame = build_pre_tld_frame(args.candidate_evidence, args.verified_topology, args.contracts)
    verification = verify_pre_tld_frame(frame)
    (output / "pre_tld_decision_frame_v1.json").write_text(
        json.dumps(frame, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n"
    )
    (output / "pre_tld_frame_verification_receipt_v1.json").write_text(
        json.dumps(verification, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n"
    )
    print(json.dumps({"candidate_id": frame["candidate_id"], "status": verification["status"]}, sort_keys=True))
    return 0 if verification["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
