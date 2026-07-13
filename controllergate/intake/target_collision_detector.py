from __future__ import annotations

import ast
from pathlib import Path


def find_symbol_locations(source_root: Path, symbol: str) -> list[str]:
    locations: list[str] = []
    for path in source_root.rglob("*.py"):
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"))
        except (OSError, SyntaxError, UnicodeDecodeError):
            continue
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)) and node.name == symbol:
                locations.append(f"{path.relative_to(source_root).as_posix()}:{node.lineno}")
    return sorted(locations)
