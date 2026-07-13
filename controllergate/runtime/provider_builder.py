from __future__ import annotations

from pathlib import Path
from typing import Any

from .provider_build_copy import create_read_only_execution_view, create_writable_build_copy, tree_identity
from .provider_capsule_verifier import verify_provider_artifacts
from .provider_state import ProviderState


def build_provider(*, immutable_source: Path, runtime_root: Path, candidate_id: str, artifacts: list[dict[str, Any]]) -> dict[str, Any]:
    candidate_root = runtime_root / "providers" / candidate_id
    build_copy = candidate_root / "writable-build-copy"
    execution_view = candidate_root / "readonly-execution-view"
    source_before = tree_identity(immutable_source)
    copied = create_writable_build_copy(immutable_source, build_copy)
    verification = verify_provider_artifacts(artifacts)
    states = [ProviderState.PLAN_CREATED.value, ProviderState.DRY_LOCK_CREATED.value]
    if artifacts: states.append(ProviderState.BYTES_ACQUIRED.value)
    if copied["status"] == "PASS" and artifacts: states.append(ProviderState.MATERIALIZED.value)
    if verification["status"] == "PASS": states.append(ProviderState.VERIFIED.value)
    view: dict[str, Any] = {"status": "NOT_RUN"}
    if verification["status"] == "PASS":
        view = create_read_only_execution_view(build_copy, execution_view)
        if view["status"] == "PASS": states.append(ProviderState.EXECUTION_READY.value)
    source_after = tree_identity(immutable_source)
    return {
        "status": "PASS" if states[-1] == ProviderState.EXECUTION_READY.value else "BLOCK",
        "candidate_id": candidate_id, "states": states, "source_identity_before": source_before,
        "source_identity_after": source_after, "original_source_immutable": source_before == source_after,
        "build_copy": copied, "artifact_verification": verification, "execution_view": view,
        "network_policy": "none", "provider_bytes_committed": False,
        "exact_blocker": None if states[-1] == ProviderState.EXECUTION_READY.value else "provider_closure_not_established",
    }
