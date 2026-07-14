from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from controllergate.governance.cumulative_maturity import validate_model


def main() -> int:
    path = ROOT / "configs/controllergate_capability_maturity_model_v2.json"
    result = validate_model(json.loads(path.read_text(encoding="utf-8")))
    print(json.dumps(result, sort_keys=True))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
