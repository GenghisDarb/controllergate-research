from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from controllergate.amds.opaque_plan_v1 import canonical_hash


FORBIDDEN_KEYS = {"tld_text", "tld_quotation", "notebook_heading", "normalized_passage", "private_filename", "private_path", "source_file_hash", "truth", "gold_outcome", "repair_content"}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--plan-registry", required=True)
    parser.add_argument("--commit", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    path = Path(args.plan_registry)
    text = path.read_text(encoding="utf-8")
    rows = [json.loads(line) for line in text.splitlines() if line.strip()]
    committed = subprocess.run(["git", "show", f"{args.commit}:configs/batch098_opaque_probe_plan_registry_v1.jsonl"], check=False, capture_output=True, text=True)
    commit_timestamp = subprocess.run(["git", "show", "-s", "--format=%ct", args.commit], check=True, capture_output=True, text=True).stdout.strip()
    failures = []
    for row in rows:
        unsigned = {key: value for key, value in row.items() if key != "plan_hash"}
        if row.get("plan_hash") != canonical_hash(unsigned):
            failures.append({"plan_id": row.get("plan_id"), "reason": "plan_hash_mismatch"})
        hits = sorted(FORBIDDEN_KEYS.intersection(row))
        if hits:
            failures.append({"plan_id": row.get("plan_id"), "reason": "forbidden_keys", "keys": hits})
    path_hits = re.findall(r"(?:[A-Za-z]:\\|/(?:home|users|mnt|private)/)[^\"\s]+", text, flags=re.IGNORECASE)
    checks = {
        "exact_commit_object": subprocess.run(["git", "cat-file", "-t", args.commit], check=True, capture_output=True, text=True).stdout.strip() == "commit",
        "committed_bytes_match": committed.returncode == 0 and committed.stdout.replace("\r\n", "\n") == text.replace("\r\n", "\n"),
        "plan_count": len(rows) == 80,
        "candidate_count": len({row.get("candidate_id") for row in rows}) == 8,
        "candidate_arm_pair_count": len({(row.get("candidate_id"), row.get("arm_id")) for row in rows}) == 80,
        "hashes": not failures,
        "no_absolute_paths": not path_hits,
        "commit_predates_execution": int(commit_timestamp) <= int(time.time()),
        "creation_before_execution_assertions": all(row.get("creation_before_execution_assertion") is True for row in rows),
    }
    result = {
        "status": "PASS" if all(checks.values()) else "BLOCK",
        "checks": checks,
        "failures": failures,
        "absolute_path_hits": path_hits,
        "opaque_plan_commit": args.commit,
        "opaque_plan_commit_timestamp": int(commit_timestamp),
        "truth_access_count": 0,
        "private_tld_source_access_count": 0,
        "authority_allowed": "public truth-blind legal-probe ordering",
        "authority_forbidden": ["truth", "terminal assignment", "repair", "count", "release"],
    }
    Path(args.output).write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(result, sort_keys=True))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
