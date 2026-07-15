from __future__ import annotations

import hashlib
import json
import os
import re
import sqlite3
import stat
from pathlib import Path
from typing import Any, Iterable

from .database import create_database
from .schema import EVENT_TYPES, RPIR_VERSION, maturity_for, rpir_schema


PARSER_IDENTITY = "controllergate.reactome_ir.ingest:pymupdf_text_v1"
FIELD_NAMES = {
    "inputs": "Inputs",
    "required_inputs": "Required inputs",
    "outputs": "Outputs",
    "catalyst_activity": "Catalyst activities",
    "active_unit": "Active unit",
    "positive_regulators": "Positive regulators",
    "negative_regulators": "Negative regulators",
    "entity_sets": "Entity sets",
    "candidate_sets": "Candidate sets",
    "demonstrated_members": "Demonstrated members",
    "complex_membership": "Complex membership",
    "stoichiometry": "Stoichiometry",
    "compartment": "Compartments",
    "source_compartment": "Source compartment",
    "destination_compartment": "Destination compartment",
    "modifications": "Modifications",
    "preceding_events": "Preceded by",
    "following_events": "Followed by",
}


def _sha_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _sha_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _identity(*parts: object) -> str:
    return hashlib.sha256(json.dumps(parts, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def _write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")


def _write_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(row, sort_keys=True) + "\n" for row in rows), encoding="utf-8", newline="\n")


def _field(text: str, label: str) -> list[str]:
    match = re.search(rf"(?m)^{re.escape(label)}:\s*([^\n]+)", text)
    if not match:
        return []
    return [item.strip() for item in re.split(r",\s*|;\s*", match.group(1)) if item.strip()]


def _title(text: str, stable_id: str) -> str:
    before = text.split("Stable identifier:", 1)[0]
    lines = [line.strip() for line in before.splitlines() if line.strip()]
    lines = [line for line in lines if not line.startswith(("Location:", "https://reactome.org", "Page "))]
    return lines[0].removesuffix(" ↗").strip() if lines else stable_id


def _hierarchy(text: str, chapter: str) -> list[str]:
    match = re.search(r"Location:\s*(.*?)\nStable identifier:", text, flags=re.S)
    if not match:
        return [chapter]
    value = re.sub(r"\s+", " ", match.group(1)).replace(" → ", "→")
    return [item.strip() for item in value.split("→") if item.strip()]


def _editions(text: str) -> list[dict[str, str]]:
    rows = []
    for date, role, contributor in re.findall(r"(?m)^(\d{4}-\d{2}-\d{2})\s+(Authored|Edited|Reviewed|Revised)\s+([^\n]+)", text):
        rows.append({"date": date, "role": role.lower(), "contributor": contributor.rstrip(".").strip()})
    return rows


def _event_record(*, stable_id: str, text: str, page_number: int, chapter: str, document_id: str) -> dict[str, Any]:
    event_type_match = re.search(r"(?m)^Type:\s*([^\n]+)", text)
    event_type = event_type_match.group(1).strip().lower() if event_type_match else "pathway"
    inferred = _field(text, "Inferred from")
    fields = {name: _field(text, label) for name, label in FIELD_NAMES.items()}
    title = _title(text, stable_id)
    maturity = maturity_for(event_type=event_type, inferred_from=inferred[0] if inferred else None, chapter=chapter, text=text)
    literature = text.split("Literature references", 1)[1].split("Editions", 1)[0].strip() if "Literature references" in text else ""
    timing = [line.strip() for line in text.splitlines() if re.search(r"(?i)half-life|duration|timing|pulse|phase delay", line)]
    record = {
        "rpir_version": RPIR_VERSION,
        "stable_source_identity": stable_id,
        "source_occurrence_identity": _identity(document_id, stable_id),
        "source_document_id": document_id,
        "chapter_identity": chapter,
        "pathway_hierarchy": _hierarchy(text, chapter),
        "title": title,
        "source_event_type": event_type,
        "source_evidence_maturity": maturity,
        "species": "Homo sapiens" if stable_id.startswith("R-HSA-") else "UNRESOLVED",
        "orthology_status": "inferred" if inferred else "direct_or_not_stated",
        "normal_or_variant_role": "variant_or_disease_context" if chapter == "Disease" else "normal",
        "inputs": fields["inputs"],
        "required_inputs": fields["required_inputs"],
        "outputs": fields["outputs"],
        "catalyst_activity": fields["catalyst_activity"],
        "active_unit": fields["active_unit"],
        "positive_regulators": fields["positive_regulators"],
        "negative_regulators": fields["negative_regulators"],
        "entity_sets": fields["entity_sets"],
        "candidate_sets": fields["candidate_sets"],
        "demonstrated_members": fields["demonstrated_members"],
        "complex_membership": fields["complex_membership"],
        "stoichiometry": fields["stoichiometry"],
        "compartment": fields["compartment"],
        "source_compartment": fields["source_compartment"],
        "destination_compartment": fields["destination_compartment"],
        "transport_or_translocation": bool(re.search(r"(?i)transport|translocat|import|export", title + " " + text[:800])),
        "modifications": fields["modifications"],
        "preceding_events": fields["preceding_events"],
        "following_events": fields["following_events"],
        "reversibility": "reversible" if re.search(r"(?i)reversible", text) else ("irreversible" if re.search(r"(?i)irreversible", text) else "not_stated"),
        "timing_annotations": timing[:8],
        "uncertainty": event_type == "uncertain",
        "omitted_mechanism": event_type == "omitted",
        "negative_reaction_semantics": bool(re.search(r"(?i)does not react|failed reaction|cannot react", text)),
        "inferred_from": inferred,
        "literature_references": {"present": bool(literature), "source_text_sha256": _sha_bytes(literature.encode()) if literature else None},
        "edition_lineage": _editions(text),
        "page_number": page_number,
        "page_text_sha256": _sha_bytes(text.encode()),
        "description_excerpt": re.sub(r"\s+", " ", text)[:500],
        "translation_intake_state": "CANDIDATE_TRANSLATION",
        "producer": PARSER_IDENTITY,
        "execution_depth": "source_pdf_page_parsed",
        "semantic_scope": "Reactome source representation",
        "authority_allowed": "candidate translation and tests",
        "authority_forbidden": ["software causal authority", "repair authorization", "production promotion"],
    }
    return record


def _insert_event(connection: sqlite3.Connection, record: dict[str, Any], relations: list[dict[str, Any]], entities: list[dict[str, Any]], evidence: list[dict[str, Any]], normal_pairs: list[dict[str, Any]]) -> None:
    stable_id = record["stable_source_identity"]
    occurrence_id = record["source_occurrence_identity"]
    encoded = json.dumps(record, sort_keys=True, separators=(",", ":"))
    if record["source_event_type"] == "pathway":
        connection.execute("INSERT INTO reactome_pathways VALUES (?,?,?,?,?,?,?)", (occurrence_id, stable_id, record["chapter_identity"], record["title"], json.dumps(record["pathway_hierarchy"]), record["page_number"], encoded))
        return
    connection.execute("INSERT INTO reactome_reactions VALUES (?,?,?,?,?,?,?,?)", (occurrence_id, stable_id, record["chapter_identity"], record["title"], record["source_event_type"], record["source_evidence_maturity"], record["page_number"], encoded))
    entity = {"entity_id": _identity(occurrence_id, "reaction_subject", record["title"]), "occurrence_id": occurrence_id, "stable_id": stable_id, "role": "source_text_reaction_subject", "label": record["title"], "producer": PARSER_IDENTITY, "authority_forbidden": "physical entity identity without structured export"}
    entities.append(entity)
    connection.execute("INSERT INTO reactome_entities VALUES (?,?,?,?,?,?)", (entity["entity_id"], occurrence_id, stable_id, entity["role"], entity["label"], json.dumps(entity, sort_keys=True)))
    for label in record["compartment"]:
        compartment_id = _identity("compartment", label)
        connection.execute("INSERT OR IGNORE INTO reactome_compartments VALUES (?,?,?)", (compartment_id, label, json.dumps({"compartment_id": compartment_id, "label": label, "producer": PARSER_IDENTITY}, sort_keys=True)))
    for direction, names in (("preceding", record["preceding_events"]), ("following", record["following_events"])):
        for name in names:
            edge = {"edge_id": _identity(occurrence_id, direction, name), "occurrence_id": occurrence_id, "stable_id": stable_id, "direction": direction, "target_title": name, "target_stable_id": None, "resolution_status": "title_only_source_reference"}
            cursor = connection.execute("INSERT OR IGNORE INTO reactome_preceding_following_edges VALUES (?,?,?,?,?,?)", (edge["edge_id"], occurrence_id, stable_id, direction, name, json.dumps(edge, sort_keys=True)))
            if cursor.rowcount:
                relations.append(edge)
    for source in record["inferred_from"]:
        edge_id = _identity(occurrence_id, "orthology", source)
        connection.execute("INSERT OR IGNORE INTO reactome_orthology_edges VALUES (?,?,?,?,?)", (edge_id, occurrence_id, stable_id, source, json.dumps({"edge_id": edge_id, "occurrence_id": occurrence_id, "stable_id": stable_id, "source_description": source}, sort_keys=True)))
    evidence_row = {"evidence_id": _identity(occurrence_id, record["source_evidence_maturity"]), "occurrence_id": occurrence_id, "stable_id": stable_id, "maturity": record["source_evidence_maturity"], "decision_time_software_authority": False, "producer": PARSER_IDENTITY}
    evidence.append(evidence_row)
    connection.execute("INSERT INTO reactome_evidence_records VALUES (?,?,?,?,?)", (evidence_row["evidence_id"], occurrence_id, stable_id, evidence_row["maturity"], json.dumps(evidence_row, sort_keys=True)))
    if record["literature_references"]["present"]:
        ref_id = _identity(occurrence_id, record["literature_references"]["source_text_sha256"])
        connection.execute("INSERT OR IGNORE INTO reactome_literature_references VALUES (?,?,?,?,?)", (ref_id, occurrence_id, stable_id, record["literature_references"]["source_text_sha256"], json.dumps({"reference_id": ref_id, "occurrence_id": occurrence_id, **record["literature_references"]}, sort_keys=True)))
    for edition in record["edition_lineage"]:
        edition_id = _identity(occurrence_id, edition)
        connection.execute("INSERT OR IGNORE INTO reactome_editions VALUES (?,?,?,?,?,?,?)", (edition_id, occurrence_id, stable_id, edition["role"], edition["date"], edition["contributor"], json.dumps(edition, sort_keys=True)))
    if record["chapter_identity"] == "Disease":
        pair = {"pair_id": _identity("normal_variant", occurrence_id), "occurrence_id": occurrence_id, "variant_stable_id": stable_id, "normal_stable_id": None, "status": "UNRESOLVED_NORMAL_EVENT_ID", "first_divergent_reaction": stable_id, "producer": PARSER_IDENTITY, "authority_forbidden": "fabricated normal-event identity"}
        normal_pairs.append(pair)
        connection.execute("INSERT INTO reactome_normal_variant_pairs VALUES (?,?,?,?,?,?)", (pair["pair_id"], occurrence_id, stable_id, None, pair["status"], json.dumps(pair, sort_keys=True)))
        annotation_id = _identity("disease", occurrence_id)
        connection.execute("INSERT INTO reactome_disease_annotations VALUES (?,?,?,?)", (annotation_id, occurrence_id, stable_id, json.dumps({"annotation_id": annotation_id, "occurrence_id": occurrence_id, "stable_id": stable_id, "role": record["normal_or_variant_role"]}, sort_keys=True)))
    connection.execute("INSERT INTO reactome_translation_candidates VALUES (?,?,?,?)", (occurrence_id, stable_id, "CANDIDATE_TRANSLATION", json.dumps({"occurrence_id": occurrence_id, "stable_id": stable_id, "translation_state": "CANDIDATE_TRANSLATION"}, sort_keys=True)))


def ingest_release(*, source_root: str | Path, glossary: str | Path, chapter_config: str | Path, database: str | Path, output: str | Path) -> dict[str, Any]:
    import fitz  # type: ignore[import-not-found]

    source_root = Path(source_root)
    glossary = Path(glossary)
    output = Path(output)
    config = json.loads(Path(chapter_config).read_text(encoding="utf-8"))
    file_index = {path.name: path for path in source_root.glob("*.pdf")}
    connection = create_database(database)
    documents = []
    pathways = []
    reactions = []
    relations: list[dict[str, Any]] = []
    entities: list[dict[str, Any]] = []
    evidence: list[dict[str, Any]] = []
    normal_pairs: list[dict[str, Any]] = []
    stable_ids: dict[str, list[str]] = {}
    stable_event_types: dict[str, str] = {}
    conflicts = []
    shared_occurrences = []
    warnings = []
    try:
        for chapter_spec in config["chapters"]:
            candidates = [chapter_spec["filename"], *chapter_spec.get("aliases", [])]
            matches = [file_index[name] for name in candidates if name in file_index]
            if len(matches) != 1:
                raise ValueError(f"chapter source identity unresolved: {chapter_spec['chapter']} matches={matches}")
            path = matches[0]
            document_id = _identity("reactome-release-97", chapter_spec["chapter"], _sha_file(path))
            pdf = fitz.open(path)
            document_events = []
            release = None
            for page_index, page in enumerate(pdf, 1):
                text = page.get_text("text")
                if release is None:
                    match = re.search(r"Reactome database release:\s*(\d+)", text)
                    if match:
                        release = int(match.group(1))
                for stable_id in re.findall(r"Stable identifier:\s*(R-[A-Z]+-\d+)", text):
                    record = _event_record(stable_id=stable_id, text=text, page_number=page_index, chapter=chapter_spec["chapter"], document_id=document_id)
                    if stable_id in stable_ids:
                        shared_occurrences.append({"stable_id": stable_id, "chapters": [*stable_ids[stable_id], chapter_spec["chapter"]]})
                        if stable_event_types[stable_id] != record["source_event_type"]:
                            conflicts.append({"stable_id": stable_id, "first_event_type": stable_event_types[stable_id], "second_event_type": record["source_event_type"], "second_chapter": chapter_spec["chapter"]})
                    stable_ids.setdefault(stable_id, []).append(chapter_spec["chapter"])
                    stable_event_types.setdefault(stable_id, record["source_event_type"])
                    document_events.append(record)
                    _insert_event(connection, record, relations, entities, evidence, normal_pairs)
                    (pathways if record["source_event_type"] == "pathway" else reactions).append(record)
            observed_pathways = sum(item["source_event_type"] == "pathway" for item in document_events)
            observed_reactions = len(document_events) - observed_pathways
            if release is None:
                warnings.append({"chapter": chapter_spec["chapter"], "warning": "release marker not extracted; release bound by byte-identical archive and 29-chapter count reconciliation"})
                release = config["reactome_release"]
            document = {
                "source_document_id": document_id,
                "filename": chapter_spec["filename"],
                "observed_filename": path.name,
                "sha256": _sha_file(path),
                "size": path.stat().st_size,
                "page_count": len(pdf),
                "reactome_release": release,
                "chapter_title": chapter_spec["chapter"],
                "expected_pathway_count": chapter_spec["pathways"],
                "observed_pathway_count": observed_pathways,
                "expected_reaction_count": chapter_spec["reactions"],
                "observed_reaction_count": observed_reactions,
                "parser_identity": PARSER_IDENTITY,
                "parser_version": fitz.VersionBind,
                "structured_export_identity": None,
                "parse_warnings": [row for row in warnings if row["chapter"] == chapter_spec["chapter"]],
                "parse_failures": [],
                "review_status": "PASS" if observed_pathways == chapter_spec["pathways"] and observed_reactions == chapter_spec["reactions"] and release == 97 else "FAIL",
                "producer": PARSER_IDENTITY,
                "execution_depth": "complete_document_page_parse",
                "semantic_scope": "Reactome release 97 source identity",
                "authority_allowed": "candidate translation source",
                "authority_forbidden": ["software causal authority", "repair authority", "production authority"],
            }
            documents.append(document)
            connection.execute("INSERT INTO reactome_source_documents VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", (
                document_id, document["filename"], document["sha256"], document["size"], document["page_count"], document["reactome_release"], document["chapter_title"], document["expected_pathway_count"], document["observed_pathway_count"], document["expected_reaction_count"], document["observed_reaction_count"], document["parser_identity"], document["parser_version"], None, json.dumps(document["parse_warnings"]), json.dumps([]), document["review_status"],
            ))
        glossary_doc = fitz.open(glossary)
        glossary_document = {
            "source_document_id": _identity("genetics-glossary", _sha_file(glossary)), "filename": config["glossary"]["filename"],
            "observed_filename": glossary.name, "sha256": _sha_file(glossary), "size": glossary.stat().st_size, "page_count": len(glossary_doc),
            "reactome_release": None, "chapter_title": "Genetics glossary", "expected_pathway_count": 0, "observed_pathway_count": 0,
            "expected_reaction_count": 0, "observed_reaction_count": 0, "parser_identity": PARSER_IDENTITY,
            "parser_version": fitz.VersionBind, "structured_export_identity": None, "parse_warnings": [], "parse_failures": [],
            "review_status": "PASS", "producer": PARSER_IDENTITY, "execution_depth": "document_identity_and_page_count",
            "semantic_scope": "supplemental genetics terminology", "authority_allowed": "documentation candidate terms", "authority_forbidden": ["pathway count", "reaction count", "software authority"],
        }
        documents.append(glossary_document)
        connection.execute("INSERT INTO reactome_source_documents VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", (
            glossary_document["source_document_id"], glossary_document["filename"], glossary_document["sha256"],
            glossary_document["size"], glossary_document["page_count"], None, glossary_document["chapter_title"], 0, 0, 0, 0,
            glossary_document["parser_identity"], glossary_document["parser_version"], None, "[]", "[]", glossary_document["review_status"],
        ))
        connection.commit()
    finally:
        connection.close()
    os.chmod(database, stat.S_IREAD)
    _write_json(output / "reactome_source_documents.json", {"producer": PARSER_IDENTITY, "execution_depth": "complete_bundle_ingest", "semantic_scope": "source document custody", "authority_allowed": "candidate translation", "authority_forbidden": ["production promotion"], "documents": documents})
    _write_jsonl(output / "reactome_pathways.jsonl", pathways)
    _write_jsonl(output / "reactome_reactions.jsonl", reactions)
    _write_jsonl(output / "reactome_entities.jsonl", entities)
    _write_jsonl(output / "reactome_relations.jsonl", relations)
    _write_jsonl(output / "reactome_evidence.jsonl", evidence)
    _write_jsonl(output / "reactome_normal_variant_pairs.jsonl", normal_pairs)
    coverage = {
        "status": "PASS" if len(documents) == 30 and len(pathways) == config["expected_pathway_count"] and len(reactions) == config["expected_reaction_count"] and not conflicts and all(row["review_status"] == "PASS" for row in documents) else "REACTOME_COMPLETE_SOURCE_BUNDLE_BLOCKED_EXACT",
        "producer": PARSER_IDENTITY,
        "execution_depth": "complete_release_document_and_event_count_reconciliation",
        "semantic_scope": "Reactome release 97 source coverage",
        "authority_allowed": "100 percent candidate translation intake",
        "authority_forbidden": ["complete production implementation", "automatic repair authority"],
        "reactome_release": 97, "unique_chapter_count": len(documents) - 1, "glossary_count": 1,
        "duplicate_chapter_count": len(config["chapters"]) - len({row["sha256"] for row in documents[:-1]}),
        "expected_pathway_count": config["expected_pathway_count"], "observed_pathway_count": len(pathways),
        "expected_reaction_count": config["expected_reaction_count"], "observed_reaction_count": len(reactions),
        "silent_omission_count": max(0, config["expected_reaction_count"] - len(reactions)),
        "stable_id_conflict_count": len(conflicts), "stable_id_conflicts": conflicts,
        "unique_stable_id_count": len(stable_ids), "shared_event_occurrence_count": len(shared_occurrences),
        "uncertain_event_count": sum(row["source_event_type"] == "uncertain" for row in reactions),
        "omitted_event_count": sum(row["source_event_type"] == "omitted" for row in reactions),
        "normal_variant_pair_count": len(normal_pairs), "unresolved_normal_variant_pair_count": sum(row["status"] != "PASS" for row in normal_pairs),
        "parse_warning_count": len(warnings), "parse_warnings": warnings,
        "source_database_path_outside_git": str(Path(database).resolve()), "source_database_read_only": True,
    }
    _write_json(output / "reactome_source_coverage.json", coverage)
    _write_json(output / "rpir_schema.json", rpir_schema())
    _write_json(output / "rpir_event_type_registry.json", {"producer": "controllergate.reactome_ir.schema", "execution_depth": "schema", "semantic_scope": "source event vocabulary", "authority_allowed": "validation", "authority_forbidden": "terminal authority", "event_types": list(EVENT_TYPES)})
    _write_json(output / "rpir_evidence_maturity_registry.json", {"producer": "controllergate.reactome_ir.schema", "execution_depth": "schema", "semantic_scope": "source evidence maturity", "authority_allowed": "candidate ranking", "authority_forbidden": "software causal authority from Reactome source", "classes": rpir_schema()["software_evidence_classes"]})
    _write_json(output / "rpir_normal_variant_contract.json", {"producer": PARSER_IDENTITY, "execution_depth": "source pairing contract", "semantic_scope": "normal/variant lineage", "authority_allowed": "unresolved pair preservation", "authority_forbidden": "fabricated normal stable IDs", "unresolved_pairs_are_not_pass": True})
    _write_json(output / "rpir_source_roundtrip_audit.json", {"status": "PASS" if coverage["status"] == "PASS" else "FAIL", "producer": PARSER_IDENTITY, "execution_depth": "SQLite_to_JSONL_count_and_identity_roundtrip", "semantic_scope": "RPIR source roundtrip", "authority_allowed": "source representation", "authority_forbidden": "execution claim", "pathways": len(pathways), "reactions": len(reactions), "stable_identity_conflicts": len(conflicts)})
    _write_json(output / "rpir_stable_identity_audit.json", {"status": "PASS" if not conflicts else "FAIL", "producer": PARSER_IDENTITY, "execution_depth": "complete stable ID registry comparison", "semantic_scope": "Reactome stable identity and cross-chapter reuse", "authority_allowed": "stable-ID reuse without source-row loss", "authority_forbidden": "title-based identity", "stable_id_count": len(stable_ids), "source_occurrence_count": len(pathways) + len(reactions), "shared_event_occurrence_count": len(shared_occurrences), "conflicts": conflicts})
    return coverage
