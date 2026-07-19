"""Persistent, append-only completion ledger validation."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


REQUIRED_GOALS = tuple(f"CG-GOAL-{index:03d}-{suffix}" for index, suffix in enumerate((
    "OFFICIAL-BATCH098-INGEST",
    "CONTRADICTION-ROOT-RECONSTRUCTION",
    "CAUSAL-EVIDENCE-HIERARCHY",
    "CORRECTED-CONSTRAINT-MODEL",
    "OFFICIAL-BATCH099-INGEST",
    "INCIDENT-IDENTITY-AND-PARITY",
    "TYPED-INCIDENT-REMATERIALIZATION",
    "MATCHED-COUNTERFACTUAL-EXECUTION",
    "CAUSAL-OWNERSHIP-CLOSURE",
    "ARCHITECTURE-GAIN",
    "TLD-ROUTING-GAIN",
    "BALANCED-HISTORICAL-COHORT",
    "ABSTENTION-REQUIRED-COHORT",
    "MIXED-FAILURE-COHORT",
    "PROSPECTIVE-VALIDATION",
    "MEMORY-LIFT-VALIDATION",
    "PROTECTED-REPAIR-ACTUATION",
    "EXTERNAL-REPLICATION",
    "PUBLIC-DEFAULT-NON-TLD-MODE",
    "PRODUCT-BETA",
    "SELF-MAINTAINING-SOFTWARE-EVIDENCE",
)))

ALLOWED_STATUSES = {"NOT_STARTED", "PROTOCOL_READY", "IN_PROGRESS", "BLOCKED", "COMPLETE_WITH_LIMITED_SCOPE", "COMPLETE", "REOPENED"}
REQUIRED_FIELDS = {"goal_id", "title", "status", "prerequisites", "required_evidence", "current_evidence", "evidence_hashes", "completion_commit", "completion_batch", "active_blockers", "reopen_conditions", "authority_allowed", "authority_forbidden", "last_updated_commit", "last_updated_timestamp"}


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validate_ledger(ledger: dict[str, Any], repository: Path, verify_files: bool = True) -> dict[str, Any]:
    errors: list[str] = []
    goals = ledger.get("goals", [])
    by_id = {goal.get("goal_id"): goal for goal in goals}
    if tuple(by_id) != REQUIRED_GOALS:
        missing = [goal for goal in REQUIRED_GOALS if goal not in by_id]
        extra = [goal for goal in by_id if goal not in REQUIRED_GOALS]
        errors.append(f"goal_set_or_order:{missing}:{extra}")
    for goal_id, goal in by_id.items():
        absent = sorted(REQUIRED_FIELDS - set(goal))
        if absent:
            errors.append(f"{goal_id}:missing_fields:{absent}")
        if goal.get("status") not in ALLOWED_STATUSES:
            errors.append(f"{goal_id}:invalid_status")
        if any(parent not in by_id for parent in goal.get("prerequisites", [])):
            errors.append(f"{goal_id}:missing_prerequisite")
        evidence = goal.get("current_evidence", [])
        hashes = goal.get("evidence_hashes", {})
        if goal.get("status") == "COMPLETE":
            if not evidence or not goal.get("completion_commit") or not goal.get("completion_batch"):
                errors.append(f"{goal_id}:complete_without_execution_evidence")
            if evidence and all(str(path).startswith("docs/") for path in evidence):
                errors.append(f"{goal_id}:documentation_only_completion")
        for relative in evidence:
            if relative not in hashes:
                errors.append(f"{goal_id}:missing_evidence_hash:{relative}")
                continue
            path = repository / relative
            if verify_files and (not path.is_file() or sha256_file(path) != hashes[relative]):
                errors.append(f"{goal_id}:evidence_hash_mismatch:{relative}")
        if not goal.get("active_blockers") and goal.get("status") in {"BLOCKED", "NOT_STARTED"}:
            errors.append(f"{goal_id}:blocker_silently_absent")
    if ledger.get("append_only") is not True:
        errors.append("append_only_not_asserted")
    if "Batch100" not in ledger.get("batch_output_links", {}):
        errors.append("current_batch_output_not_linked")
    return {"status": "PASS" if not errors else "BLOCK", "goal_count": len(goals), "errors": errors}


def load_and_validate(path: Path, repository: Path, verify_files: bool = True) -> dict[str, Any]:
    return validate_ledger(json.loads(path.read_text(encoding="utf-8")), repository, verify_files)
