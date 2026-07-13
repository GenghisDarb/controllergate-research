from __future__ import annotations

from pathlib import Path

from controllergate.execution.execution_broker import execute_command


def execute_reproducer(*, argv: list[str], workspace: Path, runtime_root: Path, candidate_id: str, authorization_id: str):
    return execute_command(argv=argv, cwd=workspace, runtime_root=runtime_root, stage_id="issue_reproducer", candidate_id=candidate_id, authorization_id=authorization_id, required_sentinels=["TARGET_STARTED", "TARGET_COMPLETED"])
