from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ReproducerContract:
    candidate_id: str
    issue_snapshot_hash: str
    source_commit: str
    platform: str
    command: tuple[str, ...]
    external_workspace: str
    network_policy: str = "none"
