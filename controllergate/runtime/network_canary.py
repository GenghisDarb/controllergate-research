from __future__ import annotations

import socket


def external_canary(host: str = "1.1.1.1", port: int = 443, timeout: float = 0.5) -> dict[str, object]:
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return {"status": "EGRESS_REACHABLE", "host": host, "port": port}
    except OSError as exc:
        return {"status": "EGRESS_BLOCKED", "host": host, "port": port, "error_class": type(exc).__name__}


def dns_canary(host: str = "example.com") -> dict[str, object]:
    try:
        socket.getaddrinfo(host, 443)
        return {"status": "DNS_REACHABLE", "host": host}
    except OSError as exc:
        return {"status": "DNS_BLOCKED", "host": host, "error_class": type(exc).__name__}
