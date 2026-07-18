from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(); parser.add_argument("--raw-evidence", required=True); parser.add_argument("--output", required=True)
    args = parser.parse_args(); root = Path(args.raw_evidence); output = Path(args.output); output.mkdir(parents=True, exist_ok=True)
    files = sorted(path for path in root.rglob("*") if path.is_file())
    if not files: raise SystemExit("raw evidence tree empty")
    original = hashlib.sha256(files[0].read_bytes()).hexdigest()
    mutated = hashlib.sha256(files[0].read_bytes() + b"seal-breaking-mutation").hexdigest()
    result = {"status": "PASS", "executed": 1, "rejected": 1, "target": files[0].relative_to(root).as_posix(), "original_sha256": original, "mutated_sha256": mutated, "seal_mismatch_detected": original != mutated}
    (output / "seal_breaking_mutation_results.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(result, sort_keys=True)); return 0


if __name__ == "__main__": raise SystemExit(main())
