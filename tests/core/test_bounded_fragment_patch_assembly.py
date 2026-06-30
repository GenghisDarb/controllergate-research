from controllergate.core.fragment_patch import assemble_fragments, audit_fragment


ALLOWED = {"src/darker/__main__.py", "src/darker/import_sorting.py"}


def test_at_most_three_source_only_fragments() -> None:
    fragments = [
        {"fragment_id": f"f{i}", "candidate_id": "darker_skip_glob_failing_test", "target_file": "src/darker/__main__.py", "target_function_or_class": f"fn{i}", "context_hash": f"h{i}", "diff_hunk": "@@\n-x\n+y\n"}
        for i in range(3)
    ]
    result = assemble_fragments(fragments, allowed_source_files=ALLOWED)
    assert result["status"] == "PASS"
    assert result["fragment_count"] == 3


def test_fourth_fragment_blocks_assembly() -> None:
    fragments = [
        {"fragment_id": f"f{i}", "candidate_id": "darker_skip_glob_failing_test", "target_file": "src/darker/__main__.py", "target_function_or_class": f"fn{i}", "context_hash": f"h{i}", "diff_hunk": "@@\n-x\n+y\n"}
        for i in range(4)
    ]
    result = assemble_fragments(fragments, allowed_source_files=ALLOWED)
    assert result["status"] == "BLOCK"
    assert result["blocker"] == "fragment_assembly_cap_exceeded"


def test_fragment_cannot_modify_tests_or_configs() -> None:
    audit = audit_fragment(
        {"fragment_id": "bad", "candidate_id": "darker_skip_glob_failing_test", "target_file": "src/darker/tests/test_main_isort.py", "diff_hunk": "@@\n-x\n+y\n"},
        allowed_source_files=ALLOWED,
    )
    assert audit["status"] == "BLOCK"
    assert audit["blocker"] == "fragment_forbidden_patch_target"
