#!/usr/bin/env python3
"""Direct internal-route accounting control for py-bugger issue 65."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--target", type=Path, required=True)
    parser.add_argument("--mask", required=True)
    args = parser.parse_args()
    os.environ["CONTROLLERGATE_MUTATION_MASK"] = args.mask
    from py_bugger.cli.config import pb_config
    from py_bugger.py_bugger import main as run_internal
    from py_bugger.utils.modification import modifications

    modifications.clear()
    pb_config.target_file = args.target
    pb_config.target_dir = ""
    pb_config.num_bugs = 10
    pb_config.exception_type = ""
    pb_config.verbose = False
    before = sha(args.target)
    requested = run_internal()
    after = sha(args.target)
    result = {
        "route": "direct_internal", "requested_mutation_count": len(requested),
        "successful_mutation_count": len(modifications),
        "persisted_source_diff_mutation_count": int(before != after),
        "target_pre_sha256": before, "target_post_sha256": after,
        "mask_sha256": hashlib.sha256(args.mask.encode()).hexdigest(),
    }
    print(json.dumps(result, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
