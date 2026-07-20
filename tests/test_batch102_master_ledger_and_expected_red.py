from __future__ import annotations

import json
from pathlib import Path

from controllergate.governance.master_completion_ledger import REQUIRED_GOALS, validate_ledger


ROOT = Path(__file__).resolve().parents[1]
LEDGER = ROOT / "configs" / "controllergate_master_completion_ledger_v2.json"
OUT = ROOT / "outputs" / "post_v2_37_hardening_batch102_fresh_exact_counterfactual_execution_necessity_sufficiency_ownership_closure"


def test_batch102_goals_are_append_only_and_validate() -> None:
    ledger = json.loads(LEDGER.read_text(encoding="utf-8"))
    assert [row["goal_id"] for row in ledger["goals"]] == list(REQUIRED_GOALS)
    assert validate_ledger(ledger, ROOT)["status"] == "PASS"
    by_id = {row["goal_id"]: row for row in ledger["goals"]}
    assert by_id["CG-GOAL-022-OFFICIAL-BATCH101-INGEST"]["status"] == "COMPLETE"
    assert by_id["CG-GOAL-023-FRESH-CANDIDATE-EXECUTION-ATTESTATION"]["status"] == "IN_PROGRESS"
    assert by_id["CG-GOAL-024-NECESSITY-SUFFICIENCY-ALTERNATIVE-EXCLUSION"]["status"] == "IN_PROGRESS"
    assert by_id["CG-GOAL-025-REAL-ARCHITECTURE-ARM-EVALUATION"]["status"] == "IN_PROGRESS"


def test_batch102_execution_origin_corrections_are_explicit() -> None:
    ledger = json.loads(LEDGER.read_text(encoding="utf-8"))
    corrections = [
        row for row in ledger["supersession_receipts"]
        if row["transition_id"].endswith("execution-origin-correction")
    ]
    assert len(corrections) == 5
    assert all("fresh execution substitution" in row["authority_forbidden"] for row in corrections)


def test_batch102_expected_red_is_complete_and_sealed() -> None:
    result = json.loads((OUT / "batch102_pre_fresh_execution_expected_failure.json").read_text(encoding="utf-8"))
    assert result["status"] == "BATCH102_PRE_FRESH_EXECUTION_FAIL_EXPECTED"
    assert result["finding_count"] == 45
    assert len(result["findings"]) == 45
    assert len({row["finding_id"] for row in result["findings"]}) == 45
