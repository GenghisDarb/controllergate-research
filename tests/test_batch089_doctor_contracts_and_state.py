from __future__ import annotations

import json
from pathlib import Path

from controllergate.product.deep_doctor import deep_doctor
from controllergate.state.database import connect, initialize
from controllergate.state.schema import SCHEMA_VERSION, TABLES


def test_deep_doctor_reports_syntax_and_reachability(tmp_path: Path) -> None:
    package = tmp_path / "controllergate" / "state"; package.mkdir(parents=True)
    (package / "authority.py").write_text("def authoritative():\n    return True\n", encoding="utf-8")
    tests = tmp_path / "tests"; tests.mkdir(); (tests / "test_authority.py").write_text("def test_it():\n    assert True\n", encoding="utf-8")
    report = deep_doctor(tmp_path)
    assert report["status"] == "PASS"
    assert report["finding_classes"] == ["OBSERVED_FACT", "INFERRED_RISK", "RECOMMENDATION"]
    assert report["report_hash"]


def test_schema_v5_authority_tables_survive_batch090_migration(tmp_path: Path) -> None:
    connection = connect(tmp_path / "state.sqlite3"); initialize(connection)
    version = connection.execute("SELECT MAX(version) FROM schema_migrations").fetchone()[0]
    tables = {row[0] for row in connection.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    connection.close()
    assert version == SCHEMA_VERSION == 6
    assert set(TABLES) <= tables
    assert {"reaction_contracts", "reaction_executions", "evidence_facts", "repair_license_tokens"} <= tables


def test_batch089_contracts_are_hash_bound_and_reconciled() -> None:
    repo = Path(__file__).resolve().parents[1]
    composite = json.loads((repo / "configs" / "batch089_composite_prompt_contract.json").read_text(encoding="utf-8"))
    requirements = [json.loads(line) for line in (repo / "configs" / "batch089_isomorphism_requirements.jsonl").read_text(encoding="utf-8").splitlines()]
    sources = json.loads((repo / "configs" / "batch089_source_document_registry.json").read_text(encoding="utf-8"))
    assert len(composite["prompt_ids"]) == len(composite["sentinels"]) == 3
    assert composite["unique_requirement_count"] == len(requirements) == 78
    assert sources["supplied_document_count"] == 29 and sources["unique_document_count"] == 28


def test_batch089_claim_boundary_does_not_overclaim() -> None:
    repo = Path(__file__).resolve().parents[1]
    path = repo / "outputs" / "post_v2_37_hardening_batch089_full_isomorphism_reaction_complete_vertical_closure" / "batch089_claim_boundary.json"
    value = json.loads(path.read_text(encoding="utf-8"))
    assert value["current_protocol"] == "v2.19"
    assert value["issue_derived_repair_count"] == 6 and value["native_external_repair_count"] == 4
    assert value["full_scoring"] == "NOT_RUN/disallowed"
    assert value["self_maintaining_software"] == "false/not_demonstrated"
