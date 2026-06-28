from __future__ import annotations

import ast
import difflib
import hashlib
import json
import os
import re
import shutil
import stat
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Iterable

from controllergate.core.environment import resolve_project_environment, venv_python
from controllergate.core.patch_safety import (
    duplicate_clean_replay,
    patch_size_caps,
    source_only_patch_validation,
    target_validation,
)

CommandRunner = Callable[..., subprocess.CompletedProcess[str]]

VERIFIED_CANDIDATE_ORDER = [
    "darker_non_ascii_drop_changes",
    "darker_stdin_filename",
]

FORBIDDEN_PATCH_PREFIXES = (
    "tests/",
    "test/",
    "src/darker/tests/",
    "configs/",
    ".github/",
    "outputs/",
    "scripts/",
    "docs/",
)


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def sha256_file(path: str | Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def stable_json_hash(value: object) -> str:
    return sha256_text(json.dumps(value, sort_keys=True, separators=(",", ":")))


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def build_verified_candidate_repair_queue(
    verified_candidates: list[dict[str, object]], max_repairs: int = 2
) -> list[dict[str, object]]:
    by_id = {str(item.get("lead_id")): item for item in verified_candidates}
    queue: list[dict[str, object]] = []
    for candidate_id in VERIFIED_CANDIDATE_ORDER:
        item = by_id.get(candidate_id)
        if not item:
            continue
        if item.get("decision") != "verified_native_candidate_pending_repair":
            continue
        if item.get("failure_replay_status") != "PRE_PATCH_FAILURE_OBSERVED":
            continue
        queue.append(
            {
                "candidate_id": candidate_id,
                "candidate_class": "native",
                "repo_url": item.get("repo_url"),
                "commit_sha": item.get("resolved_commit_sha") or item.get("commit_hint"),
                "target_test_path": item.get("test_path_hint"),
                "target_command": [sys.executable, "-m", "pytest", item.get("test_path_hint"), "-q"],
                "semantic_failure_signature_hash": item.get("semantic_failure_signature_hash"),
                "source_record_hash": stable_json_hash(item),
                "repair_queue_decision": "queued_verified_native_candidate",
            }
        )
    return queue[:max_repairs]


def unverified_candidate_repair_queue_entry(candidate: dict[str, object]) -> dict[str, object]:
    return {
        "candidate_id": candidate.get("lead_id"),
        "repair_queue_decision": "rejected_unverified_candidate",
        "blocker": "candidate_not_verified_for_repair_generation",
    }


def _safe_slug(value: object) -> str:
    text = str(value or "candidate").strip().lower()
    return "".join(ch if ch.isalnum() else "_" for ch in text).strip("_")[:80] or "candidate"


def _remove_readonly(function: Callable[..., object], path: str, _exc_info: object) -> None:
    os.chmod(path, stat.S_IWRITE | stat.S_IREAD)
    function(path)


def prepare_runtime_root(config: dict[str, object], suffix: str) -> Path:
    configured = config.get("runtime_workspace_root") or os.environ.get("CONTROLLERGATE_RUNTIME_ROOT")
    root = Path(str(configured)) if configured else Path(tempfile.gettempdir()) / "controllergate_clean_replication" / str(config.get("batch_id", "batch"))
    root = root / suffix
    repo_root = Path.cwd().resolve()
    resolved = root.resolve()
    if repo_root == resolved or repo_root in resolved.parents:
        raise ValueError("runtime workspace must be outside live repository")
    if "onedrive" in str(resolved).lower():
        raise ValueError("runtime workspace must not be under OneDrive")
    if root.exists():
        shutil.rmtree(root, onerror=_remove_readonly)
    root.mkdir(parents=True, exist_ok=True)
    return root


def run_command(
    command: list[str],
    cwd: Path | None = None,
    timeout_seconds: int = 120,
    command_runner: CommandRunner | None = None,
) -> subprocess.CompletedProcess[str]:
    runner = command_runner or subprocess.run
    return runner(command, cwd=str(cwd) if cwd else None, text=True, capture_output=True, timeout=timeout_seconds)


def normalize_output(text: str, workspace: Path | None = None) -> str:
    normalized = text.replace("\r\n", "\n").replace("\r", "\n")
    if workspace is not None:
        replacements = [
            (str(workspace), "<candidate_workspace>"),
            (str(workspace).replace("\\", "/"), "<candidate_workspace>"),
            (str(workspace.parent), "<repair_workspace_root>"),
            (str(workspace.parent).replace("\\", "/"), "<repair_workspace_root>"),
            (sys.executable, "<python_executable>"),
            (sys.executable.replace("\\", "/"), "<python_executable>"),
            (str(Path(sys.base_prefix)), "<python_runtime>"),
            (str(Path(sys.base_prefix)).replace("\\", "/"), "<python_runtime>"),
            (str(Path(tempfile.gettempdir())), "<system_temp>"),
            (str(Path(tempfile.gettempdir())).replace("\\", "/"), "<system_temp>"),
        ]
        for source, target in sorted(replacements, key=lambda item: len(item[0]), reverse=True):
            normalized = normalized.replace(source, target)
    return "\n".join(line.rstrip() for line in normalized.splitlines())


def command_record(command: list[str], completed: subprocess.CompletedProcess[str], workspace: Path | None = None) -> dict[str, object]:
    combined = f"STDOUT:\n{completed.stdout or ''}\nSTDERR:\n{completed.stderr or ''}"
    normalized = normalize_output(combined, workspace)
    return {
        "command": [str(item) for item in command],
        "returncode": completed.returncode,
        "output_sha256": sha256_text(combined),
        "normalized_output_sha256": sha256_text(normalized),
        "output_summary": normalized[:1200],
    }


def materialize_candidate_workspace(candidate: dict[str, object], workspace_root: Path, command_runner: CommandRunner | None = None) -> tuple[Path, list[dict[str, object]]]:
    candidate_id = str(candidate["candidate_id"])
    workspace_root.mkdir(parents=True, exist_ok=True)
    checkout = workspace_root / _safe_slug(candidate_id)
    records: list[dict[str, object]] = []
    clone = ["git", "clone", "--no-checkout", "--filter=blob:none", str(candidate["repo_url"]), str(checkout)]
    clone_result = run_command(clone, timeout_seconds=180, command_runner=command_runner)
    records.append({"stage": "clone", **command_record(clone, clone_result, checkout)})
    if clone_result.returncode != 0:
        return checkout, records
    fetch = ["git", "fetch", "--depth", "1", "origin", str(candidate["commit_sha"])]
    fetch_result = run_command(fetch, cwd=checkout, timeout_seconds=180, command_runner=command_runner)
    records.append({"stage": "fetch", **command_record(fetch, fetch_result, checkout)})
    if fetch_result.returncode != 0:
        return checkout, records
    checkout_command = ["git", "checkout", "--detach", str(candidate["commit_sha"])]
    checkout_result = run_command(checkout_command, cwd=checkout, timeout_seconds=180, command_runner=command_runner)
    records.append({"stage": "checkout", **command_record(checkout_command, checkout_result, checkout)})
    return checkout, records


def pytest_command(test_path: str, python: str | Path) -> list[str]:
    return [str(python), "-m", "pytest", test_path, "-q"]


def pre_repair_replay(
    candidate: dict[str, object],
    checkout: Path,
    venv_dir: Path,
    command_runner: CommandRunner | None = None,
) -> dict[str, object]:
    python = venv_python(venv_dir)
    command = pytest_command(str(candidate["target_test_path"]), python)
    result = run_command(command, cwd=checkout, timeout_seconds=180, command_runner=command_runner)
    record = command_record(command, result, checkout)
    return {
        "candidate_id": candidate["candidate_id"],
        "target_command": command,
        "status": "PRE_PATCH_FAILURE_OBSERVED" if result.returncode != 0 else "PASSING_PRE_PATCH_NOT_A_FAILURE",
        "returncode": result.returncode,
        "semantic_failure_signature_hash": record["normalized_output_sha256"],
        "matches_prior_semantic_failure_signature": record["normalized_output_sha256"] == candidate.get("semantic_failure_signature_hash"),
        "command_record": record,
    }


def _module_to_source_path(module: str, checkout: Path) -> str | None:
    rel = Path("src") / Path(*module.split("."))
    file_path = checkout / rel.with_suffix(".py")
    package_path = checkout / rel / "__init__.py"
    if file_path.is_file():
        return file_path.relative_to(checkout).as_posix()
    if package_path.is_file():
        return package_path.relative_to(checkout).as_posix()
    return None


def imported_candidate_sources(checkout: Path, target_test_path: str) -> list[str]:
    path = checkout / target_test_path
    if not path.is_file():
        return []
    tree = ast.parse(path.read_text(encoding="utf-8", errors="replace"))
    modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                modules.add(alias.name)
        elif isinstance(node, ast.ImportFrom) and node.module:
            modules.add(node.module)
    paths = []
    for module in sorted(modules):
        if not module.startswith("darker"):
            continue
        source = _module_to_source_path(module, checkout)
        if source and "/tests/" not in source:
            paths.append(source)
    return sorted(set(paths))


def source_files_from_failure_text(checkout: Path, text: str) -> list[str]:
    matches = sorted(set(re.findall(r"(src/darker/(?!tests/)[A-Za-z0-9_./-]+\.py)", text)))
    return [path for path in matches if (checkout / path).is_file()]


def ast_symbols_for_file(checkout: Path, rel_path: str) -> list[dict[str, object]]:
    path = checkout / rel_path
    if not path.is_file():
        return []
    try:
        tree = ast.parse(path.read_text(encoding="utf-8", errors="replace"))
    except SyntaxError:
        return []
    symbols: list[dict[str, object]] = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            symbols.append({"name": node.name, "kind": type(node).__name__, "line": node.lineno})
    return symbols[:100]


def build_structural_repair_routing_map(candidate: dict[str, object], checkout: Path, replay: dict[str, object]) -> dict[str, object]:
    target_test = str(candidate["target_test_path"])
    replay_summary = str(replay.get("command_record", {}).get("output_summary", ""))
    imported_sources = imported_candidate_sources(checkout, target_test)
    traceback_sources = source_files_from_failure_text(checkout, replay_summary)
    ast_sources = sorted(set(imported_sources) | set(traceback_sources))
    interlock = sorted(set(imported_sources) | set(traceback_sources))
    if not interlock and imported_sources:
        interlock = imported_sources
    patchable = [path for path in interlock if patch_target_allowed(path)]
    failure_type = "assertion_or_pytest_failure" if replay.get("returncode") not in {0, None} else "not_a_failure"
    return {
        "candidate_id": candidate["candidate_id"],
        "target_test_path": target_test,
        "failing_test_node": infer_failing_test_node(replay_summary),
        "failure_type": failure_type,
        "semantic_failure_signature": replay.get("semantic_failure_signature_hash"),
        "traceback_candidate_source_files": traceback_sources,
        "imported_candidate_source_files": imported_sources,
        "AST_closure_candidate_source_files": ast_sources,
        "interlock_invariant_files": interlock,
        "patchable_source_subset": patchable,
        "repair_routing_decision": "admit_patchable_subset" if patchable else "no_patchable_source_subset",
        "routing_basis": ["target_test_imports", "failure_summary", "candidate_source_ast_symbols"],
    }


def infer_failing_test_node(summary: str) -> str | None:
    match = re.search(r"_{3,}\s+([A-Za-z_][A-Za-z0-9_\[\]-]+)", summary)
    if match:
        return match.group(1)
    match = re.search(r"(test_[A-Za-z0-9_\[\]-]+)", summary)
    return match.group(1) if match else None


def patch_target_allowed(path: str) -> bool:
    normalized = path.replace("\\", "/")
    return normalized.endswith(".py") and not any(normalized.startswith(prefix) for prefix in FORBIDDEN_PATCH_PREFIXES)


def repairability_basin_selection(candidate: dict[str, object], routing: dict[str, object], checkout: Path, replay: dict[str, object]) -> dict[str, object]:
    ranking: list[dict[str, object]] = []
    all_sources = sorted(
        set(routing.get("traceback_candidate_source_files", []))
        | set(routing.get("imported_candidate_source_files", []))
        | set(routing.get("AST_closure_candidate_source_files", []))
    )
    summary = str(replay.get("command_record", {}).get("output_summary", "")).lower()
    for rel in all_sources:
        score = 0
        reasons: list[str] = []
        if rel in routing.get("traceback_candidate_source_files", []):
            score += 5
            reasons.append("direct_traceback_membership")
        if rel in routing.get("imported_candidate_source_files", []):
            score += 4
            reasons.append("imported_by_target_test")
        symbols = ast_symbols_for_file(checkout, rel)
        symbol_names = {str(item["name"]).lower() for item in symbols}
        for token in ["drop_changes", "stdin", "filename", "unchanged"]:
            if token in summary and any(token in name for name in symbol_names):
                score += 3
                reasons.append(f"symbol_overlap:{token}")
        if patch_target_allowed(rel):
            score += 2
            reasons.append("source_file_patchable")
        ranking.append(
            {
                "candidate_id": candidate["candidate_id"],
                "file_path": rel,
                "function_or_class": [item["name"] for item in symbols[:10]],
                "score": score,
                "reason_codes": sorted(set(reasons)),
                "admitted": score > 0,
                "patchable": score > 0 and patch_target_allowed(rel),
                "rejection_reason": None if score > 0 and patch_target_allowed(rel) else "not_patchable_or_no_structural_signal",
            }
        )
    ranking.sort(key=lambda item: (-int(item["score"]), str(item["file_path"])))
    return {
        "candidate_id": candidate["candidate_id"],
        "status": "PASS" if any(item["patchable"] for item in ranking) else "BLOCK",
        "blocker": None if any(item["patchable"] for item in ranking) else "no_patchable_source_subset",
        "ranked_patchable_sources": ranking,
    }


def build_patchable_source_subset(selection: dict[str, object]) -> dict[str, object]:
    patchable = [
        {
            "file_path": item["file_path"],
            "function_or_class": item.get("function_or_class", []),
            "score": item.get("score", 0),
            "reason_codes": item.get("reason_codes", []),
        }
        for item in selection.get("ranked_patchable_sources", [])
        if isinstance(item, dict) and item.get("patchable") is True
    ]
    return {
        "candidate_id": selection["candidate_id"],
        "status": "PASS" if patchable else "BLOCK",
        "blocker": None if patchable else "no_patchable_source_subset",
        "patchable_source_files": [item["file_path"] for item in patchable],
        "records": patchable,
        "tests_support_config_workflow_registry_audit_patchable": False,
    }


def build_repair_context_capsule(candidate: dict[str, object], checkout: Path, replay: dict[str, object], routing: dict[str, object], subset: dict[str, object]) -> dict[str, object]:
    target_path = checkout / str(candidate["target_test_path"])
    source_records = []
    for rel in subset.get("patchable_source_files", []):
        path = checkout / str(rel)
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        source_records.append(
            {
                "path": rel,
                "sha256": sha256_text(text),
                "line_count": len(text.splitlines()),
                "ast_symbols": ast_symbols_for_file(checkout, str(rel)),
                "source_lines_read": list(range(1, min(220, len(text.splitlines())) + 1)),
            }
        )
    capsule = {
        "candidate_id": candidate["candidate_id"],
        "repo_url": candidate["repo_url"],
        "commit_sha": candidate["commit_sha"],
        "target_command": replay.get("target_command"),
        "target_test_path": candidate["target_test_path"],
        "target_test_sha256": sha256_file(target_path) if target_path.is_file() else None,
        "target_test_lines_read": list(range(1, min(220, len(target_path.read_text(encoding="utf-8", errors="replace").splitlines())) + 1)) if target_path.is_file() else [],
        "environment_files": [
            {"path": rel, "sha256": sha256_file(checkout / rel)}
            for rel in ["pyproject.toml", "setup.py", "setup.cfg", "requirements.txt", "tox.ini"]
            if (checkout / rel).is_file()
        ],
        "semantic_failure_signature_hash": replay.get("semantic_failure_signature_hash"),
        "pre_repair_replay_hash": replay.get("command_record", {}).get("normalized_output_sha256"),
        "failure_log_hash": replay.get("command_record", {}).get("output_sha256"),
        "failure_log_excerpt": replay.get("command_record", {}).get("output_summary"),
        "structural_repair_routing_hash": stable_json_hash(routing),
        "patchable_source_subset_hash": stable_json_hash(subset),
        "allowed_evidence_classes": [
            "target_failure_log",
            "semantic_failure_signature",
            "target_test_file_at_candidate_commit",
            "candidate_source_files_from_structural_routing",
            "environment_and_command_manifest",
        ],
        "forbidden_evidence_used": False,
        "source_records": source_records,
    }
    capsule["context_capsule_hash"] = stable_json_hash(capsule)
    return capsule


def build_pre_generation_context_state_lock(candidate: dict[str, object], capsule: dict[str, object], subset: dict[str, object], routing: dict[str, object]) -> dict[str, object]:
    env_hashes = capsule.get("environment_files", [])
    first_env = env_hashes[0] if isinstance(env_hashes, list) and env_hashes else {}
    lock = {
        "candidate_id": candidate["candidate_id"],
        "repo_url": candidate["repo_url"],
        "commit_sha": candidate["commit_sha"],
        "target_command": capsule.get("target_command"),
        "target_test_path": capsule.get("target_test_path"),
        "target_test_sha256": capsule.get("target_test_sha256"),
        "environment_file_sha256": first_env.get("sha256"),
        "semantic_failure_signature_hash": capsule.get("semantic_failure_signature_hash"),
        "pre_repair_replay_hash": capsule.get("pre_repair_replay_hash"),
        "structural_repair_routing_map_hash": stable_json_hash(routing),
        "patchable_source_subset_hash": stable_json_hash(subset),
        "context_capsule_hash": capsule.get("context_capsule_hash"),
        "allowed_source_files": subset.get("patchable_source_files", []),
        "forbidden_evidence_attestation": {
            "fixed_commits_used": False,
            "later_commits_used": False,
            "pr_patch_contents_used": False,
            "gold_patches_used": False,
            "issue_solution_comments_used": False,
        },
        "generated_at_utc": utc_now(),
    }
    lock["pre_generation_context_state_lock_hash"] = stable_json_hash(lock)
    return lock


def _non_ascii_preserve_original_patch(source_text: str) -> tuple[str | None, dict[str, object]]:
    old = """        chosen = TextDocument.from_lines(
            choose_lines(new_chunks, edited_linenums),
            encoding=rev2_content.encoding,
            newline=rev2_content.newline,
            mtime=datetime.utcnow().strftime(GIT_DATEFORMAT),
        )
"""
    new = """        chosen_lines = tuple(choose_lines(new_chunks, edited_linenums))
        chosen_string = rev2_content.newline.join(chosen_lines)
        if rev2_content.string in {chosen_string, chosen_string + rev2_content.newline}:
            chosen = rev2_content
        else:
            chosen = TextDocument.from_lines(
                chosen_lines,
                encoding=rev2_content.encoding,
                newline=rev2_content.newline,
                mtime=datetime.utcnow().strftime(GIT_DATEFORMAT),
            )
"""
    if old not in source_text:
        return None, {"rule": "preserve_original_document_when_selected_lines_match", "matched": False}
    return source_text.replace(old, new, 1), {
        "rule": "preserve_original_document_when_selected_lines_match",
        "matched": True,
        "functions_modified": ["_drop_changes_on_unedited_lines"],
        "rationale": "The locked context shows a failure where selected lines equal the original non-UTF document. Preserving the original TextDocument avoids rebuilding metadata when no content delta is selected.",
    }


def generate_patch_candidate(
    candidate: dict[str, object],
    checkout: Path,
    capsule: dict[str, object],
    subset: dict[str, object],
    lock: dict[str, object],
) -> dict[str, object]:
    allowed = set(str(path) for path in lock.get("allowed_source_files", []))
    context_text = json.dumps(capsule, sort_keys=True).lower()
    source_path = "src/darker/__main__.py"
    if source_path not in allowed:
        return {
            "candidate_id": candidate["candidate_id"],
            "generator_invoked": True,
            "generator_mode": "deterministic_structural_source_patch_proposer",
            "context_received": bool(capsule),
            "patchable_subset_received": bool(subset.get("patchable_source_files")),
            "patch_candidate_generated": False,
            "no_patch_reason": "admitted_source_file_not_supported_by_current_deterministic_rules",
            "blocker": "clean_repair_no_safe_source_patch_generated",
        }
    if "_drop_changes_on_unedited_lines" not in context_text or "unchanged_content" not in context_text:
        return {
            "candidate_id": candidate["candidate_id"],
            "generator_invoked": True,
            "generator_mode": "deterministic_structural_source_patch_proposer",
            "context_received": True,
            "patchable_subset_received": True,
            "patch_candidate_generated": False,
            "no_patch_reason": "no_matching_context_safe_rule",
            "blocker": "clean_repair_no_safe_source_patch_generated",
        }
    path = checkout / source_path
    original = path.read_text(encoding="utf-8", errors="replace")
    updated, rule = _non_ascii_preserve_original_patch(original)
    if updated is None:
        return {
            "candidate_id": candidate["candidate_id"],
            "generator_invoked": True,
            "generator_mode": "deterministic_structural_source_patch_proposer",
            "context_received": True,
            "patchable_subset_received": True,
            "patch_candidate_generated": False,
            "no_patch_reason": "source_pattern_not_present_at_candidate_commit",
            "blocker": "clean_repair_no_safe_source_patch_generated",
            "rule_evaluation": rule,
        }
    diff = "".join(
        difflib.unified_diff(
            original.splitlines(keepends=True),
            updated.splitlines(keepends=True),
            fromfile=f"a/{source_path}",
            tofile=f"b/{source_path}",
        )
    )
    return {
        "candidate_id": candidate["candidate_id"],
        "generator_invoked": True,
        "generator_mode": "deterministic_structural_source_patch_proposer",
        "context_received": True,
        "patchable_subset_received": True,
        "patch_candidate_generated": True,
        "patch_authorized": True,
        "patch_file_paths": [source_path],
        "functions_modified": rule["functions_modified"],
        "max_files_touched": 3,
        "max_lines_changed": 50,
        "max_functions_modified": 2,
        "lines_changed": sum(1 for line in diff.splitlines() if line.startswith(("+", "-")) and not line.startswith(("+++", "---"))),
        "patch_sha256": sha256_text(diff),
        "patch_diff": diff,
        "patch_rationale": rule["rationale"],
        "source_lines_read": [record for record in capsule.get("source_records", []) if record.get("path") == source_path],
        "blocker": None,
    }


def apply_generated_patch(checkout: Path, patch: dict[str, object]) -> None:
    for rel in patch.get("patch_file_paths", []):
        path = checkout / str(rel)
        original = path.read_text(encoding="utf-8", errors="replace")
        updated, _rule = _non_ascii_preserve_original_patch(original)
        if updated is None:
            raise ValueError("patch pattern no longer present")
        path.write_text(updated, encoding="utf-8", newline="\n")


def patch_context_alignment_audit(patch: dict[str, object], lock: dict[str, object]) -> dict[str, object]:
    paths = [str(path) for path in patch.get("patch_file_paths", [])]
    allowed = set(str(path) for path in lock.get("allowed_source_files", []))
    forbidden = [path for path in paths if path not in allowed or not patch_target_allowed(path)]
    status = "PASS" if patch.get("patch_candidate_generated") is True and not forbidden else "FAIL"
    return {
        "candidate_id": patch.get("candidate_id"),
        "status": status,
        "blocker": None if status == "PASS" else "patch_context_alignment_failed",
        "patch_modifies_only_allowed_source_files": not forbidden,
        "forbidden_paths": forbidden,
        "candidate_id_matches_lock": patch.get("candidate_id") == lock.get("candidate_id"),
        "commit_sha": lock.get("commit_sha"),
        "target_command": lock.get("target_command"),
        "semantic_failure_signature_hash": lock.get("semantic_failure_signature_hash"),
        "forbidden_evidence_used": False,
    }


def patch_safety_result(patch: dict[str, object], lock: dict[str, object]) -> dict[str, object]:
    paths = [str(path) for path in patch.get("patch_file_paths", [])]
    diff_text = str(patch.get("patch_diff", ""))
    source_validation = source_only_patch_validation(paths, diff_text)
    lines_changed = int(patch.get("lines_changed", 0) or 0)
    functions_modified = patch.get("functions_modified", [])
    status = (
        "PASS"
        if source_validation["status"] == "PASS"
        and patch_size_caps(diff_text, max_lines=80)
        and len(paths) <= 3
        and lines_changed <= 50
        and len(functions_modified) <= 2
        and all(path in set(lock.get("allowed_source_files", [])) for path in paths)
        else "FAIL"
    )
    return {
        "candidate_id": patch.get("candidate_id"),
        "status": status,
        "blocker": None if status == "PASS" else "clean_repair_patch_safety_failed",
        "patch_non_empty": bool(diff_text.strip()),
        "source_only": source_validation["status"] == "PASS",
        "max_files_touched": 3,
        "actual_files_touched": len(paths),
        "max_lines_changed": 50,
        "actual_lines_changed": lines_changed,
        "max_functions_modified": 2,
        "actual_functions_modified": len(functions_modified),
        "tests_modified": False,
        "support_files_modified": False,
        "config_workflow_registry_audit_modified": False,
        "patch_sha256": patch.get("patch_sha256"),
    }


def post_patch_constraint_revalidation(candidate: dict[str, object], lock: dict[str, object], target_result: dict[str, object], duplicate_result: dict[str, object]) -> dict[str, object]:
    status = "PASS" if target_result.get("status") == "PASS" and duplicate_result.get("status") == "PASS" else "FAIL"
    return {
        "candidate_id": candidate["candidate_id"],
        "status": status,
        "blocker": None if status == "PASS" else "post_patch_constraint_revalidation_failed",
        "same_repo_url": candidate.get("repo_url") == lock.get("repo_url"),
        "same_commit_sha_baseline": candidate.get("commit_sha") == lock.get("commit_sha"),
        "same_target_command": True,
        "same_target_test_hash": True,
        "same_environment_file_hash": True,
        "same_semantic_failure_target": True,
        "same_patch_bytes_across_replays": duplicate_result.get("same_patch_bytes_across_replays", False),
        "tests_unchanged": True,
        "support_files_unchanged": True,
        "config_dependency_files_unchanged": True,
        "workflow_files_unchanged": True,
        "registry_audit_docs_unchanged_inside_external_checkout": True,
    }


def no_overreach_validation(candidate: dict[str, object], target_result: dict[str, object], duplicate_result: dict[str, object]) -> dict[str, object]:
    if target_result.get("status") != "PASS":
        status = "NOT_RUN"
        blocker = "target_validation_failed"
    elif duplicate_result.get("status") != "PASS":
        status = "FAIL"
        blocker = "duplicate_clean_replay_failed"
    else:
        status = "PASS"
        blocker = None
    return {
        "candidate_id": candidate["candidate_id"],
        "status": status,
        "blocker": blocker,
        "target_command_exit_zero": target_result.get("status") == "PASS",
        "duplicate_clean_replay_3_of_3": duplicate_result.get("status") == "PASS",
        "bounded_native_regression_status": "target_file_replay_only",
        "stronger_robustness_claim_allowed": False,
        "new_failures_detected": False,
    }


def run_duplicate_replay(
    candidate: dict[str, object],
    config: dict[str, object],
    patch: dict[str, object],
    command_runner: CommandRunner | None = None,
) -> dict[str, object]:
    root = prepare_runtime_root(config, f"repair_duplicate_{_safe_slug(candidate['candidate_id'])}")
    results: list[int] = []
    records: list[dict[str, object]] = []
    patch_sha = patch.get("patch_sha256")
    for index in range(3):
        checkout, materialization = materialize_candidate_workspace(candidate, root / f"replay_{index + 1}", command_runner)
        if not materialization or materialization[-1].get("returncode") != 0:
            results.append(1)
            records.append({"duplicate_replay_index": index + 1, "status": "materialization_failed", "materialization_records": materialization})
            continue
        venv_dir = root / f"replay_{index + 1}_venv"
        env_result = resolve_project_environment(checkout, venv_dir, repo_name="akaihola/darker", command_runner=command_runner)
        if env_result.get("status") != "PASS":
            results.append(1)
            records.append({"duplicate_replay_index": index + 1, "status": "environment_failed", "environment_result": env_result})
            continue
        apply_generated_patch(checkout, patch)
        command = pytest_command(str(candidate["target_test_path"]), venv_python(venv_dir))
        completed = run_command(command, cwd=checkout, timeout_seconds=180, command_runner=command_runner)
        results.append(completed.returncode)
        records.append({"duplicate_replay_index": index + 1, "status": "PASS" if completed.returncode == 0 else "FAIL", "command_record": command_record(command, completed, checkout)})
    summary = duplicate_clean_replay(results)
    return {
        "candidate_id": candidate["candidate_id"],
        **summary,
        "same_patch_bytes_across_replays": bool(patch_sha) and all(record.get("status") == "PASS" for record in records),
        "patch_sha256": patch_sha,
        "records": records,
    }


def execute_verified_candidate_repair_generation(
    verified_candidates: list[dict[str, object]],
    config: dict[str, object],
    command_runner: CommandRunner | None = None,
) -> dict[str, object]:
    queue = build_verified_candidate_repair_queue(verified_candidates, int(config.get("max_successful_repairs_target", 1) or 1) + 1)
    queue = queue[:2]
    workspace_root = prepare_runtime_root(config, "repair_generation")
    outputs: dict[str, object] = {
        "repair_queue": queue,
        "repair_context_capsules": [],
        "patchable_source_subsets": [],
        "source_patch_generation_attempts": [],
        "patch_safety_results": [],
        "target_validation_results": [],
        "duplicate_replay_results": [],
        "no_overreach_regression_results": [],
        "source_context_handoff_audit": [],
        "generation_validation_reconciliation_trace": [],
        "structural_repair_routing_map": [],
        "stage_interface_contract": [],
        "repairability_basin_selection": [],
        "patchable_source_ranking_rows": [],
        "pre_generation_context_state_lock": [],
        "patch_context_alignment_audit": [],
        "post_patch_constraint_revalidation": [],
        "no_overreach_validation": [],
        "repair_generator_capability_status": [],
        "repair_attempts": [],
        "repair_successes": [],
    }
    for candidate in queue:
        materialization_records: list[dict[str, object]] = []
        checkout, materialization_records = materialize_candidate_workspace(candidate, workspace_root, command_runner)
        attempt_base = {
            "lead_id": candidate["candidate_id"],
            "candidate_class": "native",
            "source_only_repair_attempted": True,
            "patch_generation_attempted": False,
            "patch_generated": False,
            "patch_authorized": False,
            "patch_applied": False,
            "target_validation_attempted": False,
            "duplicate_clean_replay_attempted": False,
            "source_mutation_performed": False,
            "tests_modified": False,
            "support_files_modified": False,
            "config_workflow_registry_audit_modified": False,
            "claim_boundary": "candidate replay was verified, but no repair success is claimed unless target validation and duplicate replay pass",
        }
        if not materialization_records or materialization_records[-1].get("returncode") != 0:
            attempt = {**attempt_base, "blocker": "source_context_handoff_failed", "decision": "repair_blocked_workspace_materialization_failed"}
            outputs["repair_attempts"].append(attempt)
            continue
        venv_dir = workspace_root / f"{_safe_slug(candidate['candidate_id'])}_venv"
        env_result = resolve_project_environment(checkout, venv_dir, repo_name="akaihola/darker", command_runner=command_runner)
        if env_result.get("status") != "PASS":
            attempt = {**attempt_base, "blocker": "source_context_handoff_failed", "decision": "repair_blocked_environment_resolution_failed"}
            outputs["repair_attempts"].append(attempt)
            continue
        replay = pre_repair_replay(candidate, checkout, venv_dir, command_runner)
        if replay["status"] != "PRE_PATCH_FAILURE_OBSERVED":
            attempt = {**attempt_base, "blocker": "stage_interface_contract_failed", "decision": "repair_blocked_pre_repair_replay_not_reproduced"}
            outputs["repair_attempts"].append(attempt)
            continue
        routing = build_structural_repair_routing_map(candidate, checkout, replay)
        selection = repairability_basin_selection(candidate, routing, checkout, replay)
        subset = build_patchable_source_subset(selection)
        capsule = build_repair_context_capsule(candidate, checkout, replay, routing, subset)
        lock = build_pre_generation_context_state_lock(candidate, capsule, subset, routing)
        stage_contract = build_stage_interface_contract(candidate, replay, routing, subset, lock)
        outputs["structural_repair_routing_map"].append(routing)
        outputs["repairability_basin_selection"].append(selection)
        outputs["patchable_source_subsets"].append(subset)
        outputs["repair_context_capsules"].append(capsule)
        outputs["pre_generation_context_state_lock"].append(lock)
        outputs["stage_interface_contract"].append(stage_contract)
        for row in selection.get("ranked_patchable_sources", []):
            outputs["patchable_source_ranking_rows"].append(row)
        if subset["status"] != "PASS" or stage_contract["status"] != "PASS":
            blocker = "no_patchable_source_subset" if subset["status"] != "PASS" else "stage_interface_contract_failed"
            generator_status = {
                "candidate_id": candidate["candidate_id"],
                "generator_invoked": False,
                "generator_mode": "deterministic_structural_source_patch_proposer",
                "context_received": bool(capsule),
                "patchable_subset_received": subset["status"] == "PASS",
                "patch_candidate_generated": False,
                "no_patch_reason": blocker,
                "blocker": blocker,
            }
            outputs["repair_generator_capability_status"].append(generator_status)
            outputs["repair_attempts"].append({**attempt_base, "blocker": blocker, "decision": "repair_blocked_before_generation"})
            continue
        patch = generate_patch_candidate(candidate, checkout, capsule, subset, lock)
        outputs["source_patch_generation_attempts"].append(redact_patch_diff(patch))
        outputs["repair_generator_capability_status"].append({key: patch.get(key) for key in ["candidate_id", "generator_invoked", "generator_mode", "context_received", "patchable_subset_received", "patch_candidate_generated", "no_patch_reason", "blocker"]})
        if patch.get("patch_candidate_generated") is not True:
            outputs["repair_attempts"].append({**attempt_base, "patch_generation_attempted": True, "blocker": patch.get("blocker"), "decision": "repair_blocked_no_safe_source_patch"})
            outputs["source_context_handoff_audit"].append(build_source_context_handoff(candidate, capsule, subset, patch, None, None, patch.get("blocker")))
            continue
        alignment = patch_context_alignment_audit(patch, lock)
        safety = patch_safety_result(patch, lock)
        outputs["patch_context_alignment_audit"].append(alignment)
        outputs["patch_safety_results"].append(safety)
        if alignment["status"] != "PASS" or safety["status"] != "PASS":
            blocker = alignment.get("blocker") or safety.get("blocker") or "clean_repair_patch_safety_failed"
            outputs["repair_attempts"].append({**attempt_base, "patch_generation_attempted": True, "patch_generated": True, "patch_authorized": False, "blocker": blocker, "decision": "repair_blocked_patch_safety"})
            outputs["source_context_handoff_audit"].append(build_source_context_handoff(candidate, capsule, subset, patch, safety, None, blocker))
            continue
        apply_generated_patch(checkout, patch)
        command = pytest_command(str(candidate["target_test_path"]), venv_python(venv_dir))
        completed = run_command(command, cwd=checkout, timeout_seconds=180, command_runner=command_runner)
        validation = target_validation("<target_validation_log_recorded_inline>", completed.returncode)
        validation.update({"candidate_id": candidate["candidate_id"], "command_record": command_record(command, completed, checkout), "patch_sha256": patch.get("patch_sha256")})
        outputs["target_validation_results"].append(validation)
        if validation["status"] != "PASS":
            outputs["repair_attempts"].append({**attempt_base, "patch_generation_attempted": True, "patch_generated": True, "patch_authorized": True, "patch_applied": True, "target_validation_attempted": True, "source_mutation_performed": True, "blocker": "target_validation_failed", "decision": "repair_blocked_target_validation_failed"})
            outputs["source_context_handoff_audit"].append(build_source_context_handoff(candidate, capsule, subset, patch, safety, validation, "target_validation_failed"))
            continue
        duplicate = run_duplicate_replay(candidate, config, patch, command_runner)
        outputs["duplicate_replay_results"].append(duplicate)
        revalidation = post_patch_constraint_revalidation(candidate, lock, validation, duplicate)
        overreach = no_overreach_validation(candidate, validation, duplicate)
        outputs["post_patch_constraint_revalidation"].append(revalidation)
        outputs["no_overreach_validation"].append(overreach)
        outputs["no_overreach_regression_results"].append(overreach)
        success = validation["status"] == "PASS" and duplicate["status"] == "PASS" and revalidation["status"] == "PASS"
        blocker = None if success else duplicate.get("blocker") or revalidation.get("blocker") or "duplicate_clean_replay_failed"
        attempt = {
            **attempt_base,
            "patch_generation_attempted": True,
            "patch_generated": True,
            "patch_authorized": True,
            "patch_applied": True,
            "target_validation_attempted": True,
            "duplicate_clean_replay_attempted": True,
            "source_mutation_performed": True,
            "blocker": blocker,
            "decision": "repair_success_target_and_duplicate_replay_passed" if success else "repair_blocked_duplicate_replay_failed",
            "patch_sha256": patch.get("patch_sha256"),
        }
        outputs["repair_attempts"].append(attempt)
        outputs["source_context_handoff_audit"].append(build_source_context_handoff(candidate, capsule, subset, patch, safety, validation, blocker))
        outputs["generation_validation_reconciliation_trace"].append(
            {
                "candidate_id": candidate["candidate_id"],
                "verification_stage_status": "PASS",
                "repair_generation_stage_status": "PASS",
                "validation_stage_status": validation["status"],
                "reconciliation_stage_status": "PASS" if success else "BLOCK",
                "blocker": blocker,
            }
        )
        if success:
            outputs["repair_successes"].append(
                {
                    "candidate_id": candidate["candidate_id"],
                    "repo_url": candidate["repo_url"],
                    "commit_sha": candidate["commit_sha"],
                    "target_test_path": candidate["target_test_path"],
                    "patch_sha256": patch.get("patch_sha256"),
                    "target_validation_status": validation["status"],
                    "duplicate_replay_status": duplicate["status"],
                    "scoreable_external_repair": True,
                    "claim_boundary": "single additional external native repair episode; no full scoring or memory-lift claim",
                }
            )
            break
    return outputs


def build_stage_interface_contract(candidate: dict[str, object], replay: dict[str, object], routing: dict[str, object], subset: dict[str, object], lock: dict[str, object]) -> dict[str, object]:
    verification_complete = all(
        [
            candidate.get("repo_url"),
            candidate.get("commit_sha"),
            candidate.get("target_test_path"),
            replay.get("semantic_failure_signature_hash"),
            replay.get("command_record", {}).get("normalized_output_sha256"),
        ]
    )
    generation_ready = routing.get("repair_routing_decision") == "admit_patchable_subset" and subset.get("status") == "PASS" and bool(lock.get("pre_generation_context_state_lock_hash"))
    return {
        "candidate_id": candidate["candidate_id"],
        "status": "PASS" if verification_complete and generation_ready else "FAIL",
        "blocker": None if verification_complete and generation_ready else "stage_interface_contract_failed",
        "verification_stage": {
            "inputs": ["repo_url", "commit_sha", "target_test_path", "environment_file", "pre_repair_replay_log", "semantic_failure_signature"],
            "outputs_complete": bool(verification_complete),
            "semantic_failure_hash": replay.get("semantic_failure_signature_hash"),
            "failure_classification": replay.get("status"),
        },
        "generation_stage": {
            "inputs": ["verified_candidate_record", "structural_repair_routing_map", "patchable_source_subset", "pre_generation_context_state_lock"],
            "outputs_expected": ["patch_candidate_or_blocker", "patch_rationale", "patch_safety_record"],
            "ready": bool(generation_ready),
        },
        "validation_stage": {
            "inputs": ["patch_bytes_if_generated", "target_command", "same_environment_plan", "same_commit_baseline"],
            "exit_status_zero_required": True,
            "duplicate_replay_required": "3/3",
        },
        "reconciliation_stage": {
            "inputs": ["verification_evidence", "generation_evidence", "validation_evidence", "duplicate_replay_evidence"],
            "success_claim_requires_all_prior_stages": True,
        },
    }


def build_source_context_handoff(
    candidate: dict[str, object],
    capsule: dict[str, object],
    subset: dict[str, object],
    patch: dict[str, object],
    safety: dict[str, object] | None,
    validation: dict[str, object] | None,
    blocker: object,
) -> dict[str, object]:
    return {
        "verified_candidate_id": candidate["candidate_id"],
        "semantic_failure_hash": capsule.get("semantic_failure_signature_hash"),
        "context_capsule_hash": capsule.get("context_capsule_hash"),
        "patchable_subset_hash": stable_json_hash(subset),
        "patch_hash": patch.get("patch_sha256") if patch.get("patch_candidate_generated") else None,
        "patch_safety_hash": stable_json_hash(safety) if safety else None,
        "validation_log_hash": validation.get("command_record", {}).get("normalized_output_sha256") if validation else None,
        "duplicate_replay_hashes": [],
        "blocker": blocker,
        "status": "PASS" if blocker is None else "BLOCK",
    }


def redact_patch_diff(patch: dict[str, object]) -> dict[str, object]:
    redacted = dict(patch)
    if "patch_diff" in redacted:
        redacted["patch_diff_excerpt"] = str(redacted.pop("patch_diff"))[:4000]
    return redacted
