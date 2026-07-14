from __future__ import annotations

from dataclasses import dataclass


POLICIES = {"ACQUISITION_NETWORK_ALLOWED", "EXECUTION_ALL_EGRESS_DENIED",
            "EXECUTION_EXTERNAL_EGRESS_DENIED_LOOPBACK_ALLOWED", "PROCESS_FIREWALL_EGRESS_DENIED",
            "APPLICATION_SOCKET_GUARD"}


@dataclass(frozen=True)
class NetworkPolicyV2:
    policy: str
    executable: str | None = None

    def validate(self) -> dict[str, object]:
        return {"status": "PASS" if self.policy in POLICIES else "BLOCK", "policy": self.policy,
                "executable": self.executable}
