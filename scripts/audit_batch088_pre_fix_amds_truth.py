from __future__ import annotations

import argparse
import ast
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
BATCH087 = ROOT / "outputs" / (
    "post_v2_37_hardening_batch087_canonical_execution_blind_dpp14_"
    "product_beta_revalidation"
)


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def audit() -> dict[str, object]:
    runtime_path = ROOT / "controllergate" / "amds" / "dpp14" / "blind_runtime.py"
    runner_path = ROOT / "scripts" / "run_batch087_canonical_execution_blind_dpp14_product_beta_revalidation.py"
    runtime = runtime_path.read_text(encoding="utf-8")
    runner = runner_path.read_text(encoding="utf-8")
    ast.parse(runtime)
    ast.parse(runner)
    frames = load_json(BATCH087 / "blind_dpp14_decision_frame_registry.json")["frames"]
    terminals = [
        json.loads(line)
        for line in (BATCH087 / "blind_dpp14_terminal_registry.jsonl").read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    quality = load_json(BATCH087 / "blind_dpp14_quality_gate.json")
    schedule = load_json(BATCH087 / "blind_dpp14_schedule_determinism.json")
    interlock = load_json(BATCH087 / "proof_bound_interlock_audit.json")
    tld_projection = load_json(BATCH087 / "tld_three_projection_execution.json")
    tld_ablation = load_json(BATCH087 / "tld_projection_ablation.json")
    tld_curvature = load_json(BATCH087 / "tld_curvature_elbow_audit.json")
    semantic_proxy_terms = (
        "source_contact=true",
        "provider_failure=true",
        "harness_failure=true",
        "environment_failure=true",
        "non_source_terminal=true",
    )
    anchor_sets = [json.dumps(frame["anchors"], sort_keys=True) for frame in frames]
    defects = {
        "semantic_class_proxy_probe_scripts": all(term in runner for term in semantic_proxy_terms),
        "arbitrary_key_value_stdout_parser": 'if "=" in line' in runtime and "values[key.strip()]" in runtime,
        "generic_anchor_hashes_reused_across_candidates": len(set(anchor_sets)) == 1 and len(frames) == 8,
        "probe_definitions_excluded_from_frame_hash": 'if key != "probes"' in runtime,
        "one_directly_collapsing_probe_per_episode": all(len(frame.get("probes", [])) == 1 for frame in frames),
        "no_information_gain_or_minimax_planner": "information_gain" not in runtime and "minimax" not in runtime,
        "observation_verification_not_semantic": "verified\": run.returncode == 0" in runtime,
        "contradiction_backtracking_structurally_unreachable": "updated.issubset(frontier)" in runtime,
        "wrong_authorization_not_exercised": all(not row.get("patch_authority") for row in terminals)
        and quality.get("wrong_patch_authorization_count") == 0,
        "fixed_baseline_accuracy_constant": quality.get("fixed_baseline_accuracy") == 0.2
        and '"fixed_baseline_accuracy": 0.2' in runner,
        "schedule_controls_reported_without_complete_adversarial_execution": schedule.get(
            "delayed_duplicate_out_of_order_controls"
        )
        == "PASS"
        and "delayed_duplicate_out_of_order_controls\": \"PASS\"" in runner,
        "causal_elbow_inferred_from_terminal": '"episode_elbows": [{' in runner and 'item["terminal"]' in runner,
        "tld_projection_and_ablation_arrays_hand_authored": bool(tld_projection.get("projections"))
        and tld_ablation.get("one_projection") == 0.45
        and '"one_projection": 0.45' in runner,
        "tld_winner_uses_array_index_outside_registered_window": tld_curvature.get("winner_N") == 4
        and "index + 1" in runner,
        "historical_jobs_only_emit_attempted_block_records": all(
            load_json(BATCH087 / f"{name}_canonical_historical_lifecycle.json").get("status") == "BLOCK"
            for name in ("cloudpickle", "freezegun")
        ),
        "interlock_summary_not_independent_candidate_chains": interlock.get("verified_token_count") == 14
        and "negative_control" not in json.dumps(interlock.get("records", {})),
        "builder_and_truth_created_in_same_orchestration_process": "critic_join(terminals, truths)" in runner,
    }
    missing = sorted(name for name, present in defects.items() if not present)
    return {
        "critic": "scripts/audit_batch088_pre_fix_amds_truth.py",
        "defects": defects,
        "detected_defect_count": sum(bool(value) for value in defects.values()),
        "expected_defect_count": 17,
        "independent_from_batch087_builder": True,
        "imports_batch087_release_decision": False,
        "missing_preregistered_defects": missing,
        "starting_head": "f00bdc4a54786e20ac9cb6f82ed061b9af3cb2ec",
        "status": "BATCH088_PRE_FIX_AUDIT_FAIL_EXPECTED" if not missing else "UNEXPECTED_AUDIT_RESULT",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = audit()
    if args.output:
        write_json(args.output, result)
    print(json.dumps(result, sort_keys=True))
    return 0 if result["status"] == "BATCH088_PRE_FIX_AUDIT_FAIL_EXPECTED" else 1


if __name__ == "__main__":
    raise SystemExit(main())
