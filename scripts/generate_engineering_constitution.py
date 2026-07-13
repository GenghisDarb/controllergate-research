from __future__ import annotations

import subprocess
import sys
import argparse
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from controllergate.governance.engineering_constitution import write_constitution


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--legacy-registry")
    args = parser.parse_args()
    root = Path.cwd()
    head = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
    laws = write_constitution(root, head, legacy_registry_path=Path(args.legacy_registry) if args.legacy_registry else None)
    print(f"engineering constitution generated: {len(laws)} laws")
