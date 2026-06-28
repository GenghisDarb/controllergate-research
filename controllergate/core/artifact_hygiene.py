from __future__ import annotations

import shutil
from pathlib import Path

from .evidence import sha256_file, write_json_deterministic, write_text_lf

CACHE_DIR_NAMES = {"__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache", ".venv", "venv", "env", "ENV"}
CACHE_SUFFIXES = {".pyc", ".pyo", ".zip", ".tar", ".gz", ".tgz", ".7z"}


def is_cache_or_archive_payload(path: str | Path) -> bool:
    candidate = Path(path)
    return any(part in CACHE_DIR_NAMES for part in candidate.parts) or candidate.suffix in CACHE_SUFFIXES


def stage_artifact_payload(destination: str | Path, sources: list[str | Path]) -> dict[str, object]:
    dest = Path(destination)
    if dest.exists():
        shutil.rmtree(dest)
    dest.mkdir(parents=True, exist_ok=True)
    copied: list[str] = []
    excluded: list[str] = []
    for source in sources:
        root = Path(source)
        if not root.exists():
            continue
        if root.is_file():
            candidates = [root]
            base = root.parent
        else:
            candidates = [path for path in root.rglob("*") if path.is_file()]
            base = root.parent
        for path in candidates:
            rel = path.relative_to(base)
            if is_cache_or_archive_payload(rel):
                excluded.append(rel.as_posix())
                continue
            target = dest / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(path, target)
            copied.append(target.relative_to(dest).as_posix())
    return {"status": "PASS", "destination": str(dest), "copied_files": sorted(copied), "excluded_files": sorted(excluded)}


def write_artifact_manifest(payload_dir: str | Path, manifest_name: str = "ARTIFACT_SHA256SUMS.txt") -> dict[str, object]:
    root = Path(payload_dir)
    rows: list[str] = []
    files: list[str] = []
    for path in sorted(root.rglob("*")):
        if path.is_file() and path.name != manifest_name and not is_cache_or_archive_payload(path.relative_to(root)):
            rel = path.relative_to(root).as_posix()
            rows.append(f"{sha256_file(path)}  {rel}")
            files.append(rel)
    write_text_lf(root / manifest_name, "\n".join(rows))
    return {"status": "PASS", "manifest_path": str(root / manifest_name), "covered_files": files, "covered_file_count": len(files)}


def audit_artifact_payload(payload_dir: str | Path, manifest_name: str = "ARTIFACT_SHA256SUMS.txt") -> dict[str, object]:
    root = Path(payload_dir)
    payload_files = sorted(path.relative_to(root).as_posix() for path in root.rglob("*") if path.is_file())
    cache_payloads = [rel for rel in payload_files if is_cache_or_archive_payload(rel)]
    manifest = root / manifest_name
    covered: set[str] = set()
    malformed: list[str] = []
    mismatches: list[str] = []
    if manifest.is_file():
        for line in manifest.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            parts = line.split(maxsplit=1)
            if len(parts) != 2:
                malformed.append(line)
                continue
            digest, rel = parts
            covered.add(rel)
            path = root / rel
            if not path.is_file() or sha256_file(path) != digest:
                mismatches.append(rel)
    uncovered = sorted(set(payload_files) - covered - {manifest_name})
    return {
        "status": "PASS" if not cache_payloads and not malformed and not mismatches and not uncovered else "FAIL",
        "payload_file_count": len(payload_files),
        "cache_payloads": cache_payloads,
        "manifest_path": str(manifest),
        "malformed": malformed,
        "mismatches": mismatches,
        "uncovered": uncovered,
    }
