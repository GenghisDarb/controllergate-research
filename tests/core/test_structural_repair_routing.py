from __future__ import annotations

from pathlib import Path

from controllergate.core.clean_repair import build_structural_repair_routing_map


def test_structural_routing_uses_target_imports_for_patchable_source(tmp_path: Path):
    (tmp_path / "src" / "darker" / "tests").mkdir(parents=True)
    (tmp_path / "src" / "darker").mkdir(parents=True, exist_ok=True)
    (tmp_path / "src" / "darker" / "__main__.py").write_text("def repair_target():\n    return 1\n", encoding="utf-8", newline="\n")
    target = tmp_path / "src" / "darker" / "tests" / "test_main.py"
    target.write_text("from darker.__main__ import repair_target\n\ndef test_a():\n    assert repair_target() == 2\n", encoding="utf-8", newline="\n")

    routing = build_structural_repair_routing_map(
        {"candidate_id": "candidate", "target_test_path": "src/darker/tests/test_main.py"},
        tmp_path,
        {"returncode": 1, "semantic_failure_signature_hash": "s" * 64, "command_record": {"output_summary": "test_a failed"}},
    )

    assert routing["repair_routing_decision"] == "admit_patchable_subset"
    assert routing["patchable_source_subset"] == ["src/darker/__main__.py"]


def test_structural_routing_blocks_without_candidate_source_interlock(tmp_path: Path):
    (tmp_path / "tests").mkdir()
    (tmp_path / "tests" / "test_main.py").write_text("def test_a():\n    assert False\n", encoding="utf-8", newline="\n")

    routing = build_structural_repair_routing_map(
        {"candidate_id": "candidate", "target_test_path": "tests/test_main.py"},
        tmp_path,
        {"returncode": 1, "semantic_failure_signature_hash": "s" * 64, "command_record": {"output_summary": "test_a failed"}},
    )

    assert routing["repair_routing_decision"] == "no_patchable_source_subset"
