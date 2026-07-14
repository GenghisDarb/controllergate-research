from __future__ import annotations

import ast
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def audit() -> dict[str, object]:
    legacy = [json.loads(line)["old_module"] for line in (ROOT / "configs/controllergate_legacy_component_registry.jsonl").read_text(encoding="utf-8").splitlines() if line]
    canonical = json.loads((ROOT / "configs/controllergate_canonical_component_registry.json").read_text(encoding="utf-8"))["components"]
    errors = []
    for module in set(canonical.values()):
        if module.startswith("scripts."):
            continue
        path = ROOT / (module.replace(".", "/") + ".py")
        if not path.is_file():
            errors.append(f"canonical_module_missing:{module}")
            continue
        tree = ast.parse(path.read_text(encoding="utf-8"))
        imports = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import): imports.extend(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module: imports.append(node.module)
        for item in imports:
            if any(item == old or item.startswith(old + ".") for old in legacy):
                errors.append(f"legacy_import:{module}:{item}")
    return {"status": "PASS" if not errors else "FAIL", "errors": errors, "canonical_modules_checked": len(set(canonical.values()))}


if __name__ == "__main__":
    result = audit(); print(json.dumps(result, sort_keys=True)); raise SystemExit(result["status"] != "PASS")
