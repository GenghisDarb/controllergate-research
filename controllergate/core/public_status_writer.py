from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from .evidence import write_text_lf


PUBLIC_STATUS_FILES: tuple[str, ...] = (
    "README.md",
    "docs/current_status.md",
    "docs/capability_inventory.md",
    "docs/technical_validation_gap_report.md",
    "controllergate_v1_7_beta/reports/critic_review_package/shareable_summary.md",
)


def replace_section(path: str | Path, marker: str, lines: list[str]) -> dict[str, Any]:
    target = Path(path)
    if not target.is_file():
        return {"path": str(target), "status": "MISSING"}
    text = target.read_text(encoding="utf-8")
    batch_match = re.search(r"\b(Batch05[23])\b", marker)
    target_batch = batch_match.group(1) if batch_match else None
    kept: list[str] = []
    skipping = False
    stale_removed = False
    for line in text.splitlines():
        is_heading = bool(re.match(r"^#+\s+", line))
        is_target_heading = line.strip() == marker or (
            target_batch is not None and is_heading and re.search(rf"\b{target_batch}\b", line)
        )
        if is_target_heading:
            skipping = True
            stale_removed = True
            continue
        if skipping and is_heading:
            skipping = False
        if not skipping:
            kept.append(line)
    text = "\n".join(kept).rstrip()
    replacement = "\n".join(["", marker, "", *lines]).rstrip() + "\n"
    write_text_lf(target, text.rstrip() + "\n" + replacement)
    return {"path": str(target), "status": "PASS", "stale_section_removed": stale_removed}


def batch052_official_status_lines(batch052_state: dict[str, Any]) -> list[str]:
    return [
        f"- Batch052 status: `{batch052_state['status']}`.",
        f"- Current protocol remains: `{batch052_state['current_protocol']}`.",
        f"- Source-only suitability: `{batch052_state['source_only_suitability_classification']}`.",
        f"- Patch generation status: `{batch052_state['patch_generation_status']}`.",
        f"- Patch apply status: `{batch052_state['patch_apply_status']}`.",
        f"- Post-repair target replay status: `{batch052_state['post_repair_target_replay_status']}`.",
        f"- Duplicate replay status: `{batch052_state['duplicate_replay_status']}`; reason: `{batch052_state['duplicate_replay_not_run_reason']}`.",
        f"- Exact blocker: `{batch052_state['exact_blocker']}`.",
        f"- Next allowed action: `{batch052_state['next_allowed_action']}`.",
        f"- External native repair episodes remain `{batch052_state['native_external_repair_episode_count']}`; issue-derived repair episodes remain `{batch052_state['issue_derived_repair_episode_count']}`.",
        "- Batch052 does not run duplicate replay, full scoring, memory-lift claims, self-maintaining claims, or production-readiness claims.",
    ]


def batch053_status_lines(batch053_state: dict[str, Any]) -> list[str]:
    return [
        f"- Batch053 status: `{batch053_state['status']}`.",
        f"- Current protocol remains: `{batch053_state['current_protocol']}`.",
        f"- Duplicate clean replay status: `{batch053_state['duplicate_replay_status']}`.",
        f"- Duplicate clean replay return code: `{batch053_state['duplicate_replay_return_code']}`.",
        f"- Issue-derived repair validated candidate: `{str(batch053_state['issue_derived_repair_validated_candidate']).lower()}`.",
        f"- Exact blocker: `{batch053_state['exact_blocker']}`.",
        f"- Next allowed action: `{batch053_state['next_allowed_action']}`.",
        f"- External native repair episodes remain `{batch053_state['native_external_repair_episode_count']}`; issue-derived repair episodes remain `{batch053_state['issue_derived_repair_episode_count']}`.",
        "- Batch053 does not increment repair counts, run full scoring, claim memory lift, claim self-maintaining software, or claim production readiness.",
    ]


def reconcile_batch052_public_status(root: Path, batch052_state: dict[str, Any]) -> dict[str, Any]:
    marker = "### Batch052 Lemon Reader source-only patch candidate gate"
    results = [
        replace_section(root / rel, marker, batch052_official_status_lines(batch052_state))
        for rel in PUBLIC_STATUS_FILES
    ]
    return {
        "status": "PASS" if all(item["status"] == "PASS" for item in results) else "BLOCK",
        "marker": marker,
        "results": results,
        "artifact_internal_state_wins": True,
        "retired_public_state_drift": True,
        "current_protocol_wording": "Current protocol remains: v2.14",
        "exact_blocker": None if all(item["status"] == "PASS" for item in results) else "public_status_file_missing",
    }


def append_batch053_public_status(root: Path, batch053_state: dict[str, Any]) -> dict[str, Any]:
    marker = "### Batch053 duplicate clean replay and evidence contract hardening"
    results = [
        replace_section(root / rel, marker, batch053_status_lines(batch053_state))
        for rel in PUBLIC_STATUS_FILES
    ]
    return {
        "status": "PASS" if all(item["status"] == "PASS" for item in results) else "BLOCK",
        "marker": marker,
        "results": results,
        "current_protocol_wording": "Current protocol remains: v2.14",
        "exact_blocker": None if all(item["status"] == "PASS" for item in results) else "public_status_file_missing",
    }


def audit_public_status_after_ingest(root: Path) -> dict[str, Any]:
    failures: list[str] = []
    for rel in (
        "README.md",
        "docs/current_status.md",
        "controllergate_v1_7_beta/reports/critic_review_package/shareable_summary.md",
    ):
        path = root / rel
        text = path.read_text(encoding="utf-8") if path.is_file() else ""
        batch052_index = text.rfind("### Batch052 Lemon Reader source-only patch candidate gate")
        section = text[batch052_index:] if batch052_index >= 0 else text
        batch053_index = section.find("### Batch053 ")
        if batch053_index >= 0:
            section = section[:batch053_index]
        if "Current protocol remains: `v2.14`" not in section:
            failures.append(f"{rel}:current_protocol_wording_missing")
        if "PASS_WITH_BATCH052_TARGET_REPLAY_PASSED" not in section:
            failures.append(f"{rel}:batch052_target_pass_missing")
        if "host_environment_not_ubuntu_latest_python311" in section:
            failures.append(f"{rel}:stale_host_blocker_present")
        if "target_replay_not_passed" in section:
            failures.append(f"{rel}:stale_target_replay_not_passed_present")
    return {
        "status": "PASS" if not failures else "BLOCK",
        "failures": failures,
        "official_artifact_supersedes_stale_public_state": True,
        "exact_blocker": None if not failures else "public_state_reconciliation_failed",
    }
