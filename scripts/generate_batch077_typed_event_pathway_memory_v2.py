from __future__ import annotations

import argparse
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from controllergate.core.batch077_typed_event_pathway_memory_v2 import generate


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--artifact", type=Path)
    args = parser.parse_args()
    result = generate(ROOT, args.artifact)
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    import json
    raise SystemExit(main())
