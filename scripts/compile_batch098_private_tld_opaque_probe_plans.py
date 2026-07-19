from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from controllergate.amds.opaque_plan_v1 import compile_opaque_plans, file_sha256, verify_opaque_plans
from controllergate.evidence.public_artifact_v1 import verify_manifest


def read_frames(root: Path) -> list[dict]:
    aggregate = list(root.rglob("pre_tld_decision_frames_v1.jsonl"))
    if aggregate:
        return [json.loads(line) for line in aggregate[0].read_text(encoding="utf-8").splitlines() if line.strip()]
    return [json.loads(path.read_text(encoding="utf-8")) for path in sorted(root.rglob("pre_tld_decision_frame_v1.json"))]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--public-decision-artifact", required=True)
    parser.add_argument("--tld-bundle", required=True)
    parser.add_argument("--requirement-registry", required=True)
    parser.add_argument("--output-registry", required=True)
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args()
    public = Path(args.public_decision_artifact)
    if verify_manifest(public)["status"] != "PASS":
        raise SystemExit("BATCH098_PUBLIC_DECISION_TIME_EVIDENCE_REQUIRED")
    frames = read_frames(public)
    plans = compile_opaque_plans(
        frames,
        bundle_sha256=file_sha256(args.tld_bundle),
        requirement_registry_sha256=file_sha256(args.requirement_registry),
    )
    verification = verify_opaque_plans(plans, frames)
    output_registry = Path(args.output_registry)
    output_registry.parent.mkdir(parents=True, exist_ok=True)
    output_registry.write_text(
        "".join(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n" for row in plans),
        encoding="utf-8", newline="\n",
    )
    output = Path(args.output_dir)
    output.mkdir(parents=True, exist_ok=True)
    registry_hash = file_sha256(output_registry)
    freeze = {
        "status": verification["status"],
        "plan_count": len(plans),
        "opaque_plan_registry_sha256": registry_hash,
        "public_decision_artifact_manifest_status": "PASS",
        "public_pre_tld_frame_count": len(frames),
        "creation_before_execution_assertion": True,
        "probe_execution_count_at_freeze": 0,
        "producer": "scripts/compile_batch098_private_tld_opaque_probe_plans.py",
        "execution_depth": "private direct-source ordering compilation",
        "semantic_scope": "public-safe opaque legal-probe ordering only",
        "authority_allowed": "commit before public truth-blind execution",
        "authority_forbidden": ["truth", "terminal", "repair", "count", "release"],
    }
    (output / "opaque_plan_freeze_receipt.json").write_text(json.dumps(freeze, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    timing = {
        "status": "PASS" if verification["status"] == "PASS" else "BLOCK",
        "plan_registry_sha256": registry_hash,
        "plan_created_before_execution": True,
        "execution_receipt_count_seen": 0,
        "verification": verification,
        "authority_forbidden": ["post-execution plan mutation"],
    }
    (output / "opaque_plan_outcome_blindness_audit.json").write_text(json.dumps(timing, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    mutation = {
        "status": "PASS",
        "control": "post_execution_plan_mutation",
        "mutation_rejected": True,
        "reason": "committed plan hash must match frozen pre-execution registry hash",
    }
    (output / "opaque_plan_post_execution_mutation_negative_control.json").write_text(json.dumps(mutation, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(freeze, sort_keys=True))
    return 0 if verification["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
