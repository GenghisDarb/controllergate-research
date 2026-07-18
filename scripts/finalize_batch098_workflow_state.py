from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs" / "post_v2_37_hardening_batch098_causal_hypergraph_real_materialization_topology_probe_closure"


def read(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def write(name: str, value: dict) -> None:
    (OUT / name).write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--custody", required=True)
    parser.add_argument("--scientific", required=True)
    args = parser.parse_args()
    custody = Path(args.custody); scientific = Path(args.scientific); OUT.mkdir(parents=True, exist_ok=True)
    for source in list(custody.glob("*")) + list(scientific.glob("*")):
        if source.is_file():
            shutil.copy2(source, OUT / source.name)
    bridge = read(OUT / "tld_raw_ci_custody_v1.json")
    if bridge.get("status") != "PASS":
        raise SystemExit("BATCH098_TLD_SOURCE_CUSTODY_BRIDGE_BLOCKED_EXACT")
    gate = read(OUT / "eight_episode_materialization_gate_v2.json")
    quality_path = OUT / "amds_historical_quality_gate_v7.json"
    quality = read(quality_path) if quality_path.is_file() else {"status": "SCIENTIFIC_BLOCK", "exact_blocker": gate.get("exact_blocker") or "batch098_amds_not_executed"}
    blocker = "PROTECTED_HISTORICAL_ACTUATION_NOT_AUTHORIZED_AFTER_SCIENTIFIC_PASS" if quality.get("status") == "PASS" else quality.get("exact_blocker") or gate.get("exact_blocker") or "batch098_scientific_criteria_not_met"
    decision = {
        "status": "PRODUCT_BETA_RC_BLOCKED_EXACT",
        "exact_blockers": [blocker],
        "active_root_blockers": [blocker],
        "TLD_raw_CI_source_custody": "PASS",
        "eight_episode_materialization": gate.get("status"),
        "AMDS_quality": quality.get("status"),
        "ordinary_patch_operation_count": 0,
        "historical_count_increment": 0,
        "producer": "scripts.finalize_batch098_workflow_state",
        "execution_depth": "official_workflow_join",
        "authority_allowed": "internal release decision",
        "authority_forbidden": ["Product Beta PASS", "patch", "repair count", "release promotion"],
    }
    write("batch098_internal_release_decision.json", decision)
    consolidated = read(OUT / "batch098_consolidated_state.json")
    consolidated.update({"status": decision["status"], "root_blocker": blocker, "official_scientific_run": quality.get("status"), "TLD_raw_CI_source_custody": "PASS"})
    write("batch098_consolidated_state.json", consolidated)
    print(json.dumps({"status": decision["status"], "exact_blocker": blocker}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
