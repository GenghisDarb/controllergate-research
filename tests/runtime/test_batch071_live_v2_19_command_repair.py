from __future__ import annotations

import json
from pathlib import Path

from controllergate.core.command_authority_resolver import resolve_command_authority
from controllergate.core.command_equivalence import commands_equivalent, split_wrapper
from controllergate.core.command_role_classifier import classify_command
from controllergate.core.command_sources.tox_parser import parse_tox
from controllergate.core.command_target_alignment import narrow_to_target
from controllergate.core.patch_synthesis import synthesize_ordering_patch
from scripts.generate_batch071_live_v2_19_command_repair_continuation import summarize

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs/post_v2_37_hardening_batch071_live_v2_19_command_repair_continuation"


def test_tox_section_multiline_comments_and_conditions(tmp_path: Path) -> None:
    path = tmp_path / "tox.ini"
    path.write_text("""[testenv]\ncommands =\n    # 1. Auto-formatting\n    min: cp pyproject.toml .saved\n    python -m pytest tests\n    pre-commit run --all-files\n[testenv:lint]\ncommands = flake8\n""", encoding="utf-8")
    parsed = parse_tox(path); default = parsed["environments"][0]
    assert len(default["commands"]) == 3
    assert default["commands"][0]["condition"] == "min"
    assert default["commands"][0]["argv"][0] == "cp"
    assert "#" not in " ".join(item["raw"] for item in default["commands"])
    assert parsed["environments"][1]["environment_name"] == "lint"


def test_command_roles_reject_mutating_formatters_and_setup() -> None:
    assert classify_command(["black", "."]) == "formatter_mutating"
    assert classify_command(["black", "--check", "."]) == "formatter_check"
    assert classify_command(["pre-commit", "run"]) == "formatter_mutating"
    assert classify_command(["poetry", "install"]) == "environment_setup"
    assert classify_command(["python", "-m", "pytest", "tests"]) == "test_runner"


def test_pytest_equivalence_and_wrapper_split() -> None:
    assert commands_equivalent(["pytest", "tests/x.py"], ["python", "-m", "pytest", "tests/x.py"])
    assert commands_equivalent(["py.test", "tests/x.py"], ["python3", "-m", "pytest", "tests/x.py"])
    wrapper, inner = split_wrapper(["poetry", "run", "python", "-m", "pytest", "tests/x.py"])
    assert wrapper == ["poetry", "run"] and inner[:3] == ["python", "-m", "pytest"]


def test_bounded_target_narrowing_preserves_runner_and_flags() -> None:
    value = narrow_to_target(["python", "-m", "pytest", "tests", "--cov", "pkg"], "tests/test_x.py::test_x")
    assert value["transformed_command"] == ["python", "-m", "pytest", "tests/test_x.py::test_x", "--cov", "pkg"]
    assert value["forbidden_flags_added"] is False


def test_unique_target_command_eliminates_false_conflicts(tmp_path: Path) -> None:
    (tmp_path / "tox.ini").write_text("""[testenv]\ncommands =\n    min: cp pyproject.toml .saved\n    poetry lock\n    poetry run python -m pytest tests --cov pkg\n    pre-commit run --all-files\n""", encoding="utf-8")
    result = resolve_command_authority(tmp_path, "tests/test_x.py::test_x")
    assert result["status"] == "PASS"
    assert result["selected"]["exact_target"] == "tests/test_x.py::test_x"
    assert result["false_conflicts_eliminated"] == 3
    assert result["true_conflict_count"] == 0


def test_true_command_conflict_requires_inequivalent_targets(tmp_path: Path) -> None:
    (tmp_path / "tox.ini").write_text("""[testenv]\ncommands =\n    python -m pytest tests/a.py\n    python -m pytest integration/b.py\n""", encoding="utf-8")
    result = resolve_command_authority(tmp_path, "tests/x.py::test_x")
    assert result["status"] == "MANUAL_REVIEW"
    assert result["true_conflict_count"] >= 1


def test_live_reconciliation_and_checkpoint_invalidation() -> None:
    reconciliation = json.loads((OUT / "batch071_candidate_reconciliation.json").read_text(encoding="utf-8"))
    rebase = json.loads((OUT / "batch070_checkpoint_validity_audit_batch071.json").read_text(encoding="utf-8"))
    assert reconciliation["biface"] == "solution_guidance_contaminated_for_fresh_authoritative_repair"
    assert reconciliation["hipo_corrected_target"].endswith("test_read_source_with_context")
    assert reconciliation["connexion_target"] == "tests/test_utils.py::test_sort_routes"
    assert rebase["h70_manifest_trust_checkpoints_are_live_evidence"] is False


def test_live_execution_patch_and_count_gate_order() -> None:
    execution = json.loads((OUT / "batch071_live_candidate_execution.json").read_text(encoding="utf-8"))["results"]
    hipo, connexion = execution
    assert hipo["summary"]["source_acquisition"] == hipo["summary"]["environment"] == "PASS"
    assert hipo["summary"]["ownership"] == "test_expectation_fragility" and not hipo["summary"]["patch_generated"]
    assert connexion["summary"]["duplicate_collection_count"] == connexion["summary"]["prerepair_reproduction_count"] == 2
    assert connexion["summary"]["ownership"] == "source_owned_behavior_defect"
    assert connexion["summary"]["modified_files"] == ["connexion/utils.py"]
    assert connexion["summary"]["target_validation"] == connexion["summary"]["invariant_validation"] == 0
    assert connexion["summary"]["duplicate_replay"] == connexion["summary"]["count_gate"] == "PASS"


def test_patch_synthesis_is_candidate_agnostic_and_source_only(tmp_path: Path) -> None:
    source = tmp_path / "utils.py"
    source.write_text('''def sort_routes(routes, *, key=None):\n    class SortableRoute:\n        def __init__(self, path):\n            self.path = path\n        def __lt__(self, other):\n            return True\n    return sorted(routes, key=lambda r: SortableRoute(key(r) if key else r))\n''', encoding="utf-8")
    result = synthesize_ordering_patch(source, "sort_routes")
    assert result["status"] == "PASS"
    assert "specificity" in source.read_text(encoding="utf-8")


def test_live_amds_and_pilot_boundaries() -> None:
    amds = json.loads((OUT / "live_amds_evidence_batch071.json").read_text(encoding="utf-8"))
    pilot = json.loads((OUT / "batch071_prospective_amds_pilot.json").read_text(encoding="utf-8"))
    assert all(row["amds_probes"] == row["posterior_updates"] == row["semantic_verifications"] == 1 for row in amds["records"])
    assert all(row["backtracking_components"] >= 1 for row in amds["records"])
    assert amds["placeholder_hashes_used"] is False
    assert pilot["arms_operationally_separate"] and pilot["matched_budgets"]
    assert len({row["independent_output_namespace"] for row in pilot["rows"]}) == len(pilot["rows"])
    assert pilot["AMDS_PROSPECTIVE_EFFECTIVENESS"] == "NOT_ESTABLISHED"


def test_v2_19_depth_and_batch072_handoff() -> None:
    depth = json.loads((OUT / "v2_19_binding_depth_registry_batch071.json").read_text(encoding="utf-8"))
    handoff = json.loads((OUT / "batch072_cold_start_handoff.json").read_text(encoding="utf-8"))
    assert any(row["prior_v2_19_classification"] == "manifest_assertion_consumer_not_live_executor" for row in depth["records"])
    assert any(row["live_operation_executed"] for row in depth["records"])
    assert all(row["generalization_demonstrated"] is False for row in depth["records"])
    assert handoff["issue_derived_repair_count"] == 5
    assert handoff["primary_objective"] == "prospective AMDS and memory validation with fresh unrelated candidates"


def test_terminal_summary_tolerates_unresolved_optional_records() -> None:
    value = {"status": "BLOCK", "context": {"source_acquisition": None, "environment": None, "provider_closure": None, "command_authority": {"selected": None}, "rollback": None, "proof_ledger_update": None}}
    result = summarize(value)
    assert result["status"] == "BLOCK"
    assert result["command_authority_source"] is None
