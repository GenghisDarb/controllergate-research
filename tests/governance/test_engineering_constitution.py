from __future__ import annotations

import json
from pathlib import Path

from controllergate.governance.engineering_constitution import build_laws, deferred_research, validate_law


ROOT = Path(__file__).resolve().parents[2]


def test_constitution_positive():
    laws = build_laws("0" * 40)
    assert len(laws) == 40
    assert all(not validate_law(law, ROOT) for law in laws)


def test_constitution_rejects_invalid_law():
    law = build_laws("0" * 40)[0]
    law["owner_module"] = "missing.owner.module"
    assert "verification_hash_invalid" in validate_law(law, ROOT)
    assert "owner_module_missing" in validate_law(law, ROOT)


def test_documentation_only_fake_implementation_rejected():
    law = build_laws("0" * 40)[0]
    law["owner_module"] = "docs.CONTROLLERGATE_ENGINEERING_CONSTITUTION"
    assert "owner_module_missing" in validate_law(law, ROOT)


def test_deferred_research_is_nonblocking():
    record = deferred_research("0" * 40)
    assert record["status"] == "DEFERRED_NAMED_BATCH"
    assert record["classification"] == "NONBLOCKING_RESEARCH"
    assert record["next_action"] == "EXPERIMENT_MESOSCOPIC_CHAOS_001"
