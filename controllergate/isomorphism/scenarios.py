from __future__ import annotations

import hashlib
import json
import sqlite3
from pathlib import Path
from typing import Any

from .primitives import GENERIC_PRIMITIVES, PRIMITIVE_CONTRACTS, apply_primitive, conformance_event


CHAPTER_ENGINEERING_SCOPES = {
    "Autophagy": ["bounded cleanup", "capacity saturation", "proof-preserving recycling"],
    "Cell Cycle": ["phase state machine", "once-per-epoch license", "irreversible checkpoint"],
    "Cell-Cell communication": ["bidirectional handshake", "barrier integrity", "interface lifecycle"],
    "Cellular responses to stimuli": ["stress detection", "adaptive recovery", "duration-sensitive response"],
    "Chromatin organization": ["accessibility state", "local opening and closing", "access reset"],
    "Circadian clock": ["negative feedback oscillator", "phase drift", "resynchronization"],
    "Developmental Biology": ["lineage state", "competence window", "branch commitment"],
    "Digestion and absorption": ["stepwise decomposition", "selective admission", "capacity control"],
    "Disease": ["normal/variant pair", "first divergent event", "graded residual activity"],
    "DNA Repair": ["damage classification", "strategy selection", "post-repair seal"],
    "DNA Replication": ["frozen origin", "single epoch firing", "gap and overlap detection"],
    "Drug ADME": ["distribution", "transformation", "clearance and half-life"],
    "Extracellular matrix organization": ["load-bearing graph", "controlled remodeling", "orphan prevention"],
    "Gene expression (Transcription)": ["entrypoint selection", "ordered execution", "handoff"],
    "Hemostasis": ["localized breach", "bounded containment", "containment release"],
    "Immune System": ["pattern detection", "evidence presentation", "bounded response memory"],
    "Metabolism": ["resource graph", "rate-limiting flow", "feedback control"],
    "Metabolism of proteins": ["artifact maturation", "stall and collision rescue", "quality tags"],
    "Metabolism of RNA": ["processing lifecycle", "quality surveillance", "decay"],
    "Muscle contraction": ["resource-coupled actuator", "load stall", "reset and reuse"],
    "Neuronal System": ["event channels", "threshold", "refractory period"],
    "Organelle biogenesis and maintenance": ["subsystem genesis", "stoichiometric assembly", "identity health"],
    "Programmed Cell Death": ["controlled termination", "commit point", "terminated-product cleanup"],
    "Protein localization": ["target descriptor", "destination validation", "transport recycling"],
    "Reproduction": ["lineage transfer", "quality gate", "new authoritative generation"],
    "Sensory Perception": ["sensor calibration", "dynamic range", "multi-sensor fusion"],
    "Signal Transduction": ["event reception", "cascade routing", "termination"],
    "Transport of small molecules": ["selective flow", "directionality", "capacity and leak"],
    "Vesicle-mediated transport": ["cargo selection", "exactly-once delivery", "retrieval"],
}


def _hash(value: object) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def chapter_scenarios(source_by_chapter: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    chapters = list(CHAPTER_ENGINEERING_SCOPES)
    scenarios = []
    for index, chapter in enumerate(chapters):
        source = source_by_chapter[chapter]
        assigned = list(GENERIC_PRIMITIVES[index::len(chapters)])
        if not assigned:
            assigned = ["EVENT_CONTRACT"]
        for required in ("EVENT_CONTRACT", "ENTITY_STATE"):
            if required not in assigned:
                assigned.insert(0, required)
        scenarios.append({
            "scenario_id": f"reactome-r97-{index + 1:02d}",
            "chapter": chapter,
            "source_stable_id": source["stable_source_identity"],
            "source_occurrence_identity": source["source_occurrence_identity"],
            "engineering_scopes": CHAPTER_ENGINEERING_SCOPES[chapter],
            "primitive_ids": assigned,
            "negative_control": "missing_source_occurrence_identity",
            "authority": "shadow_non_authorizing",
        })
    return scenarios


def execute_scenario(scenario: dict[str, Any], database: str | Path, *, platform: str) -> dict[str, Any]:
    target = Path(database)
    target.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(target)
    connection.executescript("""
    CREATE TABLE IF NOT EXISTS scenario_events(event_id TEXT PRIMARY KEY, scenario_id TEXT, event_type TEXT, payload_json TEXT);
    CREATE TABLE IF NOT EXISTS mechanism_outcomes(outcome_id TEXT PRIMARY KEY, scenario_id TEXT, mechanism_status TEXT, payload_json TEXT);
    CREATE TABLE IF NOT EXISTS test_assertions(assertion_id TEXT PRIMARY KEY, outcome_id TEXT, assertion_status TEXT, payload_json TEXT);
    """)
    state: dict[str, Any] = {"primitive_trace": []}
    event = conformance_event()
    event["source_occurrence_identity"] = scenario["source_occurrence_identity"]
    results = []
    for primitive in scenario["primitive_ids"]:
        result = apply_primitive(primitive, state, event)
        results.append(result)
        if result["status"] == "PASS":
            state = result["state"]
    negative_results = []
    for primitive in scenario["primitive_ids"]:
        malformed = dict(event)
        malformed.pop(PRIMITIVE_CONTRACTS[primitive]["required_event_field"], None)
        negative_results.append(apply_primitive(primitive, state, malformed))
    negative = apply_primitive("EVENT_CONTRACT", state, {})
    mechanism_status = "PASS" if all(row["status"] == "PASS" for row in results) and all(row["status"] == "BLOCK" for row in negative_results) and negative["status"] == "BLOCK" else "FAIL"
    module_origin = str(Path(__file__).resolve())
    outcome = {"scenario_id": scenario["scenario_id"], "chapter": scenario["chapter"], "platform": platform, "mechanism_status": mechanism_status, "primitive_trace": state["primitive_trace"], "negative_control_status": negative["status"], "primitive_negative_controls": len(negative_results), "authority": "shadow_non_authorizing", "module_origin": module_origin, "installed_site_packages_origin": "site-packages" in module_origin.replace("\\", "/").lower()}
    event_id = _hash([scenario["scenario_id"], "event"]); outcome_id = _hash([scenario["scenario_id"], "outcome"]); assertion_id = _hash([scenario["scenario_id"], "assertion"])
    connection.execute("INSERT OR REPLACE INTO scenario_events VALUES (?,?,?,?)", (event_id, scenario["scenario_id"], "RPIR_SCENARIO_STARTED", json.dumps(scenario, sort_keys=True)))
    connection.execute("INSERT OR REPLACE INTO mechanism_outcomes VALUES (?,?,?,?)", (outcome_id, scenario["scenario_id"], mechanism_status, json.dumps(outcome, sort_keys=True)))
    connection.execute("INSERT OR REPLACE INTO test_assertions VALUES (?,?,?,?)", (assertion_id, outcome_id, "PASS" if mechanism_status == "PASS" else "FAIL", json.dumps({"expected": "PASS", "observed": mechanism_status}, sort_keys=True)))
    connection.commit(); connection.close()
    return outcome
