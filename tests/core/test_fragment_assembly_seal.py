from controllergate.core.fragment_patch import assemble_fragments


def test_fragment_assembly_fails_on_conflicting_hunks() -> None:
    fragments = [
        {"fragment_id": "a", "candidate_id": "darker_skip_glob_failing_test", "target_file": "src/darker/__main__.py", "target_function_or_class": "main", "context_hash": "same", "diff_hunk": "@@\n-a\n+b\n"},
        {"fragment_id": "b", "candidate_id": "darker_skip_glob_failing_test", "target_file": "src/darker/__main__.py", "target_function_or_class": "main", "context_hash": "same", "diff_hunk": "@@\n-c\n+d\n"},
    ]
    result = assemble_fragments(fragments, allowed_source_files={"src/darker/__main__.py"})
    assert result["status"] == "BLOCK"
    assert result["blocker"] == "fragment_assembly_failed"


def test_assembled_patch_hash_is_recorded() -> None:
    fragments = [
        {"fragment_id": "a", "candidate_id": "darker_skip_glob_failing_test", "target_file": "src/darker/__main__.py", "target_function_or_class": "main", "context_hash": "one", "diff_hunk": "@@\n-a\n+b\n"},
    ]
    result = assemble_fragments(fragments, allowed_source_files={"src/darker/__main__.py"})
    assert result["status"] == "PASS"
    assert len(result["assembled_patch_sha256"]) == 64
