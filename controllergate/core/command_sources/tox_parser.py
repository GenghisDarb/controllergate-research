from __future__ import annotations

import configparser
from pathlib import Path
import re
import shlex
from typing import Any


_CONDITION = re.compile(r"^([A-Za-z0-9_{}!,.-]+):\s+(.+)$")


def _split_commands(value: str) -> list[str]:
    return [line.strip() for line in value.splitlines() if line.strip() and not line.lstrip().startswith("#")]


def parse_tox(path: Path) -> dict[str, Any]:
    parser = configparser.ConfigParser(interpolation=None, strict=False)
    parser.optionxform = str
    parser.read(path, encoding="utf-8")
    environments: list[dict[str, Any]] = []
    for section in parser.sections():
        if not section.startswith("testenv"): continue
        values = parser[section]
        commands = []
        for raw in _split_commands(values.get("commands", "")):
            match = _CONDITION.match(raw); condition = match.group(1) if match else None; command = match.group(2) if match else raw
            try: argv = shlex.split(command, posix=True)
            except ValueError: argv = []
            commands.append({"raw": raw, "condition": condition, "argv": argv})
        environments.append({
            "section": section, "environment_name": section.split(":", 1)[1] if ":" in section else "default",
            "base_python": values.get("basepython"), "dependencies": _split_commands(values.get("deps", "")),
            "setenv": _split_commands(values.get("setenv", "")), "working_directory": values.get("changedir", "."),
            "allowlisted_externals": _split_commands(values.get("allowlist_externals", values.get("whitelist_externals", ""))),
            "commands": commands,
        })
    return {"status": "PASS", "source_path": path.as_posix(), "environments": environments}
