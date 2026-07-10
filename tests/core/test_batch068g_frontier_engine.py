from __future__ import annotations

import json
from pathlib import Path

from controllergate.core.command_evidence_graph import build_command_evidence_graph, provenance_matches
from controllergate.core.command_orthology import command_token_safety, extract_command_candidates, rank_command_candidates
from controllergate.core.frontier_state import attach_state_hash, verify_state_hash
from controllergate.core.provider_feasibility import classify_provider_feasibility
from controllergate.core.runner_target import classify_runner_target
from controllergate.core.runtime_wrapper_activation_watchdog import runtime_wrapper_activation_watchdog
from controllergate.core.static_metadata import extract_explicit_test_paths, infer_issue_url, select_metadata_paths
from controllergate.core.step_runtime import execute_static_graph, resolve_registry
from controllergate.engine import FrontierEngine

ROOT = Path(__file__).resolve().parents[2]


def command(path: str, argv: list[str]) -> dict[str, object]:
    return {"source_path": path, "source_class": path, "argv": argv}


def test_source_order_invariance() -> None:
    candidates = [command("tox.ini", ["pytest", "tests/a.py"]), command("pyproject.toml", ["pytest", "tests/a.py"])]
    assert rank_command_candidates(candidates)["selected"]["argv"] == rank_command_candidates(list(reversed(candidates)))["selected"]["argv"]


def test_authoritative_conflict_requires_manual_review() -> None:
    candidates = [command("tox.ini", ["pytest", "tests/a.py"]), command("tox.ini", ["pytest", "tests/b.py"])]
    assert rank_command_candidates(candidates)["status"] == "MANUAL_REVIEW"


def test_unsafe_tokens_block() -> None:
    assert command_token_safety(["pytest", "&&", "curl"])["status"] == "BLOCK"
    assert command_token_safety(["pytest", "--rootdir=/tmp"])["status"] == "BLOCK"


def test_command_extraction_uses_structured_argv() -> None:
    records = extract_command_candidates("tox.ini", "[testenv]\ncommands = pytest", ["tests/a.py"])
    assert records
    assert isinstance(records[0]["argv"], list)
    assert "tests/a.py" in records[0]["argv"]


def test_target_path_parser_is_bounded() -> None:
    assert extract_explicit_test_paths("Run tests/unit/test_api.py::test_case") == ["tests/unit/test_api.py"]
    assert extract_explicit_test_paths("Support comes from tests/conftest.py") == []


def test_metadata_selection_is_deterministic() -> None:
    entries = [{"path": "tox.ini"}, {"path": ".github/workflows/test.yml"}, {"path": "docs/testing.md"}]
    assert select_metadata_paths(entries) == select_metadata_paths(list(reversed(entries)))


def test_issue_url_inference_is_candidate_agnostic() -> None:
    assert infer_issue_url("https://github.com/owner/repo", "prefix_issues_123") == "https://github.com/owner/repo/issues/123"


def test_provenance_swap_blocks() -> None:
    graph = build_command_evidence_graph(candidate_sha="a" * 40, sources=[], commands=[])
    assert provenance_matches(graph, "a" * 40)
    assert not provenance_matches(graph, "b" * 40)


def test_future_source_injection_blocks() -> None:
    graph = build_command_evidence_graph(candidate_sha="a" * 40, sources=[], commands=[])
    graph["forbidden_sources_used"] = ["future_commit"]
    assert not provenance_matches(graph, "a" * 40)


def test_runner_target_collision_is_classified() -> None:
    assert classify_runner_target(runner_package="pytest", target_package="pytest") == "runner_target_collision_unresolved_self_runner"


def test_provider_feasibility_classification() -> None:
    pure = classify_provider_feasibility("pytest>=7", ["pyproject.toml"])
    compiled = classify_provider_feasibility("scipy>=1", ["pyproject.toml"])
    assert pure["classification"] == "bounded_python_provider_surface_static"
    assert compiled["classification"] == "compiled_or_system_dependency_static"


def test_state_hash_is_semantic_and_stable() -> None:
    first = attach_state_hash({"value": 1, "timestamp": "one"})
    second = attach_state_hash({"value": 1, "timestamp": "two"})
    assert first["state_hash"] == second["state_hash"]
    assert verify_state_hash(first)


def test_step_handler_and_verifier_resolution() -> None:
    steps = [{"step_id": "CG-RXN-001", "handler": "passthrough_handler", "verifier": "nonempty_output_verifier"}]
    assert resolve_registry(steps)["status"] == "PASS"
    result = execute_static_graph("synthetic", steps, {"CG-RXN-001": {"status": "PASS"}})
    assert result[0]["status"] == "pass"


def test_step_graph_records_upstream_block() -> None:
    steps = [
        {"step_id": "CG-RXN-001", "handler": "passthrough_handler", "verifier": "nonempty_output_verifier"},
        {"step_id": "CG-RXN-002", "handler": "passthrough_handler", "verifier": "nonempty_output_verifier"},
    ]
    result = execute_static_graph("synthetic", steps, {"CG-RXN-001": {"status": "BLOCK", "blocker": "missing_evidence"}, "CG-RXN-002": {"status": "PASS"}})
    assert result[1]["blocker_code"] == "missing_evidence"


def test_runtime_watchdog_is_conjunctive() -> None:
    result = runtime_wrapper_activation_watchdog(issue_derived_repair_count=20, evidence={})
    assert result["issue_derived_repair_floor_met"] is True
    assert result["conjunctive_evidence_vector_complete"] is False
    assert result["runtime_wrapper_activation_allowed"] is False


def test_frontier_cli_backing_engine_when_generated() -> None:
    state = ROOT / "outputs" / "frontier" / "CURRENT_FRONTIER_STATE.json"
    if not state.is_file():
        return
    engine = FrontierEngine(ROOT)
    assert engine.validate()["status"] == "PASS"
    index = json.loads(engine.index_path.read_text(encoding="utf-8"))
    plan = engine.plan(index["records"][0]["candidate_id"])
    assert plan["status"] == "PASS"
    assert plan["execution_authorized"] is False


def test_regression_audit_registry_is_ordered_and_complete() -> None:
    registry = json.loads((ROOT / "configs/controllergate_regression_audit_registry.json").read_text(encoding="utf-8"))
    orders = [item["dependency_order"] for item in registry["audits"]]
    assert orders == sorted(orders)
    assert all((ROOT / item["script_path"]).is_file() for item in registry["audits"] if item["required"])
