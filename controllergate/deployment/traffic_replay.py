from __future__ import annotations

import hashlib
import subprocess
from pathlib import Path


def replay(command: list[str], cwd: Path, timeout: int = 60) -> dict[str, object]:
    result = subprocess.run(command, cwd=cwd, text=True, capture_output=True, timeout=timeout)
    raw = (result.stdout + result.stderr).encode()
    return {"status": "CANARY_TRAFFIC_REPLAYED", "returncode": result.returncode,
            "command": command, "output_hash": hashlib.sha256(raw).hexdigest(),
            "output_bytes": len(raw)}
