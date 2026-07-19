#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from controllergate.evidence.provider_capsule_v2 import verify_provider_capsule
from controllergate.evidence.source_capsule_v1 import verify_source_capsule


def rows(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-root", type=Path, required=True)
    args = parser.parse_args()
    source = rows(args.output_root / "source_capsule_registry_v1.jsonl")
    provider = rows(args.output_root / "provider_capsule_registry_v2.jsonl")
    source_errors = {row["candidate_id"]: verify_source_capsule(row) for row in source if verify_source_capsule(row)}
    provider_errors = {row["candidate_id"]: verify_provider_capsule(row) for row in provider if verify_provider_capsule(row)}
    if len(source) != 8 or len({row["candidate_id"] for row in provider}) != 8 or len(provider) < 8 or source_errors or provider_errors:
        raise SystemExit(f"capsule verification failed: source={len(source)} provider={len(provider)} errors={source_errors}|{provider_errors}")
    print("BATCH100_CAPSULE_VERIFICATION_PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
