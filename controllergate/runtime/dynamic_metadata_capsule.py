from __future__ import annotations

import shutil
import subprocess
from typing import Any


SECURITY_POLICY = {"non_root": True, "read_only_root": True, "read_only_artifact": True, "cap_drop": "ALL", "no_new_privileges": True, "seccomp": "default", "host_pid": False, "host_ipc": False, "docker_socket": False, "host_home": False, "credentials": False, "cpu_limit": "1", "memory_limit": "1g", "pid_limit": 128, "timeout_seconds": 180, "tmpfs_workdir": True, "metadata_network": "none"}


def dynamic_metadata_capability() -> dict[str, Any]:
    docker = shutil.which("docker")
    if not docker: return {"status": "BLOCK", "classification": "dynamic_metadata_build_backend_unresolved", "blocker": "docker_runtime_unavailable", "security_policy": SECURITY_POLICY}
    result = subprocess.run([docker, "version", "--format", "{{.Server.Version}}"], capture_output=True, text=True, timeout=15)
    return {"status": "PASS" if result.returncode == 0 else "BLOCK", "classification": "dynamic_metadata_capsule_available" if result.returncode == 0 else "dynamic_metadata_build_backend_unresolved", "blocker": None if result.returncode == 0 else "docker_daemon_unavailable", "security_policy": SECURITY_POLICY, "docker_server_version": result.stdout.strip()}
