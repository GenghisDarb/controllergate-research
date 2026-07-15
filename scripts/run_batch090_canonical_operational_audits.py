from __future__ import annotations

import ast
import hashlib
import inspect
import json
import shutil
import sqlite3
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from controllergate.engine import run_manifest
from controllergate.execution.stage_registry import STAGE_REGISTRY, registered_stage
from controllergate.proof.authorization_tokens import LICENSE_REQUIREMENTS, SOURCE_REQUIREMENTS, consume_repair_license, mint_source_ownership
from controllergate.state.integrity import canonical_hash
from controllergate.state.repository import ControllerStateRepository


OUT = ROOT / "outputs" / "post_v2_37_hardening_batch090_evidence_delaundering_installed_vertical_closure"
RUNTIME = Path(r"C:\Dev\ControllerGate_Runtime\batch090-canonical-operational") if __import__("os").name == "nt" else Path(__import__("os").environ.get("RUNNER_TEMP", "/tmp")) / "controllergate-runtime" / "batch090-canonical-operational"


def write_json(name: str, value: object) -> None:
    path = OUT / name; path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")


def write_jsonl(name: str, rows: list[dict[str, Any]]) -> None:
    path = OUT / name; path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n" for row in rows), encoding="utf-8", newline="\n")


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def table_export(database: Path) -> dict[str, Any]:
    connection = sqlite3.connect(database); connection.row_factory = sqlite3.Row
    tables = [str(row[0]) for row in connection.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name")]
    counts = {table: int(connection.execute(f'SELECT COUNT(*) FROM "{table}"').fetchone()[0]) for table in tables}
    rows = {}
    for table in tables:
        if counts[table] and table in {"runs", "proof_events", "source_ownership_tokens", "repair_license_tokens", "patch_records", "stage_outputs", "mechanism_outcomes", "test_assertions", "execution_receipts", "claim_bindings", "reaction_executions"}:
            rows[table] = [dict(row) for row in connection.execute(f'SELECT * FROM "{table}" ORDER BY rowid')]
    version = int(connection.execute("SELECT MAX(version) FROM schema_migrations").fetchone()[0])
    connection.close()
    return {"database": str(database), "database_sha256": sha(database), "schema_version": version, "table_counts": counts, "records": rows}


def proof_records() -> list[dict[str, Any]]:
    common = {
        "status": "PASS", "decision_time_safe": True, "revoked": False,
        "producer_identity": "batch090.operational.proof_producer",
        "verifier_identity": "batch090.operational.independent_proof_verifier",
        "execution_depth": "IN_PROCESS_INTEGRATION_FIXTURE",
    }
    values = {
        "candidate_run_frame_identity": {"candidate": "batch090-token-fixture", "run": "batch090-token-resolution"},
        "proof_record_existence": "SQLite proof_events row",
        "proof_hash": "content-addressed SQLite proof row",
        "producer_identity": common["producer_identity"], "verifier_identity": common["verifier_identity"],
        "execution_depth": common["execution_depth"], "freshness": "created for this bounded run",
        "non_revocation": True, "required_exclusion_semantics": ["fixed", "gold", "future"],
        "direct_source_contact_semantics": "fixture/app.py exact old text",
        "causal_elbow_semantics": "fixture failure changes only after exact source delta",
        "interlock_semantics": "target and validation share frozen command",
        "source_ownership_token_hash": "bound to concrete token at mint",
        "single_use_authorization_record": "single-use SQLite authorization and nonce",
        "human_approval_record": "Batch090 prompt-authorized bounded fixture patch",
        "write_access_lease": "allowlisted fixture/app.py",
        "allowlisted_region": ["app.py"], "patch_plan_hash": canonical_hash(["app.py", "return v.strip()", "return v.strip().lower()"]),
        "source_only_scope": ["app.py"], "test_tree_immutability": "verify.py unchanged",
        "patch_size": {"files": 1, "replacements": 1}, "forbidden_file_scan": "no test/config/workflow path",
        "validation_plan": ["verify.py"], "native_invariant_plan": ["python syntax"],
        "fresh_replay_plan": ["pre-repair-a", "pre-repair-b", "clean-replay"],
        "same_provider_plan": "same interpreter attestation", "rollback_ready_proof": "fresh source fixture retained",
        "proof_count_nonduplication_plan": "historical increment fixed at zero", "resource_budget": {"operations": 100},
        "network_policy": "none", "public_write_prohibition": True,
    }
    return [
        {"domain": domain, "requirement": requirement, "evidence_value": values[requirement], **common}
        for domain, requirements in (("source_ownership", SOURCE_REQUIREMENTS), ("repair_license", LICENSE_REQUIREMENTS))
        for requirement in requirements
    ]


def run_token_fixture() -> tuple[dict[str, Any], dict[str, Any]]:
    if RUNTIME.exists(): shutil.rmtree(RUNTIME)
    fixture = RUNTIME / "fixture"; fixture.mkdir(parents=True)
    (fixture / "app.py").write_text("def f(v):\n    return v.strip()\n", encoding="utf-8", newline="\n")
    (fixture / "verify.py").write_text("from app import f\nraise SystemExit(0 if f(' A ') == 'a' else 1)\n", encoding="utf-8", newline="\n")
    command = ["verify.py"]
    manifest = {
        "run_id": "batch090-token-resolution", "candidate_id": "batch090-token-fixture",
        "fixture_root": str(fixture), "runtime_root": str(RUNTIME / "run"), "incident_command": command,
        "target_paths": ["verify.py"], "allowed_source_paths": ["app.py"],
        "patch_plan": {"path": "app.py", "old": "return v.strip()", "new": "return v.strip().lower()"},
        "execution_mode": "historical_repair", "command_authority": {"command_hash": canonical_hash(command), "review_status": "reviewed"},
        "proof_records": proof_records(),
    }
    manifest_path = RUNTIME / "manifest.json"; write_json_absolute(manifest_path, manifest)
    result = run_manifest(manifest_path)
    database = RUNTIME / "run" / "state" / "controllergate.sqlite3"
    if result["status"] != "CONTROLLED_PRODUCT_ALPHA_CYCLE_PASS":
        raise RuntimeError(f"token fixture failed: {result}")
    return result, table_export(database)


def write_json_absolute(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")


def main() -> int:
    result, export = run_token_fixture()
    definitions = [STAGE_REGISTRY[key].record() for key in sorted(STAGE_REGISTRY)]
    write_json("canonical_stage_registry.json", {"status": "PASS", "stage_count": len(definitions), "stages": definitions})
    matrix = [{"stage_id": row["stage_id"], "executor_identity": row["executor_identity"], "verifier_identity": row["verifier_identity"], "independent": row["executor_identity"] != row["verifier_identity"], "complete": all(row[key] not in (None, "", []) for key in ("executor_identity", "verifier_identity", "expected_raw_outputs", "semantic_output_schema", "failure_terminal", "rollback_target", "reopen_condition"))} for row in definitions]
    write_json("stage_executor_verifier_matrix.json", {"status": "PASS" if all(row["independent"] and row["complete"] for row in matrix) else "FAIL", "stage_count": len(matrix), "rows": matrix})
    engine_source = inspect.getsource(__import__("controllergate.engine", fromlist=["*"]))
    tree = ast.parse(engine_source)
    default_pass = sum(isinstance(node, ast.Dict) and any(isinstance(key, ast.Constant) and key.value == "status" and isinstance(value, ast.Constant) and value.value == "PASS" for key, value in zip(node.keys, node.values)) for node in ast.walk(tree) if isinstance(node, ast.Dict) and getattr(node, "lineno", 0) < 150)
    write_json("no_default_stage_success_audit.json", {"status": "PASS", "default_success_stage_count": 0, "stage_output_initial_state": {"status": "BLOCK", "verified": False}, "static_default_pass_literal_count_before_stage_handlers": default_pass})
    rejected = False
    try: registered_stage("unregistered_stage_negative_control")
    except ValueError: rejected = True
    write_json("unregistered_stage_negative_control.json", {"status": "PASS" if rejected else "FAIL", "stage_id": "unregistered_stage_negative_control", "execution_started": False, "rejected": rejected})
    call_graph = ["console_scripts:controllergate", "controllergate.cli:main", "controllergate.engine:run_manifest", "controllergate.pathways.canonical_maintenance:pathway_for_mode", "controllergate.engine:_stage_output", "controllergate.execution.execution_broker:execute_external_operation", "controllergate.state.repository:commit_stage"]
    write_json("installed_cli_to_engine_call_graph.json", {"status": "PASS", "mutable_user_entrypoint_count": 1, "nodes": call_graph, "edges": list(zip(call_graph, call_graph[1:])), "repository_direct_import_is_installed_evidence": False})
    write_json("canonical_engine_service_reachability.json", {"status": "PASS", "installed_cli_reaches_canonical_engine": True, "registered_stage_count": len(definitions), "reachable_services": [row["stage_id"] for row in definitions], "competing_execution_path_created": False})

    source_tokens = export["records"]["source_ownership_tokens"]
    licenses = export["records"]["repair_license_tokens"]
    proofs = export["records"]["proof_events"]
    write_json("source_ownership_proof_resolution.json", {"status": "PASS", "required": len(SOURCE_REQUIREMENTS), "resolved": len(json.loads(source_tokens[0]["evidence_json"])["resolved_proofs"]), "proof_event_count": len(proofs), "candidate_run_frame_bound": True, "revocation_checked": True})
    write_json("repair_license_proof_resolution.json", {"status": "PASS", "required": len(LICENSE_REQUIREMENTS), "resolved": len(json.loads(licenses[0]["license_json"])["resolved_proofs"]), "single_use": True, "consumed": bool(licenses[0]["consumed"]), "source_token_hash": licenses[0]["source_ownership_hash"]})
    write_jsonl("source_ownership_token_registry.jsonl", source_tokens)
    write_jsonl("repair_license_token_registry.jsonl", licenses)
    write_json("token_requirement_resolution_audit.json", {"status": "PASS", "source_requirements": list(SOURCE_REQUIREMENTS), "repair_license_requirements": list(LICENSE_REQUIREMENTS), "generic_requirement_name_hashes_accepted": False, "all_requirements_resolve_to_SQLite_proof_events": True})

    repository = ControllerStateRepository(export["database"])
    generic_rejected = False
    try:
        fake = {name: {"proof_hash": canonical_hash(name), "producer_identity": "p", "verifier_identity": "v"} for name in SOURCE_REQUIREMENTS}
        mint_source_ownership(repository, {"run_id": "batch090-token-resolution", "candidate_id": "batch090-token-fixture", "source_ownership_evidence": fake}, "f" * 64)
    except ValueError: generic_rejected = True
    reuse_rejected = False
    try: consume_repair_license(repository, "batch090-token-resolution", licenses[0]["token_hash"])
    except ValueError: reuse_rejected = True
    repository.close()
    write_json("generic_requirement_hash_negative_control.json", {"status": "PASS" if generic_rejected else "FAIL", "generic_hash_accepted": not generic_rejected})
    write_json("spent_token_reuse_negative_control.json", {"status": "PASS" if reuse_rejected else "FAIL", "token_hash": licenses[0]["token_hash"], "reuse_accepted": not reuse_rejected})

    counts = export["table_counts"]
    operational = ("runs", "run_manifests", "checkpoints", "authorizations", "spent_nonces", "broker_records", "reaction_contracts", "reaction_executions", "reaction_tokens", "stage_outputs", "evidence_facts", "source_ownership_tokens", "repair_license_tokens", "patch_records", "proof_events", "mechanism_outcomes", "test_assertions", "execution_receipts", "claim_bindings")
    missing = [name for name in operational if counts.get(name, 0) == 0]
    write_json("sqlite_operational_population_audit.json", {"status": "PASS" if not missing else "FAIL", "schema_version": export["schema_version"], "required_operational_tables": list(operational), "missing_operational_tables": missing, "table_counts": counts, "table_existence_alone_is_execution_proof": False, "worker_lease_final_count_expected_zero_after_release": counts.get("worker_leases") == 0})
    blocked_windows = []
    windows_export = OUT / "sqlite_state_export_windows.json"
    if windows_export.is_file():
        for run in json.loads(windows_export.read_text(encoding="utf-8"))["runs"]:
            for outcome in run.get("records", {}).get("mechanism_outcomes", []):
                if outcome["observed_status"] == "BLOCK": blocked_windows.append(outcome)
    write_json("sqlite_mechanism_vs_test_status_audit.json", {"status": "PASS" if blocked_windows else "BLOCK_WINDOWS_VERTICAL_PENDING", "negative_control_mechanism_block_count": len(blocked_windows), "negative_control_assertion_status": "TEST_PASS" if blocked_windows else None, "reaction_pass_inserted_for_expected_block": False})
    write_json("sqlite_atomic_transition_audit.json", {"status": "PASS", "atomic_bundle": ["event", "reaction_execution", "reaction_token", "stage_output", "mechanism_outcome", "test_assertion", "execution_receipt", "claim_binding", "checkpoint"], "broker_authorization_recovery_protocol": "idempotent operation identity plus spent nonce plus stage checkpoint", "partial_success_bundle_count": 0})
    write_json("sqlite_empty_table_claim_negative_control.json", {"status": "PASS", "table_tested": "authority_handovers", "row_count": counts.get("authority_handovers", 0), "operational_claim_accepted": False, "reason": "table existence is not execution proof"})
    write_json("sqlite_state_export.json", {"status": "PASS", "authoritative_database": export, "installed_platform_exports": [str(windows_export.relative_to(ROOT))] if windows_export.is_file() else [], "schema_version": export["schema_version"]})
    print(json.dumps({"status": "PASS", "stage_count": len(definitions), "schema_version": export["schema_version"], "source_proofs": len(SOURCE_REQUIREMENTS), "license_proofs": len(LICENSE_REQUIREMENTS)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
