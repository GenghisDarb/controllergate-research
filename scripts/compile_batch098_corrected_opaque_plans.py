from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from controllergate.amds.semantic_closure_v8 import compile_arm_frame


def digest(value: object) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), default=str).encode()).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--decision-artifact", required=True)
    parser.add_argument("--private-tld-bundle", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--created-at-utc", default="2026-07-19T07:00:00Z")
    args = parser.parse_args()
    root = Path(args.decision_artifact)
    tld = Path(args.private_tld_bundle)
    tld_hash = hashlib.sha256(tld.read_bytes()).hexdigest()
    if tld_hash != "e18d208e0428944674d6ca6aa9d50609e2256e28ab83dad92ad583dc1ad8a644":
        raise SystemExit("private TLD bundle identity mismatch")
    rows = []
    for path in sorted(root.glob("evidence/batch098-public-pre-tld-*/pre_tld_decision_frame_v1.json")):
        base = json.loads(path.read_text(encoding="utf-8"))
        for arm_id in ("E", "F"):
            provisional = compile_arm_frame(base, arm_id, []) if False else None
            kinds = {
                "E": {"contact_edge", "provider_variation", "boundary_dimension", "runner_variation", "harness_variation", "service_variation", "expectation_relation"},
                "F": {"contact_edge", "provider_variation", "boundary_dimension", "runner_variation", "harness_variation", "service_variation", "expectation_relation", "modality_conflict"},
            }[arm_id]
            probe_ids = [row["probe_id"] for row in base["legal_probes"] if row["probe_kind"] in kinds]
            ordered = sorted(probe_ids, key=lambda probe_id: digest([tld_hash, base["candidate_id"], arm_id, probe_id]))
            row = {
                "schema": "Batch098CorrectedOpaqueProbePlanV2",
                "candidate_id": base["candidate_id"], "arm_id": arm_id,
                "source_frame_hash": digest(base), "legal_probe_inventory_hash": digest(sorted(probe_ids)),
                "ordered_opaque_probe_ids": ordered, "tld_bundle_identity_hash": tld_hash,
                "created_at_utc": args.created_at_utc, "creation_before_execution_assertion": True,
                "private_tld_passage_count": 0, "truth_field_count": 0,
                "authority_allowed": "ordering of already legal probes only",
                "authority_forbidden": ["causal fact", "terminal", "truth", "source ownership", "repair", "count", "release"],
            }
            row["plan_hash"] = digest(row)
            rows.append(row)
    if len(rows) != 16:
        raise SystemExit("corrected opaque plan requires two plans for eight candidates")
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("".join(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n" for row in rows), encoding="utf-8", newline="\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
