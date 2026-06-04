#!/usr/bin/env python3
"""Audit the v1.8 controlled repo replay-first capture plan."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
PLAN_JSON_PATH = REPO_ROOT / "outputs" / "v1_8_controlled_repo_replay_capture_plan.json"
PLAN_MD_PATH = REPO_ROOT / "outputs" / "v1_8_controlled_repo_replay_capture_plan.md"
BETA_REPLAY_PLAN_PATH = REPO_ROOT / "controllergate_v1_7_beta" / "outputs" / "v1_7_beta_replay_eligibility_plan.json"
BETA_SHAREABLE_SUMMARY_PATH = (
    REPO_ROOT / "controllergate_v1_7_beta" / "reports" / "critic_review_package" / "shareable_summary.md"
)

REQUIRED_ALLOWED_FAILURES = {
    "failing_unit_test",
    "lint_failure",
    "formatting_failure",
    "type_check_failure",
    "build_failure",
    "dependency_lock_failure",
    "documentation_link_check_failure",
    "schema_validation_failure",
    "small_deterministic_bug_with_test_oracle",
}

REQUIRED_DISALLOWED_FAILURES = {
    "security_exploit_tasks",
    "secrets_or_credential_extraction",
    "destructive_data_deletion_without_snapshot",
    "tasks_requiring_private_third_party_services",
    "network_only_proof_without_local_replay",
    "vague_quality_improvement_without_deterministic_validator",
    "subjective_theory_content_rewrite_without_deterministic_check",
}

REQUIRED_BIRTH_SCHEMA_FIELDS = {
    "episode_id",
    "target_repo_url",
    "target_repo_branch",
    "baseline_sha",
    "task_head_sha_or_failing_sha",
    "post_repair_sha_if_repair_attempted",
    "original_repo_snapshot_manifest",
    "changed_files_snapshot",
    "dependency_lock_files",
    "environment_snapshot",
    "setup_command",
    "failing_command",
    "failing_log_raw",
    "failure_signature",
    "pre_repair_replay_transcript",
    "decision_time_inputs",
    "controllergate_action_trace",
    "repair_patch_diff",
    "post_repair_command",
    "post_repair_log_raw",
    "post_repair_outcome",
    "no_memory_baseline_result_if_run",
    "always_rebuild_baseline_result_if_run",
    "memory_enabled_result_if_run",
    "corruption_check_result",
    "human_required_flag",
    "decision_time_outcome_overlap_check",
    "sha256_manifest_path",
    "proof_obligations_ledger_path",
    "allowed_scoring_mode",
}

REQUIRED_LABELS = {
    "seeded_controlled_real_repo_episode",
    "discovered_user_owned_repo_episode",
    "forked_public_repo_episode",
    "synthetic_realistic_repo_episode",
    "historical_review_required_episode",
}

REQUIRED_SCORING_MODES = {
    "not_scoreable",
    "review_required",
    "deterministic_replay_ready",
    "limited_replay_scoring_only",
    "full_scoring_disallowed",
}


def load_json(path: Path) -> tuple[dict[str, Any], list[str]]:
    if not path.exists():
        return {}, [f"missing JSON file: {path}"]
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return {}, [f"{path}: invalid JSON: {exc.msg}"]
    if not isinstance(data, dict):
        return {}, [f"{path}: expected object"]
    return data, []


def require_text(path: Path, required: list[str]) -> list[str]:
    if not path.exists():
        return [f"missing text file: {path}"]
    text = path.read_text(encoding="utf-8")
    return [f"{path}: missing required text {item!r}" for item in required if item not in text]


def main() -> int:
    plan, plan_errors = load_json(PLAN_JSON_PATH)
    beta_plan, beta_errors = load_json(BETA_REPLAY_PLAN_PATH)
    errors = plan_errors + beta_errors

    if plan.get("plan_status") != "planning_only_no_scoring":
        errors.append("plan_status must be planning_only_no_scoring")
    if plan.get("controllergate_full_scoring") != "NOT_RUN":
        errors.append("controllergate_full_scoring must be NOT_RUN")
    if plan.get("full_scoring_allowed") is not False:
        errors.append("full_scoring_allowed must be false")
    if plan.get("memory_lift_claim_allowed") is not False:
        errors.append("memory_lift_claim_allowed must be false")
    if plan.get("self_maintaining_software_claim_allowed") is not False:
        errors.append("self_maintaining_software_claim_allowed must be false")

    policy = plan.get("controlled_target_repo_policy")
    if not isinstance(policy, dict):
        errors.append("controlled_target_repo_policy must be an object")
        policy = {}
    if policy.get("target_repo_class") != "user_owned_public_repo":
        errors.append("target_repo_class must be user_owned_public_repo")
    target = policy.get("preferred_initial_target")
    if not isinstance(target, dict):
        errors.append("preferred_initial_target must be an object")
        target = {}
    if target.get("repo_full_name") != "GenghisDarb/TORUS-Theory":
        errors.append("preferred initial target must be GenghisDarb/TORUS-Theory")
    if target.get("authorized_role") != "controlled replay-first real-repo testbed":
        errors.append("TORUS must be named only as an authorized controlled testbed")
    if "not proof" not in str(target.get("proof_boundary", "")).lower():
        errors.append("TORUS proof boundary must say not proof")
    for field in [
        "repo_may_be_forked_branched_cloned_instrumented_and_seeded",
        "all_original_repo_states_snapshotted_and_hashed_before_modification",
        "testbed_changes_on_clearly_named_branches",
        "generated_episodes_include_before_after_shas",
        "no_claim_depends_on_uncaptured_remote_only_logs",
    ]:
        if policy.get(field) is not True:
            errors.append(f"controlled_target_repo_policy.{field} must be true")

    acceptance = set(plan.get("candidate_target_acceptance_criteria") or [])
    for required in [
        "repo is owned or explicitly authorized by Brad",
        "clean clone can be obtained",
        "baseline SHA is recorded",
        "failure logs can be captured locally",
        "post-repair validation can be captured locally",
        "SHA256 manifest can cover all input/output artifacts",
    ]:
        if required not in acceptance:
            errors.append(f"candidate_target_acceptance_criteria missing {required!r}")
    rejection = set(plan.get("candidate_target_rejection_criteria") or [])
    if "no deterministic local check can be defined" not in rejection:
        errors.append("candidate_target_rejection_criteria must reject missing deterministic local checks")

    if set(plan.get("controlled_failure_types_allowed") or []) != REQUIRED_ALLOWED_FAILURES:
        errors.append("controlled_failure_types_allowed set is incomplete or changed")
    if set(plan.get("controlled_failure_types_disallowed") or []) != REQUIRED_DISALLOWED_FAILURES:
        errors.append("controlled_failure_types_disallowed set is incomplete or changed")

    birth_schema = set(plan.get("episode_birth_capture_schema") or [])
    missing_birth_fields = REQUIRED_BIRTH_SCHEMA_FIELDS - birth_schema
    if missing_birth_fields:
        errors.append(f"episode_birth_capture_schema missing {sorted(missing_birth_fields)}")

    replay_gate = plan.get("replay_gate")
    if not isinstance(replay_gate, dict):
        errors.append("replay_gate must be an object")
        replay_gate = {}
    for field in [
        "discard_before_scoring_if_clean_checkout_cannot_reproduce_pre_repair_failure",
        "discard_before_scoring_if_failing_log_missing",
        "discard_before_scoring_if_failure_signature_missing",
        "discard_before_scoring_if_repair_patch_or_action_trace_missing",
        "discard_before_scoring_if_post_repair_validation_missing",
        "discard_before_scoring_if_decision_time_inputs_include_future_outcome_evidence",
        "if_no_memory_baseline_absent_do_not_claim_memory_lift",
        "if_baseline_comparators_absent_do_not_claim_controllergate_advantage",
        "if_only_seeded_failure_label_as_seeded_controlled_real_repo_episode_not_external_organic_evidence",
    ]:
        if replay_gate.get(field) is not True:
            errors.append(f"replay_gate.{field} must be true")

    if set(plan.get("allowed_episode_labels") or []) != REQUIRED_LABELS:
        errors.append("allowed_episode_labels set is incomplete or changed")
    if set(plan.get("allowed_scoring_modes") or []) != REQUIRED_SCORING_MODES:
        errors.append("allowed_scoring_modes set is incomplete or changed")
    if "full_scoring" in set(plan.get("allowed_scoring_modes") or []):
        errors.append("full_scoring must not appear in allowed_scoring_modes")
    full_policy = plan.get("full_scoring_policy") or {}
    if full_policy.get("full_scoring_permitted_in_this_pass") is not False:
        errors.append("full scoring must remain disallowed in this pass")

    pilot = plan.get("initial_v1_8_pilot_design")
    if not isinstance(pilot, dict):
        errors.append("initial_v1_8_pilot_design must be an object")
        pilot = {}
    if pilot.get("target_repo") != "GenghisDarb/TORUS-Theory":
        errors.append("initial pilot target must be GenghisDarb/TORUS-Theory")
    if pilot.get("pilot_episode_count") != "1_to_3":
        errors.append("initial pilot must be limited to 1_to_3 episodes")
    if pilot.get("goal") != "validate_replay_capture_machinery_not_repair_intelligence":
        errors.append("initial pilot goal must be replay capture, not repair intelligence")

    tatmapper = plan.get("historical_tatmapper_boundary")
    if not isinstance(tatmapper, dict):
        errors.append("historical_tatmapper_boundary must be an object")
        tatmapper = {}
    if tatmapper.get("tatmapper_historical_episodes_remain_review_required") is not True:
        errors.append("TatMapper episodes must remain review_required")
    if tatmapper.get("tatmapper_deterministic_replay_ready_count") != 0:
        errors.append("TatMapper deterministic replay-ready count must remain 0")
    if tatmapper.get("do_not_mark_tatmapper_scoreable") is not True:
        errors.append("TatMapper must not be marked scoreable")
    if tatmapper.get("do_not_mix_tatmapper_with_v1_8_controlled_repo_episodes") is not True:
        errors.append("TatMapper must not be mixed with v1.8 controlled episodes")
    if beta_plan.get("summary", {}).get("eligible_now_count") != 0:
        errors.append("beta replay eligibility count must remain 0")

    memory = plan.get("memory_lift_boundary")
    if not isinstance(memory, dict):
        errors.append("memory_lift_boundary must be an object")
        memory = {}
    if memory.get("real_repo_memory_lift_demonstrated") is not False:
        errors.append("real_repo_memory_lift_demonstrated must be false")
    if memory.get("no_claim_without_baseline_instrumentation") is not True:
        errors.append("memory boundary must require no claim without baseline instrumentation")

    self_boundary = plan.get("self_maintaining_software_boundary")
    if not isinstance(self_boundary, dict):
        errors.append("self_maintaining_software_boundary must be an object")
        self_boundary = {}
    if self_boundary.get("self_maintaining_software_demonstrated") is not False:
        errors.append("self_maintaining_software_demonstrated must be false")
    if self_boundary.get("controlled_seeded_episodes_do_not_establish_self_maintenance") is not True:
        errors.append("seeded episodes must not establish self maintenance")

    stop_conditions = plan.get("falsification_and_stop_conditions")
    if not isinstance(stop_conditions, list) or len(stop_conditions) < 6:
        errors.append("falsification_and_stop_conditions must list at least 6 conditions")
    else:
        required_fragments = [
            "no replay-ready episodes",
            "cannot repair them under preregistered metrics",
            "does not outperform no-memory baselines",
            "only succeeds on seeded failures",
            "freeze or redesign the architecture",
            "does not falsify all possible self-maintaining software",
        ]
        combined = "\n".join(stop_conditions)
        for fragment in required_fragments:
            if fragment not in combined:
                errors.append(f"falsification_and_stop_conditions missing fragment {fragment!r}")

    errors.extend(
        require_text(
            PLAN_MD_PATH,
            [
                "Status: planning and audit layer only. Do not score.",
                "TORUS Theory repo",
                "authorized testbed, not as proof",
                "Seeded controlled real-repo episodes are weaker than organic external repo evidence",
                "Replay Gate",
                "Full scoring remains disallowed in this pass.",
                "Falsification and Stop Conditions",
                "Self-maintaining software remains undemonstrated.",
                "Memory lift remains undemonstrated until baselines pass under replay-ready conditions.",
            ],
        )
    )
    errors.extend(
        require_text(
            BETA_SHAREABLE_SUMMARY_PATH,
            [
                "## v1.8 controlled repo replay-first path",
                "TORUS Theory repo is authorized as a controlled testbed.",
                "Seeded controlled real-repo episodes may validate replay capture.",
                "Replay Gate must pass before scoring.",
                "Self-maintaining software remains undemonstrated.",
                "Memory lift remains undemonstrated until baselines pass under replay-ready conditions.",
            ],
        )
    )

    if errors:
        print("v1.8 controlled repo replay capture plan audit: FAIL")
        for error in errors:
            print(f"- {error}")
        return 1

    print("v1.8 controlled repo replay capture plan audit: PASS")
    print("target repo: GenghisDarb/TORUS-Theory")
    print("plan status: planning_only_no_scoring")
    print("full scoring allowed: false")
    print("memory lift claim allowed: false")
    print("self-maintaining software claim allowed: false")
    return 0


if __name__ == "__main__":
    sys.exit(main())
