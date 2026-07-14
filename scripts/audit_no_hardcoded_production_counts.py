from __future__ import annotations

import ast
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def audit() -> dict[str, object]:
    registry = json.loads((ROOT / "configs/controllergate_canonical_component_registry.json").read_text(encoding="utf-8"))["components"]
    errors = []
    checked = 0
    for module in sorted(set(registry.values())):
        if module.startswith("scripts."): continue
        path = ROOT / (module.replace(".", "/") + ".py")
        if not path.is_file(): continue
        checked += 1
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Dict):
                for key, value in zip(node.keys, node.values):
                    if isinstance(key, ast.Constant) and key.value in {"issue_derived_repair_count", "native_external_repair_count"} and isinstance(value, ast.Constant) and isinstance(value.value, int):
                        errors.append(f"hardcoded_count:{module}:{key.value}")
    return {"status": "PASS" if not errors else "FAIL", "errors": errors, "canonical_modules_checked": checked}


if __name__ == "__main__":
    result = audit(); print(json.dumps(result, sort_keys=True)); raise SystemExit(result["status"] != "PASS")
