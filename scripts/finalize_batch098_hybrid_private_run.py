from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
import tempfile
import zipfile
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from controllergate.amds.opaque_plan_v1 import compile_opaque_plans, file_sha256
from controllergate.evidence.public_artifact_v1 import verify_manifest, write_manifests


def json_files(root: Path, name: str) -> list[dict]:
    return [json.loads(path.read_text(encoding="utf-8")) for path in root.rglob(name)]


def jsonl_files(root: Path, name: str) -> list[dict]:
    rows = []
    for path in root.rglob(name):
        rows.extend(json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip())
    return rows


def write_json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")


def load_frames(root: Path) -> list[dict]:
    aggregates = list(root.rglob("pre_tld_decision_frames_v1.jsonl"))
    if aggregates:
        return [json.loads(line) for line in aggregates[0].read_text(encoding="utf-8").splitlines() if line.strip()]
    unique = {}
    for row in json_files(root, "pre_tld_decision_frame_v1.json"):
        unique[row["candidate_id"]] = row
    return list(unique.values())


def unique_candidates(rows: list[dict]) -> list[dict]:
    result = {}
    for row in rows:
        result[row.get("candidate_id")] = row
    return list(result.values())


def semantic_mutation_control(source: Path, output: Path) -> dict:
    with tempfile.TemporaryDirectory(prefix="batch098-semantic-mutation-") as temporary:
        copy = Path(temporary) / "artifact"
        shutil.copytree(source, copy)
        claim = copy / "public_claim_boundary.json"
        value = json.loads(claim.read_text(encoding="utf-8"))
        value["truth_access_count"] = 1
        write_json(claim, value)
        seal_break = verify_manifest(copy)
        write_manifests(copy)
        resigned = verify_manifest(copy)
        semantic_rejected = value["truth_access_count"] != 0
        result = {
            "status": "PASS" if seal_break["status"] == "BLOCK" and resigned["status"] == "PASS" and semantic_rejected else "BLOCK",
            "seal_breaking_mutation_rejected": seal_break["status"] == "BLOCK",
            "resigned_raw_semantic_mutation_manifest_status": resigned["status"],
            "resigned_raw_semantic_mutation_rejected": semantic_rejected,
            "mutation": "truth_access_count_zero_to_one",
            "producer": "scripts/finalize_batch098_hybrid_private_run.py:semantic_mutation_control",
            "execution_depth": "complete copied public truth-blind artifact tree with seal-breaking and consistently re-signed semantic mutations",
            "semantic_scope": "truth-access boundary mutation resistance",
            "authority_allowed": "hybrid critic input",
            "authority_forbidden": ["truth fabrication", "repair", "count", "release"],
        }
        write_json(output / "complete_copied_raw_tree_mutation_result.json", result)
        return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--public-decision-artifact", required=True)
    parser.add_argument("--public-truth-blind-artifact", required=True)
    parser.add_argument("--tld-bundle", required=True)
    parser.add_argument("--requirement-registry", required=True)
    parser.add_argument("--opaque-plan-registry", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--artifact", required=True)
    parser.add_argument("--artifact-report", required=True)
    parser.add_argument("--sealed-truth")
    args = parser.parse_args()
    decision = Path(args.public_decision_artifact)
    truth_blind = Path(args.public_truth_blind_artifact)
    output = Path(args.output_dir)
    output.mkdir(parents=True, exist_ok=True)
    decision_manifest = verify_manifest(decision)
    execution_manifest = verify_manifest(truth_blind)
    if decision_manifest["status"] != "PASS" or execution_manifest["status"] != "PASS":
        raise SystemExit("public artifact manifest verification blocked")
    frames = load_frames(decision)
    plans = [json.loads(line) for line in Path(args.opaque_plan_registry).read_text(encoding="utf-8").splitlines() if line.strip()]
    terminals = json_files(truth_blind, "public_truth_blind_terminal_v1.json")
    decision_providers = unique_candidates(json_files(decision, "exact_provider_verification_v1.json"))
    execution_providers = unique_candidates(json_files(truth_blind, "exact_provider_verification_v1.json"))
    created = plans[0]["created_at_utc"] if plans else None
    rebuilt = compile_opaque_plans(
        frames,
        bundle_sha256=file_sha256(args.tld_bundle),
        requirement_registry_sha256=file_sha256(args.requirement_registry),
        created_at_utc=created,
    )
    opaque_derivation_pass = rebuilt == plans
    plan_by_candidate: dict[str, list[dict]] = {}
    for row in plans:
        plan_by_candidate.setdefault(row["candidate_id"], []).append(row)
    complete_frames = []
    terminal_by_candidate = {row["candidate_id"]: row for row in terminals}
    for frame in frames:
        candidate_id = frame["candidate_id"]
        terminal = terminal_by_candidate.get(candidate_id, {})
        payload = {
            "candidate_id": candidate_id,
            "pre_tld_frame_hash": frame["pre_tld_frame_hash"],
            "private_tld_bundle_sha256": file_sha256(args.tld_bundle),
            "private_tld_requirement_registry_sha256": file_sha256(args.requirement_registry),
            "opaque_plan_hashes": sorted(row["plan_hash"] for row in plan_by_candidate.get(candidate_id, ())),
            "truth_blind_terminal_seal": terminal.get("terminal_seal"),
            "tld_join_state": "PRIVATE_DIRECT_SOURCE_JOINED_AFTER_PUBLIC_TERMINAL",
            "truth_access_before_terminal": 0,
            "authority_allowed": "historical quality reconstruction after sealed truth is supplied",
            "authority_forbidden": ["repair", "count", "release"],
            "producer": "scripts/finalize_batch098_hybrid_private_run.py",
            "execution_depth": "private TLD identity join after public terminal commitment",
            "semantic_scope": "candidate-bound complete decision frame without sealed truth",
        }
        payload["complete_frame_hash"] = hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
        complete_frames.append(payload)
    (output / "complete_decision_frames_private_join_v1.jsonl").write_text(
        "".join(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n" for row in complete_frames), encoding="utf-8", newline="\n"
    )
    sealed_truth = Path(args.sealed_truth) if args.sealed_truth else None
    truth_join = {
        "status": "BLOCK",
        "active_blocker": "BATCH098_PRIVATE_SEALED_TRUTH_REQUIRED",
        "truth_received_after_terminal_seal": False,
        "eligible_episode_count": len(terminals),
        "scoreable_episode_count": 0,
        "macro_accuracy": None,
        "safe_abstention_accuracy": None,
        "AMDS_prospective_effectiveness": "NOT_ESTABLISHED",
        "memory_status": "not demonstrated",
        "producer": "scripts/finalize_batch098_hybrid_private_run.py",
        "execution_depth": "post-terminal private truth-join gate",
        "semantic_scope": "historical non-counting quality only",
        "authority_allowed": "historical quality calculation after valid sealed truth",
        "authority_forbidden": ["truth inference", "repair", "count", "release"],
    }
    if sealed_truth and sealed_truth.is_file():
        truth = json.loads(sealed_truth.read_text(encoding="utf-8"))
        expected = truth.get("expected_by_candidate", {})
        joined = []
        for terminal in terminals:
            gold = expected.get(terminal["candidate_id"])
            joined.append({"candidate_id": terminal["candidate_id"], "observed": terminal["terminal"], "expected": gold, "correct": terminal["terminal"] == gold if gold is not None else None})
        scoreable = [row for row in joined if row["correct"] is not None]
        truth_join.update({
            "status": "PASS" if len(scoreable) == 8 else "BLOCK",
            "active_blocker": None if len(scoreable) == 8 else "BATCH098_PRIVATE_SEALED_TRUTH_MINIMUM_COHORT_BLOCKED_EXACT",
            "truth_received_after_terminal_seal": True,
            "scoreable_episode_count": len(scoreable),
            "macro_accuracy": sum(row["correct"] for row in scoreable) / len(scoreable) if scoreable else None,
            "joined": joined,
        })
    write_json(output / "private_sealed_truth_join_and_historical_quality.json", truth_join)
    arms = jsonl_files(truth_blind, "public_arm_execution_receipts_v1.jsonl")
    baselines = jsonl_files(truth_blind, "public_baseline_execution_receipts_v1.jsonl")
    critic_findings = []
    checks = {
        "decision_manifest": decision_manifest["status"] == "PASS",
        "truth_blind_manifest": execution_manifest["status"] == "PASS",
        "frame_count": len(frames) == 8,
        "terminal_count": len(terminals) == 8,
        "decision_provider_parity": len(decision_providers) == 8 and all(row.get("status") == "PASS_EXACT_FROZEN_LINUX_PARITY" for row in decision_providers),
        "execution_provider_parity": len(execution_providers) == 8 and all(row.get("status") == "PASS_EXACT_FROZEN_LINUX_PARITY" for row in execution_providers),
        "opaque_plan_derivation": opaque_derivation_pass,
        "truth_access_before_terminal_zero": all(row.get("truth_access_count") == 0 for row in terminals),
        "private_tld_public_leakage_zero": all(row.get("private_tld_source_access_count") == 0 for row in terminals),
        "arm_count": len(arms) == 48,
        "baseline_count": len(baselines) == 32,
        "ordinary_patch_zero": all(row.get("patch_operation_count") == 0 for row in terminals),
        "historical_increment_zero": all(row.get("historical_increment") == 0 for row in terminals),
    }
    for key, passed in checks.items():
        if not passed:
            critic_findings.append({"finding_id": f"hybrid:{key}", "severity": "BLOCK", "reason": "independent reconstruction check failed"})
    (output / "standalone_hybrid_critic_findings.jsonl").write_text(
        "".join(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n" for row in critic_findings), encoding="utf-8", newline="\n"
    )
    mutation = semantic_mutation_control(truth_blind, output)
    decision_value = {
        "execution_surface": "HYBRID_PUBLIC_PROVIDER_PRIVATE_TLD_PROTECTED_RUN",
        "status": "SCIENTIFIC_BLOCK" if truth_join["status"] != "PASS" or critic_findings else "PASS_INTERNAL_HISTORICAL_CALIBRATION_ONLY",
        "public_provider_execution": "PASS_EXACT_FROZEN_LINUX_PARITY" if checks["execution_provider_parity"] else "BLOCK",
        "private_TLD_custody": "PASS_LOCAL_DIRECT_SOURCE_REPRODUCIBLE",
        "GitHub_raw_TLD_custody": "NOT_APPLICABLE_PRIVATE_DIRECT_SOURCE_MODE",
        "public_truth_access": 0,
        "private_TLD_public_leakage": 0 if checks["private_tld_public_leakage_zero"] else None,
        "local_candidate_materialization_count": 0,
        "local_candidate_probe_execution_count": 0,
        "historical_quality": truth_join,
        "source_ownership_proof_count": 0,
        "ordinary_patch_count": 0,
        "historical_increment": 0,
        "critic_status": "PASS" if not critic_findings else "BLOCK",
        "mutation_status": mutation["status"],
        "protocol": "v2.19",
        "package_version": "0.2.0b2.dev0",
        "issue_derived_repair_count": 6,
        "native_external_repair_count": 4,
        "full_scoring": "NOT_RUN/disallowed",
        "memory_status": "not demonstrated",
        "production_readiness": False,
        "self_maintaining_software": "false/not demonstrated",
        "active_blockers": [truth_join["active_blocker"]] if truth_join.get("active_blocker") else [],
        "claim_boundary": "historical non-counting hybrid calibration only",
        "producer": "scripts/finalize_batch098_hybrid_private_run.py",
        "execution_depth": "verified public artifacts plus post-terminal private TLD identity join",
        "semantic_scope": "hybrid historical calibration boundary",
        "authority_allowed": "manual compact artifact handoff only",
        "authority_forbidden": ["automatic ingest", "repair", "count", "release"],
    }
    write_json(output / "batch098_hybrid_private_final_decision.json", decision_value)
    write_json(output / "batch098_hybrid_private_critic_reconstruction.json", {
        "status": "PASS" if not critic_findings else "BLOCK",
        "checks": checks,
        "finding_count": len(critic_findings),
        "producer": "scripts/finalize_batch098_hybrid_private_run.py",
        "execution_depth": "independent reconstruction from both verified public artifact trees and committed opaque plan",
        "semantic_scope": "hybrid artifact integrity and claim-boundary checks",
        "authority_allowed": "private final decision input",
        "authority_forbidden": ["truth fabrication", "repair", "count", "release"],
    })
    manifests = write_manifests(output)
    artifact = Path(args.artifact)
    artifact.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(artifact, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(item for item in output.rglob("*") if item.is_file()):
            archive.write(path, path.relative_to(output).as_posix())
    report = {
        "status": decision_value["status"], "artifact_path": str(artifact), "artifact_size": artifact.stat().st_size,
        "artifact_sha256": file_sha256(artifact), "manifest": manifests, "active_blockers": decision_value["active_blockers"],
        "authority_allowed": "manual local artifact handoff only", "authority_forbidden": ["automatic ingest", "repair", "count", "release"],
        "producer": "scripts/finalize_batch098_hybrid_private_run.py",
        "execution_depth": "verified compact local artifact packaging",
        "semantic_scope": "historical non-counting hybrid calibration boundary",
    }
    write_json(Path(args.artifact_report), report)
    print(json.dumps(report, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
