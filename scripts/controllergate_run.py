#!/usr/bin/env python3
"""Stable ControllerGate run entry point for the current protocol."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
CURRENT_CONFIG = REPO_ROOT / "configs" / "controllergate_current.yaml"


def parse_scalar(value: str) -> str:
    value = value.strip()
    if (value.startswith('"') and value.endswith('"')) or (value.startswith("'") and value.endswith("'")):
        return value[1:-1]
    return value


def load_current_config() -> dict[str, Any]:
    if not CURRENT_CONFIG.is_file():
        raise FileNotFoundError(f"missing current protocol config: {CURRENT_CONFIG}")
    config: dict[str, Any] = {}
    section: str | None = None
    for line_number, raw in enumerate(CURRENT_CONFIG.read_text(encoding="utf-8").splitlines(), start=1):
        line = raw.rstrip()
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if not line.startswith((" ", "\t")):
            if ":" not in line:
                raise ValueError(f"{CURRENT_CONFIG}:{line_number}: malformed line")
            key, value = line.split(":", 1)
            key = key.strip()
            value = value.strip()
            if not value:
                config[key] = {}
                section = key
            else:
                config[key] = parse_scalar(value)
                section = None
            continue
        if section is None or ":" not in line:
            raise ValueError(f"{CURRENT_CONFIG}:{line_number}: malformed nested line")
        key, value = line.strip().split(":", 1)
        target = config.get(section)
        if not isinstance(target, dict):
            raise ValueError(f"{CURRENT_CONFIG}:{line_number}: nested value under non-section")
        target[key.strip()] = parse_scalar(value)
    return config


def select_protocol(protocol: str) -> dict[str, Any]:
    if protocol == "current":
        return load_current_config()
    path = REPO_ROOT / "configs" / f"controllergate_{protocol.replace('.', '_')}.yaml"
    if not path.is_file():
        raise ValueError(f"unsupported protocol {protocol!r}")
    global CURRENT_CONFIG
    original = CURRENT_CONFIG
    try:
        CURRENT_CONFIG = path
        return load_current_config()
    finally:
        CURRENT_CONFIG = original


def dry_run(config: dict[str, Any], selected_protocol: str) -> int:
    runner_script = REPO_ROOT / str(config["runner_script"])
    audit_script = REPO_ROOT / str(config["audit_script"])
    output_dir = REPO_ROOT / str(config["output_dir"])
    current_output_dir = REPO_ROOT / str(config["current_output_dir"])
    missing = [
        str(path.relative_to(REPO_ROOT))
        for path in [runner_script, audit_script, output_dir, current_output_dir]
        if not path.exists()
    ]
    status = "PASS" if not missing else "FAIL"
    print("controllergate run dry-run summary")
    print(f"selected_protocol: {selected_protocol}")
    print(f"protocol_version: {config['protocol_version']}")
    print(f"protocol_name: {config['protocol_name']}")
    print(f"campaign_id: {config['campaign_id']}")
    print(f"based_on: {config['based_on']}")
    print(f"implementation_commit: {config['implementation_commit']}")
    print(f"official_ingest_commit: {config['official_ingest_commit']}")
    print(f"workflow_run_id: {config['workflow_run_id']}")
    print(f"artifact_name: {config['artifact_name']}")
    print(f"runner_script: {config['runner_script']}")
    print(f"audit_script: {config['audit_script']}")
    print(f"output_directory: {config['output_dir']}")
    print(f"current_output_directory: {config['current_output_dir']}")
    print("full_workflow_executed: false")
    print(f"dry_run_status: {status}")
    for path in missing:
        print(f"missing_configured_path: {path}")
    return 0 if not missing else 1


def main() -> int:
    parser = argparse.ArgumentParser(description="Inspect or run the configured ControllerGate protocol.")
    parser.add_argument("action", nargs="?", choices=["status", "validate", "plan", "probe"])
    parser.add_argument("--protocol", choices=["current", "v2.14", "v2.15"], default="current")
    parser.add_argument("--dry-run", action="store_true", help="Inspect configured runner without executing it.")
    parser.add_argument("--candidate")
    parser.add_argument("--authorization")
    args = parser.parse_args()

    try:
        config = select_protocol(args.protocol)
    except Exception as exc:
        print(f"controllergate run setup FAIL: {exc}", file=sys.stderr)
        return 2

    if args.dry_run:
        return dry_run(config, args.protocol)

    if str(config.get("protocol_version")) == "v2.15" and args.action:
        from controllergate.engine import FrontierEngine
        engine = FrontierEngine(REPO_ROOT)
        if args.action == "status":
            result = engine.status()
        elif args.action == "validate":
            result = engine.validate()
        elif args.action == "plan":
            result = engine.plan(str(args.candidate or ""))
        else:
            if not args.candidate or not args.authorization:
                result = {"status": "BLOCK", "blocker": "probe_authorization_manifest_required"}
            else:
                from controllergate.runtime.probe_authorization import verify_probe_authorization
                import json as _json
                index = _json.loads(engine.index_path.read_text(encoding="utf-8"))
                item = next((row for row in index["records"] if row["candidate_id"] == args.candidate), None)
                if item is None:
                    result = {"status": "BLOCK", "blocker": "frontier_candidate_unknown"}
                else:
                    state = _json.loads((REPO_ROOT / item["state_path"]).read_text(encoding="utf-8"))
                    auth = _json.loads(Path(args.authorization).read_text(encoding="utf-8"))
                    checked = verify_probe_authorization(auth, state)
                    result = {**checked, "execution_authorized_for_versioned_workflow": checked["status"] == "PASS", "patch_authority": False}
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0 if result.get("status") == "PASS" else 2

    print(
        "controllergate non-dry-run dispatch is intentionally disabled for the current protocol interface. "
        "versioned runner execution can create or modify campaign evidence and should be invoked only through "
        "the versioned runner after explicit authorization for a new evidence-producing run.",
        file=sys.stderr,
    )
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
