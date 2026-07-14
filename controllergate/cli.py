from __future__ import annotations

import argparse
import json
from pathlib import Path

from .connectors.audit import audit_events
from .connectors.contract import ConnectorContract
from .connectors.github_public_readonly import read_frozen_resource
from .deployment.deployment_proof import seal_deployment
from .engine import resume_run, run_manifest, verify_run
from .product.doctor import doctor
from .product.manifest import load_manifest
from .state.resume import resume_status
from .state.state_store import StateStore


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="controllergate")
    sub = parser.add_subparsers(dest="command", required=True)
    doctor_command = sub.add_parser("doctor"); doctor_command.add_argument("--runtime-root")
    run = sub.add_parser("run")
    run.add_argument("--manifest", required=True)
    resume = sub.add_parser("resume"); resume.add_argument("--run-id", required=True); resume.add_argument("--manifest", required=True)
    status = sub.add_parser("status"); status.add_argument("--run-id", required=True); status.add_argument("--runtime-root", required=True)
    verify = sub.add_parser("verify"); verify.add_argument("--run-id", required=True); verify.add_argument("--manifest", required=True)
    canary = sub.add_parser("canary"); canary.add_argument("--proof", required=True)
    connectors = sub.add_parser("connectors"); connector_sub = connectors.add_subparsers(dest="connector_command", required=True)
    connector_verify = connector_sub.add_parser("verify"); connector_verify.add_argument("--manifest", required=True)
    args = parser.parse_args(argv)
    if args.command == "doctor": result = doctor(args.runtime_root)
    elif args.command == "run": result = run_manifest(args.manifest)
    elif args.command == "resume": result = resume_run(args.manifest, args.run_id)
    elif args.command == "status": result = resume_status(StateStore(Path(args.runtime_root) / "state"), args.run_id)
    elif args.command == "verify": result = verify_run(args.manifest, args.run_id)
    elif args.command == "canary":
        proof = json.loads(Path(args.proof).read_text(encoding="utf-8")); result = seal_deployment(proof.get("records", []))
    else:
        value = json.loads(Path(args.manifest).read_text(encoding="utf-8")); contract = ConnectorContract(value["connector_id"], tuple(value["allowed_resources"]), False)
        events = [read_frozen_resource(value["resource"])] if contract.validate()["status"] == "CONNECTOR_SCHEMA_VALIDATED" else []
        result = {"contract": contract.validate(), "events": events, "audit": audit_events(events)}
    print(json.dumps(result, sort_keys=True))
    terminal = result.get("status", result.get("audit", {}).get("status"))
    return 0 if terminal not in {"BLOCK", "FAIL", "CANARY_REJECTED"} else 1
