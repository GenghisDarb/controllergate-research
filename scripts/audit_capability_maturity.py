from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    parser=argparse.ArgumentParser(); parser.add_argument("--report"); args=parser.parse_args()
    model=json.loads((ROOT/"configs/controllergate_capability_maturity_model_v1.json").read_text(encoding="utf-8"))
    errors=[]; count=0
    if args.report:
        report=json.loads(Path(args.report).read_text(encoding="utf-8")); rows=report.get("dimensions",[]); count=len(rows)
        names={row.get("dimension") for row in rows}; errors += [f"missing:{name}" for name in model["dimensions"] if name not in names]
        for row in rows:
            if row.get("level") not in model["levels"]: errors.append(f"level:{row.get('dimension')}")
            if row.get("level") != "LEVEL_0_ABSENT" and not all(row.get(k) for k in model["promotion_requires"][:4]): errors.append(f"evidence:{row.get('dimension')}")
    else: count=len(model["dimensions"]); errors += [] if count==21 else ["dimension_count"]
    print(json.dumps({"status":"PASS" if not errors else "FAIL","dimension_count":count,"errors":errors},sort_keys=True)); return 0 if not errors else 1


if __name__=="__main__": raise SystemExit(main())
