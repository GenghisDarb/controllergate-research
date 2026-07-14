from __future__ import annotations

from .read_only import read_json


API = "https://api.github.com/"


def read_frozen_resource(path: str) -> dict[str, object]:
    return read_json(API + path.lstrip("/"), allowed=(API,))
