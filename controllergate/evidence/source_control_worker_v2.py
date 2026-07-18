from __future__ import annotations

import argparse
import ast
import hashlib
import json
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--relation", choices=("direct", "unrelated"), required=True)
    parser.add_argument("--target-path", action="append", default=[])
    args = parser.parse_args()
    targets = {value.replace("\\", "/").split("::", 1)[0] for value in args.target_path}
    candidates = []
    for path in sorted(args.root.rglob("*.py")):
        relative = path.relative_to(args.root).as_posix()
        try:
            tree = ast.parse(path.read_text(encoding="utf-8", errors="replace"), filename=relative)
        except SyntaxError:
            continue
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                candidates.append({"path": relative, "symbol": node.name, "line": node.lineno, "source_sha256": hashlib.sha256(path.read_bytes()).hexdigest()})
    if args.relation == "direct":
        selected = next((row for row in candidates if row["path"] in targets), None) or next(iter(candidates), None)
    else:
        selected = next((row for row in candidates if row["path"] not in targets), None)
    result = {"status": "PASS" if selected else "BLOCK", "relation": args.relation, "selected": selected, "target_paths": sorted(targets), "candidate_symbol_count": len(candidates)}
    print(json.dumps(result, sort_keys=True))
    return 0 if selected else 1


if __name__ == "__main__":
    raise SystemExit(main())
