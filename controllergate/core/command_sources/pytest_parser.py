from __future__ import annotations

import configparser
from pathlib import Path
from typing import Any


def parse_pytest_ini(path: Path) -> dict[str, Any]:
    parser = configparser.ConfigParser(interpolation=None); parser.read(path, encoding="utf-8")
    section = parser["pytest"] if parser.has_section("pytest") else {}
    return {"status": "PASS", "source_path": path.as_posix(), "addopts": str(section.get("addopts", "")).split(), "testpaths": str(section.get("testpaths", "")).split()}
