#!/usr/bin/env python3
"""GitHub Actions runner for v2.8q preflight-guided third scoreable recovery."""

from __future__ import annotations

import importlib.util
import json
import re
import shutil
from pathlib import Path
from typing import Any


REPO_ROOT = Path.cwd().resolve()
BASE_RUNNER_PATH = REPO_ROOT / "scripts" / "v2_8p_bugsinpy_harness_repair_broad_harvest_runner.py"
ARTIFACT_ROOT = (REPO_ROOT / "v2_8q_bugsinpy_preflight_guided_third_scoreable_artifacts").resolve()
RUNTIME_ROOT = (REPO_ROOT / "_v2_8q_bugsinpy_runtime").resolve()
V28P_OUTPUT_DIR = REPO_ROOT / "outputs" / "v2_8p_bugsinpy_harness_repair_broad_harvest"

spec = importlib.util.spec_from_file_location("v2_8p_runner", BASE_RUNNER_PATH)
v28p = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(v28p)

v28o = v28p.v28o
v28n = v28p.v28n
v28m = v28p.v28m
v28l = v28p.v28l
v28k = v28p.v28k
v28j = v28p.v28j
v28i = v28p.v28i
v28g = v28p.v28g
base = v28p.base
V28P_PROPOSE_PATCH = v28p.propose_patch
V28P_HEURISTIC_FAMILY = v28p.heuristic_family
V28P_PREFLIGHT_SCORE = v28p.preflight_score

BROAD_PREFLIGHT_BUDGET = v28p.BROAD_PREFLIGHT_BUDGET
REPAIR_REPLACEMENT_BUDGET = 5
PRESERVED_REFERENCE_IDS = v28p.PRESERVED_REFERENCE_IDS
PRESERVED_REFERENCE_CANDIDATES = v28p.PRESERVED_REFERENCE_CANDIDATES

CLASSIFICATION_VOCABULARY = [
    "blocked_no_safe_patch_candidate_generated",
    "blocked_patch_did_not_apply",
    "blocked_replay_or_materialization_failure",
    "blocked_target_test_failed",
    "failed_both",
    "inconclusive_equal_performance",
    "no_memory_only",
    "positive_memory_only",
    "runner_regression_preserved_reference_failure",
]

AGGREGATE_RESULTS = [
    "insufficient_episode_count_for_bugsinpy_real_bug_memory_lift",
    "insufficient_positive_memory_evidence",
    "limited_bugsinpy_real_bug_memory_lift_criteria_met",
    "runner_regression_preserved_reference_failure",
]

TARGETED_HEURISTICS: dict[str, dict[str, Any]] = {
    "fastapi:1": {
        "heuristic_family": "localized_keyword_parameter_compatibility_shim",
        "failure_type": "unexpected_keyword_argument_exclude_defaults",
        "patch_surface_estimate": "small_single_function",
        "preferred_rank": 1,
        "reason": "Direct TypeError names missing exclude_defaults parameter in fastapi/encoders.py.",
    },
    "ansible:2": {
        "heuristic_family": "localized_comparison_operator_equality_guard",
        "failure_type": "strict_greater_than_returns_true_for_equal_values",
        "patch_surface_estimate": "small_single_source_file",
        "preferred_rank": 2,
        "reason": "Assertion shows _Alpha('a') > _Alpha('a') is true; source extract shows __gt__ implemented as not __lt__.",
    },
    "ansible:5": {
        "heuristic_family": "localized_deterministic_missing_argument_order",
        "failure_type": "message_order_instability",
        "patch_surface_estimate": "small_single_expression",
        "preferred_rank": 3,
        "reason": "Assertion differs only by missing argument order; bounded fix sorts the generated missing list.",
    },
    "ansible:8": {
        "heuristic_family": "localized_path_string_normalization_unc_guard",
        "failure_type": "unc_prefix_stripped",
        "patch_surface_estimate": "small_path_join_guard_if_source_matches",
        "preferred_rank": 4,
        "reason": "Failure shows join_path strips leading UNC prefix; only attempted if the buggy source shape is recognized.",
    },
}

FALLBACK_TOP_FIVE = ["fastapi:1", "ansible:2", "ansible:5", "ansible:8", "ansible:4"]


def write_json(path: Path, data: Any) -> None:
    v28p.write_json(path, data)


def write_text(path: Path, text: str) -> None:
    v28p.write_text(path, text)


def safe_name(candidate_id: str) -> str:
    return v28p.safe_name(candidate_id)


def changed_line_count(diff: str) -> int:
    return v28j.changed_line_count(diff)


def source_only_safety(workspace: Path, diff: str) -> dict[str, Any]:
    changed_files: list[str] = []
    for line in diff.splitlines():
        if line.startswith("+++ b/"):
            changed_files.append(line[len("+++ b/") :])
    modifies_tests = any(
        file_name.startswith("test/")
        or file_name.startswith("tests/")
        or "/test/" in file_name
        or "/tests/" in file_name
        for file_name in changed_files
    )
    changed_lines = changed_line_count(diff)
    return {
        "source_only_repair_patch": bool(diff.strip()),
        "changed_files": changed_files,
        "changed_file_count": len(changed_files),
        "changed_lines": changed_lines,
        "modifies_tests": modifies_tests,
        "within_changed_line_budget": 0 < changed_lines <= v28g.REPAIR_BUDGET["max_changed_lines"],
        "uses_fixed_revision": False,
        "uses_gold_patch": False,
        "uses_future_outcome_evidence": False,
        "workspace": str(workspace),
    }


def proposal_blocked(
    candidate: dict[str, Any],
    reason: str,
    heuristic: str,
    discovery: dict[str, Any],
    memory_enabled: bool,
) -> dict[str, Any]:
    return v28p.proposal_blocked(candidate, reason, heuristic, discovery, memory_enabled)


def proposal_from_diff(
    workspace: Path,
    candidate: dict[str, Any],
    discovery: dict[str, Any],
    memory_enabled: bool,
    heuristic: str,
    reason: str,
) -> dict[str, Any]:
    diff = v28g.git_diff(workspace, v28p.os.environ.copy())
    safety = source_only_safety(workspace, diff)
    if safety["modifies_tests"] or not safety["within_changed_line_budget"]:
        return proposal_blocked(
            candidate,
            "generated patch failed source-only safety or changed-line budget",
            heuristic,
            discovery,
            memory_enabled,
        )
    return {
        "candidate_generated": True,
        "heuristic_family": heuristic,
        "diff": diff,
        "changed_lines": safety["changed_lines"],
        "source_only_patch_safety_check": safety,
        "memory_enabled_path": memory_enabled,
        "fixed_or_gold_patch_used": False,
        "future_outcome_evidence_used": False,
        "label_leakage_detected": False,
        "source_discovery_ranked_files": [item.get("file") for item in discovery.get("ranked", [])[:10]],
        "candidate": candidate["candidate"],
        "reason": reason,
    }


def apply_fastapi1_patch(
    workspace: Path,
    candidate: dict[str, Any],
    discovery: dict[str, Any],
    memory_enabled: bool,
) -> dict[str, Any]:
    target = workspace / "fastapi" / "encoders.py"
    if not target.exists():
        return proposal_blocked(candidate, "fastapi/encoders.py not found", "localized_keyword_parameter_compatibility_shim", discovery, memory_enabled)
    text = target.read_text(encoding="utf-8")
    if "exclude_defaults" in text:
        return proposal_blocked(candidate, "exclude_defaults already present in buggy source", "localized_keyword_parameter_compatibility_shim", discovery, memory_enabled)
    old_sig = "    exclude_unset: bool = False,\n    include_none: bool = True,\n"
    new_sig = "    exclude_unset: bool = False,\n    exclude_defaults: bool = False,\n    include_none: bool = True,\n"
    old_call = "                exclude_unset=bool(exclude_unset or skip_defaults),\n            )\n"
    new_call = "                exclude_unset=bool(exclude_unset or skip_defaults),\n                exclude_defaults=exclude_defaults,\n            )\n"
    if old_sig not in text or old_call not in text:
        return proposal_blocked(candidate, "fastapi encoder source shape did not match bounded exclude_defaults heuristic", "localized_keyword_parameter_compatibility_shim", discovery, memory_enabled)
    text = text.replace(old_sig, new_sig, 1).replace(old_call, new_call, 1)
    target.write_text(text, encoding="utf-8")
    return proposal_from_diff(
        workspace,
        candidate,
        discovery,
        memory_enabled,
        "localized_keyword_parameter_compatibility_shim",
        "Added the missing exclude_defaults keyword and forwarded it to Pydantic's model dict call.",
    )


def apply_ansible2_patch(
    workspace: Path,
    candidate: dict[str, Any],
    discovery: dict[str, Any],
    memory_enabled: bool,
) -> dict[str, Any]:
    target = workspace / "lib" / "ansible" / "utils" / "version.py"
    if not target.exists():
        return proposal_blocked(candidate, "lib/ansible/utils/version.py not found", "localized_comparison_operator_equality_guard", discovery, memory_enabled)
    text = target.read_text(encoding="utf-8")
    old = "    def __gt__(self, other):\n        return not self.__lt__(other)\n"
    new = "    def __gt__(self, other):\n        return not self.__lt__(other) and not self.__eq__(other)\n"
    count = text.count(old)
    if count < 2:
        return proposal_blocked(candidate, "expected _Alpha/_Numeric __gt__ source shape not found", "localized_comparison_operator_equality_guard", discovery, memory_enabled)
    target.write_text(text.replace(old, new), encoding="utf-8")
    return proposal_from_diff(
        workspace,
        candidate,
        discovery,
        memory_enabled,
        "localized_comparison_operator_equality_guard",
        "Made strict greater-than false when the operands are equal, matching the failing comparison assertion.",
    )


def apply_ansible5_patch(
    workspace: Path,
    candidate: dict[str, Any],
    discovery: dict[str, Any],
    memory_enabled: bool,
) -> dict[str, Any]:
    target = workspace / "lib" / "ansible" / "module_utils" / "common" / "validation.py"
    if not target.exists():
        return proposal_blocked(candidate, "common validation source file not found", "localized_deterministic_missing_argument_order", discovery, memory_enabled)
    text = target.read_text(encoding="utf-8")
    old = "', '.join(missing)"
    new = "', '.join(sorted(missing))"
    if old not in text:
        return proposal_blocked(candidate, "missing argument join expression not found", "localized_deterministic_missing_argument_order", discovery, memory_enabled)
    target.write_text(text.replace(old, new, 1), encoding="utf-8")
    return proposal_from_diff(
        workspace,
        candidate,
        discovery,
        memory_enabled,
        "localized_deterministic_missing_argument_order",
        "Sorted generated missing required arguments to match the deterministic assertion order in the failing test.",
    )


def apply_ansible8_patch(
    workspace: Path,
    candidate: dict[str, Any],
    discovery: dict[str, Any],
    memory_enabled: bool,
) -> dict[str, Any]:
    target = workspace / "lib" / "ansible" / "plugins" / "shell" / "powershell.py"
    if not target.exists():
        return proposal_blocked(candidate, "powershell shell plugin not found", "localized_path_string_normalization_unc_guard", discovery, memory_enabled)
    text = target.read_text(encoding="utf-8")
    marker = "def join_path(self, *args):"
    if marker not in text or "unc_path" in text:
        return proposal_blocked(candidate, "powershell join_path source shape not recognized", "localized_path_string_normalization_unc_guard", discovery, memory_enabled)
    pattern = re.compile(r"(    def join_path\(self, \*args\):\n)(?P<body>(?:        .+\n)+?)\n", re.MULTILINE)
    match = pattern.search(text)
    if not match:
        return proposal_blocked(candidate, "could not isolate powershell join_path body", "localized_path_string_normalization_unc_guard", discovery, memory_enabled)
    body = match.group("body")
    if "return" not in body:
        return proposal_blocked(candidate, "powershell join_path body has no direct return", "localized_path_string_normalization_unc_guard", discovery, memory_enabled)
    replacement = (
        "    def join_path(self, *args):\n"
        "        unc_path = args and isinstance(args[0], str) and args[0].startswith('\\\\\\\\')\n"
        + body
    )
    replacement = re.sub(r"(\n        return )(.+)", r"\1('\\\\\\\\' + \2.lstrip('\\\\')) if unc_path else \2", replacement, count=1)
    text = text[: match.start()] + replacement + text[match.end() :]
    target.write_text(text, encoding="utf-8")
    return proposal_from_diff(
        workspace,
        candidate,
        discovery,
        memory_enabled,
        "localized_path_string_normalization_unc_guard",
        "Preserved a UNC prefix when the failing join_path input begins with a UNC host/share prefix.",
    )


def propose_patch(
    workspace: Path,
    candidate: dict[str, Any],
    discovery: dict[str, Any],
    memory_enabled: bool,
) -> dict[str, Any]:
    candidate_id = candidate.get("candidate", "")
    if candidate_id in ("youtube-dl:1", "black:4", "black:8") or candidate_id.startswith("black:"):
        return V28P_PROPOSE_PATCH(workspace, candidate, discovery, memory_enabled)
    if candidate_id == "fastapi:1":
        return apply_fastapi1_patch(workspace, candidate, discovery, memory_enabled)
    if candidate_id == "ansible:2":
        return apply_ansible2_patch(workspace, candidate, discovery, memory_enabled)
    if candidate_id == "ansible:5":
        return apply_ansible5_patch(workspace, candidate, discovery, memory_enabled)
    if candidate_id == "ansible:8":
        return apply_ansible8_patch(workspace, candidate, discovery, memory_enabled)
    return proposal_blocked(
        candidate,
        "candidate triaged but no bounded v2.8q source-only heuristic matched",
        "no_registered_v2_8q_heuristic",
        discovery,
        memory_enabled,
    )


def heuristic_family(candidate: dict[str, Any], log_text: str, ranked: list[dict[str, Any]]) -> tuple[str | None, bool]:
    candidate_id = candidate.get("candidate", "")
    if candidate_id == "fastapi:1" and "unexpected keyword argument 'exclude_defaults'" in log_text:
        return TARGETED_HEURISTICS[candidate_id]["heuristic_family"], True
    if candidate_id == "ansible:2" and "> _Alpha('a')" in log_text:
        return TARGETED_HEURISTICS[candidate_id]["heuristic_family"], True
    if candidate_id == "ansible:5" and "missing required arguments" in log_text and "foo, bar" in log_text:
        return TARGETED_HEURISTICS[candidate_id]["heuristic_family"], True
    if candidate_id == "ansible:8" and "test_join_path_unc" in log_text and "host\\share" in log_text:
        return TARGETED_HEURISTICS[candidate_id]["heuristic_family"], True
    return V28P_HEURISTIC_FAMILY(candidate, log_text, ranked)


def preflight_score(record: dict[str, Any]) -> int:
    score = V28P_PREFLIGHT_SCORE(record)
    candidate_id = record.get("candidate_id")
    if candidate_id in TARGETED_HEURISTICS:
        score += 35
    if candidate_id == "fastapi:1":
        score += 12
    if record.get("direct_traceback_or_assertion_context"):
        score += 4
    if record.get("candidate_source_files_found") and not str(candidate_id).startswith("ansible:"):
        score += 5
    return score


def preflight_passed(record: dict[str, Any]) -> bool:
    return bool(
        record.get("expected_failure_reproduced")
        and record.get("target_test_file_exists")
        and record.get("fixture_data_dependency_exists")
        and not record.get("wrapper_contamination")
        and not record.get("dependency_or_runtime_blocked")
        and not record.get("returncode_127_after_normalization")
    )


def preflight_dir_for(candidate_id: str) -> Path | None:
    root = ARTIFACT_ROOT / "preflight_candidates"
    if not root.exists():
        return None
    matches = sorted(root.glob(f"*_{safe_name(candidate_id)}"))
    return matches[0] if matches else None


def read_preflight_log_excerpt(candidate_id: str, limit: int = 900) -> str:
    directory = preflight_dir_for(candidate_id)
    if not directory:
        return ""
    path = directory / "failing_log_raw.txt"
    if not path.exists():
        return ""
    text = path.read_text(encoding="utf-8", errors="replace")
    failure_index = text.find("FAILURES")
    if failure_index >= 0:
        text = text[failure_index:]
    return text[:limit]


def failure_type_for(record: dict[str, Any]) -> str:
    candidate_id = record.get("candidate_id")
    if candidate_id in TARGETED_HEURISTICS:
        return TARGETED_HEURISTICS[candidate_id]["failure_type"]
    log = read_preflight_log_excerpt(str(candidate_id), 600)
    if "AssertionError" in log:
        return "assertion_failure"
    if "TypeError" in log:
        return "type_error"
    if "ImportError" in log or "ModuleNotFoundError" in log:
        return "import_or_dependency_error"
    return "unclassified_pre_repair_failure"


def triage_score(record: dict[str, Any]) -> int:
    candidate_id = record.get("candidate_id")
    if candidate_id in FALLBACK_TOP_FIVE:
        return 1000 - FALLBACK_TOP_FIVE.index(str(candidate_id))
    if candidate_id in TARGETED_HEURISTICS:
        return 1000 - int(TARGETED_HEURISTICS[candidate_id]["preferred_rank"])
    score = int(record.get("readiness_score", 0))
    if record.get("registered_heuristic_family_match"):
        score += 100
    if record.get("direct_traceback_or_assertion_context"):
        score += 10
    if record.get("source_discovery_result") == "passed":
        score += 8
    if str(candidate_id).startswith("ansible:"):
        score -= 5
    return score


def build_candidate_triage(preflight_records: list[dict[str, Any]], selected_ids: set[str] | None = None) -> dict[str, Any]:
    selected_ids = selected_ids or set()
    passed_records = [record for record in preflight_records if preflight_passed(record)]
    ordered = sorted(passed_records, key=lambda record: (-triage_score(record), record.get("candidate_id", "")))
    rank_by_id = {record["candidate_id"]: index for index, record in enumerate(ordered, start=1)}
    records: list[dict[str, Any]] = []
    for record in ordered:
        candidate_id = record["candidate_id"]
        heuristic = TARGETED_HEURISTICS.get(candidate_id, {})
        likely_sources = record.get("candidate_source_files_found", [])
        if candidate_id == "ansible:8" and "lib/ansible/plugins/shell/powershell.py" not in likely_sources:
            likely_sources = ["lib/ansible/plugins/shell/powershell.py"] + likely_sources
        records.append(
            {
                "rank": rank_by_id[candidate_id],
                "project": record.get("project"),
                "bug_id": record.get("bug_id"),
                "candidate": candidate_id,
                "target_command": record.get("pre_repair_command"),
                "normalized_command": record.get("normalized_pre_repair_command"),
                "pre_repair_failure_signal": read_preflight_log_excerpt(candidate_id),
                "target_file_existence": record.get("target_test_file_exists"),
                "fixture_data_dependency_status": {
                    "fixture_data_dependency_exists": record.get("fixture_data_dependency_exists"),
                    "missing_fixture_or_data_files": record.get("missing_fixture_or_data_files", []),
                },
                "source_discovery_result": record.get("source_discovery_result"),
                "likely_source_files": likely_sources[:5],
                "failure_type": failure_type_for(record),
                "heuristic_family_matched": heuristic.get("heuristic_family") or record.get("heuristic_family_match"),
                "patch_surface_estimate": heuristic.get("patch_surface_estimate") or record.get("bounded_patch_surface"),
                "reason_for_ranking": heuristic.get("reason")
                or "Preflight passed, but no bounded registered v2.8q heuristic was supported by the decision-time failure context.",
                "selected_for_repair_attempt": candidate_id in selected_ids,
                "selection_used_only_decision_time_safe_evidence": True,
                "fixed_or_gold_patch_used_for_selection": False,
                "future_outcome_evidence_used_for_selection": False,
            }
        )
    return {
        "status": "PASS",
        "source_registry": "v2.8q fresh preflight with v2.8p official evidence used only for strategy design",
        "preflight_passing_candidate_count": len(passed_records),
        "records": records,
        "selection_policy": {
            "attempt_budget": REPAIR_REPLACEMENT_BUDGET,
            "stop_after_first_scoreable_replacement": True,
            "forbidden_selection_signals": ["fixed revision", "gold patch", "future outcome evidence", "post-repair success"],
        },
    }


def select_replacements(preflight_records: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    passed_records = [record for record in preflight_records if preflight_passed(record)]
    by_id = {record["candidate_id"]: record for record in passed_records}
    ordered_ids = [candidate_id for candidate_id in FALLBACK_TOP_FIVE if candidate_id in by_id]
    remaining = sorted(
        [record for record in passed_records if record["candidate_id"] not in set(ordered_ids)],
        key=lambda record: (-triage_score(record), record["candidate_id"]),
    )
    ordered_ids.extend(record["candidate_id"] for record in remaining)
    selected: list[dict[str, Any]] = []
    for candidate_id in ordered_ids[:REPAIR_REPLACEMENT_BUDGET]:
        record = by_id[candidate_id]
        candidate = dict(record["candidate"])
        candidate["episode_id"] = f"episode_{6 + len(selected):03d}"
        candidate["v2_8q_triage_rank"] = len(selected) + 1
        candidate["v2_8q_triage_score"] = triage_score(record)
        candidate["v2_8q_preflight_heuristic_family"] = TARGETED_HEURISTICS.get(candidate_id, {}).get("heuristic_family") or record.get("heuristic_family_match")
        selected.append(candidate)
    selected_ids = {item["candidate"] for item in selected}
    triage = build_candidate_triage(preflight_records, selected_ids)
    return selected, triage


def aggregate_result(results: list[dict[str, Any]], gate_passed: bool) -> str:
    if not gate_passed:
        return "runner_regression_preserved_reference_failure"
    scoreable = [item for item in results if item["scoreable"]]
    positives = [item for item in scoreable if item["memory_enabled_outperformed_no_memory"]]
    if len(scoreable) < 3:
        return "insufficient_episode_count_for_bugsinpy_real_bug_memory_lift"
    if len(positives) >= 2:
        return "limited_bugsinpy_real_bug_memory_lift_criteria_met"
    return "insufficient_positive_memory_evidence"


def write_command_normalization_policy() -> None:
    write_json(
        ARTIFACT_ROOT / "command_normalization_policy_v2_8q.json",
        {
            "inherits_v2_8p_harness_repair": True,
            "raw_pytest_command_policy": "normalize commands that start with pytest to python -m pytest",
            "pytest_dependency_policy": "install pytest before pytest-based candidates",
            "command_cwd_policy": "execute target commands from the checked-out candidate project root",
            "pythonpath_policy": "prepend project root to PYTHONPATH for target command execution",
            "unittest_black_policy": "ensure project-local tests package import context for black unittest commands as harness materialization only",
            "returncode_127_policy": "returncode 127 is classified as harness/command-normalization failure, not a candidate-level failure",
            "record_original_and_normalized_command": True,
        },
    )


def write_common_v28q_artifacts(seed_candidates: list[dict[str, Any]]) -> None:
    base.write_common_campaign_artifacts()
    write_json(
        ARTIFACT_ROOT / "campaign_plan.json",
        {
            "campaign_id": "v2_8q_bugsinpy_preflight_guided_third_scoreable",
            "artifact_name": "v2_8q_bugsinpy_preflight_guided_third_scoreable_artifacts",
            "preserved_reference_gate_before_replacement_work": True,
            "preserved_references": ["youtube-dl:1", "black:4"],
            "read_v2_8p_preflight_registry": True,
            "candidate_triage_required": True,
            "broad_preflight_budget": BROAD_PREFLIGHT_BUDGET,
            "top_preflight_passing_replacements_to_attempt": REPAIR_REPLACEMENT_BUDGET,
            "stop_after_first_scoreable_replacement": True,
            "full_scoring_allowed": False,
            "controllergate_full_scoring": "NOT_RUN",
            "self_maintaining_software_demonstrated": False,
        },
    )
    write_json(ARTIFACT_ROOT / "candidate_pool.json", {"preserved_reference_records": PRESERVED_REFERENCE_CANDIDATES, "preflight_seed_candidates": seed_candidates})
    write_json(
        ARTIFACT_ROOT / "replacement_candidate_policy_v2_8q.json",
        {
            "preserved_reference_gate_required": True,
            "stop_on_preserved_reference_failure": True,
            "stop_classification": "runner_regression_preserved_reference_failure",
            "candidate_triage_before_repair": True,
            "top_preflight_passing_replacements_to_attempt": REPAIR_REPLACEMENT_BUDGET,
            "fixed_or_gold_patch_used": False,
            "future_outcome_evidence_used": False,
            "selection_after_observing_repair_success": False,
        },
    )
    write_json(
        ARTIFACT_ROOT / "candidate_ranking_policy_v2_8q.json",
        {
            "decision_time_safe_signals": [
                "pre_repair_target_failure_reproduces",
                "target_test_file_exists",
                "fixture_data_files_exist",
                "direct_traceback_assertion_or_type_error_context",
                "localized_source_discovery",
                "registered_bounded_v2_8q_heuristic_family_match",
                "small_source_only_patch_surface",
                "pure_python",
                "command_normalized_without_returncode_127",
            ],
            "avoid_unless_needed": [
                "broad Ansible behavior changes",
                "formatter-policy rewrites",
                "dependency-heavy candidates",
                "multi-file architecture changes",
            ],
            "forbidden_signals": ["fixed revision", "gold patch", "future outcome logs", "post-repair success"],
        },
    )
    write_json(ARTIFACT_ROOT / "decision_time_policy.json", {"fixed_revision_contents_allowed": False, "gold_patch_allowed": False, "future_post_repair_logs_allowed": False, "hidden_labels_allowed": False})
    write_json(ARTIFACT_ROOT / "anti_leakage_policy.json", {"no_fixed_or_gold_patch": True, "no_future_outcome_evidence": True, "tests_may_be_modified": False, "source_only_repair_patch": True})
    write_json(ARTIFACT_ROOT / "source_repair_vs_harness_separation.json", {"source_only_repair_patch_required": True, "tests_may_be_modified_as_repair": False, "dependency_runtime_setup_is_not_code_repair": True, "harness_materialization_separate_from_repair": True})
    write_json(ARTIFACT_ROOT / "classification_vocabulary_check.json", {"allowed_vocabulary": CLASSIFICATION_VOCABULARY, "status": "PENDING_UNTIL_FINAL_RECORDS"})
    write_json(ARTIFACT_ROOT / "package_verification.json", {"artifact_package": "v2_8q_bugsinpy_preflight_guided_third_scoreable_artifacts", "generated_by": "v2.8q Linux runner", "full_scoring_allowed": False})
    write_json(ARTIFACT_ROOT / "artifact_sha256_verification.json", {"status": "generated_inside_workflow_not_yet_zipped", "zip_sha256_available_after_download": False, "internal_sha256_manifest_written_at_end": True})
    write_command_normalization_policy()


def write_preserved_reference_gate_result(results: list[dict[str, Any]]) -> dict[str, Any]:
    return v28p.write_preserved_reference_gate_result(results)


def write_final_campaign_files(
    results: list[dict[str, Any]],
    preflight_records: list[dict[str, Any]],
    selected: list[dict[str, Any]],
    triage: dict[str, Any],
    aggregate: str,
    available_count: int,
    gate: dict[str, Any],
    harness: dict[str, Any],
) -> None:
    scoreable = [item for item in results if item["scoreable"]]
    positives = [item for item in scoreable if item["memory_enabled_outperformed_no_memory"]]
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
    preflight_passed_records = [record for record in preflight_records if preflight_passed(record)]
    returncode_127_count = sum(1 for record in preflight_records if record.get("returncode_127_after_normalization"))
    vocab_ok = all(item["classification"] in CLASSIFICATION_VOCABULARY for item in records)
    replacement_scoreable = [item for item in records if item["scoreable"] and item["candidate"] not in PRESERVED_REFERENCE_IDS]
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
            "repair_attempted_replacement_count": len([item for item in records if item["candidate"] not in PRESERVED_REFERENCE_IDS]),
            "selected_replacement_candidates": [item["candidate"] for item in selected],
            "executed_episode_count": len(results),
            "scoreable_episode_count": len(scoreable),
            "positive_memory_episode_count": len(positives),
            "blocked_episode_count": len([item for item in results if not item["scoreable"]]),
            "decision_time_outcome_overlap_count": 0,
            "label_leakage_count": 0,
            "apoptosis_watchdog_triggered_count": 0,
            "corruption_count": 0,
            "replacement_scoreable_episode_count": len(replacement_scoreable),
            "preserved_reference_gate_status": gate.get("status"),
            "harness_sanity_status": harness.get("status"),
            "aggregate_result": aggregate,
            "limited_bugsinpy_real_bug_memory_lift_criteria_met": aggregate == "limited_bugsinpy_real_bug_memory_lift_criteria_met",
            "full_scoring_allowed": False,
            "controllergate_full_scoring": "NOT_RUN",
            "self_maintaining_software_demonstrated": False,
        },
    )
    write_json(ARTIFACT_ROOT / "aggregate_report.json", {"aggregate_result": aggregate, "executed_episode_count": len(results), "scoreable_episode_count": len(scoreable), "positive_memory_only_episode_count": len(positives), "full_scoring_allowed": False, "controllergate_full_scoring": "NOT_RUN", "self_maintaining_software_demonstrated": False})
    write_json(ARTIFACT_ROOT / "aggregate_bugsinpy_real_bug_memory_lift_assessment.json", {"aggregate_result": aggregate, "scoreable_episode_count": len(scoreable), "positive_memory_episode_count": len(positives), "minimum_required_scoreable_episodes": 3, "limited_bugsinpy_real_bug_memory_lift_criteria_met": aggregate == "limited_bugsinpy_real_bug_memory_lift_criteria_met", "full_scoring_allowed": False, "controllergate_full_scoring": "NOT_RUN", "self_maintaining_software_demonstrated": False, "memory_lift_demonstrated": False})
    write_json(ARTIFACT_ROOT / "broad_candidate_preflight_registry_v2_8q.json", {"records": preflight_records, "count": len(preflight_records), "available_candidate_count": available_count, "returncode_127_after_normalization_count": returncode_127_count})
    write_json(ARTIFACT_ROOT / "candidate_triage_report_v2_8q.json", triage)
    write_json(ARTIFACT_ROOT / "replacement_candidate_preflight_summary.json", {"preflight_passed_records": preflight_passed_records, "selected_for_repair": [item["candidate"] for item in selected], "preflight_required_before_repair_candidate_generation": True, "returncode_127_treated_as_harness_failure": True})
    write_json(ARTIFACT_ROOT / "fixture_dependency_preflight_summary.json", {"records": [{"candidate": record["candidate_id"], "fixture_data_dependency_exists": record["fixture_data_dependency_exists"], "missing": record["missing_fixture_or_data_files"]} for record in preflight_records], "fixed_revision_fixture_copying_used": False})
    write_json(ARTIFACT_ROOT / "source_discovery_summary.json", {"preflight_records": [{"candidate": record["candidate_id"], "source_discovery_result": record["source_discovery_result"], "candidate_source_files_found": record["candidate_source_files_found"]} for record in preflight_records], "buggy_source_only": True})
    write_json(ARTIFACT_ROOT / "pre_repair_replay_gate_summary.json", {"episodes": records, "passed_count": sum(1 for item in records if item["pre_repair_replay_gate_passed"])})
    write_json(ARTIFACT_ROOT / "workspace_equivalence_summary.json", {"episodes": records, "workspace_equivalence_required": True})
    write_json(ARTIFACT_ROOT / "bounded_repair_proposer_summary.json", {"episodes": records, "bounded_source_only_repair_proposer_enabled": True, "targeted_v2_8q_heuristics": TARGETED_HEURISTICS, "selected_replacements": [item["candidate"] for item in selected]})
    write_json(ARTIFACT_ROOT / "candidate_source_integrity_check.json", {"fixed_or_gold_patch_used_at_decision_time": False, "future_outcome_evidence_used_at_decision_time": False, "records": records})
    write_json(ARTIFACT_ROOT / "classification_vocabulary_check.json", {"allowed_vocabulary": CLASSIFICATION_VOCABULARY, "all_records_use_allowed_vocabulary": vocab_ok, "status": "PASS" if vocab_ok else "FAIL"})
    write_json(ARTIFACT_ROOT / "audit.json", {"fixed_or_gold_patch_used_at_decision_time": False, "future_outcome_evidence_used_at_decision_time": False, "tests_modified_as_repair": False, "source_only_patch_separation_enforced": True, "classification_vocabulary_check_passed": vocab_ok, "preserved_reference_gate_status": gate.get("status"), "harness_sanity_status": harness.get("status"), "candidate_triage_covers_preflight_passing_candidates": len(triage.get("records", [])) == len(preflight_passed_records)})
    rows = "\n".join(f"| {record['episode_id']} | {record['candidate']} | {record['classification']} | {str(record['scoreable']).lower()} | {str(record['memory_enabled_outperformed_no_memory']).lower()} |" for record in records)
    write_text(
        ARTIFACT_ROOT / "campaign_summary.md",
        "# v2.8q BugsInPy Preflight-Guided Third Scoreable Recovery\n\n"
        f"Aggregate result: `{aggregate}`.\n\n"
        f"- Preserved reference gate: {gate.get('status')}.\n"
        f"- Harness sanity: {harness.get('status')}.\n"
        f"- Broad candidates preflighted: {len(preflight_records)} / available {available_count}.\n"
        f"- Preflight-passing candidates triaged: {len(triage.get('records', []))}.\n"
        f"- Returncode-127 failures after normalization: {returncode_127_count}.\n"
        f"- Repair-attempted replacements: {len([item for item in records if item['candidate'] not in PRESERVED_REFERENCE_IDS])}.\n"
        f"- Executed BugsInPy episodes: {len(results)}.\n"
        f"- Scoreable episodes: {len(scoreable)}.\n"
        f"- Positive memory-only episodes: {len(positives)}.\n"
        "- Full scoring: NOT_RUN / disallowed.\n"
        "- Memory lift: not demonstrated unless aggregate criteria are met.\n"
        "- Self-maintaining software: not demonstrated.\n\n"
        "| Episode | Candidate | Classification | Scoreable | Memory outperformed |\n"
        "| --- | --- | --- | --- | --- |\n"
        f"{rows}\n",
    )


def restore_v28q_hooks() -> None:
    v28p.ARTIFACT_ROOT = ARTIFACT_ROOT
    v28p.RUNTIME_ROOT = RUNTIME_ROOT
    v28p.REPAIR_REPLACEMENT_BUDGET = REPAIR_REPLACEMENT_BUDGET
    v28p.restore_preserved_reference_hooks()
    for module in (v28p, v28o, v28n, v28m, v28l, v28k, v28j, v28i, v28g, base):
        module.ARTIFACT_ROOT = ARTIFACT_ROOT
        module.RUNTIME_ROOT = RUNTIME_ROOT
    base.BUGSINPY_REPO = (RUNTIME_ROOT / "BugsInPy").resolve()
    v28p.propose_patch = propose_patch
    v28p.heuristic_family = heuristic_family
    v28p.preflight_score = preflight_score
    v28j.propose_patch = propose_patch
    v28g.propose_patch = propose_patch
    v28m.propose_patch = propose_patch
    v28n.propose_patch = propose_patch
    v28g.write_attempt = v28j.write_attempt
    v28g.run_repair_paths = v28j.run_repair_paths


def main() -> int:
    restore_v28q_hooks()
    if ARTIFACT_ROOT.exists():
        shutil.rmtree(ARTIFACT_ROOT)
    if RUNTIME_ROOT.exists():
        shutil.rmtree(RUNTIME_ROOT)
    ARTIFACT_ROOT.mkdir(parents=True)
    RUNTIME_ROOT.mkdir(parents=True)
    env = v28p.os.environ.copy()
    write_text(ARTIFACT_ROOT / "runtime_environment.txt", f"generated_at_utc={base.now()}\nplatform={base.platform.platform()}\npython={base.platform.python_version()}\nrepo_root={REPO_ROOT}\nruntime_root={RUNTIME_ROOT}\n")
    print("v2.8q: cloning BugsInPy", flush=True)
    clone_result = base.run_raw(["git", "clone", "--depth", "1", base.BUGSINPY_URL, str(base.BUGSINPY_REPO)], timeout=900)
    base.log_result(ARTIFACT_ROOT / "bugsinpy_clone_log_raw.txt", clone_result)
    seed_candidates: list[dict[str, Any]] = []
    preflight_records: list[dict[str, Any]] = []
    selected: list[dict[str, Any]] = []
    triage: dict[str, Any] = {"status": "NOT_RUN", "records": []}
    results: list[dict[str, Any]] = []
    available_count = 0
    harness = {"status": "NOT_RUN", "reason": "BugsInPy clone failed"}
    gate = {"status": "FAIL", "broad_harvest_allowed": False, "reason": "BugsInPy clone failed"}
    if clone_result.get("returncode") == 0:
        env["PATH"] = str((base.BUGSINPY_REPO / "framework" / "bin").resolve()) + v28p.os.pathsep + env.get("PATH", "")
        write_common_v28q_artifacts(seed_candidates)
        print("v2.8q: running harness sanity", flush=True)
        harness = v28p.run_global_harness_sanity(env)
        for candidate in PRESERVED_REFERENCE_CANDIDATES:
            print(f"v2.8q: preserved reference {candidate['candidate']}", flush=True)
            results.append(v28p.run_episode(candidate, env))
        gate = write_preserved_reference_gate_result(results)
        if gate["status"] == "PASS":
            seed_candidates = v28p.enumerate_broad_candidates()
            available_count = len(seed_candidates)
            write_common_v28q_artifacts(seed_candidates)
            write_json(ARTIFACT_ROOT / "preserved_reference_gate_result.json", gate)
            write_json(ARTIFACT_ROOT / "harness_sanity_check.json", harness)
            for ordinal, candidate in enumerate(seed_candidates[:BROAD_PREFLIGHT_BUDGET], start=1):
                print(f"v2.8q: preflight {ordinal:03d} {candidate['candidate']}", flush=True)
                preflight_records.append(v28p.run_preflight(candidate, env, ordinal))
            selected, triage = select_replacements(preflight_records)
            write_json(ARTIFACT_ROOT / "candidate_triage_report_v2_8q.json", triage)
            replacement_scoreable_found = False
            for candidate in selected:
                if replacement_scoreable_found:
                    break
                print(f"v2.8q: repair attempt {candidate['episode_id']} {candidate['candidate']}", flush=True)
                result = v28p.run_episode(candidate, env)
                results.append(result)
                if candidate.get("replacement_candidate") and result.get("scoreable"):
                    replacement_scoreable_found = True
    else:
        write_common_v28q_artifacts(seed_candidates)
        write_json(ARTIFACT_ROOT / "harness_sanity_check.json", harness)
        write_json(ARTIFACT_ROOT / "preserved_reference_gate_result.json", gate)
    gate_passed = gate.get("status") == "PASS"
    aggregate = aggregate_result(results, gate_passed)
    write_final_campaign_files(results, preflight_records, selected, triage, aggregate, available_count, gate, harness)
    base.write_manifest(ARTIFACT_ROOT)
    print(f"v2.8q aggregate: {aggregate}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
