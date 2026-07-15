from __future__ import annotations

import shutil
import sys
from pathlib import Path

from .deep_doctor import deep_doctor


def doctor(runtime_root: str | Path | None = None, *, deep: bool = False, repo_root: str | Path | None = None) -> dict[str, object]:
    root = Path(runtime_root or Path.cwd() / ".controllergate-runtime").resolve()
    prohibited = str(root).upper().startswith("E:\\") or "ONEDRIVE" in str(root).upper()
    result: dict[str, object] = {"status": "PASS" if sys.version_info >= (3, 11) and not prohibited else "BLOCK",
            "python": sys.version, "git_available": shutil.which("git") is not None,
            "runtime_root": str(root), "runtime_root_prohibited": prohibited,
            "write_capable_connectors": "inactive", "current_protocol": "v2.19"}
    if deep:
        report = deep_doctor(Path(repo_root or Path.cwd()))
        result["deep"] = report
        if report["status"] != "PASS":
            result["status"] = "BLOCK"
    return result
