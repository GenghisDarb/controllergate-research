from __future__ import annotations

import ast
from pathlib import Path


def contact_domain(paths: list[Path], symbols: set[str]) -> dict[str, object]:
    contacts = []
    for path in paths:
        try: tree = ast.parse(path.read_text(encoding="utf-8"))
        except (SyntaxError, UnicodeDecodeError): continue
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)) and (not symbols or node.name in symbols):
                contacts.append({"path": str(path), "symbol": node.name, "line": node.lineno, "end_line": getattr(node, "end_lineno", node.lineno)})
    return {"status": "PASS" if contacts else "BLOCK", "contacts": contacts, "source_file_count": len({r['path'] for r in contacts})}
