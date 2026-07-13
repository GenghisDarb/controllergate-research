from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from controllergate.runtime.runtime_root_attestation import attest_runtime_root
from controllergate.runtime.runtime_root_policy import expected_runtime_root


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--runtime-root", default=str(expected_runtime_root()))
    parser.add_argument("--repo-root", default=str(Path.cwd()))
    args = parser.parse_args()
    result = attest_runtime_root(args.runtime_root, repo_root=args.repo_root)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
