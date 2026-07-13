from __future__ import annotations

from pathlib import Path

import pytest

from controllergate.execution.ci_native_result_guard import audit_guard, require_absent_and_create


def test_fresh_result_guard_creates_and_audits(tmp_path: Path) -> None:
    repo = Path(__file__).resolve().parents[2]
    output = tmp_path / "batch082"
    record = require_absent_and_create(output, repo_root=repo,
        engine_path=repo / "controllergate/engine.py",
        candidate_manifest=repo / "configs/batch082_candidate_frame.json",
        workflow_path=repo / ".github/workflows/post_v2_37_hardening_batch081_execution_constitution_provider_incident_pilot.yml")
    assert audit_guard(record)["status"] == "PASS"


def test_precommitted_result_is_rejected(tmp_path: Path) -> None:
    repo = Path(__file__).resolve().parents[2]
    output = tmp_path / "batch082"; output.mkdir()
    with pytest.raises(RuntimeError, match="precommitted"):
        require_absent_and_create(output, repo_root=repo,
            engine_path=repo / "controllergate/engine.py",
            candidate_manifest=repo / "configs/batch082_candidate_frame.json",
            workflow_path=repo / ".github/workflows/post_v2_37_hardening_batch081_execution_constitution_provider_incident_pilot.yml")

