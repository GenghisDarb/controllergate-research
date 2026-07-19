from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from controllergate.amds.real_depth_experiments_v2 import ARCHITECTURES, BASELINES, execute_experiment, score_after_truth_join
from controllergate.amds.stage_runtime_v7 import run_dpp14
from controllergate.evidence.roles_v2 import produce_roles, role_quality_gate, verify_role_receipts
from controllergate.evidence.source_ownership_v2 import produce_source_ownership_stages, verify_source_ownership_stages


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n" for row in rows), encoding="utf-8", newline="\n")


def rows(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def normalize_candidates(source: Path, output: Path) -> dict:
    found = sorted(source.rglob("candidate_lane_result_v2.json"))
    candidates = []
    for result_path in found:
        result = json.loads(result_path.read_text(encoding="utf-8"))
        candidate_id = result["candidate_id"]
        destination = output / candidate_id
        if destination.exists():
            raise ValueError(f"duplicate candidate evidence: {candidate_id}")
        shutil.copytree(result_path.parent, destination)
        candidates.append(candidate_id)
    value = {"status": "PASS" if len(candidates) == 8 else "BLOCK", "candidate_count": len(candidates), "candidate_ids": candidates}
    write_json(output / "cohort_join.json", value)
    return value


def incident_verify(source: Path, output: Path) -> dict:
    values = []
    for path in sorted(source.glob("*/candidate_lane_result_v2.json")):
        value = json.loads(path.read_text(encoding="utf-8"))
        incident_path = path.parent / "typed_incident_verification.json"
        incident = json.loads(incident_path.read_text(encoding="utf-8"))
        embedded = value.get("typed_incident", {})
        incident_status = incident.get("status")
        independently_reopened = incident == embedded
        explicit_result = incident_status in {"PASS", "BLOCK"} and bool(
            incident.get("verification_receipt") or incident.get("reasons")
        )
        verification_status = "PASS" if independently_reopened and explicit_result else "BLOCK"
        receipt_payload = {
            "candidate_id": value["candidate_id"],
            "incident_file_sha256": hashlib.sha256(incident_path.read_bytes()).hexdigest(),
            "embedded_incident_sha256": hashlib.sha256(json.dumps(embedded, sort_keys=True, separators=(",", ":")).encode()).hexdigest(),
            "incident_status": incident_status,
            "independently_reopened": independently_reopened,
            "verification_status": verification_status,
        }
        values.append({
            **receipt_payload,
            "status": verification_status,
            "typed_incident_materialized": incident.get("typed_incident_materialized") is True,
            "scientific_block_preserved": incident_status == "BLOCK",
            "verification_receipt": hashlib.sha256(json.dumps(receipt_payload, sort_keys=True, separators=(",", ":")).encode()).hexdigest(),
            "structured_product_parents": incident.get("structured_product_parents", []),
            "producer": "scripts.batch098_workflow_stage.incident_verify",
            "authority_allowed": "incident verification execution custody",
            "authority_forbidden": ["incident materialization from blocked evidence", "terminal", "repair", "count", "release"],
        })
    write_jsonl(output / "incident_verification.jsonl", values)
    verification_pass = len(values) == 8 and all(row["status"] == "PASS" for row in values)
    result = {
        "status": "PASS_VERIFICATION_EXECUTED" if verification_pass else "BLOCK",
        "count": len(values),
        "materialized_count": sum(row["typed_incident_materialized"] for row in values),
        "scientific_block_count": sum(row["scientific_block_preserved"] for row in values),
        "authority_forbidden": ["incident PASS aggregation", "terminal", "repair", "count", "release"],
    }
    write_json(output / "incident_verification_summary.json", result)
    return result


def role_produce(source: Path, output: Path) -> dict:
    produced = []
    for path in sorted(source.glob("*/candidate_lane_result_v2.json")):
        candidate = json.loads(path.read_text(encoding="utf-8"))
        candidate["neutral_observation"] = json.loads((path.parent / "neutral_observation_v2.json").read_text(encoding="utf-8"))
        produced.extend(produce_roles(candidate, preserve_blocked=True))
    write_jsonl(output / "role_producers.jsonl", produced)
    blocked = sum(row.get("status") == "BLOCK" for row in produced)
    return {"status": "PASS_EXECUTION_WITH_SCIENTIFIC_BLOCKS" if len(produced) == 80 else "BLOCK", "count": len(produced), "blocked_role_count": blocked}


def role_verify(source: Path, output: Path) -> dict:
    produced = rows(next(source.rglob("role_producers.jsonl")))
    verified = verify_role_receipts(produced)
    quality = role_quality_gate(produced, verified, 8)
    write_jsonl(output / "role_verifiers.jsonl", verified)
    write_json(output / "role_quality.json", quality)
    return {
        "status": "PASS_EXECUTION_WITH_SCIENTIFIC_BLOCKS" if len(produced) == len(verified) == 80 else "BLOCK",
        "role_quality_status": quality["status"],
        "blocked_role_count": sum(row.get("status") == "BLOCK" for row in verified),
        "quality": quality,
    }


def frame_verify(source: Path, output: Path) -> dict:
    values = []
    for path in sorted(source.rglob("topology_compiled_decision_frame_v3.json")):
        frame = json.loads(path.read_text(encoding="utf-8"))
        probes = frame.get("probes", [])
        values.append({"candidate_id": frame.get("candidate_id"), "status": "PASS" if probes and all(row.get("partition_rule") and row.get("exact_argv") for row in probes) else "BLOCK", "probe_count": len(probes), "frame_hash": frame.get("frame_hash")})
    result = {"status": "PASS" if len(values) == 8 and all(row["status"] == "PASS" for row in values) else "BLOCK", "frames": values}
    write_json(output / "independent_frame_verification.json", result)
    return result


def dpp_candidate(frame_path: Path, output: Path) -> dict:
    frame = json.loads(frame_path.read_text(encoding="utf-8"))
    terminal, produced, verified = run_dpp14({"candidate_id": frame["candidate_id"], "run_id": frame["run_id"], "frame_id": frame["frame_id"], "topology_probes": frame["probes"], "topology_constraints": frame.get("constraints", ())})
    write_json(output / "terminal.json", {key: terminal.get(key) for key in ("candidate_id", "terminal", "terminal_writer", "legal_probe_exhaustion_receipt", "patch_authority", "verified_observation_count", "backtrack_count")})
    write_jsonl(output / "stage_producers.jsonl", produced)
    write_jsonl(output / "stage_verifiers.jsonl", verified)
    write_jsonl(output / "probe_executions.jsonl", terminal.get("probe_executions", []))
    write_jsonl(output / "verified_causal_facts.jsonl", terminal.get("verified_causal_facts", []))
    return {"status": "PASS", "terminal": terminal["terminal"], "executed_probes": len(terminal.get("probe_executions", []))}


def experiment(frame_path: Path, experiment_id: str, output: Path) -> dict:
    frame = json.loads(frame_path.read_text(encoding="utf-8"))
    family = ARCHITECTURES if experiment_id in ARCHITECTURES else BASELINES
    return execute_experiment(experiment_id=experiment_id, components=family[experiment_id], probe=frame["probes"][0], output=output)


def truth_custody(output: Path) -> dict:
    value = {"status": "SEALED_WITHOUT_ELIGIBLE_GOLD_OUTCOMES", "expected_by_experiment": {}, "seal": hashlib.sha256(b"Batch098 ordinary evidence-only truth custody").hexdigest(), "available_to_candidate_jobs": False, "available_to_builder_jobs": False, "release_after_terminal_seal_only": True}
    write_json(output / "sealed_truth.json", value)
    return value


def truth_join(experiments: Path, truth: Path, output: Path) -> dict:
    results = [json.loads(path.read_text(encoding="utf-8")) for path in experiments.rglob("experiment_result.json")]
    sealed = json.loads(next(truth.rglob("sealed_truth.json")).read_text(encoding="utf-8"))
    value = score_after_truth_join(results, sealed)
    write_json(output / "truth_separated_score.json", value)
    return value


def source_ownership(candidate_path: Path, terminal_path: Path, topology: Path, output: Path, verify: bool) -> dict:
    if verify:
        produced = rows(next(candidate_path.rglob("source_ownership_producers.jsonl")))
        value = verify_source_ownership_stages(produced)
        write_json(output / "source_ownership_verification.json", value)
        return value
    candidate = json.loads(candidate_path.read_text(encoding="utf-8"))
    terminal = json.loads(terminal_path.read_text(encoding="utf-8"))
    produced = produce_source_ownership_stages(candidate, terminal, topology)
    write_jsonl(output / "source_ownership_producers.jsonl", produced)
    return {"status": "PASS" if produced else "BLOCK", "count": len(produced)}


def seal_tree(source: Path, output: Path) -> dict:
    output.mkdir(parents=True, exist_ok=True)
    manifest = {}
    for path in sorted(source.rglob("*")):
        if path.is_file():
            manifest[path.relative_to(source).as_posix()] = hashlib.sha256(path.read_bytes()).hexdigest()
    value = {"status": "PASS", "file_count": len(manifest), "files": manifest, "tree_seal": hashlib.sha256(json.dumps(manifest, sort_keys=True).encode()).hexdigest()}
    write_json(output / "complete_raw_tree_manifest.json", value)
    return value


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=("normalize-candidates", "incident-verify", "role-produce", "role-verify", "frame-verify", "dpp-candidate", "experiment", "truth-custody", "truth-join", "source-ownership-produce", "source-ownership-verify", "seal-tree"))
    parser.add_argument("--source"); parser.add_argument("--output", required=True); parser.add_argument("--frame"); parser.add_argument("--experiment-id"); parser.add_argument("--truth"); parser.add_argument("--terminal"); parser.add_argument("--topology")
    args = parser.parse_args(); output = Path(args.output)
    if args.action == "normalize-candidates": result = normalize_candidates(Path(args.source), output)
    elif args.action == "incident-verify": result = incident_verify(Path(args.source), output)
    elif args.action == "role-produce": result = role_produce(Path(args.source), output)
    elif args.action == "role-verify": result = role_verify(Path(args.source), output)
    elif args.action == "frame-verify": result = frame_verify(Path(args.source), output)
    elif args.action == "dpp-candidate": result = dpp_candidate(Path(args.frame), output)
    elif args.action == "experiment": result = experiment(Path(args.frame), str(args.experiment_id), output)
    elif args.action == "truth-custody": result = truth_custody(output)
    elif args.action == "truth-join": result = truth_join(Path(args.source), Path(args.truth), output)
    elif args.action == "source-ownership-produce": result = source_ownership(Path(args.source), Path(args.terminal), Path(args.topology), output, False)
    elif args.action == "source-ownership-verify": result = source_ownership(Path(args.source), Path(args.terminal or args.source), Path(args.topology or args.source), output, True)
    else: result = seal_tree(Path(args.source), output)
    print(json.dumps(result, sort_keys=True))
    return 0 if result.get("status") not in {"BLOCK", "FAIL"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
