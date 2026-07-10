from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "generate_batch069_multi_candidate_provider_command_probe.py"


def load_batch069_module():
    spec = importlib.util.spec_from_file_location("batch069_generator", SCRIPT)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_batch069_probe_contract_preserves_top5_order() -> None:
    module = load_batch069_module()
    contracts = module.candidate_contracts()
    assert [item["candidate_id"] for item in contracts] == module.TOP5_ORDER
    assert len(contracts) == 5


def test_batch069_command_boundary_does_not_guess_commands() -> None:
    module = load_batch069_module()
    contract = module.candidate_contracts()[1]
    result = module.command_boundary_for(contract, {"sample_test_files": ["tests/test_example.py"]}, "PASS")
    assert result["status"] == "BLOCK"
    assert result["command"] is None
    assert result["manual_guessed_commands_used"] is False
    assert result["issue_comment_fix_text_used"] is False
    assert result["command_boundary_status"] == "native_test_command_missing_under_decision_time_metadata"


def test_batch069_public_summary_preserves_no_repair_boundary() -> None:
    module = load_batch069_module()
    assert "not repair proof" in module.PUBLIC_SUMMARY
    assert "Full scoring remains NOT_RUN/disallowed" in module.PUBLIC_SUMMARY
    assert "Self-maintaining software remains false/not_demonstrated" in module.PUBLIC_SUMMARY


def test_batch069_artifact_identity_is_expected_batch068() -> None:
    module = load_batch069_module()
    assert module.EXPECTED_BATCH068["expected_size"] == 105081
    assert module.EXPECTED_BATCH068["expected_sha256"] == "f169aae0c3e145f5a4a0c410c8a2de8bee25e2d151a738b6fd2d9fe27c39565a"
