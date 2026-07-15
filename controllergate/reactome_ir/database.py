from __future__ import annotations

import sqlite3
from pathlib import Path


DDL = """
CREATE TABLE reactome_source_documents(source_document_id TEXT PRIMARY KEY, filename TEXT NOT NULL, sha256 TEXT NOT NULL UNIQUE, size INTEGER NOT NULL, page_count INTEGER NOT NULL, reactome_release INTEGER, chapter_title TEXT NOT NULL, expected_pathway_count INTEGER NOT NULL, observed_pathway_count INTEGER NOT NULL, expected_reaction_count INTEGER NOT NULL, observed_reaction_count INTEGER NOT NULL, parser_identity TEXT NOT NULL, parser_version TEXT NOT NULL, structured_export_identity TEXT, parse_warnings TEXT NOT NULL, parse_failures TEXT NOT NULL, review_status TEXT NOT NULL);
CREATE TABLE reactome_pathways(occurrence_id TEXT PRIMARY KEY, stable_id TEXT NOT NULL, chapter TEXT NOT NULL, title TEXT NOT NULL, hierarchy TEXT NOT NULL, page_number INTEGER NOT NULL, record_json TEXT NOT NULL);
CREATE TABLE reactome_reactions(occurrence_id TEXT PRIMARY KEY, stable_id TEXT NOT NULL, chapter TEXT NOT NULL, title TEXT NOT NULL, event_type TEXT NOT NULL, evidence_maturity TEXT NOT NULL, page_number INTEGER NOT NULL, record_json TEXT NOT NULL);
CREATE INDEX reactome_pathways_stable_id ON reactome_pathways(stable_id);
CREATE INDEX reactome_reactions_stable_id ON reactome_reactions(stable_id);
CREATE TABLE reactome_entities(entity_id TEXT PRIMARY KEY, occurrence_id TEXT NOT NULL, stable_id TEXT NOT NULL, role TEXT NOT NULL, label TEXT NOT NULL, record_json TEXT NOT NULL);
CREATE TABLE reactome_entity_sets(entity_set_id TEXT PRIMARY KEY, stable_id TEXT NOT NULL, record_json TEXT NOT NULL);
CREATE TABLE reactome_complexes(complex_id TEXT PRIMARY KEY, stable_id TEXT NOT NULL, record_json TEXT NOT NULL);
CREATE TABLE reactome_compartments(compartment_id TEXT PRIMARY KEY, label TEXT NOT NULL UNIQUE, record_json TEXT NOT NULL);
CREATE TABLE reactome_modifications(modification_id TEXT PRIMARY KEY, stable_id TEXT NOT NULL, record_json TEXT NOT NULL);
CREATE TABLE reactome_catalysts(catalyst_id TEXT PRIMARY KEY, stable_id TEXT NOT NULL, record_json TEXT NOT NULL);
CREATE TABLE reactome_regulations(regulation_id TEXT PRIMARY KEY, stable_id TEXT NOT NULL, regulation_type TEXT NOT NULL, record_json TEXT NOT NULL);
CREATE TABLE reactome_requirements(requirement_id TEXT PRIMARY KEY, stable_id TEXT NOT NULL, record_json TEXT NOT NULL);
CREATE TABLE reactome_preceding_following_edges(edge_id TEXT PRIMARY KEY, occurrence_id TEXT NOT NULL, stable_id TEXT NOT NULL, direction TEXT NOT NULL, target_title TEXT NOT NULL, record_json TEXT NOT NULL);
CREATE TABLE reactome_orthology_edges(edge_id TEXT PRIMARY KEY, occurrence_id TEXT NOT NULL, stable_id TEXT NOT NULL, source_description TEXT NOT NULL, record_json TEXT NOT NULL);
CREATE TABLE reactome_evidence_records(evidence_id TEXT PRIMARY KEY, occurrence_id TEXT NOT NULL, stable_id TEXT NOT NULL, maturity TEXT NOT NULL, record_json TEXT NOT NULL);
CREATE TABLE reactome_literature_references(reference_id TEXT PRIMARY KEY, occurrence_id TEXT NOT NULL, stable_id TEXT NOT NULL, source_text_sha256 TEXT NOT NULL, record_json TEXT NOT NULL);
CREATE TABLE reactome_editions(edition_id TEXT PRIMARY KEY, occurrence_id TEXT NOT NULL, stable_id TEXT NOT NULL, role TEXT NOT NULL, date TEXT NOT NULL, contributor TEXT NOT NULL, record_json TEXT NOT NULL);
CREATE TABLE reactome_disease_annotations(annotation_id TEXT PRIMARY KEY, occurrence_id TEXT NOT NULL, stable_id TEXT NOT NULL, record_json TEXT NOT NULL);
CREATE TABLE reactome_normal_variant_pairs(pair_id TEXT PRIMARY KEY, occurrence_id TEXT NOT NULL, variant_stable_id TEXT NOT NULL, normal_stable_id TEXT, status TEXT NOT NULL, record_json TEXT NOT NULL);
CREATE TABLE reactome_translation_candidates(occurrence_id TEXT PRIMARY KEY, stable_id TEXT NOT NULL, translation_state TEXT NOT NULL, record_json TEXT NOT NULL);
CREATE TABLE reactome_translation_decisions(occurrence_id TEXT PRIMARY KEY, stable_id TEXT NOT NULL, decision TEXT NOT NULL, authority_allowed INTEGER NOT NULL, record_json TEXT NOT NULL);
"""


def create_database(path: str | Path) -> sqlite3.Connection:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(target)
    connection.execute("PRAGMA journal_mode=DELETE")
    connection.executescript(DDL)
    return connection
