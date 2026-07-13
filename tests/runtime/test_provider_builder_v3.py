from pathlib import Path

from controllergate.core.evidence import sha256_file
from controllergate.runtime.provider_builder import build_provider


def test_provider_uses_writable_copy_and_preserves_source(tmp_path: Path):
    source = tmp_path / "source"; source.mkdir(); (source / "setup.py").write_text("x=1\n")
    artifact = tmp_path / "package.whl"; artifact.write_bytes(b"provider")
    result = build_provider(immutable_source=source, runtime_root=tmp_path / "runtime", candidate_id="c", artifacts=[{"path": str(artifact), "sha256": sha256_file(artifact)}])
    assert result["status"] == "PASS"
    assert result["original_source_immutable"]
    assert result["states"][-1] == "PROVIDER_EXECUTION_READY"


def test_zero_artifacts_never_recovered(tmp_path: Path):
    source = tmp_path / "source"; source.mkdir(); (source / "setup.py").write_text("x=1\n")
    result = build_provider(immutable_source=source, runtime_root=tmp_path / "runtime", candidate_id="c", artifacts=[])
    assert result["status"] == "BLOCK"
    assert "PROVIDER_VERIFIED" not in result["states"]
