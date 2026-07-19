from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--receipts", required=True)
    parser.add_argument("--wheel", required=True)
    parser.add_argument("--installed-origin", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--minimum-processes", type=int, default=20)
    args = parser.parse_args()
    receipt_path = Path(args.receipts)
    rows = [json.loads(line) for line in receipt_path.read_text(encoding="utf-8").splitlines() if line.strip()] if receipt_path.exists() else []
    wheel = Path(args.wheel)
    processes = {row["process_id"] for row in rows}
    shared = sum(bool(row.get("shared_mutable_memory")) for row in rows)
    truth = sum(bool(row.get("truth_preterminal_access")) for row in rows)
    failures = sum(int(row.get("child_return_code", 1)) != 0 for row in rows)
    producers = sum(row.get("role") == "producer" for row in rows)
    verifiers = sum(row.get("role") == "verifier" for row in rows)
    immutable = sum(bool(row.get("output_handoff_hash")) for row in rows)
    status = "PASS" if len(processes) >= args.minimum_processes and producers and verifiers and shared == 0 and truth == 0 and failures == 0 and wheel.is_file() else "BLOCK"
    value = {
        "status": status,
        "execution_surface": "LOCAL_PROTECTED_SOURCE_RUN",
        "process_count": len(processes),
        "producer_process_count": producers,
        "verifier_process_count": verifiers,
        "shared_mutable_memory_count": shared,
        "immutable_handoff_count": immutable,
        "truth_preterminal_access_count": truth,
        "failed_process_count": failures,
        "installed_wheel_origin": args.installed_origin,
        "installed_wheel_sha256": hashlib.sha256(wheel.read_bytes()).hexdigest() if wheel.is_file() else None,
        "minimum_process_count": args.minimum_processes,
    }
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(value, sort_keys=True))
    return 0 if status == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
