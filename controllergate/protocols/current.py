from __future__ import annotations

from .v2_15 import protocol


def current_protocol() -> dict[str, str]:
    return protocol()
