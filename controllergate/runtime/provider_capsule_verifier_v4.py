from __future__ import annotations

import hashlib
from pathlib import Path

from controllergate.reactions.stable_identity import stable_hash


def verify_provider(wheel_dir: Path, seal: dict[str, object]) -> dict[str, object]:
    valid = all((wheel_dir / row["path"]).is_file() and
                hashlib.sha256((wheel_dir / row["path"]).read_bytes()).hexdigest() == row["sha256"]
                for row in seal.get("wheels", []))
    source = {key: value for key, value in seal.items() if key != "provider_seal"}
    valid = valid and stable_hash(source) == seal.get("provider_seal")
    return {"status": "PASS" if valid else "BLOCK", "provider_seal": seal.get("provider_seal"),
            "wheel_count": len(seal.get("wheels", []))}
