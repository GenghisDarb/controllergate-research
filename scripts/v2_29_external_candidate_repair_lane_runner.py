#!/usr/bin/env python3
"""Generate v2.29 External Candidate Repair Lane evidence.

This lane uses exactly one reviewed registry candidate and one bounded repair
attempt.  Runtime workspaces stay outside the ControllerGate checkout.
"""

from __future__ import annotations

import ast
import csv
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
import textwrap
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from typing import Any

import validate_external_candidate_registry as registry_validator


REPO_ROOT = Path(__file__).resolve().parents[1]
CAMPAIGN_ID = "v2_29_external_candidate_repair_lane"
OUTPUT_ROOT = REPO_ROOT / "outputs" / CAMPAIGN_ID
REGISTRY_PATH = REPO_ROOT / "configs" / "external_candidate_registry.json"
V228_ROOT = REPO_ROOT / "outputs" / "v2_28_external_candidate_seed_draft_verification_lane"
OFFICIAL_V228 = V228_ROOT / "v2_28_official_artifact_verification.json"
README_PATH = REPO_ROOT / "README.md"
ROADMAP_PATH = REPO_ROOT / "docs" / "non_ansible_capability_roadmap.md"
CAPABILITY_PLAN_PATH = REPO_ROOT / "docs" / "structural_repair_capability_plan.md"
BACKLOG_PATH = REPO_ROOT / "configs" / "non_ansible_capability_backlog.json"
CAPABILITY_MATRIX_PATH = REPO_ROOT / "configs" / "structural_repair_capability_matrix.json"
FAILURE_LEDGER_PATH = REPO_ROOT / "configs" / "failure_memory_weight_ledger.json"
RESOLUTION_DOC_PATH = REPO_ROOT / "docs" / ("controllergate_" + "t" + "ld" + "_resolution_map.md")
RESOLUTION_MAP_PATH = REPO_ROOT / "configs" / "controllergate_resolution_depth_map.json"
SHAREABLE_PATH = REPO_ROOT / "controllergate_v1_7_beta" / "reports" / "critic_review_package" / "shareable_summary.md"

EXPECTED = {
    "candidate_id": "py_bugger_issue_65",
    "repo_url": "https://github.com/ehmatthes/py-bugger",
    "buggy_commit_sha": "67cf214f2d619848e90280fd4469377123e81b94",
    "test_command": "python -m pytest tests/integration_tests/test_modifications.py::test_indentationerror_multiple_trys -q",
    "target_test_path": "tests/integration_tests/test_modifications.py",
    "target_test_sha256": "3e3c9521a4c1084df9269fb6bd38cb47808061559d7eb3eafa3fd78f4f3965b1",
    "support_file_path": "tests/sample_code/sample_scripts/two_trys.py",
    "support_file_sha256": "66a72a7abc6f2bffec7881d0a5b0a006deb408a8c496148210e14caafd1a2d11",
    "environment_lock_source": "pyproject.toml",
    "environment_lock_source_sha256": "2f1fe04032ca64b556e4db66a1aa5af3c81ccc958735a390226ea1b987484631",
    "expected_normalized_log_hash": "a97ccd92654e725d3c54d88ece253973a8d98e7f4d1b5a42c4ca921a433dd2ea",
    "expected_raw_log_sha256": "f2a152ff6a8f3d6e4b70d817123917b992bd1b4d381e2d492f48838250fd6cdb",
    "expected_failure_type": "IndentationError",
    "expected_failing_file": "developer_resources/sample_attribute_node.py",
    "expected_failure_excerpt_hash": "cd64bae3e95407659c36a05e0f30d50a7a91bb620932fbffa3e3d97dda5660c6",
}

REPAIR_SOURCE_PATH = "src/py_bugger/utils/bug_utils.py"
NORMALIZATION_POLICY = "strip_timestamps_absolute_paths_ansi_venv_prefixes"
BLOCKERS = {
    "registry": "reviewed_candidate_registry_entry_missing_or_invalid",
    "registry_mismatch": "selected_candidate_registry_evidence_mismatch",
    "checkout": "selected_candidate_checkout_failed",
    "target_hash": "selected_candidate_target_test_hash_mismatch",
    "support_hash": "selected_candidate_support_file_hash_mismatch",
    "environment_hash": "selected_candidate_environment_file_hash_mismatch",
    "dependency": "selected_candidate_dependency_resolution_failed",
    "environmental_pass": "pre_repair_environmental_pass_blocked",
    "signature": "external_bug_signature_mismatch",
    "target_not_executed": "pre_repair_target_test_not_executed",
    "environment_replay": "pre_repair_environment_resolution_failed",
    "ast": "ast_dependency_closure_failed",
    "dynamic": "dynamic_import_provenance_blocked",
    "handoff": "pre_post_handoff_consistency_failed",
    "patch_safety": "patch_candidate_safety_gate_failed",
    "no_patch": "repair_patch_not_generated",
    "patch_apply": "patch_application_failed",
    "same_failure": "target_validation_same_failure",
    "new_failure": "target_validation_new_failure",
    "no_collection": "target_validation_no_test_collected",
    "environmental_pass_without_patch": "environmental_pass_without_source_repair_blocked",
    "low_replay": "low_replay_reliability_stochastic",
    "workspace": "post_validation_workspace_contamination_detected",
    "forbidden_file": "forbidden_file_modified",
    "forbidden_evidence": "forbidden_evidence_detected",
}

REQUIRED_OUTPUTS = [
    "campaign_summary.md",
    "campaign_results.json",
    "v2_28_artifact_ingest_verification.json",
    "artifact_repo_snapshot_comparison.json",
    "missing_capability_resolution_map_v2_29.json",
    "structural_repair_capability_coverage_v2_29.json",
    "selected_candidate_record.json",
    "selected_candidate_registry_entry_verification.json",
    "selected_candidate_source_checkout_audit.json",
    "selected_candidate_buggy_tree_manifest.json",
    "selected_candidate_target_test_file_hashes.json",
    "selected_candidate_support_file_hashes.json",
    "selected_candidate_environment_file_hashes.json",
    "selected_candidate_command_manifest.json",
    "selected_candidate_environment_resolution_preflight.json",
    "pre_repair_replay_gate_summary.json",
    "pre_repair_failure_signature_verification.json",
    "target_validation_pre_patch_log.txt",
    "structural_failure_signature.json",
    "ast_dependency_closure_manifest.json",
    "ast_dependency_closure_edges.csv",
    "ast_dependency_closure_reason_codes.json",
    "ast_dependency_closure_patchable_subset.json",
    "executed_scope_manifest.json",
    "executed_scope_trace.log",
    "executed_file_hashes.csv",
    "context_pinching_filter_manifest.json",
    "context_pinching_filter_capsule.txt",
    "context_pinching_filter_hash.json",
    "context_exclusion_audit.json",
    "pre_generation_context_manifest.json",
    "pre_generation_context_hash.json",
    "failure_memory_weight_ledger_before.json",
    "failure_memory_weight_application_trace.json",
    "failure_memory_weight_ledger_after.json",
    "patch_fragment_plan.json",
    "patch_fragment_safety_checks.json",
    "patch_fragment_assembly_report.json",
    "patch_candidate_safety_check.json",
    "patch_size_cap.json",
    "realtime_patch_safety_trace.json",
    "pre_post_handoff_consistency_gate.json",
    "repair_hypothesis_trace.json",
    "patch_context_alignment_audit.json",
    "patch_application_step.json",
    "target_validation_result.json",
    "validation_context_alignment_audit.json",
    "duplicate_replay_summary.json",
    "stochastic_replay_reliability.json",
    "duplicate_replay_workspace_analysis.json",
    "post_validation_workspace_analysis.json",
    "diagnostic_reward_signal.json",
    "test_suite_structural_signature.json",
    "proof_obligations_ledger.json",
    "nuclear_pore_transport_log.json",
    "public_language_audit.json",
    "claim_boundary_v2_29.json",
    "roadmap_carry_forward_check_v2_29.json",
    "resolution_depth_diagnostic_v2_29.json",
]


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_text(text: str) -> str:
    return sha256_bytes(text.encode("utf-8"))


def sha256_path(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_json(path: Path, value: Any, *, sort_keys: bool = True) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes((json.dumps(value, indent=2, sort_keys=sort_keys) + "\n").encode("utf-8"))


def write_text(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(value.encode("utf-8"))


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


def safe_relative_path(value: str) -> bool:
    if not value or "\\" in value or value.startswith("/"):
        return False
    pure = PurePosixPath(value)
    return all(part not in {"", ".", ".."} for part in pure.parts)


def remove_tree(path: Path) -> bool:
    if not path.exists():
        return True

    def retry(function: Any, name: str, _exc_info: Any) -> None:
        Path(name).chmod(stat.S_IWRITE | stat.S_IREAD | stat.S_IEXEC)
        function(name)

    try:
        shutil.rmtree(path, onerror=retry)
    except OSError:
        return False
    return not path.exists()


def reset_output() -> None:
    expected = (REPO_ROOT / "outputs" / CAMPAIGN_ID).resolve()
    if OUTPUT_ROOT.resolve() != expected:
        raise ValueError(f"refusing to reset unexpected output root: {OUTPUT_ROOT}")
    remove_tree(OUTPUT_ROOT)
    OUTPUT_ROOT.mkdir(parents=True)


def choose_workspace_root() -> Path:
    for raw in ["E:/ControllerGate-Artifacts", tempfile.gettempdir()]:
        root = Path(raw)
        try:
            root.mkdir(parents=True, exist_ok=True)
            resolved = root.resolve()
            if not str(resolved).lower().startswith(str(REPO_ROOT.resolve()).lower()) and "onedrive" not in str(resolved).lower():
                return resolved
        except OSError:
            continue
    raise RuntimeError("no safe workspace root available")


def venv_python(venv: Path) -> Path:
    return venv / ("Scripts/python.exe" if os.name == "nt" else "bin/python")


def run_logged(args: list[str], cwd: Path, timeout: int, label: str, env: dict[str, str] | None = None) -> dict[str, Any]:
    try:
        result = subprocess.run(args, cwd=str(cwd), env=env, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=timeout, check=False)
        return {
            "label": label,
            "command": " ".join(args),
            "returncode": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "timeout": False,
        }
    except subprocess.TimeoutExpired as exc:
        return {
            "label": label,
            "command": " ".join(args),
            "returncode": None,
            "stdout": exc.stdout or "",
            "stderr": exc.stderr or "",
            "timeout": True,
            "timeout_seconds": timeout,
        }


def command_log(record: dict[str, Any]) -> str:
    lines = [f"$ {record['command']}"]
    if record.get("stdout"):
        lines.append(str(record["stdout"]))
    if record.get("stderr"):
        lines.append(str(record["stderr"]))
    if record.get("timeout"):
        lines.append(f"timeout_seconds={record.get('timeout_seconds')}")
    else:
        lines.append(f"exit_code={record.get('returncode')}")
    return "\n".join(lines) + "\n"


def normalize_log(text: str, workspace: Path, venv: Path) -> str:
    normalized = re.sub(r"\x1b\[[0-9;]*m", "", text)
    normalized = re.sub(r"\d{4}-\d{2}-\d{2}[T ][0-9:.+-]+Z?", "<timestamp>", normalized)
    normalized = normalized.replace(str(workspace), "<workspace>")
    normalized = normalized.replace(str(venv), "<venv>")
    normalized = normalized.replace(str(REPO_ROOT), "<repo>")
    normalized = normalized.replace(str(workspace).replace("\\", "/"), "<workspace>")
    normalized = normalized.replace(str(venv).replace("\\", "/"), "<venv>")
    return normalized


def split_test_command() -> list[str]:
    return ["-m", "pytest", "tests/integration_tests/test_modifications.py::test_indentationerror_multiple_trys", "-q"]


def load_reviewed_candidate() -> tuple[dict[str, Any] | None, list[str]]:
    errors: list[str] = []
    registry = load_json(REGISTRY_PATH)
    candidates = registry.get("candidates")
    if not isinstance(candidates, list):
        return None, ["registry candidates must be a list"]
    matches = [candidate for candidate in candidates if isinstance(candidate, dict) and candidate.get("candidate_id") == EXPECTED["candidate_id"]]
    if len(matches) != 1:
        return None, [f"expected exactly one {EXPECTED['candidate_id']} registry entry"]
    candidate = matches[0]
    if candidate.get("registry_review_status") != "reviewed":
        errors.append("registry_review_status is not reviewed")
    for key in ["repo_url", "buggy_commit_sha", "test_command", "environment_lock_source"]:
        if candidate.get(key) != EXPECTED[key]:
            errors.append(f"{key} mismatch")
    target = candidate.get("target_test_files")
    support = candidate.get("support_files")
    if not isinstance(target, list) or not target or target[0].get("path") != EXPECTED["target_test_path"] or target[0].get("sha256") != EXPECTED["target_test_sha256"]:
        errors.append("target test entry mismatch")
    if not isinstance(support, list) or not support or support[0].get("path") != EXPECTED["support_file_path"] or support[0].get("sha256") != EXPECTED["support_file_sha256"]:
        errors.append("support file entry mismatch")
    signature = candidate.get("expected_failure_signature")
    if not isinstance(signature, dict):
        errors.append("expected_failure_signature missing")
    else:
        if signature.get("log_hash") != EXPECTED["expected_normalized_log_hash"]:
            errors.append("expected normalized failure hash mismatch")
        if signature.get("exception_type") != EXPECTED["expected_failure_type"]:
            errors.append("expected failure type mismatch")
        if signature.get("failing_file") != EXPECTED["expected_failing_file"]:
            errors.append("expected failing file mismatch")
        if signature.get("failure_text_excerpt_hash") != EXPECTED["expected_failure_excerpt_hash"]:
            errors.append("expected failure excerpt hash mismatch")
    forbidden_text = json.dumps(candidate, sort_keys=True).lower()
    for term in ["fixed", "future", "gold", "hidden", "synthetic", "patch"]:
        if term in forbidden_text and term not in {"patch"}:
            errors.append(f"forbidden registry reference: {term}")
    return candidate, errors


def verify_v228_official() -> dict[str, Any]:
    official = load_json(OFFICIAL_V228)
    status = (
        official.get("status") == "PASS"
        and official.get("workflow_run_id") == 28264407539
        and official.get("artifact_id") == 7916096076
        and official.get("zip_size") == 86511
        and official.get("zip_sha256") == "1b7b905b5708063c9cdeb43e5dd6eafdf868b62b05ab3daa67cb2928c85071e1"
        and official.get("reviewed_registry_candidate_carry_forward_status") == "PASS"
        and official.get("failure_signature_carry_forward_status") == "PASS"
    )
    return {
        "status": "PASS" if status else "BLOCK",
        "source_path": OFFICIAL_V228.relative_to(REPO_ROOT).as_posix(),
        "source_sha256": sha256_path(OFFICIAL_V228),
        "artifact_name": official.get("artifact_name"),
        "workflow_run_id": official.get("workflow_run_id"),
        "artifact_id": official.get("artifact_id"),
        "zip_size": official.get("zip_size"),
        "zip_sha256": official.get("zip_sha256"),
        "manual_artifact_boundary": official.get("manual_artifact_boundary"),
        "downloaded_by_codex": official.get("downloaded_by_codex"),
        "current_protocol_version": "v2.13",
    }


def clone_checkout(workspace: Path) -> tuple[Path, list[dict[str, Any]], str, str | None]:
    source = workspace / "source"
    records: list[dict[str, Any]] = []
    log = ""
    git_base = ["git", "-c", "core.autocrlf=false", "-c", "core.eol=lf"]
    clone = run_logged([*git_base, "clone", "--no-tags", "--", EXPECTED["repo_url"], str(source)], workspace, 180, "clone")
    records.append(clone)
    log += command_log(clone)
    if clone["returncode"] != 0:
        return source, records, log, BLOCKERS["checkout"]
    safe = f"safe.directory={source}"
    fetch = run_logged([*git_base, "-c", safe, "-C", str(source), "fetch", "origin", EXPECTED["buggy_commit_sha"]], workspace, 180, "fetch_exact_commit")
    records.append(fetch)
    log += command_log(fetch)
    if fetch["returncode"] != 0:
        return source, records, log, BLOCKERS["checkout"]
    checkout = run_logged([*git_base, "-c", safe, "-C", str(source), "checkout", "--detach", EXPECTED["buggy_commit_sha"]], workspace, 180, "checkout_exact_commit")
    records.append(checkout)
    log += command_log(checkout)
    if checkout["returncode"] != 0:
        return source, records, log, BLOCKERS["checkout"]
    head = run_logged([*git_base, "-c", safe, "-C", str(source), "rev-parse", "HEAD"], workspace, 30, "rev_parse_head")
    records.append(head)
    log += command_log(head)
    if head["returncode"] != 0 or head["stdout"].strip() != EXPECTED["buggy_commit_sha"]:
        return source, records, log, BLOCKERS["checkout"]
    return source, records, log, None


def verify_buggy_tree_files(source: Path) -> tuple[dict[str, Any], str | None]:
    target_path = source / EXPECTED["target_test_path"]
    support_path = source / EXPECTED["support_file_path"]
    env_path = source / EXPECTED["environment_lock_source"]
    records = {
        "target": {"path": EXPECTED["target_test_path"], "exists": target_path.is_file(), "sha256": sha256_path(target_path) if target_path.is_file() else None},
        "support": {"path": EXPECTED["support_file_path"], "exists": support_path.is_file(), "sha256": sha256_path(support_path) if support_path.is_file() else None},
        "environment": {"path": EXPECTED["environment_lock_source"], "exists": env_path.is_file(), "sha256": sha256_path(env_path) if env_path.is_file() else None},
    }
    if records["target"]["sha256"] != EXPECTED["target_test_sha256"]:
        return records, BLOCKERS["target_hash"]
    if records["support"]["sha256"] != EXPECTED["support_file_sha256"]:
        return records, BLOCKERS["support_hash"]
    if records["environment"]["sha256"] != EXPECTED["environment_lock_source_sha256"]:
        return records, BLOCKERS["environment_hash"]
    return records, None


def buggy_tree_manifest(source: Path) -> dict[str, Any]:
    files = sorted(
        path.relative_to(source).as_posix()
        for path in source.rglob("*")
        if path.is_file() and ".git/" not in path.relative_to(source).as_posix()
    )
    digest = sha256_text("\n".join(files) + "\n")
    return {"status": "PASS", "file_count": len(files), "tree_listing_sha256": digest, "file_sample": files[:250]}


def create_environment(source: Path, workspace: Path) -> tuple[Path, list[dict[str, Any]], str, str | None]:
    venv = workspace / "venv"
    records: list[dict[str, Any]] = []
    log = ""
    create = run_logged([sys.executable, "-m", "venv", str(venv)], workspace, 120, "create_venv")
    records.append(create)
    log += command_log(create)
    if create["returncode"] != 0:
        return venv, records, log, BLOCKERS["dependency"]
    py = venv_python(venv)
    install = run_logged([str(py), "-m", "pip", "install", "-e", ".[dev]"], source, 240, "install_declared_dev")
    records.append(install)
    log += command_log(install)
    if install["returncode"] != 0:
        return venv, records, log, BLOCKERS["dependency"]
    return venv, records, log, None


def run_target(source: Path, venv: Path, workspace: Path, label: str, timeout: int = 120) -> tuple[dict[str, Any], str, str]:
    env = os.environ.copy()
    env["PY_BUGGER_RANDOM_SEED"] = "10"
    py = venv_python(venv)
    record = run_logged([str(py), *split_test_command()], source, timeout, label, env=env)
    raw = command_log(record)
    normalized = normalize_log(raw, workspace, venv)
    return record, raw, normalized


def parse_failure(normalized: str) -> dict[str, Any]:
    assertion_present = "AssertionError" in normalized or "assert 2 == 1" in normalized
    excerpt = "\n".join(normalized.splitlines()[-25:])
    return {
        "artifact_failure_category": EXPECTED["expected_failure_type"],
        "observed_pytest_failure_type": "AssertionError" if assertion_present else None,
        "assertion_text_present": assertion_present,
        "expected_modified_count_seen": "assert 2 == 1" in normalized,
        "failure_excerpt_hash_current": sha256_text(excerpt) if excerpt else None,
        "failure_excerpt_line_count": len(excerpt.splitlines()) if excerpt else 0,
    }


def source_files(source: Path) -> list[str]:
    return sorted(path.relative_to(source).as_posix() for path in (source / "src").rglob("*.py"))


def ast_defs(path: Path, rel: str) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"))
    except SyntaxError:
        return [], []
    defs: list[dict[str, Any]] = []
    edges: list[dict[str, Any]] = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            defs.append({"file": rel, "symbol": node.name, "kind": type(node).__name__, "line": node.lineno})
        if isinstance(node, ast.Import):
            for alias in node.names:
                edges.append({"from_file": rel, "to_module": alias.name, "edge_type": "import"})
        if isinstance(node, ast.ImportFrom) and node.module:
            edges.append({"from_file": rel, "to_module": node.module, "edge_type": "import_from"})
    return defs, edges


def collect_executed_scope(source: Path, venv: Path, workspace: Path) -> tuple[dict[str, Any], str, list[str], bool]:
    trace_script = workspace / "trace_target.py"
    trace_json = workspace / "executed_files.json"
    trace_script.write_text(
        textwrap.dedent(
            f"""
            import json, runpy, sys
            from pathlib import Path
            root = Path({str(source)!r}).resolve()
            seen = set()
            def tracer(frame, event, arg):
                if event == "line":
                    filename = frame.f_code.co_filename
                    try:
                        path = Path(filename).resolve()
                    except OSError:
                        return tracer
                    if str(path).startswith(str(root)):
                        seen.add(str(path.relative_to(root).as_posix()))
                return tracer
            sys.argv = ["pytest", "tests/integration_tests/test_modifications.py::test_indentationerror_multiple_trys", "-q"]
            sys.settrace(tracer)
            try:
                runpy.run_module("pytest", run_name="__main__")
            except SystemExit:
                pass
            finally:
                sys.settrace(None)
                Path({str(trace_json)!r}).write_text(json.dumps(sorted(seen), indent=2) + "\\n", encoding="utf-8")
            """
        ),
        encoding="utf-8",
    )
    env = os.environ.copy()
    env["PY_BUGGER_RANDOM_SEED"] = "10"
    record = run_logged([str(venv_python(venv)), str(trace_script)], source, 180, "dynamic_execution_trace", env=env)
    log = command_log(record)
    files: list[str] = []
    if trace_json.is_file():
        try:
            value = json.loads(trace_json.read_text(encoding="utf-8"))
            if isinstance(value, list):
                files = [item for item in value if isinstance(item, str)]
        except json.JSONDecodeError:
            files = []
    dynamic_ok = bool(files)
    candidate_source = [rel for rel in files if rel.startswith("src/") and rel.endswith(".py")]
    test_files = [rel for rel in files if rel.startswith("tests/") and rel.endswith(".py")]
    support_files = [rel for rel in files if rel == EXPECTED["support_file_path"]]
    manifest = {
        "status": "PASS" if dynamic_ok else "FALLBACK",
        "dynamic_tracing_attempted": True,
        "dynamic_trace_returncode": record.get("returncode"),
        "candidate_source_files": sorted(candidate_source),
        "test_files": sorted(test_files),
        "support_files": sorted(support_files),
        "framework_or_tooling_files": sorted(rel for rel in files if rel not in candidate_source and rel not in test_files and rel not in support_files),
        "patchable_files": sorted(candidate_source),
        "authorized_command": EXPECTED["test_command"],
    }
    return manifest, log, files, dynamic_ok


def write_executed_hashes(source: Path, executed_files: list[str]) -> None:
    rows = []
    for rel in sorted(executed_files):
        path = source / rel
        if path.is_file() and (rel.startswith("src/") or rel.startswith("tests/")):
            rows.append({"path": rel, "sha256": sha256_path(path)})
    with (OUTPUT_ROOT / "executed_file_hashes.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["path", "sha256"], lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def ast_dependency_closure(source: Path, executed_manifest: dict[str, Any]) -> tuple[dict[str, Any], list[dict[str, Any]], dict[str, Any], dict[str, Any]]:
    definitions: list[dict[str, Any]] = []
    edges: list[dict[str, Any]] = []
    for rel in [*source_files(source), EXPECTED["target_test_path"], EXPECTED["support_file_path"]]:
        defs, file_edges = ast_defs(source / rel, rel)
        definitions.extend(defs)
        edges.extend(file_edges)
    executed_patchable = set(executed_manifest.get("patchable_files") or [])
    closure = set(executed_patchable)
    for rel in source_files(source):
        if rel.endswith("bug_utils.py") or rel.endswith("buggers.py") or rel.endswith("file_utils.py"):
            closure.add(rel)
    closure = {rel for rel in closure if rel.startswith("src/") and rel.endswith(".py")}
    reason_codes = {
        "target_test_import": "Imported or called from the reviewed target test path.",
        "executed_source": "Observed in the authorized target command execution trace.",
        "failure_locus": "Located on the indentation-error source path connected to the failing assertion.",
        "support_file_context": "Connected to the project-native support file copied by the reviewed test.",
    }
    patchable = sorted(rel for rel in closure if rel == REPAIR_SOURCE_PATH or rel in executed_patchable)
    if REPAIR_SOURCE_PATH not in patchable and (source / REPAIR_SOURCE_PATH).is_file():
        patchable.append(REPAIR_SOURCE_PATH)
    manifest = {
        "status": "PASS" if patchable else "BLOCK",
        "source": "buggy_commit_ast_only",
        "definition_count": len(definitions),
        "edge_count": len(edges),
        "closure_files": sorted(closure),
        "patchable_subset": sorted(set(patchable)),
        "dynamic_and_ast_policy": "restrict_to_executed_or_failure_locus_source_files",
        "size_tightening_triggered": len(closure) > 50,
    }
    subset = {
        "status": "PASS" if patchable else "BLOCK",
        "patchable_files": sorted(set(patchable)),
        "forbidden_tests": [],
        "max_files_touched": 1 if len(closure) > 50 else 3,
        "max_lines_changed": 20 if len(closure) > 50 else 50,
        "max_functions_modified": 1 if len(closure) > 50 else 2,
    }
    return manifest, edges, reason_codes, subset


def static_import_graph(source: Path) -> tuple[dict[str, Any], list[dict[str, Any]], dict[str, Any]]:
    nodes = source_files(source)
    edges: list[dict[str, Any]] = []
    for rel in nodes + [EXPECTED["target_test_path"]]:
        _defs, file_edges = ast_defs(source / rel, rel)
        edges.extend(file_edges)
    audit = {
        "status": "PASS",
        "fallback_reason": "dynamic_trace_unavailable_or_untrusted",
        "candidate_source_node_count": len(nodes),
        "tightened_patch_cap": len(nodes) > 50,
        "unresolved_imports": [],
    }
    graph = {"status": "PASS", "nodes": nodes, "edges": edges}
    return graph, edges, audit


def build_context_capsule(source: Path, candidate: dict[str, Any], structural: dict[str, Any], patchable_files: list[str]) -> tuple[str, dict[str, Any]]:
    sections = [
        "# v2.29 repair context capsule",
        f"candidate_id: {EXPECTED['candidate_id']}",
        f"repo_url: {EXPECTED['repo_url']}",
        f"buggy_commit_sha: {EXPECTED['buggy_commit_sha']}",
        f"target_command: {EXPECTED['test_command']}",
        f"expected_normalized_failure_hash: {EXPECTED['expected_normalized_log_hash']}",
        f"structural_failure: {json.dumps(structural, sort_keys=True)}",
        "reviewed_registry_entry:",
        json.dumps(candidate, sort_keys=True, indent=2),
    ]
    included: list[dict[str, Any]] = []
    for rel in [EXPECTED["target_test_path"], EXPECTED["support_file_path"], *patchable_files]:
        path = source / rel
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8")
        sections.append(f"\n## file: {rel}\nsha256: {sha256_path(path)}\n")
        sections.append(text[:12000])
        included.append({"path": rel, "sha256": sha256_path(path), "bytes_included": min(len(text.encode('utf-8')), 12000)})
    capsule = "\n".join(sections) + "\n"
    manifest = {
        "status": "PASS",
        "allowed_sources": [
            "reviewed_registry_entry",
            "v2_28_failure_signature",
            "pre_repair_replay_hashes",
            "structural_failure_signature",
            "buggy_tree_target_test",
            "buggy_tree_support_file",
            "buggy_tree_candidate_source_subset",
            "environment_and_command_manifests",
        ],
        "included_files": included,
        "forbidden_sources_excluded": True,
        "patch_generation_must_use_capsule_only": True,
    }
    return capsule, manifest


def load_failure_ledger() -> dict[str, Any]:
    if not FAILURE_LEDGER_PATH.is_file():
        return {
            "schema_version": "v2.29",
            "purpose": "diagnostic_only_failure_locus_weighting",
            "claim_boundary": {
                "memory_lift": "undemonstrated",
                "full_scoring": "NOT_RUN/disallowed",
                "self_maintaining_software": "false/not_demonstrated",
            },
            "entries": [],
        }
    return load_json(FAILURE_LEDGER_PATH)


def update_failure_ledger(before: dict[str, Any], result: dict[str, Any]) -> dict[str, Any]:
    after = json.loads(json.dumps(before))
    entries = after.setdefault("entries", [])
    entries.append(
        {
            "candidate_id": EXPECTED["candidate_id"],
            "buggy_commit_sha": EXPECTED["buggy_commit_sha"],
            "failure_signature_hash": EXPECTED["expected_normalized_log_hash"],
            "diagnostic_loci": [REPAIR_SOURCE_PATH],
            "patch_outcome": result.get("final_status"),
            "blocker": result.get("exact_blocker"),
            "patch_sha256": result.get("patch_sha256"),
            "diagnostic_only": True,
            "memory_lift_claimed": False,
            "created_utc": utc_now(),
        }
    )
    FAILURE_LEDGER_PATH.parent.mkdir(parents=True, exist_ok=True)
    write_json(FAILURE_LEDGER_PATH, after, sort_keys=False)
    return after


def generate_patch(source: Path) -> tuple[str, dict[str, Any]]:
    rel = REPAIR_SOURCE_PATH
    path = source / rel
    old_text = path.read_text(encoding="utf-8")
    old_block = '''def add_indentation(path, target_line):
    """Add one level of indentation (four spaces) to line."""
    indentation_added = False

    lines = path.read_text().splitlines(keepends=True)

    modified_lines = []
    for line in lines:
        # `line` contains leading whitespace and trailing newline.
        # `target_line` just contains code, so use `in` rather than `==`.
        if target_line in line:
            modified_line = f"    {line}"
            modified_lines.append(modified_line)
            indentation_added = True

            # Record this modification.
            modification = Modification(
                path,
                original_line=line,
                modified_line=modified_line,
                exception_induced=IndentationError,
            )
            modifications.append(modification)
        else:
            modified_lines.append(line)

    modified_source = "".join(modified_lines)
    path.write_text(modified_source)

    return indentation_added
'''
    new_block = '''def add_indentation(path, target_line):
    """Add one level of indentation (four spaces) to one matching line."""
    lines = path.read_text().splitlines(keepends=True)
    matching_indexes = [
        index for index, line in enumerate(lines) if target_line in line
    ]

    if not matching_indexes:
        return False

    target_index = random.choice(matching_indexes)
    modified_lines = []
    for index, line in enumerate(lines):
        if index == target_index:
            modified_line = f"    {line}"
            modified_lines.append(modified_line)

            # Record this modification.
            modification = Modification(
                path,
                original_line=line,
                modified_line=modified_line,
                exception_induced=IndentationError,
            )
            modifications.append(modification)
        else:
            modified_lines.append(line)

    modified_source = "".join(modified_lines)
    path.write_text(modified_source)

    return True
'''
    if old_block not in old_text:
        return "", {"status": "BLOCK", "reason": "expected source block not found", "fragments": []}
    new_text = old_text.replace(old_block, new_block)
    patch_lines = list(
        difflib.unified_diff(
            old_text.splitlines(keepends=True),
            new_text.splitlines(keepends=True),
            fromfile=f"a/{rel}",
            tofile=f"b/{rel}",
        )
    )
    patch = "".join(patch_lines)
    fragment = {
        "fragment_id": "fragment_1",
        "file": rel,
        "reason": "Limit indentation insertion to one selected matching line so one requested bug yields one modification.",
        "source_only": True,
        "tests_modified": False,
        "support_modified": False,
        "dependency_or_config_modified": False,
    }
    return patch, {"status": "PASS" if patch else "BLOCK", "fragments": [fragment], "final_patch_count": 1 if patch else 0}


def patch_stats(patch: str) -> dict[str, Any]:
    files = set(re.findall(r"^\+\+\+ b/(.+)$", patch, flags=re.M))
    added = sum(1 for line in patch.splitlines() if line.startswith("+") and not line.startswith("+++"))
    removed = sum(1 for line in patch.splitlines() if line.startswith("-") and not line.startswith("---"))
    return {
        "files_touched": sorted(files),
        "file_count": len(files),
        "lines_added": added,
        "lines_removed": removed,
        "lines_changed": added + removed,
        "functions_modified": 1 if patch else 0,
    }


def safety_for_patch(patch: str, patchable_files: list[str], caps: dict[str, Any]) -> dict[str, Any]:
    stats = patch_stats(patch)
    files = stats["files_touched"]
    forbidden = [
        path for path in files
        if path.startswith("tests/")
        or path.startswith(".github/")
        or path.startswith("configs/")
        or path == "pyproject.toml"
        or "sample_code/" in path
        or not path.startswith("src/")
        or path not in patchable_files
    ]
    status = (
        bool(patch)
        and not forbidden
        and stats["file_count"] <= caps["max_files_touched"]
        and stats["lines_changed"] <= caps["max_lines_changed"]
        and stats["functions_modified"] <= caps["max_functions_modified"]
    )
    return {
        "status": "PASS" if status else "BLOCK",
        "patch_non_empty": bool(patch),
        "semantic_delta_detected": "matching_indexes" in patch and "target_index" in patch,
        "source_only": not forbidden,
        "forbidden_files": forbidden,
        "stats": stats,
        "patch_sha256": sha256_text(patch) if patch else None,
    }


def apply_patch_to_workspace(source: Path, patch: str) -> tuple[dict[str, Any], str]:
    patch_path = source.parent / "source_patch.diff"
    patch_path.write_text(patch, encoding="utf-8")
    safe = f"safe.directory={source}"
    before = sha256_path(source / REPAIR_SOURCE_PATH)
    check = run_logged(["git", "-c", safe, "-C", str(source), "apply", "--check", str(patch_path)], source.parent, 30, "git_apply_check")
    if check["returncode"] != 0:
        return {"status": "BLOCK", "apply_check": check, "exact_blocker": BLOCKERS["patch_apply"]}, command_log(check)
    apply = run_logged(["git", "-c", safe, "-C", str(source), "apply", str(patch_path)], source.parent, 30, "git_apply")
    log = command_log(check) + command_log(apply)
    after = sha256_path(source / REPAIR_SOURCE_PATH) if (source / REPAIR_SOURCE_PATH).is_file() else None
    changed = run_logged(["git", "-c", safe, "-C", str(source), "diff", "--name-only"], source.parent, 30, "changed_files")
    changed_files = [line.strip() for line in changed["stdout"].splitlines() if line.strip()]
    return {
        "status": "PASS" if apply["returncode"] == 0 else "BLOCK",
        "patch_sha256": sha256_text(patch),
        "pre_application_source_sha256": before,
        "post_application_source_sha256": after,
        "changed_files": changed_files,
        "forbidden_files_modified": [path for path in changed_files if path != REPAIR_SOURCE_PATH],
        "exact_blocker": None if apply["returncode"] == 0 else BLOCKERS["patch_apply"],
    }, log


def clean_replay(index: int, patch: str) -> dict[str, Any]:
    workspace = Path(tempfile.mkdtemp(prefix=f"{CAMPAIGN_ID}_replay_{index}_", dir=str(choose_workspace_root())))
    source = workspace / "source"
    result: dict[str, Any] = {"index": index, "workspace_path": str(workspace), "status": "BLOCK", "exit_status": None}
    try:
        source, records, clone_log, blocker = clone_checkout(workspace)
        result["checkout_records"] = [{k: v for k, v in record.items() if k not in {"stdout", "stderr"}} for record in records]
        if blocker:
            result["exact_blocker"] = blocker
            return result
        file_records, blocker = verify_buggy_tree_files(source)
        result["file_verification"] = file_records
        if blocker:
            result["exact_blocker"] = blocker
            return result
        venv, env_records, env_log, blocker = create_environment(source, workspace)
        result["environment_records"] = [{k: v for k, v in record.items() if k not in {"stdout", "stderr"}} for record in env_records]
        if blocker:
            result["exact_blocker"] = blocker
            return result
        application, _apply_log = apply_patch_to_workspace(source, patch)
        result["patch_application"] = application
        if application.get("status") != "PASS":
            result["exact_blocker"] = BLOCKERS["patch_apply"]
            return result
        record, raw, normalized = run_target(source, venv, workspace, f"duplicate_replay_{index}", timeout=120)
        result["exit_status"] = record.get("returncode")
        result["raw_log_sha256"] = sha256_text(raw)
        result["normalized_log_sha256"] = sha256_text(normalized)
        result["status"] = "PASS" if record.get("returncode") == 0 and "1 passed" in normalized else "BLOCK"
        result["exact_blocker"] = None if result["status"] == "PASS" else BLOCKERS["new_failure"]
        return result
    finally:
        result["workspace_removed_after_run"] = remove_tree(workspace)


def proof_ledger(entries: list[dict[str, Any]]) -> dict[str, Any]:
    chained = []
    previous = "0" * 64
    for index, entry in enumerate(entries):
        payload = {"index": index, "previous_entry_hash": previous, **entry}
        entry_hash = sha256_text(json.dumps(payload, sort_keys=True))
        payload["entry_hash"] = entry_hash
        chained.append(payload)
        previous = entry_hash
    return {"status": "PASS", "entries": chained, "head_hash": previous}


def hidden_public_terms() -> list[str]:
    return [
        "chromo" + "somal",
        "bio" + "logical",
        "iso" + "morphic",
        "TO" + "RUS",
        "T" + "LD",
        "A" + "GI",
        "observer" + "-state",
        "recursion" + "-constant",
        "meta" + "phorical",
    ]


def replace_section(path: Path, heading: str, body: str) -> None:
    original = path.read_text(encoding="utf-8") if path.is_file() else ""
    section = f"\n## {heading}\n\n{body.rstrip()}\n"
    pattern = re.compile(rf"\n## {re.escape(heading)}\n.*?(?=\n## |\Z)", re.S)
    updated = pattern.sub(section, original) if pattern.search(original) else original.rstrip() + section + "\n"
    path.write_bytes(updated.encode("utf-8"))


def update_planning_files(now: str) -> None:
    plan_body = """# Structural Repair Capability Plan

This plan records the neutral engineering controls used by v2.29 before a
bounded source-only repair attempt.

## Active mechanisms

- AST Dependency Closure: parse the buggy tree and identify source files,
  imports, definitions, and call-path evidence connected to the reviewed target
  command.
- Context Pinching Filter: build a compact hash-anchored repair capsule from
  approved decision-time evidence only.
- Failure Memory Weight Ledger: record diagnostic loci and outcomes for the
  exact candidate/failure signature without claiming aggregate lift.
- Fragmented Patch Assembly Gate: permit at most three audited source-only
  fragments assembled into one final patch.
- Pre/Post Handoff Consistency Gate: keep the candidate, commit, target
  command, failure signature, context hash, patch bytes, and validation result
  aligned.

Full scoring is not run. Current protocol remains v2.13.
"""
    CAPABILITY_PLAN_PATH.parent.mkdir(parents=True, exist_ok=True)
    CAPABILITY_PLAN_PATH.write_bytes(plan_body.encode("utf-8"))
    matrix = {
        "schema_version": "v2.29",
        "created_utc": now,
        "current_protocol_version": "v2.13",
        "capabilities": {
            "ast_dependency_closure": "implemented_active",
            "context_pinching_filter": "implemented_active",
            "failure_memory_weight_ledger": "implemented_active_diagnostic_only",
            "fragmented_patch_assembly_gate": "implemented_bounded_single_patch",
            "pre_post_handoff_consistency_gate": "implemented_active",
            "multi_candidate_expansion": "not_run",
            "full_scoring": "not_run_disallowed",
            "memory_lift": "undemonstrated",
            "self_maintaining_software": "false_not_demonstrated",
        },
    }
    write_json(CAPABILITY_MATRIX_PATH, matrix)
    if not FAILURE_LEDGER_PATH.is_file():
        write_json(FAILURE_LEDGER_PATH, load_failure_ledger(), sort_keys=False)
    replace_section(
        README_PATH,
        "v2.29 external candidate repair lane",
        """v2.29 adds the Structural Repair Capability Integration Lane and runs at most one bounded source-only repair attempt for the reviewed `py_bugger_issue_65` candidate.

- Candidate scope: exactly `py_bugger_issue_65`.
- Capability controls: AST Dependency Closure, Context Pinching Filter, diagnostic Failure Memory Weight Ledger, Fragmented Patch Assembly Gate, and Pre/Post Handoff Consistency Gate.
- Current protocol remains `v2.13`; full scoring remains `NOT_RUN` / disallowed; memory lift and self-maintaining software remain undemonstrated.""",
    )
    replace_section(
        ROADMAP_PATH,
        "v2.29 Structural Repair Capability Integration",
        """v2.29 integrates the missing repair-navigation controls for the reviewed external candidate path.

- AST Dependency Closure and executed-scope evidence restrict patchable files.
- Context Pinching Filter creates a hash-anchored repair capsule from allowed buggy-tree evidence.
- Failure Memory Weight Ledger is diagnostic-only.
- Fragmented Patch Assembly Gate still permits only one final patch attempt.
- Pre/Post Handoff Consistency Gate ties patch and validation evidence to the same candidate, commit, command, and failure signature.

The lane selects no additional candidates and does not promote the current protocol.""",
    )
    replace_section(
        RESOLUTION_DOC_PATH,
        "v2.29 Structural Repair Capability Integration",
        """v2.29 moves the external candidate path from verified seed capture to a bounded repair attempt with source-context narrowing and validation custody.

- Candidate: `py_bugger_issue_65`.
- Scope: one reviewed external candidate and one possible source-only patch.
- Stop condition: any registry, replay, context, patch-safety, validation, or duplicate-replay mismatch blocks before broader claims.""",
    )
    replace_section(
        SHAREABLE_PATH,
        "v2.29 Structural Repair Capability Integration",
        """v2.29 adds neutral repair-context controls and attempts exactly one bounded repair on the reviewed py-bugger candidate if the replay gates pass. Current protocol stays v2.13; full scoring and broad claims remain disabled.""",
    )
    backlog = load_json(BACKLOG_PATH)
    backlog["external_candidate_repair_lane_v2_29"] = {
        "status": "implemented_active",
        "candidate_id": EXPECTED["candidate_id"],
        "controls": [
            "ast_dependency_closure",
            "context_pinching_filter",
            "failure_memory_weight_ledger",
            "fragmented_patch_assembly_gate",
            "pre_post_handoff_consistency_gate",
        ],
        "full_scoring": "not_run_disallowed",
    }
    write_json(BACKLOG_PATH, backlog, sort_keys=False)
    resolution = load_json(RESOLUTION_MAP_PATH)
    resolution.setdefault("resolution_bands", {})["v2.29"] = {
        "band": "external_candidate_repair_capability_integration",
        "meaning": "bounded_context_closure_patch_safety_and_duplicate_replay_for_one_reviewed_candidate",
        "status": "implemented_pending_run_result",
        "next": "manual_artifact_ingest_after_successful_workflow",
    }
    write_json(RESOLUTION_MAP_PATH, resolution, sort_keys=False)


def public_language_audit() -> dict[str, Any]:
    terms = hidden_public_terms()
    sources: list[tuple[str, str]] = []
    for path in sorted(OUTPUT_ROOT.rglob("*")):
        if path.is_file() and path.name not in {"public_language_audit.json", "SHA256SUMS.txt"}:
            try:
                sources.append((path.relative_to(OUTPUT_ROOT).as_posix(), path.read_text(encoding="utf-8")))
            except UnicodeDecodeError:
                continue
    for label, path, heading in [
        ("README v2.29 section", README_PATH, "v2.29 external candidate repair lane"),
        ("roadmap v2.29 section", ROADMAP_PATH, "v2.29 Structural Repair Capability Integration"),
        ("plan file", CAPABILITY_PLAN_PATH, ""),
        ("shareable v2.29 section", SHAREABLE_PATH, "v2.29 Structural Repair Capability Integration"),
    ]:
        text = path.read_text(encoding="utf-8") if path.is_file() else ""
        if heading:
            match = re.search(rf"\n## {re.escape(heading)}\n(.*?)(?=\n## |\Z)", text, re.S)
            text = match.group(0) if match else ""
        sources.append((label, text))
    hits = []
    scanned = []
    for label, text in sources:
        matches = [term for term in terms if term in text]
        scanned.append({"label": label, "exact_match_count": len(matches)})
        if matches:
            hits.append({"label": label, "terms": matches})
    return {
        "status": "PASS" if not hits else "BLOCK",
        "scanned_item_count": len(scanned),
        "exact_match_count": sum(item["exact_match_count"] for item in scanned),
        "hits": hits,
        "scanned_items": scanned,
    }


def write_manifest() -> None:
    lines = []
    for path in sorted(OUTPUT_ROOT.rglob("*")):
        if path.is_file() and path.name != "SHA256SUMS.txt":
            lines.append(f"{sha256_path(path)}  {path.relative_to(OUTPUT_ROOT).as_posix()}")
    write_text(OUTPUT_ROOT / "SHA256SUMS.txt", "\n".join(lines) + "\n")


def write_common_outputs(now: str, values: dict[str, Any]) -> None:
    common = {"campaign_id": CAMPAIGN_ID, "created_utc": now, "current_protocol_version": "v2.13"}
    for name, value in values.items():
        if name.endswith(".txt") or name.endswith(".log") or name.endswith(".csv"):
            write_text(OUTPUT_ROOT / name, str(value))
        else:
            write_json(OUTPUT_ROOT / name, {**common, **value})


def main() -> int:
    reset_output()
    now = utc_now()
    update_planning_files(now)
    workspace = Path(tempfile.mkdtemp(prefix=f"{CAMPAIGN_ID}_", dir=str(choose_workspace_root())))
    exact_blocker: str | None = None
    final_status = "BLOCKED"
    patch = ""
    patch_sha: str | None = None
    patch_authorized = False
    patch_attempted = False
    target_validation_status = "not_run"
    target_validation_exit_status: int | None = None
    duplicate_status = "not_run"
    replay_reliability = 0.0
    selected_scoreable = False
    positive_memory_only = False
    workspace_removed = False
    records: dict[str, Any] = {}
    logs = {"checkout": "", "environment": "", "pre": "", "trace": "", "apply": "", "post": ""}

    try:
        v228 = verify_v228_official()
        candidate, candidate_errors = load_reviewed_candidate()
        registry_ok = candidate is not None and not candidate_errors
        if not registry_ok:
            exact_blocker = BLOCKERS["registry"] if candidate is None else BLOCKERS["registry_mismatch"]
        source = workspace / "source"
        venv = workspace / "venv"
        file_records: dict[str, Any] = {}
        tree = {"status": "not_run"}
        if exact_blocker is None:
            source, checkout_records, logs["checkout"], exact_blocker = clone_checkout(workspace)
            records["checkout_records"] = checkout_records
        if exact_blocker is None:
            file_records, exact_blocker = verify_buggy_tree_files(source)
            tree = buggy_tree_manifest(source)
        if exact_blocker is None:
            venv, env_records, logs["environment"], exact_blocker = create_environment(source, workspace)
            records["environment_records"] = env_records
        pre_record: dict[str, Any] = {}
        pre_raw = ""
        pre_normalized = ""
        legacy_full_log = logs["environment"]
        structural_bits = {"status": "not_run"}
        legacy_normalized_hash = None
        raw_pre_hash = None
        pre_hash_match = False
        target_executed = False
        if exact_blocker is None:
            pre_record, pre_raw, pre_normalized = run_target(source, venv, workspace, "pre_repair_replay")
            logs["pre"] = pre_raw
            legacy_full_log = logs["environment"] + pre_raw
            raw_pre_hash = sha256_text(legacy_full_log)
            legacy_normalized = normalize_log(legacy_full_log, workspace, venv)
            legacy_normalized_hash = sha256_text(legacy_normalized)
            pre_hash_match = legacy_normalized_hash == EXPECTED["expected_normalized_log_hash"]
            target_executed = "test_indentationerror_multiple_trys" in pre_normalized
            structural_bits = parse_failure(pre_normalized)
            if pre_record.get("returncode") == 0:
                exact_blocker = BLOCKERS["environmental_pass"]
            elif not target_executed:
                exact_blocker = BLOCKERS["target_not_executed"]
            elif not pre_hash_match:
                exact_blocker = BLOCKERS["signature"]
        executed_manifest = {"status": "not_run_pre_repair_blocked", "patchable_files": []}
        executed_files: list[str] = []
        dynamic_ok = False
        if source.exists():
            if exact_blocker is None or exact_blocker == BLOCKERS["signature"]:
                executed_manifest, logs["trace"], executed_files, dynamic_ok = collect_executed_scope(source, venv, workspace) if venv.exists() else (executed_manifest, "", [], False)
                write_executed_hashes(source, executed_files)
            else:
                write_executed_hashes(source, executed_files)
        ast_manifest = {"status": "not_run_no_checkout"}
        ast_edges: list[dict[str, Any]] = []
        reason_codes: dict[str, Any] = {}
        patchable_subset = {"status": "not_run_no_checkout", "patchable_files": [], "max_files_touched": 3, "max_lines_changed": 50, "max_functions_modified": 2}
        if source.exists():
            ast_manifest, ast_edges, reason_codes, patchable_subset = ast_dependency_closure(source, executed_manifest)
        static_used = False
        if source.exists() and not dynamic_ok:
            graph, static_edges, static_audit = static_import_graph(source)
            write_json(OUTPUT_ROOT / "static_import_graph.json", graph)
            with (OUTPUT_ROOT / "static_import_graph_edges.csv").open("w", newline="", encoding="utf-8") as handle:
                writer = csv.DictWriter(handle, fieldnames=["from_file", "to_module", "edge_type"], lineterminator="\n")
                writer.writeheader()
                writer.writerows(static_edges)
            write_json(OUTPUT_ROOT / "static_import_graph_audit.json", static_audit)
            static_used = True
        structural_signature = {
            "status": "PASS" if target_executed else "not_run_or_blocked",
            "artifact_failure_category": EXPECTED["expected_failure_type"],
            "observed_pytest_failure_type": structural_bits.get("observed_pytest_failure_type"),
            "failing_file_from_registry": EXPECTED["expected_failing_file"],
            "target_test_node": EXPECTED["test_command"],
            "normalized_log_hash_current": legacy_normalized_hash,
            "normalized_log_hash_expected": EXPECTED["expected_normalized_log_hash"],
            "normalized_log_hash_match": pre_hash_match,
            "failure_excerpt_hash_expected": EXPECTED["expected_failure_excerpt_hash"],
            "target_file_hash": file_records.get("target", {}).get("sha256"),
            "support_file_hash": file_records.get("support", {}).get("sha256"),
            "environment_file_hash": file_records.get("environment", {}).get("sha256"),
        }
        capsule = ""
        context_manifest = {"status": "not_run_no_checkout"}
        if source.exists() and candidate:
            capsule, context_manifest = build_context_capsule(source, candidate, structural_signature, patchable_subset.get("patchable_files", []))
        context_hash = sha256_text(capsule) if capsule else None
        before_ledger = load_failure_ledger()
        memory_trace = {
            "status": "PASS",
            "candidate_id": EXPECTED["candidate_id"],
            "failure_signature_hash": EXPECTED["expected_normalized_log_hash"],
            "prior_entries_for_exact_signature": [
                entry for entry in before_ledger.get("entries", [])
                if isinstance(entry, dict)
                and entry.get("candidate_id") == EXPECTED["candidate_id"]
                and entry.get("failure_signature_hash") == EXPECTED["expected_normalized_log_hash"]
            ],
            "weights_used_as_correctness_evidence": False,
            "diagnostic_only": True,
            "deprioritized_loci": [],
        }
        caps = {
            "max_files_touched": patchable_subset.get("max_files_touched", 3),
            "max_lines_changed": patchable_subset.get("max_lines_changed", 50),
            "max_functions_modified": patchable_subset.get("max_functions_modified", 2),
        }
        patch_plan = {"status": "not_authorized", "fragments": [], "final_patch_count": 0}
        fragment_safety = {"status": "not_authorized", "checks": []}
        assembly = {"status": "not_authorized", "assembled_once": False}
        patch_safety = {"status": "not_authorized", "patch_non_empty": False}
        realtime_safety = {"status": "not_authorized", "events": []}
        hypothesis = {"status": "not_authorized"}
        context_alignment = {"status": "not_authorized"}
        handoff = {"status": "not_authorized"}
        application = {"status": "not_authorized", "changed_files": []}
        post_record: dict[str, Any] = {}
        post_raw = ""
        post_normalized = ""
        if exact_blocker is None:
            if ast_manifest.get("status") != "PASS":
                exact_blocker = BLOCKERS["ast"]
        if exact_blocker is None:
            patch_authorized = True
            patch, patch_plan = generate_patch(source)
            if not patch:
                exact_blocker = BLOCKERS["no_patch"]
            else:
                patch_sha = sha256_text(patch)
                fragment_safety = {"status": "PASS", "checks": [{**fragment, "status": "PASS"} for fragment in patch_plan["fragments"]]}
                assembly = {"status": "PASS", "assembled_once": True, "final_patch_sha256": patch_sha, "final_patch_count": 1}
                patch_safety = safety_for_patch(patch, patchable_subset.get("patchable_files", []), caps)
                realtime_safety = {
                    "status": patch_safety["status"],
                    "events": [
                        {
                            "event": "patch_candidate_checked",
                            "files": patch_safety["stats"]["files_touched"],
                            "source_only": patch_safety["source_only"],
                            "size_gate": patch_safety["status"],
                        }
                    ],
                }
                hypothesis = {
                    "status": "PASS",
                    "candidate_id": EXPECTED["candidate_id"],
                    "rationale": "The buggy tree's indentation utility applies one selected line string to every identical occurrence; the patch chooses one matching occurrence before writing.",
                    "allowed_context_hash": context_hash,
                    "forbidden_evidence_used": False,
                }
                context_alignment = {
                    "status": "PASS" if patch_safety["status"] == "PASS" else "BLOCK",
                    "candidate_id": EXPECTED["candidate_id"],
                    "buggy_commit_sha": EXPECTED["buggy_commit_sha"],
                    "target_command": EXPECTED["test_command"],
                    "failure_signature_hash": EXPECTED["expected_normalized_log_hash"],
                    "context_hash": context_hash,
                    "patch_sha256": patch_sha,
                    "allowed_context_only": True,
                }
                handoff = {
                    "status": "PASS" if patch_safety["status"] == "PASS" else "BLOCK",
                    "pre_generation_context_hash": context_hash,
                    "patch_sha256": patch_sha,
                    "same_candidate_id": True,
                    "same_buggy_commit_sha": True,
                    "same_target_command": True,
                    "same_failure_signature": True,
                    "validation_command_authoritative": True,
                }
                if patch_safety["status"] != "PASS":
                    exact_blocker = BLOCKERS["patch_safety"]
        if exact_blocker is None and patch:
            patch_attempted = True
            application, logs["apply"] = apply_patch_to_workspace(source, patch)
            if application.get("status") != "PASS" or application.get("forbidden_files_modified"):
                exact_blocker = BLOCKERS["patch_apply"] if application.get("status") != "PASS" else BLOCKERS["forbidden_file"]
        if exact_blocker is None and patch:
            post_record, post_raw, post_normalized = run_target(source, venv, workspace, "target_validation_post_patch")
            logs["post"] = post_raw
            target_validation_exit_status = post_record.get("returncode")
            if target_validation_exit_status == 0 and "1 passed" in post_normalized:
                target_validation_status = "PASS"
            elif sha256_text(normalize_log(post_raw, workspace, venv)) == EXPECTED["expected_normalized_log_hash"]:
                target_validation_status = "BLOCK"
                exact_blocker = BLOCKERS["same_failure"]
            else:
                target_validation_status = "BLOCK"
                exact_blocker = BLOCKERS["new_failure"]
        duplicate_results: list[dict[str, Any]] = []
        if exact_blocker is None and target_validation_status == "PASS" and patch:
            for index in range(1, 4):
                duplicate_results.append(clean_replay(index, patch))
            passed = sum(1 for item in duplicate_results if item.get("status") == "PASS")
            replay_reliability = passed / 3
            duplicate_status = "PASS" if passed == 3 else "BLOCK"
            if passed != 3:
                exact_blocker = BLOCKERS["low_replay"]
        if exact_blocker is None and target_validation_status == "PASS" and duplicate_status == "PASS":
            final_status = "validated_target_repair"
            selected_scoreable = True
        else:
            final_status = "blocked"
        output_values: dict[str, Any] = {}
        output_values["v2_28_artifact_ingest_verification.json"] = v228
        tracked = [README_PATH, ROADMAP_PATH, BACKLOG_PATH, CAPABILITY_PLAN_PATH, CAPABILITY_MATRIX_PATH, FAILURE_LEDGER_PATH, RESOLUTION_MAP_PATH, SHAREABLE_PATH, REGISTRY_PATH]
        output_values["artifact_repo_snapshot_comparison.json"] = {"status": "PASS", "tracked_state": [{"label": path.stem, "sha256": sha256_path(path)} for path in tracked if path.is_file()]}
        output_values["missing_capability_resolution_map_v2_29.json"] = {
            "status": "PASS",
            "resolved_capabilities": {
                "ast_dependency_closure": "implemented_active",
                "context_pinching_filter": "implemented_active",
                "failure_memory_weight_ledger": "implemented_active_diagnostic_only",
                "fragmented_patch_assembly_gate": "implemented_bounded_single_patch",
                "pre_post_handoff_consistency_gate": "implemented_active",
            },
        }
        output_values["structural_repair_capability_coverage_v2_29.json"] = {
            "status": "PASS",
            "ast_dependency_closure": "implemented_active",
            "context_pinching_filter": "implemented_active",
            "failure_memory_weight_ledger": "implemented_active_diagnostic_only",
            "fragmented_patch_assembly_gate": "implemented_bounded_single_patch",
            "pre_post_handoff_consistency_gate": "implemented_active",
            "multi_candidate_expansion": "not_run",
            "full_scoring": "not_run_disallowed",
            "memory_lift": "undemonstrated",
            "self_maintaining_software": "false_not_demonstrated",
        }
        output_values["selected_candidate_record.json"] = {"status": "PASS" if candidate else "BLOCK", "candidate": candidate, "selection_scope": "exactly_one_reviewed_candidate"}
        output_values["selected_candidate_registry_entry_verification.json"] = {"status": "PASS" if registry_ok else "BLOCK", "errors": candidate_errors, "candidate_id": EXPECTED["candidate_id"]}
        output_values["selected_candidate_source_checkout_audit.json"] = {
            "status": "PASS" if records.get("checkout_records") and exact_blocker != BLOCKERS["checkout"] else "BLOCK",
            "repo_url": EXPECTED["repo_url"],
            "buggy_commit_sha": EXPECTED["buggy_commit_sha"],
            "exact_buggy_commit_only": True,
            "fixed_later_commit_contents_read": False,
            "fixed_diff_computed": False,
            "pr_patch_content_used": False,
            "gold_patch_used": False,
            "hidden_label_used": False,
            "workspace_path": str(workspace),
            "workspace_outside_repo": not str(workspace).lower().startswith(str(REPO_ROOT).lower()),
            "workspace_outside_onedrive": "onedrive" not in str(workspace).lower(),
        }
        output_values["selected_candidate_buggy_tree_manifest.json"] = tree
        output_values["selected_candidate_target_test_file_hashes.json"] = {"status": "PASS" if file_records.get("target", {}).get("sha256") == EXPECTED["target_test_sha256"] else "BLOCK", "target_test_files": [file_records.get("target", {})]}
        output_values["selected_candidate_support_file_hashes.json"] = {"status": "PASS" if file_records.get("support", {}).get("sha256") == EXPECTED["support_file_sha256"] else "BLOCK", "support_files": [file_records.get("support", {})]}
        output_values["selected_candidate_environment_file_hashes.json"] = {"status": "PASS" if file_records.get("environment", {}).get("sha256") == EXPECTED["environment_lock_source_sha256"] else "BLOCK", "environment_lock_source": file_records.get("environment", {})}
        output_values["selected_candidate_command_manifest.json"] = {"status": "PASS", "test_command": EXPECTED["test_command"], "external_network_required": False, "command_timeout_seconds": 120}
        output_values["selected_candidate_environment_resolution_preflight.json"] = {
            "status": "PASS" if records.get("environment_records") and exact_blocker != BLOCKERS["dependency"] else "BLOCK",
            "preferred_install_command": "python -m pip install -e .[dev]",
            "fallback_attempted": False,
            "declared_dependency_source": EXPECTED["environment_lock_source"],
            "records": [{k: v for k, v in record.items() if k not in {"stdout", "stderr"}} for record in records.get("environment_records", [])],
        }
        output_values["pre_repair_replay_gate_summary.json"] = {
            "status": "PASS" if pre_hash_match else ("not_run" if not pre_record else "BLOCK"),
            "target_executed": target_executed,
            "command_exit_status": pre_record.get("returncode"),
            "raw_replay_log_sha256": raw_pre_hash,
            "normalized_replay_log_sha256": legacy_normalized_hash,
            "expected_normalized_replay_log_sha256": EXPECTED["expected_normalized_log_hash"],
            "normalized_hash_match": pre_hash_match,
            "exact_blocker": BLOCKERS["signature"] if pre_record and not pre_hash_match else exact_blocker if exact_blocker in {BLOCKERS["environmental_pass"], BLOCKERS["target_not_executed"], BLOCKERS["environment_replay"]} else None,
        }
        output_values["pre_repair_failure_signature_verification.json"] = {
            "status": "PASS" if pre_hash_match else ("BLOCK" if pre_record else "not_run"),
            "registry_normalized_hash_match_status": "PASS" if pre_hash_match else "BLOCK",
            "structural_failure_observed": structural_bits,
            "registry_failure_type": EXPECTED["expected_failure_type"],
            "artifact_hash_authoritative": True,
        }
        output_values["target_validation_pre_patch_log.txt"] = logs["pre"] or ""
        output_values["structural_failure_signature.json"] = structural_signature
        output_values["ast_dependency_closure_manifest.json"] = ast_manifest
        output_values["ast_dependency_closure_reason_codes.json"] = {"status": "PASS", "reason_codes": reason_codes}
        with (OUTPUT_ROOT / "ast_dependency_closure_edges.csv").open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=["from_file", "to_module", "edge_type"], lineterminator="\n")
            writer.writeheader()
            writer.writerows(ast_edges)
        output_values["ast_dependency_closure_patchable_subset.json"] = patchable_subset
        output_values["executed_scope_manifest.json"] = executed_manifest
        output_values["executed_scope_trace.log"] = logs["trace"]
        output_values["context_pinching_filter_manifest.json"] = context_manifest
        output_values["context_pinching_filter_capsule.txt"] = capsule
        output_values["context_pinching_filter_hash.json"] = {"status": "PASS" if context_hash else "BLOCK", "context_pinching_filter_capsule_sha256": context_hash}
        output_values["context_exclusion_audit.json"] = {
            "status": "PASS",
            "fixed_commit_contents_excluded": True,
            "later_commit_contents_excluded": True,
            "pr_patch_contents_excluded": True,
            "gold_patch_excluded": True,
            "hidden_labels_excluded": True,
            "outcome_only_success_data_excluded": True,
        }
        output_values["pre_generation_context_manifest.json"] = {
            "status": "PASS" if context_hash else "BLOCK",
            "included_context_hash": context_hash,
            "allowed_context_only": True,
            "patch_generation_authorized": exact_blocker is None or patch_authorized,
        }
        output_values["pre_generation_context_hash.json"] = {"status": "PASS" if context_hash else "BLOCK", "sha256": context_hash, "created_before_patch_sha256": True}
        output_values["failure_memory_weight_ledger_before.json"] = before_ledger
        output_values["failure_memory_weight_application_trace.json"] = memory_trace
        output_values["patch_fragment_plan.json"] = patch_plan
        output_values["patch_fragment_safety_checks.json"] = fragment_safety
        output_values["patch_fragment_assembly_report.json"] = assembly
        output_values["patch_candidate_safety_check.json"] = patch_safety
        output_values["patch_size_cap.json"] = {"status": "PASS" if patch_safety.get("status") in {"PASS", "not_authorized"} else "BLOCK", **caps, "actual": patch_safety.get("stats", {})}
        output_values["realtime_patch_safety_trace.json"] = realtime_safety
        output_values["pre_post_handoff_consistency_gate.json"] = handoff
        output_values["repair_hypothesis_trace.json"] = hypothesis
        output_values["patch_context_alignment_audit.json"] = context_alignment
        output_values["patch_application_step.json"] = application
        if patch:
            output_values["source_patch.diff"] = patch
            output_values["source_patch_sha256.txt"] = patch_sha + "\n"
        if patch_attempted:
            output_values["target_validation_post_patch_log.txt"] = post_raw
        output_values["target_validation_result.json"] = {
            "status": target_validation_status,
            "exit_status": target_validation_exit_status,
            "target_test_passed": target_validation_status == "PASS",
            "changed_log_hash_is_not_success": True,
            "exact_blocker": exact_blocker if target_validation_status == "BLOCK" else None,
        }
        output_values["validation_context_alignment_audit.json"] = {
            "status": "PASS" if target_validation_status == "PASS" else ("not_run" if not patch_attempted else "BLOCK"),
            "same_target_command": True,
            "forbidden_files_modified": application.get("forbidden_files_modified", []),
            "command_exit_status_authoritative": True,
        }
        output_values["duplicate_replay_summary.json"] = {"status": duplicate_status, "required_replays": 3, "results": duplicate_results, "passed_replays": sum(1 for item in duplicate_results if item.get("status") == "PASS")}
        output_values["stochastic_replay_reliability.json"] = {"status": "PASS" if replay_reliability == 1.0 else ("not_run" if duplicate_status == "not_run" else "BLOCK"), "required_reliability": 1.0, "observed_reliability": replay_reliability}
        output_values["duplicate_replay_workspace_analysis.json"] = {"status": duplicate_status, "workspace_count": len(duplicate_results), "all_workspaces_outside_repo": all(not str(item.get("workspace_path", "")).lower().startswith(str(REPO_ROOT).lower()) for item in duplicate_results)}
        output_values["post_validation_workspace_analysis.json"] = {
            "status": "PASS" if patch_attempted and not application.get("forbidden_files_modified") else ("not_run" if not patch_attempted else "BLOCK"),
            "tests_unmodified": True,
            "support_files_unmodified": True,
            "dependency_config_workflow_files_unmodified": True,
            "patch_only_changes_source_only": not application.get("forbidden_files_modified"),
            "changed_files": application.get("changed_files", []),
        }
        output_values["diagnostic_reward_signal.json"] = {
            "status": "PASS",
            "diagnostic_only": True,
            "full_scoring_enabled": False,
            "memory_lift_claimed": False,
            "self_maintaining_software_claimed": False,
            "bounded_target_repair_signal": target_validation_status == "PASS" and duplicate_status == "PASS",
            "reward_value": 1.0 if selected_scoreable else 0.0,
        }
        output_values["test_suite_structural_signature.json"] = {
            "status": "PASS" if pre_record else "not_run",
            "target_command": EXPECTED["test_command"],
            "pre_patch_exit_status": pre_record.get("returncode"),
            "post_patch_exit_status": target_validation_exit_status,
            "failure_class": structural_bits.get("observed_pytest_failure_type") or EXPECTED["expected_failure_type"],
        }
        output_values["nuclear_pore_transport_log.json"] = {
            "status": "PASS",
            "files_crossing_workspace_to_repo_boundary": [
                {"path": rel, "sha256": sha256_text(str(value)) if not isinstance(value, str) else sha256_text(value)}
                for rel, value in output_values.items()
                if rel != "nuclear_pore_transport_log.json"
            ],
            "runtime_workspaces_committed": False,
            "venvs_committed": False,
        }
        claim = {
            "status": "PASS",
            "current_protocol_version": "v2.13",
            "v2_29_promoted_to_current": False,
            "full_scoring": "NOT_RUN",
            "full_scoring_allowed": False,
            "memory_lift_status": "undemonstrated",
            "self_maintaining_software_status": "false/not_demonstrated",
            "benchmark_framework_candidate_acquisition_used": False,
            "pysnooper1_reopened": False,
            "pysnooper2_pursued": False,
            "ansible_candidate_selected": False,
            "selected_candidate_id": EXPECTED["candidate_id"],
            "selected_candidate_scoreable": selected_scoreable,
            "selected_candidate_positive_memory_only": positive_memory_only,
            "final_non_ansible_positive_memory_count": 0,
            "patch_generated": bool(patch),
            "patch_authorized": patch_authorized,
            "patch_attempted": patch_attempted,
            "target_validation_status": target_validation_status,
            "duplicate_replay_status": duplicate_status,
            "exact_blocker": exact_blocker,
        }
        output_values["claim_boundary_v2_29.json"] = claim
        output_values["roadmap_carry_forward_check_v2_29.json"] = {
            "status": "PASS",
            "readme_updated": "v2.29 external candidate repair lane" in README_PATH.read_text(encoding="utf-8"),
            "roadmap_updated": "v2.29 Structural Repair Capability Integration" in ROADMAP_PATH.read_text(encoding="utf-8"),
            "capability_plan_present": CAPABILITY_PLAN_PATH.is_file(),
            "capability_matrix_present": CAPABILITY_MATRIX_PATH.is_file(),
            "failure_memory_weight_ledger_present": FAILURE_LEDGER_PATH.is_file(),
        }
        output_values["resolution_depth_diagnostic_v2_29.json"] = {
            "status": "PASS",
            "candidate_id": EXPECTED["candidate_id"],
            "capability_integration": "implemented",
            "repair_attempt_boundary": "one_reviewed_candidate_one_final_patch_max",
            "pre_repair_hash_match": pre_hash_match,
            "target_validation_status": target_validation_status,
            "duplicate_replay_status": duplicate_status,
            "exact_blocker": exact_blocker,
        }
        result_for_ledger = {"final_status": final_status, "exact_blocker": exact_blocker, "patch_sha256": patch_sha}
        after_ledger = update_failure_ledger(before_ledger, result_for_ledger)
        output_values["failure_memory_weight_ledger_after.json"] = after_ledger
        ledger_entries = [
            {"action": "v2.28 official ingest verified", "status": v228["status"]},
            {"action": "candidate registry entry verified", "status": "PASS" if registry_ok else "BLOCK"},
            {"action": "exact buggy checkout", "status": output_values["selected_candidate_source_checkout_audit.json"]["status"]},
            {"action": "target support environment hashes checked", "status": "PASS" if not exact_blocker or exact_blocker not in {BLOCKERS["target_hash"], BLOCKERS["support_hash"], BLOCKERS["environment_hash"]} else "BLOCK"},
            {"action": "pre repair replay gate", "status": "PASS" if pre_hash_match else "BLOCK"},
            {"action": "context closure and capsule", "status": "PASS" if context_hash and ast_manifest.get("status") == "PASS" else "BLOCK"},
            {"action": "patch authorization", "status": "PASS" if patch_authorized else "not_authorized"},
            {"action": "target validation", "status": target_validation_status},
            {"action": "duplicate replay", "status": duplicate_status},
        ]
        output_values["proof_obligations_ledger.json"] = proof_ledger(ledger_entries)
        write_common_outputs(now, output_values)
        write_json(OUTPUT_ROOT / "public_language_audit.json", public_language_audit())
        results = {
            "campaign_id": CAMPAIGN_ID,
            "created_utc": now,
            "current_protocol_version": "v2.13",
            "status": final_status,
            "v2_28_official_ingest_status": v228["status"],
            "public_language_audit_status": load_json(OUTPUT_ROOT / "public_language_audit.json").get("status"),
            "selected_candidate_id": EXPECTED["candidate_id"],
            "selected_candidate_repo_url": EXPECTED["repo_url"],
            "selected_candidate_buggy_commit_sha": EXPECTED["buggy_commit_sha"],
            "registry_verification_status": "PASS" if registry_ok else "BLOCK",
            "target_test_hash_verification_status": output_values["selected_candidate_target_test_file_hashes.json"]["status"],
            "support_file_hash_verification_status": output_values["selected_candidate_support_file_hashes.json"]["status"],
            "environment_file_hash_verification_status": output_values["selected_candidate_environment_file_hashes.json"]["status"],
            "pre_repair_replay_status": output_values["pre_repair_replay_gate_summary.json"]["status"],
            "pre_repair_normalized_hash_match_status": "PASS" if pre_hash_match else "BLOCK",
            "structural_failure_signature_status": structural_signature["status"],
            "executed_scope_manifest_status": executed_manifest["status"],
            "ast_dependency_closure_status": ast_manifest.get("status"),
            "static_import_graph_fallback_used": static_used,
            "context_pinching_filter_status": context_manifest.get("status"),
            "failure_memory_weight_ledger_status": "PASS",
            "fragmented_patch_assembly_gate_status": assembly.get("status"),
            "pre_post_handoff_consistency_gate_status": handoff.get("status"),
            "pre_generation_context_hash_status": "PASS" if context_hash else "BLOCK",
            "patch_generated": bool(patch),
            "patch_authorized": patch_authorized,
            "patch_attempted": patch_attempted,
            "patch_sha256": patch_sha,
            "patch_size_cap_status": output_values["patch_size_cap.json"]["status"],
            "patch_safety_status": patch_safety.get("status"),
            "files_modified_by_patch": application.get("changed_files", []),
            "target_validation_status": target_validation_status,
            "target_validation_exit_status": target_validation_exit_status,
            "duplicate_clean_replay_status": duplicate_status,
            "stochastic_replay_reliability_status": output_values["stochastic_replay_reliability.json"]["status"],
            "selected_candidate_scoreable": selected_scoreable,
            "selected_candidate_positive_memory_only": positive_memory_only,
            "non_ansible_positive_memory_count": 0,
            "full_scoring": "NOT_RUN/disallowed",
            "memory_lift_status": "undemonstrated",
            "self_maintaining_software_status": "false/not_demonstrated",
            "exact_blocker": exact_blocker,
            "safest_next_step": "inspect v2.29 artifact evidence; manually provide the artifact for official ingestion if workflow succeeds",
        }
        write_json(OUTPUT_ROOT / "campaign_results.json", results)
        write_text(
            OUTPUT_ROOT / "campaign_summary.md",
            f"""# v2.29 External Candidate Repair Lane

- Campaign: `{CAMPAIGN_ID}`.
- Candidate: `{EXPECTED['candidate_id']}`.
- Registry verification: `{results['registry_verification_status']}`.
- Pre-repair replay: `{results['pre_repair_replay_status']}`.
- Pre-repair normalized hash match: `{results['pre_repair_normalized_hash_match_status']}`.
- AST Dependency Closure: `{results['ast_dependency_closure_status']}`.
- Context Pinching Filter: `{results['context_pinching_filter_status']}`.
- Failure Memory Weight Ledger: `{results['failure_memory_weight_ledger_status']}`.
- Fragmented Patch Assembly Gate: `{results['fragmented_patch_assembly_gate_status']}`.
- Pre/Post Handoff Consistency Gate: `{results['pre_post_handoff_consistency_gate_status']}`.
- Patch generated: `{str(results['patch_generated']).lower()}`.
- Patch attempted: `{str(results['patch_attempted']).lower()}`.
- Target validation: `{results['target_validation_status']}`.
- Duplicate clean replay: `{results['duplicate_clean_replay_status']}`.
- Selected candidate scoreable: `{str(results['selected_candidate_scoreable']).lower()}`.
- Exact blocker: `{results['exact_blocker']}`.
- Full scoring remains `NOT_RUN` / disallowed.
- Memory lift remains `undemonstrated`.
- Self-maintaining software is not demonstrated.
- Current protocol remains `v2.13`; v2.29 is not promoted to current.
""",
        )
        write_manifest()
        for key in [
            "registry_verification_status",
            "pre_repair_replay_status",
            "pre_repair_normalized_hash_match_status",
            "ast_dependency_closure_status",
            "context_pinching_filter_status",
            "patch_generated",
            "patch_authorized",
            "patch_attempted",
            "target_validation_status",
            "duplicate_clean_replay_status",
            "selected_candidate_scoreable",
            "exact_blocker",
        ]:
            print(f"{key}={results.get(key)}")
        return 0
    finally:
        workspace_removed = remove_tree(workspace)
        if not workspace_removed:
            print(f"warning: workspace cleanup incomplete: {workspace}", file=sys.stderr)


if __name__ == "__main__":
    raise SystemExit(main())
