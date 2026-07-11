from __future__ import annotations

from pathlib import Path
import shlex
from typing import Any


def parse_ci(path: Path) -> dict[str, Any]:
    commands = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        stripped = line.strip()
        if stripped.startswith("run:"):
            raw = stripped.split(":", 1)[1].strip().strip("'\"")
            if raw and raw not in {"|", ">"}:
                try: argv = shlex.split(raw)
                except ValueError: argv = []
                commands.append({"line": line_number, "argv": argv})
    return {"status": "PASS", "source_path": path.as_posix(), "commands": commands}
