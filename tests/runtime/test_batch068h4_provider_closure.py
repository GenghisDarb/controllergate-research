from __future__ import annotations

from pathlib import Path
import zipfile

from controllergate.runtime.artifact_metadata_reader import read_artifact_metadata
from controllergate.runtime.release_catalog import select_release_file
from controllergate.runtime.requirement_expander import applicable_requirement
from controllergate.runtime.root_requirements import reconstruct_roots
from controllergate.runtime.wheel_compatibility import wheel_compatibility


def test_root_requirement_reconstruction_separates_classes(tmp_path: Path) -> None:
    (tmp_path / "pyproject.toml").write_text('[project]\nname="x"\ndependencies=["runtime>=1"]\n[project.optional-dependencies]\ntest=["pytest>=7"]\n[build-system]\nrequires=["hatchling>=1"]\nbuild-backend="hatchling.build"\n', encoding="utf-8")
    result = reconstruct_roots(tmp_path)
    assert result["status"] == "PASS"
    assert [row["dependency_class"] for row in result["records"]] == ["runtime", "test", "build"]
    assert all(row["source_hash"] and row["source_location"] for row in result["records"])


def test_pep508_marker_and_name_normalization() -> None:
    result = applicable_requirement("Demo_Pkg>=1; python_version >= '3.13'")
    assert result["applies"] is True
    assert result["name"] == "demo-pkg"


def test_wheel_compatibility_prefers_universal_and_linux_binary() -> None:
    assert wheel_compatibility("demo-1-py3-none-any.whl")["preference"] == 1
    assert wheel_compatibility("demo-1-py3-none-manylinux_2_17_x86_64.whl")["compatible"] is True
    assert wheel_compatibility("demo-1-cp312-cp312-win_amd64.whl")["compatible"] is False


def test_release_selection_filters_cutoff_yanked_and_python() -> None:
    base = {"package": "demo", "packagetype": "bdist_wheel", "target_environment_compatible": True, "selection_preference": 1, "requires_python": ">=3.8", "artifact_file_url": "https://files.example/x", "project_metadata_url": "https://pypi.example/demo", "sha256": "a" * 64, "size": 1}
    files = [{**base, "version": "1.0", "filename": "demo-1-py3-none-any.whl", "cutoff_eligible": True, "yanked": False}, {**base, "version": "2.0", "filename": "demo-2-py3-none-any.whl", "cutoff_eligible": False, "yanked": False}, {**base, "version": "1.5", "filename": "demo-15-py3-none-any.whl", "cutoff_eligible": True, "yanked": True}]
    assert select_release_file({"files": files}, [">=1"], "3.13.0b2")["version"] == "1.0"


def test_wheel_metadata_ignores_vendored_dist_info(tmp_path: Path) -> None:
    wheel = tmp_path / "demo-1-py3-none-any.whl"
    with zipfile.ZipFile(wheel, "w") as archive:
        archive.writestr("demo-1.dist-info/METADATA", "Metadata-Version: 2.1\nName: demo\nVersion: 1\n\n")
        archive.writestr("demo/vendor/other-1.dist-info/METADATA", "Name: other\nVersion: 1\n\n")
    assert read_artifact_metadata(wheel)["name"] == "demo"


def test_archive_traversal_is_rejected(tmp_path: Path) -> None:
    wheel = tmp_path / "demo-1-py3-none-any.whl"
    with zipfile.ZipFile(wheel, "w") as archive:
        archive.writestr("../escape", "x"); archive.writestr("demo-1.dist-info/METADATA", "Name: demo\nVersion: 1\n\n")
    try: read_artifact_metadata(wheel)
    except ValueError as exc: assert str(exc) == "unsafe_archive_path"
    else: raise AssertionError("unsafe wheel accepted")
