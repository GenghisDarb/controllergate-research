from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from controllergate.governance.engineering_constitution import validate_law


def main() -> int:
    root = Path.cwd()
    path = root / "configs/controllergate_engineering_constitution_v1.json"
    if not path.is_file():
        print("engineering constitution: FAIL missing")
        return 1
    value = json.loads(path.read_text(encoding="utf-8"))
    failures = {law["requirement_id"]: errors for law in value.get("laws", []) if (errors := validate_law(law, root))}
    complete = value.get("law_count") == 40 and len(value.get("laws", [])) == 40 and not failures
    print("engineering constitution:", "PASS" if complete else "FAIL", f"laws={len(value.get('laws', []))}", failures)
    return 0 if complete else 1


if __name__ == "__main__":
    raise SystemExit(main())
