from __future__ import annotations

import argparse
from pathlib import Path

from controllergate.core.batch079_count6_runtime_incident_memory_wave1c import generate


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--artifact", type=Path)
    parser.add_argument("--execute-external", action="store_true")
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    result = generate(root, artifact=args.artifact, execute_external=args.execute_external)
    print("Batch079:", result["status"])
    return 0 if result["status"].startswith("PASS") else 1


if __name__ == "__main__":
    raise SystemExit(main())
