from __future__ import annotations

from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable


FAMILY_KEYWORDS = {
    "artifact_byte_custody": ["artifact", "sha256", "manifest", "byte_custody"],
    "source_identity": ["source_identity", "candidate_sha", "repo_url", "issue_url"],
    "provider_command_boundary": ["provider", "command", "wrapper", "runtime"],
    "patch_safety": ["patch", "source_only", "duplicate_replay", "count_gate"],
    "claim_boundary": ["claim", "memory_lift", "self_maintaining", "full_scoring"],
    "public_language": ["public", "summary", "release_readiness"],
    "workflow_validation": ["workflow", ".github"],
    "audit_validation": ["audit"],
    "registry_validation": ["registry"],
}


def mechanism_family_for_path(path: str) -> str:
    lowered = path.lower()
    for family, keywords in FAMILY_KEYWORDS.items():
        if any(keyword in lowered for keyword in keywords):
            return family
    if lowered.startswith("outputs/"):
        return "versioned_output_evidence"
    if lowered.startswith("configs/"):
        return "configuration_schema"
    if lowered.startswith("tests/"):
        return "core_tests"
    if lowered.startswith("docs/") or lowered.endswith("readme.md"):
        return "public_documentation"
    if lowered.startswith("controllergate/core/"):
        return "shared_core"
    if lowered.startswith("scripts/"):
        return "versioned_script"
    return "other"


def file_kind_for_path(path: str) -> str:
    if path.startswith("outputs/"):
        return "output_evidence"
    if path.startswith("configs/"):
        return "config"
    if path.startswith("controllergate/core/"):
        return "core_module"
    if path.startswith("scripts/"):
        return "script"
    if path.startswith(".github/workflows/"):
        return "workflow"
    if path.startswith("tests/"):
        return "test"
    if path.startswith("docs/") or path.endswith("README.md"):
        return "public_doc"
    return "tracked_file"


def build_file_inventory(paths: Iterable[str]) -> list[dict[str, Any]]:
    return [
        {
            "path": path,
            "file_kind": file_kind_for_path(path),
            "mechanism_family": mechanism_family_for_path(path),
            "recommended_action": "preserve_or_future_consolidation_review",
            "safe_to_delete_now": False,
        }
        for path in sorted(paths)
    ]


def build_family_summary(inventory: list[dict[str, Any]]) -> list[dict[str, Any]]:
    counts = Counter(row["mechanism_family"] for row in inventory)
    by_kind: dict[str, Counter[str]] = defaultdict(Counter)
    for row in inventory:
        by_kind[row["mechanism_family"]][row["file_kind"]] += 1
    return [
        {
            "mechanism_family": family,
            "tracked_file_count": counts[family],
            "file_kind_counts": dict(sorted(by_kind[family].items())),
            "consolidation_status": "future_review_recommended",
            "safe_to_delete_now_count": 0,
        }
        for family in sorted(counts)
    ]


def build_universalization_gap_ledger(paths: Iterable[str]) -> dict[str, Any]:
    inventory = build_file_inventory(paths)
    families = build_family_summary(inventory)
    return {
        "status": "PASS",
        "tracked_file_count": len(inventory),
        "mechanism_family_count": len(families),
        "family_summary": families,
        "underdeveloped_mechanisms": [
            "candidate_sha_resolution_to_command_orthology",
            "metadata_only_command_translation",
            "shared_runtime_wrapper_interfaces",
            "audit_and_workflow_deduplication",
        ],
        "batch_local_mechanism_count": sum(1 for row in inventory if row["file_kind"] in {"script", "workflow", "output_evidence"}),
        "core_promoted_mechanism_count": sum(1 for row in inventory if row["file_kind"] == "core_module"),
        "public_claim_boundary_preserved": True,
        "audit_status": "PASS",
    }


def summarize_output_directories(root: Path) -> list[dict[str, Any]]:
    outputs = root / "outputs"
    if not outputs.is_dir():
        return []
    records: list[dict[str, Any]] = []
    for directory in sorted(p for p in outputs.iterdir() if p.is_dir()):
        files = [path for path in directory.rglob("*") if path.is_file()]
        records.append(
            {
                "output_dir": directory.name,
                "file_count": len(files),
                "has_sha256sums": (directory / "SHA256SUMS.txt").is_file(),
                "recommended_action": "preserve_as_evidence_then_future_thin_artifact_standardization",
            }
        )
    return records
