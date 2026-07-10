from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
from typing import Any

from .container_evidence import inspect_security_observation
from .resource_policy import ResourcePolicy


def docker_available() -> dict[str, Any]:
    completed = subprocess.run(["docker", "version", "--format", "{{json .Server}}"], text=True, capture_output=True, check=False)
    return {"status": "PASS" if completed.returncode == 0 and completed.stdout.strip() not in {"", "null"} else "BLOCK", "returncode": completed.returncode, "server_record": completed.stdout.strip(), "error": completed.stderr.strip(), "runtime": "docker"}


def pull_and_resolve_image(image_tag: str, *, timeout_seconds: int = 300) -> dict[str, Any]:
    pull = subprocess.run(["docker", "pull", image_tag], text=True, capture_output=True, timeout=timeout_seconds, check=False)
    if pull.returncode != 0:
        return {"status": "BLOCK", "image_tag": image_tag, "blocker": "exact_runtime_image_unavailable", "pull_returncode": pull.returncode, "pull_output_tail": (pull.stdout + pull.stderr)[-1600:]}
    inspect = subprocess.run(["docker", "image", "inspect", image_tag], text=True, capture_output=True, check=False)
    if inspect.returncode != 0:
        return {"status": "BLOCK", "image_tag": image_tag, "blocker": "image_identity_inspection_failed"}
    data = json.loads(inspect.stdout)[0]
    digests = data.get("RepoDigests") or []
    if not digests:
        return {"status": "BLOCK", "image_tag": image_tag, "blocker": "immutable_image_digest_missing"}
    return {"status": "PASS", "image_tag": image_tag, "image_digest_reference": digests[0], "image_id": data.get("Id"), "architecture": data.get("Architecture"), "os": data.get("Os")}


def host_nonroot_user() -> str:
    if os.name == "nt":
        return "65532:65532"
    return f"{os.getuid()}:{os.getgid()}"


def secure_container_create_command(
    *, image_digest: str, source: Path, wheelhouse: Path, command: list[str], name: str,
    resource_policy: ResourcePolicy | None = None, environment: dict[str, str] | None = None,
) -> tuple[list[str], str]:
    policy = resource_policy or ResourcePolicy()
    user = host_nonroot_user()
    args = [
        "docker", "create", "--name", name,
        "--user", user, "--read-only", "--cap-drop", "ALL",
        "--security-opt", "no-new-privileges", "--network", "none",
        "--tmpfs", "/tmp:rw,noexec,nosuid,size=256m",
        "--tmpfs", "/venv:rw,exec,nosuid,size=1024m",
        "--mount", f"type=bind,src={source.resolve()},dst=/source,readonly",
        "--mount", f"type=bind,src={wheelhouse.resolve()},dst=/wheelhouse,readonly",
        "--workdir", "/source",
        "--env", "PYTHONDONTWRITEBYTECODE=1",
        "--env", "HOME=/tmp/home",
        "--env", "XDG_CACHE_HOME=/tmp/cache",
    ]
    for key, value in sorted((environment or {}).items()):
        args.extend(["--env", f"{key}={value}"])
    args.extend([*policy.docker_args(), image_digest, *command])
    return args, user


def create_inspect_run_remove(
    *, image_digest: str, source: Path, wheelhouse: Path, shell_script: str, name: str,
    resource_policy: ResourcePolicy | None = None, environment: dict[str, str] | None = None,
) -> dict[str, Any]:
    policy = resource_policy or ResourcePolicy()
    command, user = secure_container_create_command(image_digest=image_digest, source=source, wheelhouse=wheelhouse, command=["sh", "-lc", shell_script], name=name, resource_policy=policy, environment=environment)
    create = subprocess.run(command, text=True, capture_output=True, check=False)
    if create.returncode != 0:
        return {"status": "BLOCK", "blocker": "secure_container_create_failed", "create_returncode": create.returncode, "output": (create.stdout + create.stderr)[-2000:], "command": command}
    container_id = create.stdout.strip()
    inspect_raw = subprocess.run(["docker", "inspect", container_id], text=True, capture_output=True, check=False)
    inspect_data = json.loads(inspect_raw.stdout)[0] if inspect_raw.returncode == 0 else {}
    security = inspect_security_observation(inspect_data, expected_user=user)
    if security["status"] != "PASS":
        subprocess.run(["docker", "rm", "-f", container_id], capture_output=True)
        return {"status": "BLOCK", "blocker": "container_security_observation_failed", "container_id": container_id, "security_observation": security, "command": command}
    try:
        run = subprocess.run(["docker", "start", "-a", container_id], text=True, capture_output=True, timeout=policy.timeout_seconds, check=False)
        timed_out = False
    except subprocess.TimeoutExpired as exc:
        run = subprocess.CompletedProcess(["docker", "start", "-a", container_id], 124, stdout=exc.stdout or "", stderr=exc.stderr or "")
        timed_out = True
        subprocess.run(["docker", "kill", container_id], capture_output=True)
    removal = subprocess.run(["docker", "rm", "-f", container_id], text=True, capture_output=True, check=False)
    return {
        "status": "PASS" if run.returncode == 0 else "BLOCK", "blocker": None if run.returncode == 0 else "container_command_failed",
        "container_id": container_id, "security_observation": security, "command": command,
        "returncode": run.returncode, "stdout": run.stdout, "stderr": run.stderr,
        "timed_out": timed_out, "container_removed": removal.returncode == 0,
    }
