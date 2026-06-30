from __future__ import annotations

import re
from pathlib import Path
from typing import Any


DECLARED_TARGET_REPLAY_STATUSES = {
    "target_behavior_reached_and_failed",
    "target_passed_after_declared_precondition_resolution",
    "target_precondition_unresolved_after_declared_extras",
    "environment_dependency_failure_after_declared_extras",
    "ambiguous_runtime_path_after_declared_extras",
}

PRECONDITION_MARKERS = (
    "No module named 'black'",
    "No module named \"black\"",
    "Can't find the Black package",
    "create_formatter",
    "StopIteration",
    "EntryPoint",
)

ENVIRONMENT_FAILURE_MARKERS = (
    "ModuleNotFoundError",
    "ImportError",
    "DistributionNotFound",
    "pkg_resources.DistributionNotFound",
)

TARGET_BEHAVIOR_MARKERS = (
    "test_isort_respects_skip_glob",
    "skip_glob",
    "isort",
    "AssertionError",
)


def _canonical_package_name(value: str) -> str:
    name = re.split(r"[<>=!~;\\[]", value, maxsplit=1)[0].strip()
    return name.lower().replace("_", "-")


def declared_optional_group(metadata: dict[str, Any], group: str) -> bool:
    groups = metadata.get("optional_dependency_groups", [])
    return group in groups if isinstance(groups, list) else False


def dependency_group_specs(metadata: dict[str, Any], group: str) -> list[str]:
    groups = metadata.get("dependency_groups", {})
    if not isinstance(groups, dict):
        return []
    specs = groups.get(group, [])
    return [str(item) for item in specs] if isinstance(specs, list) else []


def optional_group_specs(metadata: dict[str, Any], group: str) -> list[str]:
    groups = metadata.get("optional_dependencies_by_group", {})
    if not isinstance(groups, dict):
        return []
    specs = groups.get(group, [])
    return [str(item) for item in specs] if isinstance(specs, list) else []


def declared_dependency_specs(metadata: dict[str, Any], package_names: list[str]) -> list[str]:
    wanted = {_canonical_package_name(name) for name in package_names}
    specs: list[str] = []
    for raw in metadata.get("declared_dependency_strings", []):
        if _canonical_package_name(str(raw)) in wanted:
            specs.append(str(raw))
    for group in ["dev", "test", "tests"]:
        for raw in dependency_group_specs(metadata, group):
            if _canonical_package_name(str(raw)) in wanted:
                specs.append(str(raw))
    seen: set[str] = set()
    unique: list[str] = []
    for spec in specs:
        if spec not in seen:
            unique.append(spec)
            seen.add(spec)
    return unique


def declared_extra_install_commands(python_executable: str | Path, extras: list[str]) -> list[list[str]]:
    python = str(python_executable)
    return [[python, "-m", "pip", "install", "-e", f".[{extra}]"] for extra in extras]


def declared_test_tool_install_command(python_executable: str | Path, specs: list[str]) -> list[str] | None:
    if not specs:
        return None
    return [str(python_executable), "-m", "pip", "install", *specs]


def classify_target_replay_after_declared_extras(returncode: int, output: str) -> dict[str, Any]:
    precondition_hits = [marker for marker in PRECONDITION_MARKERS if marker in output]
    environment_hits = [marker for marker in ENVIRONMENT_FAILURE_MARKERS if marker in output]
    target_hits = [marker for marker in TARGET_BEHAVIOR_MARKERS if marker in output]
    if returncode == 0:
        status = "target_passed_after_declared_precondition_resolution"
        target_behavior_reached = True
    elif precondition_hits:
        status = "target_precondition_unresolved_after_declared_extras"
        target_behavior_reached = False
    elif environment_hits and not target_hits:
        status = "environment_dependency_failure_after_declared_extras"
        target_behavior_reached = False
    elif {"test_isort_respects_skip_glob", "isort"}.issubset(set(target_hits)) or {"skip_glob", "isort"}.issubset(set(target_hits)):
        status = "target_behavior_reached_and_failed"
        target_behavior_reached = True
    else:
        status = "ambiguous_runtime_path_after_declared_extras"
        target_behavior_reached = False
    return {
        "status": status,
        "target_behavior_reached": target_behavior_reached,
        "target_passed_after_declared_precondition_resolution": status == "target_passed_after_declared_precondition_resolution",
        "target_failed_after_declared_precondition_resolution": status == "target_behavior_reached_and_failed",
        "precondition_markers_found": precondition_hits,
        "environment_markers_found": environment_hits,
        "target_behavior_markers_found": target_hits,
    }


def retirement_decision_after_declared_extras(
    *,
    declared_extras_attempted: bool,
    target_replay_status: str,
    repair_attempted: bool,
    target_validation_status: str,
    duplicate_replay_status: str,
) -> dict[str, Any]:
    if target_validation_status == "PASS" and duplicate_replay_status == "PASS":
        return {
            "retired": False,
            "completion_decision": "repair_success",
            "final_blocker": None,
            "declared_extras_exhausted": declared_extras_attempted,
        }
    if target_replay_status == "target_passed_after_declared_precondition_resolution":
        return {
            "retired": True,
            "completion_decision": "candidate_retired_precondition_only",
            "final_blocker": "target_passed_after_declared_precondition_resolution",
            "declared_extras_exhausted": declared_extras_attempted,
        }
    if target_replay_status == "target_behavior_reached_and_failed" and not repair_attempted:
        return {
            "retired": True,
            "completion_decision": "candidate_retired_fragment_generation_failed",
            "final_blocker": "fragment_generation_not_completed_after_target_reachability",
            "declared_extras_exhausted": declared_extras_attempted,
        }
    if repair_attempted:
        return {
            "retired": True,
            "completion_decision": "candidate_retired_validation_failed",
            "final_blocker": "target_validation_or_duplicate_replay_failed",
            "declared_extras_exhausted": declared_extras_attempted,
        }
    return {
        "retired": True,
        "completion_decision": "candidate_retired_precondition_unresolved",
        "final_blocker": target_replay_status,
        "declared_extras_exhausted": declared_extras_attempted,
    }
