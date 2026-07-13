from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def load_registry(path: str | Path) -> dict[str, Any]:
    value = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("registry root must be an object")
    return value
