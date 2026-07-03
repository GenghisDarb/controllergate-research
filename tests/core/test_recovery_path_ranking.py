from controllergate.core.recovery_path_ranking import rank_recovery_paths


def test_darker_issue112_without_manual_lock_ranks_manual_lock_first():
    ranking = rank_recovery_paths(dependency_lock_status="ABSENT", target_intent_alignment=False)

    assert ranking["top_recovery_path"] == "provide_manual_dependency_lock"
    assert ranking["paths"][2]["blocked"] is True
    assert ranking["paths"][2]["blocker"] == "manual_dependency_lock_absent"
