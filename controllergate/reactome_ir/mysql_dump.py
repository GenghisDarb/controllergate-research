from __future__ import annotations

import gzip
import re
import sqlite3
from pathlib import Path
from typing import Iterable, Iterator


CORE_TABLES = frozenset(
    {
        "AbstractModifiedResidue", "BlackBoxEvent", "CandidateSet", "CandidateSet_2_hasCandidate",
        "CatalystActivity", "CatalystActivity_2_activeUnit", "Compartment", "Complex",
        "Complex_2_compartment", "Complex_2_hasComponent", "DatabaseObject", "EntitySet",
        "EntitySet_2_compartment", "EntitySet_2_hasMember", "EntityWithAccessionedSequence_2_hasModifiedResidue",
        "Event", "Event_2_authored", "Event_2_disease", "Event_2_inferredFrom",
        "Event_2_literatureReference", "Event_2_negativePrecedingEvent", "Event_2_precedingEvent",
        "Event_2_reviewed", "Event_2_revised", "Event_2_species", "FailedReaction",
        "FragmentDeletionModification", "FragmentInsertionModification", "FragmentModification",
        "FragmentReplacedModification", "InstanceEdit", "InstanceEdit_2_author", "NegativeRegulation",
        "Pathway", "Pathway_2_compartment", "Pathway_2_hasEvent", "Person", "PhysicalEntity",
        "PhysicalEntity_2_name", "PositiveRegulation", "Reaction", "ReactionlikeEvent",
        "ReactionlikeEvent_2_catalystActivity", "ReactionlikeEvent_2_compartment",
        "ReactionlikeEvent_2_input", "ReactionlikeEvent_2_output", "ReactionlikeEvent_2_reactionType",
        "ReactionlikeEvent_2_regulatedBy", "ReactionlikeEvent_2_requiredInputComponent", "Regulation",
        "StableIdentifier", "TranslationalModification",
    }
)


def _rows(statement: str) -> Iterator[list[str | None]]:
    start = statement.find(" VALUES ")
    if start < 0:
        return
    value_text = statement[start + 8 :].rstrip().rstrip(";")
    cursor = 0
    while cursor < len(value_text):
        while cursor < len(value_text) and value_text[cursor] != "(":
            cursor += 1
        if cursor >= len(value_text):
            return
        cursor += 1
        row: list[str | None] = []
        buffer: list[str] = []
        quoted = False
        while cursor < len(value_text):
            char = value_text[cursor]
            if quoted:
                if char == "\\" and cursor + 1 < len(value_text):
                    cursor += 1
                    escaped = value_text[cursor]
                    buffer.append({"n": "\n", "r": "\r", "t": "\t", "0": "\0", "b": "\b", "Z": "\x1a"}.get(escaped, escaped))
                    cursor += 1
                    continue
                if char == "'":
                    quoted = False
                    cursor += 1
                    continue
                buffer.append(char)
                cursor += 1
                continue
            if char == "'":
                quoted = True
                cursor += 1
                continue
            if char == ",":
                token = "".join(buffer).strip()
                row.append(None if token == "NULL" else token)
                buffer = []
                cursor += 1
                continue
            if char == ")":
                token = "".join(buffer).strip()
                row.append(None if token == "NULL" else token)
                cursor += 1
                yield row
                break
            buffer.append(char)
            cursor += 1


def extract_core_tables(source: str | Path, database: str | Path, *, tables: Iterable[str] = CORE_TABLES) -> dict[str, int]:
    """Extract the exact release tables needed by RPIR without running MySQL."""
    source = Path(source)
    database = Path(database)
    selected = frozenset(tables)
    if database.exists():
        database.unlink()
    database.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(database)
    connection.execute("PRAGMA journal_mode=OFF")
    connection.execute("PRAGMA synchronous=OFF")
    connection.execute("PRAGMA temp_store=MEMORY")
    columns: dict[str, list[str]] = {}
    active: str | None = None
    created: set[str] = set()
    counts: dict[str, int] = {}
    with gzip.open(source, "rt", encoding="utf-8", errors="replace", newline="") as stream:
        for line_number, line in enumerate(stream, 1):
            create = re.match(r"CREATE TABLE `([^`]+)`", line)
            if create:
                active = create.group(1)
                columns.setdefault(active, [])
                continue
            if active is not None:
                column = re.match(r"\s+`([^`]+)`\s+", line)
                if column:
                    columns[active].append(column.group(1))
                    continue
                if line.startswith(") ENGINE="):
                    active = None
                    continue
            if not line.startswith("INSERT INTO `"):
                continue
            match = re.match(r"INSERT INTO `([^`]+)`", line)
            if match is None or match.group(1) not in selected:
                continue
            table = match.group(1)
            names = columns.get(table, [])
            if not names:
                raise ValueError(f"missing table schema for {table}")
            if table not in created:
                connection.execute(f'CREATE TABLE "{table}" ({",".join(f"\"{name}\" TEXT" for name in names)})')
                created.add(table)
            rows = list(_rows(line))
            if any(len(row) != len(names) for row in rows):
                raise ValueError(f"column mismatch in {table} at dump line {line_number}")
            connection.executemany(f'INSERT INTO "{table}" VALUES ({",".join("?" for _ in names)})', rows)
            counts[table] = counts.get(table, 0) + len(rows)
            if line_number % 1000 == 0:
                connection.commit()
    connection.commit()
    for table in created:
        if "DB_ID" in columns[table]:
            connection.execute(f'CREATE INDEX "idx_{table}_dbid" ON "{table}"("DB_ID")')
    connection.execute('CREATE INDEX "idx_DatabaseObject_stable" ON "DatabaseObject"("stableIdentifier")')
    connection.execute('CREATE INDEX "idx_StableIdentifier_identifier" ON "StableIdentifier"("identifier")')
    connection.commit()
    connection.close()
    return dict(sorted(counts.items()))
