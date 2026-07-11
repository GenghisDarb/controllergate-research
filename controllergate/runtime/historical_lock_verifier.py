from __future__ import annotations

from .historical_metadata import parse_utc


def verify_historical_lock(lock: dict[str, object], cutoff: str) -> dict[str, object]:
    selected = list(lock.get("selected_artifacts") or [])
    unresolved = list(lock.get("unresolved_nodes") or [])
    conflicts = list(lock.get("unsatisfied_constraints") or [])
    post_cutoff = [item for item in selected if parse_utc(str(item["upload_timestamp"])) > parse_utc(cutoff)]
    missing_hashes = [item for item in selected if not item.get("sha256")]
    complete = not unresolved and not conflicts and not post_cutoff and not missing_hashes and lock.get("runtime_dependency_closure") == "PASS" and lock.get("build_dependency_closure") == "PASS"
    return {"status": "PASS" if complete else "BLOCK", "complete": complete, "unresolved_node_count": len(unresolved), "unsatisfied_constraint_count": len(conflicts), "post_cutoff_selected_artifact_count": len(post_cutoff), "missing_artifact_hash_count": len(missing_hashes), "runtime_dependency_closure": lock.get("runtime_dependency_closure"), "build_dependency_closure": lock.get("build_dependency_closure")}
