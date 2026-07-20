from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from controllergate.evidence.batch102_official_ingest import ingest


parser = argparse.ArgumentParser()
parser.add_argument("--artifact", required=True)
parser.add_argument("--quarantine", required=True)
parser.add_argument("--output-root", required=True)
parser.add_argument("--acquisition-route", required=True)
args = parser.parse_args()
print(
    json.dumps(
        ingest(
            Path(args.artifact),
            Path(args.quarantine),
            Path(args.output_root),
            args.acquisition_route,
        ),
        sort_keys=True,
    )
)
