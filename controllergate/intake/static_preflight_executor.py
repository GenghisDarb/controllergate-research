from __future__ import annotations

from pathlib import Path
from typing import Any

from controllergate.intake.command_resolution_v2 import resolve_command_v2
from controllergate.intake.preflight_terminal_registry import terminal_record
from controllergate.intake.provider_dry_lock import build_provider_dry_lock
from controllergate.intake.source_object_verifier import verify_source_object
from controllergate.intake.static_collection_runner import run_static_collection
from controllergate.intake.target_resolution_v2 import resolve_target_v2


def execute_static_preflight(
    lead: dict[str, Any], workspace: Path, *, issue_snapshot: dict[str, Any], platform: dict[str, Any], runtime: dict[str, Any]
) -> dict[str, Any]:
    source = verify_source_object(str(lead["repo_url"]), str(lead["candidate_sha"]), workspace)
    stages: dict[str, dict[str, Any]] = {
        "issue_snapshot": issue_snapshot,
        "source": source,
        "runtime": runtime,
        "contamination": lead.get("contamination", {"status": "CLEAN"}),
    }
    target: dict[str, Any] = {"status": "NOT_RUN", "blocker": "source_verification_required"}
    command: dict[str, Any] = {"status": "NOT_RUN", "blocker": "target_resolution_required"}
    dry_lock: dict[str, Any] = {"status": "NOT_RUN", "blocker": "source_verification_required"}
    collection: dict[str, Any] = {"status": "NOT_RUN", "blocker": "command_resolution_required", "target_executed": False}
    if source.get("status") == "PASS":
        evidence = str(issue_snapshot.get("sanitized_text") or issue_snapshot.get("evidence_text") or lead.get("evidence_text") or "")
        target = resolve_target_v2(workspace, evidence, str(lead["candidate_sha"]))
        dry_lock = build_provider_dry_lock(workspace, runtime=runtime, platform=platform)
        if target.get("status") == "PASS":
            command = resolve_command_v2(workspace, str(target["target"]))
            if command.get("status") == "PASS" and dry_lock.get("status") == "PASS":
                collection = run_static_collection(workspace, command, str(target["target"]))
    stages.update({"target": target, "command": command, "provider_dry_lock": dry_lock, "collection": collection})
    terminal = terminal_record(str(lead["candidate_id"]), stages)
    return {"candidate_id": lead["candidate_id"], "stages": stages, "terminal": terminal}
