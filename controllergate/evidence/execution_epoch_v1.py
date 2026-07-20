"""Execution epoch identities used to distinguish new operations from replayed evidence."""

from __future__ import annotations

import re


BATCH102_FRESH_OPERATION = "BATCH102_FRESH_OPERATION"
BATCH103_FRESH_OPERATION = "BATCH103_FRESH_OPERATION"
INHERITED_EXECUTION_EPOCHS = {
    "BATCH100_RAW_EXECUTION",
    "BATCH100_INHERITED_RAW_EXECUTION_BATCH101_REPROJECTION",
    "BATCH101_SEMANTIC_REPROJECTION",
}
_SHA40 = re.compile(r"^[0-9a-f]{40}$")


def validate_execution_epoch(epoch: str, workflow_head: str) -> list[str]:
    blockers: list[str] = []
    if epoch != BATCH102_FRESH_OPERATION:
        blockers.append("not_batch102_fresh_operation")
    if epoch in INHERITED_EXECUTION_EPOCHS:
        blockers.append("inherited_execution_rejected")
    if not _SHA40.fullmatch(str(workflow_head)):
        blockers.append("invalid_workflow_head")
    return blockers


def validate_batch103_execution_epoch(epoch: str, workflow_head: str) -> list[str]:
    """Validate a genuinely new Batch103 operation without weakening v1 callers."""
    blockers: list[str] = []
    if epoch != BATCH103_FRESH_OPERATION:
        blockers.append("not_batch103_fresh_operation")
    if epoch in INHERITED_EXECUTION_EPOCHS or epoch == BATCH102_FRESH_OPERATION:
        blockers.append("historical_execution_rejected")
    if not _SHA40.fullmatch(str(workflow_head)):
        blockers.append("invalid_workflow_head")
    return blockers
