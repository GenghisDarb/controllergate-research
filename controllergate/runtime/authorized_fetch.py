from __future__ import annotations

import hashlib
import ssl
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import HTTPRedirectHandler, HTTPSHandler, Request, build_opener

from .network_authorization import authorize_network_operation
from .network_event_ledger import append_network_event


class _PolicyRedirectHandler(HTTPRedirectHandler):
    def __init__(self, allowed_hosts: set[str]): self.allowed_hosts = allowed_hosts
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        if urlparse(newurl).hostname not in self.allowed_hosts or urlparse(newurl).scheme != "https": raise HTTPError(newurl, code, "unauthorized redirect", headers, fp)
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def authorized_fetch(*, url: str, destination: Path, phase_id: str, policy: dict[str, Any], ledger_path: Path, expected_sha256: str | None = None, timeout: int = 120, budget_state: dict[str, int] | None = None) -> dict[str, Any]:
    state = budget_state if budget_state is not None else {"requests": 0, "bytes": 0}
    auth = authorize_network_operation(phase_id=phase_id, policy=policy, destination=url, requested_mode="bounded_read_only", projected_requests=state["requests"] + 1, projected_bytes=state["bytes"])
    if auth["status"] != "PASS": return auth
    opener = build_opener(_PolicyRedirectHandler(set(policy["allowed_network_destinations"])), HTTPSHandler(context=ssl.create_default_context()))
    status = "BLOCK"; blocker = None; payload = b""; http_status = None
    try:
        with opener.open(Request(url, headers={"User-Agent": "ControllerGate/Batch068h8"}), timeout=timeout) as response:
            http_status = getattr(response, "status", 200); payload = response.read(int(policy["maximum_download_bytes"]) - state["bytes"] + 1)
        if state["bytes"] + len(payload) > int(policy["maximum_download_bytes"]): blocker = "network_byte_budget_exceeded"
        elif expected_sha256 and hashlib.sha256(payload).hexdigest() != expected_sha256: blocker = "download_checksum_mismatch"
        else:
            destination.parent.mkdir(parents=True, exist_ok=True); destination.write_bytes(payload); status = "PASS"
    except HTTPError as exc: http_status = exc.code; blocker = "network_http_error"
    except (URLError, TimeoutError, ssl.SSLError) as exc: blocker = type(exc).__name__
    state["requests"] += 1; state["bytes"] += len(payload)
    event = append_network_event(ledger_path, {"phase_id": phase_id, "url": url, "host": urlparse(url).hostname, "status": status, "blocker": blocker, "http_status": http_status, "bytes": len(payload), "sha256": hashlib.sha256(payload).hexdigest() if payload else None, "tls_verification": True})
    return {"status": status, "blocker": blocker, "url": url, "destination": str(destination), "bytes": len(payload), "sha256": event.get("sha256"), "http_status": http_status, "network_event_hash": event["event_hash"]}
