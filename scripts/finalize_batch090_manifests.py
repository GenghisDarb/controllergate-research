from __future__ import annotations

import hashlib
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "outputs/post_v2_37_hardening_batch090_evidence_delaundering_installed_vertical_closure"
MANIFESTS = {"SHA256SUMS.txt", "PORTABLE_ARTIFACT_SHA256SUMS.txt", "ARTIFACT_SHA256SUMS.txt"}


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def rows(paths: list[Path], prefix: str = "") -> str:
    return "".join(f"{sha(path)}  {prefix}{path.name}\n" for path in paths)


base = [path for path in sorted(OUTPUT.iterdir()) if path.is_file() and path.name not in MANIFESTS]
portable = list(base)
(OUTPUT / "PORTABLE_ARTIFACT_SHA256SUMS.txt").write_text(rows(portable, "./"), encoding="utf-8", newline="\n")
artifact = [*base, OUTPUT / "PORTABLE_ARTIFACT_SHA256SUMS.txt"]
(OUTPUT / "ARTIFACT_SHA256SUMS.txt").write_text(rows(artifact), encoding="utf-8", newline="\n")
primary = [*base, OUTPUT / "ARTIFACT_SHA256SUMS.txt", OUTPUT / "PORTABLE_ARTIFACT_SHA256SUMS.txt"]
(OUTPUT / "SHA256SUMS.txt").write_text(rows(primary), encoding="utf-8", newline="\n")
print(f"BATCH090_MANIFESTS_PASS files={len(base)}")
