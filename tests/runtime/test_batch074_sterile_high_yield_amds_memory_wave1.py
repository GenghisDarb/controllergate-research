from __future__ import annotations

from datetime import datetime, timedelta, timezone
import json
from pathlib import Path

from controllergate.core.batch074_sterile_high_yield_wave1 import BATCH
from controllergate.core.command_authority_resolver import resolve_command_authority
from controllergate.core.evidence import hash_record, write_json_deterministic
from controllergate.intake.contamination_classifier import classify_contamination, sanitize_issue_record
from controllergate.intake.frame_freezer import freeze_frame
from controllergate.intake.target_resolver import resolve_target
from controllergate.runtime.authorized_candidate_dispatcher import dispatch_authorized_candidate
from controllergate.runtime.candidate_execution_authorization import CandidateExecutionAuthorization, seal_candidate_authorization
from controllergate.runtime.candidate_execution_plan import CandidateExecutionPlan, CandidatePhase, seal_candidate_plan

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs" / BATCH


def load(name: str) -> dict:
    return json.loads((OUT / name).read_text(encoding="utf-8"))


def test_hard_contamination_classes_reject_exact_repairs() -> None:
    cases = (
        "diff --git a/pkg.py b/pkg.py\n@@ -1 +1 @@",
        "fixed in commit deadbeef",
        "replace the function with this exact code\n```python\ndef f(): return 2\n```",
        "Please add 9 more test cases to tests/test_x.py",
    )
    assert all(classify_contamination(value)["classification"] == "HARD_REJECT" for value in cases)


def test_reproducer_and_broad_words_are_soft_not_hard() -> None:
    assert classify_contamination("```python\nraise TypeError('repro')\n```")["classification"] == "SOFT_RISK"
    assert classify_contamination("This solution and workaround patch did not work")["classification"] == "SOFT_RISK"


def test_sanitized_manifest_keeps_failure_and_excludes_repair() -> None:
    body = "AssertionError in tests/test_x.py::test_x\nPlease replace the function with this implementation"
    result = sanitize_issue_record(title="failure", body=body, comments="", classification=classify_contamination(body))
    assert "AssertionError" in result["failure_description"]
    assert "replace the function" not in result["failure_description"]
    assert result["independent_contamination_verifier"] == "PASS"


def _fixture(tmp_path: Path) -> Path:
    source = tmp_path / "source"; target = source / "tests" / "test_engine.py"; package = source / "pkg"
    target.parent.mkdir(parents=True); package.mkdir(parents=True)
    target.write_text("from pkg.engine import start_execution\n\ndef test_regression():\n    start_execution()\n", encoding="utf-8")
    (package / "engine.py").write_text("def start_execution():\n    raise TypeError\n", encoding="utf-8")
    return source


def test_target_resolution_exact_node_and_traceback(tmp_path: Path) -> None:
    source = _fixture(tmp_path)
    node = resolve_target(source, "FAILED tests/test_engine.py::test_regression", "a" * 40)
    traceback = resolve_target(source, 'File "tests/test_engine.py", line 4, in test_regression', "a" * 40)
    assert node["status"] == traceback["status"] == "PASS"
    assert node["confidence_class"] == "exact_issue_node"
    assert traceback["confidence_class"] == "traceback_derived_target"


def test_target_resolution_named_test_and_source_symbol(tmp_path: Path) -> None:
    source = _fixture(tmp_path)
    named = resolve_target(source, "failure in test_regression", "a" * 40)
    symbol = resolve_target(source, "TypeError in start_execution from pkg/engine.py", "a" * 40)
    assert named["target_node"] == "test_regression"
    assert symbol["status"] == "PASS" and symbol["confidence_class"] == "source_verified_symbol_to_test_target"


def test_bounded_single_native_target(tmp_path: Path) -> None:
    source = tmp_path / "source"; target = source / "tests" / "only_test.py"; target.parent.mkdir(parents=True)
    target.write_text("def check_behavior(): pass\n", encoding="utf-8")
    result = resolve_target(source, "regression error without a literal test path", "a" * 40)
    assert result["status"] == "PASS" and result["confidence_class"] == "bounded_project_native_target"


def test_semantic_command_continues_from_native_target(tmp_path: Path) -> None:
    source = _fixture(tmp_path); (source / "pyproject.toml").write_text("[tool.pytest.ini_options]\naddopts='-q'\n", encoding="utf-8")
    result = resolve_command_authority(source, "tests/test_engine.py::test_regression")
    assert result["status"] == "PASS" and result["selected"]["target_corroborated"]
    assert "tests/test_engine.py::test_regression" in result["selected"]["transformed_command"]


def test_true_and_false_command_conflicts(tmp_path: Path) -> None:
    true_root = tmp_path / "true"; true_root.mkdir(); (true_root / "tox.ini").write_text("[testenv]\ncommands =\n python -m pytest tests/a.py\n python -m pytest integration/b.py\n", encoding="utf-8")
    false_root = tmp_path / "false"; false_root.mkdir(); (false_root / "tox.ini").write_text("[testenv]\ncommands =\n poetry lock\n python -m pytest tests\n pre-commit run --all-files\n", encoding="utf-8")
    assert resolve_command_authority(true_root, "tests/x.py::test_x")["status"] == "MANUAL_REVIEW"
    assert resolve_command_authority(false_root, "tests/x.py::test_x")["status"] == "PASS"


def test_frame_freeze_is_ordered_and_not_replenished() -> None:
    records = [{"candidate_id": f"c{i}", "repo_url": f"https://example.invalid/{i}"} for i in range(15)]
    result = freeze_frame(records, maximum=12)
    assert result["candidate_count"] == 12 and result["adaptive_replenishment"] is False
    assert [item["frame_position"] for item in result["candidates"]] == list(range(12))


def test_resource_budget_blocks_before_phase_execution(tmp_path: Path) -> None:
    manifest = {"candidate_id": "c", "candidate_sha": "a" * 40, "repo_url": "https://example.invalid/x", "native_target_paths": ["tests/test_x.py"], "workspace_root": str(tmp_path), "frame_hash": "f" * 64, "allowed_output_root": str(tmp_path), "projected_resources": {"seconds": 11}}
    manifest_path = tmp_path / "manifest.json"; write_json_deterministic(manifest_path, manifest)
    phase = CandidatePhase("intake", "intake_candidate_manifest"); plan = seal_candidate_plan(CandidateExecutionPlan("p", "c", "a" * 40, hash_record(manifest), str(tmp_path), (phase,), str(tmp_path / "context.json"))); plan_path = tmp_path / "plan.json"; write_json_deterministic(plan_path, plan)
    now = datetime.now(timezone.utc); auth = seal_candidate_authorization(CandidateExecutionAuthorization("a", "c", "a" * 40, hash_record(manifest), plan["plan_hash"], ("intake",), (), {}, {}, {}, {"source": False, "tests": False}, {"seconds": 10}, str(tmp_path), now.isoformat(), (now + timedelta(minutes=1)).isoformat(), "nonce")); auth_path = tmp_path / "auth.json"; write_json_deterministic(auth_path, auth)
    result = dispatch_authorized_candidate(manifest_path=manifest_path, authorization_path=auth_path, plan_path=plan_path, checkpoint_path=tmp_path / "checkpoint.json", event_ledger_path=tmp_path / "events.jsonl", network_ledger_path=tmp_path / "network.jsonl", authorization_store=tmp_path / "nonces.json")
    assert result["blocker"] == "candidate_execution_resource_budget_exceeded"


def test_admission_freezes_before_diagnostics() -> None:
    value = load("batch074_admission_diagnostic_separation.json")
    assert value["status"] == "PASS" and value["cohort_frozen_before_diagnostics"]
    assert value["diagnostics_in_admission_plan"] is False and value["external_candidate_execution"] is False


def test_eight_arms_are_fully_isolated_and_cannot_patch() -> None:
    value = load("batch074_arm_isolation_validation.json")
    assert value["status"] == "PASS" and value["arm_count"] == 8
    assert all(value[key] for key in ("separate_authorization_state", "separate_nonce_stores", "separate_checkpoints", "separate_posterior_stores", "separate_event_ledgers", "separate_network_ledgers"))
    assert value["patch_authority_count"] == 0 and value["observation_sharing"] is False


def test_recovery_boundary_and_batch075_review_scope() -> None:
    final = load("batch074_final_decision.json"); allowlist = load("batch075_static_candidate_allowlist.json"); scope = load("batch075_execution_scope.json")
    assert final["status"] == "LOCAL_IMPLEMENTATION_RECOVERY_COMPLETE"
    assert final["external_prospective_cohort_execution"] == "DEFERRED_TO_MANUALLY_REVIEWED_BATCH075"
    assert final["prospective_candidate_wave_executed"] is False and final["AMDS_PROSPECTIVE_EFFECTIVENESS"] == "NOT_ESTABLISHED"
    assert len(allowlist["candidates"]) <= 3 and all(item["manual_review_required"] and not item["execution_authorized"] for item in allowlist["candidates"])
    assert scope["public_repositories_only"] and scope["manual_workflow_dispatch"] and not scope["broad_discovery"]


def test_workflow_has_no_external_candidate_operations() -> None:
    text = (ROOT / ".github" / "workflows" / "post_v2_37_hardening_batch074_sterile_high_yield_amds_memory_wave1.yml").read_text(encoding="utf-8")
    assert not any(value in text for value in ("search/issues", "gh api", "gh search issues", "git clone", "pip wheel", "--artifact", "GH_TOKEN"))
