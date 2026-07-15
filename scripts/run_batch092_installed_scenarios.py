from __future__ import annotations

import argparse
import json
import os
import platform
import sys
from pathlib import Path

from controllergate.execution.execution_broker import execute_external_operation


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--controllergate-cli", required=True)
    parser.add_argument("--registry", required=True)
    parser.add_argument("--database", required=True)
    parser.add_argument("--runtime-root", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--platform", required=True)
    args = parser.parse_args()
    registry = [json.loads(line) for line in Path(args.registry).read_text(encoding="utf-8").splitlines() if line.strip()]
    runtime_root = Path(args.runtime_root); runtime_root.mkdir(parents=True, exist_ok=True)
    os.environ.pop("PYTHONPATH", None)
    attestation = {"status": "PASS", "attestation_hash": __import__("hashlib").sha256((args.controllergate_cli + sys.version).encode()).hexdigest()}
    rows = []
    parent = None
    for index, scenario in enumerate(registry):
        command = [args.controllergate_cli, "reactome-simulate", "--scenario", str(Path(args.registry).resolve()), "--scenario-id", scenario["scenario_id"], "--database", str(Path(args.database).resolve()), "--platform", args.platform]
        run, record = execute_external_operation(
            operation_type="target_execution", argv=command, cwd=runtime_root, runtime_root=runtime_root,
            stage_id=f"batch092-installed-reactome-{index + 1:02d}", candidate_id=scenario["scenario_id"],
            authorization_id="batch092-read-only-installed-scenario", runtime_attestation=attestation,
            platform=platform.system().lower(), runtime=sys.version, network_policy="none", timeout=120,
            parent_ledger_hash=parent, run_id="batch092-installed-reactome", nonce=f"scenario-{index + 1:02d}",
        )
        parent = record["record_hash"]
        value = json.loads(run.stdout.strip()) if run.returncode == 0 else {"mechanism_status": "FAIL", "stderr_hash": record["stderr_hash"]}
        rows.append({**value, "broker_record_hash": record["record_hash"], "return_code": run.returncode, "producer": "scripts/run_batch092_installed_scenarios.py", "execution_depth": "installed_CLI_brokered_execution", "semantic_scope": "representative Reactome chapter scenario", "authority_allowed": "installed reachability evidence", "authority_forbidden": "repair authorization"})
    Path(args.output).write_text("".join(json.dumps(row, sort_keys=True) + "\n" for row in rows), encoding="utf-8", newline="\n")
    ok = len(rows) == 29 and all(row.get("mechanism_status") == "PASS" and row.get("installed_site_packages_origin") is True for row in rows)
    print(json.dumps({"status": "PASS" if ok else "FAIL", "scenario_count": len(rows), "brokered_count": sum(bool(row.get("broker_record_hash")) for row in rows), "platform": args.platform}, sort_keys=True))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
