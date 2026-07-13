from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import Any

from controllergate.core.evidence import hash_record

from .dependency_graph import DependencyGraph
from .historical_lock_verifier import verify_historical_lock
from .historical_metadata import canonicalize_name


TARGET_ENVIRONMENT = {"python_version": "3.13", "python_full_version": "3.13.0b2", "implementation_name": "cpython", "implementation_version": "3.13.0b2", "platform_machine": "x86_64", "sys_platform": "linux", "platform_system": "Linux", "os_name": "posix"}


def resolve_from_verified_roots(root_records: list[dict[str, Any]], cutoff: str) -> dict[str, Any]:
    graph = DependencyGraph(); selected = []; unresolved = []; trace = []
    for record in sorted(root_records, key=lambda item: canonicalize_name(str(item["package"]))):
        package = canonicalize_name(str(record["package"])); graph.add_node(package, version=record.get("selected_version"), artifact=record.get("selected_filename"), dependency_metadata_status="NOT_ESTABLISHED")
        selected.append({"package": package, "version": record.get("selected_version"), "filename": record.get("selected_filename"), "artifact_type": "sdist" if str(record.get("selected_filename", "")).endswith((".tar.gz", ".zip")) else "wheel", "upload_timestamp": record.get("selected_upload_time"), "sha256": record.get("selected_artifact_sha256"), "source_url": record.get("metadata_url"), "metadata_sha256": record.get("metadata_sha256"), "requires_python": None, "parent_dependency_edges": [], "selection_reason": "verified direct root artifact before cutoff", "later_versions_excluded": record.get("later_artifact_count_excluded", 0)})
        unresolved.append({"package": package, "classification": "unresolved_dynamic_metadata", "blocker": "selected_historical_artifact_dependency_metadata_not_present_in_verified_evidence", "reopen_condition": "hash_verified_static_artifact_metadata_or_isolated_metadata_capsule"})
        trace.append({"package": package, "decision": "direct_artifact_preserved_transitive_expansion_blocked", "input_metadata_hash": record.get("metadata_sha256")})
    lock = {"status": "BLOCK", "cutoff": cutoff, "target_environment": TARGET_ENVIRONMENT, "selected_artifacts": selected, "unresolved_nodes": unresolved, "unsatisfied_constraints": [], "runtime_dependency_closure": "NOT_ESTABLISHED", "build_dependency_closure": "NOT_ESTABLISHED", "post_cutoff_selected_artifact_count": 0}
    verification = verify_historical_lock(lock, cutoff)
    return {"graph": graph.as_dict(), "trace": trace, "lock": lock, "verification": verification, "next_allowed_action": "batch068h4_dynamic_historical_metadata_recovery"}


def resolve_historical_provider(
    artifacts: Iterable[Mapping[str, Any]], *, runtime: str, cutoff: str
) -> dict[str, Any]:
    """Select only hash-identified artifacts compatible with a frozen runtime and cutoff."""
    compatible = [
        dict(item) for item in artifacts
        if runtime in item.get("compatible_runtimes", []) and str(item.get("released_at", "")) <= cutoff
    ]
    passed = bool(compatible) and all(item.get("sha256") for item in compatible)
    result = {
        "status": "PASS" if passed else "BLOCK",
        "runtime": runtime,
        "cutoff": cutoff,
        "artifacts": compatible,
        "current_unrestricted_resolution_used": False,
        "executed_lock_mutated": False,
        "lock_versioning_required_for_change": True,
    }
    result["provider_lock_hash"] = hash_record(result)
    return result
