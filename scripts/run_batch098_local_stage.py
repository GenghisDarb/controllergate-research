from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
from pathlib import Path


def tree_hash(path: Path | None) -> str | None:
    if path is None or not path.exists():
        return None
    if path.is_file():
        return hashlib.sha256(path.read_bytes()).hexdigest()
    rows = []
    for child in sorted(path.rglob("*")):
        if child.is_file():
            rows.append((child.relative_to(path).as_posix(), hashlib.sha256(child.read_bytes()).hexdigest()))
    return hashlib.sha256(json.dumps(rows, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--stage", required=True)
    parser.add_argument("--role", choices=("producer", "verifier", "custody", "critic", "finalizer"), required=True)
    parser.add_argument("--input")
    parser.add_argument("--output")
    parser.add_argument("--receipts", required=True)
    parser.add_argument("--truth-preterminal-access", action="store_true")
    parser.add_argument("command", nargs=argparse.REMAINDER)
    args = parser.parse_args()
    command = args.command[1:] if args.command and args.command[0] == "--" else args.command
    if not command:
        raise SystemExit("stage command is required")
    input_path = Path(args.input) if args.input else None
    output_path = Path(args.output) if args.output else None
    before = tree_hash(input_path)
    completed = subprocess.run(command, check=False)
    after = tree_hash(output_path)
    receipt = {
        "stage": args.stage,
        "role": args.role,
        "process_id": os.getpid(),
        "child_return_code": completed.returncode,
        "input_handoff_hash": before,
        "output_handoff_hash": after,
        "shared_mutable_memory": False,
        "truth_preterminal_access": bool(args.truth_preterminal_access),
    }
    receipt_path = Path(args.receipts)
    receipt_path.parent.mkdir(parents=True, exist_ok=True)
    with receipt_path.open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(receipt, sort_keys=True, separators=(",", ":")) + "\n")
    return completed.returncode


if __name__ == "__main__":
    raise SystemExit(main())
