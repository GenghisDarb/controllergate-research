from __future__ import annotations

import argparse
import hashlib
import http.server
import json
import socket
import subprocess
import threading
from functools import partial
from pathlib import Path
from typing import Any


SENTINELS = [
    "CONTAINER_STARTED", "PROVIDER_VERIFIED", "LOOPBACK_INTERFACE_VERIFIED", "LOCAL_SERVER_STARTED",
    "LOCAL_SERVER_READY", "EXTERNAL_DNS_BLOCKED", "EXTERNAL_IP_BLOCKED", "GENERATE_SPEC_STARTED",
    "GENERATE_SPEC_COMPLETED", "GENERATE_EXTENSION_STARTED", "GENERATE_EXTENSION_COMPLETED",
    "LOCAL_SERVER_STOPPED", "CONTAINER_COMPLETED",
]


def _run(command: list[str], cwd: Path) -> dict[str, Any]:
    result = subprocess.run(command, cwd=cwd, text=True, capture_output=True, timeout=300, check=False)
    raw = (result.stdout + result.stderr).encode("utf-8", errors="replace")
    return {"command": command, "returncode": result.returncode, "log_sha256": hashlib.sha256(raw).hexdigest(), "log_tail": raw.decode(errors="replace")[-5000:]}


def execute(executable: Path, snapshot: Path, workspace: Path) -> dict[str, Any]:
    observed = ["CONTAINER_STARTED"]
    provider = _run([str(executable), "--help"], workspace)
    if provider["returncode"] == 0:
        observed.append("PROVIDER_VERIFIED")
    command_authority = "--generate-spec" in provider["log_tail"] and "--generate-extension" in provider["log_tail"]
    loopback_listener = socket.socket()
    loopback_listener.bind(("127.0.0.1", 0))
    port = loopback_listener.getsockname()[1]
    loopback_listener.listen(1)
    client = socket.create_connection(("127.0.0.1", port), timeout=2)
    server_side, _ = loopback_listener.accept(); client.close(); server_side.close(); loopback_listener.close()
    observed.append("LOOPBACK_INTERFACE_VERIFIED")
    dns_blocked = False
    try:
        socket.getaddrinfo("example.com", 443)
    except OSError:
        dns_blocked = True
    ip_blocked = False
    try:
        socket.create_connection(("1.1.1.1", 53), timeout=2).close()
    except OSError:
        ip_blocked = True
    if dns_blocked: observed.append("EXTERNAL_DNS_BLOCKED")
    if ip_blocked: observed.append("EXTERNAL_IP_BLOCKED")
    route_text = Path("/proc/net/route").read_text(encoding="utf-8") if Path("/proc/net/route").is_file() else ""
    default_external_route = any(line.split()[1] == "00000000" for line in route_text.splitlines()[1:] if len(line.split()) > 1)
    handler = partial(http.server.SimpleHTTPRequestHandler, directory=str(snapshot))
    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler); observed.append("LOCAL_SERVER_STARTED")
    thread = threading.Thread(target=server.serve_forever, daemon=True); thread.start()
    try:
        socket.create_connection(("127.0.0.1", server.server_port), timeout=2).close(); observed.append("LOCAL_SERVER_READY")
        origin = f"http://127.0.0.1:{server.server_port}"
        spec = workspace / "eodhd.spec"; extension = workspace / "openbb-eodhd"
        observed.append("GENERATE_SPEC_STARTED")
        generate_spec = _run([str(executable), "--generate-spec", "--server", origin, "--openapi-path", "/openapi.yaml", "--output", str(spec)], workspace)
        observed.append("GENERATE_SPEC_COMPLETED")
        if spec.is_file():
            observed.append("GENERATE_EXTENSION_STARTED")
            generate_extension = _run([str(executable), "--generate-extension", "--spec", str(spec), "--provider-name", "eodhd", "--output", str(extension)], workspace)
            observed.append("GENERATE_EXTENSION_COMPLETED")
        else:
            generate_extension = {"command": [], "returncode": None, "log_sha256": None, "log_tail": "spec absent"}
    finally:
        server.shutdown(); thread.join(timeout=5); server.server_close(); observed.append("LOCAL_SERVER_STOPPED")
    counts = {"commands": 0, "providers": 0, "routers": 0, "fetchers": 0}
    parsed = None
    if spec.is_file():
        try:
            parsed = json.loads(spec.read_text(encoding="utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            parsed = None
    stack = [parsed]
    while stack:
        item = stack.pop()
        if isinstance(item, dict):
            for key, child in item.items():
                normalized = key.lower()
                for name in counts:
                    if normalized in {name, name[:-1]}:
                        counts[name] += len(child) if isinstance(child, (dict, list)) else int(child is not None)
                stack.append(child)
        elif isinstance(item, list): stack.extend(item)
    observed.append("CONTAINER_COMPLETED")
    contract = provider["returncode"] == 0 and dns_blocked and ip_blocked and not default_external_route and set(SENTINELS).issubset(observed)
    incident = contract and generate_spec["returncode"] == 0 and generate_extension["returncode"] == 0 and counts["commands"] == 0
    return {
        "status": "CANDIDATE_FAILURE_REPRODUCED" if incident else ("LEGAL_NONINCIDENT_OUTCOME" if contract else "BLOCKED_EXACT_WITH_NEW_EVIDENCE"),
        "contract_pass": contract, "incident_reproduced": incident, "sentinels": observed, "missing_sentinels": sorted(set(SENTINELS) - set(observed)),
        "provider_probe": provider, "command_authority_verified": command_authority,
        "external_dns_blocked": dns_blocked, "external_ip_blocked": ip_blocked,
        "default_external_route": default_external_route, "generate_spec": generate_spec, "generate_extension": generate_extension,
        "spec_sha256": hashlib.sha256(spec.read_bytes()).hexdigest() if spec.is_file() else None,
        "exact_blocker": None if contract else ("openbb_provider_command_authority_mismatch" if not command_authority else "docker_network_none_execution_contract_incomplete"),
        **counts,
    }


def main() -> int:
    parser = argparse.ArgumentParser(); parser.add_argument("--executable", required=True); parser.add_argument("--snapshot", required=True); parser.add_argument("--workspace", required=True); parser.add_argument("--result", required=True)
    args = parser.parse_args(); result = execute(Path(args.executable), Path(args.snapshot), Path(args.workspace))
    Path(args.result).write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    return 0


if __name__ == "__main__": raise SystemExit(main())
