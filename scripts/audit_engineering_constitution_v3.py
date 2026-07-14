from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from controllergate.governance.law_runtime_adjudicator import adjudicate


def main() -> int:
    parser = argparse.ArgumentParser(); parser.add_argument("--proof-dir"); args = parser.parse_args()
    constitution = json.loads((ROOT / "configs/controllergate_engineering_constitution_v3.json").read_text(encoding="utf-8"))
    if not args.proof_dir:
        unique = len({law["requirement_id"] for law in constitution["laws"]}) == constitution["law_count"]
        result = {"status":"PASS" if unique and constitution.get("raw_evidence_required") else "FAIL", "mode":"schema", "law_count":constitution["law_count"]}
    else:
        proof_dir = Path(args.proof_dir); proofs = {p.stem:json.loads(p.read_text(encoding="utf-8")) for p in proof_dir.glob("CG-LAW-*.json")}
        result = adjudicate(constitution, proofs, proof_dir.parent)
    print(json.dumps(result, sort_keys=True)); return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__": raise SystemExit(main())
