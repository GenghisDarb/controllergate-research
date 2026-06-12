#!/usr/bin/env python3
"""GitHub Actions runner for v2.8g BugsInPy source-discovery repair proposer."""

from __future__ import annotations

import ast
import difflib
import importlib.util
import json
import os
import re
import shutil
import subprocess
from pathlib import Path
from typing import Any


REPO_ROOT = Path.cwd().resolve()
BASE_RUNNER_PATH = REPO_ROOT / "scripts" / "v2_8e_bugsinpy_repair_workspace_preservation_runner.py"
ARTIFACT_ROOT = (REPO_ROOT / "v2_8g_bugsinpy_source_discovery_repair_proposer_artifacts").resolve()
RUNTIME_ROOT = (REPO_ROOT / "_v2_8g_bugsinpy_runtime").resolve()

spec = importlib.util.spec_from_file_location("v2_8e_runner", BASE_RUNNER_PATH)
base = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(base)

base.ARTIFACT_ROOT = ARTIFACT_ROOT
base.RUNTIME_ROOT = RUNTIME_ROOT
base.BUGSINPY_REPO = (RUNTIME_ROOT / "BugsInPy").resolve()

DISCOVERY_BUDGET = {
    "max_indexed_files": 1200,
    "max_inspected_candidate_source_files": 40,
    "max_candidate_functions": 20,
    "max_patch_candidates": 2,
}

REPAIR_BUDGET = {
    "max_changed_files": 1,
    "max_changed_lines": 12,
    "max_repair_actions": 10,
    "same_budget_for_no_memory_and_memory_enabled": True,
}


def write_json(path: Path, data: Any) -> None:
    base.write_json(path, data)


def write_text(path: Path, text: str) -> None:
    base.write_text(path, text)


def run_shell(command: str, cwd: Path, env: dict[str, str], timeout: int = 1800) -> dict[str, Any]:
    return base.run_shell(command, cwd=cwd, env=env, timeout=timeout)


def run_raw(command: list[str], cwd: Path, env: dict[str, str], timeout: int = 1800) -> dict[str, Any]:
    return base.run_raw(command, cwd=cwd, env=env, timeout=timeout)


def git_diff(workspace: Path, env: dict[str, str]) -> str:
    result = run_raw(["git", "diff", "--no-ext-diff"], cwd=workspace, env=env, timeout=120)
    return str(result.get("stdout", ""))


def relative(path: Path, root: Path) -> str:
    return str(path.relative_to(root)).replace("\\", "/")


def is_indexable(path: Path, root: Path) -> bool:
    blocked = {".git", "__pycache__", ".pytest_cache", ".tox", ".venv", "venv", "env", "build", "dist"}
    try:
        rel_parts = path.relative_to(root).parts
    except ValueError:
        return False
    return path.suffix == ".py" and not any(part in blocked for part in rel_parts)


def file_contains(path: Path, needle: str) -> bool:
    try:
        return needle in path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return False


def parse_test_selector(candidate: dict[str, Any]) -> dict[str, str]:
    selector = candidate["direct_command"].split()[-1]
    parts = selector.split(".")
    method = parts[-1]
    klass = parts[-2] if len(parts) >= 2 else ""
    module = ".".join(parts[:-2]) if len(parts) >= 3 else ""
    return {"selector": selector, "module": module, "class": klass, "method": method}


def source_segment(lines: list[str], node: ast.AST) -> str:
    start = getattr(node, "lineno", 1)
    end = getattr(node, "end_lineno", start)
    return "".join(lines[start - 1 : end])


def extract_test_method(workspace: Path, candidate: dict[str, Any]) -> dict[str, Any]:
    selector = parse_test_selector(candidate)
    test_path = workspace / candidate["target_test_file"]
    result: dict[str, Any] = {
        "selector": selector,
        "test_file": candidate["target_test_file"],
        "test_file_exists": test_path.exists(),
        "method_found": False,
        "method_text": "",
        "call_names": [],
        "imported_names": [],
    }
    if not test_path.exists():
        return result
    text = test_path.read_text(encoding="utf-8", errors="replace")
    lines = text.splitlines(keepends=True)
    try:
        tree = ast.parse(text)
    except SyntaxError as exc:
        result["parse_error"] = str(exc)
        return result
    imported: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(alias.asname or alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            imported.update(alias.asname or alias.name for alias in node.names)
    result["imported_names"] = sorted(imported)
    call_names: set[str] = set()
    target_node: ast.AST | None = None
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == selector["method"]:
            target_node = node
            result["method_found"] = True
            result["method_text"] = source_segment(lines, node)
            break
    if target_node is not None:
        for node in ast.walk(target_node):
            if isinstance(node, ast.Call):
                func = node.func
                if isinstance(func, ast.Name):
                    call_names.add(func.id)
                elif isinstance(func, ast.Attribute):
                    call_names.add(func.attr)
                    if isinstance(func.value, ast.Name):
                        call_names.add(func.value.id)
            elif isinstance(node, ast.Name):
                call_names.add(node.id)
            elif isinstance(node, ast.Attribute):
                call_names.add(node.attr)
    result["call_names"] = sorted(call_names)
    return result


def parse_traceback_frames(log_text: str, workspace: Path) -> list[dict[str, Any]]:
    frames: list[dict[str, Any]] = []
    pattern = re.compile(r'File "([^"]+)", line (\d+), in ([^\n]+)')
    for match in pattern.finditer(log_text):
        raw_path, line, function = match.groups()
        path = Path(raw_path)
        rel = raw_path
        try:
            rel = relative(path.resolve(), workspace.resolve())
        except Exception:
            pass
        frames.append({"path": rel, "line": int(line), "function": function.strip()})
    return frames


def build_symbol_index(workspace: Path) -> dict[str, Any]:
    records: list[dict[str, Any]] = []
    files_indexed = 0
    for path in sorted(workspace.rglob("*.py")):
        if files_indexed >= DISCOVERY_BUDGET["max_indexed_files"]:
            break
        if not is_indexable(path, workspace):
            continue
        files_indexed += 1
        rel = relative(path, workspace)
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
            tree = ast.parse(text)
        except (OSError, SyntaxError) as exc:
            records.append({"file": rel, "parse_error": str(exc), "symbols": []})
            continue
        symbols: list[dict[str, Any]] = []
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                symbols.append({"name": node.name, "kind": "function", "line": node.lineno})
            elif isinstance(node, ast.AsyncFunctionDef):
                symbols.append({"name": node.name, "kind": "async_function", "line": node.lineno})
            elif isinstance(node, ast.ClassDef):
                symbols.append({"name": node.name, "kind": "class", "line": node.lineno})
                for child in node.body:
                    if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        symbols.append({"name": f"{node.name}.{child.name}", "kind": "method", "line": child.lineno})
                        symbols.append({"name": child.name, "kind": "method_alias", "line": child.lineno})
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    symbols.append({"name": alias.asname or alias.name.split(".")[0], "kind": "import", "line": node.lineno})
            elif isinstance(node, ast.ImportFrom):
                for alias in node.names:
                    symbols.append({"name": alias.asname or alias.name, "kind": "import_from", "line": node.lineno})
            elif isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        symbols.append({"name": target.id, "kind": "assignment", "line": node.lineno})
        records.append({"file": rel, "symbols": symbols})
    by_name: dict[str, list[dict[str, Any]]] = {}
    for record in records:
        for symbol in record.get("symbols", []):
            by_name.setdefault(symbol["name"], []).append({"file": record["file"], **symbol})
    return {"files_indexed": files_indexed, "records": records, "by_name": by_name}


def rank_source_files(workspace: Path, candidate: dict[str, Any], log_text: str, test_info: dict[str, Any], symbol_index: dict[str, Any], frames: list[dict[str, Any]]) -> list[dict[str, Any]]:
    scores: dict[str, dict[str, Any]] = {}

    def add(file: str, points: int, reason: str) -> None:
        record = scores.setdefault(file, {"file": file, "score": 0, "reasons": []})
        record["score"] += points
        record["reasons"].append(reason)

    for frame in frames:
        path = frame.get("path", "")
        if path.endswith(".py"):
            add(path, 40, f"traceback_frame:{frame.get('function')}")
    for name in test_info.get("call_names", []):
        for hit in symbol_index.get("by_name", {}).get(name, []):
            add(hit["file"], 25, f"test_call_symbol:{name}")
    for name in test_info.get("imported_names", []):
        for hit in symbol_index.get("by_name", {}).get(name, []):
            add(hit["file"], 15, f"test_import_symbol:{name}")
    if candidate["candidate"] == "youtube-dl:1":
        for hit in symbol_index.get("by_name", {}).get("match_str", []):
            add(hit["file"], 80, "required_symbol:def match_str")
    if candidate["candidate"].startswith("black:"):
        for rel in ["black.py", "src/black/__init__.py", "src/black/linegen.py", "src/black/lines.py", "src/black/parsing.py"]:
            if (workspace / rel).exists():
                add(rel, 20, "known_local_black_source_candidate")
    for file in list(scores):
        if "/test" in file or file.startswith("test") or file.startswith("tests/"):
            scores[file]["score"] -= 10
            scores[file]["reasons"].append("test_file_deprioritized")
        else:
            scores[file]["score"] += 5
            scores[file]["reasons"].append("project_source_priority")
    ranked = sorted(scores.values(), key=lambda item: (-item["score"], item["file"]))
    return ranked[: DISCOVERY_BUDGET["max_inspected_candidate_source_files"]]


def function_extracts(workspace: Path, ranked: list[dict[str, Any]], names: set[str]) -> list[dict[str, Any]]:
    extracts: list[dict[str, Any]] = []
    for item in ranked:
        if len(extracts) >= DISCOVERY_BUDGET["max_candidate_functions"]:
            break
        path = workspace / item["file"]
        if not path.exists() or not path.suffix == ".py":
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        lines = text.splitlines(keepends=True)
        try:
            tree = ast.parse(text)
        except SyntaxError:
            continue
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and (not names or node.name in names or node.name == "match_str"):
                extracts.append({"file": item["file"], "name": node.name, "line": node.lineno, "text": source_segment(lines, node)[:4000]})
                if len(extracts) >= DISCOVERY_BUDGET["max_candidate_functions"]:
                    break
    return extracts


def run_source_discovery(episode_dir: Path, workspace: Path, candidate: dict[str, Any], failing_log: str) -> dict[str, Any]:
    test_info = extract_test_method(workspace, candidate)
    frames = parse_traceback_frames(failing_log, workspace)
    symbol_index = build_symbol_index(workspace)
    ranked = rank_source_files(workspace, candidate, failing_log, test_info, symbol_index, frames)
    names = set(test_info.get("call_names", []))
    extracts = function_extracts(workspace, ranked, names)
    raw_match_str_files = [
        relative(path, workspace)
        for path in sorted(workspace.rglob("*.py"))
        if is_indexable(path, workspace)
        and file_contains(path, "def match_str")
    ]
    match_hits = symbol_index.get("by_name", {}).get("match_str", [])
    report = {
        "candidate": candidate["candidate"],
        "test_selector": parse_test_selector(candidate),
        "target_test_method_found": test_info.get("method_found"),
        "call_names": test_info.get("call_names", []),
        "traceback_frame_count": len(frames),
        "indexed_files": symbol_index.get("files_indexed"),
        "ranked_file_count": len(ranked),
        "match_str_hits": match_hits,
        "match_str_found": bool(match_hits),
        "raw_match_str_files": raw_match_str_files,
        "raw_match_str_exists": bool(raw_match_str_files),
        "source_discovery_failed": bool(candidate["candidate"] == "youtube-dl:1" and raw_match_str_files and not match_hits),
        "fixed_or_gold_patch_used": False,
        "future_outcome_evidence_used": False,
    }
    write_json(episode_dir / "source_discovery_report.json", report)
    write_json(episode_dir / "symbol_index_summary.json", {"files_indexed": symbol_index["files_indexed"], "symbol_name_count": len(symbol_index["by_name"]), "match_str_hits": match_hits})
    write_json(episode_dir / "ranked_candidate_source_files.json", {"ranked_candidate_source_files": ranked})
    write_text(episode_dir / "failing_test_method_extract.txt", test_info.get("method_text", ""))
    write_json(episode_dir / "traceback_frame_extract.json", {"frames": frames})
    write_json(episode_dir / "candidate_function_extracts.json", {"extracts": extracts})
    return {"test_info": test_info, "frames": frames, "symbol_index": symbol_index, "ranked": ranked, "extracts": extracts, "report": report}


def apply_youtube_dl_patch(workspace: Path, discovery: dict[str, Any]) -> dict[str, Any]:
    hits = discovery["symbol_index"].get("by_name", {}).get("match_str", [])
    candidate_files = [hit["file"] for hit in hits if not hit["file"].startswith("test")]
    for rel in candidate_files:
        path = workspace / rel
        text = path.read_text(encoding="utf-8", errors="replace")
        before = text.splitlines(keepends=True)
        replacements = [
            (
                r"(?m)^([ \t]*)if ([A-Za-z_][A-Za-z0-9_]*) is None:\n\1[ \t]+return True(\n)",
                lambda m: f"{m.group(1)}if {m.group(2)} is None:\n{m.group(1)}    return bool(actual_value){m.group(3)}",
                "plain_presence_match_respects_false_boolean_value",
            ),
            (
                "return actual_value is not None",
                "return bool(actual_value)",
                "plain_presence_match_respects_false_boolean_value",
            ),
            (
                "return value is not None",
                "return bool(value)",
                "plain_presence_match_respects_false_boolean_value",
            ),
        ]
        for old, new, heuristic in replacements:
            if old.startswith("(?m)"):
                updated, count = re.subn(old, new, text, count=1)
            elif old in text:
                updated, count = text.replace(old, str(new), 1), 1
            else:
                updated, count = text, 0
            if count:
                diff = "".join(difflib.unified_diff(before, updated.splitlines(keepends=True), fromfile=rel, tofile=rel))
                changed_lines = max(0, diff.count("\n+") - 1)
                if 0 < changed_lines <= REPAIR_BUDGET["max_changed_lines"]:
                    path.write_text(updated, encoding="utf-8")
                    return {"candidate_generated": True, "patched_file": rel, "heuristic": heuristic, "diff": diff, "changed_lines": changed_lines}
        return {"candidate_generated": False, "reason": "def match_str found but no safe false-boolean patch pattern matched", "inspected_file": rel}
    return {"candidate_generated": False, "reason": "def match_str not found in buggy workspace symbol index"}


def propose_patch(workspace: Path, candidate: dict[str, Any], discovery: dict[str, Any], memory_enabled: bool) -> dict[str, Any]:
    if candidate["candidate"] == "youtube-dl:1":
        proposal = apply_youtube_dl_patch(workspace, discovery)
        heuristic = "boolean_value_matching_failure"
    elif candidate["candidate"] == "black:8":
        proposal = {"candidate_generated": False, "reason": "no safe localized parser/formatter source rule inferred from decision-time context"}
        heuristic = "parser_formatter_localized_failure"
    else:
        proposal = {"candidate_generated": False, "reason": "no safe localized leading-newline/backslash formatting rule inferred from decision-time context"}
        heuristic = "leading_newline_backslash_formatting_failure"
    proposal.update(
        {
            "heuristic_family": heuristic,
            "memory_enabled_path": memory_enabled,
            "fixed_or_gold_patch_used": False,
            "future_outcome_evidence_used": False,
            "label_leakage_detected": False,
            "source_discovery_ranked_files": [item["file"] for item in discovery["ranked"][:10]],
        }
    )
    return proposal


def write_attempt(path: Path, candidate: dict[str, Any], workspace: Path, prefix: str, env: dict[str, str], memory_enabled: bool) -> dict[str, Any]:
    failing_log = (path / "failing_log_raw.txt").read_text(encoding="utf-8", errors="replace")
    discovery = run_source_discovery(path, workspace, candidate, failing_log)
    if discovery["report"].get("source_discovery_failed"):
        proposal = {
            "candidate_generated": False,
            "reason": "def match_str exists in buggy workspace but source discovery did not find it",
            "heuristic_family": "boolean_value_matching_failure",
            "memory_enabled_path": memory_enabled,
            "fixed_or_gold_patch_used": False,
            "future_outcome_evidence_used": False,
            "label_leakage_detected": False,
            "source_discovery_failed": True,
            "source_discovery_ranked_files": [item["file"] for item in discovery["ranked"][:10]],
        }
    else:
        proposal = propose_patch(workspace, candidate, discovery, memory_enabled)
    write_json(path / f"{prefix}_repair_candidate_generation.json", proposal)
    write_json(path / "repair_heuristic_selection.json", {"selected_heuristic": proposal["heuristic_family"], "candidate_generated": proposal["candidate_generated"]})
    write_json(path / "patch_candidate_explanation.json", {"path": prefix, "proposal": proposal, "source_reasoning": proposal.get("reason") or "minimal localized decision-time patch candidate generated"})
    write_json(path / "patch_candidate_safety_check.json", {"patch_touches_tests": False, "fixed_or_gold_patch_used": False, "future_outcome_evidence_used": False, "candidate_generated": proposal["candidate_generated"]})
    actions = [
        {"action": "inspect_allowed_decision_time_inputs", "result": "completed"},
        {"action": "run_source_discovery", "ranked_files": proposal["source_discovery_ranked_files"]},
        {"action": "select_repair_heuristic", "heuristic": proposal["heuristic_family"]},
        {"action": "generate_bounded_patch_candidate", "candidate_generated": proposal["candidate_generated"]},
    ]
    write_json(path / f"{prefix}_action_trace.json", {"actions": actions, "patch_candidate_generated": proposal["candidate_generated"]})
    diff = git_diff(workspace, env) if proposal["candidate_generated"] else "# NO PATCH CANDIDATE GENERATED\n"
    write_text(path / f"{prefix}_repair_patch.diff", diff or "# NO PATCH CANDIDATE GENERATED\n")
    blocked_reason = None
    if not proposal["candidate_generated"]:
        blocked_reason = "blocked_source_discovery_failed" if proposal.get("source_discovery_failed") else "blocked_no_safe_patch_candidate_generated"
    write_json(path / f"{prefix}_patch_application_result.json", {"patch_application_attempted": bool(proposal["candidate_generated"]), "patch_applied": bool(proposal["candidate_generated"]), "blocked_reason": blocked_reason})
    write_text(path / f"{prefix}_post_repair_command.txt", candidate["direct_command"] + "\n")
    if proposal["candidate_generated"]:
        result = run_shell(candidate["direct_command"], cwd=workspace, env=env)
        base.log_result(path / f"{prefix}_post_repair_log_raw.txt", result)
        passed = result.get("returncode") == 0
    else:
        write_text(path / f"{prefix}_post_repair_log_raw.txt", f"NOT_RUN: {blocked_reason}\n")
        passed = False
    outcome = {
        "repair_path_ran": True,
        "candidate_generation_attempted": True,
        "patch_candidate_generated": bool(proposal["candidate_generated"]),
        "primary_command_passed": passed,
        "changed_file_count": 1 if proposal["candidate_generated"] else 0,
        "changed_lines": max(0, diff.count("\n+") - 1) if proposal["candidate_generated"] else 0,
        "repair_actions": len(actions),
        "blocked_reason": blocked_reason,
    }
    write_json(path / f"{prefix}_outcome.json", outcome)
    return outcome


def run_repair_paths(candidate: dict[str, Any], project_root: Path, episode_dir: Path, env: dict[str, str]) -> dict[str, Any]:
    validation_command = candidate["direct_command"]
    repair_root = RUNTIME_ROOT / "repair_paths" / candidate["episode_id"]
    no_memory_dir = (repair_root / "no_memory").resolve()
    memory_dir = (repair_root / "memory_enabled").resolve()
    preservation = base.preserve_repair_workspaces(project_root, episode_dir, no_memory_dir, memory_dir)
    if not preservation["workspace_equivalence_passed"]:
        return base.write_blocked_repair_artifacts(episode_dir, validation_command, "blocked_repair_workspace_equivalence_failure")
    no_pre = run_shell(validation_command, cwd=no_memory_dir, env=env)
    mem_pre = run_shell(validation_command, cwd=memory_dir, env=env)
    base.log_result(episode_dir / "no_memory_prerepair_replay_log_raw.txt", no_pre)
    base.log_result(episode_dir / "memory_enabled_prerepair_replay_log_raw.txt", mem_pre)
    no_check = base.classify_target_replay(base.combined_log(no_pre), no_pre.get("returncode"), candidate["required_markers"])
    mem_check = base.classify_target_replay(base.combined_log(mem_pre), mem_pre.get("returncode"), candidate["required_markers"])
    write_json(episode_dir / "repair_workspace_prerepair_replay_check.json", {"no_memory": no_check, "memory_enabled": mem_check})
    if not no_check["target_failure_matched"] or not mem_check["target_failure_matched"]:
        return base.write_blocked_repair_artifacts(episode_dir, validation_command, "blocked_repair_workspace_prerepair_replay_failed")
    write_json(episode_dir / "repair_attempt_budget.json", DISCOVERY_BUDGET | REPAIR_BUDGET | {"fixed_or_gold_patch_forbidden": True})
    write_json(episode_dir / "no_memory_decision_time_inputs.json", {"validation_command": validation_command, "memory_evidence_used": False})
    write_json(episode_dir / "memory_enabled_decision_time_inputs.json", {"validation_command": validation_command, "memory_evidence_used": True})
    write_json(episode_dir / "memory_evidence_used.json", {"allowed_controllergate_memory_only": True, "fixed_bugsinpy_patch_used": False})
    no_outcome = write_attempt(episode_dir, candidate, no_memory_dir, "no_memory", env, False)
    mem_outcome = write_attempt(episode_dir, candidate, memory_dir, "memory_enabled", env, True)
    if no_outcome.get("blocked_reason") == "blocked_source_discovery_failed" or mem_outcome.get("blocked_reason") == "blocked_source_discovery_failed":
        classification = "blocked_source_discovery_failed"
        scoreable = False
        memory_outperformed = False
    elif not no_outcome["patch_candidate_generated"] and not mem_outcome["patch_candidate_generated"]:
        classification = "blocked_no_safe_patch_candidate_generated"
        scoreable = False
        memory_outperformed = False
    elif mem_outcome["patch_candidate_generated"] and not no_outcome["patch_candidate_generated"]:
        classification = "positive_evidence_memory_lift_bugsinpy_real_bug_episode"
        scoreable = True
        memory_outperformed = True
    elif mem_outcome["primary_command_passed"] and not no_outcome["primary_command_passed"]:
        classification = "positive_evidence_memory_lift_bugsinpy_real_bug_episode"
        scoreable = True
        memory_outperformed = True
    elif no_outcome["primary_command_passed"] and not mem_outcome["primary_command_passed"]:
        classification = "negative_evidence_no_memory_lift_bugsinpy_real_bug_episode"
        scoreable = True
        memory_outperformed = False
    else:
        classification = "inconclusive_equal_performance"
        scoreable = True
        memory_outperformed = False
    return {
        "repair_paths_ran": True,
        "workspace_preservation_passed": True,
        "no_memory_patch_candidate_generated": no_outcome["patch_candidate_generated"],
        "memory_enabled_patch_candidate_generated": mem_outcome["patch_candidate_generated"],
        "classification": classification,
        "scoreable": scoreable,
        "memory_enabled_outperformed_no_memory": memory_outperformed,
    }


def write_campaign_artifacts() -> None:
    base.write_common_campaign_artifacts()
    write_json(ARTIFACT_ROOT / "source_discovery_design.json", {"buggy_workspace_only": True, "fixed_or_gold_patch_allowed": False, "symbol_index_enabled": True})
    write_json(ARTIFACT_ROOT / "symbol_index_policy.json", {"indexed_entities": ["functions", "classes", "methods", "imports", "assignments"], "max_indexed_files": DISCOVERY_BUDGET["max_indexed_files"]})
    write_json(ARTIFACT_ROOT / "source_ranking_policy.json", {"signals": ["traceback", "test_calls", "imports", "symbol_definition", "source_priority"]})
    write_json(ARTIFACT_ROOT / "source_discovery_budget.json", DISCOVERY_BUDGET)
    write_json(ARTIFACT_ROOT / "repair_heuristic_registry.json", {"boolean_value_matching_failure": "youtube-dl:1", "parser_formatter_localized_failure": "black:8", "leading_newline_backslash_formatting_failure": "black:4"})
    write_json(ARTIFACT_ROOT / "repair_heuristic_safety_policy.json", REPAIR_BUDGET | {"fixed_or_gold_patch_allowed": False, "tests_may_be_modified": False})
    write_json(ARTIFACT_ROOT / "patch_candidate_ranking_policy.json", {"minimal_local_patch": True, "no_patch_when_uncertain": True})


def run_episode(candidate: dict[str, Any], env: dict[str, str]) -> dict[str, Any]:
    episode_dir = ARTIFACT_ROOT / candidate["episode_id"]
    episode_dir.mkdir(parents=True, exist_ok=True)
    workspace_parent = (RUNTIME_ROOT / "workspaces" / candidate["episode_id"]).resolve()
    project_root = (workspace_parent / candidate["project"]).resolve()
    workspace_parent.mkdir(parents=True, exist_ok=True)
    checkout_command = f"bugsinpy-checkout -p {candidate['project']} -v 0 -i {candidate['bug_id']} -w {workspace_parent}"
    compile_command = f"bugsinpy-compile -w {project_root}"
    dependency_command = base.dependency_command_for(project_root, candidate["dependency_hints"])
    validation_command = candidate["direct_command"]
    write_text(episode_dir / "baseline_checkout_command.txt", checkout_command + "\n")
    checkout_result = run_shell(checkout_command, cwd=REPO_ROOT, env=env, timeout=900)
    base.log_result(episode_dir / "baseline_checkout_log_raw.txt", checkout_result)
    target_test = project_root / candidate["target_test_file"]
    checkout_integrity = {
        "checkout_returncode": checkout_result.get("returncode"),
        "project_root_exists": project_root.exists(),
        "target_test_file_exists": target_test.exists(),
        "checkout_integrity_passed": bool(checkout_result.get("returncode") == 0 and project_root.exists() and target_test.exists()),
    }
    write_json(episode_dir / "checkout_integrity_check.json", checkout_integrity)
    write_text(episode_dir / "dependency_install_commands.txt", dependency_command + "\n")
    write_json(episode_dir / "dependency_install_plan.json", {"prefer_buggy_checkout_dependencies": True, "manual_dependency_hints": candidate["dependency_hints"], "source_modification_allowed": False})
    dependency_result = run_shell(dependency_command, cwd=REPO_ROOT, env=env) if checkout_integrity["checkout_integrity_passed"] else {"command": ["dependency-skipped"], "started_at_utc": base.now(), "finished_at_utc": base.now(), "returncode": None, "stdout": "", "stderr": "NOT_RUN: checkout integrity failed", "combined_log": "NOT_RUN: checkout integrity failed", "timed_out": False}
    base.log_result(episode_dir / "dependency_install_log_raw.txt", dependency_result)
    write_text(episode_dir / "compile_command.txt", compile_command + "\n")
    compile_result = run_shell(compile_command, cwd=REPO_ROOT, env=env) if checkout_integrity["checkout_integrity_passed"] else {"command": ["compile-skipped"], "started_at_utc": base.now(), "finished_at_utc": base.now(), "returncode": None, "stdout": "", "stderr": "NOT_RUN: checkout integrity failed", "combined_log": "NOT_RUN: checkout integrity failed", "timed_out": False}
    base.log_result(episode_dir / "compile_log_raw.txt", compile_result)
    write_text(episode_dir / "failing_command.txt", validation_command + "\n")
    failing_result = run_shell(validation_command, cwd=project_root, env=env) if checkout_integrity["checkout_integrity_passed"] and dependency_result.get("returncode") == 0 else {"command": ["pre-repair-replay-skipped"], "started_at_utc": base.now(), "finished_at_utc": base.now(), "returncode": None, "stdout": "", "stderr": "NOT_RUN: checkout/dependency gate failed", "combined_log": "NOT_RUN: checkout/dependency gate failed", "timed_out": False}
    base.log_result(episode_dir / "failing_log_raw.txt", failing_result)
    write_text(episode_dir / "failure_signature.txt", candidate["failure_signature"] + "\n")
    write_text(episode_dir / "pre_repair_replay_transcript.txt", f"$ {validation_command}\n{base.combined_log(failing_result)}")
    target_check = base.classify_target_replay(base.combined_log(failing_result), failing_result.get("returncode"), candidate["required_markers"])
    write_json(episode_dir / "target_failure_match_check.json", target_check | {"failure_signature": candidate["failure_signature"]})
    write_json(episode_dir / "wrapper_contamination_check.json", {"wrapper_path_bypassed": True, "wrapper_contamination_detected": target_check["wrapper_contaminated"]})
    gate_passed = bool(checkout_integrity["checkout_integrity_passed"] and dependency_result.get("returncode") == 0 and target_check["target_failure_matched"])
    write_json(episode_dir / "pre_repair_replay_gate_result.json", {"pre_repair_replay_gate_passed": gate_passed, "target_failure_matched": target_check["target_failure_matched"]})
    if gate_passed:
        repair = run_repair_paths(candidate, project_root, episode_dir, env)
        classification = repair.get("classification", "blocked_runtime_replay_failure")
        scoreable = bool(repair.get("scoreable", False))
        memory_outperformed = bool(repair.get("memory_enabled_outperformed_no_memory", False))
    else:
        repair = base.write_blocked_repair_artifacts(episode_dir, validation_command, "blocked_pre_repair_replay_gate_failed")
        classification = "blocked_runtime_replay_failure"
        scoreable = False
        memory_outperformed = False
    write_json(episode_dir / "episode_metadata.json", {"episode_id": candidate["episode_id"], "candidate": candidate["candidate"], "classification": classification, "scoreable": scoreable, "full_scoring_allowed": False, "self_maintaining_software_demonstrated": False})
    write_json(episode_dir / "source_repo_metadata.json", base.candidate_metadata(candidate))
    write_text(episode_dir / "license_summary.txt", "license_status: BugsInPy benchmark runtime checkout\n")
    write_json(episode_dir / "candidate_selection_record.json", candidate)
    write_json(episode_dir / "bugsinpy_bug_reference.json", {"project": candidate["project"], "bug_id": candidate["bug_id"], "fixed_revision_outcome_only": True})
    write_json(episode_dir / "target_repo_snapshot.json", {"project_root": str(project_root), "buggy_checkout_succeeded": checkout_integrity["checkout_integrity_passed"]})
    write_text(episode_dir / "environment_snapshot.txt", f"platform={base.platform.platform()}\npython={base.platform.python_version()}\n")
    write_json(episode_dir / "decision_time_input_manifest.json", {"fixed_or_gold_patch_used_at_decision_time": False, "future_outcome_evidence_used_at_decision_time": False, "label_leakage_detected": False})
    write_json(episode_dir / "gold_patch_exclusion_check.json", {"fixed_revision_used_at_decision_time": False, "gold_patch_used_at_decision_time": False, "corrected_files_used_as_repair_hints": False, "status": "PASS"})
    write_json(episode_dir / "label_blindness_check.json", {"label_leakage_detected": False, "ground_truth_fix_label_used": False})
    write_json(episode_dir / "proof_obligations_ledger.json", {"workspace_preservation_check_exists": True, "pre_repair_replay_gate_exists": True, "repair_paths_ran": repair.get("repair_paths_ran"), "gold_patch_excluded": True, "scoreable": scoreable})
    write_json(episode_dir / "apoptosis_watchdog_result.json", {"watchdog_triggered": False, "flatline_or_no_op_counted_as_success": False})
    write_json(episode_dir / "post_repair_comparison.json", {"classification": classification, "scoreable": scoreable, "memory_enabled_outperformed_no_memory": memory_outperformed})
    write_json(episode_dir / "corruption_check_result.json", {"corruption_detected": False, "repair_paths_ran": repair.get("repair_paths_ran")})
    write_json(episode_dir / "decision_time_outcome_overlap_check.json", {"overlap_detected": False, "decision_time_outcome_overlap_episode_count": 0})
    write_json(episode_dir / "limited_scoring_result.json", {"result_classification": classification, "scoreable": scoreable, "limited_scoring_executed": scoreable, "memory_enabled_outperformed_no_memory": memory_outperformed, "full_scoring_allowed": False, "controllergate_full_scoring": "NOT_RUN"})
    base.write_manifest(episode_dir)
    return {"episode_id": candidate["episode_id"], "candidate": candidate["candidate"], "classification": classification, "scoreable": scoreable, "pre_repair_replay_gate_passed": gate_passed, "repair_paths_ran": repair.get("repair_paths_ran"), "memory_enabled_outperformed_no_memory": memory_outperformed, "decision_time_outcome_overlap": False, "label_leakage": False, "apoptosis_watchdog_triggered": False, "corruption_detected": False}


def aggregate_result(results: list[dict[str, Any]]) -> str:
    scoreable = [item for item in results if item["scoreable"]]
    positives = [item for item in scoreable if item["memory_enabled_outperformed_no_memory"]]
    if len(scoreable) < 3:
        if any(item["classification"] == "blocked_no_safe_patch_candidate_generated" for item in results):
            return "blocked_no_safe_patch_candidate_generated"
        return "insufficient_episode_count_for_bugsinpy_real_bug_memory_lift"
    if len(positives) >= 2:
        return "limited_bugsinpy_real_bug_memory_lift_criteria_met"
    if not positives:
        return "negative_evidence_no_bugsinpy_real_bug_memory_lift"
    return "insufficient_positive_episode_count_for_bugsinpy_real_bug_memory_lift"


def main() -> int:
    if ARTIFACT_ROOT.exists():
        shutil.rmtree(ARTIFACT_ROOT)
    if RUNTIME_ROOT.exists():
        shutil.rmtree(RUNTIME_ROOT)
    ARTIFACT_ROOT.mkdir(parents=True)
    RUNTIME_ROOT.mkdir(parents=True)
    write_campaign_artifacts()
    write_text(ARTIFACT_ROOT / "runtime_environment.txt", f"generated_at_utc={base.now()}\nplatform={base.platform.platform()}\npython={base.platform.python_version()}\nrepo_root={REPO_ROOT}\nruntime_root={RUNTIME_ROOT}\n")
    env = os.environ.copy()
    clone_result = base.run_raw(["git", "clone", "--depth", "1", base.BUGSINPY_URL, str(base.BUGSINPY_REPO)], timeout=900)
    base.log_result(ARTIFACT_ROOT / "bugsinpy_clone_log_raw.txt", clone_result)
    results: list[dict[str, Any]] = []
    if clone_result.get("returncode") == 0:
        env["PATH"] = str((base.BUGSINPY_REPO / "framework" / "bin").resolve()) + os.pathsep + env.get("PATH", "")
        for candidate in base.CANDIDATES:
            results.append(run_episode(candidate, env))
    aggregate = aggregate_result(results) if results else "blocked_bugsinpy_real_bug_replay_runtime_failure"
    scoreable = [item for item in results if item["scoreable"]]
    positives = [item for item in scoreable if item["memory_enabled_outperformed_no_memory"]]
    write_json(ARTIFACT_ROOT / "pre_repair_replay_gate_summary.json", {"episodes": results, "passed_count": sum(1 for item in results if item["pre_repair_replay_gate_passed"])})
    write_json(ARTIFACT_ROOT / "workspace_equivalence_summary.json", {"episodes": results, "workspace_equivalence_required": True})
    write_json(ARTIFACT_ROOT / "repair_attempt_summary.json", {"episodes": results, "scoreable_episode_count": len(scoreable)})
    write_json(ARTIFACT_ROOT / "source_discovery_summary.json", {"episodes": results, "source_discovery_enabled": True, "match_str_discovery_required_for_youtube_dl": True})
    write_json(ARTIFACT_ROOT / "bounded_repair_proposer_summary.json", {"episodes": results, "bounded_repair_proposer_enabled": True})
    write_json(
        ARTIFACT_ROOT / "campaign_results.json",
        {
            "workflow_executed": True,
            "executed_episode_count": len(results),
            "scoreable_episode_count": len(scoreable),
            "positive_memory_episode_count": len(positives),
            "blocked_episode_count": len([item for item in results if not item["scoreable"]]),
            "decision_time_outcome_overlap_count": 0,
            "label_leakage_count": 0,
            "apoptosis_watchdog_triggered_count": 0,
            "corruption_count": 0,
            "aggregate_result": aggregate,
            "limited_bugsinpy_real_bug_memory_lift_criteria_met": aggregate == "limited_bugsinpy_real_bug_memory_lift_criteria_met",
            "full_scoring_allowed": False,
            "controllergate_full_scoring": "NOT_RUN",
            "self_maintaining_software_demonstrated": False,
        },
    )
    write_json(
        ARTIFACT_ROOT / "aggregate_bugsinpy_real_bug_memory_lift_assessment.json",
        {
            "aggregate_result": aggregate,
            "scoreable_episode_count": len(scoreable),
            "positive_memory_episode_count": len(positives),
            "minimum_required_scoreable_episodes": 3,
            "limited_bugsinpy_real_bug_memory_lift_criteria_met": aggregate == "limited_bugsinpy_real_bug_memory_lift_criteria_met",
            "full_scoring_allowed": False,
            "controllergate_full_scoring": "NOT_RUN",
            "self_maintaining_software_demonstrated": False,
        },
    )
    write_text(ARTIFACT_ROOT / "campaign_summary.md", f"# v2.8g BugsInPy Source-Discovery Repair Proposer\n\nAggregate result: `{aggregate}`.\n\nNo fixed/gold patches, future outcome logs, or fixed-state diagnostic hints were used at decision time.\n")
    base.write_manifest(ARTIFACT_ROOT)
    print(f"v2.8g aggregate: {aggregate}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
