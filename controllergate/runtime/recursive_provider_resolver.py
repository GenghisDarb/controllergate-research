from __future__ import annotations

from pathlib import Path
from typing import Any

from packaging.requirements import Requirement

from .artifact_metadata_reader import read_artifact_metadata
from .historical_metadata import canonicalize_name
from .release_catalog import acquire_artifact, enumerate_release_files, select_release_file
from .requirement_expander import applicable_requirement
from .resolution_state import ResolutionState


def resolve_recursive(root_records: list[dict[str, Any]], *, cutoff: str, store: Path, max_packages: int = 120) -> dict[str, Any]:
    state = ResolutionState(); queue: list[tuple[str, str, str, str]] = []
    for root in root_records:
        req = Requirement(str(root["normalized_requirement"])); name = canonicalize_name(req.name); dependency_class = str(root["dependency_class"])
        entry = {"raw": str(req), "specifier": str(req.specifier), "parent": "ROOT", "dependency_class": dependency_class, "extras": sorted(req.extras), "marker": str(req.marker) if req.marker else None}
        state.requirements.setdefault(name, []).append(entry); queue.append((name, "ROOT", dependency_class, str(req)))
    processed_signatures: dict[str, tuple[str, ...]] = {}
    catalogs: dict[str, dict[str, Any]] = {}; artifact_acquisitions = []; static_metadata = []
    while queue and len(state.selected) + len(state.unresolved) < max_packages:
        name, parent, dependency_class, raw = queue.pop(0); signature = tuple(sorted(item["raw"] for item in state.requirements[name]))
        if processed_signatures.get(name) == signature: continue
        previous = state.selected.get(name); catalog = catalogs.get(name) or enumerate_release_files(name, cutoff, store / "pypi_json"); catalogs[name] = catalog
        selection = select_release_file(catalog, [item["specifier"] for item in state.requirements[name]], "3.13.0b2")
        if selection is None:
            conflict = {"package": name, "requirements": list(state.requirements[name]), "minimal_unsatisfied_constraint_set": list(signature)}; state.conflicts.append(conflict); state.trace.append({"package": name, "decision": "BLOCK", "reason": "no_cutoff_compatible_artifact"}); break
        if previous and previous["filename"] != selection["filename"]: state.backtracking.append({"package": name, "from": previous["filename"], "to": selection["filename"], "reason": "merged_constraints_changed_selection"})
        acquisition = acquire_artifact(selection, store); artifact_acquisitions.append({"package": name, **acquisition, "filename": selection["filename"], "upload_timestamp": selection["upload_timestamp"], "artifact_file_url": selection["artifact_file_url"]})
        if acquisition["status"] != "PASS": state.unresolved.append({"package": name, "blocker": "artifact_hash_or_size_verification_failed"}); break
        metadata = read_artifact_metadata(Path(acquisition["path"])); static_metadata.append({"package": name, "filename": selection["filename"], **metadata})
        if metadata.get("status") == "BLOCK": state.unresolved.append({"package": name, "blocker": metadata.get("blocker"), "artifact": selection}); state.trace.append({"package": name, "decision": "BLOCK", "reason": metadata.get("blocker")}); break
        state.selected[name] = {**selection, "metadata_status": "PASS", "artifact_path": acquisition["path"], "parent_dependency_edges": sorted({item["parent"] for item in state.requirements[name]}), "dependency_classes": sorted({item["dependency_class"] for item in state.requirements[name]})}
        state.metadata[name] = metadata; processed_signatures[name] = signature; state.trace.append({"package": name, "decision": "SELECT", "filename": selection["filename"], "requirement_count": len(signature), "metadata_status": "PASS"})
        requested_extras = {extra for item in state.requirements[name] for extra in item.get("extras", [])}
        children = list(metadata.get("requires_dist") or []) + list(metadata.get("build_requires") or [])
        for child_raw in children:
            child = applicable_requirement(str(child_raw), requested_extras)
            if not child["applies"]: continue
            child_name = str(child["name"]); child_class = "build" if child_raw in (metadata.get("build_requires") or []) else dependency_class
            if child_name == name: state.cycles.append({"path": [name, child_name], "classification": "self_cycle"}); continue
            edge = {"parent": name, "child": child_name, "requirement": child_raw, "dependency_class": child_class}
            if edge not in state.edges: state.edges.append(edge)
            entry = {"raw": str(child_raw), "specifier": str(child["specifier"]), "parent": name, "dependency_class": child_class, "extras": child["extras"], "marker": child["marker"]}
            if entry not in state.requirements.setdefault(child_name, []): state.requirements[child_name].append(entry); queue.append((child_name, name, child_class, str(child_raw)))
    if queue and len(state.selected) + len(state.unresolved) >= max_packages: state.unresolved.append({"package": None, "blocker": "provider_resolution_package_budget_exhausted", "remaining_queue": len(queue)})
    unresolved_dependencies = sorted(set(state.requirements) - set(state.selected))
    complete = not state.unresolved and not state.conflicts and not unresolved_dependencies and not queue
    by_class = {kind: sorted(name for name, item in state.selected.items() if kind in item["dependency_classes"]) for kind in ["runtime", "test", "build"]}
    lock = {"status": "PASS" if complete else "BLOCK", "cutoff": cutoff, "selected_artifacts": state.selected, "metadata_established_package_count": len(state.metadata), "unresolved_metadata_nodes": state.unresolved, "unresolved_dependency_nodes": unresolved_dependencies, "constraint_conflicts": state.conflicts, "post_cutoff_selected_artifact_count": sum(not item["cutoff_eligible"] for item in state.selected.values()), "runtime_dependency_closure": "PASS" if complete and all(name in state.selected for name in by_class["runtime"]) else "NOT_ESTABLISHED", "test_dependency_closure": "PASS" if complete and all(name in state.selected for name in by_class["test"]) else "NOT_ESTABLISHED", "build_dependency_closure": "PASS" if complete and all(name in state.selected for name in by_class["build"]) else "NOT_ESTABLISHED"}
    graph = {"status": "PASS" if complete else "PARTIAL", "node_count": len(state.selected), "edge_count": len(state.edges), "nodes": state.selected, "edges": state.edges, "runtime_nodes": by_class["runtime"], "test_nodes": by_class["test"], "build_nodes": by_class["build"]}
    return {"status": lock["status"], "graph": graph, "lock": lock, "trace": state.trace, "backtracking": state.backtracking, "cycles": state.cycles, "catalogs": catalogs, "artifact_acquisitions": artifact_acquisitions, "static_metadata": static_metadata, "next_blocker": (state.unresolved[0]["blocker"] if state.unresolved else ("constraint_conflict" if state.conflicts else None))}
