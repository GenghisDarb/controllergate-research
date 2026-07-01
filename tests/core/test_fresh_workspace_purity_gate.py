from controllergate.core.workspace_purity import audit_workspace_purity


def test_workspace_purity_ready_without_seed():
    result = audit_workspace_purity(None, repo_root=".", seed_present=False)

    assert result["status"] == "PASS"
    assert result["workspace_purity_status"] == "READY_NO_SEED"
    assert result["workspace_created"] is False


def test_workspace_inside_repo_is_blocked(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    workspace = repo / "candidate"
    workspace.mkdir()

    result = audit_workspace_purity(workspace, repo_root=repo, seed_present=True)

    assert result["status"] == "BLOCK"
    assert result["blocker"] == "workspace_inside_repo_blocked"
