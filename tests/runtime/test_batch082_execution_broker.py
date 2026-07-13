from __future__ import annotations

import sys
from pathlib import Path

from controllergate.execution.execution_broker import execute_external_operation


def test_external_operation_binds_runtime_and_hash_chain(tmp_path: Path) -> None:
    attestation = {"status": "PASS", "attestation_hash": "a" * 64}
    run, record = execute_external_operation(
        operation_type="diagnostic_probe", argv=[sys.executable, "-c", "print('TARGET_STARTED\\nTARGET_COMPLETED')"],
        cwd=tmp_path, runtime_root=tmp_path, stage_id="probe", candidate_id="candidate",
        authorization_id="auth", runtime_attestation=attestation, platform=sys.platform,
        runtime=sys.version.split()[0], required_sentinels=["TARGET_STARTED", "TARGET_COMPLETED"],
    )
    assert run.returncode == 0
    assert record["runtime_attestation_hash"] == "a" * 64
    assert record["observed_sentinels"] == ["TARGET_STARTED", "TARGET_COMPLETED"]
    assert record["record_hash"]

