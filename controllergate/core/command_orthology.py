from __future__ import annotations

import re
import shlex
from typing import Any

from .test_framework_detector import detect_framework_from_record


COMMAND_CONFIDENCE_LEVELS = [
    "exact_declared_command",
    "high_confidence_project_local_inference",
    "medium_confidence_requires_manual_artifact",
    "low_confidence_routing_only",
    "blocked_forbidden_or_untrusted",
]

SOURCE_PRECEDENCE = {
    "tox.ini": 10,
    "noxfile.py": 20,
    "pyproject.toml": 30,
    "setup.cfg": 40,
    "pytest.ini": 50,
    "ci_workflow": 60,
    "project_local_testing_docs": 70,
    "verified_non_circular_benchmark_metadata": 80,
}

UNSAFE_TOKENS = {"|", "||", "&&", ";", ">", ">>", "<", "$(", "`"}
UNSAFE_PREFIXES = ("--ignore", "--override", "--rootdir")


def normalize_argv(command: str | list[str]) -> list[str]:
    """Return a platform-neutral argv representation without executing it."""
    if isinstance(command, list):
        return [str(item) for item in command]
    try:
        return shlex.split(command, posix=True)
    except ValueError:
        return []


def command_token_safety(argv: list[str]) -> dict[str, Any]:
    joined = " ".join(argv)
    unsafe = [token for token in argv if token in UNSAFE_TOKENS]
    unsafe.extend(token for token in argv if token.startswith(UNSAFE_PREFIXES))
    if "$((" in joined or "$(" in joined or "${" in joined or "PYTHONPATH=" in joined:
        unsafe.append("shell_or_environment_expansion")
    if any("*" in token for token in argv):
        unsafe.append("unbounded_globbing")
    return {
        "status": "PASS" if not unsafe else "BLOCK",
        "argv": argv,
        "unsafe_tokens": sorted(set(unsafe)),
        "blocker": None if not unsafe else "unsafe_command_tokens",
    }


def rank_command_candidates(candidates: list[dict[str, Any]]) -> dict[str, Any]:
    """Rank commands deterministically while retaining authoritative conflicts."""
    normalized: list[dict[str, Any]] = []
    for item in candidates:
        record = dict(item)
        record["argv"] = normalize_argv(record.get("argv") or record.get("command") or [])
        record["token_safety"] = command_token_safety(record["argv"])
        source_class = str(record.get("source_class") or record.get("source_path") or "")
        record["precedence"] = SOURCE_PRECEDENCE.get(source_class, 90)
        normalized.append(record)
    ranked = sorted(
        normalized,
        key=lambda item: (
            item["precedence"],
            str(item.get("source_path", "")),
            tuple(item["argv"]),
        ),
    )
    safe = [item for item in ranked if item["token_safety"]["status"] == "PASS" and item["argv"]]
    selected = safe[0] if safe else None
    conflicts: list[dict[str, Any]] = []
    if selected:
        same_precedence = [item for item in safe if item["precedence"] == selected["precedence"]]
        unique = {tuple(item["argv"]) for item in same_precedence}
        if len(unique) > 1:
            conflicts = same_precedence
            selected = None
    return {
        "ranked_candidates": ranked,
        "selected": selected,
        "selection_confidence": "deterministic_source_precedence" if selected else "manual_review_required",
        "conflicts": conflicts,
        "status": "PASS" if selected else "MANUAL_REVIEW",
    }


def extract_command_candidates(path: str, text: str, target_paths: list[str]) -> list[dict[str, Any]]:
    """Extract statically declared commands from pinned project metadata."""
    candidates: list[dict[str, Any]] = []
    source_class = (
        "ci_workflow" if path.startswith(".github/workflows/")
        else "project_local_testing_docs" if path.lower().endswith((".md", ".rst"))
        else path.lower()
    )
    command_lines: list[str] = []
    if path.lower() == "tox.ini":
        command_lines.extend(match.strip() for match in re.findall(r"(?mi)^\s*commands\s*=\s*([^\n]+)", text))
        if "[testenv" in text.lower():
            command_lines.append("python -m pytest")
    elif path.lower() == "noxfile.py":
        command_lines.extend("python -m pytest " + match.strip(" '\"") for match in re.findall(r"session\.run\(\s*['\"]pytest['\"]\s*(?:,\s*([^\)]*))?\)", text))
    elif path.lower() in {"pyproject.toml", "setup.cfg", "pytest.ini"}:
        if re.search(r"(?i)(pytest|tool\.pytest|pytest\.ini_options)", text):
            command_lines.append("python -m pytest")
    elif source_class in {"ci_workflow", "project_local_testing_docs"}:
        command_lines.extend(
            match.strip()
            for match in re.findall(r"(?mi)^\s*(?:run:\s*|\$\s*)?((?:python\s+-m\s+)?(?:pytest|tox|nox)(?:\s+[^\n#]+)?)", text)
        )
    for raw in command_lines:
        cleaned = re.sub(r"\$\{\{[^}]+\}\}", "", raw).strip()
        argv = normalize_argv(cleaned)
        if not argv:
            continue
        if target_paths and argv[-1] not in target_paths and any(token in {"pytest", "py.test"} for token in argv):
            argv = argv + [target_paths[0]]
        candidates.append({
            "source_path": path,
            "source_class": source_class,
            "argv": argv,
            "working_directory": ".",
            "target_path_corroborated": bool(target_paths and target_paths[0] in argv),
        })
    unique: dict[tuple[str, ...], dict[str, Any]] = {}
    for item in candidates:
        unique.setdefault(tuple(item["argv"]), item)
    return list(unique.values())


def has_verified_sha(record: dict[str, Any]) -> bool:
    sha = record.get("candidate_sha") or record.get("verified_candidate_sha")
    return isinstance(sha, str) and re.fullmatch(r"[0-9a-f]{40}", sha) is not None


def infer_command_orthology(record: dict[str, Any]) -> dict[str, Any]:
    framework = detect_framework_from_record(record)
    confidence = framework["confidence"]
    blockers: list[str] = []
    if not has_verified_sha(record):
        blockers.append("candidate_sha_still_missing")
        confidence = "low_confidence_routing_only"
    if record.get("missing_manual_artifact") or record.get("manual_artifact_required"):
        blockers.append("manual_artifact_still_required")
        confidence = "medium_confidence_requires_manual_artifact"
    if record.get("runtime_connector_required"):
        blockers.append("runtime_connector_still_required")
        confidence = "medium_confidence_requires_manual_artifact"
    if record.get("missing_environment") or record.get("missing_provider_capsule"):
        blockers.append("provider_or_environment_still_missing")
        if confidence != "medium_confidence_requires_manual_artifact":
            confidence = "low_confidence_routing_only"
    if record.get("approval_status") in {"rejected_future_or_gold_evidence", "rejected_untrusted_source"}:
        blockers.append("blocked_forbidden_or_untrusted")
        confidence = "blocked_forbidden_or_untrusted"
    approved_for_probe = confidence in {"exact_declared_command", "high_confidence_project_local_inference"} and not blockers
    return {
        "candidate_id": record.get("candidate_id"),
        "command_family": framework["test_framework_family"],
        "confidence": confidence,
        "confidence_levels": COMMAND_CONFIDENCE_LEVELS,
        "approved_for_future_provider_command_probe": approved_for_probe,
        "blockers": blockers,
        "allowed_use": "routing_and_future_provider_command_probe_only" if approved_for_probe else "routing_or_intake_only",
        "forbidden_use": ["patch_authority", "repair_proof", "count_gate_evidence", "memory_lift_evidence"],
        "audit_status": "PASS",
    }
