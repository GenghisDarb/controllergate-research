#!/usr/bin/env python3
"""Audit vHW0 ControllerGate telemetry maintenance validation plan."""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = REPO_ROOT / "outputs" / "vHW0_controllergate_telemetry_maintenance_plan"
SUMMARY = REPO_ROOT / "controllergate_v1_7_beta" / "reports" / "critic_review_package" / "shareable_summary.md"

REQUIRED = [
    "telemetry_maintenance_validation_plan.json",
    "candidate_domains.json",
    "safe_scope_boundary.md",
    "replay_dataset_requirements.json",
    "memory_vs_no_memory_telemetry_protocol.json",
    "claim_boundary.md",
    "campaign_summary.md",
    "SHA256SUMS.txt",
]


def load_json(path: Path) -> tuple[dict[str, Any], list[str]]:
    if not path.exists():
        return {}, [f"missing JSON file: {path}"]
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return {}, [f"{path}: invalid JSON: {exc.msg}"]
    if not isinstance(data, dict):
        return {}, [f"{path}: expected JSON object"]
    return data, []


def verify_manifest(directory: Path) -> list[str]:
    manifest = directory / "SHA256SUMS.txt"
    if not manifest.exists():
        return [f"missing SHA256SUMS.txt in {directory}"]
    errors: list[str] = []
    seen: set[str] = set()
    for line_no, line in enumerate(manifest.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        parts = line.split()
        if len(parts) != 2:
            errors.append(f"{manifest}:{line_no}: expected '<sha256>  <path>'")
            continue
        expected, rel = parts
        seen.add(rel)
        path = directory / rel
        if not path.exists():
            errors.append(f"{manifest}:{line_no}: missing artifact {rel}")
            continue
        actual = hashlib.sha256(path.read_bytes()).hexdigest()
        if actual != expected:
            errors.append(f"{manifest}:{line_no}: hash mismatch for {rel}")
    for path in directory.rglob("*"):
        if path.is_file() and path.name != "SHA256SUMS.txt":
            rel = str(path.relative_to(directory)).replace("\\", "/")
            if rel not in seen:
                errors.append(f"SHA256SUMS missing artifact entry {rel}")
    return errors


def require_text(path: Path, snippets: list[str]) -> list[str]:
    if not path.exists():
        return [f"missing text file: {path}"]
    text = path.read_text(encoding="utf-8", errors="replace")
    return [f"{path}: missing required text {snippet!r}" for snippet in snippets if snippet not in text]


def main() -> int:
    errors: list[str] = []
    if not OUTPUT_DIR.exists():
        errors.append(f"missing vHW0 output directory: {OUTPUT_DIR}")
    for name in REQUIRED:
        path = OUTPUT_DIR / name
        if not path.exists():
            errors.append(f"missing vHW0 artifact: {path}")
        elif path.stat().st_size == 0:
            errors.append(f"empty vHW0 artifact: {path}")
    if OUTPUT_DIR.exists():
        errors.extend(verify_manifest(OUTPUT_DIR))

    plan, plan_errors = load_json(OUTPUT_DIR / "telemetry_maintenance_validation_plan.json")
    protocol, protocol_errors = load_json(OUTPUT_DIR / "memory_vs_no_memory_telemetry_protocol.json")
    domains, domains_errors = load_json(OUTPUT_DIR / "candidate_domains.json")
    errors.extend(plan_errors + protocol_errors + domains_errors)

    if plan.get("status") != "planning_only":
        errors.append("vHW0 must remain planning_only")
    for key in ["physical_repair_performed", "physical_actuation_allowed", "autonomous_hardware_repair_claimed", "self_maintenance_claimed", "full_scoring_allowed"]:
        if plan.get(key) is not False:
            errors.append(f"vHW0 must keep {key} false")
    if "compare no-memory and memory-enabled" not in protocol.get("protocol", ""):
        errors.append("vHW0 telemetry protocol must define memory-vs-no-memory comparison")
    if "no_physical_actuation" not in protocol.get("required_checks", []):
        errors.append("vHW0 telemetry protocol must require no physical actuation")
    if len(domains.get("candidate_domains", [])) < 7:
        errors.append("vHW0 candidate domains must include the required telemetry families")
    errors.extend(require_text(OUTPUT_DIR / "safe_scope_boundary.md", ["no physical repair", "no hardware actuation", "no self-maintenance claim"]))
    errors.extend(require_text(OUTPUT_DIR / "claim_boundary.md", ["does not demonstrate hardware self-maintenance", "Future experiments must be replay-only"]))
    errors.extend(require_text(SUMMARY, ["vHW0 ControllerGate Telemetry Maintenance Validation Plan", "No hardware self-maintenance claim is made.", "No physical actuation"]))

    if errors:
        print("vHW0 ControllerGate telemetry maintenance plan audit: FAIL")
        for error in errors:
            print(f"- {error}")
        return 1
    print("vHW0 ControllerGate telemetry maintenance plan audit: PASS")
    print("planning only: true")
    print("physical actuation allowed: false")
    print("self-maintenance claim made: false")
    return 0


if __name__ == "__main__":
    sys.exit(main())
