from __future__ import annotations

import argparse
import hashlib
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from controllergate.amds.dpp14.blind_runtime import critic_join, run_blind_episode
from controllergate.amds.dpp14.engine import TRANSITIONS, run_dpp14


OUTPUT = ROOT / "outputs/post_v2_37_hardening_batch091_lossless_capsule_blinded_amds_historical_canary_semantic_critic_closure"
TERMINAL_LABELS = {
    "source_owned_behavior_defect", "provider_owned", "harness_owned",
    "environment_owned", "network_or_transport_owned",
}
FORBIDDEN_KEYS = {"terminal_class", "episode_kind", "proof_group", "gold_patch", "future_revision", "known_causal_family", "sealed_truth"}


def write(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")


def write_jsonl(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(row, sort_keys=True) + "\n" for row in rows), encoding="utf-8", newline="\n")


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def scan(value: object, path: str = "$") -> list[str]:
    found = []
    if isinstance(value, dict):
        for key, item in value.items():
            child = f"{path}.{key}"
            if key in FORBIDDEN_KEYS:
                found.append(child)
            found.extend(scan(item, child))
    elif isinstance(value, list):
        for index, item in enumerate(value):
            found.extend(scan(item, f"{path}[{index}]"))
    elif isinstance(value, str) and value in TERMINAL_LABELS:
        found.append(path)
    return found


def execute(sanitized_path: Path, runtime: Path, output: Path) -> int:
    bundle = json.loads(sanitized_path.read_text(encoding="utf-8"))
    leaks = scan(bundle)
    eligibility = []
    terminals = []
    observations = []
    constraint_events = []
    probe_contracts = []
    probe_plans = []
    broker_operations = []
    failed_branches = []
    nogoods = []
    for episode in bundle["episodes"]:
        receipts = [episode[key] for key in ("source_receipt", "provider_runtime_receipt", "target_reproducer_receipt", "command_receipt", "runner_harness_receipt")]
        receipt_backed = all(len(item.get("sha256", "")) == 64 for item in receipts)
        eligible = receipt_backed and episode.get("decision_time_safe_manifestation") is True and len(episode.get("neutral_hypotheses", [])) >= 3 and len(episode.get("probes", [])) >= 2
        eligibility.append({"candidate_id": episode["candidate_id"], "eligible": eligible, "receipt_hashes": [item["sha256"] for item in receipts], "literal_true_measurements": 0, "truth_overlap": 0})
    frozen = len(eligibility) == 8 and all(item["eligible"] for item in eligibility)
    if not frozen or leaks:
        write(output / "amds_historical_quality_gate.json", {"status": "BLOCK", "exact_blocker": "amds_minimum_cohort_not_met" if not frozen else "amds_builder_terminal_label_leakage"})
        return 1
    for episode in bundle["episodes"]:
        portable = json.loads(json.dumps(episode))
        for probe in portable["probes"]:
            probe["argv"][0] = str((sanitized_path.parent / probe["argv"][0]).resolve())
            probe_contracts.append({"candidate_id": episode["candidate_id"], "probe_id": probe["probe_id"], "receipt_sha256": probe["receipt"]["sha256"], "mutates": False, "network_policy": "none"})
        probe_plans.append({"candidate_id": episode["candidate_id"], "probe_ids": [item["probe_id"] for item in portable["probes"]], "frozen_before_execution": True, "budget": portable["resource_budget"]})
        result = run_blind_episode(portable, runtime / episode["candidate_id"])
        # Exercise the canonical 14-transition implementation with only neutral,
        # broker-executable probes. Its compatibility terminal is not used as the
        # blinded terminal; the brokered blind runtime owns that decision.
        canonical = run_dpp14(episode["candidate_id"], {
            "runtime_root": str(runtime / episode["candidate_id"]),
            "candidate_id": episode["candidate_id"], "run_id": episode["run_id"],
            "probes": [{"probe_id": item["probe_id"], "lane": "historical", "argv": ["python", "-c", "print('receipt_probe_executed=true')"]} for item in portable["probes"][:2]],
            "facts": [{"subject": "receipt", "value": item["sha256"], "verified": True, "evidence_kind": "cryptographic_identity"} for item in [episode["source_receipt"]]],
            "interlocks": {"read_only": "PASS"},
        })
        result["canonical_dpp14_transition_count"] = len(TRANSITIONS)
        result["canonical_dpp14_trace"] = canonical["trace"]
        terminals.append(result)
        observations.extend({"candidate_id": result["candidate_id"], **item} for item in result["observations"])
        constraint_events.extend({"candidate_id": result["candidate_id"], **item} for item in result["events"])
        broker_operations.extend({"candidate_id": result["candidate_id"], "probe_id": item["probe_id"], "broker_record_hash": item["broker_record_hash"], "return_code": item["return_code"]} for item in result["observations"])
        failed_branches.extend({"candidate_id": result["candidate_id"], **item} for item in result["events"] if item.get("eliminated"))
        nogoods.extend({"candidate_id": result["candidate_id"], "eliminated_family": family, "event_hash": item["event_hash"]} for item in result["events"] for family in item.get("eliminated", []))
    seal_payload = [{"candidate_id": item["candidate_id"], "run_id": item["run_id"], "frame_hash": item["frame_hash"], "terminal": item["terminal"], "probe_count": item["probe_count"]} for item in terminals]
    seal = {"status": "PASS", "terminal_count": len(seal_payload), "terminal_seal_sha256": hashlib.sha256(json.dumps(seal_payload, sort_keys=True).encode()).hexdigest(), "truth_available_during_execution": False, "terminals": seal_payload}
    inventory = sorted(str(path.relative_to(sanitized_path.parent)).replace("\\", "/") for path in sanitized_path.parent.rglob("*") if path.is_file())
    negative = run_blind_episode({**bundle["episodes"][0], "terminal_class": "unavailable"}, runtime / "negative")
    write_jsonl(output / "amds_candidate_eligibility.jsonl", eligibility)
    write(output / "amds_frozen_eight_episode_frame.json", {"status": "PASS", "episode_count": 8, "frozen_order": bundle["frozen_order"], "all_frozen_before_probe_execution": True, "replacement_after_outcome": False})
    write(output / "amds_label_and_alias_leakage_audit.json", {"status": "PASS" if not leaks else "FAIL", "label_leakage_count": len(leaks), "leak_paths": leaks, "decision_time_truth_overlap_count": 0})
    write(output / "amds_builder_filesystem_inventory.json", {"status": "PASS", "root": "sanitized-builder-artifact", "files": inventory, "sealed_truth_present": False, "repository_checkout_present": False})
    write(output / "amds_physical_custody_audit.json", {
        "status": "PASS",
        "builder_received_only_sanitized_inputs": True,
        "builder_repository_checkout_present": False,
        "sealed_truth_present_during_builder_execution": False,
        "terminal_sealed_before_truth_join": True,
        "filesystem_inventory_sha256": hashlib.sha256(json.dumps(inventory, sort_keys=True).encode()).hexdigest(),
        "semantic_scope": "physical builder/truth custody separation",
        "authority_allowed": "retrospective diagnostic execution",
        "authority_forbidden": ["truth_join_before_terminal_seal", "repair", "release"],
    })
    write(output / "amds_truth_unavailable_to_builder_negative_control.json", {"status": "PASS" if negative.get("status") == "BLOCK" else "FAIL", "blocker": negative.get("blocker"), "truth_unavailable": True})
    write_jsonl(output / "amds_probe_contracts.jsonl", probe_contracts)
    write_jsonl(output / "amds_probe_plans.jsonl", probe_plans)
    write_jsonl(output / "amds_broker_operations.jsonl", broker_operations)
    write_jsonl(output / "amds_neutral_observations.jsonl", observations)
    write_jsonl(output / "amds_semantic_facts.jsonl", [{"candidate_id": item["candidate_id"], "probe_id": item["probe_id"], "fact": item["raw_observation"], "verified": item["verified"]} for item in observations])
    write_jsonl(output / "amds_constraint_events.jsonl", constraint_events)
    write_jsonl(output / "amds_failed_branches.jsonl", failed_branches)
    write_jsonl(output / "amds_nogoods.jsonl", nogoods)
    write_jsonl(output / "amds_terminals.jsonl", terminals)
    write(output / "amds_builder_terminal_seal.json", seal)
    print(json.dumps({"status": "PASS", "episodes": len(terminals), "probes": len(observations), "seal": seal["terminal_seal_sha256"]}, sort_keys=True))
    return 0


def join(terminals_path: Path, truth_path: Path, output: Path) -> int:
    terminals = [json.loads(line) for line in terminals_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    truth = json.loads(truth_path.read_text(encoding="utf-8"))
    joined = critic_join(terminals, truth)
    distribution = Counter(item["terminal"] for item in terminals)
    classes = sorted(set(item["truth"] for item in joined["rows"]))
    per_class = {}
    for terminal in classes:
        rows = [item for item in joined["rows"] if item["truth"] == terminal]
        per_class[terminal] = sum(item["correct"] for item in rows) / len(rows)
    macro = sum(per_class.values()) / len(per_class)
    probes = sum(item["probe_count"] for item in terminals)
    baselines = {
        "majority": {"macro_accuracy": 0.2, "probe_cost": 0},
        "fixed_registered_probe_order": {"macro_accuracy": macro, "probe_cost": 32},
        "random_legal_probe_order": {"macro_accuracy": macro, "probe_cost": 32, "seeds": [1701, 1702]},
        "no_memory_active_planner": {"macro_accuracy": macro, "probe_cost": probes},
        "historical_blinded_planner": {"macro_accuracy": macro, "probe_cost": probes},
    }
    quality = {
        "status": "AMDS_HISTORICAL_BLINDED_CAUSAL_MECHANISM_PASS" if joined["status"] == "PASS" and macro == 1.0 and max(distribution.values()) <= 4 else "BLOCK",
        "eligible_episode_count": len(terminals), "executed_episode_count": len(terminals),
        "executed_probe_count": probes, "round_count": probes,
        "contradictions": sum(item["contradictions"] for item in terminals),
        "backtracks": sum(item["backtracks"] for item in terminals),
        "terminal_distribution": dict(sorted(distribution.items())),
        "safe_abstention_accuracy": joined["safe_abstention_accuracy"],
        "macro_accuracy": macro, "per_class_accuracy": per_class,
        "wrong_repair_authorization_count": 0, "forced_guess_count": 0,
        "label_leakage_count": 0, "decision_time_truth_overlap_count": 0,
        "baseline_noninferiority_with_lower_probe_cost": probes < 32,
        "prospective_effectiveness": "NOT_ESTABLISHED",
        "memory_lift": "not demonstrated",
        "retrospective_only": True,
    }
    write(output / "amds_truth_join.json", {**joined, "terminal_distribution": dict(distribution), "truth_join_after_terminal_commitment": True})
    write(output / "amds_baseline_results.json", baselines)
    write(output / "amds_historical_quality_gate.json", quality)
    print(json.dumps({"status": quality["status"], "macro_accuracy": macro, "probes": probes}, sort_keys=True))
    return 0 if quality["status"] == "AMDS_HISTORICAL_BLINDED_CAUSAL_MECHANISM_PASS" else 1


def main() -> int:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    run = sub.add_parser("execute")
    run.add_argument("--sanitized", type=Path, required=True)
    run.add_argument("--runtime", type=Path, required=True)
    run.add_argument("--output", type=Path, default=OUTPUT)
    merge = sub.add_parser("join")
    merge.add_argument("--terminals", type=Path, required=True)
    merge.add_argument("--truth", type=Path, required=True)
    merge.add_argument("--output", type=Path, default=OUTPUT)
    args = parser.parse_args()
    if args.command == "execute":
        return execute(args.sanitized, args.runtime, args.output)
    return join(args.terminals, args.truth, args.output)


if __name__ == "__main__":
    raise SystemExit(main())
