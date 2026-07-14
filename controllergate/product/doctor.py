from __future__ import annotations

import shutil
import sys
from pathlib import Path


def doctor(runtime_root: str | Path | None = None) -> dict[str, object]:
    root = Path(runtime_root or Path.cwd() / ".controllergate-runtime").resolve()
    prohibited = str(root).upper().startswith("E:\\") or "ONEDRIVE" in str(root).upper()
    return {"status": "PASS" if sys.version_info >= (3, 11) and not prohibited else "BLOCK",
            "python": sys.version, "git_available": shutil.which("git") is not None,
            "runtime_root": str(root), "runtime_root_prohibited": prohibited,
            "write_capable_connectors": "inactive", "current_protocol": "v2.19"}
