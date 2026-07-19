from __future__ import annotations

import copy
import json
from pathlib import Path

from controllergate.governance.master_completion_ledger import REQUIRED_GOALS, validate_ledger


ROOT = Path(__file__).resolve().parents[1]
LEDGER = ROOT / "configs" / "controllergate_master_completion_ledger_v2.json"


def load() -> dict:
    return json.loads(LEDGER.read_text())


def test_master_completion_ledger_passes_and_has_all_goals() -> None:
    ledger = load()
    assert [goal["goal_id"] for goal in ledger["goals"]] == list(REQUIRED_GOALS)
    assert validate_ledger(ledger, ROOT)["status"] == "PASS"


def test_goal_removal_is_blocked() -> None:
    ledger = load()
    ledger["goals"].pop()
    assert validate_ledger(ledger, ROOT, verify_files=False)["status"] == "BLOCK"


def test_complete_evidence_removal_and_document_only_completion_are_blocked() -> None:
    ledger = load()
    first = ledger["goals"][0]
    first["current_evidence"] = []
    first["evidence_hashes"] = {}
    assert validate_ledger(ledger, ROOT, verify_files=False)["status"] == "BLOCK"
    ledger = load()
    ledger["goals"][0]["current_evidence"] = ["docs/CURRENT_CONTROLLERGATE_HANDOFF.md"]
    ledger["goals"][0]["evidence_hashes"] = {"docs/CURRENT_CONTROLLERGATE_HANDOFF.md": "0" * 64}
    assert validate_ledger(ledger, ROOT, verify_files=False)["status"] == "BLOCK"


def test_blocker_cannot_be_silently_removed() -> None:
    ledger = load()
    blocked = next(goal for goal in ledger["goals"] if goal["status"] == "NOT_STARTED")
    blocked["active_blockers"] = []
    assert validate_ledger(ledger, ROOT, verify_files=False)["status"] == "BLOCK"
