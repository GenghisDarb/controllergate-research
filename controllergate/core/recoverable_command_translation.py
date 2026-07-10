from __future__ import annotations

import re
from pathlib import Path
from typing import Iterable

from .evidence import sha256_file

ALLOWED_COMMAND_SOURCE_FILES = [
    "pyproject.toml",
    "tox.ini",
    "noxfile.py",
    "setup.cfg",
    "setup.py",
    "requirements.txt",
    "requirements-dev.txt",
    "dev-requirements.txt",
    "test-requirements.txt",
    "uv.lock",
    "poetry.lock",
    "pdm.lock",
    "hatch.toml",
    "Makefile",
]

ALLOWED_COMMAND_SOURCE_GLOBS = [
    ".github/workflows/*.yml",
    ".github/workflows/*.yaml",
    "README*",
    "CONTRIBUTING*",
    "TESTING*",
    "docs/**/*.md",
    "docs/**/*.rst",
]

FORBIDDEN_COMMAND_SOURCES = [
    "modern_docs_outside_candidate_checkout",
    "future_commit",
    "fixed_patch",
    "gold_patch",
    "issue_comment_workaround_text",
    "blog_post",
    "manual_guessed_command",
    "config_suppression_flag",
    "test_mutation",
    "fixture_injection",
]

COMMAND_PATTERNS = [
    re.compile(r"\bpython\s+-m\s+pytest\b[^\n\r;&|]*"),
    re.compile(r"\bpytest\b[^\n\r;&|]*"),
    re.compile(r"\btox\b[^\n\r;&|]*"),
    re.compile(r"\bnox\b[^\n\r;&|]*"),
    re.compile(r"\bhatch\s+run\b[^\n\r;&|]*"),
    re.compile(r"\bpdm\s+run\b[^\n\r;&|]*"),
    re.compile(r"\buv\s+run\b[^\n\r;&|]*"),
    re.compile(r"\bmake\s+(?:test|tests|check|ci)\b[^\n\r;&|]*"),
]


def _safe_text(path: Path, limit: int = 200_000) -> str:
    data = path.read_bytes()[:limit]
    return data.decode("utf-8", errors="replace")


def _source_files(root: Path) -> list[Path]:
    files: list[Path] = []
    for rel in ALLOWED_COMMAND_SOURCE_FILES:
        path = root / rel
        if path.is_file():
            files.append(path)
    for pattern in ALLOWED_COMMAND_SOURCE_GLOBS:
        for path in root.glob(pattern):
            if path.is_file() and ".git" not in path.parts:
                files.append(path)
    return sorted(set(files))


def inventory_project_metadata(root: Path) -> dict[str, object]:
    records = []
    for path in _source_files(root):
        rel = path.relative_to(root).as_posix()
        records.append({"path": rel, "sha256": sha256_file(path), "size_bytes": path.stat().st_size})
    return {"status": "PASS", "metadata_file_count": len(records), "records": records}


def inventory_test_tree(root: Path, limit: int = 200) -> dict[str, object]:
    tests = []
    for path in sorted(root.rglob("*.py")):
        rel = path.relative_to(root).as_posix()
        lowered = rel.lower()
        if ".git/" in lowered:
            continue
        if "/test" in f"/{lowered}" or "test_" in path.name.lower() or path.name.lower().startswith("test"):
            tests.append({"path": rel, "sha256": sha256_file(path), "size_bytes": path.stat().st_size})
        if len(tests) >= limit:
            break
    return {"status": "PASS", "test_file_count": len(tests), "records": tests}


def discover_command_sources(root: Path) -> dict[str, object]:
    records = []
    ci_records = []
    tool_records = []
    for path in _source_files(root):
        rel = path.relative_to(root).as_posix()
        text = _safe_text(path)
        commands: list[str] = []
        for pattern in COMMAND_PATTERNS:
            commands.extend(match.group(0).strip().strip("\"'") for match in pattern.finditer(text))
        unique = sorted(set(cmd for cmd in commands if cmd and "--ignore" not in cmd and "--override" not in cmd))
        if not unique and path.name in {"tox.ini", "pyproject.toml", "setup.cfg", "noxfile.py", "Makefile"}:
            unique = _infer_tool_commands(rel, text)
        if unique:
            record = {"path": rel, "sha256": sha256_file(path), "commands": unique[:20], "command_count": len(unique)}
            records.append(record)
            if rel.startswith(".github/workflows/"):
                ci_records.append(record)
            if path.name in {"tox.ini", "pyproject.toml", "setup.cfg", "noxfile.py", "Makefile"}:
                tool_records.append(record)
    return {
        "status": "PASS",
        "records": records,
        "command_source_count": len(records),
        "ci_workflow_records": ci_records,
        "tool_config_records": tool_records,
    }


def _infer_tool_commands(rel: str, text: str) -> list[str]:
    lowered = text.lower()
    commands: list[str] = []
    if rel == "tox.ini" and "[testenv" in lowered:
        commands.append("tox")
    if rel == "pyproject.toml" and ("pytest" in lowered or "[tool.pytest" in lowered):
        commands.append("python -m pytest")
    if rel == "setup.cfg" and ("pytest" in lowered or "[tool:pytest]" in lowered):
        commands.append("python -m pytest")
    if rel == "noxfile.py" and "pytest" in lowered:
        commands.append("nox")
    if rel == "Makefile" and re.search(r"^test[s]?:", text, re.MULTILINE):
        commands.append("make test")
    return sorted(set(commands))


def runner_declared(command_records: Iterable[dict[str, object]]) -> bool:
    text = " ".join(" ".join(record.get("commands", [])) for record in command_records)
    return any(token in text for token in ["pytest", "tox", "nox", "hatch", "pdm", "uv", "make test"])


def recover_command_decision(
    *,
    candidate_id: str,
    command_inventory: dict[str, object],
    test_tree_inventory: dict[str, object],
    runtime_connector_required: bool = False,
) -> dict[str, object]:
    records = command_inventory.get("records") or []
    runner = runner_declared(records if isinstance(records, list) else [])
    test_tree_present = int(test_tree_inventory.get("test_file_count") or 0) > 0
    if runtime_connector_required:
        return {
            "status": "BLOCK",
            "candidate_id": candidate_id,
            "exact_command_found": False,
            "bounded_synthesized_command_created": False,
            "runner_declared_by_metadata": runner,
            "test_target_declared_by_metadata": False,
            "test_tree_present": test_tree_present,
            "command_manifest_status": "BLOCK",
            "exact_blocker": "nki_library_runtime_connector_required",
            "terminal_state": "runtime_connector_required",
            "next_allowed_candidate_action": "batch068c_runtime_connector_readiness_buildout",
        }
    if runner and test_tree_present:
        return {
            "status": "BLOCK",
            "candidate_id": candidate_id,
            "exact_command_found": False,
            "bounded_synthesized_command_created": False,
            "runner_declared_by_metadata": True,
            "test_target_declared_by_metadata": False,
            "test_tree_present": True,
            "command_manifest_status": "BLOCK",
            "exact_blocker": f"{_candidate_prefix(candidate_id)}_native_test_command_unrecoverable_without_manual_artifact",
            "terminal_state": "manual_artifact_required",
            "next_allowed_candidate_action": "batch068b_manual_artifact_and_external_source_custody_intake",
        }
    return {
        "status": "BLOCK",
        "candidate_id": candidate_id,
        "exact_command_found": False,
        "bounded_synthesized_command_created": False,
        "runner_declared_by_metadata": runner,
        "test_target_declared_by_metadata": False,
        "test_tree_present": test_tree_present,
        "command_manifest_status": "BLOCK",
        "exact_blocker": f"{_candidate_prefix(candidate_id)}_native_test_command_unrecoverable_without_manual_artifact",
        "terminal_state": "manual_artifact_required",
        "next_allowed_candidate_action": "batch068b_manual_artifact_and_external_source_custody_intake",
    }


def _candidate_prefix(candidate_id: str) -> str:
    if "aiosmtpd" in candidate_id:
        return "aiosmtpd"
    if "streamflow" in candidate_id:
        return "streamflow"
    if "biface" in candidate_id:
        return "biface_i18n"
    return candidate_id
