from __future__ import annotations

import socket

from controllergate.runtime.openbb_docker_supervisor import SENTINELS


def test_network_none_supervisor_contract_requires_same_container_sentinels():
    assert SENTINELS[0] == "CONTAINER_STARTED"
    assert "LOCAL_SERVER_READY" in SENTINELS
    assert "EXTERNAL_DNS_BLOCKED" in SENTINELS
    assert "EXTERNAL_IP_BLOCKED" in SENTINELS
    assert SENTINELS[-1] == "CONTAINER_COMPLETED"
