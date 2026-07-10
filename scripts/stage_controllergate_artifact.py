from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from controllergate.core.artifact_hygiene import audit_artifact_payload, stage_artifact_payload, write_artifact_manifest


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--destination", required=True)
    parser.add_argument("--source", action="append", default=[])
    args = parser.parse_args()
    sources = [ROOT / source for source in args.source]
    result = stage_artifact_payload(args.destination, sources)
    manifest = write_artifact_manifest(args.destination)
    audit = audit_artifact_payload(args.destination)
    print(f"staged={len(result['copied_files'])} excluded={len(result['excluded_files'])} manifest={manifest['covered_file_count']} status={audit['status']}")
    return 0 if audit["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
