from controllergate.state.blocker_taxonomy import BlockerClass, BlockerNode, validate_blocker_graph


def node(identifier: str, kind: BlockerClass, parent: str | None = None) -> BlockerNode:
    return BlockerNode(identifier, kind, parent, "ACTIVE", ("evidence.json",), "produce fresh evidence")


def test_dependency_ordered_blocker_graph_keeps_categories_separate() -> None:
    graph = validate_blocker_graph([
        node("cohort", BlockerClass.ACTIVE_ROOT_BLOCKER),
        node("darker", BlockerClass.ACTIVE_CHILD_BLOCKER, "cohort"),
        node("roles", BlockerClass.DOWNSTREAM_NOT_RUN, "cohort"),
        node("approval", BlockerClass.DORMANT_EXTERNAL_CONDITION),
        node("prospective", BlockerClass.CLAIM_BOUNDARY),
        node("stoichiometry", BlockerClass.SHADOW_CAPABILITY_LIMIT),
    ])
    assert graph["status"] == "PASS"
    assert graph["active_root_count"] == 1


def test_dormant_condition_cannot_be_active_child() -> None:
    graph = validate_blocker_graph([
        node("cohort", BlockerClass.ACTIVE_ROOT_BLOCKER),
        node("approval", BlockerClass.DORMANT_EXTERNAL_CONDITION, "cohort"),
    ])
    assert graph["status"] == "BLOCK"
    assert any("non_active_category" in reason for reason in graph["reasons"])
