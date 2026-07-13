from __future__ import annotations

import hashlib
import json
from typing import Any


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def state_hash(value: Any) -> str:
    return hashlib.sha256(canonical_bytes(value)).hexdigest()


def stable_identity(namespace: str, value: Any, *, version: int = 1) -> str:
    digest = state_hash({"namespace": namespace, "value": value, "version": version})
    return f"{namespace}:v{version}:{digest[:24]}"


def contextual_identity(underlying_identity: str, compartment: str, role: str) -> str:
    return stable_identity("context", {"underlying_identity": underlying_identity, "compartment": compartment, "role": role})


def versioned_identity_record(namespace: str, value: Any, *, version: int, historical_aliases: tuple[str, ...] = (), replacement_identity: str | None = None, release_membership: str = "batch077") -> dict[str, Any]:
    object_identity = state_hash({"namespace": namespace, "instance": value})
    stable_public_identity = stable_identity(namespace, value, version=version)
    return {
        "object_identity": object_identity,
        "stable_public_identity": stable_public_identity,
        "identity_version": version,
        "historical_aliases": list(historical_aliases),
        "replacement_identity": replacement_identity,
        "release_membership": release_membership,
    }
