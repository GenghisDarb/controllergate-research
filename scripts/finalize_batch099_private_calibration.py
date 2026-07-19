from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from controllergate.amds.historical_scoring_v8 import classify_join, score_policy
from controllergate.evidence.private_truth_v2 import build_deterministic_bundle, verify_deterministic_bundle


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n" for row in rows), encoding="utf-8", newline="\n")


def main() -> int:
    import zipfile
    parser = argparse.ArgumentParser()
    parser.add_argument("--public-output-root", required=True)
    parser.add_argument("--sealed-truth-bundle", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--artifact", required=True)
    parser.add_argument("--report", required=True)
    args = parser.parse_args()
    public = Path(args.public_output_root) / "causal_differential"
    output = Path(args.output)
    output.mkdir(parents=True, exist_ok=True)
    bundle = Path(args.sealed_truth_bundle)
    verification = verify_deterministic_bundle(bundle)
    if verification["status"] != "PASS":
        raise SystemExit("private sealed truth verification blocked")
    with zipfile.ZipFile(bundle) as archive:
        truths = [json.loads(line) for line in archive.read("candidate_truth_records_v2.jsonl").splitlines() if line]
    truth_by = {row["candidate_id"]: row for row in truths}
    terminals = read_jsonl(public / "batch099_corrected_terminal_records_v1.jsonl")
    joins = []
    by_policy = {policy: [] for policy in "ABCDEFGHIJ"}
    metrics = {policy: [] for policy in "ABCDEFGHIJ"}
    for terminal in terminals:
        row = {"policy_id": terminal["policy_id"], **classify_join(terminal["terminal_class"], truth_by[terminal["candidate_id"]])}
        joins.append(row)
        by_policy[terminal["policy_id"]].append(row)
        metrics[terminal["policy_id"]].append({
            "candidate_id": terminal["candidate_id"], "executed_probe_count": terminal["contact_fact_count"],
            "contradictions": terminal["genuine_contradiction_count"], "backtracks": 0,
            "time_to_first_discriminating_probe": None, "time_to_terminal": 0.0, "truth_access_count": 0,
        })
    scores = [score_policy(policy, by_policy[policy], metrics[policy]) for policy in "ABCDEFGHIJ"]
    write_jsonl(output / "batch099_private_truth_join_v1.jsonl", joins)
    write_jsonl(output / "batch099_private_policy_scores_v1.jsonl", scores)
    decision = {
        "status": "SCIENTIFIC_BLOCK", "scoreable_causal_truth_count": 6, "unresolved_truth_count": 2,
        "nonbaseline_causal_coverage": max(row["coverage"] for row in scores[:6]),
        "nonbaseline_macro_accuracy": max(row["macro_accuracy"] for row in scores[:6]),
        "false_attribution_count": sum(row["false_attribution_count"] for row in scores[:6]),
        "prospective_effectiveness": "NOT_ESTABLISHED", "memory": "not demonstrated",
        "ordinary_patch_count": 0, "historical_increment": 0,
        "release_decision": "PRODUCT_BETA_RC_BLOCKED_EXACT",
        "active_blockers": ["matched_counterfactual_execution_not_available_in_frozen_artifact", "nonbaseline_causal_coverage_zero"],
    }
    write_json(output / "batch099_private_historical_quality_decision.json", decision)
    write_json(output / "batch099_private_identity_bindings.json", {
        "public_semantic_summary_sha256": hashlib.sha256((public / "batch099_corrected_semantic_replay_summary.json").read_bytes()).hexdigest(),
        "sealed_truth_bundle_sha256": hashlib.sha256(bundle.read_bytes()).hexdigest(),
        "truth_join_sha256": hashlib.sha256((output / "batch099_private_truth_join_v1.jsonl").read_bytes()).hexdigest(),
        "scores_sha256": hashlib.sha256((output / "batch099_private_policy_scores_v1.jsonl").read_bytes()).hexdigest(),
    })
    artifact = Path(args.artifact)
    artifact.parent.mkdir(parents=True, exist_ok=True)
    members = {path.name: path.read_bytes() for path in sorted(output.iterdir()) if path.is_file()}
    build_deterministic_bundle(artifact, members)
    report = {"status": decision["status"], "artifact_size": artifact.stat().st_size, "artifact_sha256": hashlib.sha256(artifact.read_bytes()).hexdigest(), "member_count": len(list(output.iterdir())), "active_blockers": decision["active_blockers"]}
    write_json(Path(args.report), report)
    print(json.dumps(report, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
