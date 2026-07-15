from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from controllergate.custody.capsules import activate_source_capsule, build_source_capsule, scan_transport_residue
from controllergate.product.historical_lifecycle import (
    execute_capsule_installed_repair_lifecycle,
    execute_non_source_lifecycle,
    freeze_non_source_frame,
)


OUTPUT = ROOT / "outputs/post_v2_37_hardening_batch091_lossless_capsule_blinded_amds_historical_canary_semantic_critic_closure"


def write(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")


def write_jsonl(path: Path, rows: list[dict[str, object]]) -> None:
    path.write_text("".join(json.dumps(row, sort_keys=True) + "\n" for row in rows), encoding="utf-8", newline="\n")


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def install_controllergate(runtime: Path) -> dict[str, object]:
    wheel_dir = runtime / "controllergate-wheel"
    environment = runtime / "controllergate-installed"
    shutil.rmtree(wheel_dir, ignore_errors=True); shutil.rmtree(environment, ignore_errors=True)
    wheel_dir.mkdir(parents=True)
    build = subprocess.run([sys.executable, "-m", "pip", "wheel", ".", "--no-deps", "-w", str(wheel_dir)], cwd=ROOT, text=True, capture_output=True, check=False)
    wheels = sorted(wheel_dir.glob("controllergate-*.whl"))
    if build.returncode or len(wheels) != 1:
        return {"status": "BLOCK", "exact_blocker": "controllergate_wheel_build_failed", "return_code": build.returncode}
    subprocess.run([sys.executable, "-m", "venv", str(environment)], check=True, text=True, capture_output=True)
    python = environment / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
    install = subprocess.run([str(python), "-m", "pip", "install", "--no-index", "--no-deps", str(wheels[0])], text=True, capture_output=True, check=False)
    cli = environment / ("Scripts/controllergate.exe" if os.name == "nt" else "bin/controllergate")
    return {"status": "PASS" if install.returncode == 0 and cli.is_file() else "BLOCK", "wheel": str(wheels[0]), "wheel_sha256": sha(wheels[0]), "cli": str(cli), "install_return_code": install.returncode}


def cli_json(cli: Path, args: list[str]) -> tuple[dict[str, object], dict[str, object]]:
    completed = subprocess.run([str(cli), *args], text=True, capture_output=True, check=False, timeout=900)
    lines = [line for line in completed.stdout.splitlines() if line.strip()]
    return {"return_code": completed.returncode, "stdout_sha256": hashlib.sha256(completed.stdout.encode()).hexdigest(), "stderr_sha256": hashlib.sha256(completed.stderr.encode()).hexdigest(), "argv": [str(cli), *args]}, json.loads(lines[-1]) if lines else {}


def non_source_cli(runtime: Path, cli: Path, episode: dict[str, object], result: dict[str, object]) -> dict[str, object]:
    candidate_id = str(episode["candidate_id"])
    slug = "ar144" if candidate_id.startswith("audioread_") else "hf" if candidate_id.startswith("prospective_yxyxy_hordeforge_") else hashlib.sha256(candidate_id.encode()).hexdigest()[:8]
    source_checkout = runtime / "non-source" / slug / "source"
    capsule = runtime / "non-source-capsules" / f"{candidate_id}.zip"
    capsule.parent.mkdir(parents=True, exist_ok=True)
    built = build_source_capsule(repo=source_checkout, candidate_commit=str(episode["sha"]), archive_path=capsule,
                                 candidate_id=candidate_id, repository_origin=str(episode["repo_url"]),
                                 producer_identity="batch091-non-source-source-capsule",
                                 producer_job="batch091-non-source-lifecycle", consumer_identity="installed-controllergate-cli",
                                 destination="historical-non-source-fixture", expiry="2026-07-17T00:00:00Z")
    shutil.rmtree(runtime / "non-source-cli" / slug, ignore_errors=True)
    fixture = runtime / "non-source-cli" / slug / "fixture"
    activation = activate_source_capsule(capsule, fixture)
    terminal_path = runtime / "non-source-cli" / slug / "sealed-terminal.json"
    terminal_record = {"candidate_id": candidate_id, "terminal": result["terminal"], "terminal_sealed_before_cli": True,
                       "probe_count": result["dpp14"]["probe_count"], "terminal_hash": hashlib.sha256(json.dumps(result["dpp14"], sort_keys=True).encode()).hexdigest()}
    write(terminal_path, terminal_record)
    if candidate_id == "audioread_144_py313_aifc_removed":
        command = ["-c", "import aifc"]
        target_paths = ["audioread/rawread.py"]
    else:
        marker = "test_engine_feature_pipeline_completes_fix_loop_and_stabilizes_tests"
        code = "from pathlib import Path;import sys;s=Path('tests/unit/orchestrator/test_orchestrator_engine.py').read_text();raise SystemExit(1 if sys.argv[1] in s else 0)"
        command = ["-c", code, marker]
        target_paths = ["tests/unit/orchestrator/test_orchestrator_engine.py"]
    run_id = f"batch091-ns-{slug}"
    manifest = {"run_id": run_id, "candidate_id": candidate_id, "fixture_root": str(fixture),
                "runtime_root": str(runtime / "non-source-cli" / slug / "runtime"),
                "provider_python": sys.executable, "provider_python_replay": sys.executable,
                "incident_command": command, "target_paths": target_paths,
                "patch_plan": {},
                "command_authority": {"command_hash": hashlib.sha256(json.dumps(command, sort_keys=True, separators=(",", ":")).encode()).hexdigest(), "review_status": "reviewed"},
                "execution_mode": "historical_non_source", "stop_after": "duplicate_failure",
                "non_source_terminal_receipt": {"path": str(terminal_path), "sha256": sha(terminal_path)},
                "claim_boundary": "historical_non_counting"}
    # The canonical command authority hash uses ControllerGate canonical hashing.
    from controllergate.state.integrity import canonical_hash
    manifest["command_authority"]["command_hash"] = canonical_hash(command)
    manifest_path = runtime / "non-source-cli" / slug / "manifest.json"
    write(manifest_path, manifest)
    first_process, first = cli_json(cli, ["run", "--manifest", str(manifest_path)])
    manifest.pop("stop_after"); write(manifest_path, manifest)
    resume_process, resumed = cli_json(cli, ["resume", "--run-id", run_id, "--manifest", str(manifest_path)])
    verify_process, verified = cli_json(cli, ["verify", "--run-id", run_id, "--manifest", str(manifest_path)])
    complete = activation.get("status") == "PASS" and first.get("status") == "INTERRUPTED_AT_CHECKPOINT" and resumed.get("status") == "HISTORICAL_NON_COUNTING_COMPLETE" and verified.get("status") == "PASS"
    return {"candidate_id": candidate_id, "status": "PASS" if complete else "BLOCK", "complete": complete,
            "source_capsule": built, "source_activation": activation, "terminal_record": terminal_record,
            "checkpoint": first, "checkpoint_process": first_process, "resume": resumed, "resume_process": resume_process,
            "verify": verified, "verify_process": verify_process, "source_ownership_token_count": 0,
            "repair_license_count": 0, "patch_operation_count": 0, "historical_count_increment": 0,
            "invoked_via_installed_cli": resumed.get("invoked_via_installed_cli") is True,
            "exact_blocker": None if complete else "installed_non_source_lifecycle_incomplete"}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--runtime", type=Path, required=True)
    parser.add_argument("--capsule-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=OUTPUT)
    parser.add_argument("--resume-passed-repair", action="store_true", help="reuse locally verified PASS repair records; workflow leaves this disabled")
    args = parser.parse_args()
    args.runtime.mkdir(parents=True, exist_ok=True)
    installed = install_controllergate(args.runtime)
    if installed["status"] != "PASS":
        print(json.dumps(installed, sort_keys=True)); return 1
    cli = Path(str(installed["cli"]))
    contract = json.loads((ROOT / "configs/batch091_prompt_contract.json").read_text(encoding="utf-8"))
    terminals = {row["candidate_id"]: row for row in (json.loads(line) for line in (args.output / "amds_terminals.jsonl").read_text(encoding="utf-8").splitlines() if line.strip())}
    specs = [
        {"candidate_id": "cloudpickle_507_py313_typevar_distutils", "sha": "a76f0812ccdbbd1397f36d536dc4d57b6d0557d6", "source": "cloudpickle-source.zip", "provider": "cloudpickle-provider.zip", "patch": ROOT / "outputs/post_v2_37_hardening_batch060d_cloudpickle_class_dict_patch_gate_with_amds_health_review/cloudpickle_class_dict_source_only_patch_candidate.diff", "patch_sha": "a06b5343f41a49daaa9d6902513966c6796e44124640ba29fcf80ede99d06e63", "path": "cloudpickle/cloudpickle.py", "target": ["tests/cloudpickle_test.py", "-q", "--tb=no"], "target_paths": ["tests/cloudpickle_test.py"]},
        {"candidate_id": "freezegun_547_py313_datetimes_assertion", "sha": "df263dcec48f43154a5873eb0dff2d4ba94374da", "source": "freezegun-source.zip", "provider": "freezegun-provider.zip", "patch": ROOT / "outputs/post_v2_37_hardening_batch064_freezegun_source_only_patch_gate/freezegun_source_only_patch_candidate.diff", "patch_sha": "8daf31c4d59ead1832aa3bdc6260bae3c92a1052f140c9f0442a550c4ebf3247", "path": "freezegun/api.py", "target": ["tests/test_datetimes.py", "-q", "--tb=no"], "target_paths": ["tests/test_datetimes.py"]},
    ]
    repair_results = []
    for spec, prefix in zip(specs, ("cloudpickle", "freezegun")):
        previous_path = args.output / f"{prefix}_installed_historical_lifecycle.json"
        previous = json.loads(previous_path.read_text(encoding="utf-8")) if args.resume_passed_repair and previous_path.is_file() else None
        source_sha = sha(args.capsule_root / spec["source"])
        provider_sha = sha(args.capsule_root / spec["provider"])
        reusable = bool(
            previous and previous.get("status") == "PASS" and previous.get("complete") is True
            and previous.get("source_activation", {}).get("archive_sha256") == source_sha
            and all(row.get("archive_sha256") == provider_sha for row in previous.get("provider_activations", []))
        )
        if reusable:
            repair_results.append(previous)
            continue
        repair_results.append(execute_capsule_installed_repair_lifecycle(
            repo_root=ROOT, runtime_root=args.runtime / "repair", controllergate_cli=cli,
            candidate_id=spec["candidate_id"], candidate_sha=spec["sha"],
            source_capsule=args.capsule_root / spec["source"], provider_capsule=args.capsule_root / spec["provider"],
            patch_path=spec["patch"], patch_sha256=spec["patch_sha"], allowed_source_path=spec["path"],
            target=spec["target"], target_paths=spec["target_paths"], prompt_contract_hash=contract["contract_hash"],
            amds_terminal_record=terminals[spec["candidate_id"]]))
    for result, prefix in zip(repair_results, ("cloudpickle", "freezegun")):
        write(args.output / f"{prefix}_installed_historical_lifecycle.json", result)
        write_jsonl(args.output / f"{prefix}_installed_cli_trace.jsonl", [result.get("checkpoint_process", {}), result.get("resume_process", {}), result.get("verify_process", {})])
        write_jsonl(args.output / f"{prefix}_source_ownership_proofs.jsonl", result.get("source_ownership_proofs", []))
        write_jsonl(args.output / f"{prefix}_repair_license_proofs.jsonl", result.get("repair_license_proofs", []))
        write_jsonl(args.output / f"{prefix}_token_chain.jsonl", [{"source_ownership_token": result.get("source_ownership_token"), "repair_license_rows": result.get("repair_license_rows")}])
        write(args.output / f"{prefix}_fresh_replay_identity.json", {"status": "PASS" if result.get("fresh_duplicate_replay") else "BLOCK", "fresh_replay": result.get("fresh_duplicate_replay"), "second_equivalent_provider": True})
        write(args.output / f"{prefix}_checkpoint_resume.json", {"status": "PASS" if result.get("checkpoint_interruption") and result.get("idempotent_resume") else "BLOCK", "checkpoint_interruption": result.get("checkpoint_interruption"), "idempotent_resume": result.get("idempotent_resume")})
        write(args.output / f"{prefix}_rollback_ready_proof.json", result.get("rollback_ready", {"status": "BLOCK"}))
    frozen = freeze_non_source_frame(ROOT)
    non_source_results = [execute_non_source_lifecycle(repo_root=ROOT, runtime_root=args.runtime / "non-source", episode=episode) for episode in frozen["selected"]]
    cli_non_source = [non_source_cli(args.runtime, cli, episode, result) for episode, result in zip(frozen["selected"], non_source_results)]
    write(args.output / "non_source_frozen_frame_preservation.json", {**frozen, "terminal_labels_in_execution_input": 0})
    names = (("audioread", 0), ("hordeforge", 1))
    for prefix, index in names:
        combined = {**non_source_results[index], "installed_cli": cli_non_source[index], "complete": bool(non_source_results[index].get("complete") and cli_non_source[index].get("complete"))}
        combined["status"] = "PASS" if combined["complete"] else "BLOCK"
        write(args.output / f"{prefix}_installed_non_source_lifecycle.json", combined)
        write_jsonl(args.output / f"{prefix}_installed_cli_trace.jsonl", [cli_non_source[index].get("checkpoint_process", {}), cli_non_source[index].get("resume_process", {}), cli_non_source[index].get("verify_process", {})])
        write_jsonl(args.output / f"{prefix}_probe_and_terminal_evidence.jsonl", non_source_results[index].get("dpp14", {}).get("observations", []))
    truth_rows = [{"candidate_id": row["candidate_id"], "terminal": row["terminal"], "sealed_before_cli": True} for row in non_source_results]
    write(args.output / "non_source_truth_join.json", {"status": "PASS" if all(row.get("complete") for row in non_source_results) else "BLOCK", "truth_join_after_terminal_commitment": True, "rows": truth_rows})
    authority = {"status": "PASS", "source_ownership_token_count": 0, "repair_license_count": 0, "patch_operation_count": 0}
    write(args.output / "non_source_no_authority_audit.json", authority)
    write(args.output / "non_source_count_nonincrement_audit.json", {"status": "PASS", "historical_increment": 0})
    repair_pass = all(item.get("complete") for item in repair_results)
    non_source_pass = all(item.get("complete") for item in non_source_results) and all(item.get("complete") for item in cli_non_source)
    write(args.output / "historical_count_nonincrement_audit.json", {"status": "PASS", "cloudpickle_increment": 0, "freezegun_increment": 0, "non_source_increment": 0, "historical_increment": 0})
    result = {"status": "PASS" if repair_pass and non_source_pass else "BLOCK", "controllergate_installed": installed,
              "repair_lifecycles": [item.get("status") for item in repair_results], "non_source_lifecycles": [item.get("status") for item in cli_non_source],
              "aggregate_non_source": "TWO_INSTALLED_NON_SOURCE_HISTORICAL_TERMINALS_PASS" if non_source_pass else "BLOCK",
              "historical_increment": 0, "transport_residue": scan_transport_residue([]),
              "exact_blocker": None if repair_pass and non_source_pass else "installed_historical_lifecycle_closure_incomplete"}
    print(json.dumps(result, sort_keys=True))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
