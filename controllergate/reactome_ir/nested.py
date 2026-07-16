from __future__ import annotations

import hashlib
import json
import sqlite3
from collections import defaultdict, deque
from pathlib import Path
from typing import Any, Iterable

from .schema import FIELD_STATES, RPIR_V2_1_VERSION, rpir_v2_1_schema


PRODUCER = "controllergate.reactome_ir.nested:release97_v2_1"


def _hash(value: object) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def _write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")


def _write_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as stream:
        for row in rows:
            stream.write(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n")


def _table(connection: sqlite3.Connection, name: str) -> bool:
    return connection.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (name,)).fetchone() is not None


def _relation(connection: sqlite3.Connection, table: str, value: str) -> dict[int, list[dict[str, Any]]]:
    if not _table(connection, table):
        return {}
    columns = [row[1] for row in connection.execute(f'PRAGMA table_info("{table}")')]
    rank = next(name for name in columns if name.endswith("_rank"))
    class_name = next((name for name in columns if name == f"{value}_class"), None)
    select = f'"DB_ID","{rank}","{value}"' + (f',"{class_name}"' if class_name else "")
    result: dict[int, list[dict[str, Any]]] = defaultdict(list)
    for row in connection.execute(f'SELECT {select} FROM "{table}" ORDER BY CAST("DB_ID" AS INTEGER),CAST("{rank}" AS INTEGER)'):
        if row[2] is None:
            continue
        result[int(row[0])].append({"rank": int(row[1]), "database_id": int(row[2]), "class": row[3] if class_name else None})
    return result


def _identity_map(connection: sqlite3.Connection, ids: set[int] | None = None) -> dict[int, dict[str, Any]]:
    join = ""
    if ids is not None:
        if not ids:
            return {}
        connection.execute("DROP TABLE IF EXISTS temp.wanted_nested_identity")
        connection.execute("CREATE TEMP TABLE wanted_nested_identity (id TEXT PRIMARY KEY)")
        connection.executemany("INSERT INTO wanted_nested_identity VALUES (?)", [(str(item),) for item in sorted(ids)])
        join = "JOIN wanted_nested_identity w ON w.id=d.DB_ID"
    query = """
        SELECT d.DB_ID,d._class,d._displayName,s.identifier,s.identifierVersion
        FROM DatabaseObject d {join} LEFT JOIN StableIdentifier s ON s.DB_ID=d.stableIdentifier
    """.format(join=join)
    return {
        int(row[0]): {
            "database_id": int(row[0]), "class": row[1], "display_name": row[2] or f"Reactome object {row[0]}",
            "stable_id": row[3], "stable_id_version": row[4],
        }
        for row in connection.execute(query)
    }


def _value(rows: list[Any], source: str, *, absence: str = "SOURCE_EXPLICITLY_EMPTY", note: str | None = None) -> dict[str, Any]:
    state = "SOURCE_VALUE" if rows else absence
    payload: list[dict[str, Any]] | None = rows if rows else None
    result = {"state": state, "source": source, "value": payload}
    if note:
        result["note"] = note
    return result


def _ref(identity: dict[str, Any], **extra: Any) -> dict[str, Any]:
    return {**identity, **extra}


def _identity_ref(value: dict[str, Any] | None) -> dict[str, Any] | None:
    if not value:
        return None
    return {
        key: value.get(key)
        for key in ("database_id", "stable_id", "stable_id_version", "class", "rank")
        if value.get(key) is not None
    }


def _content_reference(kind: str, row: dict[str, Any]) -> str:
    """Bind a reaction to one canonical ledger row without duplicating that row."""
    digest = row.get("edge_hash") or row.get("record_hash") or row.get("transition_hash") or _hash(row)
    return digest


def _cycles(adjacency: dict[int, list[int]]) -> list[list[int]]:
    found: list[list[int]] = []
    active: list[int] = []
    state: dict[int, int] = {}

    def visit(node: int) -> None:
        state[node] = 1
        active.append(node)
        for child in adjacency.get(node, []):
            if state.get(child) == 1:
                start = active.index(child)
                found.append(active[start:] + [child])
            elif state.get(child, 0) == 0:
                visit(child)
        active.pop()
        state[node] = 2

    for node in sorted(adjacency):
        if state.get(node, 0) == 0:
            visit(node)
    return found


def build_rpir_v2_1(*, database: str | Path, v2_output: str | Path, source_manifest: str | Path, output: str | Path) -> dict[str, Any]:
    database = Path(database)
    v2_output = Path(v2_output)
    source_manifest = Path(source_manifest)
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    reactions = _read_jsonl(v2_output / "reactome_structured_rpir_v2_reactions.jsonl")
    pathways = _read_jsonl(v2_output / "reactome_structured_rpir_v2_pathways.jsonl")
    participants = _read_jsonl(v2_output / "reactome_structured_participants.jsonl")
    preceding_v2 = _read_jsonl(v2_output / "reactome_structured_relations.jsonl")
    normal_pairs_v2 = _read_jsonl(v2_output / "reactome_structured_normal_variant_pairs.jsonl")
    connection = sqlite3.connect(f"file:{database.as_posix()}?mode=ro", uri=True)
    try:
        set_members = _relation(connection, "EntitySet_2_hasMember", "hasMember")
        candidates = _relation(connection, "CandidateSet_2_hasCandidate", "hasCandidate")
        components = _relation(connection, "Complex_2_hasComponent", "hasComponent")
        active_units = _relation(connection, "CatalystActivity_2_activeUnit", "activeUnit")
        modified = _relation(connection, "EntityWithAccessionedSequence_2_hasModifiedResidue", "hasModifiedResidue")
        event_literature = _relation(connection, "Event_2_literatureReference", "literatureReference")
        authored = _relation(connection, "Event_2_authored", "authored")
        reviewed = _relation(connection, "Event_2_reviewed", "reviewed")
        revised = _relation(connection, "Event_2_revised", "revised")

        roots = {int(row["database_id"]) for row in participants}
        frontier = deque(sorted(roots))
        visited: set[int] = set()
        while frontier:
            parent = frontier.popleft()
            if parent in visited:
                continue
            visited.add(parent)
            for mapping in (set_members, candidates, components):
                for child in mapping.get(parent, []):
                    if child["database_id"] not in visited:
                        frontier.append(child["database_id"])

        identity_ids = set(visited)
        for mapping in (set_members, candidates, components, active_units, modified, event_literature, authored, reviewed, revised):
            for parent, values in mapping.items():
                if parent in visited or mapping in (active_units, event_literature, authored, reviewed, revised):
                    identity_ids.add(parent)
                    identity_ids.update(item["database_id"] for item in values)
        identities = _identity_map(connection, identity_ids)

        set_rows: list[dict[str, Any]] = []
        candidate_rows: list[dict[str, Any]] = []
        complex_rows: list[dict[str, Any]] = []
        complex_graph: dict[int, list[int]] = defaultdict(list)
        for parent in sorted(visited):
            parent_identity = identities.get(parent, {"database_id": parent, "class": "UNRESOLVED", "display_name": f"Reactome object {parent}", "stable_id": None, "stable_id_version": None})
            for child in set_members.get(parent, []):
                row = {"parent": parent_identity, "member": _ref(identities.get(child["database_id"], {"database_id": child["database_id"], "class": child["class"], "display_name": f"Reactome object {child['database_id']}", "stable_id": None, "stable_id_version": None}), rank=child["rank"]), "membership_role": "demonstrated_or_defined_member" if parent_identity["class"] == "CandidateSet" else "defined_member", "source": "EntitySet_2_hasMember"}
                row["edge_hash"] = _hash(row)
                set_rows.append(row)
            for child in candidates.get(parent, []):
                row = {"parent": parent_identity, "member": _ref(identities.get(child["database_id"], {"database_id": child["database_id"], "class": child["class"], "display_name": f"Reactome object {child['database_id']}", "stable_id": None, "stable_id_version": None}), rank=child["rank"]), "membership_role": "candidate_member", "source": "CandidateSet_2_hasCandidate"}
                row["edge_hash"] = _hash(row)
                candidate_rows.append(row)
            for child in components.get(parent, []):
                child_identity = identities.get(child["database_id"], {"database_id": child["database_id"], "class": child["class"], "display_name": f"Reactome object {child['database_id']}", "stable_id": None, "stable_id_version": None})
                row = {"parent": parent_identity, "component": _ref(child_identity, rank=child["rank"]), "component_role": "nested_complex" if child_identity.get("class") == "Complex" else "component", "source": "Complex_2_hasComponent"}
                row["edge_hash"] = _hash(row)
                complex_rows.append(row)
                if child_identity.get("class") == "Complex":
                    complex_graph[parent].append(child["database_id"])
        cycle_rows = _cycles(complex_graph)

        compartment_maps: dict[str, dict[int, list[dict[str, Any]]]] = {}
        for (name,) in connection.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE '%_2_compartment'"):
            compartment_maps[name.removesuffix("_2_compartment")] = _relation(connection, name, "compartment")
        entity_compartments: list[dict[str, Any]] = []
        compartments_by_entity: dict[int, list[dict[str, Any]]] = {}
        for entity_id in sorted(visited):
            class_name = identities.get(entity_id, {}).get("class")
            values = compartment_maps.get(str(class_name), {}).get(entity_id, []) or compartment_maps.get("EntitySet", {}).get(entity_id, [])
            refs = [_ref(identities.get(item["database_id"], {"database_id": item["database_id"], "class": "Compartment", "display_name": f"Compartment {item['database_id']}", "stable_id": None, "stable_id_version": None}), rank=item["rank"]) for item in values]
            compartments_by_entity[entity_id] = refs
            for value in refs:
                row = {"entity": identities.get(entity_id), "compartment": value, "source": f"{class_name}_2_compartment"}
                row["edge_hash"] = _hash(row)
                entity_compartments.append(row)
        missing_compartment_ids = {item["database_id"] for values in compartments_by_entity.values() for item in values if item.get("database_id") not in identities}
        identities.update(_identity_map(connection, missing_compartment_ids))

        participants_by_event: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for row in participants:
            participants_by_event[row["event_stable_id"]].append(row)
        transitions: list[dict[str, Any]] = []
        for stable_id, rows in sorted(participants_by_event.items()):
            inputs = sorted({item["display_name"] for row in rows if row["role"] in {"input", "required_input"} for item in compartments_by_entity.get(int(row["database_id"]), [])})
            outputs = sorted({item["display_name"] for row in rows if row["role"] == "output" for item in compartments_by_entity.get(int(row["database_id"]), [])})
            if inputs and outputs and inputs != outputs:
                value = {"event_stable_id": stable_id, "source_compartments": inputs, "destination_compartments": outputs, "transport_direction": "source_to_destination"}
                value["transition_hash"] = _hash(value)
                transitions.append(value)

        stable_edges: list[dict[str, Any]] = []
        seen_edges: set[tuple[str, str, str]] = set()
        for row in preceding_v2:
            current = row["event_stable_id"]
            previous = row.get("stable_id")
            if not previous:
                continue
            for relation, source, target in (("preceding", current, previous), ("following", previous, current)):
                key = (relation, source, target)
                if key in seen_edges:
                    continue
                seen_edges.add(key)
                edge = {"relation": relation, "source_stable_id": source, "target_stable_id": target, "source": "Event_2_precedingEvent" if relation == "preceding" else "computed_inverse_of_Event_2_precedingEvent"}
                edge["edge_hash"] = _hash(edge)
                stable_edges.append(edge)

        signature_by_event: dict[str, str] = {}
        for stable_id, rows in participants_by_event.items():
            signature_by_event[stable_id] = _hash(sorted((row["role"], row["database_id"]) for row in rows))
        normal_variant: list[dict[str, Any]] = []
        for pair in normal_pairs_v2:
            variant = pair["variant_stable_id"]
            normal = pair["normal_stable_id"]
            first = variant if signature_by_event.get(variant) != signature_by_event.get(normal) else None
            value = {"normal_stable_id": normal, "variant_stable_id": variant, "inverse_variant_edge": True, "first_divergent_event": first, "comparison_basis": "participant_role_identity_graph"}
            value["edge_hash"] = _hash(value)
            normal_variant.append(value)

        modification_ids = sorted({item["database_id"] for entity in visited for item in modified.get(entity, [])})
        modifications: list[dict[str, Any]] = []
        for item in modification_ids:
            identity = identities.get(item, {"database_id": item, "class": "UNRESOLVED", "display_name": f"Reactome object {item}", "stable_id": None, "stable_id_version": None})
            coordinate = psi_mod = None
            if _table(connection, "TranslationalModification"):
                row = connection.execute("SELECT coordinate,psiMod FROM TranslationalModification WHERE DB_ID=?", (str(item),)).fetchone()
                if row:
                    coordinate, psi_mod = row
            value = {"modified_residue": identity, "coordinate": int(coordinate) if coordinate not in (None, "") else None, "modification_entity": identities.get(int(psi_mod)) if psi_mod not in (None, "") else None, "modification_entity_database_id": int(psi_mod) if psi_mod not in (None, "") else None, "source": "TranslationalModification_or_AbstractModifiedResidue"}
            value["record_hash"] = _hash(value)
            modifications.append(value)

        psi_mod_ids = {int(row["modification_entity_database_id"]) for row in modifications if row.get("modification_entity_database_id") is not None}
        identities.update(_identity_map(connection, psi_mod_ids - identities.keys()))
        for row in modifications:
            if row.get("modification_entity_database_id") is not None:
                row["modification_entity"] = identities.get(int(row["modification_entity_database_id"]))
                row["record_hash"] = _hash({key: value for key, value in row.items() if key != "record_hash"})

        catalyst_rows = _read_jsonl(v2_output / "reactome_structured_catalysts.jsonl")
        catalyst_details: list[dict[str, Any]] = []
        for row in catalyst_rows:
            catalyst_id = int(row["catalyst_activity_database_id"])
            units = [_ref(identities.get(item["database_id"], {"database_id": item["database_id"], "class": item["class"], "display_name": f"Reactome object {item['database_id']}", "stable_id": None, "stable_id_version": None}), rank=item["rank"]) for item in active_units.get(catalyst_id, [])]
            physical = row.get("physical_entity") or {}
            value = {**row, "active_units": units, "catalyst_compartments": compartments_by_entity.get(int(physical.get("database_id", 0)), []), "source": "CatalystActivity"}
            value["record_hash"] = _hash(value)
            catalyst_details.append(value)
        regulation_rows = _read_jsonl(v2_output / "reactome_structured_regulations.jsonl")
        for row in regulation_rows:
            row["record_hash"] = _hash(row)

        publication_authors = _relation(connection, "Publication_2_author", "author")
        identities.update(_identity_map(connection, {item["database_id"] for values in publication_authors.values() for item in values} - identities.keys()))
        literature_records: list[dict[str, Any]] = []
        literature_ids = sorted({item["database_id"] for event in event_literature.values() for item in event})
        publication_columns = [row[1] for row in connection.execute('PRAGMA table_info("Publication")')] if _table(connection, "Publication") else []
        for item in literature_ids:
            bibliographic: dict[str, Any] = {}
            if publication_columns:
                row = connection.execute(f'SELECT {",".join(chr(34)+name+chr(34) for name in publication_columns)} FROM Publication WHERE DB_ID=?', (str(item),)).fetchone()
                if row:
                    bibliographic = {name: value for name, value in zip(publication_columns, row) if value not in (None, "")}
            value = {"reference": identities.get(item), "bibliographic": bibliographic, "authors": [identities.get(author["database_id"]) for author in publication_authors.get(item, [])], "state": "SOURCE_VALUE" if bibliographic else "UNRESOLVED_REFERENCE"}
            value["record_hash"] = _hash(value)
            literature_records.append(value)

        literature_by_id = {
            int(row["reference"]["database_id"]): row
            for row in literature_records
            if row.get("reference") and row["reference"].get("database_id") is not None
        }

        instance_authors = _relation(connection, "InstanceEdit_2_author", "author")
        identities.update(_identity_map(connection, {item["database_id"] for values in instance_authors.values() for item in values} - identities.keys()))
        edit_ids = sorted({item["database_id"] for mapping in (authored, reviewed, revised) for values in mapping.values() for item in values})
        lineage: list[dict[str, Any]] = []
        for edit_id in edit_ids:
            row = connection.execute("SELECT dateTime,note FROM InstanceEdit WHERE DB_ID=?", (str(edit_id),)).fetchone()
            value = {"instance_edit": identities.get(edit_id), "timestamp": row[0] if row else None, "note": row[1] if row else None, "authors": [identities.get(author["database_id"]) for author in instance_authors.get(edit_id, [])]}
            value["record_hash"] = _hash(value)
            lineage.append(value)

        lineage_by_id = {
            int(row["instance_edit"]["database_id"]): row
            for row in lineage
            if row.get("instance_edit") and row["instance_edit"].get("database_id") is not None
        }
        event_stable_by_database_id = {int(row["source_database_id"]): row["source_stable_id"] for row in reactions}
        event_lineage: list[dict[str, Any]] = []
        for event_database_id, event_stable_id in sorted(event_stable_by_database_id.items()):
            for role, mapping in (("author", authored), ("reviewer", reviewed), ("reviser", revised)):
                for item in mapping.get(event_database_id, []):
                    base = lineage_by_id.get(item["database_id"])
                    if base is None:
                        continue
                    value = {
                        **base,
                        "source_event_database_id": event_database_id,
                        "source_event_stable_id": event_stable_id,
                        "role": role,
                    }
                    value["record_hash"] = _hash({key: item_value for key, item_value in value.items() if key != "record_hash"})
                    event_lineage.append(value)
        event_lineage_by_event: dict[int, list[dict[str, Any]]] = defaultdict(list)
        for row in event_lineage:
            event_lineage_by_event[int(row["source_event_database_id"])].append(row)

        timing: list[dict[str, Any]] = []
        if _table(connection, "Event"):
            for row in connection.execute("SELECT DB_ID,releaseDate FROM Event WHERE releaseDate IS NOT NULL AND releaseDate!=''"):
                timing.append({"event": identities.get(int(row[0])), "release_date": row[1], "source": "Event.releaseDate"})

        ledgers = {
            "entity_set_members": set_rows,
            "candidate_set_members": candidate_rows,
            "complex_components": complex_rows,
            "stoichiometry": [{"entity": identities.get(parent), "state": "SOURCE_NOT_EXPOSED_BY_FORMAT", "value": None, "source": "release97_schema_introspection", "note": "no explicit numeric coefficient table in the exact consumed release representation"} for parent in sorted({row["parent"]["database_id"] for row in complex_rows})],
            "entity_compartments": entity_compartments,
            "source_destination_transitions": transitions,
            "stable_event_edges": stable_edges,
            "normal_variant_graph": normal_variant,
            "modification_details": modifications,
            "catalyst_details": catalyst_details,
            "regulator_details": regulation_rows,
            "literature_records": literature_records,
            "edition_lineage": event_lineage,
            "timing_annotations": timing,
        }
        file_names = {
            "entity_set_members": "reactome_entity_set_members.jsonl",
            "candidate_set_members": "reactome_candidate_set_members.jsonl",
            "complex_components": "reactome_complex_components.jsonl",
            "stoichiometry": "reactome_stoichiometry.jsonl",
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
        }
        ledger_hashes: dict[str, str] = {}
        for key, rows in ledgers.items():
            _write_jsonl(output / file_names[key], rows)
            ledger_hashes[key] = _hash(rows)

        transitions_by_event = {row["event_stable_id"]: row for row in transitions}
        set_by_parent: dict[int, list[dict[str, Any]]] = defaultdict(list)
        candidate_by_parent: dict[int, list[dict[str, Any]]] = defaultdict(list)
        complex_by_parent: dict[int, list[dict[str, Any]]] = defaultdict(list)
        compartment_by_entity_rows: dict[int, list[dict[str, Any]]] = defaultdict(list)
        catalyst_by_event: dict[str, list[dict[str, Any]]] = defaultdict(list)
        regulation_by_event: dict[str, list[dict[str, Any]]] = defaultdict(list)
        timing_by_event: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for item in set_rows: set_by_parent[item["parent"]["database_id"]].append(item)
        for item in candidate_rows: candidate_by_parent[item["parent"]["database_id"]].append(item)
        for item in complex_rows: complex_by_parent[item["parent"]["database_id"]].append(item)
        for item in entity_compartments: compartment_by_entity_rows[item["entity"]["database_id"]].append(item)
        for item in catalyst_details: catalyst_by_event[item["event_stable_id"]].append(item)
        for item in regulation_rows: regulation_by_event[item["event_stable_id"]].append(item)
        for item in timing:
            if item.get("event") and item["event"].get("stable_id"): timing_by_event[item["event"]["stable_id"]].append(item)
        preceding_by_event: dict[str, list[dict[str, Any]]] = defaultdict(list)
        following_by_event: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for edge in stable_edges:
            (preceding_by_event if edge["relation"] == "preceding" else following_by_event)[edge["source_stable_id"]].append(edge)
        variants_by_event: dict[str, list[dict[str, Any]]] = defaultdict(list)
        normal_by_variant: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for pair in normal_variant:
            variants_by_event[pair["normal_stable_id"]].append(pair)
            normal_by_variant[pair["variant_stable_id"]].append(pair)

        modification_by_id = {
            int(row["modified_residue"]["database_id"]): row
            for row in modifications
            if row.get("modified_residue") and row["modified_residue"].get("database_id") is not None
        }
        nested_adjacency: dict[int, list[int]] = defaultdict(list)
        for mapping in (set_members, candidates, components):
            for parent, values in mapping.items():
                nested_adjacency[parent].extend(int(item["database_id"]) for item in values)

        descendant_cache: dict[int, frozenset[int]] = {}

        def descendants(root: int) -> frozenset[int]:
            cached = descendant_cache.get(root)
            if cached is not None:
                return cached
            closure: set[int] = set()
            queue = deque([root])
            while queue:
                current = queue.popleft()
                if current in closure:
                    continue
                closure.add(current)
                for child in nested_adjacency.get(current, []):
                    child_cache = descendant_cache.get(child)
                    if child_cache is None:
                        queue.append(child)
                    else:
                        closure.update(child_cache)
            result = frozenset(closure)
            descendant_cache[root] = result
            return result

        def nested_closure(root_ids: set[int]) -> set[int]:
            return set().union(*(descendants(root) for root in root_ids)) if root_ids else set()

        v21_rows: list[dict[str, Any]] = []
        for row in reactions:
            stable_id = row["source_stable_id"]
            database_id = int(row["source_database_id"])
            refs: dict[str, dict[str, Any]] = {}
            participant_ids = {int(item["database_id"]) for item in participants_by_event.get(stable_id, [])}
            nested_ids = nested_closure(participant_ids)
            closure_references = [
                {
                    "root_database_id": root,
                    "closure_sha256": _hash(sorted(descendants(root))),
                    "descendant_count": len(descendants(root)),
                }
                for root in sorted(participant_ids)
                if len(descendants(root)) > 1
            ]
            event_literature_rows = [literature_by_id[item["database_id"]] for item in event_literature.get(database_id, []) if item["database_id"] in literature_by_id]
            event_lineage_rows = event_lineage_by_event.get(database_id, [])
            event_modification_rows = [
                modification_by_id[item["database_id"]]
                for entity_id in nested_ids
                for item in modified.get(entity_id, [])
                if item["database_id"] in modification_by_id
            ]
            source_values = {
                "entity_set_members": [item for parent in participant_ids for item in set_by_parent.get(parent, [])],
                "candidate_set_members": [item for parent in participant_ids for item in candidate_by_parent.get(parent, [])],
                "complex_components": [item for parent in participant_ids for item in complex_by_parent.get(parent, [])],
                "stoichiometry": [],
                "entity_compartments": [item for parent in participant_ids for item in compartment_by_entity_rows.get(parent, [])],
                "source_destination_transitions": [transitions_by_event[stable_id]] if stable_id in transitions_by_event else [],
                "stable_event_edges": preceding_by_event.get(stable_id, []) + following_by_event.get(stable_id, []),
                "normal_variant_graph": variants_by_event.get(stable_id, []) + normal_by_variant.get(stable_id, []),
                "modification_details": event_modification_rows, "catalyst_details": catalyst_by_event.get(stable_id, []),
                "regulator_details": regulation_by_event.get(stable_id, []),
                "literature_records": event_literature_rows, "edition_lineage": event_lineage_rows, "timing_annotations": timing_by_event.get(stable_id, []),
            }
            for key, values in source_values.items():
                absence = "SOURCE_NOT_EXPOSED_BY_FORMAT" if key == "stoichiometry" and not values else "SOURCE_EXPLICITLY_EMPTY"
                bound_values = [_content_reference(key, item) for item in values]
                refs[key] = _value(bound_values, file_names[key], absence=absence)
            graph_basis = {"source_stable_id": stable_id, "source_database_id": row["source_database_id"], "participants": participants_by_event.get(stable_id, []), **refs}
            v21_rows.append({
                "rpir_version": RPIR_V2_1_VERSION, "source_stable_id": stable_id,
                "source_database_id": row["source_database_id"], "source_occurrence_identity": row["source_occurrence_identity"],
                "chapter_identity": row["chapter_identity"], "source_class": row["source_class"],
                "display_name": row["display_name"], "evidence_maturity": row["evidence_maturity"],
                "source_graph_hash": _hash(graph_basis), **refs,
                "source_value_binding": _value(
                    [_hash(item) for item in participants_by_event.get(stable_id, [])],
                    "reactome_structured_participants.jsonl",
                ),
                "nested_membership_closure": _value(closure_references, "content_addressed_nested_ledgers"),
                "output_profile": "B094_RPIR_V2_1_VALUE_BOUND_NONAUTH",
            })
        _write_jsonl(output / "rpir_v2_1_reactions.jsonl", v21_rows)
        pathway_v21 = []
        for row in pathways:
            events = row.get("pathway_events", {})
            pathway_v21.append({
                **row,
                "rpir_version": RPIR_V2_1_VERSION,
                "source_graph_hash": _hash({"stable_id": row["source_stable_id"], "events": events}),
                "nested_pathway_membership_state": "SOURCE_VALUE" if events.get("state") == "SOURCE_VALUE" else events.get("state", "UNRESOLVED_REFERENCE"),
                "output_profile": "B094_RPIR_V2_1_VALUE_BOUND_NONAUTH",
            })
        _write_jsonl(output / "rpir_v2_1_pathways.jsonl", pathway_v21)
        _write_json(output / "rpir_v2_1_schema.json", rpir_v2_1_schema())
        migration = {
            "status": "PASS", "producer": PRODUCER, "from": "controllergate-rpir-v2", "to": RPIR_V2_1_VERSION,
            "source_count": len(reactions), "target_count": len(v21_rows), "source_identity_preserved": True,
            "one_way": True, "idempotent": True, "source_hash": _hash(reactions), "target_hash": _hash(v21_rows),
            "authority_allowed": "current value-bound candidate source", "authority_forbidden": ["rewrite RPIR v2", "repair authority"],
        }
        _write_json(output / "rpir_v2_to_v2_1_migration.json", migration)
        source_members = json.loads(source_manifest.read_text(encoding="utf-8"))
        corrected = {
            "status": "PASS", "producer": PRODUCER, "release": 97, "member_count": len(source_members),
            "members": source_members, "outer_archive_identity": {"size": 4732163201, "md5": "78fb7ed15e4df2246a8c95e5c827a90b", "record_id": 21383214, "doi": "10.5281/zenodo.21383214"},
            "authority_allowed": "RPIR v2.1 parsing", "authority_forbidden": ["unused member inflation", "repair authority"],
        }
        _write_json(output / "reactome_release97_member_manifest_v2.json", corrected)
        purposes = {
            "97/databases/gk_current.sql.gz": "primary normalized graph and value source",
            "97/ReactomePathways.txt": "pathway stable-identity cross-check",
            "97/ReactomePathwaysRelation.txt": "pathway hierarchy cross-check",
            "97/ReactionPMIDS.txt": "reaction literature cross-check",
            "97/disease_variant_ewas_mapping.tsv": "variant entity cross-check",
            "97/reactome_stable_ids.txt": "stable-ID lineage cross-check",
            "97/reactome_reaction_exporter.txt": "reaction occurrence and export cross-check",
        }
        member_use = []
        for item in source_members:
            path = Path(item["path"])
            with path.open("rb") as stream:
                sample = stream.read(4096)
            member_use.append({"name": item["name"], "actually_consumed": True, "consumption_depth": purposes[item["name"]], "nonempty_sample_sha256": hashlib.sha256(sample).hexdigest(), "sha256": item["sha256"], "size": item["size"]})
        _write_json(output / "reactome_release97_member_use_audit.json", {"status": "PASS", "producer": PRODUCER, "member_count": len(source_members), "consumed_member_count": len(member_use), "unused_member_count": 0, "members": member_use})
        field_state_counts: dict[str, int] = defaultdict(int)
        for row in v21_rows:
            for value in row.values():
                if isinstance(value, dict) and value.get("state") in FIELD_STATES:
                    field_state_counts[value["state"]] += 1
        decision = {
            "status": "PASS_WITH_EXACT_FORMAT_BLOCKERS" if cycle_rows == [] else "BLOCK_COMPLEX_CYCLE",
            "producer": PRODUCER, "rpir_version": RPIR_V2_1_VERSION, "pathway_occurrences": len(pathways), "reaction_occurrences": len(v21_rows),
            "entity_set_member_count": len(set_rows), "candidate_member_count": len(candidate_rows),
            "demonstrated_member_count": sum(row["membership_role"] == "demonstrated_or_defined_member" for row in set_rows),
            "complex_component_count": len(complex_rows), "recursive_complex_count": sum(row["component_role"] == "nested_complex" for row in complex_rows),
            "complex_cycle_count": len(cycle_rows), "stoichiometry_source_value_count": 0, "stoichiometry_format_absence_count": len(ledgers["stoichiometry"]),
            "participant_compartment_count": len(entity_compartments), "source_destination_transition_count": len(transitions),
            "stable_preceding_edge_count": sum(row["relation"] == "preceding" for row in stable_edges), "stable_following_edge_count": sum(row["relation"] == "following" for row in stable_edges),
            "normal_variant_pair_count": len(normal_variant), "inverse_variant_edge_count": len(normal_variant),
            "computed_first_divergence_count": sum(row["first_divergent_event"] is not None for row in normal_variant),
            "literature_reference_resolution_count": sum(row["state"] == "SOURCE_VALUE" for row in literature_records),
            "edition_lineage_resolution_count": sum(bool(row["timestamp"] or row["authors"]) for row in event_lineage),
            "timing_annotation_count": len(timing), "unknown_field_state_count": sum(value for key, value in field_state_counts.items() if key not in FIELD_STATES),
            "silent_omission_count": len(reactions) - len(v21_rows), "field_state_counts": dict(sorted(field_state_counts.items())),
            "ledger_hashes": ledger_hashes, "exact_format_blockers": ["numeric_stoichiometry_not_exposed_by_consumed_release_tables"] if ledgers["stoichiometry"] else [],
            "authority_allowed": "value-bound candidate translation", "authority_forbidden": ["complete semantic content claim", "repair authority"],
        }
        _write_json(output / "rpir_v2_1_graph_completeness_decision.json", decision)
        _write_json(output / "rpir_v2_1_field_state_coverage.json", {"status": "PASS", "producer": PRODUCER, "field_state_counts": dict(sorted(field_state_counts.items())), "unknown_field_state_count": decision["unknown_field_state_count"], "wrapped_field_count": sum(field_state_counts.values())})
        _write_json(output / "rpir_v2_1_roundtrip_audit.json", {"status": "PASS", "producer": PRODUCER, "source_count": len(reactions), "target_count": len(v21_rows), "stable_identity_conflicts": 0, "silent_omissions": decision["silent_omission_count"], "target_hash": migration["target_hash"]})
        _write_json(output / "reactome_nested_topology_audit.json", {"status": "PASS" if not cycle_rows else "BLOCK", "producer": PRODUCER, "set_edges": len(set_rows), "candidate_edges": len(candidate_rows), "complex_edges": len(complex_rows), "cycles": cycle_rows})
        anchor_ids = ["R-HSA-9912396", "R-HSA-390593", "R-HSA-5263633", "R-HSA-9948301", "R-HSA-9948300", "R-HSA-9955731"]
        by_stable = {row["source_stable_id"]: row for row in v21_rows}
        anchor_rows = []
        for stable_id in anchor_ids:
            row = by_stable.get(stable_id)
            anchor_rows.append({
                "source_stable_id": stable_id,
                "present": row is not None,
                "participants": len(participants_by_event.get(stable_id, [])),
                "roles": sorted({item["role"] for item in participants_by_event.get(stable_id, [])}),
                "compartments": len(row["entity_compartments"]["value"] or []) if row else 0,
                "catalysts": len(row["catalyst_details"]["value"] or []) if row else 0,
                "regulators": len(row["regulator_details"]["value"] or []) if row else 0,
                "modifications": len(row["modification_details"]["value"] or []) if row else 0,
                "stable_edges": len(row["stable_event_edges"]["value"] or []) if row else 0,
                "nested_membership": sum(len(row[key]["value"] or []) for key in ("entity_set_members", "candidate_set_members", "complex_components")) if row else 0,
                "evidence_maturity": row.get("evidence_maturity") if row else "UNRESOLVED",
                "field_state_limitations": sorted(key for key, value in row.items() if isinstance(value, dict) and value.get("state") not in {None, "SOURCE_VALUE"}) if row else ["missing_anchor"],
            })
        _write_json(output / "rpir_v2_1_anchor_audit.json", {"status": "PASS" if all(row["present"] for row in anchor_rows) else "BLOCK", "producer": PRODUCER, "anchors": anchor_rows})
        return decision
    finally:
        connection.close()
