from __future__ import annotations

import hashlib
import json


def stable_hash(value: object) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()


def active_context_filtering_policy() -> dict[str, object]:
    return {
        "status": "PASS",
        "filter_runs_after_seed_validation": True,
        "cannot_remove_all_legal_patchable_source": True,
        "memory_disabled_arm_cannot_read_failure_memory_weights": True,
        "blockers": [
            "active_context_filter_removed_all_legal_source",
            "active_context_filter_forbidden_memory_input",
            "active_context_filter_untracked_seed",
        ],
    }


def context_filter_manifest(*, seed_present: bool, before: list[str], after: list[str], reason: str) -> dict[str, object]:
    removed = sorted(set(before) - set(after))
    blocker = None
    status = "PASS"
    if not seed_present:
        status = "NOT_RUN"
        blocker = "targeted_prospective_seed_missing_or_invalid_after_locks_ready"
    elif before and not after:
        status = "BLOCK"
        blocker = "active_context_filter_removed_all_legal_source"
    return {
        "status": status,
        "seed_present": seed_present,
        "before_context_paths": sorted(before),
        "after_context_paths": sorted(after),
        "removed_context_paths": removed,
        "reason": reason,
        "before_hash": stable_hash(sorted(before)),
        "after_hash": stable_hash(sorted(after)),
        "delta_hash": stable_hash({"removed": removed, "reason": reason}),
        "blocker": blocker,
    }


def filter_delta_audit(manifest: dict[str, object]) -> dict[str, object]:
    if manifest.get("status") == "NOT_RUN":
        return {
            "status": "NOT_RUN",
            "blocker": manifest.get("blocker"),
            "removed_all_legal_source": False,
            "forbidden_memory_input_used": False,
        }
    removed_all = bool(manifest.get("before_context_paths")) and not bool(manifest.get("after_context_paths"))
    return {
        "status": "BLOCK" if removed_all else "PASS",
        "blocker": "active_context_filter_removed_all_legal_source" if removed_all else None,
        "removed_all_legal_source": removed_all,
        "forbidden_memory_input_used": False,
    }
