from __future__ import annotations

import argparse
from pathlib import Path

from controllergate.core.batch080_executed_preflight_provider_memory_wave1d import generate_checkpoint


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--artifact", type=Path, required=True)
    parser.add_argument("--checkpoint", action="store_true")
    args = parser.parse_args()
    result = generate_checkpoint(Path(__file__).resolve().parents[1], args.artifact)
    print("Batch080 checkpoint:", result["status"])
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
