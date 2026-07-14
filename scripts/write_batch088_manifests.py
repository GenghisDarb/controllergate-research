from __future__ import annotations

import argparse
import hashlib
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    excluded = {"SHA256SUMS.txt", "PORTABLE_ARTIFACT_SHA256SUMS.txt"}
    rows = []
    for path in sorted(args.output.rglob("*")):
        if path.is_file() and path.name not in excluded:
            relative = path.relative_to(args.output).as_posix()
            rows.append(f"{hashlib.sha256(path.read_bytes()).hexdigest()}  {relative}")
    payload = "\n".join(rows) + "\n"
    for name in excluded:
        (args.output / name).write_text(payload, encoding="utf-8", newline="\n")
    print(f"manifest_entries={len(rows)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
