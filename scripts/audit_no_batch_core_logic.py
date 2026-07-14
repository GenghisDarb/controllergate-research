from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def audit() -> dict[str, object]:
    forbidden = []
    for path in ROOT.glob("controllergate/batch085/**/*.py"):
        if path.name != "__init__.py":
            forbidden.append(path.relative_to(ROOT).as_posix())
    return {"status": "PASS" if not forbidden else "FAIL", "batch085_core_files": forbidden, "policy": "batch code may report but may not implement product operations"}


if __name__ == "__main__":
    result = audit(); print(json.dumps(result, sort_keys=True)); raise SystemExit(result["status"] != "PASS")
