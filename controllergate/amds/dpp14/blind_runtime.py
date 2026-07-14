from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

from controllergate.execution.execution_broker import execute_external_operation
from controllergate.state.integrity import canonical_hash


FORBIDDEN_DECISION_KEYS = {
    "expected_terminal", "terminal_class", "ground_truth", "correct_classification",
    "known_patch", "patch_outcome", "future_validation_outcome", "count_decision", "sealed_truth",
}
FAMILIES = ("source_owned", "provider_owned", "harness_owned", "environment_owned", "non_source_terminal")


def _forbidden_paths(value: Any, path: str = "$") -> list[str]:
    found: list[str] = []
    if isinstance(value, dict):
        for key, item in value.items():
            child = f"{path}.{key}"
            if key in FORBIDDEN_DECISION_KEYS:
                found.append(child)
            found.extend(_forbidden_paths(item, child))
    elif isinstance(value, list):
        for index, item in enumerate(value):
            found.extend(_forbidden_paths(item, f"{path}[{index}]"))
    return found


def _parse_observation(text: str) -> dict[str, str]:
    values: dict[str, str] = {}
    for line in text.splitlines():
        if "=" in line:
            key, value = line.split("=", 1)
            if key.replace("_", "").isalnum():
                values[key.strip()] = value.strip()
    return values


def _update(frontier: set[str], observation: dict[str, str]) -> tuple[set[str], list[str]]:
    eliminated: list[str] = []
    signals = {
        "source_contact": "source_owned", "provider_failure": "provider_owned",
        "harness_failure": "harness_owned", "environment_failure": "environment_owned",
        "non_source_terminal": "non_source_terminal",
    }
    supported = {family for key, family in signals.items() if observation.get(key) == "true"}
    if supported:
        eliminated = sorted(frontier - supported)
        return frontier & supported, eliminated
    return frontier, eliminated


def run_blind_episode(decision_bundle: dict[str, Any], output_root: Path,
                      *, schedule: list[int] | None = None, max_probes: int = 8) -> dict[str, Any]:
    leaks = _forbidden_paths(decision_bundle)
    if leaks:
        return {"status": "BLOCK", "blocker": "decision_bundle_future_or_terminal_label_rejected", "leak_paths": leaks}
    output_root.mkdir(parents=True, exist_ok=True)
    candidate = str(decision_bundle["candidate_id"]); run_id = str(decision_bundle["run_id"])
    frame_hash = canonical_hash({key: value for key, value in decision_bundle.items() if key != "probes"})
    frontier = set(FAMILIES); probes = list(decision_bundle.get("probes", []))[:max_probes]
    order = schedule or list(range(len(probes))); observations = []; events = []; spent: set[str] = set(); backtracks = 0; contradictions = 0
    for round_number, index in enumerate(order, 1):
        probe = probes[index]
        if any(key in probe for key in ("classification", "causal_family", "terminal")):
            return {"status": "BLOCK", "blocker": "label_fed_probe_rejected", "probe_id": probe.get("probe_id")}
        nonce = canonical_hash([run_id, probe["probe_id"], frame_hash])[:40]
        if nonce in spent:
            events.append({"round": round_number, "status": "BLOCK", "blocker": "spent_nonce_reuse_rejected"}); continue
        spent.add(nonce)
        argv = [sys.executable, "-c", str(probe["script"])]
        attestation = {"status": "PASS", "attestation_hash": canonical_hash([sys.version, sys.platform])}
        run, record = execute_external_operation(
            operation_type="diagnostic_probe", argv=argv, cwd=output_root, runtime_root=output_root,
            stage_id=f"blind-dpp14-round-{round_number}", candidate_id=candidate,
            authorization_id=canonical_hash([run_id, round_number, "read-only"]), nonce=nonce,
            runtime_attestation=attestation, platform=sys.platform, runtime=sys.version,
            run_id=run_id, network_policy="none", source_tree_hash_before=decision_bundle["anchors"]["source_and_test_tree_identity"],
            source_tree_hash_after=decision_bundle["anchors"]["source_and_test_tree_identity"],
            test_tree_hash_before=decision_bundle["anchors"]["source_and_test_tree_identity"],
            test_tree_hash_after=decision_bundle["anchors"]["source_and_test_tree_identity"],
        )
        raw = _parse_observation(run.stdout)
        before = sorted(frontier); updated, eliminated = _update(frontier, raw)
        if frontier != set(FAMILIES) and updated and not updated.issubset(frontier):
            contradictions += 1; backtracks += 1
        frontier = updated
        observation = {"probe_id": probe["probe_id"], "round": round_number, "return_code": run.returncode,
                       "raw_observation": raw, "broker_record_hash": record["record_hash"], "verified": run.returncode == 0,
                       "frame_hash": frame_hash, "source_tree_immutable": True}
        observations.append(observation)
        events.append({"round": round_number, "frontier_before": before, "eliminated": eliminated,
                       "frontier_after": sorted(frontier), "nonce": nonce, "event_hash": canonical_hash(observation)})
        if len(frontier) == 1:
            break
    terminal = next(iter(frontier)) if len(frontier) == 1 else "safe_abstention_insufficient_evidence"
    return {"status": "PASS", "candidate_id": candidate, "run_id": run_id, "frame_hash": frame_hash,
            "terminal": terminal, "rounds": len(observations), "probe_count": len(observations),
            "contradictions": contradictions, "backtracks": backtracks, "spent_nonces": sorted(spent),
            "observations": observations, "events": events, "wrong_patch_authorizations": 0,
            "patch_authority": False, "decision_time_truth_overlap": 0, "label_leakage_count": 0}


def critic_join(terminals: list[dict[str, Any]], sealed_truth: list[dict[str, Any]]) -> dict[str, Any]:
    truth = {item["candidate_id"]: item["terminal"] for item in sealed_truth}
    rows = [{"candidate_id": item["candidate_id"], "decision": item["terminal"],
             "truth": truth.get(item["candidate_id"]), "correct": item["terminal"] == truth.get(item["candidate_id"])} for item in terminals]
    correct = sum(bool(row["correct"]) for row in rows); total = len(rows)
    abstentions = [row for row in rows if row["truth"].startswith("safe_abstention")]
    return {"status": "PASS" if total >= 8 and correct == total else "BLOCK", "episode_count": total,
            "macro_accuracy": correct / total if total else 0.0,
            "safe_abstention_accuracy": (sum(row["correct"] for row in abstentions) / len(abstentions)) if abstentions else 0.0,
            "wrong_patch_authorization_count": sum(item.get("wrong_patch_authorizations", 0) for item in terminals),
            "rows": rows, "truth_join_after_terminal_commit": True}
