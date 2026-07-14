from __future__ import annotations

import json
from pathlib import Path

from .historical_provider_manifest import HistoricalProviderManifest


class HistoricalProviderRegistry:
    def __init__(self, path: str | Path):
        value = json.loads(Path(path).read_text(encoding="utf-8"))
        manifests = [HistoricalProviderManifest.from_record(item) for item in value.get("episodes", [])]
        self._by_id = {manifest.candidate_id: manifest for manifest in manifests}
        if len(self._by_id) != len(manifests):
            raise ValueError("historical provider candidate IDs must be unique")

    def get(self, candidate_id: str) -> HistoricalProviderManifest:
        try:
            return self._by_id[candidate_id]
        except KeyError as exc:
            raise KeyError(f"historical provider not registered: {candidate_id}") from exc

    def identities(self) -> dict[str, str]:
        return {candidate_id: manifest.identity for candidate_id, manifest in sorted(self._by_id.items())}
