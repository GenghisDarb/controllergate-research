from __future__ import annotations

import shutil
import subprocess


def verify_namespace_guard() -> dict[str, object]:
    unshare = shutil.which("unshare")
    if not unshare:
        return {"status": "BLOCKED_EXACT_WITH_NEW_EVIDENCE", "exact_blocker": "linux_unshare_unavailable"}
    command = [unshare, "--net", "python", "-c", "import socket; socket.getaddrinfo('example.com',443)"]
    result = subprocess.run(command, text=True, capture_output=True)
    blocked = result.returncode != 0 and "Operation not permitted" not in result.stderr
    return {"status": "PASS" if blocked else "BLOCKED_EXACT_WITH_NEW_EVIDENCE",
            "external_dns_blocked": blocked, "returncode": result.returncode,
            "exact_blocker": None if blocked else "linux_network_namespace_not_enforceable_in_runner"}
