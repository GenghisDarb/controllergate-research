from controllergate.runtime.active_ast_excision_probe import plan_excision_probe


def test_ast_excision_probe_runs_only_in_sandbox(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    sandbox = tmp_path / "sandbox"
    sandbox.mkdir()
    source = "def target():\n    return 1\n"
    result = plan_excision_probe("pkg/mod.py", source, sandbox, repo)
    assert result["status"] == "PASS"
    assert result["sandbox_only"] is True
    assert result["real_source_tree_modified"] is False
    blocked = plan_excision_probe("pkg/mod.py", source, repo / "inner", repo)
    assert blocked["status"] == "BLOCK"
