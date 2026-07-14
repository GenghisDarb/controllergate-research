from __future__ import annotations

from controllergate.reactions.stable_identity import stable_hash


def verify_identity(connector_id: str, implementation: str) -> dict[str, object]:
    return {"status": "CONNECTOR_IDENTITY_VERIFIED", "connector_id": connector_id,
            "implementation_hash": stable_hash({"connector_id": connector_id, "implementation": implementation})}
