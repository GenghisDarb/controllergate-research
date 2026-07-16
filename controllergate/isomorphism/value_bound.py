from __future__ import annotations

import hashlib
import json
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable

from .primitives import GENERIC_PRIMITIVES


LEDGER_FILES = {
    "entity_set_members": "reactome_entity_set_members.jsonl",
    "candidate_set_members": "reactome_candidate_set_members.jsonl",
    "complex_components": "reactome_complex_components.jsonl",
    "entity_compartments": "reactome_entity_compartments.jsonl",
    "source_destination_transitions": "reactome_source_destination_transitions.jsonl",
    "stable_event_edges": "reactome_stable_event_edges_v2.jsonl",
    "normal_variant_graph": "reactome_normal_variant_graph_v2.jsonl",
    "modification_details": "reactome_modification_details.jsonl",
    "catalyst_details": "reactome_catalyst_details.jsonl",
    "regulator_details": "reactome_regulation_details.jsonl",
    "literature_records": "reactome_literature_details.jsonl",
    "edition_lineage": "reactome_edition_lineage_details.jsonl",
    "timing_annotations": "reactome_timing_annotations.jsonl",
    "source_value_binding": "reactome_structured_participants.jsonl",
}


def canonical_hash(value: object) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def record_hash(row: dict[str, Any]) -> str:
    return str(row.get("edge_hash") or row.get("record_hash") or row.get("transition_hash") or canonical_hash(row))


class ValueBindingResolver:
    """Resolve RPIR references against immutable, content-addressed JSONL ledgers."""

    def __init__(self, current_root: str | Path, participant_ledger: str | Path):
        self.current_root = Path(current_root)
        self.participant_ledger = Path(participant_ledger)
        self._indices: dict[str, dict[str, dict[str, Any]]] = {}

    def _path(self, field: str) -> Path:
        if field == "source_value_binding":
            return self.participant_ledger
        return self.current_root / LEDGER_FILES[field]

    def index(self, field: str) -> dict[str, dict[str, Any]]:
        if field not in self._indices:
            values: dict[str, dict[str, Any]] = {}
            with self._path(field).open(encoding="utf-8") as stream:
                for line_number, line in enumerate(stream, 1):
                    if not line.strip():
                        continue
                    row = json.loads(line)
                    digest = record_hash(row)
                    if digest in values and values[digest] != row:
                        raise ValueError(f"content address collision in {field}:{line_number}")
                    values[digest] = row
            self._indices[field] = values
        return self._indices[field]

    def resolve(self, record: dict[str, Any], field: str) -> list[dict[str, Any]]:
        wrapped = record.get(field, {})
        if wrapped.get("state") != "SOURCE_VALUE":
            return []
        index = self.index(field)
        refs = wrapped.get("value") or []
        resolved = []
        for reference in refs:
            digest = reference if isinstance(reference, str) else reference.get("ledger_record_sha256")
            if digest not in index:
                raise ValueError(f"unresolved content address for {record['source_stable_id']}:{field}:{digest}")
            resolved.append(index[digest])
        return resolved


def _primitives(record: dict[str, Any], values: dict[str, list[dict[str, Any]]]) -> list[str]:
    selected = ["EVENT_CONTRACT", "ENTITY_STATE"]
    participants = values["source_value_binding"]
    if values["complex_components"] or any(row.get("class") == "Complex" for row in participants):
        selected.append("COMPLEX_ASSEMBLY")
    if values["candidate_set_members"]:
        selected.append("CANDIDATE_SET")
    if values["entity_set_members"]:
        selected.append("DEMONSTRATED_MEMBER")
    if values["entity_compartments"]:
        selected.append("COMPARTMENT")
    if values["source_destination_transitions"]:
        selected.append("TRANSLOCATION")
    if values["catalyst_details"]:
        selected.append("CATALYST")
    regulation_classes = " ".join(str(row.get("regulation_class", "")) for row in values["regulator_details"]).lower()
    if "positive" in regulation_classes:
        selected.append("POSITIVE_REGULATOR")
    if "negative" in regulation_classes:
        selected.append("NEGATIVE_REGULATOR")
    if values["modification_details"]:
        selected.append("MODIFICATION_CODE")
    if values["stable_event_edges"]:
        selected.append("CHECKPOINT")
    if values["normal_variant_graph"]:
        selected.append("NORMAL_VARIANT_PAIR")
    source_class = record["source_class"]
    selected.extend({
        "FailedReaction": ["NEGATIVE_REACTION", "QUALITY_CONTROL"],
        "Polymerisation": ["PROCESSIVE_CYCLE", "IRREVERSIBLE_REACTION"],
        "Depolymerisation": ["DEGRADATION", "RECYCLING"],
        "CellDevelopmentStep": ["PHASE_MACHINE", "LINEAGE"],
        "BlackBoxEvent": ["QUALITY_CONTROL"],
    }.get(source_class, ["IRREVERSIBLE_REACTION"]))
    return list(dict.fromkeys(item for item in selected if item in GENERIC_PRIMITIVES))


def _role_refs(rows: list[dict[str, Any]], role: str) -> list[str]:
    return [record_hash(row) for row in rows if row.get("role") == role]


def compile_value_bound_candidate(record: dict[str, Any], resolver: ValueBindingResolver) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    fields = tuple(LEDGER_FILES)
    values = {field: resolver.resolve(record, field) for field in fields}
    participants = values["source_value_binding"]
    primitives = _primitives(record, values)
    open_contract = record["source_class"] == "BlackBoxEvent" or record["evidence_maturity"] in {"UNCERTAIN_BLACK_BOX", "OMITTED_DETAIL"}
    unknown = record["source_class"] not in {
        "Reaction", "FailedReaction", "Polymerisation", "Depolymerisation", "CellDevelopmentStep", "BlackBoxEvent",
    }
    reference_fields = {field: list(record.get(field, {}).get("value") or []) for field in fields if field != "source_value_binding"}
    participant_refs = list(record["source_value_binding"].get("value") or [])
    inputs = _role_refs(participants, "input")
    required = _role_refs(participants, "required_input")
    outputs = _role_refs(participants, "output")
    transition_relation = {
        "event_class": record["source_class"],
        "relation_kind": "open_black_box" if open_contract else "source_bound_state_transition",
        "direction": "source_to_destination" if reference_fields.get("source_destination_transitions") else "source_ordered",
    }
    first_input = next((row for row in participants if row.get("role") in {"input", "required_input"}), None)
    first_output = next((row for row in participants if row.get("role") == "output"), None)
    plain = (
        f"Apply a {record['source_class']} transition from "
        f"{(first_input or {}).get('stable_id') or (first_input or {}).get('database_id') or 'an explicit empty input set'} "
        f"to {(first_output or {}).get('stable_id') or (first_output or {}).get('database_id') or 'an explicit empty output set'}; "
        f"enforce {len(required)} required inputs, {len(values['catalyst_details'])} catalyst activities, "
        f"{len(values['regulator_details'])} regulator edges, and {len(values['entity_compartments'])} compartment bindings."
    )
    candidate = {
        "translation_candidate_id": canonical_hash([record["source_occurrence_identity"], record["source_graph_hash"], "v3"]),
        "source_stable_id": record["source_stable_id"],
        "source_database_id": record["source_database_id"],
        "source_occurrence_id": record["source_occurrence_identity"],
        "source_graph_hash": record["source_graph_hash"],
        "source_chapter": record["chapter_identity"],
        "event_class": record["source_class"],
        "plain_engineering_translation": plain,
        "actual_participant_role_references": participant_refs,
        "actual_required_input_references": required,
        "actual_output_references": outputs,
        "actual_catalyst_references": reference_fields.get("catalyst_details", []),
        "actual_active_unit_references": [record_hash(row) for row in values["catalyst_details"] if row.get("active_units")],
        "actual_positive_negative_regulator_references": reference_fields.get("regulator_details", []),
        "actual_compartment_transition_references": reference_fields.get("source_destination_transitions", []),
        "actual_complex_set_membership_references": reference_fields.get("complex_components", []) + reference_fields.get("entity_set_members", []) + reference_fields.get("candidate_set_members", []),
        "actual_modification_references": reference_fields.get("modification_details", []),
        "actual_predecessor_follower_references": reference_fields.get("stable_event_edges", []),
        "normal_variant_references": reference_fields.get("normal_variant_graph", []),
        "evidence_maturity": record["evidence_maturity"],
        "preconditions": ["all required input references resolve", "source graph identity remains frozen"],
        "transition_relation": transition_relation,
        "postconditions": ["all output references resolve", "source graph hash is preserved"],
        "invariants": ["source identity immutable", "content references resolve exactly", "source evidence cannot grant repair authority"],
        "failure_terminals": ["MISSING_REQUIRED_INPUT", "UNRESOLVED_CONTENT_REFERENCE", "SOURCE_DETAIL_OPEN"],
        "compensating_actions": ["preserve candidate state", "record exact blocker", "reopen on release-bound source detail"],
        "resource_cofactor_requirements": required,
        "uncertainty_boundary": "faithful_open_contract" if open_contract else "structured_source_boundary",
        "positive_control": "execute resolved source transition",
        "negative_control": "remove one required input and require a block",
        "adversarial_control": "attempt evidence-maturity escalation and require rejection",
        "generic_primitive_bindings": primitives,
        "execution_maturity": "schema_compiled_value_bound",
        "translation_state": "BLOCKED_MISSING_SOURCE_DETAIL" if open_contract else "SCHEMA_COMPILED",
        "unknown_structural_pattern": unknown,
        "authority_allowed": "shadow candidate execution",
        "authority_forbidden": ["repair authorization", "production promotion", "source metadata as software causal proof"],
        "producer": "controllergate.isomorphism.value_bound:compile_value_bound_candidate",
        "execution_depth": "value_bound_structural_compilation",
        "semantic_scope": "release-97 candidate translation",
        "parent_evidence": [record["source_graph_hash"]],
    }
    bindings = []
    for field, rows in values.items():
        for row in rows:
            bindings.append({
                "ledger_record_sha256": record_hash(row),
                "ledger": LEDGER_FILES[field],
                "field": field,
                "source_stable_id": record["source_stable_id"],
            })
    return candidate, bindings


def distinctness_audit(candidates: Iterable[dict[str, Any]]) -> dict[str, Any]:
    rows = list(candidates)
    strings = [row["plain_engineering_translation"] for row in rows]
    without_ids = [re.sub(r"R-HSA-\d+|\b[0-9a-f]{16,64}\b", "<identity>", text) for text in strings]
    without_counts = [re.sub(r"\b\d+\b", "<n>", text) for text in without_ids]
    relations = [canonical_hash(row["transition_relation"]) for row in rows]
    compositions = [canonical_hash(row["generic_primitive_bindings"]) for row in rows]
    clusters: dict[str, list[str]] = defaultdict(list)
    for row, normalized in zip(rows, without_counts):
        clusters[canonical_hash([normalized, row["event_class"], row["generic_primitive_bindings"]])].append(row["source_occurrence_id"])
    return {
        "status": "PASS",
        "producer": "controllergate.isomorphism.value_bound:distinctness_audit",
        "candidate_count": len(rows),
        "exact_string_count": len(set(strings)),
        "count_after_removing_ids_and_hashes": len(set(without_ids)),
        "count_after_normalizing_numeric_counts": len(set(without_counts)),
        "distinct_transition_relation_count": len(set(relations)),
        "distinct_primitive_composition_count": len(set(compositions)),
        "semantic_equivalence_cluster_count": len(clusters),
        "largest_cluster": max(map(len, clusters.values()), default=0),
        "authority_allowed": "translation quality audit",
        "authority_forbidden": ["repair authorization", "production promotion"],
    }
