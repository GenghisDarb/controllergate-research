from pathlib import Path

from controllergate.runtime.isolated_repair_sandbox import validate_sandbox_path


def test_sandbox_cannot_be_inside_repo_or_onedrive(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    inside = repo / "sandbox"
    inside.mkdir()
    assert validate_sandbox_path(inside, repo)["status"] == "BLOCK"
    outside = tmp_path / "other_sandbox"
    outside.mkdir()
    assert validate_sandbox_path(outside, repo)["status"] == "PASS"
    onedrive = Path(tmp_path) / "OneDrive" / "sandbox"
    onedrive.mkdir(parents=True)
    assert validate_sandbox_path(onedrive, repo)["status"] == "BLOCK"
