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
    portable_payload = "\n".join(rows) + "\n"
    portable_path = args.output / "PORTABLE_ARTIFACT_SHA256SUMS.txt"
    portable_path.write_text(portable_payload, encoding="utf-8", newline="\n")
    portable_hash = hashlib.sha256(portable_path.read_bytes()).hexdigest()
    primary_payload = (
        f"{portable_hash}  PORTABLE_ARTIFACT_SHA256SUMS.txt\n" + portable_payload
    )
    (args.output / "SHA256SUMS.txt").write_text(
        primary_payload, encoding="utf-8", newline="\n"
    )
    print(f"manifest_entries={len(rows)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
