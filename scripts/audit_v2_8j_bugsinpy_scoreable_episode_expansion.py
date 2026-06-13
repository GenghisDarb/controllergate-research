#!/usr/bin/env python3
"""Audit v2.8j BugsInPy scoreable episode expansion."""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = REPO_ROOT / "outputs" / "v2_8j_bugsinpy_scoreable_episode_expansion"
WORKFLOW = REPO_ROOT / ".github" / "workflows" / "v2_8j_bugsinpy_scoreable_episode_expansion.yml"
RUNNER = REPO_ROOT / "scripts" / "v2_8j_bugsinpy_scoreable_episode_expansion_runner.py"
PREP = REPO_ROOT / "scripts" / "v2_8j_prepare_bugsinpy_scoreable_episode_expansion.py"
SUMMARY = REPO_ROOT / "controllergate_v1_7_beta" / "reports" / "critic_review_package" / "shareable_summary.md"
V28I_RESULTS = REPO_ROOT / "outputs" / "v2_8i_bugsinpy_real_bug_boolean_patch_comparison" / "campaign_results.json"
V28I_BOOLEAN = REPO_ROOT / "outputs" / "v2_8i_bugsinpy_boolean_patch_construction_fix" / "v2_8i_boolean_patch_construction_result.json"

REQUIRED = [
    "campaign_plan.json",
    "candidate_pool.json",
    "previous_v2_8i_scoreable_reference.json",
    "source_repair_vs_harness_separation.json",
    "scoreable_episode_expansion_policy.json",
    "black_candidate_generation_policy.json",
    "decision_report.json",
    "aggregate_report.json",
    "campaign_results.json",
    "aggregate_bugsinpy_real_bug_memory_lift_assessment.json",
    "label_hygiene_check.json",
    "artifact_sha256_verification.json",
    "github_actions_artifact_metadata.json",
    "linux_artifact_ingestion_metadata.json",
    "large_workspace_snapshots_index.json",
    "audit.json",
    "verification_commands.md",
    "campaign_summary.md",
    "SHA256SUMS.txt",
]

EPISODES = {
    "episode_001": "youtube-dl:1",
    "episode_002": "black:8",
    "episode_003": "black:4",
}


def load_json(path: Path) -> tuple[dict[str, Any], list[str]]:
    if not path.exists():
        return {}, [f"missing JSON file: {path}"]
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return {}, [f"{path}: invalid JSON: {exc.msg}"]
    if not isinstance(data, dict):
        return {}, [f"{path}: expected JSON object"]
    return data, []


def verify_manifest(directory: Path) -> list[str]:
    manifest = directory / "SHA256SUMS.txt"
    if not manifest.exists():
        return [f"missing SHA256SUMS.txt in {directory}"]
    errors: list[str] = []
    seen: set[str] = set()
    for line_no, line in enumerate(manifest.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        parts = line.split()
        if len(parts) != 2:
            errors.append(f"{manifest}:{line_no}: expected '<sha256>  <path>'")
            continue
        expected, rel = parts
        seen.add(rel)
        path = directory / rel
        if not path.exists():
            errors.append(f"{manifest}:{line_no}: missing artifact {rel}")
            continue
        actual = hashlib.sha256(path.read_bytes()).hexdigest()
        if actual != expected:
            errors.append(f"{manifest}:{line_no}: hash mismatch for {rel}")
    for path in directory.rglob("*"):
        if path.is_file() and path.name != "SHA256SUMS.txt":
            rel = str(path.relative_to(directory)).replace("\\", "/")
            if rel not in seen:
                errors.append(f"SHA256SUMS missing artifact entry {rel}")
    return errors


def require_text(path: Path, snippets: list[str]) -> list[str]:
    if not path.exists():
        return [f"missing text file: {path}"]
    text = path.read_text(encoding="utf-8", errors="replace")
    return [f"{path}: missing required text {snippet!r}" for snippet in snippets if snippet not in text]


def scan_for_stale_labels(directory: Path) -> list[str]:
    errors: list[str] = []
    forbidden = ["v2.8g BugsInPy", "v2_8g_bugsinpy", "v2.8i BugsInPy Boolean Patch Construction Fix"]
    for path in directory.rglob("*"):
        if not path.is_file() or path.name == "SHA256SUMS.txt":
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        for marker in forbidden:
            if marker in text:
                errors.append(f"{path}: stale label {marker!r} appears in v2.8j artifact")
    return errors


def main() -> int:
    errors: list[str] = []
    for path in [WORKFLOW, RUNNER, PREP]:
        if not path.exists():
            errors.append(f"missing v2.8j implementation file: {path}")
    if not OUTPUT_DIR.exists():
        errors.append(f"missing v2.8j output directory: {OUTPUT_DIR}")
    else:
        for name in REQUIRED:
            path = OUTPUT_DIR / name
            if not path.exists():
                errors.append(f"missing v2.8j artifact: {path}")
            elif path.stat().st_size == 0:
                errors.append(f"empty v2.8j artifact: {path}")
        errors.extend(verify_manifest(OUTPUT_DIR))
        errors.extend(scan_for_stale_labels(OUTPUT_DIR))
        for episode_id, candidate in EPISODES.items():
            meta, meta_errors = load_json(OUTPUT_DIR / episode_id / "episode_metadata.json")
            errors.extend(meta_errors)
            if meta and meta.get("candidate") != candidate:
                errors.append(f"{episode_id} expected {candidate}, found {meta.get('candidate')}")
            for patch_name in ["no_memory_source_only_repair_patch.diff", "memory_enabled_source_only_repair_patch.diff"]:
                patch = OUTPUT_DIR / episode_id / patch_name
                if not patch.exists():
                    errors.append(f"missing v2.8j per-episode patch artifact: {patch}")

    plan, plan_errors = load_json(OUTPUT_DIR / "campaign_plan.json")
    pool, pool_errors = load_json(OUTPUT_DIR / "candidate_pool.json")
    prior, prior_errors = load_json(OUTPUT_DIR / "previous_v2_8i_scoreable_reference.json")
    separation, separation_errors = load_json(OUTPUT_DIR / "source_repair_vs_harness_separation.json")
    policy, policy_errors = load_json(OUTPUT_DIR / "scoreable_episode_expansion_policy.json")
    black_policy, black_policy_errors = load_json(OUTPUT_DIR / "black_candidate_generation_policy.json")
    campaign, campaign_errors = load_json(OUTPUT_DIR / "campaign_results.json")
    decision, decision_errors = load_json(OUTPUT_DIR / "decision_report.json")
    aggregate, aggregate_errors = load_json(OUTPUT_DIR / "aggregate_bugsinpy_real_bug_memory_lift_assessment.json")
    aggregate_report, aggregate_report_errors = load_json(OUTPUT_DIR / "aggregate_report.json")
    hygiene, hygiene_errors = load_json(OUTPUT_DIR / "label_hygiene_check.json")
    artifact_verification, artifact_verification_errors = load_json(OUTPUT_DIR / "artifact_sha256_verification.json")
    artifact_metadata, artifact_metadata_errors = load_json(OUTPUT_DIR / "github_actions_artifact_metadata.json")
    ingestion_metadata, ingestion_metadata_errors = load_json(OUTPUT_DIR / "linux_artifact_ingestion_metadata.json")
    excluded_snapshots, excluded_snapshots_errors = load_json(OUTPUT_DIR / "large_workspace_snapshots_index.json")
    v28i_results, v28i_errors = load_json(V28I_RESULTS)
    v28i_boolean, v28i_boolean_errors = load_json(V28I_BOOLEAN)
    errors.extend(
        plan_errors
        + pool_errors
        + prior_errors
        + separation_errors
        + policy_errors
        + black_policy_errors
        + campaign_errors
        + decision_errors
        + aggregate_errors
        + aggregate_report_errors
        + hygiene_errors
        + artifact_verification_errors
        + artifact_metadata_errors
        + ingestion_metadata_errors
        + excluded_snapshots_errors
        + v28i_errors
        + v28i_boolean_errors
    )

    if plan.get("campaign_id") != "v2_8j_bugsinpy_scoreable_episode_expansion":
        errors.append("v2.8j campaign_plan has wrong campaign_id")
    if plan.get("full_scoring_allowed") is not False or plan.get("controllergate_full_scoring") != "NOT_RUN":
        errors.append("v2.8j must keep full scoring NOT_RUN / disallowed")
    if plan.get("self_maintaining_software_demonstrated") is not False:
        errors.append("v2.8j must not claim self-maintaining software")
    candidates = [item.get("candidate") for item in pool.get("records", [])]
    if candidates != ["youtube-dl:1", "black:8", "black:4"]:
        errors.append(f"v2.8j candidate pool mismatch: {candidates}")
    if prior.get("candidate") != "youtube-dl:1" or prior.get("classification") != "inconclusive_equal_performance" or prior.get("scoreable") is not True:
        errors.append("v2.8j must preserve youtube-dl:1 as scoreable inconclusive reference")
    if separation.get("tests_may_be_modified_as_repair") is not False:
        errors.append("v2.8j must forbid test edits as repair candidates")
    if separation.get("dependency_runtime_setup_is_not_code_repair") is not True:
        errors.append("v2.8j must distinguish dependency/runtime setup from code repair")
    if policy.get("no_patch_or_no_op_is_scoreable") is not False:
        errors.append("v2.8j must not count no-patch/no-op traces as scoreable")
    for required_label in ["positive_memory_only", "no_memory_only", "inconclusive_equal_performance", "failed_both", "blocked_no_safe_patch_candidate_generated"]:
        if required_label not in policy.get("classification_vocabulary", []):
            errors.append(f"v2.8j classification vocabulary missing {required_label}")
    if black_policy.get("source_only") is not True:
        errors.append("v2.8j Black candidate generation must be source-only")
    if black_policy.get("fixed_or_gold_patch_used") is not False or black_policy.get("future_outcome_evidence_used") is not False:
        errors.append("v2.8j Black policy must forbid fixed/gold/future evidence")
    if hygiene.get("campaign_label") != "v2.8j" or hygiene.get("current_artifact_uses_v2_8j_names") is not True:
        errors.append("v2.8j label hygiene check must name v2.8j")

    workflow_executed = campaign.get("workflow_executed") is True
    if not workflow_executed:
        if campaign.get("aggregate_result") != "blocked_pending_v2_8j_scoreable_episode_expansion_artifact":
            errors.append("local v2.8j checkpoint must be blocked_pending_v2_8j_scoreable_episode_expansion_artifact")
        if campaign.get("scoreable_episode_count") != 0:
            errors.append("local pending v2.8j checkpoint must not claim scoreable episodes")
    else:
        if campaign.get("executed_episode_count") != 3:
            errors.append("executed v2.8j must run exactly three promoted BugsInPy episodes")
        if campaign.get("scoreable_episode_count") != 2:
            errors.append("executed v2.8j official Linux result must preserve exactly two scoreable episodes")
        if campaign.get("positive_memory_episode_count") != 0:
            errors.append("executed v2.8j official Linux result must preserve zero positive memory episodes")
        if campaign.get("aggregate_result") != "insufficient_episode_count_for_bugsinpy_real_bug_memory_lift":
            errors.append("executed v2.8j official Linux result must remain insufficient count")
        if campaign.get("full_scoring_allowed") is not False or campaign.get("controllergate_full_scoring") != "NOT_RUN":
            errors.append("executed v2.8j must keep full scoring NOT_RUN / disallowed")
        if campaign.get("self_maintaining_software_demonstrated") is not False:
            errors.append("executed v2.8j must not claim self-maintaining software")
        if aggregate.get("scoreable_episode_count") != 2 or aggregate.get("positive_memory_episode_count") != 0:
            errors.append("executed v2.8j aggregate assessment must preserve two scoreable, zero positive memory episodes")
        if aggregate_report.get("positive_memory_only_episode_count") != 0:
            errors.append("executed v2.8j aggregate report must preserve zero positive memory-only episodes")
        decision_records = {record.get("candidate"): record for record in decision.get("records", [])}
        expected = {
            "youtube-dl:1": ("inconclusive_equal_performance", True),
            "black:8": ("failed_both", False),
            "black:4": ("inconclusive_equal_performance", True),
        }
        for candidate, (classification, scoreable) in expected.items():
            record = decision_records.get(candidate)
            if not record:
                errors.append(f"executed v2.8j decision report missing {candidate}")
                continue
            if record.get("classification") != classification or record.get("scoreable") is not scoreable:
                errors.append(
                    f"executed v2.8j decision report for {candidate} expected "
                    f"{classification}/{scoreable}, found {record.get('classification')}/{record.get('scoreable')}"
                )
        if aggregate.get("limited_bugsinpy_real_bug_memory_lift_criteria_met") is True and campaign.get("positive_memory_episode_count", 0) < 2:
            errors.append("v2.8j cannot claim memory lift without at least two positive memory episodes")
        if artifact_verification.get("artifact_zip_sha256") != "363a3a4bfc3ddac3f95bb0f09ac4fe7b632acf84d6747a25f91f5c8414e30ed1":
            errors.append("v2.8j artifact SHA256 verification does not match uploaded Linux artifact")
        if artifact_verification.get("internal_hash_failures") != 0 or artifact_verification.get("internal_missing_entries") != 0:
            errors.append("v2.8j artifact internal SHA256 verification must be clean")
        if artifact_metadata.get("artifact_name") != "v2_8j_bugsinpy_scoreable_episode_expansion_artifacts":
            errors.append("v2.8j artifact metadata has wrong artifact name")
        if artifact_metadata.get("artifact_zip_committed_to_repository") is not False:
            errors.append("v2.8j Linux artifact zip must not be marked as committed")
        if ingestion_metadata.get("official_result_confirmed") is not True:
            errors.append("v2.8j ingestion metadata must confirm official Linux result")
        if excluded_snapshots.get("excluded_large_artifact_count") != 3:
            errors.append("v2.8j must index the three excluded large workspace tar snapshots")

    if v28i_results.get("scoreable_episode_count") != 1 or v28i_results.get("positive_memory_episode_count") != 0:
        errors.append("v2.8j must preserve v2.8i one-scoreable, zero-positive result")
    if v28i_boolean.get("result_interpretation") != "scoreable_inconclusive_equal_performance_not_memory_lift":
        errors.append("v2.8j must preserve v2.8i youtube-dl tie interpretation")

    if RUNNER.exists():
        runner_text = RUNNER.read_text(encoding="utf-8")
        for snippet in [
            "black_comment_trailing_comma_guard",
            "black_beginning_backslash_leading_newline_guard",
            "source_repair_vs_harness_separation",
            "source_only_repair_patch.diff",
            "fixed_or_gold_patch_used",
            "future_outcome_evidence_used",
            "tests_may_be_modified",
        ]:
            if snippet not in runner_text:
                errors.append(f"v2.8j runner missing required guard/generator snippet: {snippet}")
    errors.extend(require_text(SUMMARY, ["v2.8j BugsInPy Scoreable Episode Expansion", "Scoreable episodes: 2", "Full scoring: NOT_RUN / disallowed", "Memory lift: not demonstrated", "Self-maintaining software: not demonstrated"]))

    if errors:
        print("v2.8j BugsInPy scoreable episode expansion audit FAIL")
        for error in errors:
            print(f"- {error}")
        return 1
    print("v2.8j BugsInPy scoreable episode expansion audit PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
