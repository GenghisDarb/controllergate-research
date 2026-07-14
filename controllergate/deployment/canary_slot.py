from __future__ import annotations

import hashlib
import shutil
from pathlib import Path


def materialize_slot(source: Path, destination: Path) -> dict[str, object]:
    if destination.exists():
        shutil.rmtree(destination)
    shutil.copytree(source, destination)
    identities = {str(p.relative_to(destination)): hashlib.sha256(p.read_bytes()).hexdigest()
                  for p in destination.rglob("*") if p.is_file()}
    return {"status": "CANARY_SLOT_MATERIALIZED", "slot": str(destination), "file_identities": identities}
