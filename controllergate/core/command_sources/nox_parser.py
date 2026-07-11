from __future__ import annotations

import ast
from pathlib import Path
from typing import Any


def parse_nox(path: Path) -> dict[str, Any]:
    tree = ast.parse(path.read_text(encoding="utf-8")); commands = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Attribute) or node.func.attr != "run": continue
        argv = [item.value for item in node.args if isinstance(item, ast.Constant) and isinstance(item.value, str)]
        if argv: commands.append({"argv": argv, "line": node.lineno})
    return {"status": "PASS", "source_path": path.as_posix(), "commands": commands}
