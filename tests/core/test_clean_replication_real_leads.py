from __future__ import annotations

import json
import subprocess
from pathlib import Path

from controllergate.experiments.replication_batch import run_replication_batch
from scripts.audit_post_v2_37_hardening_and_batch002 import audit_real_acquisition_records


def _run(command: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, cwd=str(cwd), text=True, capture_output=True, check=True)


def _local_git_repo(tmp_path: Path) -> tuple[Path, str]:
    repo = tmp_path / "source_repo"
    test_dir = repo / "tests"
    test_dir.mkdir(parents=True)
    (repo / "pyproject.toml").write_text("[project]\nname = \"local-lead\"\nversion = \"0.0.0\"\n", encoding="utf-8", newline="\n")
    (test_dir / "test_sample.py").write_text("def test_sample():\n    assert True\n", encoding="utf-8", newline="\n")
    _run(["git", "init"], repo)
    _run(["git", "add", "."], repo)
    _run(["git", "-c", "user.email=test@example.invalid", "-c", "user.name=Test User", "commit", "-m", "seed"], repo)
    sha = _run(["git", "rev-parse", "HEAD"], repo).stdout.strip()
    return repo, sha


def _lead_pool(tmp_path: Path, leads: list[dict[str, object]]) -> Path:
    path = tmp_path / "lead_pool.json"
    path.write_text(json.dumps({"leads": leads}, indent=2), encoding="utf-8")
    return path


def test_non_empty_native_lead_pool_triggers_clone_checkout_and_replay(tmp_path):
    repo, sha = _local_git_repo(tmp_path)
    lead_pool = _lead_pool(
        tmp_path,
        [
            {
                "allowed_candidate_class": "native",
                "commit_hint": sha,
                "expected_failure_hint": None,
                "issue_number": None,
                "issue_url": None,
                "lead_id": "local_native_lead",
                "lead_type": "commit_hint",
                "notes": "lead only, not proof",
                "repo": "local/repo",
                "repo_url": repo.resolve().as_uri(),
                "test_path_hint": "tests/test_sample.py",
            }
        ],
    )

    result = run_replication_batch(
        {
            "candidate_source_mode": "mixed",
            "lead_pool_path": str(lead_pool),
            "runtime_workspace_root": str(tmp_path / "runtime"),
            "max_repos_attempted": 1,
            "max_candidate_or_issue_leads_attempted": 1,
            "full_scoring": False,
        }
    )

    attempt = result["metadata_probe_attempts"][0]
    assert attempt["lead_id"] == "local_native_lead"
    assert attempt["git_clone_attempted"] is True
    assert attempt["commit_resolved"] is True
    assert attempt["checkout_attempted"] is True
    assert attempt["target_test_present"] is True
    assert attempt["environment_file_present"] is True
    assert attempt["collection_attempted"] is True
    assert attempt["failure_replay_attempted"] is True
    assert result["candidate_verification_attempts"][0]["lead_id"] == "local_native_lead"
    assert result["issue_derived_attempts"][0]["blocker"] == "issue_derived_no_safe_leads"


def test_placeholder_metadata_and_issue_sources_fail_audit():
    errors = audit_real_acquisition_records(
        {"leads": [{"lead_id": "real", "lead_type": "commit_hint", "allowed_candidate_class": "native"}]},
        [{"repo": "offline_local_metadata_lead_pool", "checkout_attempted": False, "blocker": "metadata_probe_no_verified_candidates"}],
        [{"issue_lead": "offline_local_issue_lead_pool", "blocker": "issue_derived_no_verified_candidates"}],
        [{"mode": "metadata_probe"}],
        {"exact_blocker": "clean_replication_batch_002_no_verified_candidates"},
    )

    assert any("placeholder" in error for error in errors)
    assert any("real lead_id" in error for error in errors)


def test_audit_fails_checkout_false_for_all_leads_without_specific_blocker():
    errors = audit_real_acquisition_records(
        {"leads": [{"lead_id": "real", "lead_type": "commit_hint", "allowed_candidate_class": "native"}]},
        [{"lead_id": "real", "git_clone_attempted": True, "git_clone_status": "PASS", "checkout_attempted": False, "blocker": None}],
        [{"blocker": "issue_derived_no_safe_leads"}],
        [{"mode": "metadata_probe", "lead_id": "real"}],
        {"exact_blocker": "clean_replication_batch_002_no_verified_candidates"},
    )

    assert "metadata_probe clone passed but no checkout was attempted" in errors
    assert "metadata_probe checkout false for every lead without specific blockers" in errors


def test_forbidden_py_bugger_lead_is_rejected(tmp_path):
    lead_pool = _lead_pool(
        tmp_path,
        [
            {
                "allowed_candidate_class": "native",
                "commit_hint": "0" * 40,
                "lead_id": "py_bugger_issue_65",
                "lead_type": "commit_hint",
                "repo": "forbidden/repo",
                "repo_url": "https://example.invalid/repo.git",
                "test_path_hint": "tests/test_repro.py",
            }
        ],
    )

    result = run_replication_batch(
        {
            "candidate_source_mode": "metadata_probe",
            "lead_pool_path": str(lead_pool),
            "runtime_workspace_root": str(tmp_path / "runtime"),
            "max_repos_attempted": 1,
            "max_candidate_or_issue_leads_attempted": 1,
            "full_scoring": False,
        }
    )

    assert result["metadata_probe_attempts"][0]["blocker"] == "forbidden_py_bugger_issue_65_lead"
    assert result["metadata_probe_attempts"][0]["git_clone_attempted"] is False
