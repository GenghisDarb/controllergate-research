from __future__ import annotations

from pathlib import Path
from typing import Any

from controllergate.execution.execution_broker import execute_command


def execute_pathway_step(step: dict[str, Any], *, runtime_root: Path, authorization_id: str):
    return execute_command(argv=list(step["argv"]), cwd=Path(step["cwd"]), runtime_root=runtime_root, stage_id=str(step["stage_id"]), candidate_id=str(step["candidate_id"]), authorization_id=authorization_id, required_sentinels=list(step.get("required_sentinels", [])))
