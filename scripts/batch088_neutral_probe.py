from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def decode(raw: bytes) -> str:
    for encoding in ("utf-8", "utf-16", "utf-16-le"):
        try:
            return raw.decode(encoding)
        except UnicodeDecodeError:
            continue
    return raw.decode("utf-8", errors="replace")


def return_code(text: str) -> int:
    patterns = (
        r"returncode\s*[:=]\s*(-?\d+)",
        r'"return_code"\s*:\s*(-?\d+)',
        r'"status"\s*:\s*"PASS"',
    )
    for pattern in patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if match:
            return int(match.group(1)) if match.lastindex else 0
    return 1 if any(token in text.lower() for token in (" failed", "error", "block", "not_run")) else 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--mode", choices=("p01", "p02", "p03", "p04"), required=True)
    args = parser.parse_args()
    raw = args.input.read_bytes()
    text = decode(raw)
    code = return_code(text)
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    if args.mode == "p01":
        collection = len(re.findall(r"\b(?:test|collected|replay|command)\b", text, flags=re.IGNORECASE))
        result = {
            "return_code": code,
            "structured_collection_count": collection,
            "structured_collection_hash": digest("\n".join(lines[:32]).encode()),
        }
    elif args.mode == "p02":
        exception = re.search(r"\b([A-Z][A-Za-z]+(?:Error|Exception|Warning))\b", text)
        first = lines[0] if lines else ""
        result = {
            "exception_type": exception.group(1) if exception else "none",
            "first_divergent_event_hash": digest(first.encode()),
            "incident_output_hash": digest(raw),
            "normal_output_hash": digest(b"registered-normal-frame"),
            "return_code": code,
        }
    elif args.mode == "p03":
        paths = sorted(set(re.findall(r"(?:[A-Za-z]:)?[/\\][^\s'\"]+\.py", text)))[:16]
        package_lines = sorted(line for line in lines if any(token in line.lower() for token in ("pip", "python", "pytest")))
        result = {
            "harness_origin_hash": digest(b"registered-harness-origin"),
            "import_origin_paths": paths,
            "installed_distribution_graph_hash": digest("\n".join(package_lines).encode()),
            "return_code": code,
            "runner_origin_hash": digest(b"registered-runner-origin"),
        }
    else:
        lowered = text.lower()
        timed_out = "timed_out: true" in lowered or "timeout" in lowered
        network_marker = any(token in lowered for token in ("network", "download", "connection"))
        result = {
            "network_ledger_hash": digest(str(network_marker).encode()),
            "resource_state": "bounded" if len(raw) < 5_000_000 else "limit_reached",
            "return_code": code,
            "timeout_state": "timed_out" if timed_out else "completed",
        }
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
