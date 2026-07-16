from __future__ import annotations

import json
from pathlib import Path

from controllergate.amds.fresh_cohort import ROLE_NAMES, _expand_argv, _path_manifest


ROOT = Path(__file__).resolve().parents[1]


def test_frozen_cohort_has_exact_eight_without_substitution() -> None:
    config = json.loads((ROOT / "configs/batch094_fresh_cohort_acquisition.json").read_text(encoding="utf-8"))
    assert [row["candidate_id"] for row in config["episodes"]] == [
        "darker_issue_112_relative_git_dir",
        "py_bugger_issue_65",
        "cloudpickle_507_py313_typevar_distutils",
        "freezegun_547_py313_datetimes_assertion",
        "audioread_144_py313_aifc_removed",
        "pytest_13480_wdefault_unraisable_threadexception",
        "incident_openbb_7585_modular_openapi_reproducer",
        "incident_poetry_10974_init_duplicate_name",
    ]
    assert config["replacement_after_outcome_allowed"] is False
    assert config["minimum_eligible_episodes"] == 8


def test_every_episode_has_exact_source_and_command_identity() -> None:
    config = json.loads((ROOT / "configs/batch094_fresh_cohort_acquisition.json").read_text(encoding="utf-8"))
    for row in config["episodes"]:
        assert len(row["source_commit"]) == 40
        assert all(character in "0123456789abcdef" for character in row["source_commit"])
        assert row["repository"].startswith("https://github.com/")
        assert row["target_argv"]
        assert row["install_argv"]
        assert row["target_paths"]


def test_forbidden_outcome_evidence_is_declared_and_not_in_episode_contracts() -> None:
    config = json.loads((ROOT / "configs/batch094_fresh_cohort_acquisition.json").read_text(encoding="utf-8"))
    assert "terminal_class" in config["forbidden_inputs"]
    assert "post_repair_output" in config["forbidden_inputs"]
    for row in config["episodes"]:
        assert not ({"terminal_class", "gold_patch", "repair_outcome", "future_revision"} & set(row))


def test_role_contract_is_ten_semantically_distinct_roles() -> None:
    assert len(ROLE_NAMES) == 10
    assert len(set(ROLE_NAMES)) == 10


def test_command_template_expansion_uses_fresh_provider(tmp_path: Path) -> None:
    venv = tmp_path / "provider"
    expanded = _expand_argv(["{python}", "-m", "pytest"], venv=venv)
    assert expanded[0].startswith(str(venv))
    assert expanded[1:] == ["-m", "pytest"]


def test_pytest_source_build_has_decision_time_version_identity() -> None:
    config = json.loads((ROOT / "configs/batch094_fresh_cohort_acquisition.json").read_text(encoding="utf-8"))
    pytest_spec = next(row for row in config["episodes"] if row["candidate_id"].startswith("pytest_13480"))
    assert pytest_spec["install_environment"] == {"SETUPTOOLS_SCM_PRETEND_VERSION_FOR_PYTEST": "8.4.0"}


def test_missing_target_path_blocks_tree_capsule(tmp_path: Path) -> None:
    rows, complete = _path_manifest(tmp_path, ["missing.py"])
    assert complete is False
    assert rows == [{"path": "missing.py", "kind": "missing", "sha256": None}]
