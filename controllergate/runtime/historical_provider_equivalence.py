from __future__ import annotations

import hashlib
import json
import zipfile
from pathlib import Path
from typing import Any

from controllergate.state.integrity import canonical_hash


IGNORED_WHEEL_MEMBERS = ("/RECORD",)


def normalized_wheel_record(path: str | Path) -> dict[str, str]:
    wheel = Path(path)
    with zipfile.ZipFile(wheel) as archive:
        return {
            name: hashlib.sha256(archive.read(name)).hexdigest()
            for name in sorted(archive.namelist())
            if not any(name.endswith(suffix) for suffix in IGNORED_WHEEL_MEMBERS)
        }


def compare_independent_builds(first: str | Path, second: str | Path) -> dict[str, Any]:
    left = normalized_wheel_record(first)
    right = normalized_wheel_record(second)
    differing = sorted(name for name in set(left) | set(right) if left.get(name) != right.get(name))
    return {
        "status": "PASS" if not differing else "BLOCK",
        "normalized_first_hash": canonical_hash(left),
        "normalized_second_hash": canonical_hash(right),
        "normalized_contents_equivalent": not differing,
        "non_reproducible_fields": differing,
        "raw_first_sha256": hashlib.sha256(Path(first).read_bytes()).hexdigest(),
        "raw_second_sha256": hashlib.sha256(Path(second).read_bytes()).hexdigest(),
    }


def compare_installed_graphs(first: list[dict[str, Any]], second: list[dict[str, Any]]) -> dict[str, Any]:
    normalized_first = sorted((str(row["name"]).casefold(), str(row["version"])) for row in first)
    normalized_second = sorted((str(row["name"]).casefold(), str(row["version"])) for row in second)
    return {
        "status": "PASS" if normalized_first == normalized_second else "BLOCK",
        "equivalent": normalized_first == normalized_second,
        "first_graph_hash": canonical_hash(normalized_first),
        "second_graph_hash": canonical_hash(normalized_second),
    }
