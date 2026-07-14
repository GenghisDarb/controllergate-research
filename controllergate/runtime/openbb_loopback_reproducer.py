from __future__ import annotations

import argparse
import hashlib
import http.server
import json
import subprocess
import threading
from functools import partial
from pathlib import Path
from typing import Any


def _run(command: list[str], cwd: Path) -> dict[str, Any]:
    result = subprocess.run(command, cwd=cwd, text=True, capture_output=True, timeout=300)
    raw = (result.stdout + result.stderr).encode()
    return {
        "command": command,
        "returncode": result.returncode,
        "log_hash": hashlib.sha256(raw).hexdigest(),
        "log_tail": raw.decode(errors="replace")[-3000:],
    }


def _key_counts(value: Any) -> dict[str, int]:
    counts = {"commands": 0, "providers": 0, "routers": 0, "fetchers": 0}
    stack = [value]
    while stack:
        item = stack.pop()
        if isinstance(item, dict):
            for key, child in item.items():
                normalized = str(key).lower()
                for name in counts:
                    if normalized in {name, name[:-1]}:
                        counts[name] += len(child) if isinstance(child, (dict, list)) else int(child is not None)
                stack.append(child)
        elif isinstance(item, list):
            stack.extend(item)
    return counts


def execute(executable: Path, snapshot: Path, workspace: Path) -> dict[str, Any]:
    workspace.mkdir(parents=True, exist_ok=True)
    loopback = subprocess.run(["ip", "link", "set", "lo", "up"], text=True, capture_output=True)
    if loopback.returncode:
        return {
            "status": "BLOCKED_EXACT_WITH_NEW_EVIDENCE",
            "exact_blocker": "linux_isolated_loopback_activation_failed",
            "loopback_returncode": loopback.returncode,
            "loopback_log_hash": hashlib.sha256((loopback.stdout + loopback.stderr).encode()).hexdigest(),
        }

    handler = partial(http.server.SimpleHTTPRequestHandler, directory=str(snapshot))
    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        origin = f"http://127.0.0.1:{server.server_port}"
        spec = workspace / "eodhd.spec"
        extension = workspace / "openbb-eodhd"
        generate_spec = _run(
            [str(executable), "--generate-spec", "--server", origin, "--openapi-path", "/openapi.yaml", "--output", str(spec)],
            workspace,
        )
        generate_extension = (
            _run(
                [str(executable), "--generate-extension", "--spec", str(spec), "--provider-name", "eodhd", "--output", str(extension)],
                workspace,
            )
            if generate_spec["returncode"] == 0 and spec.is_file()
            else {"command": [], "returncode": None, "log_hash": None, "log_tail": "not run because spec generation did not produce a file"}
        )
    finally:
        server.shutdown()
        thread.join(timeout=5)
        server.server_close()

    parsed: Any = {}
    parse_error: str | None = None
    if spec.is_file():
        try:
            parsed = json.loads(spec.read_text(encoding="utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            parse_error = f"{type(exc).__name__}:{exc}"
    counts = _key_counts(parsed)
    operation_succeeded = generate_spec["returncode"] == 0 and generate_extension["returncode"] == 0
    incident = operation_succeeded and parse_error is None and counts["commands"] == 0
    return {
        "status": "CANDIDATE_FAILURE_REPRODUCED" if incident else "LEGAL_NONINCIDENT_OUTCOME",
        "incident_reproduced": incident,
        "operation_succeeded": operation_succeeded,
        "loopback_only": True,
        "external_egress_namespace": "denied_by_linux_network_namespace",
        "generate_spec": generate_spec,
        "generate_extension": generate_extension,
        "spec_exists": spec.is_file(),
        "spec_sha256": hashlib.sha256(spec.read_bytes()).hexdigest() if spec.is_file() else None,
        "bounded_parse_error": parse_error,
        **counts,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--executable", required=True)
    parser.add_argument("--snapshot", required=True)
    parser.add_argument("--workspace", required=True)
    parser.add_argument("--result", required=True)
    args = parser.parse_args()
    result = execute(Path(args.executable), Path(args.snapshot), Path(args.workspace))
    Path(args.result).write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
