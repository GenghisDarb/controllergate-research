from __future__ import annotations

import ast
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BOUNDARIES = {
    "controllergate/execution/execution_broker.py",
    "controllergate/runtime/provider_service.py",
}
CHECK = (
    "controllergate/state", "controllergate/intake/canonical.py", "controllergate/intake/structured_collection.py",
    "controllergate/intake/failure_contract_v2.py", "controllergate/amds/canonical_v3.py",
    "controllergate/amds/memory_isolation.py", "controllergate/proof", "controllergate/repair",
)


def audit() -> dict[str, object]:
    errors = []
    paths = []
    for item in CHECK:
        path = ROOT / item
        paths.extend(path.rglob("*.py") if path.is_dir() else [path])
    for path in paths:
        rel = path.relative_to(ROOT).as_posix()
        if rel in BOUNDARIES or not path.is_file(): continue
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                text = ast.unparse(node)
                if any(name in text for name in ("subprocess", "requests", "urllib")):
                    errors.append(f"external_import:{rel}:{text}")
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr in {"run", "Popen", "system"}:
                errors.append(f"direct_external_call:{rel}:{node.func.attr}")
    return {"status": "PASS" if not errors else "FAIL", "errors": errors, "files_checked": len(paths)}


if __name__ == "__main__":
    result=audit(); print(json.dumps(result, sort_keys=True)); raise SystemExit(result["status"] != "PASS")
