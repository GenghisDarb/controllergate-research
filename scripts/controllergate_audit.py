#!/usr/bin/env python3
"""Stable ControllerGate audit entry point for the current protocol."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
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
    if protocol == "v2.16":
        filename = "controllergate_v2_16_current.yaml"
    elif protocol == "v2.17":
        filename = "controllergate_v2_17_topology_runtime.yaml"
    elif protocol == "v2.18":
        filename = "controllergate_v2_18_evidence_derived_topology_historical_provider.yaml"
    else:
        filename = f"controllergate_{protocol.replace('.', '_')}.yaml"
    path = REPO_ROOT / "configs" / filename
    if not path.is_file():
        raise ValueError(f"unsupported protocol {protocol!r}")
    global CURRENT_CONFIG
    original = CURRENT_CONFIG
    try:
        CURRENT_CONFIG = path
        return load_current_config()
    finally:
        CURRENT_CONFIG = original


def load_json(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as handle:
        value = json.load(handle)
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


def claim_boundary_status(config: dict[str, Any]) -> tuple[str, list[str]]:
    errors: list[str] = []
    boundaries = config.get("claim_boundaries")
    if not isinstance(boundaries, dict):
        errors.append("config claim_boundaries must be present")
    else:
        if boundaries.get("full_scoring") != "NOT_RUN/disallowed":
            errors.append("config full_scoring boundary changed")
        if boundaries.get("self_maintaining_software") != "false/not demonstrated":
            errors.append("config self_maintaining_software boundary changed")
        if boundaries.get("family_generalization") != "not_expanded":
            errors.append("config family_generalization boundary changed")
        if not str(boundaries.get("non_ansible_positive_memory_count", "")).startswith("0"):
            errors.append("config non-Ansible positive-memory boundary changed")

    protocol_version = str(config.get("protocol_version", ""))
    if protocol_version in {"v2.15", "v2.16", "v2.17", "v2.18"}:
        state_path = REPO_ROOT / "outputs/current/CURRENT_PROTOCOL_STATE.json"
        if not state_path.is_file():
            return "FAIL", [f"missing {protocol_version} current protocol state"]
        state = load_json(state_path)
        if state.get("protocol_version") != protocol_version:
            approved_successor = False
            if protocol_version == "v2.15" and state.get("protocol_version") in {"v2.16", "v2.17"}:
                promotion_path = REPO_ROOT / "outputs/post_v2_37_hardening_batch068h1_universal_interlock_elbow_harness_decomposition/v2_16_promotion_decision_batch068h1.json"
                if promotion_path.is_file():
                    promotion = load_json(promotion_path)
                    approved_successor = promotion.get("status") == "PASS" and promotion.get("protocol_before") == "v2.15" and promotion.get("protocol_after") == "v2.16"
            if protocol_version == "v2.16" and state.get("protocol_version") == "v2.17":
                promotion_path = REPO_ROOT / "outputs/post_v2_37_hardening_batch068h2_tld_brot_bulb_topology_runtime_historical_capsule_recovery/v2_17_topology_promotion_decision.json"
                if promotion_path.is_file():
                    promotion = load_json(promotion_path)
                    approved_successor = promotion.get("status") == "PASS" and promotion.get("protocol_before") == "v2.16" and promotion.get("protocol_after") == "v2.17"
            if protocol_version in {"v2.15", "v2.16", "v2.17"} and state.get("protocol_version") == "v2.18":
                promotion_path = REPO_ROOT / "outputs/post_v2_37_hardening_batch068h3_historical_transitive_provider_closure_topology_hardening/v2_18_promotion_decision_batch068h3.json"
                if promotion_path.is_file():
                    promotion = load_json(promotion_path)
                    approved_successor = promotion.get("status") == "PASS" and promotion.get("protocol_before") == "v2.17" and promotion.get("protocol_after") == "v2.18"
            if not approved_successor:
                errors.append(f"{protocol_version} protocol state version mismatch")
        if state.get("patch_authority") is not False: errors.append("v2.15 patch authority changed")
        if state.get("repair_execution_authority") is not False: errors.append("v2.15 repair authority changed")
        if state.get("full_scoring") != "NOT_RUN/disallowed": errors.append("v2.15 full scoring changed")
        if state.get("memory_lift") != "not_demonstrated": errors.append("v2.15 memory claim changed")
        if state.get("self_maintaining_software") != "false/not_demonstrated": errors.append("v2.15 self-maintaining claim changed")
        return ("PASS" if not errors else "FAIL"), errors
    output_dir = REPO_ROOT / str(config["output_dir"])
    state_filename = "candidate_state_v2_14.json" if protocol_version == "v2.14" else "candidate_state_v2_13.json"
    state_path = output_dir / state_filename
    if not state_path.is_file():
        errors.append(f"missing candidate state: {state_path}")
        return "FAIL", errors

    state = load_json(state_path)
    final = state.get("final_result")
    if not isinstance(final, dict):
        errors.append("candidate state missing final_result object")
        return "FAIL", errors

    if final.get("controllergate_full_scoring") != "NOT_RUN" or final.get("full_scoring_allowed") is not False:
        errors.append("full scoring is no longer NOT_RUN/disallowed")
    if final.get("self_maintaining_software_demonstrated") is not False:
        errors.append("self-maintaining software is no longer false/not demonstrated")
    if final.get("family_generalization") != "not_expanded":
        errors.append("family generalization boundary changed")
    if final.get("non_ansible_positive_memory_count") != 0:
        errors.append("non-Ansible positive-memory count boundary changed")
    if protocol_version == "v2.14":
        if final.get("pysnooper2_final_classification") != "pysnooper2_fixture_materialization_forbidden_or_unavailable":
            errors.append("PySnooper:2 v2.14 final blocker changed")
        if final.get("pysnooper1_final_classification") != "pysnooper1_dependency_recovery_execution_blocked":
            errors.append("PySnooper:1 v2.14 final blocker changed")
    elif final.get("pysnooper2_classification") != "blocked_fixture_materialization_incomplete":
        errors.append("PySnooper:2 final blocker changed")
    return ("PASS" if not errors else "FAIL"), errors


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the configured ControllerGate protocol audit.")
    parser.add_argument("--protocol", choices=["current", "v2.14", "v2.15", "v2.16", "v2.17", "v2.18"], default="current")
    args = parser.parse_args()

    try:
        config = select_protocol(args.protocol)
        audit_script = REPO_ROOT / str(config["audit_script"])
        output_dir = REPO_ROOT / str(config["output_dir"])
        if not audit_script.is_file():
            raise FileNotFoundError(f"configured audit script does not exist: {audit_script}")
        if not output_dir.is_dir():
            raise FileNotFoundError(f"configured output directory does not exist: {output_dir}")
        boundary_status, boundary_errors = claim_boundary_status(config)
    except Exception as exc:
        print(f"controllergate audit setup FAIL: {exc}", file=sys.stderr)
        return 2

    command = [sys.executable, str(audit_script)] if str(config.get("protocol_version")) in {"v2.15", "v2.16", "v2.17", "v2.18"} else [sys.executable, str(audit_script), "--artifact-root", str(output_dir)]
    result = subprocess.run(command, cwd=REPO_ROOT)
    audit_status = "PASS" if result.returncode == 0 else "FAIL"

    print("controllergate audit summary")
    print(f"selected_protocol: {args.protocol}")
    print(f"protocol_version: {config['protocol_version']}")
    print(f"protocol_name: {config['protocol_name']}")
    print(f"audit_script: {config['audit_script']}")
    print(f"output_directory: {config['output_dir']}")
    print(f"audit_status: {audit_status}")
    print(f"claim_boundary_status: {boundary_status}")
    for error in boundary_errors:
        print(f"claim_boundary_error: {error}")
    return 0 if result.returncode == 0 and boundary_status == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
