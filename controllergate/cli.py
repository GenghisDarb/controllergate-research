from __future__ import annotations

import argparse
import json
from pathlib import Path

from .connectors.audit import audit_events
from .connectors.contract import ConnectorContract
from .connectors.github_public_readonly import read_frozen_resource
from .deployment.deployment_proof import seal_deployment
from .engine import resume_run, run_historical_lifecycle, run_manifest, status_run, verify_run
from .product.doctor import doctor
from .product.manifest import load_manifest
from .state.repository import ControllerStateRepository
from .proof.count_service import public_counts
from .watch.controller import WatchController
from .isomorphism.scenarios import execute_scenario
from .isomorphism.runtime import execute_structured_scenario
from .evidence.contracts import load_contracts, seal_contracts
from .evidence.materializer import materialize_candidate
from .topology.pipeline_v1 import compile_candidate_frame, produce_topology, verify_topology
from .amds.batch098_diagnose import diagnose_batch098


def _load_scenario(path: str, scenario_id: str | None = None) -> dict[str, object]:
    text = Path(path).read_text(encoding="utf-8")
    if Path(path).suffix == ".jsonl":
        rows = [json.loads(line) for line in text.splitlines() if line.strip()]
        if scenario_id is not None:
            return next(row for row in rows if row.get("scenario_id") == scenario_id)
        return rows[0]
    return json.loads(text)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="controllergate")
    sub = parser.add_subparsers(dest="command", required=True)
    doctor_command = sub.add_parser("doctor"); doctor_command.add_argument("--runtime-root"); doctor_command.add_argument("--deep", action="store_true"); doctor_command.add_argument("--json", dest="json_path"); doctor_command.add_argument("--repo-root")
    run = sub.add_parser("run")
    run.add_argument("--manifest", required=True)
    historical = sub.add_parser("historical-run"); historical.add_argument("--config", required=True)
    migrate = sub.add_parser("migrate-state"); migrate.add_argument("--from-json", required=True); migrate.add_argument("--database", required=True)
    resume = sub.add_parser("resume"); resume.add_argument("--run-id", required=True); resume.add_argument("--manifest", required=True)
    status = sub.add_parser("status"); status.add_argument("--run-id"); status.add_argument("--runtime-root"); status.add_argument("--database")
    verify = sub.add_parser("verify"); verify.add_argument("--run-id", required=True); verify.add_argument("--manifest", required=True)
    canary = sub.add_parser("canary"); canary.add_argument("--proof", required=True)
    connectors = sub.add_parser("connectors"); connector_sub = connectors.add_subparsers(dest="connector_command", required=True)
    connector_verify = connector_sub.add_parser("verify"); connector_verify.add_argument("--manifest", required=True)
    watch = sub.add_parser("watch"); watch.add_argument("--database", required=True); watch.add_argument("--connector-id", required=True); watch.add_argument("--events", required=True); watch.add_argument("--cursor"); watch.add_argument("--once", action="store_true")
    reactome = sub.add_parser("reactome-simulate"); reactome.add_argument("--scenario", required=True); reactome.add_argument("--scenario-id"); reactome.add_argument("--database", required=True); reactome.add_argument("--platform", required=True)
    structured_reactome = sub.add_parser("reactome-execute"); structured_reactome.add_argument("--scenario", required=True); structured_reactome.add_argument("--scenario-id"); structured_reactome.add_argument("--database", required=True); structured_reactome.add_argument("--platform", required=True)
    reactome_run = sub.add_parser("reactome-run"); reactome_run.add_argument("--scenario", required=True); reactome_run.add_argument("--scenario-id"); reactome_run.add_argument("--database", required=True); reactome_run.add_argument("--platform", required=True)
    evidence = sub.add_parser("evidence")
    evidence_sub = evidence.add_subparsers(dest="evidence_command", required=True)
    materialize = evidence_sub.add_parser("materialize-candidate")
    materialize.add_argument("--contracts", required=True)
    materialize.add_argument("--candidate", required=True)
    materialize.add_argument("--runtime-root", required=True)
    materialize.add_argument("--output", required=True)
    materialize.add_argument("--provider-python")
    materialize.add_argument("--forbidden-repo-root", required=True)
    materialize.add_argument("--run-id")
    verify_incident = evidence_sub.add_parser("verify-incident")
    verify_incident.add_argument("--result", required=True)
    inspect_contracts = evidence_sub.add_parser("inspect-contracts")
    inspect_contracts.add_argument("--contracts", required=True)
    topology = sub.add_parser("topology")
    topology_sub = topology.add_subparsers(dest="topology_command", required=True)
    topology_produce = topology_sub.add_parser("produce")
    topology_produce.add_argument("--candidate-evidence", required=True); topology_produce.add_argument("--contracts", required=True); topology_produce.add_argument("--output", required=True)
    topology_verify = topology_sub.add_parser("verify")
    topology_verify.add_argument("--candidate-evidence", required=True); topology_verify.add_argument("--producer-evidence", required=True); topology_verify.add_argument("--output", required=True)
    topology_compile = topology_sub.add_parser("compile-board")
    topology_compile.add_argument("--candidate-evidence", required=True); topology_compile.add_argument("--verified-topology", required=True); topology_compile.add_argument("--contracts", required=True); topology_compile.add_argument("--output", required=True)
    amds = sub.add_parser("amds")
    amds_sub = amds.add_subparsers(dest="amds_command", required=True)
    diagnose = amds_sub.add_parser("diagnose")
    diagnose.add_argument("--candidate-evidence-root", required=True); diagnose.add_argument("--topology-root", required=True); diagnose.add_argument("--contracts", required=True); diagnose.add_argument("--output", required=True)
    args = parser.parse_args(argv)
    if args.command == "doctor":
        result = doctor(args.runtime_root, deep=args.deep, repo_root=args.repo_root)
        if args.json_path:
            destination = Path(args.json_path)
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    elif args.command == "run": result = run_manifest(args.manifest, invoked_via_cli=True)
    elif args.command == "historical-run": result = run_historical_lifecycle(args.config, invoked_via_cli=True)
    elif args.command == "resume": result = resume_run(args.manifest, args.run_id, invoked_via_cli=True)
    elif args.command == "status":
        if args.database:
            result = status_run(args.database, args.run_id)
        elif args.run_id and args.runtime_root:
            result = status_run(Path(args.runtime_root) / "state" / "controllergate.sqlite3", args.run_id)
        else:
            result = {"status": "BLOCK", "blocker": "status_database_or_run_runtime_required"}
    elif args.command == "verify": result = verify_run(args.manifest, args.run_id)
    elif args.command == "canary":
        proof = json.loads(Path(args.proof).read_text(encoding="utf-8")); result = seal_deployment(proof.get("records", []))
    elif args.command == "watch":
        events = json.loads(Path(args.events).read_text(encoding="utf-8"))
        result = WatchController(args.database).observe(args.connector_id, events, args.cursor)
    elif args.command == "reactome-simulate":
        result = execute_scenario(_load_scenario(args.scenario, args.scenario_id), args.database, platform=args.platform)
    elif args.command in {"reactome-execute", "reactome-run"}:
        result = execute_structured_scenario(_load_scenario(args.scenario, args.scenario_id), args.database, platform=args.platform)
    elif args.command == "evidence" and args.evidence_command == "materialize-candidate":
        result = materialize_candidate(
            args.contracts, args.candidate, args.runtime_root, args.output,
            provider_python=args.provider_python, forbidden_repo_root=args.forbidden_repo_root, run_id=args.run_id,
        )
    elif args.command == "evidence" and args.evidence_command == "verify-incident":
        value = json.loads(Path(args.result).read_text(encoding="utf-8"))
        result = {"status": "PASS" if value.get("typed_incident", {}).get("status") == "PASS" else "SCIENTIFIC_BLOCK", "candidate_id": value.get("candidate_id"), "typed_incident": value.get("typed_incident")}
    elif args.command == "evidence" and args.evidence_command == "inspect-contracts":
        contracts = load_contracts(args.contracts)
        sealed = seal_contracts(contracts)
        result = {
            "status": sealed["status"],
            "candidate_count": len(contracts),
            "candidate_ids": [row.candidate_id for row in contracts],
            "bundle_hash": sealed["bundle_hash"],
            "read_only": True,
            "patch_operation_count": 0,
            "authority_allowed": "contract inspection only",
            "authority_forbidden": ["candidate execution", "patch", "repair count", "release promotion"],
        }
    elif args.command == "topology" and args.topology_command == "produce":
        result = produce_topology(args.candidate_evidence, args.contracts, args.output)
    elif args.command == "topology" and args.topology_command == "verify":
        result = verify_topology(args.candidate_evidence, args.producer_evidence, args.output)
    elif args.command == "topology" and args.topology_command == "compile-board":
        result = compile_candidate_frame(args.candidate_evidence, args.verified_topology, args.contracts, args.output)
    elif args.command == "amds" and args.amds_command == "diagnose":
        result = diagnose_batch098(args.candidate_evidence_root, args.topology_root, args.contracts, args.output)
    elif args.command == "migrate-state":
        repository = ControllerStateRepository(args.database)
        try: result = repository.migrate_json_state(getattr(args, "from_json"))
        finally: repository.close()
    else:
        value = json.loads(Path(args.manifest).read_text(encoding="utf-8")); contract = ConnectorContract(value["connector_id"], tuple(value["allowed_resources"]), False)
        events = [read_frozen_resource(value["resource"])] if contract.validate()["status"] == "CONNECTOR_SCHEMA_VALIDATED" else []
        result = {"contract": contract.validate(), "events": events, "audit": audit_events(events)}
    print(json.dumps(result, sort_keys=True))
    terminal = result.get("status", result.get("audit", {}).get("status"))
    if terminal == "CANARY_REJECTED": return 5
    if terminal == "SAFE_ABSTENTION": return 2
    if terminal == "BLOCK": return 3
    if terminal == "FAIL": return 4
    if terminal == "MANUAL_APPROVAL_REQUIRED": return 6
    return 0
