from __future__ import annotations

import argparse
import hashlib
import json
import shutil
from pathlib import Path


def sha(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def manifest_rows(path: Path) -> list[tuple[str, str]]:
    values = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line:
            digest, name = line.split("  ", 1)
            values.append((digest, name))
    return values


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", default=".")
    parser.add_argument("--output", required=True)
    parser.add_argument("--stage", required=True)
    args = parser.parse_args()
    repo = Path(args.repo).resolve()
    output = Path(args.output).resolve()
    stage = Path(args.stage).resolve()
    if stage.exists():
        shutil.rmtree(stage)
    staged_output = stage / "outputs" / output.name
    staged_output.mkdir(parents=True)
    rows = manifest_rows(output / "PORTABLE_ARTIFACT_SHA256SUMS.txt")
    for expected, name in rows:
        source = output / name
        if not source.is_file() or sha(source) != expected:
            raise RuntimeError(f"portable source mismatch: {name}")
        shutil.copy2(source, staged_output / name)
    shutil.copy2(output / "PORTABLE_ARTIFACT_SHA256SUMS.txt", staged_output / "PORTABLE_ARTIFACT_SHA256SUMS.txt")
    inner_artifact_rows = [f"{expected}  {name}" for expected, name in rows]
    inner_artifact_rows.append(f"{sha(staged_output / 'PORTABLE_ARTIFACT_SHA256SUMS.txt')}  PORTABLE_ARTIFACT_SHA256SUMS.txt")
    (staged_output / "ARTIFACT_SHA256SUMS.txt").write_text("\n".join(sorted(inner_artifact_rows)) + "\n", encoding="utf-8", newline="\n")
    inner_repo_rows = [*inner_artifact_rows, f"{sha(staged_output / 'ARTIFACT_SHA256SUMS.txt')}  ARTIFACT_SHA256SUMS.txt"]
    (staged_output / "SHA256SUMS.txt").write_text("\n".join(sorted(inner_repo_rows)) + "\n", encoding="utf-8", newline="\n")
    docs = [
        "README.md", "docs/current_status.md", "docs/capability_inventory.md", "docs/public_release_readiness.md",
        "controllergate_v1_7_beta/reports/critic_review_package/shareable_summary.md",
    ]
    for relative in docs:
        source = repo / relative
        target = stage / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
    forbidden_suffixes = {".zip", ".pdf", ".whl", ".pyc", ".pyo", ".tar", ".tgz", ".sqlite", ".sqlite3", ".owl"}
    forbidden_files = [str(path) for path in stage.rglob("*") if path.is_file() and path.suffix.lower() in forbidden_suffixes]
    forbidden_dirs = [str(path) for path in stage.rglob("*") if path.is_dir() and path.name in {".git", "__pycache__", "site-packages"}]
    if forbidden_files or forbidden_dirs:
        raise RuntimeError(f"forbidden staged payload: files={forbidden_files} dirs={forbidden_dirs}")
    root_rows = []
    root_manifest = stage / "ARTIFACT_SHA256SUMS.txt"
    for path in sorted(item for item in stage.rglob("*") if item.is_file() and item != root_manifest):
        root_rows.append(f"{sha(path)}  {path.relative_to(stage).as_posix()}")
    root_manifest.write_text("\n".join(root_rows) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({"status": "PASS", "staged_file_count": sum(1 for path in stage.rglob('*') if path.is_file()), "portable_evidence_file_count": len(rows)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
