from controllergate.core.source_ranking import select_two_candidate_routes


def test_two_candidate_selection_records_secondary_when_available():
    result = select_two_candidate_routes([
        {"source_path": "src/pkg/a.py", "function_or_class": None},
        {"source_path": "src/pkg/b.py", "function_or_class": None},
    ])
    assert result["primary_route"]["source_path"] == "src/pkg/a.py"
    assert result["secondary_route"]["source_path"] == "src/pkg/b.py"
    assert result["secondary_available"] is True


def test_two_candidate_selection_handles_single_route():
    result = select_two_candidate_routes([{"source_path": "src/pkg/a.py", "function_or_class": None}])
    assert result["primary_route"]["source_path"] == "src/pkg/a.py"
    assert result["secondary_route"] is None
