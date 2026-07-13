from __future__ import annotations

import argparse
from pathlib import Path

from controllergate.core.batch080_executed_preflight_provider_memory_wave1d import generate_checkpoint, generate_full


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--artifact", type=Path)
    parser.add_argument("--checkpoint", action="store_true")
    parser.add_argument("--execute-external", action="store_true")
    parser.add_argument("--refresh-pool", action="store_true")
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    if args.checkpoint:
        if args.artifact is None:
            parser.error("--artifact is required with --checkpoint")
        result = generate_checkpoint(root, args.artifact)
        print("Batch080 checkpoint:", result["status"])
        return 0 if result["status"] == "PASS" else 1
    result = generate_full(root, execute_external=args.execute_external, refresh_pool=args.refresh_pool)
    print("Batch080:", result["status"])
    return 0 if result["status"].startswith("PASS") else 1


if __name__ == "__main__":
    raise SystemExit(main())
