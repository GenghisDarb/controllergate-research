from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Iterable


REPO = Path(__file__).resolve().parents[1]
OUTPUT = REPO / "outputs" / "post_v2_37_hardening_batch089_full_isomorphism_reaction_complete_vertical_closure"
PROMPT2_OUTPUT = OUTPUT / "prompt2_signal_cargo_homeostasis"
PROMPT3_OUTPUT = OUTPUT / "prompt3_replication_repair_defense_actuation"
STARTING_HEAD = "e02fb4d3a899dd0a6ccc9eb8fc0e38ab0e4e4e94"


def canonical_bytes(value: Any) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")


def digest(value: Any) -> str:
    raw = value if isinstance(value, bytes) else canonical_bytes(value)
    return hashlib.sha256(raw).hexdigest()


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")


def write_jsonl(path: Path, values: Iterable[Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(value, sort_keys=True) + "\n" for value in values), encoding="utf-8", newline="\n")


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()
