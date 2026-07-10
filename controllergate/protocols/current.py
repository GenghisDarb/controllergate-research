from __future__ import annotations

from .v2_16 import protocol


def current_protocol() -> dict[str, str]:
    return protocol()
