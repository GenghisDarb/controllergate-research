from __future__ import annotations

import sys
from typing import Any


def platform_gate(required: str) -> dict[str, Any]:
    actual = "windows" if sys.platform.startswith("win") else "linux" if sys.platform.startswith("linux") else sys.platform
    return {"status": "PASS" if required.lower() == actual else "PLATFORM_BLOCKED", "required": required.lower(), "actual": actual}
