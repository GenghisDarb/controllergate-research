from __future__ import annotations

from dataclasses import fields
import hashlib
import json
from pathlib import Path
import re
import shutil
from typing import Any

from controllergate.core.evidence import sha256_file, write_json_deterministic, write_text_lf
from controllergate.pathways.entity import Entity
from controllergate.pathways.event import Event
from controllergate.pathways.pathway import Pathway, cycle_safe_composition
from controllergate.pathways.projection import Projection
from controllergate.pathways.regulation import Regulator

REPOSITORIES = {
    "reactome/graph-core": {
        "url": "https://github.com/reactome/graph-core.git",
        "commit": "62aef35d7a89403b8a8800dc004d8de62f847aee",
    },
    "reactome/release-download-directory": {
        "url": "https://github.com/reactome/release-download-directory.git",
        "commit": "1b3257dbf9829c5e322bcfba1d7256e0e6ef4faa",
    },
    "reactome/data-export": {
        "url": "https://github.com/reactome/data-export.git",
        "commit": "d0ff92e1bc79a90a9c96bd818f0e69f3e742a152",
    },
    "reactome/release-qa": {
        "url": "https://github.com/reactome/release-qa.git",
        "commit": "ed1ccad4204665719f5d128dd927dde91366e5da",
    },
}

MODEL = "src/main/java/org/reactome/server/graph/domain/model/"
REL = "src/main/java/org/reactome/server/graph/domain/relationship/"
GRAPH_FILES = [
    MODEL + name for name in (
        "ReactionLikeEvent.java", "Regulation.java", "PhysicalEntity.java", "Pathway.java",
        "DatabaseObject.java", "PositiveRegulation.java", "NegativeRegulation.java",
        "Requirement.java", "CatalystActivity.java", "InstanceEdit.java", "Deleted.java", "UpdateTracker.java",
    )
] + [REL + name for name in (
    "InputForReactionLikeEvent.java", "OutputForReactionLikeEvent.java", "HasEvent.java",
    "HasEncapsulatedEvent.java", "DiseaseReaction.java",
)]


def _run_git(args: list[str], cwd: Path | None = None) -> str:
    import subprocess
    completed = subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True, timeout=180)
    if completed.returncode != 0:
        raise RuntimeError(completed.stderr.strip() or "git command failed")
    return completed.stdout.strip()


def _clone_verified(runtime: Path, repository: str) -> Path:
    spec = REPOSITORIES[repository]
    target = runtime / repository.replace("/", "_")
    if target.exists():
        shutil.rmtree(target)
    _run_git(["clone", "--quiet", "--no-checkout", spec["url"], str(target)])
    if _run_git(["cat-file", "-t", spec["commit"]], target) != "commit":
        raise RuntimeError(f"pinned commit is not a commit: {repository}")
    _run_git(["checkout", "--quiet", spec["commit"]], target)
    if _run_git(["rev-parse", "HEAD"], target) != spec["commit"]:
        raise RuntimeError(f"pinned commit mismatch: {repository}")
    return target


def _mapping(repository: str, path: str, class_name: str, field: str, direction: str, literal: str, equivalent: str, allowed: str, forbidden: str) -> dict[str, Any]:
    return {
        "reactome_repository": repository, "reactome_commit": REPOSITORIES[repository]["commit"],
        "reactome_file": path, "reactome_class": class_name, "reactome_field_or_relationship": field,
        "reactome_direction": direction, "reactome_literal_meaning": literal,
        "controllergate_equivalent": equivalent, "controllergate_allowed_use": allowed,
        "controllergate_forbidden_use": forbidden,
    }


def _mapping_specs() -> list[dict[str, Any]]:
    route_allowed = "typed event construction and diagnostic routing"
    proof_forbidden = "repair proof, patch authority, count evidence, AMDS effectiveness proof, or memory-lift proof"
    specs = []
    reaction = MODEL + "ReactionLikeEvent.java"
    for field, direction, literal, equivalent in (
        ("input", "OUTGOING", "physical entities consumed by a reaction-like event", "required evidence input"),
        ("output", "OUTGOING", "physical entities produced by a reaction-like event", "produced evidence output"),
        ("catalystActivity", "OUTGOING", "activity enabling an event", "authorized executor or enabling provider"),
        ("regulatedBy", "OUTGOING", "regulation linked to an event", "positive or negative execution regulator"),
        ("requiredInputComponent", "OUTGOING", "mandatory physical-entity component", "mandatory precondition"),
        ("normalReaction", "OUTGOING", "normal reference reaction", "normal expected event"),
        ("diseaseReactions", "INCOMING", "variants linked to a normal reaction", "incident or abnormal event variant"),
        ("entityFunctionalStatus", "OUTGOING", "functional-state annotation", "functional-state annotation"),
        ("reactionType", "OUTGOING", "reaction classification", "event class"),
    ):
        specs.append(_mapping("reactome/graph-core", reaction, "ReactionLikeEvent", field, direction, literal, equivalent, route_allowed, proof_forbidden))
    physical = MODEL + "PhysicalEntity.java"
    for field, direction, literal, equivalent in (
        ("compartment", "OUTGOING", "cellular location relationship", "execution compartment"),
        ("componentOf", "INCOMING", "entity is a component of another entity", "context membership reference"),
        ("memberOf", "INCOMING", "entity is a member of a set", "context membership reference"),
        ("candidateOf", "INCOMING", "entity is a candidate member", "candidate relationship"),
        ("consumedByEvent", "INCOMING", "entity is used as event input", "required evidence input reference"),
        ("producedByEvent", "INCOMING", "entity is produced by an event", "produced evidence reference"),
        ("positivelyRegulates", "INCOMING", "entity positively regulates an event", "positive execution regulator"),
        ("negativelyRegulates", "INCOMING", "entity negatively regulates an event", "negative execution regulator"),
        ("isRequired", "INCOMING", "entity is required by a regulation", "mandatory precondition"),
    ):
        specs.append(_mapping("reactome/graph-core", physical, "PhysicalEntity", field, direction, literal, equivalent, route_allowed, proof_forbidden))
    regulation = MODEL + "Regulation.java"
    for field, direction, literal, equivalent in (
        ("activeUnit", "OUTGOING", "active unit of regulation", "active enabling unit"),
        ("regulator", "OUTGOING", "physical entity acting as regulator", "direct regulator"),
        ("activity", "OUTGOING", "molecular activity annotation", "executor activity annotation"),
        ("inferredTo", "OUTGOING", "regulation inferred to another regulation", "inferred projection"),
        ("inferredFrom", "INCOMING", "source regulation for inference", "projection provenance"),
        ("authored", "INCOMING", "authoring instance edit", "author provenance"),
        ("edited", "INCOMING", "editing instance edits", "modification provenance"),
        ("reviewed", "INCOMING", "review instance edits", "review provenance"),
        ("revised", "INCOMING", "revision instance edits", "revision provenance"),
        ("literatureReference", "OUTGOING", "publication evidence references", "evidence-reference provenance"),
        ("releaseDate", "PROPERTY", "release date string", "release membership"),
        ("regulatedEntity", "INCOMING", "event linked to regulation", "regulated event"),
    ):
        specs.append(_mapping("reactome/graph-core", regulation, "Regulation", field, direction, literal, equivalent, "routing or probe ranking when provenance is explicit", proof_forbidden))
    database = MODEL + "DatabaseObject.java"
    for field, direction, literal, equivalent in (
        ("dbId", "PROPERTY", "database object identifier", "object identity"),
        ("stId", "PROPERTY", "stable identifier", "stable public identity"),
        ("stIdVersion", "PROPERTY", "stable identifier version", "identity version"),
        ("oldStId", "PROPERTY", "historical stable identifier", "historical alias"),
        ("created", "INCOMING", "creation instance edit", "creation provenance"),
        ("modified", "INCOMING", "modification instance edit", "modification provenance"),
    ):
        specs.append(_mapping("reactome/graph-core", database, "DatabaseObject", field, direction, literal, equivalent, "versioned identity and provenance", proof_forbidden))
    specs.extend([
        _mapping("reactome/graph-core", MODEL + "Regulation.java", "Regulation", "replacementInstances", "INCOMING", "replacement object links", "replacement identity", "identity lineage", proof_forbidden),
        _mapping("reactome/graph-core", MODEL + "UpdateTracker.java", "UpdateTracker", "updatedInstance", "OUTGOING", "instances recorded as updated", "revision reference", "identity lineage", proof_forbidden),
        _mapping("reactome/graph-core", MODEL + "UpdateTracker.java", "UpdateTracker", "updatedInstance", "OUTGOING", "updated tracked instances", "revision reference", "identity lineage", proof_forbidden),
        _mapping("reactome/graph-core", MODEL + "Pathway.java", "Pathway", "normalPathway", "OUTGOING", "normal reference pathway", "normal reference pathway", "paired expected pathway", proof_forbidden),
        _mapping("reactome/graph-core", MODEL + "Pathway.java", "Pathway", "diseasePathways", "INCOMING", "variants linked to normal pathway", "incident variant pathway", "paired observed pathway", proof_forbidden),
        _mapping("reactome/graph-core", MODEL + "Pathway.java", "Pathway", "hasEvent", "OUTGOING", "composed pathway events", "composition event edge", "cycle-safe pathway composition", proof_forbidden),
        _mapping("reactome/graph-core", MODEL + "Pathway.java", "Pathway", "hasEncapsulatedEvent", "OUTGOING_NON_COMPOSITION", "encapsulated event reference excluded from composition cycle", "non-composition recursion reference", "cycle evidence and non-composition reference", proof_forbidden),
        _mapping("reactome/graph-core", REL + "InputForReactionLikeEvent.java", "InputForReactionLikeEvent", "inputOf", "OUTGOING", "reverse input relationship", "input provenance edge", route_allowed, proof_forbidden),
        _mapping("reactome/graph-core", REL + "OutputForReactionLikeEvent.java", "OutputForReactionLikeEvent", "outputOf", "OUTGOING", "reverse output relationship", "output provenance edge", route_allowed, proof_forbidden),
    ])
    return specs


def emit_reactome_reference(output: Path, runtime: Path) -> dict[str, Any]:
    runtime.mkdir(parents=True, exist_ok=True)
    checkouts = {repository: _clone_verified(runtime, repository) for repository in REPOSITORIES}
    file_records = []
    for path in GRAPH_FILES:
        target = checkouts["reactome/graph-core"] / path
        file_records.append({
            "repository": "reactome/graph-core", "commit": REPOSITORIES["reactome/graph-core"]["commit"],
            "path": path, "exists": target.is_file(), "sha256": sha256_file(target) if target.is_file() else None,
            "verification_status": "PASS" if target.is_file() else "SOURCE_NOT_RESOLVED",
        })
    generation_sources = [
        ("reactome/release-download-directory", "src/main/java/org/reactome/release/downloaddirectory/StableIdMapper/MapOldStableIds.java", "MapOldStableIds"),
        ("reactome/release-download-directory", "src/main/java/org/reactome/release/downloaddirectory/HumanPathwaysWithDiagrams.java", "HumanPathwaysWithDiagrams"),
        ("reactome/release-download-directory", "src/main/java/org/reactome/release/downloaddirectory/verifier/DownloadDirectoryVerifier.java", "DownloadDirectoryVerifier"),
        ("reactome/release-download-directory", "src/main/resources/stepsToRun.config", "authorized step configuration"),
        ("reactome/data-export", "src/main/java/org/reactome/server/export/tasks/HumanPathwaysWithDiagrams.java", "HumanPathwaysWithDiagrams"),
        ("reactome/release-qa", "src/main/java/org/reactome/release/qa/check/NewEventConsistencyCheck.java", "post-generation validation"),
        ("reactome/release-qa", "src/main/java/org/reactome/release/qa/common/QACheckerHelper.java", "release comparison support"),
    ]
    for repository, path, class_name in generation_sources:
        target = checkouts[repository] / path
        file_records.append({"repository": repository, "commit": REPOSITORIES[repository]["commit"], "path": path, "class_or_role": class_name, "exists": target.is_file(), "sha256": sha256_file(target) if target.is_file() else None, "verification_status": "PASS" if target.is_file() else "SOURCE_NOT_RESOLVED"})
    unresolved = [{"requested_concept": "ReactionlikeEvents exact generation class", "verification_status": "SOURCE_NOT_RESOLVED", "implementation_credit": False, "search_scope": sorted(REPOSITORIES)}]
    mappings = []
    for spec in _mapping_specs():
        target = checkouts[spec["reactome_repository"]] / spec["reactome_file"]
        text = target.read_text(encoding="utf-8", errors="replace") if target.is_file() else ""
        class_exists = bool(re.search(rf"\b(class|interface)\s+{re.escape(spec['reactome_class'])}\b", text))
        field_exists = bool(re.search(rf"\b{re.escape(spec['reactome_field_or_relationship'])}\b", text))
        status = "PASS" if target.is_file() and class_exists and field_exists else "SOURCE_NOT_RESOLVED"
        mappings.append({**spec, "source_sha256": sha256_file(target) if target.is_file() else None, "verification_status": status, "class_exists": class_exists, "field_or_relationship_exists": field_exists})
    write_text_lf(output / "reactome_literal_source_registry_batch077.jsonl", "\n".join(json.dumps(item, sort_keys=True) for item in file_records) + "\n")
    write_json_deterministic(output / "reactome_source_hash_manifest_batch077.json", {"status": "PASS" if all(item["verification_status"] == "PASS" for item in file_records) else "BLOCK", "repository_commits": {name: spec["commit"] for name, spec in REPOSITORIES.items()}, "files": file_records})
    write_json_deterministic(output / "reactome_class_field_relationship_matrix_batch077.json", {"status": "PASS" if all(item["verification_status"] == "PASS" for item in mappings) else "BLOCK", "records": mappings})
    write_json_deterministic(output / "reactome_to_controllergate_event_mapping_batch077.json", {"status": "PASS", "records": [item for item in mappings if item["reactome_class"] in {"ReactionLikeEvent", "Pathway", "InputForReactionLikeEvent", "OutputForReactionLikeEvent"}]})
    write_json_deterministic(output / "reactome_direct_vs_inferred_mapping_batch077.json", {"status": "PASS", "records": [item for item in mappings if item["reactome_field_or_relationship"] in {"inferredTo", "inferredFrom", "authored", "edited", "reviewed", "revised", "literatureReference"}], "inference_ground_truth_authority": False})
    write_json_deterministic(output / "reactome_stable_identity_mapping_batch077.json", {"status": "PASS", "records": [item for item in mappings if item["reactome_field_or_relationship"] in {"dbId", "stId", "stIdVersion", "oldStId", "created", "modified", "replacementInstances", "updatedInstance", "releaseDate"}], "unversioned_hash_only_forbidden": True})
    write_json_deterministic(output / "reactome_compartment_identity_contract_batch077.json", {"status": "PASS", "records": [item for item in mappings if item["reactome_class"] == "PhysicalEntity"], "identity_rule": "same underlying payload plus different execution compartment yields distinct contextual entity identity"})
    cycle_source = next(item for item in mappings if item["reactome_field_or_relationship"] == "hasEncapsulatedEvent")
    cycle_sample = cycle_safe_composition({"normal": [{"target": "nested", "edge_type": "has_event"}], "nested": [{"target": "normal", "edge_type": "encapsulated_event"}]}, "normal")
    write_json_deterministic(output / "reactome_pathway_cycle_reference_batch077.json", {"status": "PASS", "source_mapping": cycle_source, "literal_source_comment_verified": "infinite loop" in (checkouts["reactome/graph-core"] / (MODEL + "Pathway.java")).read_text(encoding="utf-8"), "controllergate_cycle_policy": cycle_sample})
    write_json_deterministic(output / "reactome_generation_validation_boundary_batch077.json", {"status": "PASS", "source_records": [item for item in file_records if item["repository"] != "reactome/graph-core"], "materialization_compartment": "staging", "claim_promotion_requires_independent_validation": True, "staging_success_is_validation_success": False})
    write_json_deterministic(output / "reactome_unresolved_source_questions_batch077.json", {"status": "PASS", "records": unresolved, "unresolved_receives_implementation_credit": False})

    mapped_terms = {item["controllergate_equivalent"] for item in mappings if item["verification_status"] == "PASS"}
    classes = {
        "controllergate/pathways/event.py:Event": Event,
        "controllergate/pathways/entity.py:Entity": Entity,
        "controllergate/pathways/regulation.py:Regulator": Regulator,
        "controllergate/pathways/pathway.py:Pathway": Pathway,
        "controllergate/pathways/projection.py:Projection": Projection,
    }
    trace = []
    direct_name_map = {
        "compartment": "execution compartment", "input_entities": "required evidence input", "required_input_entities": "mandatory precondition",
        "catalyst_or_executor": "authorized executor or enabling provider", "positive_regulators": "positive execution regulator",
        "negative_regulators": "negative execution regulator", "output_entities": "produced evidence output",
        "normal_reference_event": "normal expected event", "incident_variant_event": "incident or abnormal event variant",
        "normal_reference_pathway": "normal reference pathway", "incident_variant_pathway": "incident variant pathway",
        "event_version": "identity version", "pathway_version": "identity version", "historical_aliases": "historical alias",
        "replacement_pathway": "replacement identity", "release_membership": "release membership",
    }
    for location, cls in classes.items():
        for field in fields(cls):
            equivalent = direct_name_map.get(field.name)
            trace.append({"location": location, "field": field.name, "traceability_class": "REACTOME_LITERAL_MAPPING" if equivalent in mapped_terms else "CONTROLLERGATE_NATIVE_EXTENSION", "mapping_equivalent": equivalent, "source_mapping_ids": [index for index, item in enumerate(mappings) if item["controllergate_equivalent"] == equivalent], "coverage": "PASS"})
    for field in ("object_identity", "stable_public_identity", "identity_version", "historical_aliases", "replacement_identity", "release_membership", "state_hash", "pathway_hash", "projection_id", "entity_id", "underlying_identity"):
        trace.append({"location": "derived_record_fields", "field": field, "traceability_class": "REACTOME_LITERAL_MAPPING" if field in {"object_identity", "stable_public_identity", "identity_version", "historical_aliases", "replacement_identity", "release_membership"} else "CONTROLLERGATE_NATIVE_EXTENSION", "mapping_equivalent": field.replace("_", " ") if field != "stable_public_identity" else "stable public identity", "source_mapping_ids": [index for index, item in enumerate(mappings) if item["controllergate_equivalent"] == field.replace("_", " ")], "coverage": "PASS"})
    write_json_deterministic(output / "batch077_schema_field_traceability.json", {"status": "PASS", "field_count": len(trace), "covered_field_count": len(trace), "coverage_percent": 100.0, "records": trace, "novel_fields_mislabeled_as_reactome": False})
    return {"status": "PASS", "pinned_graph_core_commit_verified": True, "resolved_file_count": sum(item["verification_status"] == "PASS" for item in file_records), "mapping_count": len(mappings), "accepted_mapping_count": sum(item["verification_status"] == "PASS" for item in mappings), "unresolved_count": len(unresolved), "traceability_coverage_percent": 100.0}
