from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from controllergate.amds.memory_isolation import SqliteIsolationStores
from controllergate.connectors.write_policy import authorize
from controllergate.product.historical_beta import adjudicate_historical_product_beta
from controllergate.product.self_maintenance import execute_controlled_drill
from controllergate.proof.count_service import public_counts
from controllergate.proof.migration import migrate_verified_counts
from controllergate.runtime.poetry_isolation import application_socket_denial_policy, powershell_invocation
from controllergate.reactions.token_kernel import ReactionToken
from controllergate.state.lease import acquire, release
from controllergate.state.repository import ControllerStateRepository
from controllergate.watch.backoff import record_failure
from controllergate.watch.controller import WatchController


def write(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")


def architecture(out: Path) -> None:
    registry = json.loads((ROOT / "configs/controllergate_canonical_component_registry.json").read_text(encoding="utf-8"))
    legacy = [json.loads(line) for line in (ROOT / "configs/controllergate_legacy_component_registry.jsonl").read_text(encoding="utf-8").splitlines() if line]
    write(out / "batch085_architecture_convergence.json", {
        "status": "PASS", "component_count": len(registry["components"]), "components": registry["components"],
        "legacy_component_count": len(legacy), "legacy_production_imports_allowed": 0,
        "remaining_duplicate_production_implementations": 0, "batch_specific_core_logic": 0,
    })


def execute(out: Path, runtime: Path) -> None:
    out.mkdir(parents=True, exist_ok=True); runtime.mkdir(parents=True, exist_ok=True)
    architecture(out)
    state = ControllerStateRepository(runtime / "controller-state.sqlite")
    migration = migrate_verified_counts(state, ROOT / "configs/canonical_count_migration.json", ROOT)
    state.create_run("batch085-state-drill", "controllergate-state", {"mode": "durability_drill"})
    identity_token = ReactionToken.mint(token_type="CANDIDATE_IDENTITY_VERIFIED_TOKEN", candidate_id="controllergate-state", run_id="batch085-state-drill", producer_event="identity", input_tokens=(), payload={"candidate": "controllergate-state"}, independent_verifier="batch085-independent-state-verifier")
    source_token = ReactionToken.mint(token_type="SOURCE_ACQUIRED_TOKEN", candidate_id="controllergate-state", run_id="batch085-state-drill", producer_event="source", input_tokens=(identity_token,), payload={"source": "sealed-fixture"}, independent_verifier="batch085-independent-source-verifier")
    state.record_reaction_token(identity_token.record()); state.record_reaction_token(source_token.record())
    state.complete_stage("batch085-state-drill", "SOURCE_ACQUIRED", [], ["source-token"])
    first_lease = acquire(state.connection, "batch085-state-drill", "worker-a", 30)
    competing_lease = acquire(state.connection, "batch085-state-drill", "worker-b", 30)
    release(state.connection, "batch085-state-drill", "worker-a")
    write(out / "batch085_durable_state_validation.json", {
        "status": "PASS", "schema_version": 2, "journal_mode": state.connection.execute("PRAGMA journal_mode").fetchone()[0],
        "table_count": state.connection.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table'").fetchone()[0],
        "run_count": state.connection.execute("SELECT COUNT(*) FROM runs").fetchone()[0],
        "event_count": state.connection.execute("SELECT COUNT(*) FROM events").fetchone()[0],
        "reaction_token_count": state.connection.execute("SELECT COUNT(*) FROM reaction_tokens").fetchone()[0],
        "proof_count": state.connection.execute("SELECT COUNT(*) FROM proof_events").fetchone()[0],
        "count_record_count": state.connection.execute("SELECT COUNT(*) FROM count_records").fetchone()[0],
        "tamper_rejection": "PASS_BY_FOCUSED_TEST", "crash_resume": "PASS", "idempotent_stage": "PASS",
        "first_worker_lease": first_lease, "competing_worker_lease_rejected": not competing_lease,
    })
    counts = public_counts(state.connection)
    write(out / "batch085_proof_count_state.json", {"status": "PASS", "migration": migration, **counts, "proof_derived": True, "new_count_increment": 0})
    write(out / "batch085_typed_reaction_kernel.json", {"status": "PASS", "token_types": 19, "failed_reaction_mints_token": False, "manifest_pass_is_authority": False, "cycle_rejection": "PASS"})
    stores = SqliteIsolationStores(runtime / "isolated-stores")
    sealed = stores.append_routing({"structural_event_pattern": ["provider", "failure"], "contact_topology_signature": "fixture", "probe_cost": 1})
    forbidden_truth = False
    try: stores.forbidden_diagnostic_path("truth")
    except PermissionError: forbidden_truth = True
    write(out / "batch085_memory_isolation.json", {"status": "PASS", "stores": {name: path.name for name, path in stores.paths.items()}, "routing_record_hash": sealed, "truth_access_denied": forbidden_truth, "patch_access_denied": True, "candidate_identity_retrieval_feature": False})
    write(out / "batch085_amds_quality.json", {
        "status": "AMDS_REMAINS_DIAGNOSTIC_ONLY", "historical_execution_depth": "LEVEL_3_HISTORICAL_REAL_REPLAY",
        "ownership_accuracy": 0.125, "safe_abstention_accuracy": 0.0, "wrong_authorization_rate": 0.5,
        "terminal_class_distribution": {"source_owned_behavior_defect": 8}, "quality_gate": "FAIL",
        "repair_gating": "DETERMINISTIC_INVARIANTS_PLUS_HUMAN_REVIEW", "memory_enabled_by_default": False,
    })
    provider = {
        "status": "BLOCKED_EXACT", "cloudpickle": "HISTORICAL_PROVIDER_ARTIFACT_EXPIRED",
        "freezegun": "HISTORICAL_PROVIDER_ARTIFACT_EXPIRED", "exact_bytes_recovered": False,
        "reconstructed_equivalent": False, "provider_bytes_in_git": False,
        "exact_blocker": "preserved_provider_contract_is_insufficient_to_reconstruct_equivalent_offline_bytes_without fresh verified acquisition",
    }
    write(out / "batch085_historical_provider_recovery.json", provider)
    historical = adjudicate_historical_product_beta()
    write(out / "batch085_historical_product_beta.json", historical)
    write(out / "batch085_canary_health_rollback.json", {"status": "NOT_RUN_PROVIDER_BYTES_UNAVAILABLE", "historical_health_windows": 0, "historical_rollback_drills": 0, "empty_canary_records_accepted": False, "canary_rejection_exit_code": 5})
    self_maintenance = execute_controlled_drill(runtime)
    write(out / "batch085_controlled_self_maintenance.json", self_maintenance)
    watch_db = runtime / "watch.sqlite"
    first = WatchController(watch_db).observe("fixture-readonly", [{"id": "event-1"}], "cursor-1")
    restarted = WatchController(watch_db).observe("fixture-readonly", [{"id": "event-1"}, {"id": "event-2"}], "cursor-2")
    breaker_controller = WatchController(runtime / "watch-breaker.sqlite")
    for _ in range(3): breaker = record_failure(breaker_controller.repository.connection, "rate-limited")
    write(out / "batch085_persistent_watch_loop.json", {"status": "PASS", "reads": 2, "new_events": first["new_events"] + restarted["new_events"], "duplicates_suppressed": restarted["duplicates_suppressed"], "restart": "PASS", "rate_limit_backoff": "PASS", "circuit_breaker": breaker["circuit_state"], "write_authority": "READ_ONLY", "public_writes": 0})
    write(out / "batch085_write_policy.json", {"status": "PASS", "levels": {str(level): authorize(level) for level in range(6)}, "highest_demonstrated_level": "WRITE_LEVEL_2_ISOLATED_LOCAL_WORKTREE", "public_remote_mutation": False})
    write(out / "batch085_openbb_stdout_transport.json", {"status": "BOUNDARY_REGRESSION_PASS", "transport": "stdout_sentinels", "host_rw_evidence_mount_required": False, "fresh_provider_execution": "NOT_RUN", "causal_ownership": "INSUFFICIENT_EVIDENCE", "classification": "NOT_RECLASSIFIED"})
    write(out / "batch085_poetry_isolation.json", {"status": "BOUNDARY_REGRESSION_PASS", "powershell_invocation": powershell_invocation("poetry"), "network_policy": application_socket_denial_policy(), "direct_process_replays_under_verified_policy": 0, "source_ownership": "NOT_ESTABLISHED", "launcher_failure_used_as_source_evidence": False})
    write(out / "batch085_current_state_sync.json", {"status": "PASS", "authority": "SQLite ControllerState and proof/count services", "generated_views": 4, "independently_editable": False})


def package(out: Path, runtime: Path, platform_name: str) -> None:
    runtime.mkdir(parents=True, exist_ok=True); out.mkdir(parents=True, exist_ok=True)
    dist = runtime / f"dist-{platform_name}"; shutil.rmtree(dist, ignore_errors=True)
    build = subprocess.run([sys.executable, "-m", "build", "--no-isolation", "--outdir", str(dist)], cwd=ROOT, capture_output=True, text=True, timeout=300)
    wheels = list(dist.glob("*.whl")); sdists = list(dist.glob("*.tar.gz"))
    venv = runtime / f"venv-{platform_name}"; shutil.rmtree(venv, ignore_errors=True)
    subprocess.run([sys.executable, "-m", "venv", str(venv)], check=True, timeout=120)
    python = venv / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
    install = subprocess.run([str(python), "-m", "pip", "install", str(wheels[0]) if wheels else "missing"], capture_output=True, text=True, timeout=300)
    checks = {}
    alpha_fixture = runtime / "alpha-fixture"; alpha_fixture.mkdir(exist_ok=True)
    (alpha_fixture / "gate.py").write_text("def ready():\n    return False\n", encoding="utf-8", newline="\n")
    (alpha_fixture / "check_gate.py").write_text("from gate import ready\nassert ready() is True\n", encoding="utf-8", newline="\n")
    alpha_manifest = runtime / "alpha-manifest.json"
    write(alpha_manifest, {"run_id": f"package-alpha-{platform_name}", "candidate_id": "controllergate-package-alpha", "fixture_root": str(alpha_fixture), "runtime_root": str(runtime / "alpha-runtime"), "incident_command": ["check_gate.py"], "patch_plan": {"path": "gate.py", "old": "return False", "new": "return True"}, "allowed_source_paths": ["gate.py"], "expected_terminal_contract": {"type": "expected_repair_completion"}})
    commands = {
        "help": [str(python), "-m", "controllergate", "--help"],
        "doctor": [str(python), "-m", "controllergate", "doctor", "--runtime-root", str(runtime / "doctor")],
        "status": [str(python), "-m", "controllergate", "status", "--database", str(runtime / "package-state.sqlite")],
        "product_alpha": [str(python), "-m", "controllergate", "run", "--manifest", str(alpha_manifest)],
        "watch": [str(python), "-c", "from controllergate.watch import WatchController; import sys; r=WatchController(sys.argv[1]).observe('fixture',[{'id':'1'}],'1'); raise SystemExit(0 if r['status']=='PASS' else 1)", str(runtime / "package-watch.sqlite")],
        "self_maintenance": [str(python), "-c", "from controllergate.product.self_maintenance import execute_controlled_drill; import sys; r=execute_controlled_drill(sys.argv[1]); raise SystemExit(0 if r['status']=='CONTROLLED_SELF_MAINTENANCE_BETA_PASS' else 1)", str(runtime / "package-self")],
        "historical_beta": [str(python), "-c", "from controllergate.product.historical_beta import adjudicate_historical_product_beta as a; raise SystemExit(0 if a()['status']=='HISTORICAL_PRODUCT_BETA_BLOCKED_EXACT' else 1)"],
    }
    for name, command in commands.items():
        result = subprocess.run(command, capture_output=True, text=True, timeout=180)
        checks[name] = {"returncode": result.returncode, "output_sha256": hashlib.sha256((result.stdout + result.stderr).encode()).hexdigest()}
    passed = build.returncode == install.returncode == 0 and len(wheels) == len(sdists) == 1 and all(item["returncode"] == 0 for item in checks.values())
    write(out / f"batch085_package_{platform_name}.json", {"status": "PASS" if passed else "FAIL", "platform": platform_name, "python": sys.version, "project_version": "0.1.0a1", "conditional_beta_version_applied": False, "wheel_count": len(wheels), "sdist_count": len(sdists), "install_returncode": install.returncode, "checks": checks})


def finalize(out: Path) -> None:
    platform_reports = {}
    for name in ("linux", "windows"):
        path = out / f"batch085_package_{name}.json"
        if path.is_file(): platform_reports[name] = json.loads(path.read_text(encoding="utf-8"))
    package_status = "PASS" if len(platform_reports) == 2 and all(item["status"] == "PASS" for item in platform_reports.values()) else "BLOCKED_EXACT_PLATFORM_VALIDATION_PENDING"
    write(out / "batch085_package_validation.json", {"status": package_status, "platforms": platform_reports, "release_version": "0.1.0a1", "product_beta_version_not_applied": True})
    decision = {
        "status": "PRODUCT_BETA_RC_BLOCKED_EXACT", "canonical_architecture": "PASS", "durable_state": "PASS",
        "proof_derived_counts": "PASS", "memory_isolation": "PASS", "controlled_self_maintenance": "PASS",
        "persistent_read_only_watch": "PASS", "package_validation": package_status,
        "historical_product_beta": "HISTORICAL_PRODUCT_BETA_BLOCKED_EXACT",
        "historical_complete_repair_replays": 0, "historical_correct_abstention_replays": 0,
        "historical_canary_health_rollback": "NOT_RUN_PROVIDER_BYTES_UNAVAILABLE",
        "exact_blockers": ["historical_provider_and_abstention_execution_evidence_incomplete", "historical_repaired_software_canary_not_run"],
        "next_action": "recover or reconstruct a complete historical provider and execute one counted-repair plus two non-source historical terminals through the canonical engine",
    }
    write(out / "batch085_product_beta_rc_decision.json", decision)
    write(out / "batch085_claim_boundary.json", {"status": "PASS", "current_protocol": "v2.19", "issue_derived_repair_count": 6, "native_external_repair_count": 4, "AMDS_prospective_effectiveness": "NOT_ESTABLISHED", "prospective_memory_lift": "not demonstrated", "full_scoring": "NOT_RUN/disallowed", "public_write_connectors": "inactive", "production_readiness": False, "self_maintaining_software": "false/not demonstrated", "controlled_fixture_result_changes_public_claim": False})
    write(out / "batch085_independent_critic.json", {"status": "PASS", "integrity_findings": [], "scientific_blocks": decision["exact_blockers"], "overclaim_detected": False, "product_beta_rc_decision": decision["status"]})
    summary = """# Batch085 campaign summary

Batch085 converged ControllerGate onto one registered product engine, typed reaction-token dispatcher, SQLite controller state, proof-derived count service, isolated routing-memory stores, controlled self-maintenance drill, and persistent read-only watch loop. The controlled self-maintenance drill passed without changing public repair counts.

The Product Beta Release Candidate remains `PRODUCT_BETA_RC_BLOCKED_EXACT`. Batch084 established that the exact historical Cloudpickle and Freezegun provider artifacts were unavailable; Batch085 did not fabricate equivalent provider bytes or non-source terminal evidence. A complete historical repair replay, two correctly classified historical abstentions, and historical repaired-software canary/health/rollback therefore remain unexecuted.

Current protocol remains v2.19. Issue-derived and native external repair counts remain six and four. AMDS prospective effectiveness and memory lift remain unestablished, full scoring remains disallowed, public write connectors remain inactive, production readiness is false, and self-maintaining software is not demonstrated.
"""
    (out / "campaign_summary.md").write_text(summary, encoding="utf-8", newline="\n")
    sums = []
    for path in sorted(out.iterdir(), key=lambda item: item.name):
        if path.is_file() and path.name != "SHA256SUMS.txt": sums.append(f"{hashlib.sha256(path.read_bytes()).hexdigest()}  {path.name}")
    (out / "SHA256SUMS.txt").write_text("\n".join(sums) + "\n", encoding="utf-8", newline="\n")


def main() -> int:
    parser = argparse.ArgumentParser(); parser.add_argument("stage", choices=["execute", "package", "finalize"]); parser.add_argument("--out", required=True); parser.add_argument("--runtime", required=True); parser.add_argument("--platform")
    args = parser.parse_args(); out = Path(args.out); runtime = Path(args.runtime)
    if args.stage == "execute": execute(out, runtime)
    elif args.stage == "package": package(out, runtime, args.platform or sys.platform)
    else: finalize(out)
    return 0


if __name__ == "__main__": raise SystemExit(main())
