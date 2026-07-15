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
    args = parser.parse_args(argv)
    if args.command == "doctor":
        result = doctor(args.runtime_root, deep=args.deep, repo_root=args.repo_root)
        if args.json_path:
            destination = Path(args.json_path)
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    elif args.command == "run": result = run_manifest(args.manifest)
    elif args.command == "historical-run": result = run_historical_lifecycle(args.config)
    elif args.command == "resume": result = resume_run(args.manifest, args.run_id)
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
