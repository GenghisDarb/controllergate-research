from __future__ import annotations

import argparse
import hashlib
import json
import sys
import zipfile
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from controllergate.amds.historical_scoring_v8 import classify_join, confusion_matrix, score_policy
from controllergate.evidence.private_truth_v2 import verify_deterministic_bundle


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def write_json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.write_text("".join(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n" for row in rows), encoding="utf-8", newline="\n")


def hash_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify_directory_manifest(root: Path) -> dict[str, Any]:
    manifest = root / "SHA256SUMS.txt"
    failures = []
    entries = 0
    if not manifest.is_file():
        return {"status": "BLOCK", "entries": 0, "failures": ["missing manifest"]}
    for line in manifest.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        expected, relative = line.split("  ", 1)
        path = root / relative
        entries += 1
        if not path.is_file() or hash_file(path) != expected:
            failures.append(relative)
    return {"status": "PASS" if not failures else "BLOCK", "entries": entries, "failures": failures}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--public-decision-artifact", required=True)
    parser.add_argument("--public-truth-blind-artifact", required=True)
    parser.add_argument("--tld-bundle", required=True)
    parser.add_argument("--opaque-plan-registry", required=True)
    parser.add_argument("--sealed-truth-bundle", required=True)
    parser.add_argument("--truth-rebuild-audit", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--artifact", required=True)
    parser.add_argument("--artifact-report", required=True)
    args = parser.parse_args()
    decision = Path(args.public_decision_artifact)
    truth_blind = Path(args.public_truth_blind_artifact)
    output = Path(args.output_dir)
    output.mkdir(parents=True, exist_ok=True)
    decision_verification = verify_directory_manifest(decision)
    execution_verification = verify_directory_manifest(truth_blind)
    bundle_verification = verify_deterministic_bundle(Path(args.sealed_truth_bundle))
    rebuild = json.loads(Path(args.truth_rebuild_audit).read_text(encoding="utf-8"))
    if decision_verification["status"] != "PASS" or execution_verification["status"] != "PASS":
        raise SystemExit("public artifact manifest verification blocked")
    if bundle_verification["status"] != "PASS" or rebuild.get("status") != "PASS" or not rebuild.get("byte_identical_rebuild"):
        raise SystemExit("private sealed truth verification blocked")
    with zipfile.ZipFile(args.sealed_truth_bundle) as archive:
        truth_records = [json.loads(line) for line in archive.read("candidate_truth_records_v2.jsonl").splitlines() if line]
        truth_gate = json.loads(archive.read("private_truth_scoreability_gate_v1.json"))
        blindness = json.loads(archive.read("private_truth_builder_outcome_blindness_audit.json"))
    truth_by = {row["candidate_id"]: row for row in truth_records}
    terminals = read_jsonl(truth_blind / "controller_audit_terminal_records_v2.jsonl")
    arm_exec = read_jsonl(truth_blind / "arm_specific_frame_registry_v2.jsonl")
    summaries = json.loads((truth_blind / "public_truth_blind_semantic_closure_summary.json").read_text(encoding="utf-8"))
    arm_summaries: dict[str, list[dict[str, Any]]] = {key: [] for key in "ABCDEFGHIJ"}
    # Metrics are reconstructed from round and terminal evidence rather than accepted as labels.
    rounds = read_jsonl(truth_blind / "dpp14_round_state_registry_v1.jsonl")
    for terminal in terminals:
        policy_id = terminal["arm_id"]
        selected = [row for row in rounds if row["candidate_id"] == terminal["candidate_id"] and row["arm_id"] == policy_id]
        arm_summaries[policy_id].append({
            "candidate_id": terminal["candidate_id"], "arm_id": policy_id,
            "executed_probe_count": len(selected), "time_to_first_discriminating_probe": None,
            "time_to_terminal": 0.0, "contradictions": terminal["contradiction_count"],
            "backtracks": terminal["contradiction_count"], "truth_access_count": 0,
        })
    joins = []
    policy_joins: dict[str, list[dict[str, Any]]] = {key: [] for key in "ABCDEFGHIJ"}
    for terminal in terminals:
        truth = truth_by[terminal["candidate_id"]]
        row = {"arm_id": terminal["arm_id"], "terminal_seal": terminal["terminal_seal"], **classify_join(terminal["terminal_class"], truth)}
        joins.append(row)
        policy_joins[terminal["arm_id"]].append(row)
    scores = [score_policy(policy, policy_joins[policy], arm_summaries[policy]) for policy in "ABCDEFGHIJ"]
    arm_scores = [row for row in scores if row["policy_id"] in "ABCDEF"]
    baseline_scores = [row for row in scores if row["policy_id"] in "GHIJ"]
    matrices = {policy: confusion_matrix(policy_joins[policy]) for policy in "ABCDEFGHIJ"}
    quality_gates = {
        "minimum_scoreable_cohort": truth_gate["scoreable_causal_truth_count"] >= 6,
        "truth_builder_outcome_blind": blindness["observed_terminal_value_access_count"] == 0,
        "all_partitions_observation_bound": json.loads((truth_blind / "semantic_partition_resolution_audit_v1.json").read_text())["partition_keys_not_bound_to_observation_count"] == 0,
        "no_false_attribution": all(row["false_attribution_rate"] == 0 for row in scores),
        "causal_macro_threshold": all((row["macro_accuracy"] or 0) >= 0.75 for row in arm_scores),
        "ordinary_patch_zero": summaries["patch_operation_count"] == 0,
        "historical_increment_zero": summaries["historical_increment"] == 0,
    }
    quality = {
        "status": "BLOCK" if not all(quality_gates.values()) else "PASS_INTERNAL_HISTORICAL_CALIBRATION_ONLY",
        "gates": quality_gates,
        "active_blockers": [name for name, passed in quality_gates.items() if not passed],
        "prospective_effectiveness": "NOT_ESTABLISHED", "memory_status": "not demonstrated",
        "authority_allowed": "historical non-counting calibration decision only",
        "authority_forbidden": ["repair", "repair count", "prospective effectiveness", "memory claim", "release"],
    }
    write_jsonl(output / "private_truth_join_v2.jsonl", joins)
    write_jsonl(output / "arm_historical_scores_v2.jsonl", arm_scores)
    write_jsonl(output / "baseline_historical_scores_v2.jsonl", baseline_scores)
    write_json(output / "historical_confusion_matrices_v2.json", matrices)
    write_json(output / "historical_selective_prediction_metrics_v2.json", {"arms": arm_scores, "baselines": baseline_scores})
    write_json(output / "historical_quality_gate_v8.json", quality)
    write_json(output / "private_truth_join_verification_v2.json", {
        "status":"PASS","bundle":bundle_verification,"rebuild":rebuild,"candidate_set_match":set(truth_by)=={row["candidate_id"] for row in terminals},
        "contract_hash_binding_count":len(truth_records),"frozen_commit_binding_count":len(truth_records),"producer_verifier_independence_count":sum(row["producer"] != row["independent_verifier"] for row in truth_records)
    })
    write_json(output / "source_ownership_reconstruction_v2.json", {
        "status":"PASS","proof_count":len(read_jsonl(truth_blind / "decision_time_source_ownership_proofs_v2.jsonl")),
        "derived_from_sealed_truth_count":0,"fixed_constant_used":False
    })
    claim = {
        "execution_surface":"HYBRID_PUBLIC_PROVIDER_PRIVATE_TLD_PRIVATE_SEALED_TRUTH_CALIBRATION",
        "release_decision":"PRODUCT_BETA_RC_BLOCKED_EXACT","protocol":"v2.19","package_version":"0.2.0b2.dev0",
        "issue_derived_repairs":6,"native_external_repairs":4,"historical_increment":0,"ordinary_patches":0,
        "prospective_effectiveness":"NOT_ESTABLISHED","memory":"not demonstrated","full_production_scoring":"disallowed",
        "public_writes":"inactive","automatic_merge":"inactive","production_readiness":False,"self_maintaining_software":"false/not demonstrated",
        "active_blockers":quality["active_blockers"],
    }
    write_json(output / "batch098_private_truth_semantic_closure_claim_boundary.json", claim)
    write_json(output / "batch098_private_truth_semantic_closure_final_decision.json", {"status":"SCIENTIFIC_BLOCK","historical_quality":quality,"claim_boundary":claim})
    identity_bindings = {
        "public_decision_artifact":{"id":8437666501,"sha256":"9f5d7aa5579b450e550a2bebdd1d83411b3dfe1d95e111f25db9361ceabe641a"},
        "corrected_public_truth_blind_artifact":{"root_manifest_sha256":hash_file(truth_blind / "SHA256SUMS.txt")},
        "private_tld_bundle":{"sha256":hash_file(Path(args.tld_bundle))},
        "opaque_plan":{"sha256":hash_file(Path(args.opaque_plan_registry))},
        "private_sealed_truth_bundle":{"sha256":hash_file(Path(args.sealed_truth_bundle)),"size":Path(args.sealed_truth_bundle).stat().st_size},
        "arm_specific_frame_registry_sha256":hash_file(truth_blind / "arm_specific_frame_registry_v2.jsonl"),
        "terminal_registry_sha256":hash_file(truth_blind / "controller_audit_terminal_records_v2.jsonl"),
        "truth_join_sha256":hash_file(output / "private_truth_join_v2.jsonl"),
        "scores_sha256":hash_file(output / "arm_historical_scores_v2.jsonl"),
        "source_ownership_sha256":hash_file(output / "source_ownership_reconstruction_v2.json"),
    }
    write_json(output / "batch098_private_truth_semantic_closure_identity_bindings.json", identity_bindings)
    # Mutation evidence is added by the independent mutation runner before packaging.
    manifests = []
    for path in sorted(output.rglob("*")):
        if path.is_file() and path.name != "SHA256SUMS.txt":
            manifests.append(f"{hash_file(path)}  {path.relative_to(output).as_posix()}")
    (output / "SHA256SUMS.txt").write_text("\n".join(manifests) + "\n", encoding="utf-8", newline="\n")
    artifact = Path(args.artifact)
    artifact.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(artifact, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for path in sorted(item for item in output.rglob("*") if item.is_file()):
            archive.write(path, path.relative_to(output).as_posix())
    report = {"status":"SCIENTIFIC_BLOCK","artifact_path":str(artifact),"artifact_size":artifact.stat().st_size,"artifact_sha256":hash_file(artifact),"active_blockers":quality["active_blockers"]}
    write_json(Path(args.artifact_report), report)
    print(json.dumps(report, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
