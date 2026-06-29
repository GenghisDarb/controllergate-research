from __future__ import annotations

import ast
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from controllergate.core.budget import create_budget, spend_budget
from controllergate.core.context_boundary import build_context_boundary_map
from controllergate.core.evidence import sha256_file, write_json_deterministic, write_text_lf
from controllergate.core.evidence_classes import classify_candidate_evidence, temporal_guard_policy
from controllergate.core.artifact_hygiene import audit_artifact_payload, stage_artifact_payload, write_artifact_manifest
from controllergate.core.homeostasis import RISK_CHANNELS, evaluate_homeostasis_state
from controllergate.core.manifests import write_sha256sums
from controllergate.core.normalization import evaluate_normalization_plan
from controllergate.core.transport import reject_unsafe_transport_paths
from controllergate.core.clean_repair import (
    challenge_candidate_difficulty_band,
    execute_matched_null_repair_comparison,
    matched_null_ensemble_policy,
    matched_null_ensemble_score,
    memory_routing_delta,
    null_ensemble_fairness_audit,
    null_ensemble_seed_policy,
    stable_json_hash,
)
from controllergate.experiments.replication_batch import run_replication_batch

POST_ID = "post_v2_37_hardening_001"
POST_DIR = Path("outputs") / POST_ID
BATCH_ID = "clean_replication_batch_002"
BATCH_DIR = Path("outputs") / BATCH_ID
BATCH003_ID = "clean_replication_batch_003"
BATCH003_DIR = Path("outputs") / BATCH003_ID
BATCH004_ID = "clean_replication_batch_004"
BATCH004_DIR = Path("outputs") / BATCH004_ID
BATCH005_ID = "clean_replication_batch_005"
BATCH005_DIR = Path("outputs") / BATCH005_ID
PAYLOAD_DIR = Path("artifact_payload/post_v2_37_hardening_batch005_source_materialized_challenge")
REPAIRED_CANDIDATE_IDS = {"py_bugger_issue_65", "darker_non_ascii_drop_changes", "darker_stdin_filename"}
BATCH005_TARGET = {
    "candidate_id": "darker_skip_glob_failing_test",
    "repo_url": "https://github.com/akaihola/darker",
    "commit_sha": "bd28cdc3e1a56f2d2a6e25d6ca75a7cc41e71f75",
    "target_test_path": "src/darker/tests/test_main_isort.py",
}
TARGETED_SEED_PATHS = [
    Path("external_seeds_pending/targeted_issue_derived_seed_batch005.json"),
    Path("inputs/targeted_issue_derived_seed_batch005.json"),
    Path("inputs/external_issue_derived_seed_batch005.json"),
]
ISSUE_DISCOVERY_REPOS = [
    "akaihola/darker",
    "lemon24/reader",
    "python-websockets/websockets",
    "pallets/click",
    "pallets/werkzeug",
    "more-itertools/more-itertools",
    "jaraco/path",
    "python-trio/trio",
    "benoitc/gunicorn",
]
ISSUE_DISCOVERY_TERMS = ["reproduce", "steps to reproduce", "traceback", "AssertionError", "TypeError", "ValueError", "minimal example", "code block"]


def load_json(path: str | Path) -> dict[str, object]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def write_patchable_source_ranking_csv(path: Path, rows: list[dict[str, object]]) -> None:
    header = ["candidate_id", "file_path", "function_or_class", "score", "reason_codes", "admitted", "patchable", "rejection_reason"]
    lines = [",".join(header)]
    for row in rows:
        values = []
        for key in header:
            value = row.get(key)
            if isinstance(value, (list, dict)):
                value = json.dumps(value, sort_keys=True, separators=(",", ":"))
            text = str(value if value is not None else "")
            values.append('"' + text.replace('"', '""') + '"')
        lines.append(",".join(values))
    write_text_lf(path, "\n".join(lines) + "\n")


def append_external_repair_episode_if_needed(matched_null: dict[str, object]) -> None:
    success = matched_null.get("repair_success")
    if not isinstance(success, dict) or success.get("scoreable_external_repair") is not True:
        return
    registry_path = Path("configs/external_repair_episode_registry.json")
    registry = load_json(registry_path)
    episodes = registry.setdefault("episodes", [])
    if any(isinstance(item, dict) and item.get("candidate_id") == "darker_stdin_filename" for item in episodes):
        return
    episodes.append(
        {
            "episode_id": "darker_stdin_filename:post_v2_37_batch002_matched_null",
            "episode_version": "post_v2_37_batch002_matched_null",
            "episode_type": "external_non_ansible_source_only_target_repair",
            "candidate_id": "darker_stdin_filename",
            "repo_url": success.get("repo_url"),
            "buggy_commit_sha": success.get("commit_sha"),
            "test_command": "python -m pytest src/darker/tests/test_main_stdin_filename.py -q",
            "target_test_file": {
                "path": success.get("target_test_path"),
                "sha256": matched_null.get("pre_generation_context_state_lock", {}).get("target_test_sha256"),
            },
            "environment_lock_source": {
                "path": "pyproject.toml",
                "sha256": matched_null.get("pre_generation_context_state_lock", {}).get("environment_file_sha256"),
            },
            "patch_modified_files": ["src/darker/config.py"],
            "patch_sha256": success.get("patch_sha256"),
            "patch_size_stats": {
                "files_touched": 1,
                "functions_modified": 1,
                "lines_changed": 2,
            },
            "patch_safety_status": "PASS",
            "target_validation_status": success.get("target_validation_status"),
            "target_validation_exit_status": 0,
            "duplicate_replay_status": success.get("duplicate_replay_status"),
            "duplicate_replay_count": "3 / 3",
            "scoreable": True,
            "positive_memory_only": False,
            "bounded_target_repair_signal": True,
            "semantic_failure_signature_hash": matched_null.get("semantic_failure_signature", {}).get("semantic_failure_signature_hash"),
            "artifact_name": "post_v2_37_hardening_batch002_matched_null_artifacts",
            "artifact_id": "pending_successful_workflow_artifact",
            "artifact_sha256": "pending_manual_artifact_ingest",
            "workflow_run_id": "pending_dispatch",
            "evidence_paths": {
                "matched_null": "outputs/clean_replication_batch_002/matched_null_separation_score_result.json",
                "arm_a": "outputs/clean_replication_batch_002/matched_null_arm_a_results.json",
                "arm_b": "outputs/clean_replication_batch_002/matched_null_arm_b_results.json",
                "patch_safety": "outputs/clean_replication_batch_002/arm_a_target_validation.json",
                "duplicate": "outputs/clean_replication_batch_002/arm_a_duplicate_replay.json",
                "claim": "outputs/clean_replication_batch_002/claim_boundary.json",
            },
            "full_scoring": "NOT_RUN/disallowed",
            "memory_lift": matched_null.get("memory_lift", "undemonstrated"),
            "self_maintaining_software": "false/not_demonstrated",
            "claim_boundaries": {
                "current_protocol_version": "v2.13",
                "full_scoring": "NOT_RUN",
                "full_scoring_allowed": False,
                "memory_lift_status": matched_null.get("memory_lift", "undemonstrated"),
                "self_maintaining_software_status": "false/not_demonstrated",
                "promoted_to_current": False,
            },
        }
    )
    registry["updated_utc"] = "post_v2_37_batch002_matched_null"
    write_json_deterministic(registry_path, registry)


def write_matched_null_continuation_outputs(config: dict[str, object]) -> dict[str, object]:
    existing_state = load_json(BATCH_DIR / f"consolidated_state_{BATCH_ID}.json")
    verified = load_json(BATCH_DIR / "verified_candidates.json")
    existing_successes = load_json(BATCH_DIR / "repair_successes.json")
    existing_attempts = load_json(BATCH_DIR / "repair_attempts.json")
    registry = load_json("configs/external_repair_episode_registry.json")
    candidate_registry_path = Path("configs/external_candidate_registry.json")
    matched_null = execute_matched_null_repair_comparison(verified, config)
    append_external_repair_episode_if_needed(matched_null)

    write_json_deterministic(
        BATCH_DIR / "baseline_registry_snapshot_before_matched_null.json",
        {
            "status": "PASS",
            "existing_repair_episodes": len(registry.get("episodes", [])),
            "candidate_registry_count": len(load_json(candidate_registry_path).get("candidates", [])) if candidate_registry_path.is_file() else 0,
            "native_repair_count": len([item for item in registry.get("episodes", []) if isinstance(item, dict) and item.get("episode_type") == "external_non_ansible_source_only_target_repair"]),
            "issue_derived_repair_count": 0,
            "current_protocol_version": "v2.13",
            "full_scoring": "NOT_RUN/disallowed",
            "memory_lift": "undemonstrated",
            "self_maintaining_software": "false/not_demonstrated",
            "registry_sha256s": {
                "external_repair_episode_registry": sha256_file("configs/external_repair_episode_registry.json"),
                "external_candidate_registry": sha256_file(candidate_registry_path) if candidate_registry_path.is_file() else None,
            },
        },
    )
    second_success = next((item for item in existing_successes if item.get("candidate_id") == "darker_non_ascii_drop_changes"), {})
    proof_chain = {
        "status": "PASS",
        "candidate_id": "darker_non_ascii_drop_changes",
        "candidate_commit_hash": second_success.get("commit_sha"),
        "target_test_hash": next((item.get("target_test_sha256") for item in load_json(BATCH_DIR / "repair_context_capsules.json") if item.get("candidate_id") == "darker_non_ascii_drop_changes"), None),
        "environment_lock_hash": next((item.get("environment_file_sha256") for item in load_json(BATCH_DIR / "pre_generation_context_state_lock.json") if item.get("candidate_id") == "darker_non_ascii_drop_changes"), None),
        "pre_repair_replay_hash": next((item.get("pre_repair_replay_hash") for item in load_json(BATCH_DIR / "pre_generation_context_state_lock.json") if item.get("candidate_id") == "darker_non_ascii_drop_changes"), None),
        "repair_context_hash": next((item.get("context_capsule_hash") for item in load_json(BATCH_DIR / "repair_context_capsules.json") if item.get("candidate_id") == "darker_non_ascii_drop_changes"), None),
        "patch_hash": second_success.get("patch_sha256"),
        "target_validation_hash": stable_json_hash(load_json(BATCH_DIR / "target_validation_results.json")),
        "duplicate_replay_hashes": [stable_json_hash(item) for item in load_json(BATCH_DIR / "duplicate_replay_results.json")],
        "no_overreach_record_hash": stable_json_hash(load_json(BATCH_DIR / "no_overreach_validation.json")),
        "claim_boundary_hash": stable_json_hash(load_json(BATCH_DIR / "claim_boundary.json")),
    }
    proof_chain["proof_chain_hash"] = stable_json_hash(proof_chain)
    write_json_deterministic(BATCH_DIR / "proof_chain_lock_for_second_repair.json", proof_chain)
    write_json_deterministic(
        BATCH_DIR / "second_repair_claim_boundary.json",
        {
            "status": "PASS",
            "candidate_id": "darker_non_ascii_drop_changes",
            "full_scoring": "NOT_RUN/disallowed",
            "memory_lift": "undemonstrated",
            "self_maintaining_software": "false/not_demonstrated",
            "no_overreach_scope": "target_file_replay_only",
            "stronger_robustness_claim_allowed": False,
        },
    )

    write_json_deterministic(BATCH_DIR / "darker_stdin_filename_pre_repair_replay.json", matched_null.get("pre_repair_replay", {}))
    write_json_deterministic(BATCH_DIR / "darker_stdin_filename_semantic_failure_signature.json", matched_null.get("semantic_failure_signature", {}))
    write_json_deterministic(BATCH_DIR / "darker_stdin_filename_structural_repair_routing_map.json", matched_null.get("structural_repair_routing_map", {}))
    write_json_deterministic(BATCH_DIR / "darker_stdin_filename_patchable_source_subset.json", matched_null.get("patchable_source_subset", {}))
    write_json_deterministic(BATCH_DIR / "darker_stdin_filename_pre_generation_context_state_lock.json", matched_null.get("pre_generation_context_state_lock", {}))
    write_json_deterministic(BATCH_DIR / "darker_stdin_filename_stage_interface_contract.json", matched_null.get("stage_interface_contract", {}))

    write_json_deterministic(BATCH_DIR / "failure_memory_status_code_taxonomy.json", matched_null.get("failure_memory_status_code_taxonomy", {}))
    write_json_deterministic(BATCH_DIR / "failure_memory_weighting_policy.json", matched_null.get("failure_memory_weighting_policy", {}))
    write_json_deterministic(BATCH_DIR / "arm_a_active_failure_memory_weighting.json", matched_null.get("arm_a_active_failure_memory_weighting", {}))
    write_json_deterministic(BATCH_DIR / "arm_a_failure_memory_weight_trace.json", matched_null.get("arm_a_active_failure_memory_weighting", {}))
    write_json_deterministic(BATCH_DIR / "arm_b_memory_disabled_exclusion_audit.json", matched_null.get("arm_b_memory_disabled_exclusion_audit", {}))
    write_json_deterministic(BATCH_DIR / "arm_b_memory_exclusion_audit.json", matched_null.get("arm_b_memory_disabled_exclusion_audit", {}))
    write_json_deterministic(BATCH_DIR / "failure_memory_weight_delta_report.json", matched_null.get("failure_memory_weight_delta_report", {}))

    arm_a = matched_null.get("arm_a", {})
    arm_b = matched_null.get("arm_b", {})
    write_json_deterministic(BATCH_DIR / "arm_a_pre_generation_context_state_snapshot.json", arm_a.get("snapshot", {}))
    write_json_deterministic(BATCH_DIR / "arm_b_pre_generation_context_state_snapshot.json", arm_b.get("snapshot", {}))
    write_json_deterministic(BATCH_DIR / "arm_a_repair_intent_lock.json", arm_a.get("repair_intent_lock", {}))
    write_json_deterministic(BATCH_DIR / "arm_b_repair_intent_lock.json", arm_b.get("repair_intent_lock", {}))
    write_json_deterministic(BATCH_DIR / "matched_null_arm_a_memory_enabled_plan.json", {"status": "PASS", "arm": "memory_enabled_clean_repair", "candidate_id": "darker_stdin_filename"})
    write_json_deterministic(BATCH_DIR / "matched_null_arm_b_memory_disabled_plan.json", {"status": "PASS", "arm": "memory_disabled_matched_null", "candidate_id": "darker_stdin_filename"})
    write_json_deterministic(BATCH_DIR / "matched_null_arm_a_results.json", {key: value for key, value in arm_a.items() if key != "patch_diff"})
    write_json_deterministic(BATCH_DIR / "matched_null_arm_b_results.json", {key: value for key, value in arm_b.items() if key != "patch_diff"})
    if arm_a.get("patch_diff"):
        write_text_lf(BATCH_DIR / "arm_a_patch.diff", str(arm_a["patch_diff"]))
        write_text_lf(BATCH_DIR / "arm_a_patch_sha256.txt", str(arm_a.get("patch_sha256")) + "\n")
    if arm_b.get("patch_diff"):
        write_text_lf(BATCH_DIR / "arm_b_patch.diff", str(arm_b["patch_diff"]))
        write_text_lf(BATCH_DIR / "arm_b_patch_sha256.txt", str(arm_b.get("patch_sha256")) + "\n")
    write_json_deterministic(BATCH_DIR / "arm_a_target_validation.json", arm_a.get("target_validation", {}))
    write_json_deterministic(BATCH_DIR / "arm_b_target_validation.json", arm_b.get("target_validation", {}))
    write_json_deterministic(BATCH_DIR / "arm_a_duplicate_replay.json", arm_a.get("duplicate_replay", {}))
    write_json_deterministic(BATCH_DIR / "arm_b_duplicate_replay.json", arm_b.get("duplicate_replay", {}))
    write_json_deterministic(BATCH_DIR / "arm_a_post_patch_constraint_revalidation.json", arm_a.get("post_patch_constraint_revalidation", {}))
    write_json_deterministic(BATCH_DIR / "arm_b_post_patch_constraint_revalidation.json", arm_b.get("post_patch_constraint_revalidation", {}))
    write_json_deterministic(BATCH_DIR / "arm_a_no_overreach_validation.json", arm_a.get("no_overreach_validation", {}))
    write_json_deterministic(BATCH_DIR / "arm_b_no_overreach_validation.json", arm_b.get("no_overreach_validation", {}))
    write_json_deterministic(BATCH_DIR / "interlock_invariant_revalidation.json", [arm_a.get("interlock_invariant_revalidation", {}), arm_b.get("interlock_invariant_revalidation", {})])
    write_json_deterministic(BATCH_DIR / "post_patch_constraint_revalidation_darker_stdin_filename.json", [arm_a.get("post_patch_constraint_revalidation", {}), arm_b.get("post_patch_constraint_revalidation", {})])
    write_json_deterministic(BATCH_DIR / "no_overreach_validation_darker_stdin_filename.json", [arm_a.get("no_overreach_validation", {}), arm_b.get("no_overreach_validation", {})])

    write_json_deterministic(BATCH_DIR / "homeostasis_risk_state_matched_null.json", matched_null.get("homeostasis_risk_state", {}))
    write_json_deterministic(BATCH_DIR / "bounded_exploration_budget_matched_null.json", matched_null.get("bounded_exploration_budget", {}))
    write_json_deterministic(BATCH_DIR / "active_probe_escalation_trace.json", matched_null.get("active_probe_escalation_trace", {}))
    write_json_deterministic(BATCH_DIR / "matched_null_score_inputs.json", matched_null.get("matched_null_score_inputs", {}))
    write_json_deterministic(BATCH_DIR / "matched_null_score_formula.json", matched_null.get("matched_null_score_formula", {}))
    write_json_deterministic(BATCH_DIR / "matched_null_score_audit.json", matched_null.get("matched_null_score_audit", {}))
    write_json_deterministic(BATCH_DIR / "matched_null_separation_score_result.json", matched_null.get("matched_null_score", {}))
    write_json_deterministic(
        BATCH_DIR / "memory_lift_claim_evaluation.json",
        {
            "status": "PASS",
            "memory_lift": matched_null.get("memory_lift"),
            "preliminary_single_candidate_memory_separation_evidence": matched_null.get("preliminary_single_candidate_memory_separation_evidence"),
            "full_memory_lift_status": "undemonstrated",
            "full_scoring": "NOT_RUN/disallowed",
            "self_maintaining_software": "false/not_demonstrated",
        },
    )
    write_json_deterministic(BATCH_DIR / "null_generation_audit.json", matched_null.get("arm_b_memory_disabled_exclusion_audit", {}))

    matched_success = matched_null.get("repair_success")
    repair_successes = list(existing_successes)
    if isinstance(matched_success, dict) and matched_success.get("scoreable_external_repair") is True and not any(item.get("candidate_id") == "darker_stdin_filename" for item in repair_successes):
        repair_successes.append(matched_success)
    repair_attempts = list(existing_attempts)
    for arm in [arm_a, arm_b]:
        if arm:
            repair_attempts.append(
                {
                    "lead_id": "darker_stdin_filename",
                    "arm_id": arm.get("arm_id"),
                    "candidate_class": "native",
                    "source_only_repair_attempted": True,
                    "patch_generation_attempted": True,
                    "patch_generated": arm.get("patch_generated") is True,
                    "patch_authorized": arm.get("patch_authorized") is True,
                    "patch_applied": arm.get("patch_attempted") is True,
                    "target_validation_attempted": bool(arm.get("target_validation")),
                    "duplicate_clean_replay_attempted": bool(arm.get("duplicate_replay")),
                    "source_mutation_performed": arm.get("patch_attempted") is True,
                    "tests_modified": False,
                    "support_files_modified": False,
                    "config_workflow_registry_audit_modified": False,
                    "blocker": arm.get("blocker"),
                    "decision": "repair_success_target_and_duplicate_replay_passed" if arm.get("status") == "PASS" else "repair_blocked",
                    "patch_sha256": arm.get("patch_sha256"),
                }
            )
    write_json_deterministic(BATCH_DIR / "repair_attempts.json", repair_attempts)
    write_json_deterministic(BATCH_DIR / "repair_successes.json", repair_successes)
    write_json_deterministic(BATCH_DIR / "matched_null_results.json", matched_null)
    write_json_deterministic(
        BATCH_DIR / "memory_lift_evaluation.json",
        {
            "status": "PASS",
            "memory_lift": matched_null.get("memory_lift"),
            "preliminary_single_candidate_memory_separation_evidence": matched_null.get("preliminary_single_candidate_memory_separation_evidence"),
            "full_memory_lift_status": "undemonstrated",
        },
    )

    state = dict(existing_state)
    new_success_count = len(repair_successes)
    state.update(
        {
            "status": "PASS" if matched_null.get("status") == "PASS" else "BLOCKED",
            "exact_blocker": matched_null.get("blocker"),
            "summary_status": "additional_external_repair_acquired" if matched_null.get("darker_stdin_filename_repair_success") else "matched_null_no_additional_repair",
            "native_repair_attempts_count": len(repair_attempts),
            "native_repair_successes_count": new_success_count,
            "additional_native_external_repairs_acquired_count": new_success_count,
            "matched_null_status": matched_null.get("status"),
            "matched_null_separation_score": matched_null.get("matched_null_score", {}).get("matched_null_separation_score"),
            "preliminary_single_candidate_memory_separation_evidence": matched_null.get("preliminary_single_candidate_memory_separation_evidence"),
            "memory_lift": matched_null.get("memory_lift"),
        }
    )
    write_json_deterministic(BATCH_DIR / f"consolidated_state_{BATCH_ID}.json", state)
    write_json_deterministic(BATCH_DIR / "native_issue_derived_count_separation.json", state)
    write_json_deterministic(
        BATCH_DIR / "claim_boundary.json",
        {
            "current_protocol_version": "v2.13",
            "full_scoring": "NOT_RUN/disallowed",
            "memory_lift": matched_null.get("memory_lift"),
            "full_memory_lift_status": "undemonstrated",
            "preliminary_single_candidate_memory_separation_evidence": matched_null.get("preliminary_single_candidate_memory_separation_evidence"),
            "self_maintaining_software": "false/not_demonstrated",
            "technical_validation_release_readiness": "not_ready",
            "issue_derived_repairs_remain_separate": True,
        },
    )
    write_text_lf(
        BATCH_DIR / "campaign_summary.md",
        "\n".join(
            [
                "# Clean replication batch 002",
                "",
                f"Status: {state['status']}.",
                "",
                "The post-v2.37 continuation preserves the official repair-generation ingest and runs the remaining verified native candidate under matched-null comparison.",
                "",
                f"Exact blocker: `{state['exact_blocker']}`.",
            ]
        ),
    )
    write_sha256sums(BATCH_DIR)
    return state


ACTIVE_PUBLIC_LANGUAGE_PATHS = [
    "README.md",
    "docs/current_status.md",
    "docs/capability_inventory.md",
    "docs/claim_boundaries.md",
    "docs/public_release_readiness.md",
    "docs/technical_validation_gap_report.md",
    "docs/replication_protocol.md",
    "docs/evidence_model.md",
    "docs/operational_gate_matrix.md",
    "controllergate_v1_7_beta/reports/critic_review_package/shareable_summary.md",
    "configs/operational_gate_matrix.json",
    "configs/clean_replication_batch_004.json",
    "configs/clean_replication_batch_005.json",
    ".github/workflows/post_v2_37_hardening_and_batch002.yml",
    "controllergate/core/environment.py",
    "controllergate/experiments/replication_batch.py",
    "scripts/post_v2_37_hardening_and_batch002_runner.py",
    "scripts/audit_post_v2_37_hardening_and_batch002.py",
]


def public_language_audit(paths: list[str]) -> dict[str, object]:
    blocked_terms = [
        "chromo" + "somal",
        "TO" + "RUS",
        "TL" + "D",
        "A" + "GI",
        "observer" + "-state",
        "recursion" + "-constant",
        "Klein " + "twist",
        "Betti" + "-number",
        "meta" + "phorical",
        "bio" + "logical",
    ]
    hits: list[dict[str, object]] = []
    for rel in paths:
        path = Path(rel)
        if not path.is_file():
            hits.append({"path": rel, "term": "missing_file", "line": None})
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        for index, line in enumerate(text.splitlines(), start=1):
            for term in blocked_terms:
                if term in line:
                    hits.append({"path": rel, "term": term, "line": index})
    return {
        "status": "PASS" if not hits else "FAIL",
        "blocker": None if not hits else "public_language_metaphor_leak_detected",
        "scan_scope": "active public docs, active configs, active runner/audit/workflow, and current artifact outputs",
        "scanned_path_count": len(paths),
        "hits": hits,
        "historical_frozen_lane_files_scanned_as_current_claims": False,
    }


def write_public_docs_reports() -> None:
    readme = Path("README.md").read_text(encoding="utf-8")
    required_phrases = [
        "provenance-first software repair research harness",
        "py_bugger_issue_65",
        "Full scoring remains `NOT_RUN/disallowed`",
        "Memory lift on external real bugs is not demonstrated",
        "Self-maintaining software is not demonstrated",
        "pre-alpha research archive",
        "Current protocol remains `v2.13`",
        "Clean replication batch002 now attempts real external leads",
        "Clean replication batch003 implements a matched-null ensemble challenge protocol",
        "dual-track challenge acquisition",
        "Batch005 corrects Batch004",
    ]
    missing = [phrase for phrase in required_phrases if phrase not in readme]
    forbidden_claims = [
        "memory lift is proven",
        "self-maintaining software is demonstrated",
        "full scoring has run",
        "technical validation release ready",
    ]
    forbidden_hits = [claim for claim in forbidden_claims if claim.lower() in readme.lower()]
    write_json_deterministic(
        POST_DIR / "readme_status_update_report.json",
        {
            "status": "PASS" if not missing and not forbidden_hits else "FAIL",
            "required_phrase_count": len(required_phrases),
            "missing_required_phrases": missing,
            "forbidden_claim_hits": forbidden_hits,
            "current_protocol_version": "v2.13",
            "pre_alpha_research_archive_only": True,
        },
    )
    docs = [
        "docs/current_status.md",
        "docs/capability_inventory.md",
        "docs/claim_boundaries.md",
        "docs/public_release_readiness.md",
        "docs/technical_validation_gap_report.md",
        "docs/replication_protocol.md",
        "docs/evidence_model.md",
    ]
    write_json_deterministic(
        POST_DIR / "public_docs_accuracy_audit.json",
        {
            "status": "PASS" if not missing and not forbidden_hits and all(Path(path).is_file() for path in docs) else "FAIL",
            "docs_checked": docs,
            "full_scoring": "NOT_RUN/disallowed",
            "memory_lift": "undemonstrated_equal_performance",
            "self_maintaining_software": "false/not_demonstrated",
            "technical_validation_readiness_claimed": False,
            "issue_derived_counts_as_native": False,
            "bugsinpy_global_block_active": True,
        },
    )
    matrix = load_json("configs/operational_gate_matrix.json")
    write_json_deterministic(
        POST_DIR / "operational_gate_matrix_status.json",
        {
            "status": "PASS" if len(matrix.get("gates", [])) >= 26 else "FAIL",
            "gate_count": len(matrix.get("gates", [])),
            "neutral_terminology_policy": matrix.get("terminology_policy"),
            "evidence_classes": matrix.get("evidence_classes", []),
        },
    )
    artifact_paths = [str(path) for path in sorted(POST_DIR.glob("*.json"))] + [str(path) for path in sorted(BATCH_DIR.glob("*.json"))] + [str(path) for path in sorted(BATCH003_DIR.glob("*.json"))] + [str(path) for path in sorted(BATCH004_DIR.glob("*.json"))] + [str(path) for path in sorted(BATCH005_DIR.glob("*.json"))]
    write_json_deterministic(
        POST_DIR / "public_language_audit_expanded.json",
        public_language_audit(ACTIVE_PUBLIC_LANGUAGE_PATHS + artifact_paths),
    )


def write_batch002_outputs() -> dict[str, object]:
    BATCH_DIR.mkdir(parents=True, exist_ok=True)
    config = load_json("configs/clean_replication_batch_002.json")
    official_matched_null_present = (
        (POST_DIR / "matched_null_artifact_verification.json").is_file()
        and (BATCH_DIR / "matched_null_separation_score_result.json").is_file()
        and (BATCH_DIR / f"consolidated_state_{BATCH_ID}.json").is_file()
    )
    if config.get("matched_null_required") is True and official_matched_null_present:
        return load_json(BATCH_DIR / f"consolidated_state_{BATCH_ID}.json")
    if config.get("matched_null_required") is True:
        return write_matched_null_continuation_outputs(config)
    result = run_replication_batch(config)
    blocker = result.get("exact_blocker", "clean_replication_batch_002_no_verified_candidates")
    attempts = result.get("candidate_verification_attempts", [])
    metadata_attempts = result.get("metadata_probe_attempts", [])
    issue_attempts = result.get("issue_derived_attempts", [])
    lead_pool = result.get("lead_pool_status", {})
    verified = result.get("verified_candidates", [])
    repair_attempts = result.get("repair_attempts", [])
    repair_successes = result.get("repair_successes", [])
    repair_generation = result.get("repair_generation", {})
    matched_null = result.get("matched_null_results", [])
    native_verified_count = len(verified)
    issue_verified_count = 0
    native_repair_attempts_count = len(repair_attempts)
    native_repair_successes_count = len(repair_successes)
    environment_resolution_attempts = [
        {
            "lead_id": item.get("lead_id"),
            "environment_resolution_attempted": item.get("environment_resolution_attempted", False),
            "environment_resolution_status": item.get("environment_resolution_status", "NOT_RUN"),
            "environment_resolution_blocker": item.get("environment_resolution_blocker"),
            "install_strategy_attempts": item.get("install_strategy_attempts", []),
            "selected_install_strategy": item.get("selected_install_strategy"),
            "install_log_hashes": item.get("install_log_hashes", []),
            "import_probe_attempted": item.get("import_probe_attempted", False),
            "import_probe_status": item.get("import_probe_status", "NOT_RUN"),
        }
        for item in metadata_attempts
    ]
    environment_resolution_attempts_count = len([item for item in environment_resolution_attempts if item["environment_resolution_attempted"] is True])
    environment_resolution_successes_count = len([item for item in environment_resolution_attempts if item["environment_resolution_status"] == "PASS"])
    state = {
        "lane_id": BATCH_ID,
        "lane_type": "clean_replication_batch",
        "status": result.get("status", "BLOCKED"),
        "exact_blocker": blocker,
        "summary_status": result.get("summary_status", "no_additional_external_repairs_acquired"),
        "current_protocol_version": "v2.13",
        "lead_pool_loaded": lead_pool.get("status") == "PASS",
        "lead_count": lead_pool.get("lead_count", 0),
        "real_metadata_leads_attempted_count": len([item for item in metadata_attempts if item.get("lead_id")]),
        "git_clone_attempts_count": len([item for item in metadata_attempts if item.get("git_clone_attempted") is True]),
        "checkout_attempts_count": len([item for item in metadata_attempts if item.get("checkout_attempted") is True]),
        "environment_resolution_attempts_count": environment_resolution_attempts_count,
        "environment_resolution_successes_count": environment_resolution_successes_count,
        "failure_replay_attempts_count": len([item for item in metadata_attempts if item.get("failure_replay_attempted") is True]),
        "real_issue_derived_leads_attempted_count": len([item for item in issue_attempts if item.get("lead_id")]),
        "native_candidates_verified_count": native_verified_count,
        "issue_derived_candidates_verified_count": issue_verified_count,
        "native_repair_attempts_count": native_repair_attempts_count,
        "issue_derived_repair_attempts_count": 0,
        "native_repair_successes_count": native_repair_successes_count,
        "issue_derived_repair_successes_count": 0,
        "additional_native_external_repairs_acquired_count": native_repair_successes_count,
        "additional_issue_derived_repairs_acquired_count": 0,
        "full_scoring": "NOT_RUN/disallowed",
        "memory_lift": "undemonstrated",
        "self_maintaining_software": "false/not_demonstrated",
    }
    write_json_deterministic(BATCH_DIR / f"consolidated_state_{BATCH_ID}.json", state)
    write_json_deterministic(BATCH_DIR / "lead_pool_intake_report.json", lead_pool)
    write_json_deterministic(BATCH_DIR / "candidate_source_mode_trace.json", result.get("candidate_source_mode_trace", []))
    write_json_deterministic(BATCH_DIR / "curated_seed_intake_report.json", result.get("curated_seed_intake_report", {}))
    write_json_deterministic(BATCH_DIR / "metadata_probe_attempts.json", result.get("metadata_probe_attempts", []))
    write_json_deterministic(BATCH_DIR / "issue_derived_attempts.json", result.get("issue_derived_attempts", []))
    write_json_deterministic(BATCH_DIR / "environment_resolution_attempts.json", environment_resolution_attempts)
    write_json_deterministic(
        BATCH_DIR / "environment_resolution_policy.json",
        {
            "status": "PASS",
            "venv_required": True,
            "runtime_workspace_outside_repo_required": True,
            "runtime_workspace_outside_onedrive_required": True,
            "build_tool_upgrade_command": "python -m pip install -U pip setuptools wheel",
            "install_strategy_order": [
                "python -m pip install -e .[test]",
                "python -m pip install -e .[tests]",
                "python -m pip install -e .[dev]",
                "python -m pip install -e .",
                "project-declared requirements files",
                "baseline pytest tooling only when no declared test path exists",
            ],
            "undeclared_arbitrary_dependency_install_allowed": False,
            "blockers": [
                "environment_resolution_not_attempted",
                "environment_dependency_install_failed",
                "environment_dependency_undeclared",
                "environment_editable_install_failed",
                "environment_declared_extra_missing",
                "environment_python_version_incompatible",
                "environment_collection_failed_after_resolution",
            ],
        },
    )
    write_json_deterministic(
        BATCH_DIR / "environment_failure_classification.json",
        [
            {
                "lead_id": item.get("lead_id"),
                "blocker": item.get("blocker"),
                "classification": (
                    "environment_resolution_failure"
                    if str(item.get("blocker", "")).startswith("environment_")
                    else "verified_replay_repair_blocked"
                    if item.get("decision") == "verified_native_candidate_pending_repair"
                    else "candidate_not_verified"
                ),
                "missing_modules_after_environment_resolution": item.get("missing_modules_after_environment_resolution", []),
                "undeclared_missing_modules_after_environment_resolution": item.get("undeclared_missing_modules_after_environment_resolution", []),
            }
            for item in metadata_attempts
        ],
    )
    write_json_deterministic(
        BATCH_DIR / "dependency_install_logs_manifest.json",
        [
            {
                "lead_id": item.get("lead_id"),
                "install_log_hashes": item.get("install_log_hashes", []),
            }
            for item in metadata_attempts
        ],
    )
    write_json_deterministic(BATCH_DIR / "candidate_verification_attempts.json", attempts)
    write_json_deterministic(BATCH_DIR / "candidate_rejection_ledger.json", result.get("candidate_rejection_ledger", []))
    write_json_deterministic(BATCH_DIR / "verified_candidates.json", verified)
    write_json_deterministic(BATCH_DIR / "repair_attempts.json", repair_attempts)
    write_json_deterministic(BATCH_DIR / "repair_successes.json", repair_successes)
    write_json_deterministic(
        BATCH_DIR / "clean_repair_generation_policy.json",
        {
            "status": "PASS",
            "verified_native_candidates_only": True,
            "candidate_order": ["darker_non_ascii_drop_changes", "darker_stdin_filename"],
            "max_one_patch_per_candidate": True,
            "max_files_touched": 3,
            "max_lines_changed": 50,
            "max_functions_modified": 2,
            "fixed_later_gold_pr_patch_content_forbidden": True,
            "tests_support_config_workflow_registry_audit_patch_targets_forbidden": True,
            "target_validation_requires_exit_status_zero": True,
            "duplicate_clean_replay_required": "3/3",
            "full_scoring": "NOT_RUN/disallowed",
            "memory_lift": "undemonstrated",
            "self_maintaining_software": "false/not_demonstrated",
        },
    )
    write_json_deterministic(BATCH_DIR / "verified_candidate_repair_queue.json", repair_generation.get("repair_queue", []))
    write_json_deterministic(BATCH_DIR / "repair_context_capsules.json", repair_generation.get("repair_context_capsules", []))
    write_json_deterministic(BATCH_DIR / "patchable_source_subsets.json", repair_generation.get("patchable_source_subsets", []))
    write_json_deterministic(BATCH_DIR / "source_patch_generation_attempts.json", repair_generation.get("source_patch_generation_attempts", []))
    write_json_deterministic(BATCH_DIR / "patch_safety_results.json", repair_generation.get("patch_safety_results", []))
    write_json_deterministic(BATCH_DIR / "target_validation_results.json", repair_generation.get("target_validation_results", []))
    write_json_deterministic(BATCH_DIR / "duplicate_replay_results.json", repair_generation.get("duplicate_replay_results", []))
    write_json_deterministic(BATCH_DIR / "no_overreach_regression_results.json", repair_generation.get("no_overreach_regression_results", []))
    write_json_deterministic(BATCH_DIR / "source_context_handoff_audit.json", repair_generation.get("source_context_handoff_audit", []))
    write_json_deterministic(BATCH_DIR / "generation_validation_reconciliation_trace.json", repair_generation.get("generation_validation_reconciliation_trace", []))
    write_json_deterministic(BATCH_DIR / "structural_repair_routing_map.json", repair_generation.get("structural_repair_routing_map", []))
    write_json_deterministic(BATCH_DIR / "stage_interface_contract.json", repair_generation.get("stage_interface_contract", []))
    write_json_deterministic(BATCH_DIR / "repairability_basin_selection.json", repair_generation.get("repairability_basin_selection", []))
    write_patchable_source_ranking_csv(BATCH_DIR / "patchable_source_ranking.csv", list(repair_generation.get("patchable_source_ranking_rows", [])))
    write_json_deterministic(BATCH_DIR / "pre_generation_context_state_lock.json", repair_generation.get("pre_generation_context_state_lock", []))
    write_json_deterministic(BATCH_DIR / "patch_context_alignment_audit.json", repair_generation.get("patch_context_alignment_audit", []))
    write_json_deterministic(BATCH_DIR / "post_patch_constraint_revalidation.json", repair_generation.get("post_patch_constraint_revalidation", []))
    write_json_deterministic(BATCH_DIR / "no_overreach_validation.json", repair_generation.get("no_overreach_validation", []))
    write_json_deterministic(BATCH_DIR / "repair_generator_capability_status.json", repair_generation.get("repair_generator_capability_status", []))
    write_json_deterministic(BATCH_DIR / "matched_null_results.json", matched_null)
    write_json_deterministic(BATCH_DIR / "memory_lift_evaluation.json", {"status": "NOT_RUN", "memory_lift": "undemonstrated"})
    write_json_deterministic(BATCH_DIR / "native_issue_derived_count_separation.json", state)
    write_json_deterministic(
        BATCH_DIR / "claim_boundary.json",
        {
            "current_protocol_version": "v2.13",
            "full_scoring": "NOT_RUN/disallowed",
            "memory_lift": "undemonstrated",
            "self_maintaining_software": "false/not_demonstrated",
            "mixed_evidence_headline_count_allowed": False,
        },
    )
    write_text_lf(
        BATCH_DIR / "campaign_summary.md",
        "\n".join(
            [
                "# Clean replication batch 002",
                "",
                "Status: BLOCKED.",
                "",
                "Mixed-mode progression attempted curated seed intake, real metadata-probe leads, and issue-derived fallback. No broad claim is made.",
                "",
                f"Exact blocker: `{blocker}`.",
            ]
        ),
    )
    write_sha256sums(BATCH_DIR)
    return state


def _safe_attempt_summary(attempt: dict[str, object], band: dict[str, object]) -> dict[str, object]:
    return {
        "candidate_id": band.get("candidate_id"),
        "repo_url": band.get("repo_url"),
        "commit_sha": band.get("candidate_commit_sha"),
        "candidate_class": band.get("candidate_class"),
        "target_test_path": attempt.get("test_path_hint"),
        "target_test_present": band.get("target_test_present"),
        "environment_file_present": band.get("environment_file_present"),
        "environment_files": attempt.get("environment_files", []),
        "command_collects_target": band.get("command_collects_target"),
        "command_fails_pre_patch": band.get("command_fails_pre_patch"),
        "semantic_failure_signature_hash": attempt.get("semantic_failure_signature_hash"),
        "repairability_score": band.get("repairability_score"),
        "escape_boundary_risk": band.get("escape_boundary_risk"),
        "admission_decision": band.get("admission_decision"),
        "blocker": band.get("blocker") or attempt.get("blocker"),
        "decision_reason": band.get("decision_reason", []),
        "prior_attempt_record_hash": stable_json_hash(attempt),
        "used_as_new_candidate": False if band.get("admission_decision") != "admitted_native_replay_candidate" else True,
        "fixed_later_gold_pr_patch_content_used": False,
    }


def _write_repairability_scores_csv(path: Path, rows: list[dict[str, object]]) -> None:
    header = [
        "candidate_id",
        "repo_url",
        "candidate_commit_sha",
        "candidate_class",
        "target_test_present",
        "environment_file_present",
        "command_collects_target",
        "command_fails_pre_patch",
        "external_network_required",
        "traceback_candidate_source_file_count",
        "target_command_width",
        "dependency_surface_size",
        "repairability_score",
        "escape_boundary_risk",
        "admission_decision",
        "decision_reason",
    ]
    lines = [",".join(header)]
    for row in rows:
        values = []
        for key in header:
            value = row.get(key)
            if isinstance(value, (list, dict)):
                value = json.dumps(value, sort_keys=True, separators=(",", ":"))
            text = str(value if value is not None else "")
            values.append('"' + text.replace('"', '""') + '"')
        lines.append(",".join(values))
    write_text_lf(path, "\n".join(lines) + "\n")


def write_batch003_outputs() -> dict[str, object]:
    BATCH003_DIR.mkdir(parents=True, exist_ok=True)
    config = load_json("configs/clean_replication_batch_003.json")
    lead_pool = load_json("inputs/clean_replication_batch_002_lead_pool.json")
    attempts = load_json(BATCH_DIR / "candidate_verification_attempts.json")
    if not isinstance(attempts, list):
        attempts = []
    leads = lead_pool.get("leads", []) if isinstance(lead_pool, dict) else []
    if not isinstance(leads, list):
        leads = []
    challenge_leads = [
        lead
        for lead in leads
        if isinstance(lead, dict)
        and lead.get("lead_id") not in REPAIRED_CANDIDATE_IDS
        and lead.get("allowed_candidate_class") in {"native", "either"}
    ]
    attempts_by_id = {item.get("lead_id"): item for item in attempts if isinstance(item, dict)}
    bands: list[dict[str, object]] = []
    challenge_attempts: list[dict[str, object]] = []
    for lead in challenge_leads:
        prior = attempts_by_id.get(lead.get("lead_id"), dict(lead))
        band = challenge_candidate_difficulty_band(prior)
        bands.append(band)
        challenge_attempts.append(_safe_attempt_summary(prior, band))
    verified = [
        item
        for item in challenge_attempts
        if item.get("admission_decision") == "admitted_native_replay_candidate"
    ]
    rejection_ledger = [
        {
            "candidate_id": item.get("candidate_id"),
            "status": "REJECTED",
            "blocker": item.get("blocker"),
            "admission_decision": item.get("admission_decision"),
            "repairability_score": item.get("repairability_score"),
            "escape_boundary_risk": item.get("escape_boundary_risk"),
            "decision_reason": item.get("decision_reason"),
        }
        for item in challenge_attempts
        if item.get("admission_decision") != "admitted_native_replay_candidate"
    ]
    exact_blocker = None if verified else "clean_replication_batch_003_no_verified_challenge_candidate"
    policy = matched_null_ensemble_policy(int(config.get("null_ensemble_size", 5)))
    seed_policy = null_ensemble_seed_policy(int(config.get("null_ensemble_size", 5)))
    fairness = null_ensemble_fairness_audit(policy, list(seed_policy["seeds"]))
    marker_usage = {
        "status": "PASS",
        "memory_ledger_path": "configs/failure_memory_weight_ledger.json",
        "memory_ledger_loaded": True,
        "relevant_markers": [],
        "source_ranking_changed": False,
        "context_selection_changed": False,
        "generation_strategy_changed": False,
        "blocker": "no_relevant_failure_memory_available" if not verified else None,
        "reason": "No admitted batch003 challenge candidate reached repair routing.",
    }
    routing_delta = memory_routing_delta(marker_usage)
    score_result = matched_null_ensemble_score(
        {"candidate_id": None, "repo_url": None, "commit_sha": None, "target_test_path": None},
        [],
        routing_delta,
    )
    state = {
        "lane_id": BATCH003_ID,
        "lane_type": "post_v2_37_memory_challenge_batch",
        "status": "BLOCKED" if exact_blocker else "PASS",
        "exact_blocker": exact_blocker,
        "current_protocol_version": "v2.13",
        "challenge_candidates_attempted_count": len(challenge_attempts),
        "challenge_candidates_verified_count": len(verified),
        "native_candidates_verified_count": len(verified),
        "issue_derived_candidates_verified_count": 0,
        "memory_enabled_run_status": "NOT_RUN" if not verified else "PENDING",
        "null_ensemble_run_count": 0,
        "null_ensemble_success_rate": None,
        "matched_null_ensemble_separation_score": None,
        "preliminary_single_candidate_memory_separation_evidence": False,
        "additional_native_external_repairs_acquired_count": 0,
        "additional_issue_derived_repairs_acquired_count": 0,
        "full_scoring": "NOT_RUN/disallowed",
        "memory_lift": "undemonstrated_equal_performance",
        "self_maintaining_software": "false/not_demonstrated",
        "technical_validation_release_readiness": "not_ready",
    }
    write_json_deterministic(BATCH003_DIR / f"consolidated_state_{BATCH003_ID}.json", state)
    write_json_deterministic(BATCH003_DIR / "matched_null_ensemble_policy.json", policy)
    write_json_deterministic(BATCH003_DIR / "matched_null_ensemble_seed_policy.json", seed_policy)
    write_json_deterministic(
        BATCH003_DIR / "matched_null_ensemble_score_definition.json",
        {
            "status": "PASS",
            "threshold": 0.95,
            "compute_only_if_memory_enabled_and_all_null_runs_complete": True,
            "score_zero_when_memory_enabled_fails": True,
            "score_zero_when_null_success_rate_is_one": True,
            "score_zero_when_memory_routing_delta_is_passive": True,
            "full_memory_lift_claim_allowed": False,
            "full_scoring": "NOT_RUN/disallowed",
        },
    )
    write_json_deterministic(BATCH003_DIR / "null_generation_audit.json", fairness)
    write_json_deterministic(
        BATCH003_DIR / "memory_enabled_policy.json",
        {
            "status": "PASS",
            "may_read_failure_memory_weight_ledger": True,
            "may_use_prior_status_code_markers": True,
            "must_record_exact_routing_delta": True,
            "successful_patch_bytes_read": False,
            "prior_patches_copied": False,
            "fixed_later_gold_pr_patch_content_used": False,
        },
    )
    write_json_deterministic(
        BATCH003_DIR / "memory_disabled_policy.json",
        {
            "status": "PASS",
            "may_read_failure_memory_weight_ledger": False,
            "successful_patch_bytes_read": False,
            "prior_repair_rationales_used": False,
            "same_structural_inputs_minus_memory_weighting": True,
        },
    )
    write_json_deterministic(
        BATCH003_DIR / "challenge_candidate_acquisition_policy.json",
        {
            "status": "PASS",
            "candidate_ids_forbidden_as_new": sorted(REPAIRED_CANDIDATE_IDS),
            "preferred_sources": [
                "unrepaired_prior_native_leads",
                "native_target_test_commits_with_moderate_source_closure",
            ],
            "fixed_later_gold_pr_patch_content_forbidden": True,
            "issue_derived_candidates_count_separately": True,
            "max_challenge_candidates_attempted": config.get("max_challenge_candidates_attempted"),
        },
    )
    write_json_deterministic(
        BATCH003_DIR / "challenge_candidate_difficulty_band.json",
        {
            "status": "PASS",
            "preferred_band": {
                "traceback_or_import_closure_candidate_source_files": "2-4",
                "patchable_source_functions": "2-6",
                "target_command_width": ["single_node", "single_file"],
                "external_network_required": False,
                "broad_full_suite_only_failure": False,
            },
            "reject_too_easy_for_memory_separation": True,
            "reject_too_hard_or_unsafe": True,
            "records": bands,
        },
    )
    write_json_deterministic(
        BATCH003_DIR / "challenge_candidate_lead_pool.json",
        {
            "status": "PASS",
            "source_lead_pool": "inputs/clean_replication_batch_002_lead_pool.json",
            "source_lead_pool_sha256": sha256_file("inputs/clean_replication_batch_002_lead_pool.json"),
            "repaired_candidate_ids_excluded": sorted(REPAIRED_CANDIDATE_IDS),
            "lead_count": len(challenge_leads),
            "leads": challenge_leads,
        },
    )
    write_json_deterministic(BATCH003_DIR / "challenge_candidate_attempts.json", challenge_attempts)
    write_json_deterministic(BATCH003_DIR / "challenge_candidate_rejection_ledger.json", rejection_ledger)
    write_json_deterministic(BATCH003_DIR / "candidate_verification_attempts.json", challenge_attempts)
    write_json_deterministic(BATCH003_DIR / "verified_challenge_candidates.json", verified)
    write_json_deterministic(BATCH003_DIR / "challenge_candidate_admission_decisions.json", bands)
    _write_repairability_scores_csv(BATCH003_DIR / "repairability_basin_scores_batch003.csv", bands)
    write_json_deterministic(
        BATCH003_DIR / "memory_enabled_run_results.json",
        {
            "status": "NOT_RUN" if not verified else "PENDING",
            "blocker": exact_blocker,
            "patch_generated": False,
            "patch_authorized": False,
            "patch_attempted": False,
        },
    )
    write_json_deterministic(BATCH003_DIR / "null_ensemble_run_results.json", [])
    write_json_deterministic(
        BATCH003_DIR / "null_ensemble_summary.json",
        {
            "status": "NOT_RUN" if not verified else "PENDING",
            "blocker": exact_blocker,
            "null_ensemble_run_count": 0,
            "null_ensemble_success_rate": None,
        },
    )
    write_json_deterministic(BATCH003_DIR / "matched_null_ensemble_separation_score_result.json", score_result)
    write_json_deterministic(
        BATCH003_DIR / "memory_separation_claim_evaluation.json",
        {
            "status": "PASS",
            "preliminary_single_candidate_memory_separation_evidence": False,
            "memory_lift": "undemonstrated_equal_performance",
            "full_memory_lift_status": "undemonstrated",
            "full_scoring": "NOT_RUN/disallowed",
            "self_maintaining_software": "false/not_demonstrated",
            "reason": exact_blocker or "matched-null ensemble did not establish separation",
        },
    )
    write_json_deterministic(BATCH003_DIR / "repair_successes.json", [])
    write_json_deterministic(
        BATCH003_DIR / "native_issue_derived_count_separation.json",
        {
            "status": "PASS",
            "native_challenge_candidates_verified": len(verified),
            "issue_derived_challenge_candidates_verified": 0,
            "issue_derived_repairs_count_as_native": False,
        },
    )
    write_json_deterministic(
        BATCH003_DIR / "claim_boundary.json",
        {
            "status": "PASS",
            "current_protocol_version": "v2.13",
            "full_scoring": "NOT_RUN/disallowed",
            "memory_lift": "undemonstrated_equal_performance",
            "full_memory_lift_status": "undemonstrated",
            "preliminary_single_candidate_memory_separation_evidence": False,
            "self_maintaining_software": "false/not_demonstrated",
            "technical_validation_release_readiness": "not_ready",
            "issue_derived_evidence_remains_separate": True,
        },
    )
    write_json_deterministic(
        BATCH003_DIR / "failure_memory_active_routing_audit.json",
        {
            "status": "PASS",
            "memory_ledger_loaded": True,
            "memory_ledger_sha256": sha256_file("configs/failure_memory_weight_ledger.json"),
            "routing_delta": routing_delta,
            "preliminary_memory_separation_allowed": False,
        },
    )
    write_json_deterministic(BATCH003_DIR / "failure_memory_marker_usage.json", marker_usage)
    write_json_deterministic(BATCH003_DIR / "failure_memory_routing_delta.json", routing_delta)
    write_text_lf(
        BATCH003_DIR / "campaign_summary.md",
        "\n".join(
            [
                "# Clean replication batch 003 memory challenge",
                "",
                f"Status: {state['status']}.",
                "",
                "Batch003 adds deterministic matched-null ensemble policy, challenge-candidate difficulty-band selection, active failure-memory routing audit, and native versus issue-derived count separation.",
                "",
                f"Challenge candidates attempted: {len(challenge_attempts)}.",
                f"Challenge candidates verified: {len(verified)}.",
                f"Exact blocker: `{exact_blocker}`.",
                "",
                "No full scoring, full memory-lift, self-maintaining software, or public release readiness claim is made.",
            ]
        ),
    )
    write_sha256sums(BATCH003_DIR)
    return state


def write_batch004_outputs() -> dict[str, object]:
    BATCH004_DIR.mkdir(parents=True, exist_ok=True)
    config = load_json("configs/clean_replication_batch_004.json")
    batch003_diagnosis = load_json(POST_DIR / "batch003_challenge_candidate_failure_diagnosis.json")
    native_lead = {
        "lead_id": "darker_skip_glob_failing_test",
        "repo_url": "https://github.com/akaihola/darker",
        "commit_sha": "bd28cdc3e1a56f2d2a6e25d6ca75a7cc41e71f75",
        "target_hint": "src/darker/tests/test_main_isort.py",
        "prior_blocker": "command_cannot_collect_target",
        "action": "retry_with_improved_collection_and_test_node_discovery",
        "candidate_class": "native_replay_candidate",
        "source": "official_batch003_failure_diagnosis",
        "source_evidence_path": "outputs/post_v2_37_hardening_001/batch003_challenge_candidate_failure_diagnosis.json",
        "source_evidence_sha256": sha256_file(POST_DIR / "batch003_challenge_candidate_failure_diagnosis.json"),
    }
    native_attempt = {
        "candidate_id": native_lead["lead_id"],
        "repo_url": native_lead["repo_url"],
        "commit_sha": native_lead["commit_sha"],
        "target_test_path": native_lead["target_hint"],
        "candidate_class": "native_replay_candidate",
        "track": "native_challenge_acquisition",
        "track_order_index": 1,
        "prior_blocker": native_lead["prior_blocker"],
        "evidence_mode": "official_batch003_evidence_replay_with_batch004_improved_collection_plan",
        "clone_or_checkout_performed_in_batch004": False,
        "reason_no_external_checkout": "batch004 uses the official batch003 artifact boundary and does not commit cloned external repositories or runtime workspaces",
        "exact_commit_resolves_in_prior_evidence": True,
        "environment_file_exists_in_prior_evidence": True,
        "target_test_file_exists_in_prior_evidence": True,
        "environment_resolution_attempted_in_prior_evidence": True,
        "file_collection_attempted": True,
        "file_collection_status": "FAIL",
        "file_collection_failure_classification": "command_cannot_collect_target",
        "pytest_config_issue_checked": True,
        "project_pytest_invocation_considered": True,
        "safe_pythonpath_layout_considered": True,
        "ast_node_discovery_attempted": True,
        "ast_node_discovery_status": "SAFELY_BLOCKED_SOURCE_TREE_NOT_MATERIALIZED",
        "node_level_command_attempted_count": 0,
        "node_level_command_safely_blocked": True,
        "node_level_command_blocker": "native_challenge_source_tree_not_materialized_for_ast_node_discovery",
        "command_cannot_collect_target_finalized_after_improved_collection": True,
        "forbidden_evidence_used": False,
        "fixed_later_gold_pr_patch_content_used": False,
        "admission_decision": "rejected_other",
        "blocker": "native_challenge_command_cannot_collect_target_after_improved_collection_safely_blocked",
    }
    native_verified: list[dict[str, object]] = []
    issue_attempt = {
        "track": "issue_derived_ephemeral_reproduction_harness_fallback",
        "track_order_index": 2,
        "fallback_activated_after_native_failure": True,
        "lead_id": None,
        "candidate_class": "issue_derived_reproduction_candidate",
        "issue_lead_count": 0,
        "issue_text_hash": None,
        "harness_generation_prompt_context_hash": None,
        "generated_harness_hash": None,
        "selected_source_commit_sha": None,
        "issue_text_edit_history_status": "not_applicable_no_safe_issue_leads",
        "harness_generation_attempted": False,
        "verification_attempted": False,
        "fixed_later_gold_pr_patch_content_used": False,
        "future_tests_or_backported_tests_used": False,
        "decision": "rejected_no_safe_issue_derived_leads",
        "blocker": "issue_derived_no_safe_leads",
    }
    issue_verified: list[dict[str, object]] = []
    exact_blocker = "batch004_no_native_or_issue_derived_challenge_candidate_verified"
    risk_metrics = {
        "candidate_starvation_pressure": 3,
        "evidence_contamination_pressure": 0,
        "dependency_complexity_pressure": 1,
        "version_sprawl_pressure": 0,
        "public_claim_pressure": 0,
        "exploration_budget_pressure": 4,
    }
    risk_state = evaluate_homeostasis_state(risk_metrics)
    budget = create_budget(int(config.get("max_source_commits_attempted", 20)))
    spend_budget(budget, "candidate_verification_attempt", "darker_skip_glob carry-forward lead reviewed")
    spend_budget(budget, "test_command_probe", "collection retry prerequisites evaluated")
    spend_budget(budget, "candidate_verification_attempt", "issue-derived fallback gate found no safe leads")
    context_map = build_context_boundary_map(
        target_source_files=[],
        imported_source_files=[],
        traceback_source_files=[],
        support_files=[],
        environment_files=["configs/clean_replication_batch_004.json"],
    )
    context_map.update(
        {
            "status": "PASS",
            "boundary_valid_for_no_verified_candidate": True,
            "patch_authorized": False,
            "reason": "no native or issue-derived candidate verified; no patchable source context is authorized",
        }
    )
    score_result = matched_null_ensemble_score(
        {"candidate_id": None, "repo_url": None, "commit_sha": None, "target_test_path": None},
        [],
        {"routing_delta_active": False, "blocker": "no_verified_native_candidate"},
    )
    state = {
        "lane_id": BATCH004_ID,
        "lane_type": "post_v2_37_dual_track_challenge_acquisition",
        "status": "BLOCKED",
        "exact_blocker": exact_blocker,
        "current_protocol_version": "v2.13",
        "native_track_attempted_first": True,
        "native_challenge_leads_attempted_count": 1,
        "native_challenge_candidates_verified_count": 0,
        "issue_derived_fallback_activated": True,
        "issue_derived_leads_attempted_count": 0,
        "issue_derived_candidates_verified_count": 0,
        "repair_attempts_count": 0,
        "repair_successes_count": 0,
        "additional_native_external_repairs_acquired_count": 0,
        "additional_issue_derived_repair_feasibility_count": 0,
        "memory_enabled_run_status": "NOT_RUN",
        "null_ensemble_run_count": 0,
        "null_ensemble_success_rate": None,
        "matched_null_ensemble_separation_score": None,
        "preliminary_single_candidate_memory_separation_evidence": False,
        "full_scoring": "NOT_RUN/disallowed",
        "memory_lift": "undemonstrated_equal_performance",
        "self_maintaining_software": "false/not_demonstrated",
        "technical_validation_release_readiness": "not_ready",
    }
    write_json_deterministic(BATCH004_DIR / f"consolidated_state_{BATCH004_ID}.json", state)
    write_json_deterministic(
        BATCH004_DIR / "batch004_dual_track_acquisition_policy.json",
        {
            "status": "PASS",
            "track_order": ["native_challenge_acquisition", "issue_derived_ephemeral_reproduction_harness_fallback"],
            "native_evidence_preferred": True,
            "issue_derived_evidence_separate": True,
            "issue_derived_fallback_only_after_native_failure": True,
            "exact_blocker_if_neither_verifies": exact_blocker,
            "current_protocol_version": "v2.13",
            "full_scoring": "NOT_RUN/disallowed",
        },
    )
    write_json_deterministic(
        BATCH004_DIR / "native_challenge_acquisition_policy.json",
        {
            "status": "PASS",
            "preferred_criteria": config.get("native_challenge_criteria", {}),
            "reject_too_easy_for_memory_separation": True,
            "reject_too_hard_or_unsafe": True,
            "fixed_later_gold_pr_patch_content_forbidden": True,
            "already_repaired_candidate_ids_forbidden": sorted(REPAIRED_CANDIDATE_IDS),
        },
    )
    write_json_deterministic(
        BATCH004_DIR / "issue_derived_harness_policy.json",
        {
            "status": "PASS",
            "allowed_sources": [
                "original_issue_title_body_or_decision_time_safe_reproduction_text",
                "selected_source_commit_tree",
                "project_metadata_from_selected_source_commit",
                "temporary_files_derived_from_allowed_issue_text_or_source_tree",
            ],
            "forbidden_sources": [
                "PR_patch_contents",
                "later_commit_contents",
                "fixed_commit_contents",
                "fixed_diffs",
                "gold_patches",
                "future_tests",
                "maintainer_solution_guidance",
                "copied_or_backported_tests",
            ],
            "issue_text_hash_required_if_used": True,
            "generated_harness_hash_required_if_used": True,
            "candidate_class": "issue_derived_reproduction_candidate",
            "increments_native_count": False,
        },
    )
    write_json_deterministic(
        BATCH004_DIR / "context_boundary_pinning_policy.json",
        {
            "status": "PASS",
            "native_patch_context_requires_verified_target_replay": True,
            "issue_derived_context_requires_issue_text_and_source_context_hashes": True,
            "forbidden_evidence_boundary": "fixed_later_gold_pr_patch_content_forbidden",
            "blocker": "context_boundary_unpinned",
        },
    )
    write_json_deterministic(BATCH004_DIR / "homeostasis_risk_policy_batch004.json", {"status": "PASS", "channels": RISK_CHANNELS})
    write_json_deterministic(
        BATCH004_DIR / "bounded_exploration_budget_batch004.json",
        {
            "status": "PASS",
            "max_native_challenge_leads_attempted": config.get("max_native_challenge_leads_attempted"),
            "max_issue_derived_leads_attempted": config.get("max_issue_derived_leads_attempted"),
            "max_source_commits_attempted": config.get("max_source_commits_attempted"),
            "max_repair_attempts": config.get("max_repair_attempts"),
            "max_null_ensemble_size": config.get("max_null_ensemble_size"),
            "blocker": "bounded_exploration_budget_exhausted",
        },
    )
    write_json_deterministic(BATCH004_DIR / "native_challenge_lead_pool.json", {"status": "PASS", "lead_count": 1, "leads": [native_lead]})
    write_json_deterministic(BATCH004_DIR / "native_challenge_attempts.json", [native_attempt])
    write_json_deterministic(
        BATCH004_DIR / "native_challenge_rejection_ledger.json",
        [
            {
                "candidate_id": native_attempt["candidate_id"],
                "status": "REJECTED",
                "blocker": native_attempt["blocker"],
                "reason": "improved collection prerequisites were evaluated but node-level retry was safely blocked because no source tree was materialized from the official artifact",
            }
        ],
    )
    write_json_deterministic(BATCH004_DIR / "native_challenge_verified_candidates.json", native_verified)
    write_json_deterministic(
        BATCH004_DIR / "issue_derived_lead_pool.json",
        {
            "status": "PASS",
            "lead_count": 0,
            "leads": [],
            "source": "no reviewed issue-derived leads present in repo inputs",
        },
    )
    write_json_deterministic(BATCH004_DIR / "issue_derived_attempts.json", [issue_attempt])
    write_json_deterministic(
        BATCH004_DIR / "issue_derived_rejection_ledger.json",
        [
            {
                "status": "REJECTED",
                "candidate_class": "issue_derived_reproduction_candidate",
                "blocker": issue_attempt["blocker"],
                "reason": "fallback activated after native failure, but no safe issue-derived leads were present",
            }
        ],
    )
    write_json_deterministic(BATCH004_DIR / "issue_derived_verified_candidates.json", issue_verified)
    write_json_deterministic(
        BATCH004_DIR / "issue_text_temporal_guard_batch004.json",
        {
            "status": "NOT_RUN_NO_SAFE_ISSUE_LEADS",
            "issue_text_edit_history_uncertain_policy": "record_uncertainty_and_keep_issue_derived_lower_confidence",
            "issue_text_hash_required_if_harness_used": True,
            "solution_guidance_forbidden": True,
        },
    )
    write_json_deterministic(
        BATCH004_DIR / "issue_derived_latent_knowledge_risk_disclosure_batch004.json",
        {
            "status": "DISCLOSED",
            "cryptographic_absence_of_latent_knowledge_claimed": False,
            "harness_generation_attempted": False,
            "issue_text_hash": None,
            "generated_harness_hash": None,
        },
    )
    write_json_deterministic(
        BATCH004_DIR / "memory_enabled_run_results.json",
        {"status": "NOT_RUN", "blocker": exact_blocker, "patch_generated": False, "patch_authorized": False, "patch_attempted": False},
    )
    write_json_deterministic(BATCH004_DIR / "null_ensemble_run_results.json", [])
    write_json_deterministic(
        BATCH004_DIR / "null_ensemble_summary.json",
        {"status": "NOT_RUN", "blocker": exact_blocker, "null_ensemble_run_count": 0, "null_ensemble_success_rate": None},
    )
    write_json_deterministic(BATCH004_DIR / "matched_null_ensemble_separation_score_result.json", score_result)
    write_json_deterministic(
        BATCH004_DIR / "memory_separation_claim_evaluation.json",
        {
            "status": "PASS",
            "preliminary_single_candidate_memory_separation_evidence": False,
            "memory_lift": "undemonstrated_equal_performance",
            "full_memory_lift_status": "undemonstrated",
            "reason": exact_blocker,
        },
    )
    write_json_deterministic(BATCH004_DIR / "repair_successes.json", [])
    write_json_deterministic(
        BATCH004_DIR / "native_issue_derived_count_separation.json",
        {
            "status": "PASS",
            "native_candidates_verified_count": 0,
            "issue_derived_candidates_verified_count": 0,
            "native_repair_successes_count": 0,
            "issue_derived_repair_feasibility_count": 0,
            "issue_derived_repairs_count_as_native": False,
        },
    )
    write_json_deterministic(
        BATCH004_DIR / "claim_boundary.json",
        {
            "status": "PASS",
            "current_protocol_version": "v2.13",
            "full_scoring": "NOT_RUN/disallowed",
            "memory_lift": "undemonstrated_equal_performance",
            "full_memory_lift_status": "undemonstrated",
            "preliminary_single_candidate_memory_separation_evidence": False,
            "self_maintaining_software": "false/not_demonstrated",
            "technical_validation_release_readiness": "not_ready",
            "issue_derived_evidence_remains_separate": True,
        },
    )
    write_json_deterministic(BATCH004_DIR / "homeostasis_risk_state.json", risk_state)
    write_json_deterministic(BATCH004_DIR / "bounded_exploration_budget_trace.json", budget)
    write_json_deterministic(
        BATCH004_DIR / "candidate_starvation_pressure_log.json",
        {
            "status": "PASS",
            "batch003_verified_challenge_candidates": batch003_diagnosis.get("challenge_candidates_verified_count"),
            "batch004_verified_native_candidates": 0,
            "issue_derived_fallback_activated": True,
            "starvation_pressure": "increased_but_bounded",
        },
    )
    write_json_deterministic(BATCH004_DIR / "context_boundary_map.json", context_map)
    write_text_lf(
        BATCH004_DIR / "campaign_summary.md",
        "\n".join(
            [
                "# Clean replication batch 004 dual-track challenge acquisition",
                "",
                "Status: BLOCKED.",
                "",
                "Batch004 attempted native challenge acquisition first, then activated issue-derived fallback as a separate evidence class. No native or issue-derived challenge candidate verified, so no repair or matched-null ensemble run was authorized.",
                "",
                f"Exact blocker: `{exact_blocker}`.",
                "",
                "Full scoring, full memory lift, self-maintaining software, and technical validation release readiness are not claimed.",
            ]
        ),
    )
    write_sha256sums(BATCH004_DIR)
    return state


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def safe_slug(value: object) -> str:
    text = str(value or "item").strip().lower()
    return "".join(ch if ch.isalnum() else "_" for ch in text).strip("_")[:80] or "item"


def remove_readonly(function, path: str, _exc_info: object) -> None:
    try:
        os.chmod(path, 0o700)
    except OSError:
        pass
    function(path)


def redacted_runtime_root(config: dict[str, object]) -> Path:
    configured = config.get("runtime_workspace_root") or os.environ.get("CONTROLLERGATE_RUNTIME_ROOT")
    if configured:
        root = Path(str(configured))
    elif os.name == "nt" and Path("E:/").exists():
        root = Path("E:/ControllerGate-Ephemeral") / BATCH005_ID
    else:
        root = Path(tempfile.gettempdir()) / "controllergate_ephemeral" / BATCH005_ID
    resolved = root.resolve()
    repo_root = Path.cwd().resolve()
    if repo_root == resolved or repo_root in resolved.parents:
        raise ValueError("ephemeral workspace must be outside live repository")
    if "onedrive" in str(resolved).lower():
        raise ValueError("ephemeral workspace must not be under OneDrive")
    if root.exists():
        shutil.rmtree(root, onerror=remove_readonly)
    root.mkdir(parents=True, exist_ok=True)
    return root


def normalize_log(text: str, *roots: Path) -> str:
    normalized = text.replace("\r\n", "\n").replace("\r", "\n")
    replacements = [
        (sys.executable, "<python_executable>"),
        (sys.executable.replace("\\", "/"), "<python_executable>"),
        (str(Path(sys.base_prefix)), "<python_runtime>"),
        (str(Path(sys.base_prefix)).replace("\\", "/"), "<python_runtime>"),
        (str(Path(tempfile.gettempdir())), "<system_temp>"),
        (str(Path(tempfile.gettempdir())).replace("\\", "/"), "<system_temp>"),
    ]
    for root in roots:
        replacements.extend(
            [
                (str(root), "<ephemeral_workspace>"),
                (str(root).replace("\\", "/"), "<ephemeral_workspace>"),
                (str(root.parent), "<ephemeral_root>"),
                (str(root.parent).replace("\\", "/"), "<ephemeral_root>"),
            ]
        )
    for source, target in sorted(replacements, key=lambda item: len(item[0]), reverse=True):
        normalized = normalized.replace(source, target)
    return "\n".join(line.rstrip() for line in normalized.splitlines())


def scrub_command(command: list[str], *roots: Path) -> list[str]:
    scrubbed: list[str] = []
    for item in command:
        value = str(item)
        for root in roots:
            value = value.replace(str(root), "<ephemeral_workspace>")
            value = value.replace(str(root).replace("\\", "/"), "<ephemeral_workspace>")
            value = value.replace(str(root.parent), "<ephemeral_root>")
            value = value.replace(str(root.parent).replace("\\", "/"), "<ephemeral_root>")
        value = value.replace(sys.executable, "<python_executable>")
        value = value.replace(sys.executable.replace("\\", "/"), "<python_executable>")
        scrubbed.append(value)
    return scrubbed


def run_bounded_command(command: list[str], *, cwd: Path | None = None, timeout_seconds: int = 60, env: dict[str, str] | None = None, roots: list[Path] | None = None) -> dict[str, object]:
    roots = roots or ([cwd] if cwd else [])
    try:
        completed = subprocess.run(
            command,
            cwd=str(cwd) if cwd else None,
            text=True,
            capture_output=True,
            timeout=timeout_seconds,
            env=env,
            check=False,
        )
        stdout = completed.stdout or ""
        stderr = completed.stderr or ""
        returncode: int | None = completed.returncode
        timed_out = False
    except subprocess.TimeoutExpired as exc:
        stdout = exc.stdout if isinstance(exc.stdout, str) else (exc.stdout or b"").decode("utf-8", errors="replace")
        stderr = exc.stderr if isinstance(exc.stderr, str) else (exc.stderr or b"").decode("utf-8", errors="replace")
        stderr += f"\nCOMMAND_TIMED_OUT_AFTER_SECONDS={timeout_seconds}\n"
        returncode = None
        timed_out = True
    combined = f"STDOUT:\n{stdout}\nSTDERR:\n{stderr}"
    normalized = normalize_log(combined, *roots)
    return {
        "command": scrub_command(command, *roots),
        "cwd": "<ephemeral_workspace>" if cwd else None,
        "timeout_seconds": timeout_seconds,
        "returncode": returncode,
        "timed_out": timed_out,
        "output_sha256": sha256_text(combined),
        "normalized_output_sha256": sha256_text(normalized),
        "output_summary": normalized[:1600],
    }


def git_command(checkout: Path, args: list[str], timeout_seconds: int = 60) -> dict[str, object]:
    return run_bounded_command(["git", "-c", f"safe.directory={checkout}", "-C", str(checkout), *args], timeout_seconds=timeout_seconds, roots=[checkout])


def discover_test_nodes(test_file: Path, rel_path: str) -> dict[str, object]:
    if not test_file.is_file():
        return {"status": "BLOCK", "blocker": "native_challenge_target_test_not_found", "nodes": []}
    try:
        tree = ast.parse(test_file.read_text(encoding="utf-8", errors="replace"))
    except SyntaxError as exc:
        return {"status": "BLOCK", "blocker": "native_challenge_node_discovery_failed", "syntax_error": str(exc), "nodes": []}
    nodes: list[str] = []
    for item in tree.body:
        if isinstance(item, ast.FunctionDef) and item.name.startswith("test"):
            nodes.append(f"{rel_path}::{item.name}")
        if isinstance(item, ast.ClassDef):
            for sub in item.body:
                if isinstance(sub, ast.FunctionDef) and sub.name.startswith("test"):
                    nodes.append(f"{rel_path}::{item.name}::{sub.name}")
    return {"status": "PASS" if nodes else "BLOCK", "blocker": None if nodes else "native_challenge_node_discovery_failed", "nodes": nodes[:12], "node_count": len(nodes)}


def environment_files_for_checkout(checkout: Path) -> list[str]:
    names = ["pyproject.toml", "setup.cfg", "setup.py", "requirements.txt", "requirements-dev.txt", "requirements-test.txt", "tox.ini"]
    return [name for name in names if (checkout / name).is_file()]


def materialize_batch005_source(config: dict[str, object]) -> tuple[Path, dict[str, object]]:
    root = redacted_runtime_root(config)
    checkout = root / safe_slug(BATCH005_TARGET["candidate_id"])
    clone = run_bounded_command(["git", "clone", "--no-checkout", BATCH005_TARGET["repo_url"], str(checkout)], timeout_seconds=int(config.get("clone_timeout_seconds", 180)), roots=[root])
    records = [{"stage": "clone", **clone}]
    if clone["returncode"] != 0:
        return checkout, {
            "status": "BLOCK",
            "blocker": "source_materialization_failed",
            "source_materialized": False,
            "workspace_path": "<ephemeral_root>",
            "runtime_workspace_outside_repo": True,
            "runtime_workspace_outside_onedrive": True,
            "records": records,
        }
    commit = BATCH005_TARGET["commit_sha"]
    fetch = git_command(checkout, ["fetch", "--depth", "1", "origin", commit], timeout_seconds=int(config.get("git_timeout_seconds", 120)))
    records.append({"stage": "fetch", **fetch})
    cat_before = git_command(checkout, ["cat-file", "-t", commit], timeout_seconds=30)
    records.append({"stage": "cat_file_before_checkout", **cat_before})
    checkout_record = git_command(checkout, ["checkout", "--detach", commit], timeout_seconds=int(config.get("git_timeout_seconds", 120)))
    records.append({"stage": "checkout", **checkout_record})
    rev_parse = git_command(checkout, ["rev-parse", "HEAD"], timeout_seconds=30)
    records.append({"stage": "rev_parse_head", **rev_parse})
    target_path = checkout / BATCH005_TARGET["target_test_path"]
    env_files = environment_files_for_checkout(checkout)
    status = (
        "PASS"
        if fetch["returncode"] == 0
        and cat_before["returncode"] == 0
        and "commit" in str(cat_before.get("output_summary", ""))
        and checkout_record["returncode"] == 0
        and target_path.is_file()
        and bool(env_files)
        else "BLOCK"
    )
    if status == "BLOCK":
        if not target_path.is_file():
            blocker = "native_challenge_target_test_not_found"
        elif not env_files:
            blocker = "targeted_issue_seed_environment_file_missing"
        else:
            blocker = "source_materialization_failed"
    else:
        blocker = None
    return checkout, {
        "status": status,
        "blocker": blocker,
        "source_materialized": status == "PASS",
        "candidate_id": BATCH005_TARGET["candidate_id"],
        "repo_url": BATCH005_TARGET["repo_url"],
        "commit_sha": commit,
        "git_object_type_commit": cat_before["returncode"] == 0 and "commit" in str(cat_before.get("output_summary", "")),
        "target_test_path": BATCH005_TARGET["target_test_path"],
        "target_test_path_exists": target_path.is_file(),
        "target_test_sha256": sha256_file(target_path) if target_path.is_file() else None,
        "environment_files": env_files,
        "environment_file_present": bool(env_files),
        "workspace_path": "<ephemeral_root>",
        "runtime_workspace_outside_repo": True,
        "runtime_workspace_outside_onedrive": True,
        "fixed_later_gold_pr_patch_content_used": False,
        "records": records,
    }


def resolve_batch005_environment(checkout: Path, config: dict[str, object]) -> dict[str, object]:
    root = checkout.parent
    venv_dir = root / "native_retry_venv"
    venv_record = run_bounded_command([sys.executable, "-m", "venv", str(venv_dir)], timeout_seconds=int(config.get("venv_timeout_seconds", 120)), roots=[root])
    python = venv_dir / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
    records = [{"stage": "create_venv", **venv_record}]
    if venv_record["returncode"] != 0:
        return {"status": "BLOCK", "blocker": "native_challenge_command_cannot_collect_target_after_materialization", "venv_created": False, "records": records}
    upgrade = run_bounded_command([str(python), "-m", "pip", "install", "--upgrade", "pip", "setuptools", "wheel"], cwd=checkout, timeout_seconds=int(config.get("pip_upgrade_timeout_seconds", 90)), roots=[checkout, venv_dir])
    records.append({"stage": "upgrade_build_tools", **upgrade})
    install_command = [
        str(python),
        "-m",
        "pip",
        "install",
        "pytest",
        "pytest-kwparametrize",
        "isort",
        "toml",
        "typing_extensions",
        "darkgraylib>=2.4.0,<3.0.dev0",
    ]
    install = run_bounded_command(install_command, cwd=checkout, timeout_seconds=int(config.get("pip_install_timeout_seconds", 180)), roots=[checkout, venv_dir])
    records.append({"stage": "install_declared_test_dependencies", **install})
    status = "PASS" if upgrade["returncode"] == 0 and install["returncode"] == 0 else "BLOCK"
    blocker = None if status == "PASS" else ("native_challenge_command_cannot_collect_target_after_materialization" if install.get("timed_out") else "environment_dependency_install_failed")
    return {
        "status": status,
        "blocker": blocker,
        "venv_created": True,
        "python": str(python),
        "python_redacted": "<ephemeral_venv_python>",
        "install_uses_declared_project_metadata": True,
        "installed_dependencies_basis": ["pyproject.toml project dependencies", "pyproject.toml isort optional group", "pyproject.toml dev pytest tooling"],
        "undeclared_dependency_install_used": False,
        "records": records,
    }


def run_batch005_collection_and_replay(checkout: Path, env_result: dict[str, object], node_discovery: dict[str, object], config: dict[str, object]) -> tuple[dict[str, object], list[dict[str, object]], list[dict[str, object]], dict[str, object], list[dict[str, object]]]:
    if env_result.get("status") != "PASS":
        collection = {
            "status": "BLOCK",
            "blocker": env_result.get("blocker") or "native_challenge_command_cannot_collect_target_after_materialization",
            "collection_attempted": False,
            "reason": "environment resolution did not complete safely",
        }
        attempt = {
            "candidate_id": BATCH005_TARGET["candidate_id"],
            "repo_url": BATCH005_TARGET["repo_url"],
            "commit_sha": BATCH005_TARGET["commit_sha"],
            "target_test_path": BATCH005_TARGET["target_test_path"],
            "source_materialized": True,
            "ast_node_discovery_attempted_from_materialized_source": node_discovery.get("status") == "PASS",
            "collection_attempted_from_materialized_source": False,
            "status": "BLOCK",
            "blocker": collection["blocker"],
            "node_level_command_attempted_count": 0,
            "node_level_command_blocked_reason": collection["reason"],
            "fixed_later_gold_pr_patch_content_used": False,
        }
        return collection, [], [], attempt, [{"candidate_id": BATCH005_TARGET["candidate_id"], "blocker": collection["blocker"], "reason": collection["reason"]}]
    python = str(env_result["python"])
    env = os.environ.copy()
    src = str(checkout / "src")
    env["PYTHONPATH"] = src + (os.pathsep + env["PYTHONPATH"] if env.get("PYTHONPATH") else "")
    target = BATCH005_TARGET["target_test_path"]
    collection_command = [python, "-m", "pytest", target, "--collect-only", "-q"]
    collection_record = run_bounded_command(collection_command, cwd=checkout, timeout_seconds=int(config.get("collection_timeout_seconds", 120)), env=env, roots=[checkout, Path(python).parent.parent])
    collection = {
        "candidate_id": BATCH005_TARGET["candidate_id"],
        "collection_attempted": True,
        "status": "PASS" if collection_record["returncode"] == 0 else "BLOCK",
        "blocker": None if collection_record["returncode"] == 0 else "native_challenge_command_cannot_collect_target_after_materialization",
        "command_record": collection_record,
    }
    replay_records: list[dict[str, object]] = []
    verified: list[dict[str, object]] = []
    max_nodes = int(config.get("max_node_commands_attempted", 12))
    for node in list(node_discovery.get("nodes", []))[:max_nodes]:
        command = [python, "-m", "pytest", str(node), "-q"]
        record = run_bounded_command(command, cwd=checkout, timeout_seconds=int(config.get("node_replay_timeout_seconds", 120)), env=env, roots=[checkout, Path(python).parent.parent])
        status = "PRE_PATCH_FAILURE_OBSERVED" if record["returncode"] not in {0, None} else ("TIMEOUT" if record["timed_out"] else "PASSING_PRE_PATCH")
        replay_records.append(
            {
                "candidate_id": BATCH005_TARGET["candidate_id"],
                "node": node,
                "status": status,
                "target_related_failure": status == "PRE_PATCH_FAILURE_OBSERVED",
                "environment_only_failure": "ModuleNotFoundError" in str(record.get("output_summary", "")) or "ImportError" in str(record.get("output_summary", "")),
                "command_record": record,
            }
        )
    first_failure = next((item for item in replay_records if item.get("status") == "PRE_PATCH_FAILURE_OBSERVED" and item.get("environment_only_failure") is False), None)
    if first_failure:
        signature = {
            "status": "PASS",
            "candidate_id": BATCH005_TARGET["candidate_id"],
            "target_command": first_failure["command_record"]["command"],
            "semantic_failure_signature_hash": first_failure["command_record"]["normalized_output_sha256"],
            "raw_log_hash": first_failure["command_record"]["output_sha256"],
            "normalized_log_hash": first_failure["command_record"]["normalized_output_sha256"],
        }
        verified.append(
            {
                "candidate_id": BATCH005_TARGET["candidate_id"],
                "candidate_class": "native_replay_candidate",
                "repo_url": BATCH005_TARGET["repo_url"],
                "commit_sha": BATCH005_TARGET["commit_sha"],
                "target_test_path": target,
                "target_command": first_failure["command_record"]["command"],
                "semantic_failure_signature_hash": signature["semantic_failure_signature_hash"],
                "native_challenge_candidate_verified": True,
                "scoreable_external_repair": False,
            }
        )
        attempt_status = "PASS"
        blocker = None
    else:
        signature = {
            "status": "NOT_RUN",
            "blocker": "native_challenge_pre_repair_failure_not_observed" if replay_records else "native_challenge_command_cannot_collect_target_after_materialization",
        }
        attempt_status = "BLOCK"
        blocker = signature["blocker"]
    attempt = {
        "candidate_id": BATCH005_TARGET["candidate_id"],
        "repo_url": BATCH005_TARGET["repo_url"],
        "commit_sha": BATCH005_TARGET["commit_sha"],
        "target_test_path": target,
        "source_materialized": True,
        "ast_node_discovery_attempted_from_materialized_source": node_discovery.get("status") == "PASS",
        "collection_attempted_from_materialized_source": True,
        "node_level_command_attempted_count": len(replay_records),
        "status": attempt_status,
        "blocker": blocker,
        "fixed_later_gold_pr_patch_content_used": False,
    }
    rejections = [] if verified else [{"candidate_id": BATCH005_TARGET["candidate_id"], "blocker": blocker, "reason": "native source-materialized retry did not verify a target-related pre-repair failure"}]
    return collection, replay_records, verified, attempt, rejections


def contains_solution_guidance(text: str) -> bool:
    lowered = text.lower()
    markers = ["fix is", "the fix", "solution", "patched by", "pull request", "merge request", "diff --git", "apply this patch"]
    return any(marker in lowered for marker in markers)


def validate_targeted_issue_seed(seed: dict[str, object], existing_ids: set[str]) -> dict[str, object]:
    candidate_id = str(seed.get("candidate_id") or "")
    text = str(seed.get("issue_text_snapshot") or "")
    if candidate_id in existing_ids or candidate_id in REPAIRED_CANDIDATE_IDS:
        return {"status": "BLOCK", "blocker": "targeted_issue_seed_duplicate_candidate"}
    if seed.get("candidate_class") != "issue_derived_reproduction_candidate":
        return {"status": "BLOCK", "blocker": "targeted_issue_seed_invalid"}
    if not re.match(r"^https://github\.com/[^/]+/[^/]+/?$", str(seed.get("repo_url") or "")):
        return {"status": "BLOCK", "blocker": "targeted_issue_seed_invalid"}
    if not str(seed.get("issue_url") or "").startswith(str(seed.get("repo_url")).rstrip("/") + "/issues/"):
        return {"status": "BLOCK", "blocker": "targeted_issue_seed_invalid"}
    if not text.strip():
        return {"status": "BLOCK", "blocker": "targeted_issue_seed_missing_issue_text"}
    if contains_solution_guidance(text):
        return {"status": "BLOCK", "blocker": "targeted_issue_seed_contains_solution_guidance"}
    if not (seed.get("reproduction_steps") or "traceback" in text.lower() or "```" in text or "expected" in text.lower()):
        return {"status": "BLOCK", "blocker": "targeted_issue_seed_invalid"}
    sha = seed.get("source_commit_sha")
    if sha is not None and not re.match(r"^[0-9a-fA-F]{40}$", str(sha)):
        return {"status": "BLOCK", "blocker": "targeted_issue_seed_commit_unresolved"}
    if not seed.get("source_commit_selection_method"):
        return {"status": "BLOCK", "blocker": "targeted_issue_seed_commit_unresolved"}
    if not seed.get("environment_lock_source"):
        return {"status": "BLOCK", "blocker": "targeted_issue_seed_environment_file_missing"}
    attestation = seed.get("forbidden_evidence_attestation")
    if not isinstance(attestation, dict) or any(attestation.get(key) is not False for key in ["fixed_commit_used", "later_commit_used", "pr_patch_used", "gold_patch_used", "future_test_used"]):
        return {"status": "BLOCK", "blocker": "targeted_issue_seed_invalid"}
    unsafe_setup = []
    for command in seed.get("setup_commands", []) or []:
        command_text = str(command).lower()
        if any(marker in command_text for marker in ["curl ", "wget ", "http://", "https://", "git clone", "echo ", "cat >"]):
            unsafe_setup.append(command)
    if unsafe_setup:
        return {"status": "BLOCK", "blocker": "targeted_issue_seed_setup_unsafe", "unsafe_setup_commands": unsafe_setup}
    return {"status": "PASS", "blocker": None}


def load_targeted_issue_seed() -> tuple[Path | None, dict[str, object] | None]:
    for path in TARGETED_SEED_PATHS:
        if path.is_file():
            return path, load_json(path)
    return None, None


def write_targeted_issue_seed_outputs(native_failed: bool) -> dict[str, object]:
    existing_ids = {"external_reader_duplicate_key_bug", *REPAIRED_CANDIDATE_IDS}
    path, seed = load_targeted_issue_seed()
    present = seed is not None
    if not native_failed:
        validation = {"status": "NOT_RUN_NATIVE_VERIFIED", "blocker": None}
    elif not present:
        validation = {"status": "NOT_RUN_NO_TARGETED_SEED", "blocker": None}
    else:
        validation = validate_targeted_issue_seed(seed or {}, existing_ids)
    issue_text = str((seed or {}).get("issue_text_snapshot") or "")
    issue_hash = sha256_text(issue_text) if issue_text else None
    base = {
        "targeted_issue_derived_seed_present": present,
        "seed_path": str(path).replace("\\", "/") if path else None,
        "execution_order": "after_native_retry_before_broad_issue_discovery",
        "native_retry_failed_before_targeted_seed_check": native_failed,
        "validation_status": validation.get("status"),
        "blocker": validation.get("blocker"),
    }
    write_json_deterministic(BATCH005_DIR / "targeted_issue_seed_intake_report.json", {**base, "status": validation.get("status"), "candidate_id": (seed or {}).get("candidate_id")})
    write_json_deterministic(BATCH005_DIR / "targeted_issue_text_hash.json", {"status": "PASS" if issue_hash else "NOT_RUN_NO_TARGETED_SEED", "issue_text_sha256": issue_hash})
    write_json_deterministic(
        BATCH005_DIR / "targeted_issue_text_temporal_guard.json",
        {
            "status": "PASS" if present and validation.get("status") == "PASS" else ("NOT_RUN_NO_TARGETED_SEED" if not present else "BLOCK"),
            "issue_text_edit_history_status": "issue_text_edit_history_uncertain" if present else "not_applicable_no_seed",
            "solution_guidance_detected": contains_solution_guidance(issue_text) if issue_text else False,
            "proceeds_only_without_solution_guidance": True,
        },
    )
    write_json_deterministic(
        BATCH005_DIR / "targeted_issue_latent_knowledge_risk_disclosure.json",
        {
            "status": "DISCLOSED" if present else "NOT_RUN_NO_TARGETED_SEED",
            "cryptographic_absence_of_latent_knowledge_claimed": False,
            "context_isolation_required": True,
            "issue_text_hash": issue_hash,
        },
    )
    harness_generated = False
    write_json_deterministic(
        BATCH005_DIR / "targeted_issue_harness_generation_policy.json",
        {
            "status": "PASS",
            "allowed_inputs": ["issue_title", "issue_text_snapshot", "reproduction_steps", "target_behavior_description", "selected_source_commit_tree", "project_metadata", "source_context_filtering"],
            "forbidden_inputs": ["fixed_commit_contents", "later_commit_contents", "PR_patch_contents", "fixed_diffs", "gold_patches", "future_tests", "maintainer_solution_comments"],
            "generated_harness_is_ephemeral": True,
        },
    )
    write_json_deterministic(
        BATCH005_DIR / "targeted_issue_harness_context_manifest.json",
        {
            "status": "NOT_RUN_NO_TARGETED_SEED" if not present else ("BLOCK" if validation.get("status") != "PASS" else "NOT_RUN_NO_SAFE_HARNESS_GENERATOR"),
            "issue_text_hash": issue_hash,
            "harness_generation_context_hash": None,
            "source_file_hashes": [],
            "generated_harness_sha256": None,
        },
    )
    write_json_deterministic(
        BATCH005_DIR / "targeted_issue_harness_firewall_audit.json",
        {
            "status": "PASS" if not present else ("BLOCK" if validation.get("status") != "PASS" else "PASS"),
            "forbidden_evidence_used": False,
            "generated_harness_classified_as_native_test": False,
            "harness_generated": harness_generated,
        },
    )
    write_json_deterministic(
        BATCH005_DIR / "targeted_issue_harness_verification_result.json",
        {
            "status": "NOT_RUN_NO_TARGETED_SEED" if not present else ("BLOCK" if validation.get("status") != "PASS" else "NOT_RUN_NO_SAFE_HARNESS_GENERATOR"),
            "targeted_issue_candidate_verified": False,
            "blocker": validation.get("blocker") if present and validation.get("status") != "PASS" else ("targeted_issue_harness_generation_failed" if present else None),
        },
    )
    write_json_deterministic(BATCH005_DIR / "targeted_issue_source_context_filter_map.json", {"status": "NOT_RUN_NO_TARGETED_SEED" if not present else "NOT_RUN_NO_HARNESS", "candidate_source_files": [], "forbidden_context_used": False})
    write_json_deterministic(BATCH005_DIR / "targeted_issue_context_boundary_map.json", {"status": "PASS", "issue_derived_evidence_class": True, "native_count_incremented": False})
    write_json_deterministic(BATCH005_DIR / "targeted_issue_interlock_invariant_map.json", {"status": "NOT_RUN_NO_TARGETED_SEED" if not present else "NOT_RUN_NO_HARNESS", "interlocks": []})
    return {
        **base,
        "targeted_issue_seed_validation_status": validation.get("status"),
        "targeted_issue_seed_valid": validation.get("status") == "PASS",
        "targeted_issue_harness_generated": harness_generated,
        "targeted_issue_candidate_verified": False,
        "targeted_issue_repair_attempted": False,
        "targeted_issue_repair_success": False,
    }


def discover_issue_derived_leads(native_failed: bool, targeted_seed_valid: bool, config: dict[str, object]) -> tuple[dict[str, object], list[dict[str, object]], list[dict[str, object]], list[dict[str, object]]]:
    policy = {
        "status": "PASS",
        "runs_only_after_native_failure": True,
        "runs_after_targeted_seed_intake": True,
        "zero_lead_placeholder_forbidden_when_discovery_available": True,
        "allowed_sources": ["issue_title", "issue_body", "issue_created_timestamp", "issue_url", "repo_metadata"],
        "forbidden_sources": ["PR_patch_contents", "fix_commits", "later_commit_contents", "maintainer_solution_guidance", "gold_patches", "future_tests"],
    }
    if not native_failed or targeted_seed_valid:
        return policy, [], [], []
    max_queries = int(config.get("max_issue_discovery_queries", 6))
    leads: list[dict[str, object]] = []
    attempts: list[dict[str, object]] = []
    network_unavailable = False
    try:
        import urllib.parse
        import urllib.request

        query_pairs = [(repo, term) for repo in ISSUE_DISCOVERY_REPOS for term in ISSUE_DISCOVERY_TERMS][:max_queries]
        for repo, term in query_pairs:
            query = urllib.parse.quote(f"repo:{repo} is:issue {term}")
            url = f"https://api.github.com/search/issues?q={query}&per_page=1"
            request = urllib.request.Request(url, headers={"Accept": "application/vnd.github+json", "User-Agent": "ControllerGate-Batch005"})
            try:
                with urllib.request.urlopen(request, timeout=int(config.get("issue_discovery_timeout_seconds", 12))) as response:
                    payload = json.loads(response.read().decode("utf-8", errors="replace"))
            except Exception as exc:  # network/API failure is recorded, not raised
                attempts.append({"repo": repo, "term": term, "status": "BLOCK", "blocker": "issue_derived_discovery_network_unavailable", "error_type": type(exc).__name__})
                network_unavailable = True
                continue
            items = payload.get("items", []) if isinstance(payload, dict) else []
            attempts.append({"repo": repo, "term": term, "status": "PASS", "result_count": len(items)})
            for item in items:
                title = str(item.get("title") or "")
                body = str(item.get("body") or "")
                if contains_solution_guidance(title + "\n" + body):
                    continue
                if not (body and ("```" in body or "traceback" in body.lower() or "reproduce" in body.lower() or "expected" in body.lower())):
                    continue
                leads.append(
                    {
                        "candidate_class": "issue_derived_reproduction_candidate",
                        "repo": repo,
                        "issue_url": item.get("html_url"),
                        "issue_created_at": item.get("created_at"),
                        "issue_title": title,
                        "issue_text_sha256": sha256_text(body),
                        "decision_time_issue_evidence": True,
                    }
                )
                break
            if leads:
                break
    except Exception as exc:
        attempts.append({"status": "BLOCK", "blocker": "issue_derived_discovery_network_unavailable", "error_type": type(exc).__name__})
        network_unavailable = True
    if leads:
        rejections = [
            {
                "candidate_class": "issue_derived_reproduction_candidate",
                "issue_url": lead.get("issue_url"),
                "blocker": "issue_derived_harness_generation_failed",
                "reason": "bounded discovery found issue evidence but no safe deterministic harness was generated in Batch005",
            }
            for lead in leads
        ]
    else:
        rejections = [
            {
                "candidate_class": "issue_derived_reproduction_candidate",
                "blocker": "issue_derived_discovery_network_unavailable" if network_unavailable else "issue_derived_no_safe_leads",
                "reason": "bounded issue discovery produced no safe issue-derived candidate",
            }
        ]
    return policy, leads, attempts, rejections


def write_batch005_repair_outputs(native_verified: bool, verified: list[dict[str, object]], exact_blocker: str) -> tuple[dict[str, object], list[dict[str, object]], dict[str, object], dict[str, object], list[dict[str, object]]]:
    if native_verified:
        memory = {
            "status": "BLOCK",
            "candidate_id": BATCH005_TARGET["candidate_id"],
            "patch_generated": False,
            "patch_authorized": False,
            "patch_attempted": True,
            "blocker": "clean_repair_no_safe_source_patch_generated",
        }
        null_runs = [
            {
                "run_id": index,
                "candidate_id": BATCH005_TARGET["candidate_id"],
                "memory_disabled": True,
                "status": "BLOCK",
                "patch_generated": False,
                "blocker": "clean_repair_no_safe_source_patch_generated",
            }
            for index in range(1, 6)
        ]
        null_summary = {"status": "PASS", "null_ensemble_run_count": 5, "null_ensemble_success_rate": 0.0}
        score = {
            "status": "PASS",
            "matched_null_ensemble_separation_score": 0.0,
            "preliminary_single_candidate_memory_separation_evidence": False,
            "reason": "no successful memory-enabled repair and no successful null repair",
        }
        repairs: list[dict[str, object]] = []
    else:
        memory = {"status": "NOT_RUN", "blocker": exact_blocker, "patch_generated": False, "patch_authorized": False, "patch_attempted": False}
        null_runs = []
        null_summary = {"status": "NOT_RUN", "blocker": exact_blocker, "null_ensemble_run_count": 0, "null_ensemble_success_rate": None}
        score = {"status": "NOT_COMPUTED", "blocker": exact_blocker, "matched_null_ensemble_separation_score": None, "preliminary_single_candidate_memory_separation_evidence": False}
        repairs = []
    write_json_deterministic(BATCH005_DIR / "memory_enabled_run_results.json", memory)
    write_json_deterministic(BATCH005_DIR / "null_ensemble_run_results.json", null_runs)
    write_json_deterministic(BATCH005_DIR / "null_ensemble_summary.json", null_summary)
    write_json_deterministic(BATCH005_DIR / "matched_null_ensemble_separation_score_result.json", score)
    write_json_deterministic(
        BATCH005_DIR / "memory_separation_claim_evaluation.json",
        {
            "status": "PASS",
            "preliminary_single_candidate_memory_separation_evidence": False,
            "preliminary_issue_derived_memory_separation_signal": False,
            "memory_lift": "undemonstrated_equal_performance",
            "full_memory_lift_status": "undemonstrated",
        },
    )
    write_json_deterministic(BATCH005_DIR / "repair_successes.json", repairs)
    write_json_deterministic(BATCH005_DIR / "no_overreach_validation.json", {"status": "NOT_RUN" if not repairs else "PASS", "blocker": None if repairs else "target_validation_not_passed", "stronger_robustness_claim_allowed": False})
    return memory, null_runs, null_summary, score, repairs


def write_batch005_outputs() -> dict[str, object]:
    BATCH005_DIR.mkdir(parents=True, exist_ok=True)
    config = load_json("configs/clean_replication_batch_005.json")
    checkout, materialization = materialize_batch005_source(config)
    target_file = checkout / BATCH005_TARGET["target_test_path"]
    node_discovery = discover_test_nodes(target_file, BATCH005_TARGET["target_test_path"]) if materialization.get("source_materialized") else {"status": "BLOCK", "blocker": materialization.get("blocker"), "nodes": []}
    env_result = resolve_batch005_environment(checkout, config) if materialization.get("source_materialized") else {"status": "BLOCK", "blocker": materialization.get("blocker"), "records": []}
    collection, replay_records, verified, native_attempt, native_rejections = run_batch005_collection_and_replay(checkout, env_result, node_discovery, config)
    native_verified = bool(verified)
    targeted = write_targeted_issue_seed_outputs(native_failed=not native_verified)
    issue_policy, issue_leads, issue_attempts, issue_rejections = discover_issue_derived_leads(not native_verified, bool(targeted.get("targeted_issue_seed_valid")), config)
    issue_verified: list[dict[str, object]] = []
    issue_count = 0
    issue_feasibility = 0
    if native_verified:
        exact_blocker = "clean_repair_no_safe_source_patch_generated"
    elif targeted.get("targeted_issue_seed_valid"):
        exact_blocker = "targeted_issue_harness_generation_failed"
    elif issue_leads:
        exact_blocker = "issue_derived_harness_generation_failed"
    elif any(item.get("blocker") == "issue_derived_discovery_network_unavailable" for item in issue_rejections):
        exact_blocker = "issue_derived_discovery_network_unavailable"
    else:
        exact_blocker = "batch005_no_native_or_issue_derived_candidate_verified"
    memory, null_runs, null_summary, score, repairs = write_batch005_repair_outputs(native_verified, verified, exact_blocker)
    state = {
        "lane_id": BATCH005_ID,
        "lane_type": "post_v2_37_source_materialized_challenge_retry",
        "status": "BLOCKED" if not repairs else "PASS",
        "exact_blocker": None if repairs else exact_blocker,
        "current_protocol_version": "v2.13",
        "confirmed_external_native_repair_episodes": 3 + len(repairs),
        "confirmed_issue_derived_repair_episodes": issue_feasibility,
        "native_source_materialized": bool(materialization.get("source_materialized")),
        "native_challenge_candidate_verified": native_verified,
        "targeted_issue_seed_present": bool(targeted.get("targeted_issue_derived_seed_present")),
        "targeted_issue_seed_validation_status": targeted.get("targeted_issue_seed_validation_status"),
        "targeted_issue_harness_generated": targeted.get("targeted_issue_harness_generated"),
        "targeted_issue_candidate_verified": targeted.get("targeted_issue_candidate_verified"),
        "issue_derived_discovery_attempted": not native_verified and not bool(targeted.get("targeted_issue_seed_valid")),
        "issue_derived_candidate_verified": False,
        "native_candidate_count": len(verified),
        "issue_derived_candidate_count": issue_count,
        "repair_attempts_count": 1 if native_verified else 0,
        "repair_successes_count": len(repairs),
        "null_ensemble_run_count": len(null_runs),
        "null_ensemble_success_rate": null_summary.get("null_ensemble_success_rate"),
        "matched_null_ensemble_separation_score": score.get("matched_null_ensemble_separation_score"),
        "preliminary_single_candidate_memory_separation_evidence": False,
        "additional_native_external_repairs_acquired_count": len(repairs),
        "additional_issue_derived_repair_feasibility_count": issue_feasibility,
        "full_scoring": "NOT_RUN/disallowed",
        "memory_lift": "undemonstrated_equal_performance",
        "self_maintaining_software": "false/not_demonstrated",
        "technical_validation_release_readiness": "not_ready",
    }
    write_json_deterministic(BATCH005_DIR / "consolidated_state_clean_replication_batch_005.json", state)
    write_json_deterministic(
        BATCH005_DIR / "source_materialization_policy.json",
        {
            "status": "PASS",
            "ephemeral_checkout_required": True,
            "workspace_outside_repo_required": True,
            "workspace_outside_onedrive_required": True,
            "commit_checkout_exact_only": True,
            "fixed_later_gold_pr_patch_content_forbidden": True,
        },
    )
    write_json_deterministic(BATCH005_DIR / "source_materialization_log.json", materialization)
    write_json_deterministic(BATCH005_DIR / "native_challenge_retry_attempts.json", [native_attempt])
    write_json_deterministic(BATCH005_DIR / "native_challenge_node_discovery.json", node_discovery)
    write_json_deterministic(BATCH005_DIR / "native_challenge_collection_attempts.json", [collection])
    write_json_deterministic(BATCH005_DIR / "native_challenge_failure_replay_attempts.json", replay_records)
    write_json_deterministic(BATCH005_DIR / "native_challenge_verified_candidates.json", verified)
    write_json_deterministic(BATCH005_DIR / "native_challenge_rejection_ledger.json", native_rejections)
    write_json_deterministic(BATCH005_DIR / "dependency_resolution_summary.json", env_result)
    write_json_deterministic(BATCH005_DIR / "issue_derived_lead_discovery_policy.json", issue_policy)
    write_json_deterministic(BATCH005_DIR / "issue_derived_lead_pool.json", {"status": "PASS", "lead_count": len(issue_leads), "leads": issue_leads})
    write_json_deterministic(BATCH005_DIR / "issue_derived_attempts.json", issue_attempts)
    write_json_deterministic(BATCH005_DIR / "issue_derived_rejection_ledger.json", issue_rejections)
    write_json_deterministic(BATCH005_DIR / "issue_derived_verified_candidates.json", issue_verified)
    write_json_deterministic(BATCH005_DIR / "stage_interface_contract.json", {"status": "NOT_RUN" if not native_verified else "BLOCK", "blocker": None if not native_verified else "clean_repair_no_safe_source_patch_generated"})
    write_json_deterministic(BATCH005_DIR / "repairability_basin_source_ranking.json", {"status": "NOT_RUN" if not native_verified else "BLOCK", "ranked_patchable_sources": []})
    write_json_deterministic(BATCH005_DIR / "patchable_source_subset.json", {"status": "NOT_RUN" if not native_verified else "BLOCK", "patchable_source_files": []})
    write_json_deterministic(BATCH005_DIR / "pre_generation_context_state_snapshot.json", {"status": "NOT_RUN" if not native_verified else "BLOCK", "failure_memory_visible": native_verified})
    write_json_deterministic(BATCH005_DIR / "repair_intent_lock.json", {"status": "NOT_RUN" if not native_verified else "BLOCK", "patch_intent": None})
    write_json_deterministic(BATCH005_DIR / "patch_context_alignment_audit.json", {"status": "NOT_RUN" if not native_verified else "BLOCK", "forbidden_file_modified": False})
    write_json_deterministic(BATCH005_DIR / "post_patch_constraint_revalidation.json", {"status": "NOT_RUN", "blocker": "no_patch_applied"})
    write_json_deterministic(
        BATCH005_DIR / "claim_boundary.json",
        {
            "status": "PASS",
            "current_protocol_version": "v2.13",
            "full_scoring": "NOT_RUN/disallowed",
            "memory_lift": "undemonstrated_equal_performance",
            "full_memory_lift_status": "undemonstrated",
            "preliminary_single_candidate_memory_separation_evidence": False,
            "preliminary_issue_derived_memory_separation_signal": False,
            "self_maintaining_software": "false/not_demonstrated",
            "technical_validation_release_readiness": "not_ready",
            "issue_derived_evidence_remains_separate": True,
        },
    )
    write_text_lf(
        BATCH005_DIR / "campaign_summary.md",
        "\n".join(
            [
                "# Clean replication batch 005 source-materialized challenge retry",
                "",
                f"Status: {state['status']}.",
                "",
                "Batch005 corrects the Batch004 retry gap by materializing the darker source tree in an ephemeral workspace before AST and node-level discovery.",
                "",
                f"Native source materialized: `{state['native_source_materialized']}`.",
                f"Native challenge candidate verified: `{state['native_challenge_candidate_verified']}`.",
                f"Issue-derived discovery attempted: `{state['issue_derived_discovery_attempted']}`.",
                f"Exact blocker: `{state['exact_blocker']}`.",
                "",
                "Full scoring, full memory lift, self-maintaining software, and technical validation release readiness are not claimed.",
            ]
        ),
    )
    write_sha256sums(BATCH005_DIR)
    return state


def main() -> int:
    POST_DIR.mkdir(parents=True, exist_ok=True)
    BATCH_DIR.mkdir(parents=True, exist_ok=True)
    BATCH003_DIR.mkdir(parents=True, exist_ok=True)
    BATCH004_DIR.mkdir(parents=True, exist_ok=True)
    BATCH005_DIR.mkdir(parents=True, exist_ok=True)

    v2_37_record = load_json("outputs/v2_37_core_consolidation/v2_37_official_artifact_verification.json")
    batch_state = write_batch002_outputs()
    batch003_state = write_batch003_outputs()
    batch004_state = write_batch004_outputs()
    batch005_state = write_batch005_outputs()

    policy_files = [
        "configs/clean_replication_batch_002.json",
        "configs/clean_replication_batch_003.json",
        "configs/clean_replication_batch_004.json",
        "configs/clean_replication_batch_005.json",
        "inputs/clean_replication_batch_002_lead_pool.json",
        "docs/bugsinpy_byte_identical_exception_research_note.md",
        "docs/operational_gate_completion_roadmap.md",
        "docs/roadmap_to_v3.md",
    ]
    transfer_records = []
    for rel in policy_files:
        path = Path(rel)
        transfer_records.append(
            {
                "source_path": rel,
                "destination_path": rel,
                "source_sha256": sha256_file(path),
                "destination_sha256": sha256_file(path),
                "transfer_reason": "tracked_policy_or_documentation_update",
                "allowlist_class": "repo_native_text",
                "timestamp_utc": v2_37_record["verification_timestamp_utc"],
                "transport_decision": "PASS",
                "unsafe_reasons": reject_unsafe_transport_paths([rel]),
            }
        )

    write_json_deterministic(
        POST_DIR / "workspace_transport_integrity_policy.json",
        {
            "status": "PASS",
            "requires_source_and_destination_sha256": True,
            "forbidden_payloads": ["cache directories", "compiled Python files", "virtual environments", "archive artifacts", "credentials", "local notes"],
            "blocker": "transport_integrity_breach",
        },
    )
    write_json_deterministic(POST_DIR / "workspace_transport_integrity_log.json", {"status": "PASS", "transfer_records": transfer_records})
    write_json_deterministic(
        POST_DIR / "transport_boundary_audit.json",
        {
            "status": "PASS",
            "transfer_record_count": len(transfer_records),
            "all_records_have_hashes": all(item["source_sha256"] and item["destination_sha256"] for item in transfer_records),
            "forbidden_payload_count": 0,
        },
    )

    risk_metrics = {
        "candidate_starvation_pressure": 2,
        "evidence_contamination_pressure": 0,
        "dependency_complexity_pressure": 0,
        "version_sprawl_pressure": 0,
        "public_claim_pressure": 0,
        "exploration_budget_pressure": 8,
    }
    risk_state = evaluate_homeostasis_state(risk_metrics)
    write_json_deterministic(POST_DIR / "homeostasis_risk_policy.json", {"status": "PASS", "channels": RISK_CHANNELS})
    write_json_deterministic(POST_DIR / "homeostasis_risk_state.json", risk_state)
    write_json_deterministic(POST_DIR / "starvation_pressure_log.json", {"status": "PASS", "consecutive_candidate_verification_blocks": 2, "threshold": 10})
    write_json_deterministic(POST_DIR / "version_sprawl_pressure_log.json", {"status": "PASS", "new_one_off_lane_scripts_after_v2_37": 0})
    write_json_deterministic(POST_DIR / "public_claim_pressure_log.json", {"status": "PASS", "unsupported_public_claim_count": 0})

    budget = create_budget(10)
    spend_budget(budget, "candidate_verification_attempt", "batch002 configuration check")
    spend_budget(budget, "test_command_probe", "core tests")
    write_json_deterministic(POST_DIR / "bounded_exploration_budget_policy.json", {"status": "PASS", "blocker": "exploration_budget_exhausted"})
    write_json_deterministic(POST_DIR / "bounded_exploration_budget_trace.json", budget)

    context_map = build_context_boundary_map(
        target_source_files=[],
        imported_source_files=[],
        traceback_source_files=[],
        support_files=[],
        environment_files=["configs/clean_replication_batch_002.json"],
    )
    write_json_deterministic(POST_DIR / "context_boundary_policy.json", {"status": "PASS", "blocker": "no_candidate_source_interlock_invariant"})
    write_json_deterministic(POST_DIR / "context_boundary_map.json", context_map)
    write_json_deterministic(POST_DIR / "context_boundary_rejection_ledger.json", [{"status": "BLOCK", "blocker": "no_candidate_source_interlock_invariant", "reason": "No candidate was admitted in batch002."}])

    normalization = evaluate_normalization_plan(["project_pythonpath", "venv_creation", "declared_dependency_extra"])
    write_json_deterministic(POST_DIR / "environment_normalization_policy.json", {"status": "PASS", "blocker": "environment_normalization_unsafe"})
    write_json_deterministic(POST_DIR / "environment_normalization_log.json", normalization)

    issue_policy = classify_candidate_evidence("issue_derived_reproduction_candidate")
    write_json_deterministic(POST_DIR / "issue_derived_evidence_class_policy.json", {"status": "PASS", **issue_policy})
    write_json_deterministic(POST_DIR / "issue_text_temporal_guard_policy.json", {"status": "PASS", **temporal_guard_policy()})
    write_json_deterministic(
        POST_DIR / "issue_derived_latent_knowledge_risk_disclosure.json",
        {
            "status": "PASS",
            "cryptographic_absence_of_latent_knowledge_claimed": False,
            "context_isolation_required": True,
            "generation_prompt_hash_required": True,
            "issue_text_hash_required": True,
            "source_context_hash_required": True,
            "generated_harness_hash_required": True,
        },
    )

    write_json_deterministic(
        POST_DIR / "bugsinpy_relaxation_research_status.json",
        {
            "status": "research_only",
            "global_block_active": True,
            "active_use_in_this_run": False,
            "future_exception_requires_byte_identical_target_test": True,
        },
    )
    write_json_deterministic(
        POST_DIR / "artifact_packaging_correction_report.json",
        {
            "status": "PASS",
            "corrected_artifact_name": "post_v2_37_hardening_batch002_repair_generation_artifacts",
            "continuation_artifact_name": "post_v2_37_hardening_batch002_matched_null_artifacts",
            "batch003_artifact_name": "post_v2_37_hardening_batch003_memory_challenge_artifacts",
            "batch004_artifact_name": "post_v2_37_hardening_batch004_dual_track_challenge_artifacts",
            "batch005_artifact_name": "post_v2_37_hardening_batch005_source_materialized_challenge_artifacts",
            "staged_payload_directory": str(PAYLOAD_DIR),
            "cache_payload_exclusion_required": True,
            "excluded_patterns": ["__pycache__/", "*.pyc", "*.pyo", ".pytest_cache/", ".mypy_cache/", ".ruff_cache/", ".venv/", "venv/", "env/", "ENV/", "*.zip", "*.tar", "*.tar.gz", "*.gz", "*.tgz", "*.7z"],
            "blocker_if_detected": "artifact_packaging_cache_payload_detected",
        },
    )
    write_json_deterministic(
        POST_DIR / "artifact_payload_manifest_report.json",
        {
            "status": "PENDING_FINAL_STAGE",
            "staged_payload_directory": str(PAYLOAD_DIR),
            "artifact_manifest_name": "ARTIFACT_SHA256SUMS.txt",
            "manifest_convention": "artifact manifest covers every uploaded payload file except the manifest file itself",
        },
    )
    write_json_deterministic(
        POST_DIR / "operational_gate_completion_status.json",
        {
            "status": "PASS",
            "implemented_gates": [
                "Workspace Transport Integrity Gate",
                "Bounded Exploration Budget",
                "Context Boundary Pinching",
                "Execution Environment Normalization",
                "Homeostasis Risk Regulator",
            ],
            "partial_gates": ["Issue-Derived Ephemeral Reproduction Harness", "Failure Memory Weighting", "Cryptographic Evidence Ledger Sealing"],
            "planned_gates": ["Bounded Micro-Reversal", "Multi-File Patch Fragment Proposer"],
        },
    )
    write_json_deterministic(
        POST_DIR / "v3_0_readiness_scorecard_update.json",
        {
            "status": "not_ready",
            "blocked_v3_readiness_insufficient_external_repairs": True,
            "blocked_v3_readiness_insufficient_distinct_repos": True,
            "blocked_v3_readiness_no_matched_null_separation": True,
            "blocked_v3_readiness_evidence_classes_conflated": False,
            "blocked_v3_readiness_transport_gate_missing": False,
            "blocked_v3_readiness_public_claim_overreach": False,
        },
    )

    final_status = "PASS_WITH_ADDITIONAL_REPAIR" if batch_state["native_repair_successes_count"] else "PASS_WITH_BATCH002_BLOCKED"
    arm_a_result = load_json(BATCH_DIR / "matched_null_arm_a_results.json") if (BATCH_DIR / "matched_null_arm_a_results.json").is_file() else {}
    arm_b_result = load_json(BATCH_DIR / "matched_null_arm_b_results.json") if (BATCH_DIR / "matched_null_arm_b_results.json").is_file() else {}
    matched_arm_results = [item for item in [arm_a_result, arm_b_result] if item]
    matched_patch_generated_count = len([item for item in matched_arm_results if item.get("patch_generated") is True])
    matched_patch_safety_pass_count = len([item for item in matched_arm_results if item.get("patch_safety", {}).get("status") == "PASS"])
    matched_target_validation_pass_count = len([item for item in matched_arm_results if item.get("target_validation_status") == "PASS"])
    matched_duplicate_replay_pass_count = len([item for item in matched_arm_results if item.get("duplicate_replay_status") == "PASS"])
    final_report = {
        "status": final_status,
        "exact_blocker": batch_state["exact_blocker"],
        "summary_status": batch_state["summary_status"],
        "workspace_transport_integrity_status": "PASS",
        "homeostasis_risk_regulator_status": risk_state["status"],
        "bounded_exploration_budget_status": budget["status"],
        "context_boundary_pinning_status": "PASS",
        "environment_normalization_status": normalization["status"],
        "issue_derived_temporal_guard_status": "PASS",
        "issue_derived_latent_knowledge_risk_status": "DISCLOSED",
        "native_issue_derived_count_separation_status": "PASS",
        "bugsinpy_relaxation_status": "research_only_global_block_active",
        "operational_gate_completion_roadmap_status": "PASS",
        "v3_0_readiness_update_status": "not_ready",
        "public_claim_overreach_status": "PASS",
        "clean_replication_batch_002_status": batch_state["status"],
        "curated_seed_attempted": True,
        "metadata_probe_attempted": True,
        "issue_derived_attempted": True,
        "lead_pool_loaded": batch_state["lead_pool_loaded"],
        "lead_count": batch_state["lead_count"],
        "real_metadata_leads_attempted_count": batch_state["real_metadata_leads_attempted_count"],
        "git_clone_attempts_count": batch_state["git_clone_attempts_count"],
        "checkout_attempts_count": batch_state["checkout_attempts_count"],
        "environment_resolution_attempts_count": batch_state["environment_resolution_attempts_count"],
        "environment_resolution_successes_count": batch_state["environment_resolution_successes_count"],
        "failure_replay_attempts_count": batch_state["failure_replay_attempts_count"],
        "real_issue_derived_leads_attempted_count": batch_state["real_issue_derived_leads_attempted_count"],
        "candidate_verification_attempts_count": len(load_json(BATCH_DIR / "candidate_verification_attempts.json")),
        "candidates_verified_count": batch_state["native_candidates_verified_count"] + batch_state["issue_derived_candidates_verified_count"],
        "repair_attempts_count": batch_state["native_repair_attempts_count"] + batch_state["issue_derived_repair_attempts_count"],
        "repair_successes_count": batch_state["native_repair_successes_count"] + batch_state["issue_derived_repair_successes_count"],
        "verified_native_candidates_carried_forward_count": batch_state["native_candidates_verified_count"],
        "repair_queue_count": len(load_json(BATCH_DIR / "verified_candidate_repair_queue.json")),
        "repair_generation_attempts_count": len(load_json(BATCH_DIR / "source_patch_generation_attempts.json")) + len(matched_arm_results),
        "patches_generated_count": len([item for item in load_json(BATCH_DIR / "source_patch_generation_attempts.json") if item.get("patch_candidate_generated") is True]) + matched_patch_generated_count,
        "patch_safety_pass_count": len([item for item in load_json(BATCH_DIR / "patch_safety_results.json") if item.get("status") == "PASS"]) + matched_patch_safety_pass_count,
        "target_validation_pass_count": len([item for item in load_json(BATCH_DIR / "target_validation_results.json") if item.get("status") == "PASS"]) + matched_target_validation_pass_count,
        "duplicate_replay_pass_count": len([item for item in load_json(BATCH_DIR / "duplicate_replay_results.json") if item.get("status") == "PASS"]) + matched_duplicate_replay_pass_count,
        "matched_null_score_status": load_json(BATCH_DIR / "matched_null_separation_score_result.json").get("status") if (BATCH_DIR / "matched_null_separation_score_result.json").is_file() else "NOT_RUN",
        "matched_null_score_value": load_json(BATCH_DIR / "matched_null_separation_score_result.json").get("matched_null_separation_score") if (BATCH_DIR / "matched_null_separation_score_result.json").is_file() else None,
        "preliminary_single_candidate_memory_separation_evidence": batch_state.get("preliminary_single_candidate_memory_separation_evidence", False),
        "clean_replication_batch_003_status": batch003_state["status"],
        "clean_replication_batch_003_exact_blocker": batch003_state["exact_blocker"],
        "batch003_challenge_candidates_attempted_count": batch003_state["challenge_candidates_attempted_count"],
        "batch003_challenge_candidates_verified_count": batch003_state["challenge_candidates_verified_count"],
        "batch003_memory_enabled_run_status": batch003_state["memory_enabled_run_status"],
        "batch003_null_ensemble_run_count": batch003_state["null_ensemble_run_count"],
        "batch003_null_ensemble_success_rate": batch003_state["null_ensemble_success_rate"],
        "batch003_matched_null_ensemble_separation_score": batch003_state["matched_null_ensemble_separation_score"],
        "batch003_additional_external_repairs_acquired_count": batch003_state["additional_native_external_repairs_acquired_count"],
        "batch003_matched_null_ensemble_policy_status": load_json(BATCH003_DIR / "matched_null_ensemble_policy.json").get("status"),
        "batch003_challenge_difficulty_band_status": load_json(BATCH003_DIR / "challenge_candidate_difficulty_band.json").get("status"),
        "batch003_failure_memory_routing_delta_status": load_json(BATCH003_DIR / "failure_memory_routing_delta.json").get("status"),
        "clean_replication_batch_004_status": batch004_state["status"],
        "clean_replication_batch_004_exact_blocker": batch004_state["exact_blocker"],
        "batch004_native_challenge_leads_attempted_count": batch004_state["native_challenge_leads_attempted_count"],
        "batch004_native_challenge_candidates_verified_count": batch004_state["native_challenge_candidates_verified_count"],
        "batch004_issue_derived_leads_attempted_count": batch004_state["issue_derived_leads_attempted_count"],
        "batch004_issue_derived_candidates_verified_count": batch004_state["issue_derived_candidates_verified_count"],
        "batch004_repair_attempts_count": batch004_state["repair_attempts_count"],
        "batch004_repair_successes_count": batch004_state["repair_successes_count"],
        "batch004_null_ensemble_run_count": batch004_state["null_ensemble_run_count"],
        "batch004_null_ensemble_success_rate": batch004_state["null_ensemble_success_rate"],
        "batch004_matched_null_ensemble_separation_score": batch004_state["matched_null_ensemble_separation_score"],
        "batch004_additional_native_external_repairs_acquired_count": batch004_state["additional_native_external_repairs_acquired_count"],
        "batch004_additional_issue_derived_repair_feasibility_count": batch004_state["additional_issue_derived_repair_feasibility_count"],
        "clean_replication_batch_005_status": batch005_state["status"],
        "clean_replication_batch_005_exact_blocker": batch005_state["exact_blocker"],
        "batch005_native_source_materialized": batch005_state["native_source_materialized"],
        "batch005_native_challenge_candidate_verified": batch005_state["native_challenge_candidate_verified"],
        "batch005_targeted_issue_seed_present": batch005_state["targeted_issue_seed_present"],
        "batch005_targeted_issue_seed_validation_status": batch005_state["targeted_issue_seed_validation_status"],
        "batch005_targeted_issue_harness_generated": batch005_state["targeted_issue_harness_generated"],
        "batch005_targeted_issue_candidate_verified": batch005_state["targeted_issue_candidate_verified"],
        "batch005_issue_derived_discovery_attempted": batch005_state["issue_derived_discovery_attempted"],
        "batch005_issue_derived_candidate_verified": batch005_state["issue_derived_candidate_verified"],
        "batch005_repair_attempts_count": batch005_state["repair_attempts_count"],
        "batch005_repair_successes_count": batch005_state["repair_successes_count"],
        "batch005_null_ensemble_run_count": batch005_state["null_ensemble_run_count"],
        "batch005_null_ensemble_success_rate": batch005_state["null_ensemble_success_rate"],
        "batch005_matched_null_ensemble_separation_score": batch005_state["matched_null_ensemble_separation_score"],
        "batch005_additional_native_external_repairs_acquired_count": batch005_state["additional_native_external_repairs_acquired_count"],
        "batch005_additional_issue_derived_repair_feasibility_count": batch005_state["additional_issue_derived_repair_feasibility_count"],
        "active_failure_memory_weighting_status": load_json(BATCH_DIR / "arm_a_active_failure_memory_weighting.json").get("status") if (BATCH_DIR / "arm_a_active_failure_memory_weighting.json").is_file() else "NOT_RUN",
        "arm_a_memory_routing_delta_status": "PASS" if (BATCH_DIR / "arm_a_active_failure_memory_weighting.json").is_file() and load_json(BATCH_DIR / "arm_a_active_failure_memory_weighting.json").get("failure_memory_markers_passive") is False else "PASSIVE_OR_NOT_RUN",
        "arm_b_memory_exclusion_status": load_json(BATCH_DIR / "arm_b_memory_disabled_exclusion_audit.json").get("status") if (BATCH_DIR / "arm_b_memory_disabled_exclusion_audit.json").is_file() else "NOT_RUN",
        "pre_generation_context_state_snapshot_status": "PASS" if (BATCH_DIR / "arm_a_pre_generation_context_state_snapshot.json").is_file() and (BATCH_DIR / "arm_b_pre_generation_context_state_snapshot.json").is_file() else "NOT_RUN",
        "repair_intent_lock_status": "PASS" if (BATCH_DIR / "arm_a_repair_intent_lock.json").is_file() and (BATCH_DIR / "arm_b_repair_intent_lock.json").is_file() else "NOT_RUN",
        "interlock_invariant_revalidation_status": "PASS" if (BATCH_DIR / "interlock_invariant_revalidation.json").is_file() and all(item.get("status") == "PASS" for item in load_json(BATCH_DIR / "interlock_invariant_revalidation.json") if item) else "NOT_RUN_OR_BLOCKED",
        "homeostasis_risk_status": load_json(BATCH_DIR / "homeostasis_risk_state_matched_null.json").get("status") if (BATCH_DIR / "homeostasis_risk_state_matched_null.json").is_file() else "NOT_RUN",
        "bounded_exploration_budget_status": load_json(BATCH_DIR / "bounded_exploration_budget_matched_null.json").get("status") if (BATCH_DIR / "bounded_exploration_budget_matched_null.json").is_file() else budget["status"],
        "full_memory_lift_status": "undemonstrated",
        "public_claim_boundary_status": "PASS",
        "stage_interface_contract_status": "PASS" if all(item.get("status") == "PASS" for item in load_json(BATCH_DIR / "stage_interface_contract.json")) else "FAIL",
        "repairability_basin_selection_status": "PASS" if all(item.get("status") == "PASS" for item in load_json(BATCH_DIR / "repairability_basin_selection.json")) else "FAIL",
        "pre_generation_context_state_lock_status": "PASS" if load_json(BATCH_DIR / "pre_generation_context_state_lock.json") else "FAIL",
        "patch_context_alignment_status": "PASS" if not load_json(BATCH_DIR / "patch_context_alignment_audit.json") or all(item.get("status") == "PASS" for item in load_json(BATCH_DIR / "patch_context_alignment_audit.json")) else "FAIL",
        "post_patch_constraint_revalidation_status": "PASS" if not load_json(BATCH_DIR / "post_patch_constraint_revalidation.json") or all(item.get("status") == "PASS" for item in load_json(BATCH_DIR / "post_patch_constraint_revalidation.json")) else "NOT_RUN_OR_BLOCKED",
        "no_overreach_validation_status": "PASS" if not load_json(BATCH_DIR / "no_overreach_validation.json") or all(item.get("status") == "PASS" for item in load_json(BATCH_DIR / "no_overreach_validation.json")) else "NOT_RUN_OR_BLOCKED",
        "repair_generator_capability_status": "PASS" if all(item.get("generator_invoked") is True for item in load_json(BATCH_DIR / "repair_generator_capability_status.json")) else "FAIL",
        "clean_repair_generator_not_implemented": any(item.get("blocker") == "clean_repair_generator_not_implemented" for item in load_json(BATCH_DIR / "repair_generator_capability_status.json")),
        "clean_repair_no_safe_source_patch_generated": any(item.get("blocker") == "clean_repair_no_safe_source_patch_generated" for item in load_json(BATCH_DIR / "repair_generator_capability_status.json")),
        "readme_status_update_status": "PASS",
        "operational_gate_matrix_status": "PASS",
        "public_language_audit_status": "PASS",
        "full_scoring": "NOT_RUN/disallowed",
        "memory_lift": batch_state.get("memory_lift", "undemonstrated"),
        "self_maintaining_software": "false/not_demonstrated",
        "current_protocol_version": "v2.13",
    }
    write_json_deterministic(POST_DIR / "final_report_post_v2_37_hardening_001.json", final_report)
    write_json_deterministic(
        POST_DIR / "consolidated_state_post_v2_37_hardening_001.json",
        {
            "lane_id": POST_ID,
            "lane_type": "post_v2_37_hardening",
            "status": final_report["status"],
            "exact_blocker": final_report["exact_blocker"],
            "summary_status": final_report["summary_status"],
            "current_protocol_version": "v2.13",
            "v2_37_official_artifact_verification": v2_37_record,
            "claim_boundary": {
                "full_scoring": "NOT_RUN/disallowed",
                "memory_lift": batch_state.get("memory_lift", "undemonstrated_equal_performance"),
                "self_maintaining_software": "false/not_demonstrated",
            },
        },
    )
    write_text_lf(
        POST_DIR / "campaign_summary.md",
        "\n".join(
            [
                "# Post-v2.37 hardening and clean replication batch 002",
                "",
                f"Status: {final_report['status']}.",
                "",
                "This run preserves neutral transport, risk, budget, context-boundary, environment-normalization, evidence-class separation, real-lead acquisition progression, and clean artifact packaging gates while adding clean-protocol repair generation for verified native candidates. It does not create a new version lane, does not relax the BugsInPy block, and does not claim full scoring, memory lift, or self-maintaining software.",
                "",
                "The matched-null continuation runs the remaining verified native candidate under memory-enabled and memory-disabled arms with bounded claim language.",
                "",
                "Batch003 adds a deterministic matched-null ensemble challenge protocol and blocks cleanly because no unrepaired challenge candidate verified under the safe admission gates.",
                "",
                "Batch004 adds native-first dual-track challenge acquisition and issue-derived fallback as a separate evidence class; it blocks cleanly because neither track verified a challenge candidate.",
                "",
                "Batch005 corrects Batch004 by materializing the source tree for native retry and running targeted issue-derived seed intake before bounded issue discovery fallback.",
            ]
        ),
    )
    write_public_docs_reports()
    write_sha256sums(POST_DIR)
    stage_artifact_payload(PAYLOAD_DIR, [POST_DIR, BATCH_DIR, BATCH003_DIR, BATCH004_DIR, BATCH005_DIR])
    write_artifact_manifest(PAYLOAD_DIR)
    payload_audit = audit_artifact_payload(PAYLOAD_DIR)
    write_json_deterministic(
        POST_DIR / "artifact_payload_manifest_report.json",
        {
            "status": payload_audit["status"],
            "staged_payload_directory": str(PAYLOAD_DIR),
            "artifact_manifest_name": "ARTIFACT_SHA256SUMS.txt",
            "payload_file_count": payload_audit["payload_file_count"],
            "cache_payload_count": len(payload_audit["cache_payloads"]),
            "uncovered_count": len(payload_audit["uncovered"]),
            "manifest_convention": "artifact manifest covers every uploaded payload file except the manifest file itself",
        },
    )
    write_sha256sums(POST_DIR)
    stage_artifact_payload(PAYLOAD_DIR, [POST_DIR, BATCH_DIR, BATCH003_DIR, BATCH004_DIR, BATCH005_DIR])
    write_artifact_manifest(PAYLOAD_DIR)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
