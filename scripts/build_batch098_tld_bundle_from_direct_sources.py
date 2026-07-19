from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from controllergate.tld_direct_sources import build_bundle


def main() -> int:
    parser = argparse.ArgumentParser(description="Build a deterministic private TLD source-custody bundle.")
    parser.add_argument("--source-root", required=True)
    parser.add_argument("--output-bundle", required=True)
    parser.add_argument("--output-manifest", required=True)
    parser.add_argument("--output-report", required=True)
    args = parser.parse_args()
    try:
        result = build_bundle(
            Path(args.source_root),
            Path(args.output_bundle),
            Path(args.output_manifest),
            Path(args.output_report),
        )
    except (OSError, ValueError) as exc:
        print(json.dumps({"status": "BLOCK", "error": str(exc)}, sort_keys=True))
        return 1
    print(json.dumps(result, sort_keys=True))
    return 0 if result["status"] == "PASS_44_OF_44" else 1


if __name__ == "__main__":
    raise SystemExit(main())
