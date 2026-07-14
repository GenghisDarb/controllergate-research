from __future__ import annotations

import re
from pathlib import Path


REF = re.compile(r"(?:\$ref\s*:\s*|[\"']\$ref[\"']\s*:\s*)[\"']?([^\"'\s}]+)")


def parse_references(path: Path) -> list[str]:
    return REF.findall(path.read_text(encoding="utf-8", errors="strict"))
