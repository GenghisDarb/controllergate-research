from __future__ import annotations

import argparse
import ast
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "controllergate"
ENTRY_MODULE = "controllergate.cli"
FORBIDDEN_MODULES = {
    "controllergate.product.cycle", "controllergate.state.state_store", "controllergate.state.run_state",
    "controllergate.runtime.authorized_maintenance", "controllergate.runtime.live_authorized_maintenance",
    "controllergate.intake.admission_executor", "controllergate.runtime.batch068h4_pipeline",
    "controllergate.runtime.batch068h5_pipeline", "controllergate.runtime.batch068h6_pipeline",
    "controllergate.runtime.batch068h7_pipeline", "controllergate.runtime.batch068h8_pipeline",
}
FORBIDDEN_EXTERNAL = {"subprocess", "urllib.request", "requests", "socket", "pip"}
BROKER = "controllergate.execution.execution_broker"


def _module(path: Path) -> str:
    relative = path.relative_to(ROOT).with_suffix("")
    parts = list(relative.parts)
    if parts[-1] == "__init__":
        parts.pop()
    return ".".join(parts)


def _resolve_relative(current: str, node: ast.ImportFrom) -> str:
    if not node.level:
        return node.module or ""
    package = current.split(".")[:-1]
    package = package[: len(package) - max(0, node.level - 1)]
    return ".".join([*package, *([node.module] if node.module else [])])


def scan(root: Path = ROOT, injected_source: str | None = None) -> dict[str, Any]:
    sources = {_module(path): path for path in PACKAGE.rglob("*.py")}
    edges: dict[str, set[str]] = {name: set() for name in sources}
    direct_external: dict[str, list[str]] = {}
    dynamic_bindings: dict[str, list[str]] = {}
    for name, path in sources.items():
        text = injected_source if injected_source is not None and name == "controllergate.engine" else path.read_text(encoding="utf-8")
        tree = ast.parse(text, filename=str(path))
        imports: set[str] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.update(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom):
                imports.add(_resolve_relative(name, node))
            elif isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id in {"__import__", "import_module"}:
                if node.args and isinstance(node.args[0], ast.Constant) and isinstance(node.args[0].value, str):
                    imports.add(node.args[0].value); dynamic_bindings.setdefault(name, []).append(node.args[0].value)
        for imported in imports:
            candidates = [candidate for candidate in sources if candidate == imported or candidate.startswith(imported + ".")]
            if imported in sources:
                edges[name].add(imported)
            elif candidates and imported.startswith("controllergate"):
                edges[name].update(candidate for candidate in candidates if candidate.count(".") == imported.count(".") + 1)
        external = sorted(item for item in imports if any(item == blocked or item.startswith(blocked + ".") for blocked in FORBIDDEN_EXTERNAL))
        if external and name != BROKER:
            direct_external[name] = external
    reachable: set[str] = set(); stack = [ENTRY_MODULE]
    while stack:
        name = stack.pop()
        if name in reachable:
            continue
        reachable.add(name); stack.extend(sorted(edges.get(name, ())))
    forbidden_reachable = sorted(reachable & FORBIDDEN_MODULES)
    unbrokered = {name: value for name, value in direct_external.items() if name in reachable}
    status = "PASS" if not forbidden_reachable and not unbrokered else "FAIL"
    return {
        "status": status, "console_script_target": "controllergate.cli:main", "entry_module": ENTRY_MODULE,
        "reachable_module_count": len(reachable), "reachable_modules": sorted(reachable),
        "forbidden_reachable_modules": forbidden_reachable, "forbidden_reachability_count": len(forbidden_reachable),
        "unbrokered_external_operation_modules": unbrokered, "unbrokered_external_operation_count": len(unbrokered),
        "dynamic_string_bindings": dynamic_bindings, "relative_and_absolute_imports_resolved": True,
        "transitive_reachability_resolved": True, "broker_module": BROKER,
    }


def main() -> int:
    parser = argparse.ArgumentParser(); parser.add_argument("--output", type=Path); parser.add_argument("--negative-control", action="store_true")
    args = parser.parse_args()
    injected = "import subprocess\n" if args.negative_control else None
    result = scan(injected_source=injected)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(result, sort_keys=True))
    if args.negative_control:
        return 0 if result["status"] == "FAIL" else 2
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
