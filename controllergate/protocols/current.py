from __future__ import annotations

from .v2_18_evidence_derived_topology_historical_provider import protocol


def current_protocol() -> dict[str, str]:
    return protocol()
