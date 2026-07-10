from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from controllergate.engine import FrontierEngine

def main() -> int:
    parser = argparse.ArgumentParser(description="ControllerGate static frontier planning interface")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("status")
    sub.add_parser("validate")
    plan = sub.add_parser("plan")
    plan.add_argument("--candidate", required=True)
    execute = sub.add_parser("execute")
    execute.add_argument("--candidate", required=True)
    args = parser.parse_args()
    engine = FrontierEngine(ROOT)
    if args.command == "status":
        result = engine.status()
    elif args.command == "validate":
        result = engine.validate()
    elif args.command == "plan":
        result = engine.plan(args.candidate)
    else:
        result = {
            "status": "BLOCK",
            "candidate_id": args.candidate,
            "blocker": "frontier_execution_not_authorized_static_planning_only",
        }
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result.get("status") in {"PASS", None} else (2 if args.command == "execute" else 1)


if __name__ == "__main__":
    raise SystemExit(main())
