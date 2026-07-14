from __future__ import annotations

import hashlib
from pathlib import Path


def translocate(source: Path, destination: Path, *, artifact_identity: str,
                transformation: str = "byte_preserving_copy") -> dict[str, object]:
    before = hashlib.sha256(source.read_bytes()).hexdigest()
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(source.read_bytes())
    after = hashlib.sha256(destination.read_bytes()).hexdigest()
    return {"status": "PASS" if before == after else "BLOCK", "source": str(source.resolve()),
            "destination": str(destination.resolve()), "source_hash": before, "destination_hash": after,
            "artifact_identity": artifact_identity, "declared_transformation": transformation,
            "unexpected_mutation_count": 0 if before == after else 1, "translocation_verifier": "sha256"}
