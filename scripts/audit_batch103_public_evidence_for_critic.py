"""Check the public evidence overlay before the independent mutation campaign."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


REQUIRED = (
    "batch103_fresh_execution_origin_audit.json",
    "batch103_outcome_envelope_seal_receipt_v1.json",
    "reactome_planner_gain_metrics_v1.json",
    "reactome_planner_gain_gate_v1.json",
    "batch103_causal_evidence_summary_v1.json",
    "batch103_consolidated_state.json",
    "batch103_source_ownership_proof_registry_v1.json",
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--evidence-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    missing = [name for name in REQUIRED if not (args.evidence_root / name).is_file()]
    serialized = "\n".join(
        path.read_text(encoding="utf-8", errors="replace")
        for path in args.evidence_root.rglob("*")
        if path.is_file()
    )
    forbidden_markers = [
        marker
        for marker in ("PRIVATE_TRUTH_BUNDLE", "raw_private_tld", "gold_patch_payload", "future_fix_payload")
        if marker in serialized
    ]
    state = json.loads((args.evidence_root / "batch103_consolidated_state.json").read_text()) if not missing else {}
    errors = [f"missing:{name}" for name in missing]
    errors.extend(f"forbidden_marker:{marker}" for marker in forbidden_markers)
    if state and (
        state.get("ordinary_patch_count") != 0
        or state.get("repair_counts") != {"issue_derived": 6, "native_external": 4, "historical": 0}
        or state.get("release") != "PRODUCT_BETA_RC_BLOCKED_EXACT"
    ):
        errors.append("release_or_count_boundary")
    result = {
        "status": "PASS" if not errors else "BLOCK",
        "required_file_count": len(REQUIRED),
        "private_inputs_present": bool(forbidden_markers),
        "errors": errors,
        "authority_allowed": "independent public-boundary critic input review",
        "authority_forbidden": ["truth", "patch", "repair count", "release"],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(result, sort_keys=True))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
