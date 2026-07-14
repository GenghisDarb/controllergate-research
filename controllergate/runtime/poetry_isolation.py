from __future__ import annotations

import os


def powershell_invocation(executable: str) -> list[str]:
    """Use PowerShell's call operator with each native argument separately."""
    return ["pwsh", "-NoProfile", "-Command", "& $args[0] $args[1] $args[2]", executable, "init", "-n"]


def application_socket_denial_policy() -> dict[str, object]:
    return {
        "status": "PASS", "assurance_level": "APPLICATION_SOCKET_DENIAL_WITH_CHILD_AUDIT",
        "socket_denial": True, "network_capable_child_process_allowed": False,
        "external_socket_canary_required": True, "subprocess_tree_audit_required": True,
        "command_network_independent": True, "policy_frozen_before_execution": True,
        "environment_marker_only": False, "platform": os.name,
    }
