from __future__ import annotations

import ast
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


FORBIDDEN_IMPORTS = {"subprocess", "requests", "urllib.request", "docker"}
SCOPED_PREFIXES = ("generate_batch081", "audit_batch081", "finalize_batch081")


def violations(root: Path) -> list[str]:
    found: list[str] = []
    for path in (root / "scripts").glob("*.py"):
        if not path.name.startswith(SCOPED_PREFIXES):
            continue
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for item in node.names:
                    if item.name in FORBIDDEN_IMPORTS: found.append(f"{path}:{item.name}")
            elif isinstance(node, ast.ImportFrom) and node.module in FORBIDDEN_IMPORTS:
                found.append(f"{path}:{node.module}")
    return found


def main() -> int:
    found = violations(Path.cwd())
    print("canonical boundary audit:", "PASS" if not found else "FAIL", found)
    return 0 if not found else 1


if __name__ == "__main__":
    raise SystemExit(main())
