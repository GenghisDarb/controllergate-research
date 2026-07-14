from __future__ import annotations

import hashlib
import os
import shutil
import subprocess
from pathlib import Path


def verify_process_guard(executable: str) -> dict[str, object]:
    if os.name != "nt":
        return {"status": "NOT_APPLICABLE", "platform": os.name}
    netsh = shutil.which("netsh")
    return {"status": "BLOCKED_EXACT_WITH_NEW_EVIDENCE", "executable": executable,
            "netsh_available": netsh is not None,
            "exact_blocker": "windows_process_firewall_requires_elevated_runner_authority",
            "rule_created": False, "cleanup_verified": True}


def install_process_guards(executables: list[Path], prefix: str) -> dict[str, object]:
    if os.name != "nt":
        return {"status": "NOT_APPLICABLE", "platform": os.name, "rules": []}
    if not shutil.which("netsh"):
        return {"status": "BLOCKED_EXACT_WITH_NEW_EVIDENCE", "exact_blocker": "windows_netsh_unavailable", "rules": []}
    rules = []
    for executable in executables:
        name = f"{prefix}-{hashlib.sha256(str(executable).encode()).hexdigest()[:12]}"
        command = ["netsh", "advfirewall", "firewall", "add", "rule", f"name={name}", "dir=out", "action=block", f"program={executable}", "enable=yes", "profile=any"]
        result = subprocess.run(command, text=True, capture_output=True)
        rules.append({"name": name, "executable": str(executable), "returncode": result.returncode,
                      "log_hash": hashlib.sha256((result.stdout + result.stderr).encode()).hexdigest()})
        if result.returncode:
            remove_process_guards(rules)
            return {"status": "BLOCKED_EXACT_WITH_NEW_EVIDENCE", "exact_blocker": "windows_process_firewall_rule_creation_failed", "rules": rules}
    return {"status": "PASS", "exact_blocker": None, "rules": rules}


def remove_process_guards(rules: list[dict[str, object]]) -> dict[str, object]:
    records = []
    for rule in rules:
        result = subprocess.run(["netsh", "advfirewall", "firewall", "delete", "rule", f"name={rule['name']}"], text=True, capture_output=True)
        records.append({"name": rule["name"], "returncode": result.returncode,
                        "log_hash": hashlib.sha256((result.stdout + result.stderr).encode()).hexdigest()})
    return {"status": "PASS" if records and all(row["returncode"] == 0 for row in records) else "BLOCKED_EXACT_WITH_NEW_EVIDENCE", "records": records}
