#!/usr/bin/env python3
"""Stage the compact public Batch101 artifact and write non-self manifests."""

from __future__ import annotations

import argparse
import hashlib
import shutil
from pathlib import Path


EXCLUDED_PARTS = {"extracted_public_artifact", "__pycache__", ".git", "site-packages"}
EXCLUDED_SUFFIXES = {".zip", ".tar", ".pyc", ".pyd"}
MANIFESTS = {"SHA256SUMS.txt", "ARTIFACT_SHA256SUMS.txt", "PORTABLE_ARTIFACT_SHA256SUMS.txt"}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--destination", type=Path, required=True)
    args = parser.parse_args()
    if args.destination.exists():
        shutil.rmtree(args.destination)
    args.destination.mkdir(parents=True)
    for source in sorted(args.source.rglob("*")):
        rel = source.relative_to(args.source)
        if not source.is_file() or set(rel.parts) & EXCLUDED_PARTS or source.suffix.lower() in EXCLUDED_SUFFIXES or source.name in MANIFESTS:
            continue
        target = args.destination / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
    lines = []
    for path in sorted(args.destination.rglob("*")):
        if path.is_file() and path.name not in MANIFESTS:
            rel = path.relative_to(args.destination).as_posix()
            lines.append(f"{hashlib.sha256(path.read_bytes()).hexdigest()}  {rel}\n")
    payload = "".join(lines)
    # The two portable manifests cover only the payload.  The root manifest
    # additionally covers both portable manifests and never hashes itself.
    for name in ("ARTIFACT_SHA256SUMS.txt", "PORTABLE_ARTIFACT_SHA256SUMS.txt"):
        (args.destination / name).write_text(payload, encoding="utf-8", newline="\n")
    root_payload = payload
    for name in ("ARTIFACT_SHA256SUMS.txt", "PORTABLE_ARTIFACT_SHA256SUMS.txt"):
        path = args.destination / name
        root_payload += f"{hashlib.sha256(path.read_bytes()).hexdigest()}  {name}\n"
    (args.destination / "SHA256SUMS.txt").write_text(root_payload, encoding="utf-8", newline="\n")
    print(f"staged_files={len(lines)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
