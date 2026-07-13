from pathlib import Path

from controllergate.intake.target_resolver_v3 import resolve_target_v3


def test_exact_native_target(tmp_path: Path):
    target = tmp_path / "tests/test_a.py"; target.parent.mkdir(); target.write_text("def test_unique():\n    pass\n")
    assert resolve_target_v3(tmp_path, exact_target="tests/test_a.py::test_unique")["status"] == "PASS"


def test_symbol_collision_routes_issue_lane(tmp_path: Path):
    tests = tmp_path / "tests"; tests.mkdir()
    (tests / "test_a.py").write_text("def test_sync():\n    pass\n")
    (tests / "test_b.py").write_text("def test_sync():\n    pass\n")
    result = resolve_target_v3(tmp_path, exact_target="tests/test_a.py::test_sync")
    assert result["status"] == "BLOCK"
    assert result["lane"] == "ISSUE_DERIVED_REPRODUCER_LANE"


def test_single_test_file_not_promoted_without_node(tmp_path: Path):
    assert resolve_target_v3(tmp_path, exact_target="tests/test_a.py")["status"] == "BLOCK"
