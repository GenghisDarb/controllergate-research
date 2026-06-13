#!/usr/bin/env python3
"""Audit v2.8p BugsInPy harness-repair broad-harvest checkpoint/artifact."""

from __future__ import annotations

import hashlib
import json
import zipfile
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = REPO_ROOT / "outputs" / "v2_8p_bugsinpy_harness_repair_broad_harvest"
WORKFLOW = REPO_ROOT / ".github" / "workflows" / "v2_8p_bugsinpy_harness_repair_broad_harvest.yml"
RUNNER = REPO_ROOT / "scripts" / "v2_8p_bugsinpy_harness_repair_broad_harvest_runner.py"
PREP = REPO_ROOT / "scripts" / "v2_8p_prepare_bugsinpy_harness_repair_broad_harvest.py"
SUMMARY = REPO_ROOT / "controllergate_v1_7_beta" / "reports" / "critic_review_package" / "shareable_summary.md"
V28O_ARTIFACT = Path(r"C:\Users\thisb\Downloads\v2_8o_bugsinpy_broad_preflight_harvest_artifacts.zip")

EXPECTED_V28O_ZIP_SHA256 = "4ae274921bb0ea3a25a3443daaa77056c028d12be0b7910065a39623baea0a9e"

CLASSIFICATION_VOCABULARY = {
    "blocked_no_safe_patch_candidate_generated",
    "blocked_patch_did_not_apply",
    "blocked_replay_or_materialization_failure",
    "blocked_target_test_failed",
    "failed_both",
    "inconclusive_equal_performance",
    "no_memory_only",
    "positive_memory_only",
    "runner_regression_preserved_reference_failure",
}

REQUIRED_TOP_LEVEL = [
    "campaign_summary.md",
    "campaign_results.json",
    "decision_report.json",
    "aggregate_report.json",
    "aggregate_bugsinpy_real_bug_memory_lift_assessment.json",
    "bounded_repair_proposer_summary.json",
    "candidate_pool.json",
    "preserved_reference_gate_result.json",
    "harness_sanity_check.json",
    "command_normalization_policy_v2_8p.json",
    "broad_candidate_preflight_registry_v2_8p.json",
    "replacement_candidate_policy_v2_8p.json",
    "replacement_candidate_preflight_summary.json",
    "fixture_dependency_preflight_summary.json",
    "candidate_ranking_policy_v2_8p.json",
    "candidate_source_integrity_check.json",
    "decision_time_policy.json",
    "anti_leakage_policy.json",
    "source_discovery_summary.json",
    "pre_repair_replay_gate_summary.json",
    "workspace_equivalence_summary.json",
    "source_repair_vs_harness_separation.json",
    "classification_vocabulary_check.json",
    "audit.json",
    "package_verification.json",
    "artifact_sha256_verification.json",
    "SHA256SUMS.txt",
]

REPAIR_ATTEMPT_ARTIFACTS = [
    "episode_metadata.json",
    "candidate_preflight_result.json",
    "fixture_dependency_preflight_result.json",
    "command_normalization_result.json",
    "failing_command.txt",
    "normalized_failing_command.txt",
    "failing_log_raw.txt",
    "failure_signature.txt",
    "source_discovery_report.json",
    "ranked_candidate_source_files.json",
    "candidate_function_extracts.json",
    "repair_heuristic_selection.json",
    "no_memory_repair_candidate_generation.json",
    "memory_enabled_repair_candidate_generation.json",
    "no_memory_source_only_repair_patch.diff",
    "memory_enabled_source_only_repair_patch.diff",
    "patch_candidate_safety_check.json",
    "no_memory_patch_application_result.json",
    "memory_enabled_patch_application_result.json",
    "no_memory_post_repair_command.txt",
    "memory_enabled_post_repair_command.txt",
    "no_memory_post_repair_log_raw.txt",
    "memory_enabled_post_repair_log_raw.txt",
    "post_repair_comparison.json",
    "limited_scoring_result.json",
    "decision_time_input_manifest.json",
    "decision_time_outcome_overlap_check.json",
    "label_blindness_check.json",
    "gold_patch_exclusion_check.json",
    "corruption_check_result.json",
    "wrapper_contamination_check.json",
    "repair_materialization_separation.json",
    "proof_obligations_ledger.json",
    "SHA256SUMS.txt",
]


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


def sha_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


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


def verify_v28o_zip() -> list[str]:
    errors: list[str] = []
    if not V28O_ARTIFACT.exists():
        return [f"missing official v2.8o artifact zip: {V28O_ARTIFACT}"]
    if sha_file(V28O_ARTIFACT) != EXPECTED_V28O_ZIP_SHA256:
        errors.append("official v2.8o artifact SHA256 mismatch")
    with zipfile.ZipFile(V28O_ARTIFACT) as archive:
        bad = archive.testzip()
        if bad is not None:
            errors.append(f"official v2.8o zip has bad member: {bad}")
        names = set(archive.namelist())
        if "SHA256SUMS.txt" not in names:
            errors.append("official v2.8o zip missing SHA256SUMS.txt")
            return errors
        missing = 0
        failures = 0
        checked = 0
        for raw in archive.read("SHA256SUMS.txt").decode("utf-8").splitlines():
            if not raw.strip():
                continue
            parts = raw.split()
            if len(parts) < 2:
                continue
            expected, rel = parts[0], parts[1]
            if rel not in names:
                missing += 1
                continue
            checked += 1
            if hashlib.sha256(archive.read(rel)).hexdigest() != expected:
                failures += 1
        if checked != 664:
            errors.append(f"official v2.8o internal SHA256 checked count expected 664, got {checked}")
        if missing != 0 or failures != 0:
            errors.append(f"official v2.8o internal SHA256 verification expected 0 missing/failures, got {missing}/{failures}")
        campaign = json.loads(archive.read("campaign_results.json").decode("utf-8"))
        if campaign.get("scoreable_episode_count") != 0 or campaign.get("preflight_passing_candidate_count") != 0:
            errors.append("official v2.8o regression baseline must remain 0 scoreable and 0 preflight-passing")
        decision = json.loads(archive.read("decision_report.json").decode("utf-8"))
        by_candidate = {record.get("candidate"): record for record in decision.get("records", [])}
        if by_candidate.get("youtube-dl:1", {}).get("scoreable") is not False:
            errors.append("official v2.8o youtube-dl:1 regression baseline not recorded")
        if by_candidate.get("black:4", {}).get("scoreable") is not False:
            errors.append("official v2.8o black:4 regression baseline not recorded")
    return errors


def text_contains(path: Path, snippets: list[str]) -> list[str]:
    if not path.exists():
        return [f"missing text file: {path}"]
    text = path.read_text(encoding="utf-8", errors="replace")
    return [f"{path}: missing {snippet!r}" for snippet in snippets if snippet not in text]


def main() -> int:
    errors: list[str] = []
    for path in [WORKFLOW, RUNNER, PREP]:
        if not path.exists():
            errors.append(f"missing v2.8p implementation file: {path}")
    if not OUTPUT_DIR.exists():
        errors.append(f"missing v2.8p output directory: {OUTPUT_DIR}")
    else:
        for name in REQUIRED_TOP_LEVEL:
            path = OUTPUT_DIR / name
            if not path.exists():
                errors.append(f"missing v2.8p artifact: {path}")
            elif path.stat().st_size == 0:
                errors.append(f"empty v2.8p artifact: {path}")
        errors.extend(verify_manifest(OUTPUT_DIR))

    errors.extend(verify_v28o_zip())

    campaign, e = load_json(OUTPUT_DIR / "campaign_results.json")
    errors.extend(e)
    aggregate, e = load_json(OUTPUT_DIR / "aggregate_bugsinpy_real_bug_memory_lift_assessment.json")
    errors.extend(e)
    decision, e = load_json(OUTPUT_DIR / "decision_report.json")
    errors.extend(e)
    gate, e = load_json(OUTPUT_DIR / "preserved_reference_gate_result.json")
    errors.extend(e)
    harness, e = load_json(OUTPUT_DIR / "harness_sanity_check.json")
    errors.extend(e)
    normalization, e = load_json(OUTPUT_DIR / "command_normalization_policy_v2_8p.json")
    errors.extend(e)
    registry, e = load_json(OUTPUT_DIR / "broad_candidate_preflight_registry_v2_8p.json")
    errors.extend(e)
    vocab, e = load_json(OUTPUT_DIR / "classification_vocabulary_check.json")
    errors.extend(e)
    source_separation, e = load_json(OUTPUT_DIR / "source_repair_vs_harness_separation.json")
    errors.extend(e)

    if campaign.get("full_scoring_allowed") is not False or campaign.get("controllergate_full_scoring") != "NOT_RUN":
        errors.append("v2.8p must keep full scoring NOT_RUN / disallowed")
    if campaign.get("self_maintaining_software_demonstrated") is not False:
        errors.append("v2.8p must not claim self-maintaining software")
    if aggregate.get("limited_bugsinpy_real_bug_memory_lift_criteria_met") is True and aggregate.get("positive_memory_episode_count", 0) < 2:
        errors.append("v2.8p cannot claim memory lift without at least two positive memory episodes")
    if normalization.get("raw_pytest_command_policy") is None or "python -m pytest" not in json.dumps(normalization):
        errors.append("v2.8p must document pytest command normalization to python -m pytest")
    if "returncode 127" not in json.dumps(normalization):
        errors.append("v2.8p must document returncode 127 as harness/normalization failure")
    if source_separation.get("tests_may_be_modified_as_repair") is not False:
        errors.append("v2.8p must forbid test edits as repair candidates")

    workflow_executed = campaign.get("workflow_executed") is True
    if not workflow_executed:
        if campaign.get("aggregate_result") != "blocked_pending_v2_8p_harness_repair_broad_harvest_artifact":
            errors.append("local v2.8p checkpoint must be pending Linux artifact")
        if campaign.get("scoreable_episode_count") != 0:
            errors.append("local v2.8p checkpoint must not claim scoreable episodes")
        if gate.get("status") != "PENDING_GITHUB_ACTIONS":
            errors.append("local v2.8p preserved-reference gate must be pending")
    else:
        records = decision.get("records", [])
        by_candidate = {record.get("candidate"): record for record in records}
        if gate.get("status") != "PASS":
            errors.append("executed v2.8p preserved-reference gate must pass")
        if harness.get("status") != "PASS":
            errors.append("executed v2.8p harness sanity must pass")
        for candidate in ["youtube-dl:1", "black:4"]:
            if by_candidate.get(candidate, {}).get("scoreable") is not True:
                errors.append(f"executed v2.8p must restore {candidate} as scoreable")
        if campaign.get("scoreable_episode_count", 0) < 2:
            errors.append("executed v2.8p must have at least two scoreable episodes")
        if campaign.get("label_leakage_count") != 0 or campaign.get("decision_time_outcome_overlap_count") != 0 or campaign.get("corruption_count") != 0:
            errors.append("executed v2.8p must have zero leakage/overlap/corruption")
        if campaign.get("broad_preflight_candidate_count", 0) < 20 and registry.get("available_candidate_count", 0) >= 20 and gate.get("status") == "PASS":
            errors.append("executed v2.8p must preflight at least 20 broad candidates when available")
        for record in registry.get("records", []):
            if record.get("pre_repair_command_returncode") == 127 and record.get("blocked_reason") != "runner_command_normalization_failure_not_candidate_failure":
                errors.append(f"returncode 127 was not classified as harness failure for {record.get('candidate_id')}")
        for record in records:
            classification = record.get("classification")
            if classification not in CLASSIFICATION_VOCABULARY:
                errors.append(f"unexpected v2.8p classification: {classification}")
            directory = OUTPUT_DIR / str(record.get("episode_id"))
            if not directory.exists():
                errors.append(f"executed v2.8p missing {directory}")
                continue
            for name in REPAIR_ATTEMPT_ARTIFACTS:
                if not (directory / name).exists():
                    errors.append(f"executed v2.8p {record.get('episode_id')} missing {name}")
            command_norm, ep_errors = load_json(directory / "command_normalization_result.json")
            errors.extend(ep_errors)
            if command_norm.get("pythonpath_includes_project_root") is not True:
                errors.append(f"executed v2.8p {record.get('episode_id')} missing project root PYTHONPATH")
            errors.extend(verify_manifest(directory))
        if vocab.get("status") != "PASS":
            errors.append("executed v2.8p classification vocabulary check must pass")

    runner_text = RUNNER.read_text(encoding="utf-8", errors="replace") if RUNNER.exists() else ""
    for snippet in [
        "restore_preserved_reference_hooks",
        "normalize_command",
        "python -m pytest",
        "preserved_reference_gate_result",
        "runner_regression_preserved_reference_failure",
        "PYTHONPATH",
        "returncode_127_treated_as_harness_failure",
    ]:
        if snippet not in runner_text:
            errors.append(f"v2.8p runner missing required snippet: {snippet}")
    workflow_text = WORKFLOW.read_text(encoding="utf-8", errors="replace") if WORKFLOW.exists() else ""
    for snippet in ["workflow_dispatch", "v2_8p_bugsinpy_harness_repair_broad_harvest_artifacts", "preserved_reference_gate_result"]:
        if snippet not in workflow_text:
            errors.append(f"v2.8p workflow missing required snippet: {snippet}")
    errors.extend(text_contains(SUMMARY, ["v2.8p BugsInPy Harness Repair Broad Harvest", "Returncode 127", "Memory lift is not demonstrated", "Self-maintaining software is not demonstrated"]))

    if errors:
        print("v2.8p BugsInPy harness repair broad harvest audit FAIL")
        for error in errors:
            print(f"- {error}")
        return 1
    print("v2.8p BugsInPy harness repair broad harvest audit PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
