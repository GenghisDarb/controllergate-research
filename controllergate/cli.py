from __future__ import annotations

import argparse
import json
from pathlib import Path

from .current_pathway import current_pathway


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="controllergate")
    sub = parser.add_subparsers(dest="command", required=True)
    run = sub.add_parser("run")
    run.add_argument("--manifest", required=True)
    args = parser.parse_args(argv)
    manifest = Path(args.manifest)
    if not manifest.is_file():
        print(json.dumps({"status": "BLOCK", "exact_blocker": "manifest_missing"}, sort_keys=True))
        return 1
    payload = json.loads(manifest.read_text(encoding="utf-8"))
    print(json.dumps({"status": "ADMITTED_FOR_CANONICAL_DISPATCH", "manifest": str(manifest), "candidate_id": payload.get("candidate_id"), **current_pathway()}, sort_keys=True))
    return 0
