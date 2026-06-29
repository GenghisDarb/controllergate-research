from __future__ import annotations

from controllergate.core.clean_repair import SKIP_GLOB_SEMANTIC_MARKERS, SKIP_GLOB_TARGET_NODE, select_semantic_target_node


def test_intended_target_node_can_be_selected_by_semantic_markers() -> None:
    nodes = [
        "src/darker/tests/test_main_isort.py::test_unrelated_fixture",
        SKIP_GLOB_TARGET_NODE,
    ]
    selection = select_semantic_target_node(
        nodes,
        intended_node=SKIP_GLOB_TARGET_NODE,
        semantic_markers=SKIP_GLOB_SEMANTIC_MARKERS,
    )
    assert selection["status"] == "PASS"
    assert selection["selected_node"] == SKIP_GLOB_TARGET_NODE
    assert selection["non_intent_first_failure_allowed_as_primary"] is False


def test_missing_intended_target_node_blocks_even_if_other_nodes_exist() -> None:
    selection = select_semantic_target_node(
        ["src/darker/tests/test_main_isort.py::test_unrelated_fixture"],
        intended_node=SKIP_GLOB_TARGET_NODE,
        semantic_markers=SKIP_GLOB_SEMANTIC_MARKERS,
    )
    assert selection["status"] == "BLOCK"
    assert selection["blocker"] == "target_node_semantic_intent_mismatch"
