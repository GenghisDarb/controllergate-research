from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from controllergate.governance.master_completion_ledger import load_and_validate


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--ledger", default="configs/controllergate_master_completion_ledger_v2.json")
    args = parser.parse_args()
    result = load_and_validate(ROOT / args.ledger, ROOT)
    print(json.dumps(result, sort_keys=True))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
