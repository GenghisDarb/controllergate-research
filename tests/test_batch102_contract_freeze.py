from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def load(name: str) -> list[dict]:
    return [json.loads(line) for line in (ROOT / "configs" / name).read_text(encoding="utf-8").splitlines() if line]


def test_batch102_contracts_are_frozen_before_execution() -> None:
    programs = load("batch102_candidate_counterfactual_programs_v4.jsonl")
    cells = load("batch102_counterfactual_cell_registry_v4.jsonl")
    assert len(programs) == 9
    assert len(cells) == 70
    assert len({row["cell_id"] for row in cells}) == len(cells)
    assert all(row["execution_epoch_required"] == "BATCH102_FRESH_OPERATION" for row in cells)
    assert all(row["fresh_broker_receipt_required"] is True for row in cells)
    assert all(row["truth_access"] == row["private_tld_access"] == row["patch_operations"] == 0 for row in cells)


def test_batch102_programs_cover_every_required_candidate_family() -> None:
    programs = load("batch102_candidate_counterfactual_programs_v4.jsonl")
    identifiers = {row["program_id"] for row in programs}
    for fragment in ("darker", "py-bugger", "distutils", "freezegun", "audioread", "pytest", "openbb", "poetry", "typevar"):
        assert any(fragment in value for value in identifiers)
    assert all(row["necessity_sufficiency_required_for_ownership"] for row in programs)
    assert all(row["alternative_exclusion_required_for_ownership"] for row in programs)
    by_id = {row["program_id"]: row for row in programs}
    assert by_id["batch100-darker-112-git-dir"]["required_source_commit"] == "bc751841439a02f5fd7277bbddb28190d4dcedd3"
    assert by_id["batch100-pytest-13480-warning-mode"]["required_source_commit"] == "80dfa2db8e6157bf706c2f2656ba0fd7bc13195a"
    assert by_id["batch100-openbb-7585-topology"]["required_secondary_source_commit"] == "901d6209e5738b0cbb42d48553c51fdc5f98bd7e"


def test_supersession_receipts_bind_old_and_new_contracts() -> None:
    rows = load("batch102_contract_supersession_registry_v1.jsonl")
    assert len(rows) == 4
    assert all(len(row["old_hash"]) == len(row["new_hash"]) == len(row["supersession_receipt"]) == 64 for row in rows)
    assert all(row["execution_mechanics_changed"] is True for row in rows)
    assert all(row["scientific_meaning_changed"] is False for row in rows)


def test_alternative_exclusion_contracts_do_not_predeclare_outcomes() -> None:
    rows = load("batch102_alternative_exclusion_programs_v1.jsonl")
    assert len(rows) == 9
    assert all(row["execution_required"] is True for row in rows)
    assert all("excluded" not in row for row in rows)
