#!/usr/bin/env python3
"""Prepare vHW0 ControllerGate telemetry maintenance validation plan."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = REPO_ROOT / "outputs" / "vHW0_controllergate_telemetry_maintenance_plan"
SUMMARY = REPO_ROOT / "controllergate_v1_7_beta" / "reports" / "critic_review_package" / "shareable_summary.md"


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def sha_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_manifest(directory: Path) -> None:
    paths = sorted(
        [path for path in directory.rglob("*") if path.is_file() and path.name != "SHA256SUMS.txt"],
        key=lambda path: str(path.relative_to(directory)).replace("\\", "/"),
    )
    lines = [f"{sha_file(path)}  {str(path.relative_to(directory)).replace(chr(92), '/')}" for path in paths]
    write_text(directory / "SHA256SUMS.txt", "\n".join(lines) + "\n")


def update_summary() -> None:
    section = """## vHW0 ControllerGate Telemetry Maintenance Validation Plan

vHW0 is a planning-only replay protocol for future telemetry maintenance validation. It does not run physical hardware repair, does not perform actuation, and does not claim hardware self-maintenance.

- Status: planning only.
- Scope: diagnosis, recommendation, and replay evaluation over captured telemetry logs.
- Physical actuation: not allowed.
- Autonomous hardware repair: not allowed.
- Safety-critical deployment: not allowed.
- Self-maintenance claim: not made.
- Required future evidence: replay datasets, no-memory versus memory-enabled comparison, artifact custody, decision-time/outcome separation, and corruption/safety checks.

Full scoring remains disallowed. Self-maintaining software remains undemonstrated unless separately proven.

No hardware self-maintenance claim is made. No physical actuation is performed.
"""
    marker = "## vHW0 ControllerGate Telemetry Maintenance Validation Plan"
    text = SUMMARY.read_text(encoding="utf-8") if SUMMARY.exists() else ""
    if marker in text:
        text = text[: text.index(marker)].rstrip() + "\n\n" + section
    else:
        text = text.rstrip() + "\n\n" + section
    write_text(SUMMARY, text)


def main() -> int:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    domains = [
        "thermal_throttling_logs",
        "fan_pump_anomaly_logs",
        "battery_degradation_telemetry",
        "sensor_drift_detection",
        "robotics_simulator_fault_logs",
        "ci_runtime_resource_exhaustion_logs",
        "data_center_cooling_power_telemetry",
    ]
    write_json(
        OUTPUT_DIR / "telemetry_maintenance_validation_plan.json",
        {
            "plan_id": "vHW0_controllergate_telemetry_maintenance_validation_plan",
            "status": "planning_only",
            "purpose": "design future replayable telemetry-maintenance validation experiments",
            "physical_repair_performed": False,
            "physical_actuation_allowed": False,
            "autonomous_hardware_repair_claimed": False,
            "self_maintenance_claimed": False,
            "full_scoring_allowed": False,
            "future_validation_mode": "replay_only_no_memory_vs_memory_enabled_comparison",
        },
    )
    write_json(
        OUTPUT_DIR / "candidate_domains.json",
        {
            "candidate_domains": domains,
            "excluded_domains": ["live_physical_actuation", "security_exploit_tasks", "safety_critical_deployment"],
        },
    )
    write_text(
        OUTPUT_DIR / "safe_scope_boundary.md",
        "# vHW0 Safe Scope Boundary\n\nvHW0 is diagnosis/recommendation/replay planning only. It performs no physical repair, no hardware actuation, no autonomous robot maintenance, no safety-critical deployment, and no self-maintenance claim.\n",
    )
    write_json(
        OUTPUT_DIR / "replay_dataset_requirements.json",
        {
            "required_inputs": [
                "timestamped telemetry log",
                "baseline normal window",
                "fault or anomaly window",
                "environment/context metadata",
                "ground-truth outcome withheld from decision-time inputs",
                "safety/corruption check definition",
                "SHA256 artifact manifest",
            ],
            "forbidden_inputs_at_decision_time": [
                "post-outcome repair success labels",
                "future telemetry after decision boundary",
                "operator intervention notes generated after outcome",
                "unsafe actuation commands",
            ],
        },
    )
    write_json(
        OUTPUT_DIR / "memory_vs_no_memory_telemetry_protocol.json",
        {
            "protocol": "compare no-memory and memory-enabled maintenance recommendations under identical replay conditions",
            "no_memory_path": "uses only current telemetry episode decision-time inputs",
            "memory_enabled_path": "uses current telemetry episode decision-time inputs plus allowed prior ControllerGate memory",
            "required_checks": [
                "decision_time_outcome_separation",
                "artifact_custody",
                "recommendation_safety_check",
                "no_physical_actuation",
                "corruption_or_harm_risk_recorded",
            ],
            "scoreable_only_if": [
                "same replay dataset used by both paths",
                "same decision boundary used by both paths",
                "no future outcome leakage",
                "recommendations are auditable",
                "safety boundary remains intact",
            ],
        },
    )
    write_text(
        OUTPUT_DIR / "claim_boundary.md",
        "# vHW0 Claim Boundary\n\nControllerGate-HW is only a future telemetry diagnosis and recommendation validation plan. It does not demonstrate hardware self-maintenance, physical repair, autonomous actuation, safety-critical readiness, or self-maintaining software. Future experiments must be replay-only and compare no-memory versus memory-enabled maintenance decisions.\n",
    )
    write_text(
        OUTPUT_DIR / "campaign_summary.md",
        "# vHW0 ControllerGate Telemetry Maintenance Validation Plan\n\nvHW0 defines a replay-only telemetry-maintenance validation design. It is a sidecar planning artifact, not execution evidence. No physical actuation is performed and no hardware self-maintenance claim is made.\n",
    )
    write_manifest(OUTPUT_DIR)
    update_summary()
    print("vHW0 ControllerGate telemetry maintenance validation plan prepared")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
