from __future__ import annotations

from pathlib import Path

from controllergate.execution.execution_broker import execute_command


def run_pytest_collection(*, target: str, source_root: Path, runtime_root: Path, python: str, authorization_id: str):
    return execute_command(argv=[python, "-m", "pytest", target, "--collect-only", "-q"], cwd=source_root, runtime_root=runtime_root, stage_id="pytest_collection_v2", candidate_id=source_root.name, authorization_id=authorization_id, required_sentinels=["COLLECTION_STARTED", "COLLECTION_COMPLETED"])
