from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from controllergate.execution.ci_native_result_guard import audit_guard


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("guard")
    args = parser.parse_args()
    result = audit_guard(json.loads(Path(args.guard).read_text(encoding="utf-8")))
    print("CI-native result generation audit: " + result["status"])
    for failure in result["failures"]: print(f"- {failure}")
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())

