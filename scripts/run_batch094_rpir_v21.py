from __future__ import annotations

import argparse
import json
from pathlib import Path

from controllergate.reactome_ir.nested import build_rpir_v2_1


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--database", required=True)
    parser.add_argument("--v2-output", required=True)
    parser.add_argument("--source-manifest", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    result = build_rpir_v2_1(database=args.database, v2_output=args.v2_output, source_manifest=args.source_manifest, output=args.output)
    print(json.dumps(result, sort_keys=True))
    return 0 if str(result["status"]).startswith("PASS") else 1


if __name__ == "__main__":
    raise SystemExit(main())
