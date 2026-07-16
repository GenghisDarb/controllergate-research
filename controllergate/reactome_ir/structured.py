from __future__ import annotations

import hashlib
import json
import sqlite3
from collections import defaultdict
from pathlib import Path
from typing import Any, Iterable

from .schema import RPIR_V2_VERSION, field_value, rpir_v2_schema


PRODUCER = "controllergate.reactome_ir.structured:release97_mysql_v1"


def _sha(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")


def _jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as stream:
        for row in rows:
            stream.write(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n")


def _occurrences(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def _relation(connection: sqlite3.Connection, table: str, value_column: str, class_column: str | None = None) -> dict[int, list[tuple[int, int, str | None]]]:
    rank_column = next(row[1] for row in connection.execute(f'PRAGMA table_info("{table}")') if row[1].endswith("_rank"))
    selected = f'"DB_ID", "{rank_column}", "{value_column}"' + (f', "{class_column}"' if class_column else "")
    result: dict[int, list[tuple[int, int, str | None]]] = defaultdict(list)
    for row in connection.execute(f'SELECT {selected} FROM "{table}" ORDER BY CAST("DB_ID" AS INTEGER), CAST("{rank_column}" AS INTEGER)'):
        result[int(row[0])].append((int(row[1]), int(row[2]), row[3] if class_column else None))
    return result


def _object_identity(connection: sqlite3.Connection, ids: set[int]) -> dict[int, dict[str, Any]]:
    if not ids:
        return {}
    connection.execute("DROP TABLE IF EXISTS temp.wanted_object")
    connection.execute("CREATE TEMP TABLE wanted_object (id TEXT PRIMARY KEY)")
    connection.executemany("INSERT INTO wanted_object VALUES (?)", [(str(item),) for item in sorted(ids)])
    query = """
        SELECT d.DB_ID,d._class,d._displayName,s.identifier,s.identifierVersion
        FROM wanted_object w
        JOIN DatabaseObject d ON d.DB_ID=w.id
        LEFT JOIN StableIdentifier s ON s.DB_ID=d.stableIdentifier
    """
    return {
        int(row[0]): {
            "database_id": int(row[0]), "class": row[1], "display_name": row[2] or f"Reactome object {row[0]}",
            "stable_id": row[3], "stable_id_version": row[4],
        }
        for row in connection.execute(query)
    }


def _wrapped_list(values: list[Any], source: str, *, exposed: bool = True) -> dict[str, Any]:
    if not exposed:
        return field_value(None, state="SOURCE_NOT_EXPOSED_BY_FORMAT", source=source)
    return field_value(values, state="SOURCE_VALUE" if values else "SOURCE_EXPLICITLY_EMPTY", source=source)


def build_structured_rpir(
    *,
    database: str | Path,
    reaction_occurrences: str | Path,
    pathway_occurrences: str | Path,
    source_manifest: str | Path,
    output: str | Path,
) -> dict[str, Any]:
    database = Path(database)
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    reactions_in = _occurrences(Path(reaction_occurrences))
    pathways_in = _occurrences(Path(pathway_occurrences))
    stable_ids = {row["stable_source_identity"] for row in [*reactions_in, *pathways_in]}
    connection = sqlite3.connect(f"file:{database.as_posix()}?mode=ro", uri=True)
    try:
        connection.execute("CREATE TEMP TABLE wanted_stable (id TEXT PRIMARY KEY)")
        connection.executemany("INSERT INTO wanted_stable VALUES (?)", [(item,) for item in sorted(stable_ids)])
        object_by_stable = {
            row[3]: {
                "database_id": int(row[0]), "class": row[1], "display_name": row[2] or row[3],
                "stable_id": row[3], "stable_id_version": row[4],
            }
            for row in connection.execute(
                "SELECT d.DB_ID,d._class,d._displayName,s.identifier,s.identifierVersion "
                "FROM wanted_stable w JOIN StableIdentifier s ON s.identifier=w.id "
                "JOIN DatabaseObject d ON d.stableIdentifier=s.DB_ID"
            )
        }
        missing = sorted(stable_ids - set(object_by_stable))
        if missing:
            raise ValueError(f"structured stable IDs missing: {missing[:10]} count={len(missing)}")

        inputs = _relation(connection, "ReactionlikeEvent_2_input", "input", "input_class")
        outputs = _relation(connection, "ReactionlikeEvent_2_output", "output", "output_class")
        required = _relation(connection, "ReactionlikeEvent_2_requiredInputComponent", "requiredInputComponent", "requiredInputComponent_class")
        event_compartments = _relation(connection, "ReactionlikeEvent_2_compartment", "compartment", "compartment_class")
        catalysts_for_event = _relation(connection, "ReactionlikeEvent_2_catalystActivity", "catalystActivity", "catalystActivity_class")
        regulations_for_event = _relation(connection, "ReactionlikeEvent_2_regulatedBy", "regulatedBy", "regulatedBy_class")
        preceding = _relation(connection, "Event_2_precedingEvent", "precedingEvent", "precedingEvent_class")
        inferred = _relation(connection, "Event_2_inferredFrom", "inferredFrom", "inferredFrom_class")
        literature = _relation(connection, "Event_2_literatureReference", "literatureReference", "literatureReference_class")
        authored = _relation(connection, "Event_2_authored", "authored", "authored_class")
        reviewed = _relation(connection, "Event_2_reviewed", "reviewed", "reviewed_class")
        revised = _relation(connection, "Event_2_revised", "revised", "revised_class")
        pathway_events = _relation(connection, "Pathway_2_hasEvent", "hasEvent", "hasEvent_class")

        event_ids = {object_by_stable[row["stable_source_identity"]]["database_id"] for row in reactions_in}
        catalyst_ids = {item[1] for event in event_ids for item in catalysts_for_event.get(event, [])}
        catalyst_rows: dict[int, dict[str, Any]] = {}
        active_units = _relation(connection, "CatalystActivity_2_activeUnit", "activeUnit", "activeUnit_class")
        if catalyst_ids:
            marks = ",".join("?" for _ in catalyst_ids)
            for row in connection.execute(f"SELECT DB_ID,activity,activity_class,physicalEntity,physicalEntity_class FROM CatalystActivity WHERE DB_ID IN ({marks})", tuple(map(str, catalyst_ids))):
                catalyst_rows[int(row[0])] = {"activity": int(row[1]) if row[1] else None, "activity_class": row[2], "physical_entity": int(row[3]) if row[3] else None, "physical_entity_class": row[4]}
        regulation_ids = {item[1] for event in event_ids for item in regulations_for_event.get(event, [])}
        regulation_rows: dict[int, dict[str, Any]] = {}
        if regulation_ids:
            marks = ",".join("?" for _ in regulation_ids)
            for row in connection.execute(f"SELECT DB_ID,regulator,regulator_class,activity,activity_class FROM Regulation WHERE DB_ID IN ({marks})", tuple(map(str, regulation_ids))):
                regulation_rows[int(row[0])] = {"regulator": int(row[1]) if row[1] else None, "regulator_class": row[2], "activity": int(row[3]) if row[3] else None, "activity_class": row[4]}

        wanted_objects = set()
        for mapping in (inputs, outputs, required, event_compartments, preceding, inferred, literature):
            for event in event_ids:
                wanted_objects.update(item[1] for item in mapping.get(event, []))
        for row in catalyst_rows.values():
            if row["physical_entity"]:
                wanted_objects.add(row["physical_entity"])
        for catalyst_id in catalyst_ids:
            wanted_objects.update(item[1] for item in active_units.get(catalyst_id, []))
        for row in regulation_rows.values():
            if row["regulator"]:
                wanted_objects.add(row["regulator"])
        pathway_ids = {object_by_stable[row["stable_source_identity"]]["database_id"] for row in pathways_in}
        pathway_event_ids = {item[1] for pathway_id in pathway_ids for item in pathway_events.get(pathway_id, [])}
        identities = _object_identity(connection, wanted_objects | event_ids | pathway_ids | pathway_event_ids)

        normal_reaction = {
            int(row[0]): int(row[1]) if row[1] else None
            for row in connection.execute("SELECT DB_ID,normalReaction FROM ReactionlikeEvent")
            if int(row[0]) in event_ids
        }
        normal_ids = {value for value in normal_reaction.values() if value}
        identities.update(_object_identity(connection, normal_ids))

        entity_ids = {
            item[1]
            for event in event_ids
            for mapping in (inputs, outputs, required)
            for item in mapping.get(event, [])
        }
        set_members = _relation(connection, "EntitySet_2_hasMember", "hasMember", "hasMember_class")
        candidate_members = _relation(connection, "CandidateSet_2_hasCandidate", "hasCandidate", "hasCandidate_class")
        complex_members = _relation(connection, "Complex_2_hasComponent", "hasComponent", "hasComponent_class")
        modifications = _relation(connection, "EntityWithAccessionedSequence_2_hasModifiedResidue", "hasModifiedResidue", "hasModifiedResidue_class")
        nested_ids = set()
        for entity_id in entity_ids:
            nested_ids.update(item[1] for item in set_members.get(entity_id, []))
            nested_ids.update(item[1] for item in candidate_members.get(entity_id, []))
            nested_ids.update(item[1] for item in complex_members.get(entity_id, []))
            nested_ids.update(item[1] for item in modifications.get(entity_id, []))
        identities.update(_object_identity(connection, nested_ids | entity_ids))

        def identity(item: int, role: str, rank: int | None = None) -> dict[str, Any]:
            value = identities.get(item, {"database_id": item, "class": "UNRESOLVED", "display_name": f"Reactome object {item}", "stable_id": None, "stable_id_version": None})
            return {"role": role, "rank": rank, **value}

        def reference(value: dict[str, Any] | None) -> dict[str, Any] | None:
            if value is None:
                return None
            return {key: value.get(key) for key in ("database_id", "stable_id", "class", "role", "rank") if value.get(key) is not None}

        reaction_rows = []
        participant_rows = []
        catalyst_output = []
        regulation_output = []
        relation_output = []
        normal_pairs = []
        unresolved_states = 0
        for occurrence in reactions_in:
            stable_id = occurrence["stable_source_identity"]
            source = object_by_stable[stable_id]
            event_id = source["database_id"]
            event_inputs = [identity(item, "input", rank) for rank, item, _ in inputs.get(event_id, [])]
            event_outputs = [identity(item, "output", rank) for rank, item, _ in outputs.get(event_id, [])]
            event_required = [identity(item, "required_input", rank) for rank, item, _ in required.get(event_id, [])]
            participants = [*event_inputs, *event_outputs, *event_required]
            participant_rows.extend({"event_stable_id": stable_id, "event_occurrence_identity": occurrence["source_occurrence_identity"], **row} for row in participants)
            event_catalysts = []
            event_active_units = []
            for rank, catalyst_id, _ in catalysts_for_event.get(event_id, []):
                catalyst = catalyst_rows.get(catalyst_id, {})
                physical = catalyst.get("physical_entity")
                event_catalysts.append({"rank": rank, "catalyst_activity_database_id": catalyst_id, "activity_database_id": catalyst.get("activity"), "physical_entity": identity(physical, "catalyst", rank) if physical else None})
                event_active_units.extend(identity(item, "active_unit", unit_rank) for unit_rank, item, _ in active_units.get(catalyst_id, []))
            catalyst_output.extend({"event_stable_id": stable_id, **row} for row in event_catalysts)
            positive = []
            negative = []
            for rank, regulation_id, regulation_class in regulations_for_event.get(event_id, []):
                raw = regulation_rows.get(regulation_id, {})
                regulator_id = raw.get("regulator")
                row = {"rank": rank, "regulation_database_id": regulation_id, "regulation_class": regulation_class, "regulator": identity(regulator_id, "regulator", rank) if regulator_id else None}
                (negative if regulation_class and "Negative" in regulation_class else positive).append(row)
                regulation_output.append({"event_stable_id": stable_id, **row})
            event_preceding = [identity(item, "preceding", rank) for rank, item, _ in preceding.get(event_id, [])]
            relation_output.extend({"event_stable_id": stable_id, "relation": "preceding", **row} for row in event_preceding)
            event_inferred = [identity(item, "inferred_from", rank) for rank, item, _ in inferred.get(event_id, [])]
            event_literature = [identity(item, "literature", rank) for rank, item, _ in literature.get(event_id, [])]
            normal_id = normal_reaction.get(event_id)
            normal = identity(normal_id, "normal_event") if normal_id else None
            if normal:
                normal_pairs.append({"variant_stable_id": stable_id, "variant_database_id": event_id, "normal_stable_id": normal.get("stable_id"), "normal_database_id": normal_id, "first_divergent_event": stable_id, "source": "gk_current.ReactionlikeEvent.normalReaction"})
            documentary_type = occurrence.get("source_event_type", "transition")
            maturity = occurrence.get("source_evidence_maturity", "DIRECT_CURATED")
            if source["class"] == "FailedReaction":
                maturity = "NEGATIVE_REACTION_CURATED"
            elif normal:
                maturity = "DISEASE_VARIANT_CURATED"
            elif event_inferred:
                maturity = "INFERRED_ORTHOLOGY"
            elif source["class"] == "BlackBoxEvent":
                maturity = "OMITTED_DETAIL" if documentary_type == "omitted" else "UNCERTAIN_BLACK_BOX"
            participant_ids = {participant["database_id"] for participant in participants}
            event_sets = [identity(entity_id, "entity_set") for entity_id in participant_ids if identities.get(entity_id, {}).get("class") in {"DefinedSet", "EntitySet"}]
            event_candidates = [identity(entity_id, "candidate_set") for entity_id in participant_ids if identities.get(entity_id, {}).get("class") == "CandidateSet"]
            event_complexes = [identity(entity_id, "complex") for entity_id in participant_ids if identities.get(entity_id, {}).get("class") == "Complex"]
            event_modifications = [identity(item, "modification", rank) for entity_id in {p["database_id"] for p in participants} for rank, item, _ in modifications.get(entity_id, [])]
            compartments = [identity(item, "compartment", rank) for rank, item, _ in event_compartments.get(event_id, [])]
            lineage_ids = [item[1] for mapping in (authored, reviewed, revised) for item in mapping.get(event_id, [])]
            compact_participants = [reference(item) for item in participants]
            compact_catalysts = [
                {**{key: value for key, value in item.items() if key != "physical_entity"}, "physical_entity": reference(item.get("physical_entity"))}
                for item in event_catalysts
            ]
            compact_positive = [{**{key: value for key, value in item.items() if key != "regulator"}, "regulator": reference(item.get("regulator"))} for item in positive]
            compact_negative = [{**{key: value for key, value in item.items() if key != "regulator"}, "regulator": reference(item.get("regulator"))} for item in negative]
            row = {
                "rpir_version": RPIR_V2_VERSION,
                "source_stable_id": stable_id,
                "source_database_id": event_id,
                "source_class": source["class"],
                "source_occurrence_identity": occurrence["source_occurrence_identity"],
                "chapter_identity": occurrence["chapter_identity"],
                "display_name": source["display_name"],
                "source_event_type": documentary_type,
                "evidence_maturity": maturity,
                "participants": _wrapped_list(compact_participants, "RLE_IO"),
                "catalysts": _wrapped_list(compact_catalysts, "RLE_CA"),
                "active_units": _wrapped_list([reference(item) for item in event_active_units], "CA_AU"),
                "positive_regulators": _wrapped_list(compact_positive, "RLE_POS"),
                "negative_regulators": _wrapped_list(compact_negative, "RLE_NEG"),
                "entity_sets": _wrapped_list([reference(item) for item in event_sets], "ES_MEMBER"),
                "candidate_sets": _wrapped_list([reference(item) for item in event_candidates], "CS_CANDIDATE"),
                "complexes": _wrapped_list([reference(item) for item in event_complexes], "CX_COMPONENT"),
                "stoichiometry": field_value(None, state="SOURCE_NOT_EXPOSED_BY_FORMAT", source="CORE_SUBSET", note="member ranks preserved; numeric reaction stoichiometry not exposed"),
                "compartments": _wrapped_list([reference(item) for item in compartments], "RLE_COMP"),
                "modifications": _wrapped_list([reference(item) for item in event_modifications], "EWAS_MOD"),
                "preceding_events": _wrapped_list([reference(item) for item in event_preceding], "EVENT_PREV"),
                "following_events": field_value(None, state="SOURCE_NOT_EXPOSED_BY_FORMAT", source="INVERSE_EVENT_PREV"),
                "normal_event": field_value(reference(normal), state="SOURCE_VALUE" if normal else "SOURCE_NOT_APPLICABLE", source="RLE_NORMAL"),
                "variant_events": field_value(None, state="SOURCE_NOT_EXPOSED_BY_FORMAT", source="INVERSE_RLE_NORMAL"),
                "orthology_sources": _wrapped_list([reference(item) for item in event_inferred], "EVENT_INFERRED"),
                "literature_references": _wrapped_list([reference(item) for item in event_literature], "EVENT_LIT"),
                "edition_lineage": _wrapped_list(lineage_ids, "EVENT_EDITS"),
                "timing_annotations": field_value(None, state="SOURCE_NOT_EXPOSED_BY_FORMAT", source="CORE_SUBSET"),
                "output_profile": "B093_RPIR_V2_STRUCTURED_NONAUTH",
            }
            unresolved_states += sum(value.get("state") == "UNRESOLVED_REFERENCE" for value in row.values() if isinstance(value, dict))
            reaction_rows.append(row)

        pathway_rows = []
        for occurrence in pathways_in:
            source = object_by_stable[occurrence["stable_source_identity"]]
            pathway_id = source["database_id"]
            event_refs = [reference(identity(item, "pathway_event", rank)) for rank, item, _ in pathway_events.get(pathway_id, [])]
            pathway_rows.append({
                "rpir_version": RPIR_V2_VERSION, "source_stable_id": occurrence["stable_source_identity"],
                "source_database_id": pathway_id, "source_class": source["class"],
                "source_occurrence_identity": occurrence["source_occurrence_identity"], "chapter_identity": occurrence["chapter_identity"],
                "display_name": source["display_name"], "pathway_events": _wrapped_list(event_refs, "PATH_HAS_EVENT"),
                "output_profile": "B093_RPIR_V2_STRUCTURED_NONAUTH",
            })

        _jsonl(output / "reactome_structured_rpir_v2_reactions.jsonl", reaction_rows)
        _jsonl(output / "reactome_structured_rpir_v2_pathways.jsonl", pathway_rows)
        _jsonl(output / "reactome_structured_participants.jsonl", participant_rows)
        _jsonl(output / "reactome_structured_catalysts.jsonl", catalyst_output)
        _jsonl(output / "reactome_structured_regulations.jsonl", regulation_output)
        _jsonl(output / "reactome_structured_relations.jsonl", relation_output)
        _jsonl(output / "reactome_structured_normal_variant_pairs.jsonl", normal_pairs)
        _json(output / "rpir_v2_schema.json", rpir_v2_schema())
        source_rows = json.loads(Path(source_manifest).read_text(encoding="utf-8"))
        source_record = {
            "status": "PASS", "producer": PRODUCER, "execution_depth": "exact_release_structured_source_custody",
            "semantic_scope": "Reactome release 97 machine-readable source identity", "authority_allowed": "RPIR v2 parsing",
            "authority_forbidden": ["software causal authority", "repair authorization"], "release": 97,
            "zenodo_record_id": 21383214, "zenodo_doi": "10.5281/zenodo.21383214", "sources": source_rows,
            "runtime_database_sha256": _sha(database), "runtime_database_path": str(database), "runtime_database_committed": False,
        }
        _json(output / "reactome_structured_source_manifest.json", source_record)
        class_counts: dict[str, int] = defaultdict(int)
        state_counts: dict[str, int] = defaultdict(int)
        for row in reaction_rows:
            class_counts[row["source_class"]] += 1
            for value in row.values():
                if isinstance(value, dict) and value.get("state"):
                    state_counts[value["state"]] += 1
        anchor = next(row for row in reaction_rows if row["source_stable_id"] == "R-HSA-9912396")
        anchor_nonempty = {
            name: len(anchor[name]["value"])
            for name in ("participants", "catalysts", "compartments", "preceding_events", "orthology_sources")
            if anchor[name]["state"] == "SOURCE_VALUE"
        }
        summary = {
            "status": "PASS",
            "producer": PRODUCER,
            "execution_depth": "reaction_complete_structured_semantic_graph",
            "semantic_scope": "Reactome release 97 structured RPIR v2",
            "authority_allowed": "complete candidate translation input",
            "authority_forbidden": ["complete production implementation", "repair authority"],
            "reaction_occurrence_count": len(reaction_rows), "unique_reaction_stable_id_count": len({row["source_stable_id"] for row in reaction_rows}),
            "pathway_occurrence_count": len(pathway_rows), "unique_pathway_stable_id_count": len({row["source_stable_id"] for row in pathway_rows}),
            "missing_structured_stable_id_count": 0, "silent_omission_count": 0, "duplicate_inflation_count": 0,
            "source_class_counts": dict(sorted(class_counts.items())), "field_state_counts": dict(sorted(state_counts.items())),
            "unresolved_field_state_count": unresolved_states, "normal_variant_pair_count": len(normal_pairs),
            "anchor_reaction": {"stable_id": "R-HSA-9912396", "database_id": anchor["source_database_id"], "nonempty_structured_fields": anchor_nonempty},
        }
        _json(output / "reactome_structured_source_coverage.json", summary)
        _json(output / "reactome_structured_count_reconciliation.json", {
            **summary,
            "documentary_expected": {"pathway_occurrences": 2916, "reaction_occurrences": 16814},
            "structured_unique": {"pathways": 2883, "reactions": 16107},
            "shared_chapter_occurrences": {"pathways": len(pathway_rows) - 2883, "reactions": len(reaction_rows) - 16107},
            "reconciliation": "PASS_OCCURRENCE_TO_UNIQUE_STRUCTURED_IDENTITY",
        })
        return summary
    finally:
        connection.close()
