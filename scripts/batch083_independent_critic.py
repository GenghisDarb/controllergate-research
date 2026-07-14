from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from controllergate.evaluation.batch083_independent_critic import recompute


def main() -> int:
    p=argparse.ArgumentParser();p.add_argument("--evidence",required=True);p.add_argument("--output",required=True);args=p.parse_args()
    result=recompute(Path(args.evidence),ROOT/"controllergate/batch083/orchestrator.py",ROOT/"controllergate/evaluation/batch083_independent_critic.py")
    Path(args.output).write_text(json.dumps(result,indent=2,sort_keys=True)+"\n",encoding="utf-8",newline="\n")
    print(json.dumps({"status":result["status"],"errors":result["errors"]},sort_keys=True));return 0 if result["status"]=="PASS" else 1


if __name__=="__main__":raise SystemExit(main())
