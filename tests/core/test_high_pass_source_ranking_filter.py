from controllergate.core.source_ranking import apply_high_pass_filter


def test_high_pass_filter_cannot_mask_all_legal_source_files():
    result = apply_high_pass_filter([])
    assert result["blocker"] == "high_pass_filter_no_legal_source_remaining"


def test_high_pass_filter_preserves_only_legal_source_path():
    result = apply_high_pass_filter([{"source_path": "src/pkg/mod.py"}])
    assert result["status"] == "PASS"
    assert result["admitted"][0]["source_path"] == "src/pkg/mod.py"
