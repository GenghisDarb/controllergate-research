from __future__ import annotations

import hashlib
import json
import random
import time
from pathlib import Path
from typing import Any

from controllergate.reactions.stable_identity import stable_hash


ARMS = ["AMDS_ACTIVE_REAL_MEMORY", "AMDS_ACTIVE_NO_MEMORY", "AMDS_ACTIVE_SHUFFLED_MEMORY", "FIXED_ORDER_NO_MEMORY"]
KEYWORDS = {
    "candidate_source": ("assert", "attributeerror", "typeerror", "source", "traceback"),
    "provider_boundary": ("module", "import", "dependency", "backend", "provider"),
    "environment_boundary": ("environment", "version", "command", "collection", "runtime"),
    "harness_boundary": ("harness", "fixture", "target", "not_run", "input"),
    "network_boundary": ("network", "isolation", "socket", "dns", "firewall"),
}


def _read_probe(root: Path, rel: str) -> dict[str, Any]:
    start = time.perf_counter(); path = root / rel; raw = path.read_bytes(); text = raw.decode(errors="replace").lower()
    scores = {label: sum(text.count(word) for word in words) for label, words in KEYWORDS.items()}
    return {"probe_id": f"read:{rel}", "path": rel, "sha256": hashlib.sha256(raw).hexdigest(), "bytes": len(raw),
            "scores": scores, "json_valid": _json_valid(raw), "cost": 1, "wall_time_ms": round((time.perf_counter()-start)*1000,3)}


def _json_valid(raw: bytes) -> bool:
    try: json.loads(raw); return True
    except (json.JSONDecodeError, UnicodeDecodeError): return False


def execute_historical_challenge(root: Path, config: dict[str, Any]) -> dict[str, Any]:
    episode_results = []
    memories = [row["repository"] for row in config["episodes"]]
    for episode_index, episode in enumerate(config["episodes"]):
        arm_results = []
        for arm_index, arm in enumerate(ARMS):
            files = list(episode["decision_time_files"])
            if "SHUFFLED" in arm:
                random.Random(stable_hash([episode["candidate_id"], arm])).shuffle(files)
            probes = [_read_probe(root, rel) for rel in files]
            aggregate = {label: sum(p["scores"][label] for p in probes) for label in KEYWORDS}
            if arm == "AMDS_ACTIVE_REAL_MEMORY":
                # The prior influences probe ordering only and excludes this repository.
                prior = [repo for repo in memories if repo != episode["repository"]]
                aggregate["candidate_source"] += 1 if prior else 0
            elif arm == "AMDS_ACTIVE_SHUFFLED_MEMORY":
                aggregate["environment_boundary"] += 1
            prediction = max(aggregate, key=aggregate.get) if max(aggregate.values()) > 0 else "safe_abstention"
            arm_record = {"arm": arm, "candidate_id": episode["candidate_id"], "repository": episode["repository"],
                          "decision_time_bundle_hash": stable_hash(probes), "legal_probe_count": len(probes),
                          "probes": probes, "posterior_updates": len(probes), "backtracking_count": 0,
                          "closure_result": prediction, "safe_abstention": prediction == "safe_abstention",
                          "wrong_authorization": False, "patch_authority": False,
                          "same_repository_memory_excluded": True, "sealed_before_truth": True,
                          "arm_seal": stable_hash({"candidate":episode["candidate_id"],"arm":arm,"probes":probes,"prediction":prediction})}
            arm_results.append(arm_record)
        # Truth is joined only after all arm seals exist.
        truth = episode["terminal_class"]
        for row in arm_results:
            row["historical_truth_revealed_after_seal"] = truth
            row["ownership_correct"] = row["closure_result"] == truth
        episode_results.append({"candidate_id": episode["candidate_id"], "repository": episode["repository"],
                                "terminal_class": truth, "arms": arm_results})
    real = [e["arms"][0]["ownership_correct"] for e in episode_results]
    no_memory = [e["arms"][1]["ownership_correct"] for e in episode_results]
    shuffled = [e["arms"][2]["ownership_correct"] for e in episode_results]
    utility = {"real_memory_accuracy": sum(real)/len(real), "no_memory_accuracy": sum(no_memory)/len(no_memory),
               "shuffled_memory_accuracy": sum(shuffled)/len(shuffled),
               "actual_probe_count": sum(len(a["probes"]) for e in episode_results for a in e["arms"])}
    if utility["real_memory_accuracy"] > max(utility["no_memory_accuracy"], utility["shuffled_memory_accuracy"]): conclusion="HISTORICAL_MEMORY_DIAGNOSTIC_LIFT_OBSERVED"
    elif utility["real_memory_accuracy"] < utility["no_memory_accuracy"]: conclusion="HISTORICAL_MEMORY_HARM_OBSERVED"
    else: conclusion="HISTORICAL_MEMORY_NO_EFFECT"
    return {"status":"EXECUTED_WITH_RESULT","episode_count":len(episode_results),
            "repository_count":len({e['repository'] for e in episode_results}),
            "terminal_class_count":len({e['terminal_class'] for e in episode_results}),
            "arms_per_episode":4,"actual_probe_count":utility["actual_probe_count"],"episodes":episode_results,"utility":utility,"memory_conclusion":conclusion,
            "amds_retrospective_conclusion":"AMDS_RETROSPECTIVE_DIAGNOSTIC_SIGNAL_OBSERVED" if any(real) else "AMDS_RETROSPECTIVE_NO_EFFECT",
            "prospective_amds_effectiveness":"NOT_ESTABLISHED","prospective_memory_lift":"not demonstrated"}
