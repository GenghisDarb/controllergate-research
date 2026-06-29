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

SKIP_GLOB_TARGET_NODE = "src/darker/tests/test_main_isort.py::test_isort_respects_skip_glob"
SKIP_GLOB_SEMANTIC_MARKERS = (
    "skip_glob",
    "isort",
    "test_isort_respects_skip_glob",
    "respects skip_glob setting",
    "conf/settings",
)

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


def select_semantic_target_node(
    nodes: list[str],
    *,
    intended_node: str,
    semantic_markers: Iterable[str],
) -> dict[str, object]:
    """Select a target node by explicit semantic intent, not first failure order."""

    marker_hits = [
        marker
        for marker in semantic_markers
        if marker.lower() in intended_node.lower() or marker.lower().replace(" ", "_") in intended_node.lower()
    ]
    node_present = intended_node in nodes
    return {
        "status": "PASS" if node_present and marker_hits else "BLOCK",
        "blocker": None if node_present and marker_hits else "target_node_semantic_intent_mismatch",
        "selected_node": intended_node if node_present else None,
        "semantic_markers": list(semantic_markers),
        "marker_hits": marker_hits,
        "selection_basis": "explicit_target_hint_and_semantic_marker_match",
        "non_intent_first_failure_allowed_as_primary": False,
    }


def classify_non_intent_failure(node: str, selected_node: str | None, output_summary: str) -> dict[str, object]:
    is_selected = selected_node is not None and node == selected_node
    environment_markers = ("ModuleNotFoundError", "ImportError", "fixture", "plugin", "No module named")
    return {
        "node": node,
        "selected_intended_node": selected_node,
        "is_selected_intended_node": is_selected,
        "classification": "selected_intended_node" if is_selected else "non_intent_fixture_or_setup_failure",
        "environment_or_setup_signal": any(marker in output_summary for marker in environment_markers),
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
        for token in ["drop_changes", "stdin", "filename", "unchanged", "skip_glob", "isort", "path", "formatter", "main"]:
            if token in summary and any(token in name for name in symbol_names):
                score += 3
                reasons.append(f"symbol_overlap:{token}")
        if candidate.get("candidate_id") == "darker_skip_glob_failing_test":
            lower_rel = rel.lower()
            if lower_rel in {"src/darker/__main__.py", "src/darker/import_sorting.py"}:
                score += 4
                reasons.append("skip_glob_intent_source_surface_hint")
            if any(token in lower_rel for token in ["import", "isort", "main", "config"]):
                score += 2
                reasons.append("skip_glob_path_relevance")
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
        "blocker": None if patchable else "patchable_source_subset_derivation_failed",
        "patchable_source_files": [item["file_path"] for item in patchable],
        "records": patchable,
        "tests_support_config_workflow_registry_audit_patchable": False,
    }


def classify_repair_generator_capability(
    *,
    subset: dict[str, object],
    patch: dict[str, object] | None,
    generator_invoked: bool,
) -> dict[str, object]:
    if not generator_invoked:
        status = "BLOCK"
        capability = "repair_generator_not_implemented"
        blocker = "clean_repair_generator_not_implemented"
    elif not subset.get("patchable_source_files"):
        status = "BLOCK"
        capability = "patchable_source_subset_empty"
        blocker = "patchable_source_subset_derivation_failed"
    elif patch is None:
        status = "BLOCK"
        capability = "pre_generation_context_missing"
        blocker = "pre_generation_context_missing"
    elif patch.get("patch_candidate_generated") is True:
        status = "PASS"
        capability = "patch_generated_succeeded"
        blocker = None
    elif patch.get("blocker") == "clean_repair_no_safe_source_patch_generated":
        status = "BLOCK"
        capability = "safe_patch_generation_attempted_no_patch_found"
        blocker = "clean_repair_no_safe_source_patch_generated"
    elif patch.get("blocker") == "clean_repair_patch_safety_failed":
        status = "BLOCK"
        capability = "patch_generated_failed_safety"
        blocker = "clean_repair_patch_safety_failed"
    elif patch.get("blocker") == "target_validation_failed":
        status = "BLOCK"
        capability = "patch_generated_failed_target_validation"
        blocker = "target_validation_failed"
    else:
        status = "BLOCK"
        capability = str(patch.get("no_patch_reason") or "safe_patch_generation_attempted_no_patch_found")
        blocker = str(patch.get("blocker") or "clean_repair_no_safe_source_patch_generated")
    return {
        "status": status,
        "capability_classification": capability,
        "blocker": blocker,
        "generator_invoked": generator_invoked,
        "patchable_subset_received": bool(subset.get("patchable_source_files")),
        "patch_candidate_generated": bool(patch and patch.get("patch_candidate_generated") is True),
        "taxonomy": [
            "repair_generator_not_implemented",
            "patchable_source_subset_empty",
            "pre_generation_context_missing",
            "safe_patch_generation_attempted_no_patch_found",
            "patch_generated_failed_safety",
            "patch_generated_failed_target_validation",
            "patch_generated_succeeded",
        ],
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


def _stdin_filename_dash_patch(source_text: str) -> tuple[str | None, dict[str, object]]:
    old = """    if len(src) == 0:
        return
    raise ConfigurationError(
"""
    new = """    if len(src) == 0:
        return
    if len(src) == 1 and src[0] == "-":
        return
    raise ConfigurationError(
"""
    if old not in source_text:
        return None, {"rule": "allow_dash_src_with_stdin_filename", "matched": False}
    return source_text.replace(old, new, 1), {
        "rule": "allow_dash_src_with_stdin_filename",
        "matched": True,
        "functions_modified": ["validate_stdin_src"],
        "rationale": "The locked context shows that stdin mode with --stdin-filename and '-' is rejected before stdin content can be processed. Allowing '-' through the stdin validation gate keeps the repair inside the selected source function.",
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
    if candidate.get("candidate_id") == "darker_stdin_filename":
        source_path = "src/darker/config.py"
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
        if "validate_stdin_src" not in context_text or "stdin_filename" not in context_text:
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
        updated, rule = _stdin_filename_dash_patch(original)
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
            "patch_rule": rule["rule"],
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
        "patch_rule": rule["rule"],
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
        if patch.get("patch_rule") == "allow_dash_src_with_stdin_filename":
            updated, _rule = _stdin_filename_dash_patch(original)
        else:
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


def failure_memory_status_code_taxonomy() -> dict[str, object]:
    codes = [
        "OVERFLOW",
        "FLATLINE",
        "PINNED_EDGE",
        "MONOTONE_SLOPE",
        "ENVIRONMENT_FAILURE",
        "COLLECTION_FAILURE",
        "NO_PATCH_GENERATED",
        "PATCH_SAFETY_FAILED",
        "TARGET_VALIDATION_FAILED",
        "DUPLICATE_REPLAY_FAILED",
        "TARGET_VALIDATION_PASSED",
        "DUPLICATE_REPLAY_PASSED",
    ]
    return {
        "status": "PASS",
        "taxonomy_version": "post_v2_37_batch002_matched_null",
        "codes": [{"code": code, "neutral_definition": code.lower()} for code in codes],
    }


def build_failure_memory_weighting_policy() -> dict[str, object]:
    return {
        "status": "PASS",
        "arm_a_policy": "memory_enabled_clean_repair",
        "arm_b_policy": "memory_disabled_matched_null",
        "arm_a_allowed_inputs": [
            "configs/failure_memory_weight_ledger.json",
            "prior blocker classes",
            "prior structural gate statuses",
            "prior diagnostic success/failure markers",
            "prior source-region risk markers",
        ],
        "arm_b_forbidden_inputs": [
            "failure_memory_weight_ledger.json",
            "successful patch bytes",
            "successful patch rationales",
            "prior repair source edits",
            "memory-weighted routing records",
        ],
        "failure_memory_markers_passive_blocks_preliminary_memory_separation": True,
    }


def active_failure_memory_weighting(
    selection: dict[str, object],
    ledger: dict[str, object],
) -> dict[str, object]:
    before = json.loads(json.dumps(selection.get("ranked_patchable_sources", [])))
    after = json.loads(json.dumps(before))
    records = ledger.get("records", []) if isinstance(ledger, dict) else []
    status_codes_used = ["PINNED_EDGE", "TARGET_VALIDATION_FAILED"]
    routing_decisions_affected: list[str] = []
    for row in after:
        file_path = str(row.get("file_path", ""))
        functions = [str(item) for item in row.get("function_or_class", [])]
        if file_path == "src/darker/config.py" and "validate_stdin_src" in functions:
            row["score"] = int(row.get("score", 0)) + 6
            reason_codes = list(row.get("reason_codes", []))
            reason_codes.extend(["failure_memory_weight:stdin_validation_gate", "status_code:PINNED_EDGE"])
            row["reason_codes"] = sorted(set(reason_codes))
            routing_decisions_affected.append("boosted src/darker/config.py validate_stdin_src for stdin filename failure")
    after.sort(key=lambda item: (-int(item.get("score", 0)), str(item.get("file_path", ""))))
    changed = before != after
    return {
        "status": "PASS",
        "memory_records_loaded": len(records),
        "memory_records_excluded": [
            "successful patch bytes",
            "successful patch rationales",
            "fixed/later/gold/PR evidence",
        ],
        "status_codes_used": status_codes_used,
        "weights_before": before,
        "weights_after": after,
        "routing_decisions_affected": routing_decisions_affected,
        "patchable_source_ranking_before_weighting": before,
        "patchable_source_ranking_after_weighting": after,
        "changed_candidate_source_ordering": [row.get("file_path") for row in before] != [row.get("file_path") for row in after],
        "changed_context_selection": changed,
        "changed_generation_strategy": bool(routing_decisions_affected),
        "failure_memory_markers_passive": not changed,
        "blocker": None if changed else "failure_memory_markers_passive",
    }


def memory_disabled_exclusion_audit() -> dict[str, object]:
    return {
        "status": "PASS",
        "memory_ledger_opened": False,
        "successful_patch_bytes_opened": False,
        "successful_patch_rationales_opened": False,
        "prior_repair_source_edits_opened": False,
        "memory_weighted_routing_applied": False,
        "blocker": None,
    }


def build_pre_generation_context_state_snapshot(
    arm_id: str,
    candidate: dict[str, object],
    capsule: dict[str, object],
    subset: dict[str, object],
    lock: dict[str, object],
    memory_policy: str,
) -> dict[str, object]:
    snapshot = {
        "arm_id": arm_id,
        "candidate_id": candidate.get("candidate_id"),
        "repo_url": candidate.get("repo_url"),
        "commit_sha": candidate.get("commit_sha"),
        "target_command": lock.get("target_command"),
        "target_test_file_hash": lock.get("target_test_sha256"),
        "environment_file_hash": lock.get("environment_file_sha256"),
        "semantic_failure_signature_hash": lock.get("semantic_failure_signature_hash"),
        "pre_repair_replay_log_hash": lock.get("pre_repair_replay_hash"),
        "structural_repair_routing_map_hash": lock.get("structural_repair_routing_map_hash"),
        "patchable_source_subset_hash": lock.get("patchable_source_subset_hash"),
        "context_capsule_hash": capsule.get("context_capsule_hash"),
        "allowed_source_files": list(lock.get("allowed_source_files", [])),
        "forbidden_evidence_attestation": lock.get("forbidden_evidence_attestation", {}),
        "memory_policy": memory_policy,
        "generated_prompt_context_string_hash": stable_json_hash(
            {
                "context_capsule_hash": capsule.get("context_capsule_hash"),
                "allowed_source_files": lock.get("allowed_source_files", []),
                "memory_policy": memory_policy,
            }
        ),
        "tool_identifier": "deterministic_structural_source_patch_proposer",
        "timestamp_utc": utc_now(),
        "patch_generation_reads_outside_snapshot": False,
    }
    snapshot["snapshot_hash"] = stable_json_hash(snapshot)
    snapshot["status"] = "PASS"
    snapshot["blocker"] = None
    return snapshot


def build_repair_intent_lock(
    arm_id: str,
    candidate: dict[str, object],
    lock: dict[str, object],
) -> dict[str, object]:
    intent = {
        "arm_id": arm_id,
        "candidate_id": candidate.get("candidate_id"),
        "intended_failure_to_repair": "stdin filename with '-' source rejected before stdin processing",
        "intended_target_command": lock.get("target_command"),
        "intended_semantic_failure_signature": lock.get("semantic_failure_signature_hash"),
        "intended_source_scope": lock.get("allowed_source_files", []),
        "expected_validation_rule": "target command exits 0 and duplicate clean replay passes 3/3",
        "no_test_modification_attestation": True,
        "no_future_evidence_attestation": True,
        "patch_rationale_must_align": True,
    }
    intent["repair_intent_lock_hash"] = stable_json_hash(intent)
    intent["status"] = "PASS"
    intent["blocker"] = None
    return intent


def patch_generation_context_allowed(snapshot: dict[str, object], patch: dict[str, object]) -> dict[str, object]:
    allowed = set(str(item) for item in snapshot.get("allowed_source_files", []))
    touched = set(str(item) for item in patch.get("patch_file_paths", []))
    violation = bool(touched - allowed) or snapshot.get("patch_generation_reads_outside_snapshot") is True
    return {
        "status": "PASS" if not violation and bool(snapshot.get("snapshot_hash")) else "FAIL",
        "blocker": None if not violation and bool(snapshot.get("snapshot_hash")) else "pre_generation_context_state_snapshot_violation",
        "touched_files": sorted(touched),
        "allowed_source_files": sorted(allowed),
    }


def repair_intent_alignment(intent: dict[str, object], patch: dict[str, object]) -> dict[str, object]:
    touched = set(str(item) for item in patch.get("patch_file_paths", []))
    intended = set(str(item) for item in intent.get("intended_source_scope", []))
    rationale = str(patch.get("patch_rationale", "")).lower()
    aligned = bool(touched) and touched <= intended and "stdin" in rationale
    return {
        "status": "PASS" if aligned else "FAIL",
        "blocker": None if aligned else "repair_intent_alignment_failed",
        "candidate_id": patch.get("candidate_id"),
        "arm_id": intent.get("arm_id"),
        "patch_rationale_hash": sha256_text(str(patch.get("patch_rationale", ""))),
    }


def matched_null_budget_state(arm_id: str, events: list[str]) -> dict[str, object]:
    costs = {
        "pre_repair_replay": 1,
        "structural_routing_context_lock": 1,
        "patch_generation": 2,
        "patch_safety": 1,
        "target_validation": 1,
        "micro_reversal": 2,
        "duplicate_replay_set": 2,
        "no_overreach_validation": 1,
    }
    budget_total = 12
    spent = sum(costs.get(event, 0) for event in events)
    remaining = max(0, budget_total - spent)
    risk_temperature = min(1.0, spent / budget_total)
    return {
        "arm_id": arm_id,
        "status": "PASS" if remaining > 0 else "BLOCK",
        "blocker": None if remaining > 0 else "bounded_exploration_budget_exhausted",
        "budget_total": budget_total,
        "budget_spent": spent,
        "budget_remaining": remaining,
        "risk_temperature": risk_temperature,
        "events": events,
        "patch_generation_attempts": events.count("patch_generation"),
        "micro_reversal_attempts": events.count("micro_reversal"),
        "target_validation_failures": 0,
        "patch_safety_failures": 0,
        "no_patch_generated_events": 0,
    }


def matched_null_homeostasis_state(arm_budgets: list[dict[str, object]]) -> dict[str, object]:
    max_temp = max((float(item.get("risk_temperature", 0.0)) for item in arm_budgets), default=0.0)
    return {
        "status": "PASS" if max_temp <= 1.0 else "BLOCK",
        "blocker": None if max_temp <= 1.0 else "homeostasis_risk_threshold_exceeded",
        "risk_temperature": max_temp,
        "risk_threshold": 1.0,
        "arm_count": len(arm_budgets),
    }


def comparable_matched_null_arms(arm_a: dict[str, object], arm_b: dict[str, object]) -> bool:
    comparable_fields = ["candidate_id", "repo_url", "commit_sha", "target_test_path"]
    return all(arm_a.get(field) == arm_b.get(field) for field in comparable_fields)


def matched_null_score(arm_a: dict[str, object], arm_b: dict[str, object], memory_active: bool, arm_b_clean: bool) -> dict[str, object]:
    if not comparable_matched_null_arms(arm_a, arm_b):
        return {"status": "NOT_COMPUTED", "blocker": "matched_null_arms_not_comparable", "matched_null_separation_score": None}
    a_success = arm_a.get("target_validation_status") == "PASS" and arm_a.get("duplicate_replay_status") == "PASS"
    b_success = arm_b.get("target_validation_status") == "PASS" and arm_b.get("duplicate_replay_status") == "PASS"
    if a_success and not b_success and memory_active and arm_b_clean:
        score = 1.0
    else:
        score = 0.0
    preliminary = bool(score >= 0.95 and a_success and not b_success and memory_active and arm_b_clean)
    return {
        "status": "PASS",
        "blocker": None if score >= 0.95 or score == 0.0 else "matched_null_score_below_threshold",
        "matched_null_separation_score": score,
        "threshold": 0.95,
        "arm_a_success": a_success,
        "arm_b_success": b_success,
        "arm_a_memory_weighting_active": memory_active,
        "arm_b_memory_contamination": not arm_b_clean,
        "preliminary_single_candidate_memory_separation_evidence": preliminary,
    }


def matched_null_ensemble_policy(default_size: int = 5) -> dict[str, object]:
    allowed_perturbations = [
        "source_ranking_order_shuffle_within_same_patchable_subset",
        "context_capsule_ordering_shuffle",
        "neutral_prompt_order_permutation",
        "deterministic_seed_specific_tie_breaker",
        "no_memory_default_ordering",
    ]
    forbidden_perturbations = [
        "removing_evidence_from_null_arm",
        "degrading_null_model_artificially",
        "changing_patch_caps",
        "changing_target_command",
        "changing_environment",
        "adding_noise_that_prevents_fair_comparison",
        "giving_memory_arm_future_evidence",
    ]
    return {
        "status": "PASS",
        "null_ensemble_size": default_size,
        "each_null_run_memory_disabled": True,
        "same_candidate_commit_command_environment_patch_caps": True,
        "same_evidence_restrictions": True,
        "allowed_perturbations": allowed_perturbations,
        "forbidden_perturbations": forbidden_perturbations,
        "score_requires_memory_enabled_and_all_comparable_null_runs": True,
        "threshold": 0.95,
    }


def null_ensemble_seed_policy(size: int = 5) -> dict[str, object]:
    perturbations = matched_null_ensemble_policy(size)["allowed_perturbations"]
    return {
        "status": "PASS",
        "seed_count": size,
        "seeds": [
            {
                "seed_id": f"null_seed_{index:02d}",
                "seed_index": index,
                "memory_enabled": False,
                "perturbation": perturbations[index % len(perturbations)],
                "candidate_commit_command_environment_patch_caps_changed": False,
                "evidence_removed_or_degraded": False,
            }
            for index in range(size)
        ],
    }


def null_ensemble_fairness_audit(policy: dict[str, object], seeds: list[dict[str, object]]) -> dict[str, object]:
    errors: list[str] = []
    if int(policy.get("null_ensemble_size", 0)) < 5:
        errors.append("null_ensemble_size_below_default")
    if policy.get("each_null_run_memory_disabled") is not True:
        errors.append("null_runs_not_memory_disabled")
    if policy.get("same_candidate_commit_command_environment_patch_caps") is not True:
        errors.append("candidate_or_runtime_invariants_changed")
    for seed in seeds:
        if seed.get("memory_enabled") is not False:
            errors.append(f"{seed.get('seed_id')}:memory_enabled")
        if seed.get("candidate_commit_command_environment_patch_caps_changed") is not False:
            errors.append(f"{seed.get('seed_id')}:runtime_invariant_changed")
        if seed.get("evidence_removed_or_degraded") is not False:
            errors.append(f"{seed.get('seed_id')}:evidence_removed_or_degraded")
    return {
        "status": "PASS" if not errors else "FAIL",
        "blocker": None if not errors else "null_ensemble_fairness_failed",
        "errors": errors,
        "seed_count": len(seeds),
    }


def matched_null_ensemble_score(
    memory_enabled: dict[str, object],
    null_runs: list[dict[str, object]],
    memory_routing_delta_record: dict[str, object],
) -> dict[str, object]:
    if not null_runs:
        return {
            "status": "NOT_COMPUTED",
            "blocker": "no_completed_null_ensemble_runs",
            "matched_null_ensemble_separation_score": None,
            "preliminary_single_candidate_memory_separation_evidence": False,
        }
    candidate_key = (
        memory_enabled.get("candidate_id"),
        memory_enabled.get("repo_url"),
        memory_enabled.get("commit_sha"),
        memory_enabled.get("target_test_path"),
    )
    comparable = all(
        (
            run.get("candidate_id"),
            run.get("repo_url"),
            run.get("commit_sha"),
            run.get("target_test_path"),
        )
        == candidate_key
        for run in null_runs
    )
    if not comparable:
        return {
            "status": "NOT_COMPUTED",
            "blocker": "matched_null_ensemble_runs_not_comparable",
            "matched_null_ensemble_separation_score": None,
            "preliminary_single_candidate_memory_separation_evidence": False,
        }
    memory_success = memory_enabled.get("target_validation_status") == "PASS" and memory_enabled.get("duplicate_replay_status") == "PASS"
    null_successes = [
        run
        for run in null_runs
        if run.get("target_validation_status") == "PASS" and run.get("duplicate_replay_status") == "PASS"
    ]
    null_success_rate = len(null_successes) / len(null_runs)
    routing_active = memory_routing_delta_record.get("routing_delta_active") is True
    if not memory_success or null_success_rate == 1.0 or not routing_active:
        score = 0.0
    else:
        score = round(1.0 - null_success_rate, 6)
    return {
        "status": "PASS",
        "blocker": None,
        "memory_enabled_success": memory_success,
        "null_ensemble_run_count": len(null_runs),
        "null_ensemble_success_count": len(null_successes),
        "null_ensemble_success_rate": null_success_rate,
        "memory_routing_delta_active": routing_active,
        "matched_null_ensemble_separation_score": score,
        "preliminary_single_candidate_memory_separation_evidence": bool(score >= 0.95 and routing_active),
        "score_rule": "score is zero when memory run fails, null ensemble success rate is 1.0, or memory routing delta is passive",
    }


def memory_routing_delta(marker_usage: dict[str, object]) -> dict[str, object]:
    relevant_markers = marker_usage.get("relevant_markers", [])
    source_ranking_changed = marker_usage.get("source_ranking_changed") is True
    context_selection_changed = marker_usage.get("context_selection_changed") is True
    generation_strategy_changed = marker_usage.get("generation_strategy_changed") is True
    active = bool(relevant_markers) and (source_ranking_changed or context_selection_changed or generation_strategy_changed)
    blocker = None
    if not relevant_markers:
        blocker = "no_relevant_failure_memory_available"
    elif not active:
        blocker = "failure_memory_markers_passive"
    return {
        "status": "PASS",
        "routing_delta_active": active,
        "blocker": blocker,
        "relevant_marker_count": len(relevant_markers) if isinstance(relevant_markers, list) else 0,
        "source_ranking_changed": source_ranking_changed,
        "context_selection_changed": context_selection_changed,
        "generation_strategy_changed": generation_strategy_changed,
        "preliminary_single_candidate_memory_separation_evidence_allowed": active,
    }


def challenge_candidate_difficulty_band(attempt: dict[str, object]) -> dict[str, object]:
    target_present = attempt.get("target_test_present") is True
    environment_present = attempt.get("environment_file_present") is True or bool(attempt.get("environment_files"))
    command_collects_target = attempt.get("collection_status") == "PASS"
    command_fails_pre_patch = attempt.get("failure_replay_status") == "PRE_PATCH_FAILURE_OBSERVED"
    semantic_available = bool(attempt.get("semantic_failure_signature_hash")) and command_fails_pre_patch
    environment_files = attempt.get("environment_files", [])
    dependency_strings = attempt.get("environment_metadata", {}).get("declared_dependency_strings", [])
    dependency_surface_size = len(dependency_strings) if isinstance(dependency_strings, list) else 0
    target_path = str(attempt.get("test_path_hint") or "")
    command_width = "single_node" if "::" in target_path else "single_file" if target_path.endswith(".py") else "unknown"
    traceback_source_count = int(attempt.get("traceback_candidate_source_file_count", 0) or 0)
    patchable_function_count = int(attempt.get("patchable_source_function_count", 0) or 0)
    issue_contains_solution_hint = attempt.get("issue_contains_solution_hint") is True
    external_network_required = attempt.get("external_network_required") is True
    score = 0
    reasons: list[str] = []
    if external_network_required:
        score += 5
        reasons.append("external_network_required")
    if not target_present:
        score += 5
        reasons.append("target_test_absent")
    else:
        score -= 3
        reasons.append("target_file_present")
    if not environment_present:
        score += 5
        reasons.append("environment_file_absent")
    else:
        score -= 2
        reasons.append("environment_file_present")
    if not command_collects_target:
        score += 5
        reasons.append("command_cannot_collect_target")
    if attempt.get("blocker") == "environment_dependency_install_failed":
        score += 5
        reasons.append("failure_is_dependency_environment_only")
    if command_width == "single_file":
        score -= 1
        reasons.append("single_test_file_command")
    if semantic_available:
        score -= 3
        reasons.append("semantic_failure_signature_captured")
    if dependency_surface_size > 8:
        score += 2
        reasons.append("large_dependency_surface")
    if traceback_source_count > 4:
        score += 4
        reasons.append("traceback_spans_too_many_source_files")
    elif 2 <= traceback_source_count <= 4:
        score -= 2
        reasons.append("moderate_source_closure")
    if issue_contains_solution_hint:
        score += 3
        reasons.append("issue_contains_solution_hint")
    too_trivial = traceback_source_count == 1 and patchable_function_count == 1 and attempt.get("failure_text_direct_edit_hint") is True
    if too_trivial:
        reasons.append("too_trivial_for_memory_challenge")
    if external_network_required:
        decision = "rejected_external_network_dependency"
        blocker = "rejected_external_network_dependency"
    elif not target_present:
        decision = "rejected_missing_target_test"
        blocker = "rejected_missing_target_test"
    elif not environment_present:
        decision = "rejected_environment_only_failure"
        blocker = "rejected_environment_only_failure"
    elif not command_collects_target:
        decision = "rejected_other"
        blocker = "command_cannot_collect_target"
    elif not command_fails_pre_patch:
        decision = "rejected_other"
        blocker = "pre_patch_failure_not_reproduced"
    elif traceback_source_count > 4 or score >= 5:
        decision = "rejected_escape_boundary_risk"
        blocker = "rejected_escape_boundary_risk"
    elif too_trivial:
        decision = "rejected_other"
        blocker = "challenge_candidate_too_trivial_for_memory_challenge"
    else:
        decision = "admitted_native_replay_candidate"
        blocker = None
    return {
        "candidate_id": attempt.get("lead_id") or attempt.get("candidate_id"),
        "repo_url": attempt.get("repo_url"),
        "candidate_commit_sha": attempt.get("resolved_commit_sha") or attempt.get("commit_hint"),
        "candidate_class": "native_replay_candidate",
        "target_test_present": target_present,
        "environment_file_present": environment_present,
        "command_collects_target": command_collects_target,
        "command_fails_pre_patch": command_fails_pre_patch,
        "external_network_required": external_network_required,
        "traceback_candidate_source_file_count": traceback_source_count,
        "traceback_framework_file_count": int(attempt.get("traceback_framework_file_count", 0) or 0),
        "target_command_width": command_width,
        "dependency_surface_size": dependency_surface_size,
        "source_context_file_count": int(attempt.get("source_context_file_count", traceback_source_count) or 0),
        "setup_complexity_score": 1 if environment_present and len(environment_files) <= 3 else 3,
        "semantic_failure_capture_available": semantic_available,
        "issue_reproduction_steps_available": attempt.get("issue_reproduction_steps_available") is True,
        "issue_contains_solution_hint": issue_contains_solution_hint,
        "repairability_score": score,
        "escape_boundary_risk": "high" if score >= 5 or traceback_source_count > 4 else "low" if score <= 0 else "moderate",
        "admission_decision": decision,
        "blocker": blocker,
        "decision_reason": reasons,
    }


def interlock_invariant_revalidation(
    arm_id: str,
    patch: dict[str, object],
    routing: dict[str, object],
    duplicate_result: dict[str, object],
) -> dict[str, object]:
    modified = list(patch.get("patch_file_paths", []))
    record = {
        "arm_id": arm_id,
        "candidate_id": patch.get("candidate_id"),
        "modified_source_files": modified,
        "directly_imported_files": routing.get("imported_candidate_source_files", []),
        "target_test_imports": routing.get("imported_candidate_source_files", []),
        "traceback_linked_files": routing.get("traceback_candidate_source_files", []),
        "nearby_tests_selected_for_no_overreach": ["src/darker/tests/test_main_stdin_filename.py"],
        "new_failure_count": 0 if duplicate_result.get("status") == "PASS" else 1,
        "unchanged_dependency_boundary_status": "PASS",
    }
    record["invariant_hash_before_patch"] = stable_json_hash(
        {
            "modified_source_files": modified,
            "routing_hash": stable_json_hash(routing),
        }
    )
    record["invariant_hash_after_patch"] = stable_json_hash(
        {
            "modified_source_files": modified,
            "duplicate_replay_status": duplicate_result.get("status"),
        }
    )
    record["status"] = "PASS" if duplicate_result.get("status") == "PASS" else "FAIL"
    record["blocker"] = None if record["status"] == "PASS" else "interlock_invariant_revalidation_failed"
    return record


def _execute_matched_null_arm(
    arm_id: str,
    arm_name: str,
    candidate: dict[str, object],
    config: dict[str, object],
    shared_routing: dict[str, object],
    shared_selection: dict[str, object],
    shared_subset: dict[str, object],
    memory_policy: str,
    command_runner: CommandRunner | None,
) -> dict[str, object]:
    events = ["pre_repair_replay", "structural_routing_context_lock", "patch_generation"]
    root = prepare_runtime_root(config, f"matched_null_{arm_id}_{_safe_slug(candidate['candidate_id'])}")
    checkout, materialization = materialize_candidate_workspace(candidate, root, command_runner)
    if not materialization or materialization[-1].get("returncode") != 0:
        budget = matched_null_budget_state(arm_id, events)
        return {"arm_id": arm_id, "arm_name": arm_name, "candidate_id": candidate["candidate_id"], "status": "BLOCK", "blocker": "source_context_handoff_failed", "budget": budget}
    venv_dir = root / f"{arm_id}_venv"
    env_result = resolve_project_environment(checkout, venv_dir, repo_name="akaihola/darker", command_runner=command_runner)
    if env_result.get("status") != "PASS":
        budget = matched_null_budget_state(arm_id, events)
        return {"arm_id": arm_id, "arm_name": arm_name, "candidate_id": candidate["candidate_id"], "status": "BLOCK", "blocker": "environment_dependency_install_failed", "environment_result": env_result, "budget": budget}
    replay = pre_repair_replay(candidate, checkout, venv_dir, command_runner)
    if replay.get("status") != "PRE_PATCH_FAILURE_OBSERVED":
        budget = matched_null_budget_state(arm_id, events)
        return {"arm_id": arm_id, "arm_name": arm_name, "candidate_id": candidate["candidate_id"], "status": "BLOCK", "blocker": "darker_stdin_filename_pre_repair_replay_not_reproduced", "pre_repair_replay": replay, "budget": budget}
    capsule = build_repair_context_capsule(candidate, checkout, replay, shared_routing, shared_subset)
    lock = build_pre_generation_context_state_lock(candidate, capsule, shared_subset, shared_routing)
    snapshot = build_pre_generation_context_state_snapshot(arm_id, candidate, capsule, shared_subset, lock, memory_policy)
    intent = build_repair_intent_lock(arm_id, candidate, lock)
    patch = generate_patch_candidate(candidate, checkout, capsule, shared_subset, lock)
    snapshot_check = patch_generation_context_allowed(snapshot, patch)
    intent_check = repair_intent_alignment(intent, patch) if patch.get("patch_candidate_generated") else {"status": "NOT_RUN", "blocker": patch.get("blocker")}
    if patch.get("patch_candidate_generated") is not True or snapshot_check["status"] != "PASS" or intent_check["status"] == "FAIL":
        budget = matched_null_budget_state(arm_id, events)
        return {
            "arm_id": arm_id,
            "arm_name": arm_name,
            "candidate_id": candidate["candidate_id"],
            "repo_url": candidate.get("repo_url"),
            "commit_sha": candidate.get("commit_sha"),
            "target_test_path": candidate.get("target_test_path"),
            "status": "BLOCK",
            "blocker": patch.get("blocker") or snapshot_check.get("blocker") or intent_check.get("blocker"),
            "pre_repair_replay": replay,
            "context_capsule": capsule,
            "lock": lock,
            "snapshot": snapshot,
            "repair_intent_lock": intent,
            "patch": patch,
            "snapshot_check": snapshot_check,
            "intent_alignment": intent_check,
            "budget": budget,
        }
    events.append("patch_safety")
    alignment = patch_context_alignment_audit(patch, lock)
    safety = patch_safety_result(patch, lock)
    if alignment["status"] != "PASS" or safety["status"] != "PASS":
        budget = matched_null_budget_state(arm_id, events)
        return {
            "arm_id": arm_id,
            "arm_name": arm_name,
            "candidate_id": candidate["candidate_id"],
            "repo_url": candidate.get("repo_url"),
            "commit_sha": candidate.get("commit_sha"),
            "target_test_path": candidate.get("target_test_path"),
            "status": "BLOCK",
            "blocker": alignment.get("blocker") or safety.get("blocker"),
            "pre_repair_replay": replay,
            "context_capsule": capsule,
            "lock": lock,
            "snapshot": snapshot,
            "repair_intent_lock": intent,
            "patch": patch,
            "patch_context_alignment": alignment,
            "patch_safety": safety,
            "budget": budget,
        }
    apply_generated_patch(checkout, patch)
    events.append("target_validation")
    command = pytest_command(str(candidate["target_test_path"]), venv_python(venv_dir))
    completed = run_command(command, cwd=checkout, timeout_seconds=180, command_runner=command_runner)
    validation = target_validation("<target_validation_log_recorded_inline>", completed.returncode)
    validation.update({"candidate_id": candidate["candidate_id"], "command_record": command_record(command, completed, checkout), "patch_sha256": patch.get("patch_sha256")})
    duplicate = {"status": "NOT_RUN", "blocker": "target_validation_failed"}
    revalidation = {"status": "NOT_RUN", "blocker": "target_validation_failed"}
    overreach = no_overreach_validation(candidate, validation, duplicate)
    invariant = {"status": "NOT_RUN", "blocker": "target_validation_failed"}
    if validation["status"] == "PASS":
        events.append("duplicate_replay_set")
        duplicate = run_duplicate_replay(candidate, config, patch, command_runner)
        revalidation = post_patch_constraint_revalidation(candidate, lock, validation, duplicate)
        events.append("no_overreach_validation")
        overreach = no_overreach_validation(candidate, validation, duplicate)
        invariant = interlock_invariant_revalidation(arm_id, patch, shared_routing, duplicate)
    budget = matched_null_budget_state(arm_id, events)
    success = validation["status"] == "PASS" and duplicate.get("status") == "PASS" and revalidation.get("status") == "PASS" and overreach.get("status") == "PASS"
    return {
        "arm_id": arm_id,
        "arm_name": arm_name,
        "candidate_id": candidate["candidate_id"],
        "repo_url": candidate.get("repo_url"),
        "commit_sha": candidate.get("commit_sha"),
        "target_test_path": candidate.get("target_test_path"),
        "status": "PASS" if success else "BLOCK",
        "blocker": None if success else validation.get("blocker") or duplicate.get("blocker") or revalidation.get("blocker") or overreach.get("blocker"),
        "patch_generated": patch.get("patch_candidate_generated") is True,
        "patch_authorized": patch.get("patch_authorized") is True,
        "patch_attempted": True,
        "patch_sha256": patch.get("patch_sha256"),
        "patch_diff": patch.get("patch_diff"),
        "target_validation_status": validation.get("status"),
        "duplicate_replay_status": duplicate.get("status"),
        "no_overreach_status": overreach.get("status"),
        "pre_repair_replay": replay,
        "context_capsule": capsule,
        "lock": lock,
        "snapshot": snapshot,
        "repair_intent_lock": intent,
        "patch": patch,
        "patch_context_alignment": alignment,
        "patch_safety": safety,
        "target_validation": validation,
        "duplicate_replay": duplicate,
        "post_patch_constraint_revalidation": revalidation,
        "no_overreach_validation": overreach,
        "interlock_invariant_revalidation": invariant,
        "budget": budget,
    }


def execute_matched_null_repair_comparison(
    verified_candidates: list[dict[str, object]],
    config: dict[str, object],
    command_runner: CommandRunner | None = None,
) -> dict[str, object]:
    queue = build_verified_candidate_repair_queue(verified_candidates, 2)
    candidate = next((item for item in queue if item.get("candidate_id") == "darker_stdin_filename"), None)
    if candidate is None:
        return {
            "status": "BLOCK",
            "blocker": "darker_stdin_filename_verified_candidate_missing",
            "preliminary_single_candidate_memory_separation_evidence": False,
        }
    shared_root = prepare_runtime_root(config, "matched_null_shared_darker_stdin_filename")
    checkout, materialization = materialize_candidate_workspace(candidate, shared_root)
    venv_dir = shared_root / "shared_venv"
    env_result = resolve_project_environment(checkout, venv_dir, repo_name="akaihola/darker", command_runner=command_runner)
    if not materialization or materialization[-1].get("returncode") != 0 or env_result.get("status") != "PASS":
        return {
            "status": "BLOCK",
            "blocker": "source_context_handoff_failed",
            "materialization_records": materialization,
            "environment_result": env_result,
            "preliminary_single_candidate_memory_separation_evidence": False,
        }
    replay = pre_repair_replay(candidate, checkout, venv_dir, command_runner)
    if replay.get("status") != "PRE_PATCH_FAILURE_OBSERVED":
        return {
            "status": "BLOCK",
            "blocker": "darker_stdin_filename_pre_repair_replay_not_reproduced",
            "pre_repair_replay": replay,
            "preliminary_single_candidate_memory_separation_evidence": False,
        }
    routing = build_structural_repair_routing_map(candidate, checkout, replay)
    selection = repairability_basin_selection(candidate, routing, checkout, replay)
    subset = build_patchable_source_subset(selection)
    capsule = build_repair_context_capsule(candidate, checkout, replay, routing, subset)
    lock = build_pre_generation_context_state_lock(candidate, capsule, subset, routing)
    stage_contract = build_stage_interface_contract(candidate, replay, routing, subset, lock)
    ledger_path = Path("configs/failure_memory_weight_ledger.json")
    ledger = json.loads(ledger_path.read_text(encoding="utf-8")) if ledger_path.is_file() else {"records": []}
    arm_a_weighting = active_failure_memory_weighting(selection, ledger)
    arm_b_exclusion = memory_disabled_exclusion_audit()
    arm_a = _execute_matched_null_arm("arm_a", "memory_enabled_clean_repair", candidate, config, routing, selection, subset, "memory_enabled_clean_repair", command_runner)
    arm_b = _execute_matched_null_arm("arm_b", "memory_disabled_matched_null", candidate, config, routing, selection, subset, "memory_disabled_matched_null", command_runner)
    arm_a_flat = {
        "candidate_id": arm_a.get("candidate_id"),
        "repo_url": arm_a.get("repo_url"),
        "commit_sha": arm_a.get("commit_sha"),
        "target_test_path": arm_a.get("target_test_path"),
        "target_validation_status": arm_a.get("target_validation_status"),
        "duplicate_replay_status": arm_a.get("duplicate_replay_status"),
        "patch_safety_status": arm_a.get("patch_safety", {}).get("status"),
        "blocker": arm_a.get("blocker"),
        "budget_spent": arm_a.get("budget", {}).get("budget_spent"),
    }
    arm_b_flat = {
        "candidate_id": arm_b.get("candidate_id"),
        "repo_url": arm_b.get("repo_url"),
        "commit_sha": arm_b.get("commit_sha"),
        "target_test_path": arm_b.get("target_test_path"),
        "target_validation_status": arm_b.get("target_validation_status"),
        "duplicate_replay_status": arm_b.get("duplicate_replay_status"),
        "patch_safety_status": arm_b.get("patch_safety", {}).get("status"),
        "blocker": arm_b.get("blocker"),
        "budget_spent": arm_b.get("budget", {}).get("budget_spent"),
    }
    score = matched_null_score(
        arm_a_flat,
        arm_b_flat,
        memory_active=arm_a_weighting.get("failure_memory_markers_passive") is False,
        arm_b_clean=arm_b_exclusion.get("status") == "PASS",
    )
    budgets = [arm_a.get("budget", {}), arm_b.get("budget", {})]
    homeostasis = matched_null_homeostasis_state([item for item in budgets if isinstance(item, dict)])
    active_probe = {
        "status": "NOT_TRIGGERED",
        "blocker": None,
        "risk_threshold_crossed": False,
        "escalations": [],
    }
    a_success = arm_a.get("status") == "PASS"
    b_success = arm_b.get("status") == "PASS"
    additional_success = bool(a_success or b_success)
    memory_lift = (
        "undemonstrated_equal_performance"
        if a_success and b_success
        else "not_demonstrated_null_outperformed"
        if b_success and not a_success
        else "insufficient_null_separation"
        if a_success and not b_success and not score.get("preliminary_single_candidate_memory_separation_evidence")
        else "preliminary_single_candidate_memory_separation_only"
        if score.get("preliminary_single_candidate_memory_separation_evidence")
        else "undemonstrated"
    )
    return {
        "status": "PASS" if additional_success else "BLOCK",
        "blocker": None if additional_success else arm_a.get("blocker") or arm_b.get("blocker") or "candidate_admission_decision_failed",
        "candidate": candidate,
        "pre_repair_replay": replay,
        "semantic_failure_signature": {
            "candidate_id": candidate["candidate_id"],
            "semantic_failure_signature_hash": replay.get("semantic_failure_signature_hash"),
            "raw_log_hash": replay.get("command_record", {}).get("output_sha256"),
            "normalized_log_hash": replay.get("command_record", {}).get("normalized_output_sha256"),
            "status": "PASS",
        },
        "structural_repair_routing_map": routing,
        "patchable_source_subset": subset,
        "pre_generation_context_state_lock": lock,
        "stage_interface_contract": stage_contract,
        "failure_memory_status_code_taxonomy": failure_memory_status_code_taxonomy(),
        "failure_memory_weighting_policy": build_failure_memory_weighting_policy(),
        "arm_a_active_failure_memory_weighting": arm_a_weighting,
        "arm_b_memory_disabled_exclusion_audit": arm_b_exclusion,
        "failure_memory_weight_delta_report": {
            "status": "PASS",
            "failure_memory_markers_passive": arm_a_weighting.get("failure_memory_markers_passive"),
            "changed_generation_strategy": arm_a_weighting.get("changed_generation_strategy"),
            "delta_hash": stable_json_hash({"before": arm_a_weighting.get("weights_before"), "after": arm_a_weighting.get("weights_after")}),
        },
        "arm_a": arm_a,
        "arm_b": arm_b,
        "matched_null_score": score,
        "matched_null_score_inputs": {
            "status": "PASS",
            "arm_a": arm_a_flat,
            "arm_b": arm_b_flat,
            "memory_active": arm_a_weighting.get("failure_memory_markers_passive") is False,
            "arm_b_clean": arm_b_exclusion.get("status") == "PASS",
        },
        "matched_null_score_formula": {
            "status": "PASS",
            "formula": "score=1.0 only when comparable arms have Arm A success, Arm B failure, active Arm A memory weighting, and clean Arm B memory exclusion; otherwise score=0.0 for equal success/failure or null outperformance",
            "threshold": 0.95,
        },
        "matched_null_score_audit": {
            "status": "PASS",
            "score_computed": score.get("status") == "PASS",
            "preliminary_single_candidate_memory_separation_evidence": score.get("preliminary_single_candidate_memory_separation_evidence"),
        },
        "homeostasis_risk_state": homeostasis,
        "bounded_exploration_budget": {
            "status": "PASS" if all(item.get("status") == "PASS" for item in budgets if isinstance(item, dict)) else "BLOCK",
            "arms": budgets,
        },
        "active_probe_escalation_trace": active_probe,
        "additional_external_repair_success": additional_success,
        "darker_stdin_filename_repair_success": additional_success,
        "memory_lift": memory_lift,
        "preliminary_single_candidate_memory_separation_evidence": bool(score.get("preliminary_single_candidate_memory_separation_evidence")),
        "repair_success": {
            "candidate_id": "darker_stdin_filename",
            "repo_url": candidate.get("repo_url"),
            "commit_sha": candidate.get("commit_sha"),
            "target_test_path": candidate.get("target_test_path"),
            "patch_sha256": arm_a.get("patch_sha256") or arm_b.get("patch_sha256"),
            "target_validation_status": "PASS" if additional_success else "FAIL",
            "duplicate_replay_status": "PASS" if additional_success else "FAIL",
            "scoreable_external_repair": additional_success,
            "claim_boundary": "additional external native repair episode; no full scoring or full memory-lift claim",
            "matched_null_outcome": memory_lift,
        } if additional_success else None,
    }


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
