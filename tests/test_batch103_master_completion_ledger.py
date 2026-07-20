import json
from pathlib import Path

from controllergate.governance.master_completion_ledger import REQUIRED_GOALS, validate_ledger


ROOT = Path(__file__).resolve().parents[1]
LEDGER = ROOT / "configs/controllergate_master_completion_ledger_v2.json"


def test_batch103_goals_are_append_only_and_conservative():
    ledger = json.loads(LEDGER.read_text(encoding="utf-8"))
    assert [row["goal_id"] for row in ledger["goals"]] == list(REQUIRED_GOALS)
    assert validate_ledger(ledger, ROOT)["status"] == "PASS"
    goals = {row["goal_id"]: row for row in ledger["goals"]}
    assert goals["CG-GOAL-026-OFFICIAL-BATCH102-INGEST"]["status"] == "COMPLETE"
    assert goals["CG-GOAL-027-CANONICAL-ISOMORPHISM-RECONCILIATION"]["status"] == "IN_PROGRESS"
    assert goals["CG-GOAL-028-REACTOME-RPIR-SOURCE-GROUNDING"]["status"] == "IN_PROGRESS"
    assert goals["CG-GOAL-029-REACTOME-EXECUTABLE-MAINTENANCE-MAPPING"]["status"] == "IN_PROGRESS"
    assert goals["CG-GOAL-030-REACTOME-CAUSAL-PLANNING-GAIN"]["status"] == "IN_PROGRESS"
    assert goals["CG-GOAL-031-REACTOME-CROSS-CANDIDATE-GENERALIZATION"]["status"] == "NOT_STARTED"
    assert goals["CG-GOAL-032-ISOMORPHIC-ARCHITECTURE-EXTERNAL-VALIDATION"]["status"] == "NOT_STARTED"
    assert goals["CG-GOAL-033-REACTOME-PROSPECTIVE-VALIDATION"]["status"] == "NOT_STARTED"


def test_batch103_goal_deletion_or_blocker_deletion_fails():
    ledger = json.loads(LEDGER.read_text(encoding="utf-8"))
    ledger["goals"] = ledger["goals"][:-1]
    assert validate_ledger(ledger, ROOT, verify_files=False)["status"] == "BLOCK"
    ledger = json.loads(LEDGER.read_text(encoding="utf-8"))
    ledger["goals"][-1]["active_blockers"] = []
    assert validate_ledger(ledger, ROOT, verify_files=False)["status"] == "BLOCK"
