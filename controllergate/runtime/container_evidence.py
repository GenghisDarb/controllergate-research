from __future__ import annotations

from typing import Any


def inspect_security_observation(inspect_record: dict[str, Any], *, expected_user: str) -> dict[str, Any]:
    config = inspect_record.get("Config") or {}
    host = inspect_record.get("HostConfig") or {}
    network = host.get("NetworkMode")
    cap_drop = host.get("CapDrop") or []
    security_opt = host.get("SecurityOpt") or []
    mounts = inspect_record.get("Mounts") or []
    errors: list[str] = []
    if str(config.get("User") or "") in {"", "0", "root", "0:0"}: errors.append("container_user_is_root")
    if expected_user and str(config.get("User")) != expected_user: errors.append("container_user_mismatch")
    if host.get("ReadonlyRootfs") is not True: errors.append("root_filesystem_not_read_only")
    if "ALL" not in cap_drop: errors.append("all_capabilities_not_dropped")
    if not any("no-new-privileges" in str(item) for item in security_opt): errors.append("no_new_privileges_missing")
    if network != "none": errors.append("execution_network_not_none")
    if host.get("Privileged") is True: errors.append("privileged_mode_forbidden")
    if host.get("PidMode") in {"host"}: errors.append("host_pid_namespace_forbidden")
    if host.get("IpcMode") in {"host"}: errors.append("host_ipc_namespace_forbidden")
    for mount in mounts:
        source = str(mount.get("Source") or "").lower()
        destination = str(mount.get("Destination") or "")
        if "docker.sock" in source or destination == "/var/run/docker.sock": errors.append("docker_socket_mount_forbidden")
        if destination in {"/root", "/home"} or destination.startswith("/home/"): errors.append("host_home_mount_forbidden")
    return {
        "status": "PASS" if not errors else "BLOCK",
        "errors": errors,
        "observed_user": config.get("User"),
        "non_root_verified": str(config.get("User") or "") not in {"", "0", "root", "0:0"},
        "read_only_root_filesystem_verified": host.get("ReadonlyRootfs") is True,
        "capabilities_dropped_verified": "ALL" in cap_drop,
        "no_new_privileges_verified": any("no-new-privileges" in str(item) for item in security_opt),
        "network_isolation_verified": network == "none",
        "network_mode": network,
        "privileged": bool(host.get("Privileged")),
        "pid_mode": host.get("PidMode"),
        "ipc_mode": host.get("IpcMode"),
        "memory_bytes": host.get("Memory"),
        "memory_swap_bytes": host.get("MemorySwap"),
        "pids_limit": host.get("PidsLimit"),
        "nano_cpus": host.get("NanoCpus"),
        "ulimits": host.get("Ulimits") or [],
        "mounts": [{"Destination": item.get("Destination"), "Mode": item.get("Mode"), "RW": item.get("RW")} for item in mounts],
    }
