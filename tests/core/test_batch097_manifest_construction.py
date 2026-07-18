from __future__ import annotations

import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def test_sha_manifest_hashes_scoped_manifests_without_self_entry(tmp_path: Path) -> None:
    joined = tmp_path / "joined"
    output = tmp_path / "output"
    joined.mkdir()
    subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "finalize_batch097.py"),
            "--joined",
            str(joined),
            "--output",
            str(output),
            "--workflow-run",
            "test-run",
            "--workflow-head",
            "0" * 40,
        ],
        cwd=ROOT,
        check=True,
    )
    paths = {line.split(maxsplit=1)[1] for line in (output / "SHA256SUMS.txt").read_text().splitlines()}
    assert "ARTIFACT_SHA256SUMS.txt" in paths
    assert "PORTABLE_ARTIFACT_SHA256SUMS.txt" in paths
    assert "SHA256SUMS.txt" not in paths
