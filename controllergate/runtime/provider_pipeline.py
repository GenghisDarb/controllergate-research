from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
from typing import Any

from .oci_probe_sandbox import host_nonroot_user
from .resource_policy import ResourcePolicy


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def resolve_wheelhouse(
    *, image_digest: str, source: Path, wheelhouse: Path, requirement: str,
    resource_policy: ResourcePolicy | None = None,
) -> dict[str, Any]:
    policy = resource_policy or ResourcePolicy(timeout_seconds=300)
    wheelhouse.mkdir(parents=True, exist_ok=True)
    user = host_nonroot_user()
    name = "controllergate-resolver-" + hashlib.sha256(str(source).encode()).hexdigest()[:12]
    script = f"python -m pip wheel --disable-pip-version-check --wheel-dir /wheelhouse '{requirement}'"
    command = [
        "docker", "create", "--name", name, "--user", user, "--read-only",
        "--cap-drop", "ALL", "--security-opt", "no-new-privileges",
        "--network", "bridge", "--tmpfs", "/tmp:rw,exec,nosuid,size=1024m",
        "--mount", f"type=bind,src={source.resolve()},dst=/source,readonly",
        "--mount", f"type=bind,src={wheelhouse.resolve()},dst=/wheelhouse",
        "--workdir", "/source", *policy.docker_args(), image_digest, "sh", "-lc", script,
    ]
    started = utc_now()
    create = subprocess.run(command, text=True, capture_output=True, check=False)
    if create.returncode != 0:
        return {"status": "BLOCK", "blocker": "provider_resolver_container_create_failed", "command": command, "returncode": create.returncode, "output_tail": (create.stdout + create.stderr)[-2000:], "network_start": started, "network_stop": utc_now()}
    container_id = create.stdout.strip()
    inspect = subprocess.run(["docker", "inspect", container_id], text=True, capture_output=True, check=False)
    inspect_data = json.loads(inspect.stdout)[0] if inspect.returncode == 0 else {}
    try:
        run = subprocess.run(["docker", "start", "-a", container_id], text=True, capture_output=True, timeout=policy.timeout_seconds, check=False)
    except subprocess.TimeoutExpired as exc:
        run = subprocess.CompletedProcess([], 124, stdout=exc.stdout or "", stderr=exc.stderr or "")
        subprocess.run(["docker", "kill", container_id], capture_output=True)
    stopped = utc_now()
    subprocess.run(["docker", "rm", "-f", container_id], capture_output=True)
    archives = []
    for path in sorted(wheelhouse.iterdir()):
        if path.is_file():
            archives.append({"filename": path.name, "sha256": hashlib.sha256(path.read_bytes()).hexdigest(), "size": path.stat().st_size, "archive_type": "wheel" if path.suffix == ".whl" else "source_distribution"})
    return {
        "status": "PASS" if run.returncode == 0 and archives else "BLOCK",
        "blocker": None if run.returncode == 0 and archives else "provider_resolution_failure",
        "strategy_id": "declared_test_extra_wheel_resolution_v1",
        "resolver_container_id": container_id, "resolver_execution_container_reused": False,
        "command": command, "returncode": run.returncode, "output_tail": (run.stdout + run.stderr)[-4000:],
        "network_start": started, "network_stop": stopped, "network_authorization_reason": "declared provider archive resolution only",
        "candidate_test_execution_allowed": False, "container_inspect": inspect_data, "archives": archives,
    }


def verify_archive_manifest(wheelhouse: Path, archives: list[dict[str, Any]]) -> dict[str, Any]:
    failures = []
    for item in archives:
        path = wheelhouse / item["filename"]
        if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != item["sha256"]:
            failures.append(item["filename"])
    return {"status": "PASS" if not failures else "BLOCK", "checked": len(archives), "failures": failures}


def parse_inventory_markers(output: str) -> dict[str, Any]:
    records: dict[str, Any] = {}
    for line in output.splitlines():
        if line.startswith("CG_") and "=" in line:
            key, value = line.split("=", 1)
            try:
                records[key] = json.loads(value)
            except json.JSONDecodeError:
                records[key] = value
    return records
