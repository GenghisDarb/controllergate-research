from __future__ import annotations

import argparse
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from controllergate.core.batch078_count6_minimal_closure_memory_wave1b import generate


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate Batch078 evidence")
    parser.add_argument("--artifact", type=Path)
    parser.add_argument("--execute-external", action="store_true")
    args = parser.parse_args()
    result = generate(ROOT, artifact=args.artifact, execute_external=args.execute_external)
    print(
        "Batch078 generation:",
        result["status"],
        "mode=", result["execution_mode"],
        "admitted=", result["wave1b_admitted_count"],
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
