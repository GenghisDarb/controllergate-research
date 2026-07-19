from __future__ import annotations

import argparse
import json
from pathlib import Path


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--decision-artifact", required=True)
    parser.add_argument("--candidate-evidence", required=True)
    parser.add_argument("--candidate", required=True)
    parser.add_argument("--provider-receipt", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    decision = Path(args.decision_artifact)
    current_root = Path(args.candidate_evidence)
    current = load(current_root / "candidate_lane_result_v2.json")
    current_observation = load(current_root / "neutral_observation_v2.json")
    originals = [load(path) for path in decision.rglob("candidate_lane_result_v2.json")]
    originals = [row for row in originals if row.get("candidate_id") == args.candidate]
    original = originals[0] if originals else {}
    original_paths = [path for path in decision.rglob("candidate_lane_result_v2.json") if load(path).get("candidate_id") == args.candidate]
    original_root = original_paths[0].parent if original_paths else None
    original_observation = load(original_root / "neutral_observation_v2.json") if original_root else {}
    provider = load(Path(args.provider_receipt))
    checks = {
        "candidate_id": current.get("candidate_id") == original.get("candidate_id") == args.candidate,
        "source_commit": current.get("source_commit") == original.get("source_commit"),
        "candidate_contract": current.get("contract_hash") == original.get("contract_hash"),
        "source_manifest": current.get("source_manifest_hash_before") == original.get("source_manifest_hash_before"),
        "test_manifest": current.get("test_manifest_hash_before") == original.get("test_manifest_hash_before"),
        "target_return_code": current_observation.get("return_code") == original_observation.get("return_code"),
        "typed_incident_status": current.get("typed_incident", {}).get("status") == original.get("typed_incident", {}).get("status"),
        "provider_exact": provider.get("status") == "PASS_EXACT_FROZEN_LINUX_PARITY",
        "candidate_substitution_zero": current.get("candidate_substitution") is False,
        "future_outcome_zero": current.get("future_or_outcome_evidence_count") == 0,
        "patch_zero": current.get("patch_operation_count") == 0,
    }
    result = {
        "candidate_id": args.candidate,
        "status": "PASS" if all(checks.values()) else "BLOCK",
        "checks": checks,
        "original_evidence_copy_count": len(originals),
        "provider_verification_receipt": provider.get("verification_receipt"),
        "producer": "scripts/verify_batch098_reconstruction_equivalence.py",
        "execution_depth": "second independent exact-provider materialization comparison",
        "semantic_scope": "public decision-time environment equivalence",
        "authority_allowed": "truth-blind probe execution",
        "authority_forbidden": ["truth", "source ownership", "repair", "count", "release"],
    }
    Path(args.output).write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(result, sort_keys=True))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
