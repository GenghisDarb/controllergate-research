from __future__ import annotations

from pathlib import Path

DEFAULT_BATCH008_PATCH_DENYLIST = [
    "outputs/clean_replication_batch_008/assembled_patch_batch008.diff",
    "outputs/clean_replication_batch_008/assembled_patch_batch008_sha256.txt",
    "outputs/clean_replication_batch_008/fragment_patch_candidates_batch008.json",
    "outputs/clean_replication_batch_008/fragment_safety_audits_batch008.json",
    "outputs/clean_replication_batch_008/proof_chain_lock_batch008.json",
    "outputs/clean_replication_batch_008/target_validation_result_batch008.json",
    "outputs/clean_replication_batch_008/duplicate_replay_result_batch008.json",
]


def normalize_repo_path(path: str | Path) -> str:
    return str(path).replace("\\", "/").lstrip("./")


def build_patch_artifact_denylist(extra_paths: list[str] | None = None) -> dict[str, object]:
    paths = list(DEFAULT_BATCH008_PATCH_DENYLIST)
    if extra_paths:
        paths.extend(extra_paths)
    return {
        "status": "PASS",
        "denylist": sorted(dict.fromkeys(normalize_repo_path(path) for path in paths)),
        "reason": "exclude prior successful repair artifacts from retrospective matched-null arms",
    }


def context_manifest_excludes_denied(manifest: dict[str, object], denied_paths: list[str]) -> bool:
    denied = {normalize_repo_path(path) for path in denied_paths}
    paths: set[str] = set()
    for key in ["allowed_context_paths", "loaded_context_paths", "excluded_context_paths"]:
        values = manifest.get(key, [])
        if isinstance(values, list) and key != "excluded_context_paths":
            paths.update(normalize_repo_path(str(value)) for value in values)
    return paths.isdisjoint(denied)


def audit_patch_quarantine(manifests: list[dict[str, object]], denylist: dict[str, object]) -> dict[str, object]:
    denied_paths = [str(path) for path in denylist.get("denylist", []) if isinstance(path, str)]
    per_manifest = [
        {
            "arm": manifest.get("arm"),
            "denied_paths_excluded": context_manifest_excludes_denied(manifest, denied_paths),
            "reads_successful_patch": manifest.get("reads_successful_patch") is True,
            "reads_patch_rationale": manifest.get("reads_patch_rationale") is True,
        }
        for manifest in manifests
    ]
    status = "PASS" if all(
        item["denied_paths_excluded"] and not item["reads_successful_patch"] and not item["reads_patch_rationale"]
        for item in per_manifest
    ) else "FAIL"
    return {
        "status": status,
        "blocker": None if status == "PASS" else "matched_null_patch_quarantine_failed",
        "per_manifest": per_manifest,
        "denylist_count": len(denied_paths),
    }
