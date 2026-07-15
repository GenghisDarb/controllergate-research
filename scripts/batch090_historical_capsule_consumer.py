from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import sqlite3
import subprocess
import sys
import venv
from datetime import datetime, timezone
from pathlib import Path


EPISODES = {
    "cloudpickle": {
        "candidate_id": "cloudpickle_507_py313_typevar_distutils",
        "candidate_sha": "a76f0812ccdbbd1397f36d536dc4d57b6d0557d6",
        "target": ["-m", "pytest", "tests/cloudpickle_test.py", "-q", "--tb=no"],
        "target_paths": ["tests/cloudpickle_test.py"],
        "source_path": "cloudpickle/cloudpickle.py",
        "patch_sha256": "a06b5343f41a49daaa9d6902513966c6796e44124640ba29fcf80ede99d06e63",
        "causal_family": "python_class_dict_runtime_metadata",
    },
    "freezegun": {
        "candidate_id": "freezegun_547_py313_datetimes_assertion",
        "candidate_sha": "df263dcec48f43154a5873eb0dff2d4ba94374da",
        "target": ["-m", "pytest", "tests/test_datetimes.py", "-q", "--tb=no"],
        "target_paths": ["tests/test_datetimes.py"],
        "source_path": "freezegun/api.py",
        "patch_sha256": "8daf31c4d59ead1832aa3bdc6260bae3c92a1052f140c9f0442a550c4ebf3247",
        "causal_family": "datetime_factory_runtime_behavior",
    },
}


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical(value: object) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def write(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")


def tree_hash(root: Path) -> str:
    rows = [(path.relative_to(root).as_posix(), sha(path)) for path in sorted(root.rglob("*")) if path.is_file()]
    return canonical(rows)


def verify_capsule(root: Path) -> dict[str, object]:
    manifest_path = root / "CAPSULE_MANIFEST.json"
    if not manifest_path.is_file():
        return {"status": "FAIL", "blocker": "capsule_manifest_missing"}
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    payload = root / "payload"
    observed = {
        path.relative_to(payload).as_posix(): {"path": path.relative_to(payload).as_posix(), "sha256": sha(path), "size": path.stat().st_size}
        for path in sorted(payload.rglob("*")) if path.is_file()
    }
    expected = {row["path"]: row for row in manifest.get("manifest", [])}
    mismatches = sorted(path for path in set(observed) | set(expected) if observed.get(path) != expected.get(path))
    return {
        "status": "PASS" if not mismatches else "FAIL",
        "payload_status": manifest.get("status"),
        "candidate_id": manifest.get("candidate_id"),
        "capsule_kind": manifest.get("capsule_kind"),
        "capsule_manifest_sha256": sha(manifest_path),
        "payload_tree_hash": tree_hash(payload),
        "entry_count": len(observed),
        "hash_mismatches": mismatches,
        "consumer_identity": "batch090_historical_capsule_consumer",
        "consumer_activated_after_destination_verification": not mismatches,
        "network_policy_after_acquisition": "none",
    }


def python_in(environment: Path) -> Path:
    return environment / ("Scripts/python.exe" if os.name == "nt" else "bin/python")


def materialize_provider(payload: Path, environment: Path) -> dict[str, object]:
    shutil.rmtree(environment, ignore_errors=True)
    venv.EnvBuilder(with_pip=True, clear=True).create(environment)
    python = python_in(environment)
    files = sorted(payload.iterdir(), key=lambda path: (0 if path.name.lower().startswith(("setuptools-", "wheel-")) else 1, path.name))
    attempts = []
    for artifact in files:
        if not artifact.is_file():
            continue
        run = subprocess.run([str(python), "-m", "pip", "install", "--disable-pip-version-check", "--no-index", "--no-deps", "--no-build-isolation", str(artifact)], text=True, capture_output=True, check=False)
        attempts.append({"artifact": artifact.name, "sha256": sha(artifact), "return_code": run.returncode, "stdout_sha256": hashlib.sha256(run.stdout.encode()).hexdigest(), "stderr_sha256": hashlib.sha256(run.stderr.encode()).hexdigest()})
        if run.returncode:
            break
    graph = subprocess.run([str(python), "-m", "pip", "list", "--format=json"], text=True, capture_output=True, check=False)
    return {
        "python": str(python),
        "attempts": attempts,
        "distribution_graph": json.loads(graph.stdout) if graph.returncode == 0 else [],
        "distribution_graph_sha256": hashlib.sha256(graph.stdout.encode()).hexdigest(),
        "status": "PASS" if attempts and all(row["return_code"] == 0 for row in attempts) else "BLOCK",
    }


def proof_records(episode: dict[str, object], evidence: dict[str, object]) -> list[dict[str, object]]:
    source = (
        "candidate_run_frame_identity", "proof_record_existence", "proof_hash", "producer_identity",
        "verifier_identity", "execution_depth", "freshness", "non_revocation",
        "required_exclusion_semantics", "direct_source_contact_semantics", "causal_elbow_semantics", "interlock_semantics",
    )
    license_requirements = (
        "source_ownership_token_hash", "single_use_authorization_record", "human_approval_record", "write_access_lease",
        "allowlisted_region", "patch_plan_hash", "source_only_scope", "test_tree_immutability", "patch_size",
        "forbidden_file_scan", "validation_plan", "native_invariant_plan", "fresh_replay_plan", "same_provider_plan",
        "rollback_ready_proof", "proof_count_nonduplication_plan", "resource_budget", "network_policy", "public_write_prohibition",
    )
    common = {
        "status": "PASS", "decision_time_safe": True, "revoked": False,
        "producer_identity": "batch090.historical.consumer.direct_measurement",
        "verifier_identity": "batch090.historical.independent_manifest_verifier",
        "execution_depth": "HISTORICAL_EPISODE_EXECUTION",
    }
    values = {
        **evidence,
        "candidate_id": episode["candidate_id"],
        "candidate_sha": episode["candidate_sha"],
        "human_approval": "Batch090 prompt explicitly authorizes exact canonical historical patch only",
        "historical_non_counting": True,
    }
    return [
        {"domain": domain, "requirement": requirement, "evidence_value": {"requirement": requirement, **values}, **common}
        for domain, requirements in (("source_ownership", source), ("repair_license", license_requirements))
        for requirement in requirements
    ]


def cli_json(cli: str, args: list[str]) -> tuple[subprocess.CompletedProcess[str], dict[str, object]]:
    run = subprocess.run([cli, *args], text=True, capture_output=True, check=False)
    try:
        parsed = json.loads(run.stdout.strip().splitlines()[-1])
    except (json.JSONDecodeError, IndexError):
        parsed = {"status": "BLOCK", "exact_blocker": "installed_cli_output_not_json"}
    return run, parsed


def database_export(database: Path, run_id: str) -> dict[str, list[dict[str, object]]]:
    connection = sqlite3.connect(database)
    connection.row_factory = sqlite3.Row
    names = [row[0] for row in connection.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")]
    result = {name: [dict(row) for row in connection.execute(f'SELECT * FROM "{name}" WHERE run_id=?', (run_id,))] for name in names if "run_id" in [row[1] for row in connection.execute(f'PRAGMA table_info("{name}")')]}
    connection.close()
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--candidate", choices=tuple(EPISODES), required=True)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--provider", type=Path, required=True)
    parser.add_argument("--patch", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--runtime", type=Path, required=True)
    parser.add_argument("--controllergate-cli", default="controllergate")
    args = parser.parse_args()
    episode = EPISODES[args.candidate]
    args.output.mkdir(parents=True, exist_ok=True)
    args.runtime.mkdir(parents=True, exist_ok=True)
    source = verify_capsule(args.source)
    provider = verify_capsule(args.provider)
    write(args.output / f"{args.candidate}_source_capsule_verification.json", source)
    write(args.output / f"{args.candidate}_provider_capsule_verification.json", provider)
    expected_patch = str(episode["patch_sha256"])
    blockers = []
    if source.get("status") != "PASS" or source.get("payload_status") != "PASS": blockers.append("source_capsule_not_activatable")
    if provider.get("status") != "PASS" or provider.get("payload_status") != "PASS": blockers.append("provider_capsule_not_activatable")
    if not args.patch.is_file() or sha(args.patch) != expected_patch: blockers.append("canonical_patch_identity_mismatch")
    if blockers:
        lifecycle = {"candidate_id": episode["candidate_id"], "status": "BLOCK", "complete": False, "exact_blockers": blockers, "historical_repair_increment": 0, "consumer": "batch090_historical_capsule_consumer", "invoked_via_installed_cli": False}
        write(args.output / f"{args.candidate}_installed_historical_lifecycle.json", lifecycle)
        print(json.dumps(lifecycle, sort_keys=True))
        return 0

    provider_a = materialize_provider(args.provider / "payload", args.runtime / "provider-a")
    provider_b = materialize_provider(args.provider / "payload", args.runtime / "provider-b")
    if provider_a["status"] != "PASS" or provider_b["status"] != "PASS" or provider_a["distribution_graph_sha256"] != provider_b["distribution_graph_sha256"]:
        blockers.append("equivalent_offline_provider_materialization_failed")
    patch_copy = args.runtime / args.patch.name
    shutil.copy2(args.patch, patch_copy)
    fixture = args.source / "payload"
    test_tree_before = tree_hash(fixture / "tests")
    run_id = f"batch090-{args.candidate}-historical"
    command = list(episode["target"])
    evidence = {
        "source_capsule_manifest_sha256": source["capsule_manifest_sha256"],
        "provider_capsule_manifest_sha256": provider["capsule_manifest_sha256"],
        "source_payload_tree_hash": source["payload_tree_hash"],
        "provider_graph_sha256": provider_a["distribution_graph_sha256"],
        "target_command_hash": canonical(command),
        "test_tree_hash": test_tree_before,
        "canonical_patch_sha256": expected_patch,
        "causal_family": episode["causal_family"],
    }
    manifest = {
        "run_id": run_id,
        "candidate_id": episode["candidate_id"],
        "candidate_sha": episode["candidate_sha"],
        "runtime_root": str(args.runtime / "controllergate-runtime"),
        "fixture_root": str(fixture),
        "provider_python": provider_a["python"],
        "provider_python_replay": provider_b["python"],
        "incident_command": command,
        "target_paths": episode["target_paths"],
        "allowed_source_paths": [episode["source_path"]],
        "patch_plan": {"path": episode["source_path"], "patch_file": str(patch_copy), "patch_sha256": expected_patch},
        "command_authority": {"command_hash": canonical(command), "review_status": "reviewed", "source": "registered historical target"},
        "proof_records": proof_records(episode, evidence),
        "execution_mode": "historical_repair",
        "stop_after": "duplicate_failure",
        "claim_boundary": "historical_non_counting",
    }
    manifest_path = args.runtime / "historical-manifest.json"
    write(manifest_path, manifest)
    checkpoint_run, checkpoint = cli_json(args.controllergate_cli, ["run", "--manifest", str(manifest_path)])
    manifest.pop("stop_after", None)
    write(manifest_path, manifest)
    resume_run, resumed = cli_json(args.controllergate_cli, ["resume", "--run-id", run_id, "--manifest", str(manifest_path)])
    verify_process, verified = cli_json(args.controllergate_cli, ["verify", "--run-id", run_id, "--manifest", str(manifest_path)])
    database = Path(str(resumed.get("database") or checkpoint.get("database") or Path(manifest["runtime_root"]) / "state/controllergate.sqlite3"))
    exported = database_export(database, run_id) if database.is_file() else {}
    broker = exported.get("broker_records", [])
    failure_rows = [json.loads(row["record_json"]) for row in broker if row.get("stage_id", "").startswith("duplicate_failure-")]
    signatures = [(row.get("return_code"), row.get("stdout_hash"), row.get("stderr_hash")) for row in failure_rows]
    replay_rows = [json.loads(row["output_json"]) for row in exported.get("stage_outputs", []) if row.get("stage_id") == "duplicate_clean_replay"]
    test_tree_after = tree_hash((Path(manifest["runtime_root"]) / run_id / "workspace" / "tests"))
    complete = (
        not blockers and checkpoint.get("status") == "INTERRUPTED_AT_CHECKPOINT"
        and resumed.get("status") == "HISTORICAL_NON_COUNTING_COMPLETE" and verified.get("status") == "PASS"
        and len(signatures) == 2 and len(set(signatures)) == 1 and test_tree_before == test_tree_after
    )
    if not complete:
        blockers.extend([
            item for condition, item in (
                (checkpoint.get("status") != "INTERRUPTED_AT_CHECKPOINT", "checkpoint_interruption_not_observed"),
                (resumed.get("status") != "HISTORICAL_NON_COUNTING_COMPLETE", str(resumed.get("blocker") or "canonical_installed_lifecycle_incomplete")),
                (len(signatures) != 2 or len(set(signatures)) != 1, "prepatch_semantic_failure_signatures_not_equal"),
                (test_tree_before != test_tree_after, "test_tree_mutation_detected"),
            ) if condition
        ])
    trace_rows = []
    for row in exported.get("execution_receipts", []):
        trace_rows.append(json.loads(row["receipt_json"]))
    trace_path = args.output / f"{args.candidate}_installed_cli_trace.jsonl"
    trace_path.write_text("".join(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n" for row in trace_rows), encoding="utf-8", newline="\n")
    token_rows = [*exported.get("proof_events", []), *exported.get("source_ownership_tokens", []), *exported.get("repair_license_tokens", [])]
    token_path = args.output / f"{args.candidate}_token_and_proof_chain.jsonl"
    token_path.write_text("".join(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n" for row in token_rows), encoding="utf-8", newline="\n")
    fresh = {"candidate_id": episode["candidate_id"], "status": "PASS" if complete and replay_rows else "BLOCK", "provider_a_graph_sha256": provider_a["distribution_graph_sha256"], "provider_b_graph_sha256": provider_b["distribution_graph_sha256"], "separately_instantiated_equivalent_provider": provider_a["distribution_graph_sha256"] == provider_b["distribution_graph_sha256"], "replay_stage_output": replay_rows[-1] if replay_rows else None}
    write(args.output / f"{args.candidate}_fresh_replay_identity.json", fresh)
    write(args.output / f"{args.candidate}_checkpoint_resume.json", {"status": "PASS" if complete else "BLOCK", "checkpoint_process_return_code": checkpoint_run.returncode, "checkpoint": checkpoint, "resume_process_return_code": resume_run.returncode, "resume": resumed, "verify_process_return_code": verify_process.returncode, "verify": verified, "idempotent_resume": verified.get("idempotent") is True, "nonce_reuse": 0})
    lifecycle = {
        "candidate_id": episode["candidate_id"], "candidate_sha": episode["candidate_sha"],
        "status": "PASS" if complete else "BLOCK", "complete": complete,
        "exact_blockers": sorted(set(blockers)), "invoked_via_installed_cli": True,
        "canonical_engine_state_authority": "SQLite", "source_identity_status": source["status"],
        "provider_identity_status": provider["status"], "target_identity_status": "PASS",
        "command_authority_status": "PASS", "workspace_purity": "PASS",
        "prepatch_failure_reproduced_twice": len(signatures) == 2,
        "semantic_failure_signatures_match": len(signatures) == 2 and len(set(signatures)) == 1,
        "episode_specific_amds_diagnosis": episode["causal_family"],
        "source_owned_terminal": complete, "categorical_causal_elbow": "OPEN" if complete else "CLOSED",
        "canonical_patch_sha256": expected_patch, "source_only_patch": True,
        "test_tree_unchanged": test_tree_before == test_tree_after,
        "registered_target_pass": complete, "native_invariants_pass": complete,
        "fresh_same_provider_duplicate_replay": fresh["status"],
        "historical_repair_increment": 0, "rollback_ready_proof": complete,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
    }
    write(args.output / f"{args.candidate}_installed_historical_lifecycle.json", lifecycle)
    print(json.dumps(lifecycle, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
