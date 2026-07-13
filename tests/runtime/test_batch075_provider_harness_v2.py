from __future__ import annotations

import json
from pathlib import Path

from controllergate.core.evidence import hash_record, sha256_file
from controllergate.intake import admission_executor
from controllergate.runtime.duplicate_environment_factory import duplicate_environment_specs
from controllergate.runtime.provider_build_copy import create_read_only_execution_view, create_writable_build_copy, tree_identity
from controllergate.runtime.provider_store_verifier import build_provider_lock, next_provider_lock_version, seal_and_verify_provider_store
from controllergate.runtime.provider_workspace import candidate_key, plan_provider_workspace
from controllergate.runtime.python_provider_strategy import classify_python_source_layout, provider_strategy
from controllergate.runtime.target_dependency_analysis import analyze_target_dependencies


def _project(tmp_path: Path, *, buildable: bool = True) -> Path:
    source = tmp_path / "source"
    target = source / "tests" / "test_api.py"
    package = source / "sample"
    target.parent.mkdir(parents=True)
    package.mkdir(parents=True)
    target.write_text("from fastapi.testclient import TestClient\n\ndef test_api():\n    assert TestClient\n", encoding="utf-8")
    (package / "__init__.py").write_text("VALUE = 1\n", encoding="utf-8")
    if buildable:
        (source / "pyproject.toml").write_text(
            "[build-system]\nrequires=['setuptools']\nbuild-backend='setuptools.build_meta'\n"
            "[project]\nname='sample'\nversion='0.0.0'\n"
            "[project.optional-dependencies]\nserver=['fastapi>=0.110']\ndev=['pytest>=8','httpx>=0.27']\ndocs=['sphinx']\n",
            encoding="utf-8",
        )
    else:
        (source / "runner.py").write_text("VALUE = 1\n", encoding="utf-8")
        (source / "pyproject.toml").write_text("[tool.pytest.ini_options]\naddopts='-q'\n", encoding="utf-8")
        (source / "requirements.txt").write_text("pytest>=8\n", encoding="utf-8")
    return source


def test_short_workspace_key_and_windows_path_preflight(tmp_path: Path, monkeypatch) -> None:
    candidate_id = "prospective_" + "very_long_candidate_id_" * 20
    key = candidate_key(candidate_id, "a" * 40)
    assert len(key) == 12 and all(value in "0123456789abcdef" for value in key)
    monkeypatch.setenv("CONTROLLERGATE_SHORT_RUNTIME_ROOT", str(tmp_path / "r"))
    plan = plan_provider_workspace(tmp_path / ("long" * 80), candidate_id, "a" * 40)
    assert plan.relocated and plan.effective_projected_maximum_path_length <= plan.path_limit
    assert candidate_id not in plan.candidate_root and Path(plan.candidate_root).name == key


def test_target_informed_cognicore_style_server_and_dev_extras(tmp_path: Path) -> None:
    source = _project(tmp_path)
    analysis = analyze_target_dependencies(source, "tests/test_api.py::test_api")
    assert analysis["selected_extras"] == ["dev", "server"]
    assert {item["extra"] for item in analysis["rejected_extras"]} == {"docs"}
    assert "fastapi" in analysis["normalized_imports"]


def test_buildable_and_source_on_pythonpath_strategies(tmp_path: Path) -> None:
    buildable = _project(tmp_path / "a")
    source_only = _project(tmp_path / "b", buildable=False)
    assert classify_python_source_layout(buildable)["classification"] == "buildable_python_package"
    assert classify_python_source_layout(source_only)["classification"] == "source_on_pythonpath"
    analysis = analyze_target_dependencies(source_only, "tests/test_api.py::test_api")
    selected = provider_strategy(source_only, "tests/test_api.py::test_api", analysis)
    assert selected["strategy"] == "source_on_pythonpath"
    assert selected["project_wheel_allowed"] is False


def test_writable_build_copy_preserves_read_only_source_identity(tmp_path: Path) -> None:
    source = _project(tmp_path)
    before = tree_identity(source)
    record = create_writable_build_copy(source, tmp_path / "build")
    (tmp_path / "build" / "sample.egg-info").mkdir()
    assert record["status"] == "PASS" and record["metadata_outside_source"]
    assert tree_identity(source) == before
    assert not (source / "sample.egg-info").exists()


def test_read_only_execution_view_preserves_content_and_supplies_overlay_mountpoint(tmp_path: Path) -> None:
    source = _project(tmp_path)
    record = create_read_only_execution_view(source, tmp_path / "run")
    assert record["status"] == "PASS" and record["source_immutable"]
    assert Path(record["ephemeral_mountpoints"][0]).is_dir()
    assert tree_identity(source) == tree_identity(Path(record["execution_view"]))


def test_provider_lock_is_sealed_before_execution_and_versioned(tmp_path: Path) -> None:
    wheelhouse = tmp_path / "whl"
    wheelhouse.mkdir()
    wheel = wheelhouse / "sample-0.0.0-py3-none-any.whl"
    wheel.write_bytes(b"synthetic-wheel-provider-lock-fixture")
    lock = build_provider_lock(wheelhouse, version=1, dependency_analysis={"selected_extras": [], "requirement_files": []}, strategy={"strategy": "build_project_wheel"})
    verification = seal_and_verify_provider_store(wheelhouse, lock)
    assert verification["status"] == "PASS" and verification["expected_hashes_recorded_before_execution"]
    assert json.loads(Path(verification["provider_lock_path"]).read_text(encoding="utf-8"))["artifacts"][0]["expected_sha256"] == sha256_file(wheel)
    retry = next_provider_lock_version(lock, "declared-extra:server")
    assert retry["provider_lock_version"] == 2 and retry["previous_store_mutated"] is False and retry["fresh_environments_required"]


def test_duplicate_environments_share_exact_store_and_source_mode(tmp_path: Path) -> None:
    specs = duplicate_environment_specs(tmp_path / "src", tmp_path / "whl", "tests/test_x.py::test_x", "f" * 64, {"strategy": "source_on_pythonpath"})
    assert [item["environment"] for item in specs] == ["env1", "env2"]
    assert len({item["provider_store"] for item in specs}) == len({item["provider_lock_hash"] for item in specs}) == 1
    assert all(item["PYTHONPATH"] == "/source" and item["network"] == "none" for item in specs)
    assert all(item["HOME"] == "/tmp/home" and "/source/.pytest_tmp_runtime" in item["ephemeral_write_overlays"] for item in specs)
    assert admission_executor.TARGET_REPLAY_TIMEOUT_SECONDS == 180


def test_amds_arm_invokes_canonical_loop_and_fixed_arm_uses_same_facts(tmp_path: Path, monkeypatch) -> None:
    source = tmp_path / "src"
    target = source / "tests" / "test_x.py"
    target.parent.mkdir(parents=True)
    target.write_text("def test_x():\n    assert False\n", encoding="utf-8")
    wheelhouse = tmp_path / "whl"
    wheelhouse.mkdir()
    wheel = wheelhouse / "pytest-8.0.0-py3-none-any.whl"
    wheel.write_bytes(b"fixture")
    called = {"value": False}
    def canonical(_board, _probes, executor_factory, **kwargs):
        called["value"] = True
        observations = []
        for probe_id in ("provider_hash_recheck", "target_ast_recheck", "failure_signature_recheck"):
            observations.append(executor_factory({"probe_id": probe_id})())
        return {"status": "PASS", "observations": observations, "posterior_updates": [{"probe_id": item["probe_id"], "entropy_before": 0.0, "entropy_after": 0.0} for item in observations], "registry_versions": [{"generation": 1}], "backtracking_trace": [], "stop_decision": {"stop": True}}
    monkeypatch.setattr(admission_executor, "run_amds_active_loop", canonical)
    context = {
        "candidate_manifest": {"candidate_id": "candidate", "candidate_sha": "a" * 40, "native_target_paths": ["tests/test_x.py::test_x"], "workspace_root": str(tmp_path / "runtime"), "frame_hash": "b" * 64, "arm_output_root": str(tmp_path / "arm")},
        "source_root": str(source),
        "provider_closure": {"wheelhouse": str(wheelhouse), "artifacts": [{"filename": wheel.name, "sha256": sha256_file(wheel)}]},
        "duplicate_replay": {"duplicate_failure": True, "capsules": []},
        "amds_board": {"board_hash": hash_record({"fixture": True})},
    }
    active = admission_executor.intake_amds_arm(context, "arm_amds_active_memory_disabled")["context_updates"]["diagnostic_arms"]["amds_active_memory_disabled"]
    fixed = admission_executor.intake_amds_arm(context, "arm_fixed_legal_order_memory_disabled")["context_updates"]["diagnostic_arms"]["fixed_legal_order_memory_disabled"]
    assert called["value"] and active["canonical_run_amds_active_loop"]
    assert fixed["canonical_run_amds_active_loop"] is False
    assert {item["probe"] for item in active["observations"]} == {item["probe"] for item in fixed["observations"]}
