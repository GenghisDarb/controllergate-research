from __future__ import annotations

import hashlib
from pathlib import Path
import re
from typing import Any

from controllergate.core.evidence import hash_record, sha256_file


NODE_PATTERN = re.compile(r"(?P<path>(?:[A-Za-z0-9_.-]+/)*(?:test_[A-Za-z0-9_.-]+|[A-Za-z0-9_.-]+_test)\.py)::(?P<node>[A-Za-z0-9_\[\].:-]+)")
FILE_PATTERN = re.compile(r"(?<![A-Za-z0-9_.-])(?P<path>(?:[A-Za-z0-9_.-]+/)*(?:test_[A-Za-z0-9_.-]+|[A-Za-z0-9_.-]+_test)\.py)")
TRACEBACK_FILE = re.compile(r"(?i)File\s+[\"'](?P<path>(?:[A-Za-z0-9_.-]+[/\\])*(?:test_[A-Za-z0-9_.-]+|[A-Za-z0-9_.-]+_test)\.py)[\"']\s*,\s*line\s+\d+")
TEST_NAME = re.compile(r"\b(test_[A-Za-z0-9_]+|Test[A-Za-z0-9_]+)\b")
SOURCE_PATH = re.compile(r"(?<![A-Za-z0-9_.-])(?P<path>(?:[A-Za-z0-9_.-]+[/\\])+[A-Za-z0-9_.-]+\.py)")
SYMBOL = re.compile(r"\b(?P<symbol>[A-Za-z_][A-Za-z0-9_]{4,})\b")
IGNORED_SYMBOLS = {"python", "pytest", "traceback", "assertionerror", "typeerror", "exception", "expected", "actual", "observed", "runtime", "version", "failure", "failed", "tests"}


def _test_tree_hash(root: Path) -> str:
    rows = [(path.relative_to(root).as_posix(), sha256_file(path)) for path in sorted(root.rglob("*.py")) if "test" in path.relative_to(root).as_posix().lower()]
    return hash_record(rows)


def resolve_target(source_root: Path, evidence_text: str, candidate_sha: str) -> dict[str, Any]:
    for match in NODE_PATTERN.finditer(evidence_text):
        path = match.group("path").lstrip("./")
        if (source_root / path).is_file():
            return _result(source_root, path, match.group("node"), "exact_issue_node", candidate_sha, "issue_node")
    for match in TRACEBACK_FILE.finditer(evidence_text):
        path = match.group("path").replace("\\", "/").lstrip("./")
        if (source_root / path).is_file():
            names = [name for name in dict.fromkeys(TEST_NAME.findall(evidence_text)) if name in (source_root / path).read_text(encoding="utf-8", errors="replace")]
            return _result(source_root, path, names[0] if names else None, "traceback_derived_target", candidate_sha, "traceback_test_path")
    for match in FILE_PATTERN.finditer(evidence_text):
        path = match.group("path").lstrip("./")
        if (source_root / path).is_file():
            file_text = (source_root / path).read_text(encoding="utf-8", errors="replace")
            for name in dict.fromkeys(TEST_NAME.findall(evidence_text)):
                if re.search(rf"(?m)^\s*(?:def|class)\s+{re.escape(name)}\b", file_text):
                    return _result(source_root, path, name, "source_verified_symbol_to_test_target", candidate_sha, "issue_file_and_named_test")
            return _result(source_root, path, None, "exact_issue_file", candidate_sha, "issue_file_or_traceback")
    names = list(dict.fromkeys(TEST_NAME.findall(evidence_text)))
    test_files = [path for path in source_root.rglob("*.py") if "test" in path.relative_to(source_root).as_posix().lower() and ".git" not in path.parts]
    for name in names:
        declaration = re.compile(rf"(?m)^\s*(?:def|class)\s+{re.escape(name)}\b")
        for path in test_files:
            try:
                if declaration.search(path.read_text(encoding="utf-8", errors="replace")):
                    return _result(source_root, path.relative_to(source_root).as_posix(), name, "source_verified_symbol_to_test_target", candidate_sha, "named_test_tree_search")
            except OSError:
                continue
    # A source symbol or traceback source path may identify a native test even
    # when the issue does not spell out tests/*.py.  Admit only a unique,
    # source-verified reference so this cannot silently become guessing.
    source_paths = [match.group("path").replace("\\", "/").lstrip("./") for match in SOURCE_PATH.finditer(evidence_text)]
    symbols = []
    for match in SYMBOL.finditer(evidence_text):
        value = match.group("symbol")
        if value.lower() not in IGNORED_SYMBOLS and ("_" in value or any(ch.isupper() for ch in value[1:])):
            symbols.append(value)
    references: dict[str, set[str]] = {}
    for path in test_files:
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        matched = {symbol for symbol in symbols if re.search(rf"\b{re.escape(symbol)}\b", text)}
        for source_path in source_paths:
            module = Path(source_path).stem
            dotted = source_path[:-3].replace("/", ".")
            if module.startswith("test_") or module.endswith("_test"):
                continue
            if re.search(rf"\b{re.escape(module)}\b|{re.escape(dotted)}", text):
                matched.add(source_path)
        if matched:
            references[path.relative_to(source_root).as_posix()] = matched
    if len(references) == 1:
        path, matched = next(iter(references.items()))
        return _result(source_root, path, None, "source_verified_symbol_to_test_target", candidate_sha, "bounded_source_symbol_to_test_reference:" + ",".join(sorted(matched)))
    if len(test_files) == 1 and re.search(r"(?i)\b(?:failed|failure|error|exception|regression|traceback)\b", evidence_text):
        path = test_files[0].relative_to(source_root).as_posix()
        return _result(source_root, path, None, "bounded_project_native_target", candidate_sha, "single_native_test_file_in_failure_repository")
    return {"status": "BLOCK", "blocker": "source_verified_native_target_unresolved", "confidence_class": "guessed_target", "candidate_source_sha": candidate_sha, "names_searched": names, "synthetic_target": False}


def _result(root: Path, path: str, node: str | None, confidence: str, sha: str, evidence: str) -> dict[str, Any]:
    target = f"{path}::{node}" if node else path
    return {"status": "PASS", "target_file": path, "target_node": node, "target": target, "source_evidence": evidence, "confidence_class": confidence, "candidate_source_sha": sha, "test_tree_hash": _test_tree_hash(root), "target_sha256": sha256_file(root / path), "independent_verification": True, "synthetic_target": False}
