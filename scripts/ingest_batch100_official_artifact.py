from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from controllergate.evidence.batch100_official_ingest import ingest


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--artifact", required=True)
    parser.add_argument("--quarantine", required=True)
    parser.add_argument("--output-root", required=True)
    parser.add_argument("--acquisition-route", required=True)
    args = parser.parse_args()
    result = ingest(Path(args.artifact), Path(args.quarantine), Path(args.output_root), args.acquisition_route)
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
