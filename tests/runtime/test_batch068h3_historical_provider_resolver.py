from __future__ import annotations

from pathlib import Path
import zipfile

from controllergate.runtime.artifact_metadata_reader import read_artifact_metadata
from controllergate.runtime.historical_metadata import ArtifactCandidate
from controllergate.runtime.historical_provider_resolver import resolve_from_verified_roots
from controllergate.runtime.provider_constraint_solver import requirement_applies, solve


def candidate(version: str, *, yanked: bool = False, requires_python: str | None = None, requires_dist: tuple[str, ...] = ()) -> ArtifactCandidate:
    return ArtifactCandidate("demo", version, f"demo-{version}-py3-none-any.whl", "wheel", "2024-01-01T00:00:00Z", "a" * 64, "https://example.invalid/demo", "b" * 64, requires_python, requires_dist, yanked)


def test_pep508_markers_and_deterministic_constraint_selection() -> None:
    assert requirement_applies("demo>=1; python_version >= '3.11'", {"python_version": "3.13"})
    result = solve(["demo>=1,<3"], [candidate("1.0"), candidate("2.0"), candidate("2.5", yanked=True), candidate("3.0")], environment={"python_full_version": "3.13.0", "python_version": "3.13"}, cutoff="2024-07-03T12:05:28Z")
    assert result["status"] == "PASS"
    assert result["selected"]["demo"]["version"] == "2.0"


def test_constraint_conflict_is_explicit() -> None:
    result = solve(["demo<1"], [candidate("2.0")], environment={"python_full_version": "3.13.0", "python_version": "3.13"}, cutoff="2024-07-03T12:05:28Z")
    assert result["status"] == "BLOCK"
    assert result["conflicts"][0]["minimal_unsatisfied_constraint_set"] == ["demo<1"]


def test_wheel_metadata_is_read_without_execution(tmp_path: Path) -> None:
    wheel = tmp_path / "demo-1-py3-none-any.whl"
    with zipfile.ZipFile(wheel, "w") as archive:
        archive.writestr("demo-1.dist-info/METADATA", "Metadata-Version: 2.1\nName: demo\nVersion: 1\nRequires-Dist: dep>=2\n\n")
    metadata = read_artifact_metadata(wheel)
    assert metadata["status"] == "PASS"
    assert metadata["requires_dist"] == ["dep>=2"]


def test_verified_roots_preserve_direct_artifacts_and_block_dynamic_metadata() -> None:
    roots = [{"package": "demo", "selected_version": "1.0", "selected_filename": "demo-1.0.tar.gz", "selected_upload_time": "2024-01-01T00:00:00Z", "selected_artifact_sha256": "a" * 64, "metadata_url": "https://example.invalid/demo", "metadata_sha256": "b" * 64, "later_artifact_count_excluded": 2}]
    result = resolve_from_verified_roots(roots, "2024-07-03T12:05:28Z")
    assert result["lock"]["status"] == "BLOCK"
    assert result["lock"]["selected_artifacts"][0]["package"] == "demo"
    assert result["lock"]["unresolved_nodes"][0]["classification"] == "unresolved_dynamic_metadata"
    assert result["next_allowed_action"] == "batch068h4_dynamic_historical_metadata_recovery"
