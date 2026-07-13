from __future__ import annotations

from pathlib import Path
import subprocess

from controllergate.intake.command_resolution_v2 import resolve_command_v2
from controllergate.intake.preflight_terminal_registry import terminal_record
from controllergate.intake.provider_dry_lock import build_provider_dry_lock
from controllergate.intake.source_object_verifier import verify_source_object
from controllergate.intake.target_resolution_v2 import resolve_target_v2
from controllergate.runtime.provider_capsule_v3 import build_provider_capsule_v3


def test_real_source_object_verification(tmp_path: Path) -> None:
    source = tmp_path / "origin"
    source.mkdir()
    subprocess.run(["git", "init", "-q"], cwd=source, check=True)
    subprocess.run(["git", "config", "user.email", "batch080@example.invalid"], cwd=source, check=True)
    subprocess.run(["git", "config", "user.name", "Batch080"], cwd=source, check=True)
    (source / "x.py").write_text("x = 1\n", encoding="utf-8")
    subprocess.run(["git", "add", "x.py"], cwd=source, check=True)
    subprocess.run(["git", "commit", "-qm", "fixture"], cwd=source, check=True)
    sha = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=source, text=True).strip()
    record = verify_source_object(str(source), sha, tmp_path / "checkout")
    assert record["status"] == "PASS"
    assert record["head"] == sha and record["object_type"] == "commit"


def test_target_command_provider_and_terminal(tmp_path: Path) -> None:
    (tmp_path / "tests").mkdir()
    (tmp_path / "tests" / "test_unit.py").write_text("def test_one():\n    assert True\n", encoding="utf-8")
    (tmp_path / "pyproject.toml").write_text('[build-system]\nrequires=["setuptools"]\nbuild-backend="setuptools.build_meta"\n[tool.pytest.ini_options]\n', encoding="utf-8")
    target = resolve_target_v2(tmp_path, "tests/test_unit.py::test_one", "a" * 40)
    command = resolve_command_v2(tmp_path, target["target"])
    runtime = {"status": "PASS", "python_version": "3.13"}
    platform = {"status": "PASS", "operating_system": "linux"}
    provider = build_provider_dry_lock(tmp_path, runtime=runtime, platform=platform)
    assert target["target_exists"] and command["status"] == provider["status"] == "PASS"
    terminal = terminal_record("fixture", {name: {"status": "PASS"} for name in ("issue_snapshot", "source", "runtime", "target", "command", "provider_dry_lock", "collection") } | {"contamination": {"status": "CLEAN"}})
    assert terminal["admitted_to_execution_frame"]


def test_provider_capsule_v3_requires_hashed_artifacts() -> None:
    common = {"status": "PASS"}
    blocked = build_provider_capsule_v3(source_sha="b" * 40, platform=common, abi=common, toolchain=common, dry_lock={"status": "PASS"})
    assert blocked["status"] == "BLOCK"
    passed = build_provider_capsule_v3(source_sha="b" * 40, platform=common, abi=common, toolchain=common, dry_lock={"status": "PASS"}, artifacts=[{"filename": "x.whl", "sha256": "c" * 64, "source_url": "https://example.invalid/x.whl"}])
    assert passed["status"] == "PASS" and not passed["provider_bytes_committed"]
