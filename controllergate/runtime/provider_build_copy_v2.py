from __future__ import annotations

import shutil
from pathlib import Path

from .provider_plan_v4 import immutable_source_hash


def create_build_copy(source: Path, destination: Path) -> dict[str, object]:
    before = immutable_source_hash(source)
    if destination.exists():
        shutil.rmtree(destination)
    shutil.copytree(source, destination, ignore=shutil.ignore_patterns(".git", "__pycache__", "*.pyc"))
    after_source = immutable_source_hash(source)
    return {"state": "PROVIDER_BUILD_COPY_CREATED" if before == after_source else "BLOCK",
            "source_hash_before": before, "source_hash_after": after_source,
            "build_copy_hash": immutable_source_hash(destination), "build_copy": str(destination)}
