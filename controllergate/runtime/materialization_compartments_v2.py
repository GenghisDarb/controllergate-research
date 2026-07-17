from __future__ import annotations

import hashlib
import os
import shutil
from dataclasses import asdict, dataclass
from enum import Enum
from pathlib import Path
from typing import Iterable


class Compartment(str, Enum):
    SOURCE_VAULT = "SOURCE_VAULT"
    BUILD_WORKSPACE = "BUILD_WORKSPACE"
    PROVIDER_STORE = "PROVIDER_STORE"
    EXECUTION_WORKSPACE = "EXECUTION_WORKSPACE"
    CONSUMER_OR_TARGET_WORKSPACE = "CONSUMER_OR_TARGET_WORKSPACE"
    TRUTH_AND_OUTCOME_VAULT = "TRUTH_AND_OUTCOME_VAULT"


GENERATED_NAMES = {".coverage", ".pytest_cache", "__pycache__", "build", "dist", ".tox", ".nox"}
GENERATED_SUFFIXES = (".pyc", ".pyo", ".egg-info", ".dist-info")


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def tracked_manifest(root: Path, tracked_paths: Iterable[str]) -> dict[str, str]:
    result: dict[str, str] = {}
    for raw in sorted(set(tracked_paths)):
        relative = Path(raw)
        path = root / relative
        if path.is_file():
            result[relative.as_posix()] = file_sha256(path)
        else:
            result[relative.as_posix()] = "MISSING"
    return result


def compare_tracked(before: dict[str, str], after: dict[str, str]) -> dict[str, object]:
    paths = sorted(set(before) | set(after))
    changes = [{"path": path, "before": before.get(path), "after": after.get(path)} for path in paths if before.get(path) != after.get(path)]
    return {"changed_paths": changes, "tracked_mutation_count": len(changes), "status": "PASS" if not changes else "BLOCK"}


def generated_residue(root: Path, tracked_paths: Iterable[str] = ()) -> list[dict[str, object]]:
    tracked = {Path(path).as_posix() for path in tracked_paths}
    rows: list[dict[str, object]] = []
    if not root.exists():
        return rows
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        relative = path.relative_to(root).as_posix()
        parts = set(path.relative_to(root).parts)
        generated = bool(parts & GENERATED_NAMES) or path.name.endswith(GENERATED_SUFFIXES)
        if generated and relative not in tracked:
            rows.append({"path": relative, "sha256": file_sha256(path), "tracked": False, "classification": "GENERATED_RESIDUE"})
    return rows


@dataclass(frozen=True)
class CompartmentReceipt:
    candidate_id: str
    compartment: str
    path: str
    parent_identity: str | None
    writable: bool
    purpose: str

    def record(self) -> dict[str, object]:
        return asdict(self)


def materialize_build_copy(source_vault: Path, build_workspace: Path) -> None:
    if build_workspace.exists():
        raise FileExistsError(build_workspace)
    shutil.copytree(source_vault, build_workspace, symlinks=True, ignore=shutil.ignore_patterns(".git", "__pycache__", ".pytest_cache", "*.pyc"))


def enforce_disjoint(paths: Iterable[Path]) -> None:
    resolved = [path.resolve() for path in paths]
    if len(resolved) != len(set(resolved)):
        raise ValueError("materialization compartments must be distinct")
    for index, left in enumerate(resolved):
        for right in resolved[index + 1 :]:
            if left in right.parents or right in left.parents:
                raise ValueError("materialization compartments must not nest")


def readonly_tree(root: Path) -> None:
    for path in root.rglob("*"):
        if path.is_file():
            os.chmod(path, 0o444)
