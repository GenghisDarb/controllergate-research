from controllergate.core.source_ranking import strict_minimum_delta


def test_identical_rankings_produce_no_routing_delta():
    ranking = [{"source_path": "src/pkg/mod.py", "function_or_class": None}]
    result = strict_minimum_delta(
        before=ranking,
        after=ranking,
        context_before=["src/pkg/mod.py"],
        context_after=["src/pkg/mod.py"],
        generation_before={"strategy": "fragment"},
        generation_after={"strategy": "fragment"},
    )
    assert result["routing_delta_detected"] is False
    assert result["blocker"] == "active_memory_routing_delta_not_established"


def test_metadata_only_changes_do_not_count_as_routing_delta():
    before = [{"source_path": "src/pkg/mod.py", "function_or_class": None, "score": 0}]
    after = [{"source_path": "src/pkg/mod.py", "function_or_class": None, "score": 1}]
    result = strict_minimum_delta(
        before=before,
        after=after,
        context_before=["src/pkg/mod.py"],
        context_after=["src/pkg/mod.py"],
        generation_before={"strategy": "fragment"},
        generation_after={"strategy": "fragment"},
    )
    assert result["routing_delta_detected"] is False


def test_changed_top_ranked_source_counts_as_routing_delta():
    result = strict_minimum_delta(
        before=[{"source_path": "src/pkg/a.py", "function_or_class": None}],
        after=[{"source_path": "src/pkg/b.py", "function_or_class": None}],
        context_before=["src/pkg/a.py"],
        context_after=["src/pkg/a.py"],
        generation_before={"strategy": "fragment"},
        generation_after={"strategy": "fragment"},
    )
    assert result["routing_delta_detected"] is True
    assert "top_ranked_source_file_changed" in result["routing_delta_reason_codes"]


def test_changed_context_selection_counts_as_routing_delta():
    result = strict_minimum_delta(
        before=[{"source_path": "src/pkg/a.py", "function_or_class": None}],
        after=[{"source_path": "src/pkg/a.py", "function_or_class": None}],
        context_before=["src/pkg/a.py"],
        context_after=["src/pkg/a.py", "src/pkg/b.py"],
        generation_before={"strategy": "fragment"},
        generation_after={"strategy": "fragment"},
    )
    assert result["routing_delta_detected"] is True
    assert "context_selection_changed" in result["routing_delta_reason_codes"]
