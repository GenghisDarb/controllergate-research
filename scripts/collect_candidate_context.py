#!/usr/bin/env python3
"""Collect bounded, decision-time-safe context for one repair candidate."""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
import re
import subprocess
from pathlib import Path, PurePosixPath
from typing import Any


METADATA_NAMES = (
    "setup.py",
    "pyproject.toml",
    "setup.cfg",
    "requirements.txt",
    "requirements-dev.txt",
    "test-requirements.txt",
    "dev-requirements.txt",
    "tox.ini",
    "pytest.ini",
)


def sha256_path(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def safe_relative(root: Path, raw: str) -> Path | None:
    value = raw.replace("\\", "/").lstrip("./")
    if not value or value.startswith("/") or re.match(r"^[A-Za-z]:", value):
        return None
    parts = PurePosixPath(value).parts
    if any(part in {"", ".", ".."} for part in parts):
        return None
    candidate = root.joinpath(*parts).resolve()
    return candidate if candidate == root or root in candidate.parents else None


def git_identity(root: Path) -> dict[str, Any]:
    def run(*args: str) -> str:
        result = subprocess.run(
            ["git", "-C", str(root), *args],
            check=False,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        return result.stdout.strip() if result.returncode == 0 else "unknown"

    return {
        "head_sha": run("rev-parse", "HEAD"),
        "status_porcelain": run("status", "--porcelain"),
        "top_level": run("rev-parse", "--show-toplevel"),
    }


def patch_files_and_symbols(text: str) -> tuple[list[str], list[str]]:
    files: set[str] = set()
    symbols: set[str] = set()
    for line in text.splitlines():
        if line.startswith(("--- ", "+++ ")):
            value = line[4:].split("\t", 1)[0].strip().replace("\\", "/")
            if value != "/dev/null":
                if value.startswith(("a/", "b/")):
                    value = value[2:]
                files.add(value)
        elif (line.startswith("+") and not line.startswith("+++")) or (line.startswith("-") and not line.startswith("---")):
            code = line[1:].split("#", 1)[0]
            symbols.update(re.findall(r"\b[A-Za-z_][A-Za-z0-9_]*\b", code))
    return sorted(files), sorted(symbols)[:80]


def trace_context(text: str) -> tuple[list[str], list[str]]:
    paths = sorted(set(re.findall(r"(?<![A-Za-z0-9_])((?:[A-Za-z0-9_.-]+/)+[A-Za-z0-9_.-]+\.py)", text)))
    symbols = set(re.findall(r"::([A-Za-z_][A-Za-z0-9_]*)", text))
    symbols.update(re.findall(r"cannot import name ['\"]([A-Za-z_][A-Za-z0-9_]*)", text))
    symbols.update(re.findall(r"in <module>\s*$", text, flags=re.MULTILINE))
    for match in re.finditer(r"^([A-Za-z_][A-Za-z0-9_]*)Error:", text, flags=re.MULTILINE):
        symbols.add(match.group(1) + "Error")
    return paths, sorted(symbols)[:80]


def resolve_import(root: Path, source: Path, node: ast.Import | ast.ImportFrom, alias: ast.alias) -> tuple[str, Path | None]:
    rel_source = source.relative_to(root).as_posix()
    if isinstance(node, ast.Import):
        module = alias.name
        display = f"{rel_source} -> {module}"
        parts = module.split(".")
    else:
        module = node.module or ""
        if node.level:
            package_parts = list(source.relative_to(root).parent.parts)
            keep = max(0, len(package_parts) - (node.level - 1))
            parts = package_parts[:keep] + ([part for part in module.split(".") if part] if module else [])
            if not module:
                parts.append(alias.name)
        else:
            parts = [part for part in module.split(".") if part]
        display = f"{rel_source} -> {'.' * node.level}{module}{'.' if module and alias.name else ''}{alias.name}"
    if not parts:
        return display, None
    file_candidate = root.joinpath(*parts).with_suffix(".py")
    package_candidate = root.joinpath(*parts, "__init__.py")
    if file_candidate.exists():
        return display, file_candidate.resolve()
    if package_candidate.exists():
        return display, package_candidate.resolve()
    return display, file_candidate.resolve()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--candidate", default="PySnooper:2")
    parser.add_argument("--buggy-checkout", type=Path, required=True)
    parser.add_argument("--checkout-baseline-identity", type=Path, required=True)
    parser.add_argument("--target-command-file", type=Path, required=True)
    parser.add_argument("--failure-log", type=Path, required=True)
    parser.add_argument("--pre-failure-log", type=Path)
    parser.add_argument("--patch", type=Path, required=True)
    parser.add_argument("--source-root", default="pysnooper")
    parser.add_argument("--target-test", required=True)
    parser.add_argument("--dependency-metadata", type=Path, action="append", default=[])
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--max-files", type=int, default=20)
    parser.add_argument("--max-symbols", type=int, default=80)
    args = parser.parse_args()

    root = args.buggy_checkout.resolve()
    if not root.is_dir():
        raise SystemExit(f"buggy checkout is not a directory: {root}")
    required = [args.target_command_file, args.failure_log, args.patch, args.checkout_baseline_identity]
    if any(not path.exists() for path in required):
        raise SystemExit(f"missing context inputs: {[str(path) for path in required if not path.exists()]}")

    try:
        checkout_baseline_identity = json.loads(args.checkout_baseline_identity.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        raise SystemExit(f"invalid checkout baseline identity: {exc}") from exc
    if not isinstance(checkout_baseline_identity, dict):
        raise SystemExit("checkout baseline identity must be a JSON object")

    patch_text = args.patch.read_text(encoding="utf-8", errors="strict")
    failure_text = args.failure_log.read_text(encoding="utf-8", errors="replace")
    if args.pre_failure_log and args.pre_failure_log.exists():
        failure_text = args.pre_failure_log.read_text(encoding="utf-8", errors="replace") + "\n" + failure_text
    patch_files, patch_symbols = patch_files_and_symbols(patch_text)
    traceback_paths, traceback_symbols = trace_context(failure_text)

    selected: dict[Path, str] = {}
    missing_helpers: set[str] = set()
    test_path = safe_relative(root, args.target_test)
    if test_path and test_path.exists():
        selected[test_path] = "direct target test from the exact target command"
    for raw in patch_files:
        path = safe_relative(root, raw)
        if path and path.exists() and len(selected) < args.max_files:
            selected[path] = "file touched by the v2.12 patch"
    for raw in traceback_paths:
        path = safe_relative(root, raw)
        if path and path.exists() and len(selected) < args.max_files:
            selected.setdefault(path, "file named by the target traceback")

    metadata_paths: list[Path] = []
    for name in METADATA_NAMES:
        path = (root / name).resolve()
        if path.exists() and path.is_file():
            metadata_paths.append(path)
    for path in args.dependency_metadata:
        resolved = path.resolve()
        if resolved.exists() and resolved.is_file() and resolved not in metadata_paths:
            metadata_paths.append(resolved)
    for path in metadata_paths:
        if len(selected) < args.max_files:
            selected.setdefault(path, "repo-local or BugsInPy dependency metadata")

    import_edges: list[dict[str, Any]] = []
    definitions: list[dict[str, Any]] = []
    helpers: set[str] = set()
    parsed_paths: set[Path] = set()
    while True:
        pending = [path for path in selected if path.suffix == ".py" and path not in parsed_paths]
        if not pending:
            break
        source = pending[0]
        parsed_paths.add(source)
        try:
            tree = ast.parse(source.read_text(encoding="utf-8", errors="replace"), filename=str(source))
        except SyntaxError:
            continue
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)) and len(definitions) < args.max_symbols:
                definitions.append(
                    {
                        "file": source.relative_to(root).as_posix() if root in source.parents else str(source),
                        "symbol": node.name,
                        "kind": type(node).__name__,
                        "line": node.lineno,
                        "selection_basis": "definition in bounded target/traceback/patch/import context",
                    }
                )
            if isinstance(node, ast.Import):
                aliases = node.names
            elif isinstance(node, ast.ImportFrom):
                aliases = node.names
            else:
                continue
            for alias in aliases:
                display, resolved = resolve_import(root, source, node, alias)
                local_exists = bool(resolved and resolved.exists() and (resolved == root or root in resolved.parents))
                edge = {
                    "edge": display,
                    "resolved_repo_path": resolved.relative_to(root).as_posix() if local_exists and resolved else None,
                    "resolved_repo_path_exists": local_exists,
                }
                import_edges.append(edge)
                if source == test_path and isinstance(node, ast.ImportFrom) and node.level:
                    helper_name = resolved.relative_to(root).as_posix() if resolved and (resolved == root or root in resolved.parents) else display
                    helpers.add(helper_name)
                    if not local_exists:
                        missing_helpers.add(helper_name)
                if local_exists and resolved and resolved not in selected and len(selected) < args.max_files:
                    selected[resolved] = f"repo-local import edge from {source.relative_to(root).as_posix()}"

    dependency_records: list[dict[str, Any]] = []
    declared_dependencies: set[str] = set()
    for path in metadata_paths:
        text = path.read_text(encoding="utf-8", errors="replace")
        matches = []
        for line_number, line in enumerate(text.splitlines(), start=1):
            if re.search(r"python[-_]toolbox", line, flags=re.IGNORECASE):
                matches.append({"line_number": line_number, "line": line.strip()})
                declared_dependencies.add("python_toolbox")
        dependency_records.append(
            {
                "path": path.relative_to(root).as_posix() if root in path.parents else str(path),
                "sha256": sha256_path(path),
                "matching_lines": matches,
            }
        )

    evidence_paths = sorted(selected, key=lambda path: str(path).lower())
    limitations = []
    if missing_helpers:
        limitations.append("directly referenced target-test helpers are absent from the buggy checkout: " + ", ".join(sorted(missing_helpers)))
    if len(selected) >= args.max_files:
        limitations.append("context file budget reached")
    current_checkout_identity = git_identity(root)
    checkout_drift_detected = any(
        current_checkout_identity.get(field) != checkout_baseline_identity.get(field)
        for field in ["head_sha", "status_porcelain"]
    )
    result = {
        "status": "PASS",
        "candidate": args.candidate,
        "target_command": args.target_command_file.read_text(encoding="utf-8", errors="strict").strip(),
        "checkout_baseline_identity": checkout_baseline_identity,
        "buggy_checkout_identity": current_checkout_identity,
        "checkout_drift_detected": checkout_drift_detected,
        "source_root": args.source_root,
        "test_paths": [args.target_test],
        "traceback_symbols": traceback_symbols[: args.max_symbols],
        "patch_touched_symbols": patch_symbols[: args.max_symbols],
        "import_graph_edges": import_edges[: args.max_symbols],
        "ast_definitions_near_traceback": [item for item in definitions if item["symbol"] in traceback_symbols][: args.max_symbols],
        "ast_definitions_near_patch": [item for item in definitions if item["symbol"] in patch_symbols][: args.max_symbols],
        "bounded_ast_definitions": definitions[: args.max_symbols],
        "dependency_metadata_files": dependency_records,
        "declared_dependencies": sorted(declared_dependencies),
        "missing_or_suspect_dependencies": [],
        "fixture_or_test_helpers_referenced": sorted(helpers),
        "missing_fixture_or_test_helpers_referenced": sorted(missing_helpers),
        "context_budget": {
            "max_files": args.max_files,
            "max_symbols": args.max_symbols,
            "max_probe_commands": 2,
            "selected_file_count": len(evidence_paths),
            "selected_symbol_count": len(definitions[: args.max_symbols]),
        },
        "context_selection_basis": [
            {
                "path": path.relative_to(root).as_posix() if root in path.parents else str(path),
                "basis": selected[path],
            }
            for path in evidence_paths
        ],
        "excluded_context_reason": [
            "repository files without a target-command, target-test, traceback, patch, local-import, or dependency-metadata connection were excluded",
            "fixed revisions, gold patches, and future outcome evidence were not inspected",
        ],
        "context_limitations": limitations,
        "evidence_files": [
            path.relative_to(root).as_posix() if root in path.parents else str(path) for path in evidence_paths
        ],
        "sha256_inputs": {
            str(path): sha256_path(path)
            for path in [args.target_command_file, args.failure_log, args.patch, args.checkout_baseline_identity]
            + ([args.pre_failure_log] if args.pre_failure_log and args.pre_failure_log.exists() else [])
            + evidence_paths
        },
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
