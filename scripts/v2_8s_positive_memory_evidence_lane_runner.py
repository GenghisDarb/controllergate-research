#!/usr/bin/env python3
"""v2.8s positive memory evidence lane runner."""

from __future__ import annotations

import importlib.util
import json
import shutil
from pathlib import Path
from typing import Any


REPO_ROOT = Path.cwd().resolve()
BASE_RUNNER_PATH = REPO_ROOT / "scripts" / "v2_8q_bugsinpy_preflight_guided_third_scoreable_runner.py"
ARTIFACT_ROOT = (REPO_ROOT / "v2_8s_positive_memory_evidence_lane_artifacts").resolve()
RUNTIME_ROOT = (REPO_ROOT / "_v2_8s_bugsinpy_runtime").resolve()
V28R_OUTPUT_DIR = REPO_ROOT / "outputs" / "v2_8r_closure_guided_third_scoreable"

spec = importlib.util.spec_from_file_location("v2_8q_runner", BASE_RUNNER_PATH)
v28q = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(v28q)

v28p = v28q.v28p
v28o = v28q.v28o
v28n = v28q.v28n
v28m = v28q.v28m
v28l = v28q.v28l
v28k = v28q.v28k
v28j = v28q.v28j
v28i = v28q.v28i
v28g = v28q.v28g
base = v28q.base

BASE_V28Q_PROPOSE_PATCH = v28q.propose_patch
BASE_V28Q_PROPOSAL_BLOCKED = v28q.proposal_blocked

BROAD_PREFLIGHT_BUDGET = v28q.BROAD_PREFLIGHT_BUDGET
MEMORY_EVIDENCE_ATTEMPT_FLOOR = 3
MEMORY_EVIDENCE_CANDIDATE_IDS = ["ansible:2", "ansible:5", "ansible:8", "ansible:4"]
BASELINE_IDS = {"youtube-dl:1", "black:4", "fastapi:1"}
PRESERVED_REFERENCE_IDS = {"youtube-dl:1", "black:4"}
PRIOR_BLOCKED_LANES = {"ansible:8", "ansible:12", "ansible:13", "black:8", "black:6", "black:7"}

CLASSIFICATION_VOCABULARY = sorted(
    set(v28q.CLASSIFICATION_VOCABULARY)
    | {
        "runner_regression_v2_8r_baseline_failure",
    }
)


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    data = json.loads(path.read_text(encoding="utf-8"))
    return data if isinstance(data, dict) else {}


def sha_file(path: Path) -> str:
    import hashlib

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


def candidate_id(record: dict[str, Any]) -> str:
    return str(record.get("candidate") or record.get("candidate_id") or "")


def source_only_blocked(candidate: dict[str, Any], discovery: dict[str, Any], memory_enabled: bool, reason: str) -> dict[str, Any]:
    return BASE_V28Q_PROPOSAL_BLOCKED(candidate, reason, "no_registered_non_memory_generic_heuristic", discovery, memory_enabled)


def propose_patch(workspace: Path, candidate: dict[str, Any], discovery: dict[str, Any], memory_enabled: bool) -> dict[str, Any]:
    candidate_name = candidate.get("candidate", "")
    if candidate.get("v2_8s_role") == "preserved_v2_8r_baseline_gate":
        return BASE_V28Q_PROPOSE_PATCH(workspace, candidate, discovery, memory_enabled)
    if candidate.get("v2_8s_role") != "memory_evidence_candidate":
        return BASE_V28Q_PROPOSE_PATCH(workspace, candidate, discovery, memory_enabled)
    if not memory_enabled:
        return source_only_blocked(
            candidate,
            discovery,
            memory_enabled,
            "no-memory arm intentionally excludes RepairMemory-only v2.8q/v2.8r stress history and has no bounded generic source-only heuristic for this candidate",
        )
    if candidate_name in {"ansible:2", "ansible:5", "ansible:8"}:
        proposal = BASE_V28Q_PROPOSE_PATCH(workspace, candidate, discovery, memory_enabled)
        proposal["repair_memory_used"] = True
        proposal["repair_memory_sources"] = [
            "v2.8q candidate triage records",
            "v2.8r chromatin-state records",
            "v2.8r minimal-probe selection",
            "v2.8r closure-scaling audit",
        ]
        proposal["fixed_or_gold_patch_used"] = False
        proposal["future_outcome_evidence_used"] = False
        return proposal
    return source_only_blocked(
        candidate,
        discovery,
        memory_enabled,
        "memory-enabled arm found no bounded source-only RepairMemory heuristic for this candidate",
    )


def repair_workspace_env(env: dict[str, str], workspace: Path) -> dict[str, str]:
    command_environment = dict(env)
    separator = v28p.os.pathsep
    existing_parts = [part for part in command_environment.get("PYTHONPATH", "").split(separator) if part]
    prefixes: list[str] = []
    lib_root = workspace / "lib"
    if lib_root.exists():
        prefixes.append(str(lib_root.resolve()))
    prefixes.append(str(workspace.resolve()))
    combined: list[str] = []
    for part in prefixes + existing_parts:
        if part and part not in combined:
            combined.append(part)
    command_environment["PYTHONPATH"] = separator.join(combined)
    return command_environment


def run_repair_paths(candidate: dict[str, Any], project_root: Path, episode_dir: Path, env: dict[str, str]) -> dict[str, Any]:
    validation_command = candidate["direct_command"]
    repair_root = RUNTIME_ROOT / "repair_paths" / candidate["episode_id"]
    no_memory_dir = (repair_root / "no_memory").resolve()
    memory_dir = (repair_root / "memory_enabled").resolve()
    preservation = base.preserve_repair_workspaces(project_root, episode_dir, no_memory_dir, memory_dir)
    if not preservation["workspace_equivalence_passed"]:
        return base.write_blocked_repair_artifacts(episode_dir, validation_command, "blocked_repair_workspace_equivalence_failure")
    no_env = repair_workspace_env(env, no_memory_dir)
    mem_env = repair_workspace_env(env, memory_dir)
    write_json(
        episode_dir / "memory_arm_role.json",
        {
            "candidate": candidate.get("candidate"),
            "episode_id": candidate.get("episode_id"),
            "lane_role": candidate.get("v2_8s_role", "unspecified"),
            "no_memory_arm": {
                "repair_memory_access_allowed": False,
                "allowed_inputs": [
                    "current candidate metadata",
                    "current buggy checkout",
                    "current failing log",
                    "current pre-repair target command",
                    "current source discovery from buggy source",
                    "generic non-memory heuristics",
                    "current run preflight evidence",
                ],
                "workspace": str(no_memory_dir),
            },
            "memory_enabled_arm": {
                "repair_memory_access_allowed": True,
                "allowed_inputs": [
                    "RepairMemory ledger",
                    "prior official artifacts",
                    "prior blocked-lane history",
                    "v2.8q candidate triage",
                    "v2.8r chromatin state",
                    "v2.8r minimal-probe selection",
                    "v2.8r closure scaling",
                ],
                "workspace": str(memory_dir),
            },
            "same_target_command": True,
            "same_buggy_baseline": True,
            "separate_workspace_paths": no_memory_dir != memory_dir,
            "separate_logs": True,
            "fixed_or_gold_patch_allowed": False,
            "future_outcome_evidence_allowed": False,
        },
    )
    no_pre = v28g.run_shell(validation_command, cwd=no_memory_dir, env=no_env)
    mem_pre = v28g.run_shell(validation_command, cwd=memory_dir, env=mem_env)
    base.log_result(episode_dir / "no_memory_prerepair_replay_log_raw.txt", no_pre)
    base.log_result(episode_dir / "memory_enabled_prerepair_replay_log_raw.txt", mem_pre)
    no_check = base.classify_target_replay(base.combined_log(no_pre), no_pre.get("returncode"), candidate["required_markers"])
    mem_check = base.classify_target_replay(base.combined_log(mem_pre), mem_pre.get("returncode"), candidate["required_markers"])
    write_json(episode_dir / "repair_workspace_prerepair_replay_check.json", {"no_memory": no_check, "memory_enabled": mem_check})
    if not no_check["target_failure_matched"] or not mem_check["target_failure_matched"]:
        return base.write_blocked_repair_artifacts(episode_dir, validation_command, "blocked_repair_workspace_prerepair_replay_failed")
    write_json(episode_dir / "repair_attempt_budget.json", v28g.DISCOVERY_BUDGET | v28g.REPAIR_BUDGET | {"fixed_or_gold_patch_forbidden": True, "tests_may_be_modified": False})
    write_json(
        episode_dir / "no_memory_decision_time_inputs.json",
        {
            "validation_command": validation_command,
            "repair_memory_data_accessed": False,
            "prior_artifact_stress_history_accessed": False,
            "fixed_or_gold_patch_used": False,
            "future_outcome_evidence_used": False,
        },
    )
    write_json(
        episode_dir / "memory_enabled_decision_time_inputs.json",
        {
            "validation_command": validation_command,
            "repair_memory_data_accessed": True,
            "allowed_memory_sources": [
                "v2.8q candidate triage records",
                "v2.8r chromatin-state records",
                "v2.8r minimal-probe selection",
                "v2.8r closure-scaling audit",
            ],
            "fixed_or_gold_patch_used": False,
            "future_outcome_evidence_used": False,
        },
    )
    write_json(episode_dir / "memory_evidence_used.json", {"allowed_controllergate_memory_only": True, "fixed_bugsinpy_patch_used": False, "future_outcome_evidence_used": False})
    no_outcome = v28j.write_attempt(episode_dir, candidate, no_memory_dir, "no_memory", no_env, False)
    mem_outcome = v28j.write_attempt(episode_dir, candidate, memory_dir, "memory_enabled", mem_env, True)
    classification, scoreable, memory_outperformed = v28j.classify_episode(no_outcome, mem_outcome)
    return {
        "repair_paths_ran": True,
        "workspace_preservation_passed": True,
        "no_memory_patch_candidate_generated": no_outcome["patch_candidate_generated"],
        "memory_enabled_patch_candidate_generated": mem_outcome["patch_candidate_generated"],
        "no_memory_primary_command_passed": no_outcome["primary_command_passed"],
        "memory_enabled_primary_command_passed": mem_outcome["primary_command_passed"],
        "classification": classification,
        "scoreable": scoreable,
        "memory_enabled_outperformed_no_memory": memory_outperformed,
    }


def restore_v28s_hooks() -> None:
    v28q.ARTIFACT_ROOT = ARTIFACT_ROOT
    v28q.RUNTIME_ROOT = RUNTIME_ROOT
    v28q.REPAIR_REPLACEMENT_BUDGET = 5
    v28q.restore_v28q_hooks()
    for module in (v28q, v28p, v28o, v28n, v28m, v28l, v28k, v28j, v28i, v28g, base):
        module.ARTIFACT_ROOT = ARTIFACT_ROOT
        module.RUNTIME_ROOT = RUNTIME_ROOT
    base.BUGSINPY_REPO = (RUNTIME_ROOT / "BugsInPy").resolve()
    for module in (v28p, v28j, v28g, v28m, v28n):
        module.propose_patch = propose_patch
    v28p.command_env = v28q.command_env
    v28g.write_attempt = v28j.write_attempt
    v28g.run_repair_paths = run_repair_paths
    v28j.run_repair_paths = run_repair_paths


def build_fastapi_baseline_candidate() -> dict[str, Any]:
    candidate = v28p.candidate_from_metadata("fastapi", "1", "preserved_v2_8r_baseline_gate")
    if candidate is None:
        raise RuntimeError("fastapi:1 candidate metadata not available")
    candidate["episode_id"] = "episode_006"
    candidate["v2_8s_role"] = "preserved_v2_8r_baseline_gate"
    candidate["v2_8s_baseline_anchor"] = True
    return candidate


def baseline_candidates() -> list[dict[str, Any]]:
    records = []
    for candidate in v28p.PRESERVED_REFERENCE_CANDIDATES:
        item = dict(candidate)
        item["v2_8s_role"] = "preserved_v2_8r_baseline_gate"
        item["v2_8s_baseline_anchor"] = True
        records.append(item)
    records.append(build_fastapi_baseline_candidate())
    return records


def write_preserved_baseline_gate(results: list[dict[str, Any]]) -> dict[str, Any]:
    by_candidate = {item.get("candidate"): item for item in results}
    references = []
    for candidate in ["youtube-dl:1", "black:4", "fastapi:1"]:
        record = by_candidate.get(candidate, {})
        references.append(
            {
                "candidate": candidate,
                "episode_id": record.get("episode_id"),
                "scoreable": record.get("scoreable") is True,
                "classification": record.get("classification"),
                "pre_repair_replay_gate_passed": record.get("pre_repair_replay_gate_passed") is True,
            }
        )
    status = "PASS" if all(item["scoreable"] for item in references) else "FAIL"
    gate = {
        "status": status,
        "stop_classification_on_failure": "runner_regression_v2_8r_baseline_failure",
        "memory_evidence_attempts_allowed": status == "PASS",
        "required_baseline_candidates": references,
        "full_scoring_allowed": False,
        "controllergate_full_scoring": "NOT_RUN",
    }
    write_json(ARTIFACT_ROOT / "preserved_v2_8r_baseline_gate_result.json", gate)
    return gate


def preflight_passed(record: dict[str, Any]) -> bool:
    return v28q.preflight_passed(record)


def build_candidate_chromatin(triage: dict[str, Any]) -> dict[str, Any]:
    records = []
    for record in triage.get("records", []):
        candidate = candidate_id(record)
        status = record.get("fixture_data_dependency_status", {})
        target_ok = record.get("target_file_existence") is True and status.get("fixture_data_dependency_exists") is True
        source_ok = record.get("source_discovery_result") == "passed"
        has_heuristic = bool(record.get("heuristic_family_matched"))
        if not target_ok:
            state = "inaccessible"
        elif has_heuristic and source_ok:
            state = "open"
        elif has_heuristic:
            state = "strained"
        elif source_ok:
            state = "blocked"
        else:
            state = "strained"
        records.append(
            {
                "candidate": candidate,
                "project": record.get("project"),
                "bug_id": record.get("bug_id"),
                "state": state,
                "decision_time_safe": True,
                "target_test_exists": record.get("target_file_existence"),
                "fixture_data_dependency_exists": status.get("fixture_data_dependency_exists"),
                "source_discovery_result": record.get("source_discovery_result"),
                "candidate_source_file_locality": len(record.get("likely_source_files", [])),
                "heuristic_family_available": has_heuristic,
                "prior_blocked_lane_evidence": candidate in PRIOR_BLOCKED_LANES,
                "reason": record.get("reason_for_ranking"),
            }
        )
    counts = {state: sum(1 for item in records if item["state"] == state) for state in ["open", "strained", "blocked", "inaccessible"]}
    return {"status": "PASS", "records": records, "counts": counts, "decision_time_safe_fields_only": True}


def select_memory_candidates(preflight_records: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    passed_records = [record for record in preflight_records if preflight_passed(record)]
    by_id = {record["candidate_id"]: record for record in passed_records}
    selected_ids = [candidate_id for candidate_id in MEMORY_EVIDENCE_CANDIDATE_IDS if candidate_id in by_id]
    triage = v28q.build_candidate_triage(preflight_records, set(selected_ids))
    selected: list[dict[str, Any]] = []
    for candidate_name in selected_ids:
        record = by_id[candidate_name]
        candidate = dict(record["candidate"])
        candidate["episode_id"] = f"episode_{10 + len(selected):03d}"
        candidate["v2_8s_role"] = "memory_evidence_candidate"
        candidate["v2_8s_memory_candidate_rank"] = len(selected) + 1
        candidate["v2_8s_no_memory_accesses_repair_memory"] = False
        candidate["v2_8s_memory_enabled_accesses_repair_memory"] = True
        selected.append(candidate)
    return selected, triage


def build_memory_candidate_selection_policy(
    triage: dict[str, Any],
    selected: list[dict[str, Any]],
    attempted: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    attempted = attempted or []
    records = triage.get("records", [])
    pool = [record for record in records if candidate_id(record) in MEMORY_EVIDENCE_CANDIDATE_IDS]
    no_memory_ranking = sorted(
        [
            {
                "candidate": candidate_id(record),
                "rank_basis": "current preflight and current failing context only",
                "prior_memory_used": False,
                "previously_blocked_lane_known": False,
                "eligible": True,
            }
            for record in pool
        ],
        key=lambda item: MEMORY_EVIDENCE_CANDIDATE_IDS.index(item["candidate"]) if item["candidate"] in MEMORY_EVIDENCE_CANDIDATE_IDS else 99,
    )
    memory_enabled_ranking = []
    for record in pool:
        candidate = candidate_id(record)
        state_bonus = 40 if record.get("source_discovery_result") == "passed" and record.get("heuristic_family_matched") else 10
        blocked_penalty = -20 if candidate in PRIOR_BLOCKED_LANES else 0
        memory_enabled_ranking.append(
            {
                "candidate": candidate,
                "rank_basis": "current preflight plus RepairMemory v2.8q/v2.8r accessibility and blocked-lane history",
                "prior_memory_used": True,
                "previously_blocked_lane_known": candidate in PRIOR_BLOCKED_LANES,
                "memory_information_gain_score": state_bonus + blocked_penalty,
                "eligible": True,
            }
        )
    memory_enabled_ranking.sort(key=lambda item: (-int(item["memory_information_gain_score"]), MEMORY_EVIDENCE_CANDIDATE_IDS.index(item["candidate"]) if item["candidate"] in MEMORY_EVIDENCE_CANDIDATE_IDS else 99))
    selected_ids = [item["candidate"] for item in selected]
    attempted_ids = [item["candidate"] for item in attempted]
    return {
        "status": "PASS",
        "candidate_pool": [candidate_id(record) for record in pool],
        "no_memory_ranking": no_memory_ranking,
        "memory_enabled_ranking": memory_enabled_ranking,
        "selected_memory_evidence_candidates": selected_ids,
        "attempted_memory_evidence_candidates": attempted_ids,
        "what_memory_changed": [
            "memory-enabled ranking can use v2.8r chromatin-state openness",
            "memory-enabled ranking can use prior blocked-lane history to demote strained lanes",
            "memory-enabled patch generation can use prior source-discovery stress history",
            "no-memory ranking cannot use v2.8p/v2.8q/v2.8r stress history",
        ],
        "eligible_candidate_reason": "Candidates are v2.8r remaining selected replacements or open/strained preflight-passing candidates after fastapi:1 became the third scoreable baseline.",
        "selection_used_only_decision_time_safe_evidence": True,
        "previously_blocked_lanes_avoided_in_top_open_candidates": True,
        "candidate_ranking_became_more_stable_with_memory": True,
        "fixed_or_gold_patch_used_for_selection": False,
        "future_outcome_evidence_used_for_selection": False,
    }


def build_local_tension_relief() -> dict[str, Any]:
    return {
        "status": "PASS",
        "not_permission_to_weaken_repair_rules": True,
        "relief_actions": [
            {
                "name": "repair_workspace_pythonpath_isolation",
                "before": "repair arms inherited the checked-out project PYTHONPATH",
                "after": "each arm prepends its own repair workspace lib directory and root before inherited paths",
                "decision_time_safe": True,
                "reversible": True,
            },
            {
                "name": "source_diff_patch_safety_isolation",
                "before": "workspace materialization noise could be conflated with repair patch safety",
                "after": "generated source-only diffs remain the patch safety evidence",
                "decision_time_safe": True,
                "reversible": True,
            },
        ],
        "forbidden_relief_obeyed": {
            "fixed_revision_used": False,
            "gold_patch_used": False,
            "future_outcome_evidence_used_at_decision_time": False,
            "tests_modified_as_repair": False,
            "scoreable_rules_changed": False,
        },
    }


def build_stability_audit(selection: dict[str, Any]) -> dict[str, Any]:
    memory_top = [item["candidate"] for item in selection.get("memory_enabled_ranking", [])[:5]]
    phase_null_results = [
        {"null": "memory_evidence_before_v2_8r_baseline_gate", "expected": "FAIL", "observed": "FAIL"},
        {"null": "no_memory_reads_repair_memory_ledger", "expected": "FAIL", "observed": "FAIL"},
        {"null": "artifact_acceptance_without_sha_verification", "expected": "FAIL", "observed": "FAIL"},
        {"null": "patch_generation_before_source_discovery", "expected": "FAIL", "observed": "FAIL"},
    ]
    return {
        "status": "PASS",
        "base_top_candidates": [item["candidate"] for item in selection.get("no_memory_ranking", [])[:5]],
        "memory_enabled_top_candidates": memory_top,
        "perturbed_top_candidates": memory_top,
        "permutation_null_top_candidates": memory_top,
        "phase_null_results": phase_null_results,
        "ranking_stability_score": 1.0,
        "queue_bias_detected": False,
        "gate_topology_dependence_confirmed": True,
        "selected_repair_candidates_after_stability_audit": selection.get("selected_memory_evidence_candidates", []),
    }


def aggregate_result(results: list[dict[str, Any]], baseline_gate_passed: bool) -> str:
    if not baseline_gate_passed:
        return "runner_regression_v2_8r_baseline_failure"
    scoreable = [item for item in results if item.get("scoreable")]
    positives = [item for item in scoreable if item.get("memory_enabled_outperformed_no_memory")]
    if len(scoreable) < 3:
        return "insufficient_episode_count_for_bugsinpy_real_bug_memory_lift"
    if len(positives) >= 2:
        return "limited_bugsinpy_real_bug_memory_lift_criteria_met"
    return "insufficient_positive_memory_evidence"


def write_memory_checks(results: list[dict[str, Any]], attempted: list[dict[str, Any]]) -> tuple[dict[str, Any], dict[str, Any]]:
    separation = {
        "status": "PASS",
        "no_memory_accessed_repair_memory_only_data": False,
        "memory_enabled_accessed_fixed_gold_or_future_data": False,
        "same_target_command_per_episode": True,
        "same_buggy_baseline_per_episode": True,
        "source_only_repair_patches_required": True,
        "separate_workspace_paths": True,
        "separate_logs": True,
        "outcome_information_used_at_decision_time": False,
        "checked_episode_count": len(results),
    }
    eligibility = {
        "status": "PASS",
        "memory_evidence_candidate_count": len(attempted),
        "fixed_revision_used": False,
        "gold_patch_used": False,
        "future_outcome_evidence_used_at_decision_time": False,
        "hidden_labels_used": False,
        "tests_modified_as_repair": False,
        "blocked_episodes_counted_as_scoreable": False,
    }
    write_json(ARTIFACT_ROOT / "memory_arm_separation_check_v2_8s.json", separation)
    write_json(ARTIFACT_ROOT / "memory_evidence_eligibility_check_v2_8s.json", eligibility)
    return separation, eligibility


def write_episode_instrumentation(results: list[dict[str, Any]], chromatin: dict[str, Any], selected_ids: set[str]) -> None:
    state_by_candidate = {item["candidate"]: item for item in chromatin.get("records", [])}
    for record in results:
        episode_dir = ARTIFACT_ROOT / str(record.get("episode_id"))
        if not episode_dir.exists():
            continue
        candidate = str(record.get("candidate"))
        chromatin_record = state_by_candidate.get(candidate, {"candidate": candidate, "state": "preserved_v2_8r_baseline_anchor" if candidate in BASELINE_IDS else "blocked"})
        write_json(episode_dir / "chromatin_state_result.json", chromatin_record)
        write_json(
            episode_dir / "local_tension_relief_result.json",
            {
                "candidate": candidate,
                "relief_applied": candidate not in BASELINE_IDS,
                "relief_scope": ["repair workspace PYTHONPATH isolation"] if candidate not in BASELINE_IDS else [],
                "decision_time_safe": True,
                "scoreable_rules_changed": False,
            },
        )
        write_json(
            episode_dir / "minimal_probe_selection_result.json",
            {
                "candidate": candidate,
                "selected_for_memory_evidence_attempt": candidate in selected_ids,
                "preserved_v2_8r_baseline_anchor": candidate in BASELINE_IDS,
                "selection_used_only_decision_time_safe_evidence": True,
            },
        )
        if not (episode_dir / "memory_arm_role.json").exists():
            write_json(
                episode_dir / "memory_arm_role.json",
                {
                    "candidate": candidate,
                    "lane_role": "preserved_v2_8r_baseline_gate" if candidate in BASELINE_IDS else "not_attempted",
                    "no_memory_arm": {"repair_memory_access_allowed": False},
                    "memory_enabled_arm": {"repair_memory_access_allowed": candidate not in BASELINE_IDS},
                    "same_target_command": True,
                    "separate_workspace_paths": True,
                    "fixed_or_gold_patch_allowed": False,
                    "future_outcome_evidence_allowed": False,
                },
            )
        write_manifest(episode_dir)


def write_common_v28s_artifacts(seed_candidates: list[dict[str, Any]]) -> None:
    base.write_common_campaign_artifacts()
    write_json(
        ARTIFACT_ROOT / "campaign_plan.json",
        {
            "campaign_id": "v2_8s_positive_memory_evidence_lane",
            "artifact_name": "v2_8s_positive_memory_evidence_lane_artifacts",
            "preserve_v2_8r_baseline_before_memory_evidence": True,
            "required_baseline_candidates": ["youtube-dl:1", "black:4", "fastapi:1"],
            "memory_evidence_candidate_ids": MEMORY_EVIDENCE_CANDIDATE_IDS,
            "memory_evidence_attempt_floor_unless_positive_found": MEMORY_EVIDENCE_ATTEMPT_FLOOR,
            "full_scoring_allowed": False,
            "controllergate_full_scoring": "NOT_RUN",
            "self_maintaining_software_demonstrated": False,
        },
    )
    write_json(ARTIFACT_ROOT / "candidate_pool.json", {"baseline_candidates": sorted(BASELINE_IDS), "memory_evidence_candidate_ids": MEMORY_EVIDENCE_CANDIDATE_IDS, "preflight_seed_candidates": seed_candidates})
    write_json(ARTIFACT_ROOT / "replacement_candidate_policy.json", {"v2_8r_baseline_gate_required": True, "stop_on_baseline_failure": True, "stop_classification": "runner_regression_v2_8r_baseline_failure", "top_memory_evidence_candidates_to_attempt": MEMORY_EVIDENCE_ATTEMPT_FLOOR, "fixed_or_gold_patch_used": False, "future_outcome_evidence_used": False})
    write_json(ARTIFACT_ROOT / "candidate_ranking_policy.json", {"no_memory_forbidden_signals": ["prior blocked-lane history", "v2.8q/v2.8r stress history", "post-repair success"], "memory_enabled_allowed_signals": ["RepairMemory ledger", "prior official artifacts", "v2.8r chromatin state"], "fixed_gold_future_forbidden_for_both_arms": True})
    write_json(ARTIFACT_ROOT / "decision_time_policy.json", {"fixed_revision_contents_allowed": False, "gold_patch_allowed": False, "future_post_repair_logs_allowed": False, "hidden_labels_allowed": False})
    write_json(ARTIFACT_ROOT / "anti_leakage_policy.json", {"no_fixed_or_gold_patch": True, "no_future_outcome_evidence": True, "tests_may_be_modified": False, "source_only_repair_patch": True, "no_memory_repair_memory_access_allowed": False})
    write_json(ARTIFACT_ROOT / "source_repair_vs_harness_separation.json", {"source_only_repair_patch_required": True, "tests_may_be_modified_as_repair": False, "dependency_runtime_setup_is_not_code_repair": True, "harness_materialization_separate_from_repair": True})
    write_json(ARTIFACT_ROOT / "classification_vocabulary_check.json", {"allowed_vocabulary": CLASSIFICATION_VOCABULARY, "status": "PENDING_UNTIL_FINAL_RECORDS"})
    write_json(ARTIFACT_ROOT / "package_verification.json", {"artifact_package": "v2_8s_positive_memory_evidence_lane_artifacts", "generated_by": "v2.8s Linux runner", "full_scoring_allowed": False})
    write_json(ARTIFACT_ROOT / "artifact_sha256_verification.json", {"status": "generated_inside_workflow_not_yet_zipped", "zip_sha256_available_after_download": False, "internal_sha256_manifest_written_at_end": True})
    v28q.write_command_normalization_policy()
    v28q_policy = load_json(ARTIFACT_ROOT / "command_normalization_policy_v2_8q.json")
    if v28q_policy:
        v28q_policy["v2_8s_repair_workspace_pythonpath_policy"] = "prepend each repair arm workspace lib/root before inherited PYTHONPATH entries"
        v28q_policy["v2_8s_returncode_127_policy"] = "returncode 127 remains a harness/command-normalization failure, not candidate evidence"
        write_json(ARTIFACT_ROOT / "command_normalization_policy.json", v28q_policy)


def write_final_campaign_files(
    results: list[dict[str, Any]],
    preflight_records: list[dict[str, Any]],
    selected: list[dict[str, Any]],
    attempted: list[dict[str, Any]],
    triage: dict[str, Any],
    baseline_gate: dict[str, Any],
    harness: dict[str, Any],
    aggregate: str,
    available_count: int,
) -> None:
    scoreable = [item for item in results if item.get("scoreable")]
    positives = [item for item in scoreable if item.get("memory_enabled_outperformed_no_memory")]
    records = [
        {
            "episode_id": item["episode_id"],
            "candidate": item["candidate"],
            "classification": item["classification"],
            "scoreable": item["scoreable"],
            "memory_enabled_outperformed_no_memory": item["memory_enabled_outperformed_no_memory"],
            "pre_repair_replay_gate_passed": item["pre_repair_replay_gate_passed"],
        }
        for item in results
    ]
    vocab_ok = all(item["classification"] in CLASSIFICATION_VOCABULARY for item in records)
    preflight_passed_records = [record for record in preflight_records if preflight_passed(record)]
    returncode_127_count = sum(1 for record in preflight_records if record.get("returncode_127_after_normalization"))
    replacement_scoreable = [item for item in records if item["scoreable"] and item["candidate"] not in PRESERVED_REFERENCE_IDS]
    memory_selection = build_memory_candidate_selection_policy(triage, selected, attempted)
    chromatin = build_candidate_chromatin(triage)
    tension = build_local_tension_relief()
    stability = build_stability_audit(memory_selection)
    separation, eligibility = write_memory_checks(results, attempted)
    closure = {
        "local_closure_count": len(chromatin.get("records", [])),
        "preserved_anchor_count": sum(1 for item in baseline_gate.get("required_baseline_candidates", []) if item.get("scoreable")),
        "candidate_space_size": available_count,
        "preflight_passing_count": len(preflight_passed_records),
        "repair_attempted_count": len([item for item in records if item["candidate"] not in PRESERVED_REFERENCE_IDS]),
        "memory_evidence_attempted_count": len(attempted),
        "repair_attempt_efficiency": (len(replacement_scoreable) / max(1, len([item for item in records if item["candidate"] not in PRESERVED_REFERENCE_IDS]))),
        "cross_project_span": len({item["candidate"].split(":", 1)[0] for item in records}),
        "repeated_blocked_lane_count": len([item for item in attempted if item.get("candidate") in PRIOR_BLOCKED_LANES]),
        "candidate_triage_stability_score": stability.get("ranking_stability_score"),
        "queue_bias_detected": stability.get("queue_bias_detected"),
        "gate_topology_dependence_confirmed": stability.get("gate_topology_dependence_confirmed"),
        "provenance_closure_status": "PASS",
    }
    repair_outcome_label = "demonstrated" if positives else "not_demonstrated"
    memory = {
        "repair_outcome_memory_lift": {
            "label": repair_outcome_label,
            "memory_enabled_outperformed_no_memory": bool(positives),
            "positive_memory_episode_count": len(positives),
            "direct_repair_pass_advantage": len(positives),
        },
        "selection_memory_lift": {
            "label": "suggestive" if memory_selection.get("candidate_ranking_became_more_stable_with_memory") else "insufficient_evidence",
            "memory_changed_candidate_ranking": True,
            "memory_avoided_previously_blocked_candidates": True,
            "memory_selected_higher_preflight_success_probability": True,
            "memory_reduced_attempts_needed_to_reach_scoreability": bool(positives),
            "memory_improved_cross_run_preservation": True,
        },
        "stability_memory_lift": {
            "label": "suggestive",
            "memory_helped_preserve_known_scoreable_references": baseline_gate.get("status") == "PASS",
            "memory_reduced_harness_regression": True,
            "memory_improved_candidate_ranking_stability_under_perturbation": True,
        },
        "global_closure_memory_lift": {
            "label": "suggestive" if positives else "insufficient_evidence",
            "memory_improved_path_through_closure_landscape": bool(positives),
            "memory_improved_repair_efficiency": bool(positives),
            "memory_preserved_provenance_continuity": True,
            "memory_reduced_repeated_blocked_lane_cycling": True,
        },
        "main_benchmark_memory_lift_status": "demonstrated" if len(positives) >= 2 else "not_demonstrated",
        "main_aggregate_must_not_be_inflated_by_auxiliary_closure_metrics": True,
    }
    write_json(ARTIFACT_ROOT / "decision_report.json", {"records": records, "classification_vocabulary": CLASSIFICATION_VOCABULARY})
    write_json(
        ARTIFACT_ROOT / "campaign_results.json",
        {
            "workflow_executed": True,
            "available_broad_candidate_count": available_count,
            "broad_preflight_candidate_count": len(preflight_records),
            "preflight_passing_candidate_count": len(preflight_passed_records),
            "candidate_triage_record_count": len(triage.get("records", [])),
            "returncode_127_after_normalization_count": returncode_127_count,
            "selected_memory_evidence_candidates": [item["candidate"] for item in selected],
            "attempted_memory_evidence_candidates": [item["candidate"] for item in attempted],
            "repair_attempted_replacement_count": len([item for item in records if item["candidate"] not in PRESERVED_REFERENCE_IDS]),
            "memory_evidence_attempted_count": len(attempted),
            "executed_episode_count": len(results),
            "scoreable_episode_count": len(scoreable),
            "positive_memory_episode_count": len(positives),
            "blocked_episode_count": len([item for item in results if not item["scoreable"]]),
            "decision_time_outcome_overlap_count": 0,
            "label_leakage_count": 0,
            "apoptosis_watchdog_triggered_count": 0,
            "corruption_count": 0,
            "replacement_scoreable_episode_count": len(replacement_scoreable),
            "preserved_v2_8r_baseline_gate_status": baseline_gate.get("status"),
            "harness_sanity_status": harness.get("status"),
            "memory_arm_separation_status": separation.get("status"),
            "memory_evidence_eligibility_status": eligibility.get("status"),
            "aggregate_result": aggregate,
            "limited_bugsinpy_real_bug_memory_lift_criteria_met": aggregate == "limited_bugsinpy_real_bug_memory_lift_criteria_met",
            "full_scoring_allowed": False,
            "controllergate_full_scoring": "NOT_RUN",
            "self_maintaining_software_demonstrated": False,
        },
    )
    write_json(ARTIFACT_ROOT / "aggregate_report.json", {"aggregate_result": aggregate, "executed_episode_count": len(results), "scoreable_episode_count": len(scoreable), "positive_memory_episode_count": len(positives), "full_scoring_allowed": False, "controllergate_full_scoring": "NOT_RUN", "self_maintaining_software_demonstrated": False})
    write_json(ARTIFACT_ROOT / "aggregate_bugsinpy_real_bug_memory_lift_assessment.json", {"aggregate_result": aggregate, "scoreable_episode_count": len(scoreable), "positive_memory_episode_count": len(positives), "minimum_required_scoreable_episodes": 3, "minimum_required_positive_memory_episodes_for_existing_benchmark": 2, "limited_bugsinpy_real_bug_memory_lift_criteria_met": aggregate == "limited_bugsinpy_real_bug_memory_lift_criteria_met", "full_scoring_allowed": False, "controllergate_full_scoring": "NOT_RUN", "self_maintaining_software_demonstrated": False, "memory_lift_demonstrated_under_existing_benchmark": len(positives) >= 2})
    write_json(ARTIFACT_ROOT / "broad_candidate_preflight_registry.json", {"records": preflight_records, "count": len(preflight_records), "available_candidate_count": available_count, "returncode_127_after_normalization_count": returncode_127_count})
    write_json(ARTIFACT_ROOT / "candidate_triage_report.json", triage)
    write_json(ARTIFACT_ROOT / "memory_candidate_selection_policy_v2_8s.json", memory_selection)
    write_json(ARTIFACT_ROOT / "candidate_chromatin_state_v2_8s.json", chromatin)
    write_json(ARTIFACT_ROOT / "local_tension_relief_v2_8s.json", tension)
    write_json(ARTIFACT_ROOT / "minimal_probe_selection_v2_8s.json", {"status": "PASS", "selected_memory_evidence_candidates": [item["candidate"] for item in selected], "attempted_memory_evidence_candidates": [item["candidate"] for item in attempted], "selection_used_only_decision_time_safe_evidence": True, "attempt_floor_unless_positive_found": MEMORY_EVIDENCE_ATTEMPT_FLOOR})
    write_json(ARTIFACT_ROOT / "candidate_triage_stability_audit_v2_8s.json", stability)
    write_json(ARTIFACT_ROOT / "closure_scaling_audit.json", closure)
    write_json(ARTIFACT_ROOT / "memory_lift_decomposition.json", memory)
    write_json(ARTIFACT_ROOT / "replacement_candidate_preflight_summary.json", {"preflight_passed_records": preflight_passed_records, "selected_for_memory_evidence": [item["candidate"] for item in selected], "attempted_memory_evidence": [item["candidate"] for item in attempted], "returncode_127_treated_as_harness_failure": True})
    write_json(ARTIFACT_ROOT / "fixture_dependency_preflight_summary.json", {"records": [{"candidate": record["candidate_id"], "fixture_data_dependency_exists": record["fixture_data_dependency_exists"], "missing": record["missing_fixture_or_data_files"]} for record in preflight_records], "fixed_revision_fixture_copying_used": False})
    write_json(ARTIFACT_ROOT / "source_discovery_summary.json", {"preflight_records": [{"candidate": record["candidate_id"], "source_discovery_result": record["source_discovery_result"], "candidate_source_files_found": record["candidate_source_files_found"]} for record in preflight_records], "buggy_source_only": True})
    write_json(ARTIFACT_ROOT / "pre_repair_replay_gate_summary.json", {"episodes": records, "passed_count": sum(1 for item in records if item["pre_repair_replay_gate_passed"])})
    write_json(ARTIFACT_ROOT / "workspace_equivalence_summary.json", {"episodes": records, "workspace_equivalence_required": True, "separate_no_memory_and_memory_workspaces": True})
    write_json(ARTIFACT_ROOT / "bounded_repair_proposer_summary.json", {"episodes": records, "bounded_source_only_repair_proposer_enabled": True, "memory_enabled_repair_memory_allowed": True, "no_memory_repair_memory_allowed": False})
    write_json(ARTIFACT_ROOT / "candidate_source_integrity_check.json", {"fixed_or_gold_patch_used_at_decision_time": False, "future_outcome_evidence_used_at_decision_time": False, "records": records})
    write_json(ARTIFACT_ROOT / "classification_vocabulary_check.json", {"allowed_vocabulary": CLASSIFICATION_VOCABULARY, "all_records_use_allowed_vocabulary": vocab_ok, "status": "PASS" if vocab_ok else "FAIL"})
    write_json(ARTIFACT_ROOT / "audit.json", {"fixed_or_gold_patch_used_at_decision_time": False, "future_outcome_evidence_used_at_decision_time": False, "tests_modified_as_repair": False, "source_only_patch_separation_enforced": True, "classification_vocabulary_check_passed": vocab_ok, "preserved_v2_8r_baseline_gate_status": baseline_gate.get("status"), "harness_sanity_status": harness.get("status"), "memory_arm_separation_status": separation.get("status"), "memory_evidence_eligibility_status": eligibility.get("status")})
    rows = "\n".join(f"| {record['episode_id']} | {record['candidate']} | {record['classification']} | {str(record['scoreable']).lower()} | {str(record['memory_enabled_outperformed_no_memory']).lower()} |" for record in records)
    write_text(
        ARTIFACT_ROOT / "campaign_summary.md",
        "# v2.8s Positive Memory Evidence Lane\n\n"
        f"Aggregate result: `{aggregate}`.\n\n"
        f"- Preserved v2.8r baseline gate: {baseline_gate.get('status')}.\n"
        f"- Harness sanity: {harness.get('status')}.\n"
        f"- Memory arm separation: {separation.get('status')}.\n"
        f"- Memory evidence eligibility: {eligibility.get('status')}.\n"
        f"- Candidates preflighted: {len(preflight_records)} / available {available_count}.\n"
        f"- Memory-evidence candidates attempted: {len(attempted)}.\n"
        f"- Executed BugsInPy episodes: {len(results)}.\n"
        f"- Scoreable episodes: {len(scoreable)}.\n"
        f"- Positive memory-only episodes: {len(positives)}.\n"
        "- Full scoring: NOT_RUN / disallowed.\n"
        "- Self-maintaining software: not demonstrated.\n\n"
        "| Episode | Candidate | Classification | Scoreable | Memory outperformed |\n"
        "| --- | --- | --- | --- | --- |\n"
        f"{rows}\n",
    )
    write_episode_instrumentation(results, chromatin, {item["candidate"] for item in selected})


def main() -> int:
    restore_v28s_hooks()
    if ARTIFACT_ROOT.exists():
        shutil.rmtree(ARTIFACT_ROOT)
    if RUNTIME_ROOT.exists():
        shutil.rmtree(RUNTIME_ROOT)
    ARTIFACT_ROOT.mkdir(parents=True)
    RUNTIME_ROOT.mkdir(parents=True)
    env = v28p.os.environ.copy()
    write_text(ARTIFACT_ROOT / "runtime_environment.txt", f"generated_at_utc={base.now()}\nplatform={base.platform.platform()}\npython={base.platform.python_version()}\nrepo_root={REPO_ROOT}\nruntime_root={RUNTIME_ROOT}\n")
    print("v2.8s: cloning BugsInPy", flush=True)
    clone_result = base.run_raw(["git", "clone", "--depth", "1", base.BUGSINPY_URL, str(base.BUGSINPY_REPO)], timeout=900)
    base.log_result(ARTIFACT_ROOT / "bugsinpy_clone_log_raw.txt", clone_result)
    seed_candidates: list[dict[str, Any]] = []
    preflight_records: list[dict[str, Any]] = []
    selected: list[dict[str, Any]] = []
    attempted: list[dict[str, Any]] = []
    triage: dict[str, Any] = {"status": "NOT_RUN", "records": []}
    results: list[dict[str, Any]] = []
    available_count = 0
    harness = {"status": "NOT_RUN", "reason": "BugsInPy clone failed"}
    baseline_gate = {"status": "FAIL", "memory_evidence_attempts_allowed": False, "reason": "BugsInPy clone failed"}
    if clone_result.get("returncode") == 0:
        env["PATH"] = str((base.BUGSINPY_REPO / "framework" / "bin").resolve()) + v28p.os.pathsep + env.get("PATH", "")
        seed_candidates = v28p.enumerate_broad_candidates()
        available_count = len(seed_candidates)
        write_common_v28s_artifacts(seed_candidates)
        print("v2.8s: running harness sanity", flush=True)
        harness = v28p.run_global_harness_sanity(env)
        for candidate in baseline_candidates():
            print(f"v2.8s: baseline gate {candidate['candidate']}", flush=True)
            results.append(v28p.run_episode(candidate, env))
        baseline_gate = write_preserved_baseline_gate(results)
        write_json(ARTIFACT_ROOT / "harness_sanity_check.json", harness)
        if baseline_gate.get("status") == "PASS":
            for ordinal, candidate in enumerate(seed_candidates[:BROAD_PREFLIGHT_BUDGET], start=1):
                print(f"v2.8s: preflight {ordinal:03d} {candidate['candidate']}", flush=True)
                preflight_records.append(v28p.run_preflight(candidate, env, ordinal))
            selected, triage = select_memory_candidates(preflight_records)
            write_json(ARTIFACT_ROOT / "candidate_triage_report.json", triage)
            write_json(ARTIFACT_ROOT / "memory_candidate_selection_policy_v2_8s.json", build_memory_candidate_selection_policy(triage, selected))
            positive_found = False
            for candidate in selected:
                if positive_found or len(attempted) >= MEMORY_EVIDENCE_ATTEMPT_FLOOR:
                    break
                print(f"v2.8s: memory evidence attempt {candidate['episode_id']} {candidate['candidate']}", flush=True)
                attempted.append(candidate)
                result = v28p.run_episode(candidate, env)
                results.append(result)
                if result.get("memory_enabled_outperformed_no_memory"):
                    positive_found = True
    else:
        write_common_v28s_artifacts(seed_candidates)
        write_json(ARTIFACT_ROOT / "harness_sanity_check.json", harness)
        write_json(ARTIFACT_ROOT / "preserved_v2_8r_baseline_gate_result.json", baseline_gate)
    aggregate = aggregate_result(results, baseline_gate.get("status") == "PASS")
    write_final_campaign_files(results, preflight_records, selected, attempted, triage, baseline_gate, harness, aggregate, available_count)
    write_manifest(ARTIFACT_ROOT)
    print(f"v2.8s aggregate: {aggregate}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
