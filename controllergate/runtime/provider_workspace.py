from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import os
from pathlib import Path
import tempfile


WINDOWS_SAFE_PATH_LIMIT = 240
PROJECTED_SUFFIXES = (
    "src/tests/unit/orchestrator/test_orchestrator_engine.py",
    "build/.controllergate-build-metadata/provider-lock-v999.json",
    "whl/a-very-long-normalized-python-distribution-name-0.0.0-py3-none-any.whl",
    "env1/Lib/site-packages/a_very_long_normalized_python_distribution_name/__init__.py",
    "env2/Lib/site-packages/a_very_long_normalized_python_distribution_name/__init__.py",
    "arms/fixed_legal_order_memory_disabled/posterior.json",
)


def candidate_key(candidate_id: str, candidate_sha: str) -> str:
    return hashlib.sha256((candidate_id + candidate_sha).encode("utf-8")).hexdigest()[:12]


def projected_maximum_path(root: Path, key: str) -> int:
    base = root / "c" / key
    return max(len(str(base / suffix)) for suffix in PROJECTED_SUFFIXES)


def _short_runtime_root() -> Path:
    configured = os.environ.get("CONTROLLERGATE_SHORT_RUNTIME_ROOT")
    if configured:
        return Path(configured)
    drive = Path(tempfile.gettempdir()).anchor
    if os.name == "nt" and drive:
        return Path(drive) / "cgr"
    return Path(tempfile.gettempdir()) / "cgr"


@dataclass(frozen=True)
class ProviderWorkspace:
    candidate_id: str
    candidate_sha: str
    candidate_key: str
    requested_runtime_root: str
    effective_runtime_root: str
    candidate_root: str
    source_root: str
    build_root: str
    wheelhouse: str
    environment_one: str
    environment_two: str
    arms_root: str
    requested_projected_maximum_path_length: int
    effective_projected_maximum_path_length: int
    path_limit: int
    relocated: bool

    def record(self) -> dict[str, object]:
        return asdict(self)


def plan_provider_workspace(
    runtime_root: Path,
    candidate_id: str,
    candidate_sha: str,
    *,
    path_limit: int = WINDOWS_SAFE_PATH_LIMIT,
) -> ProviderWorkspace:
    key = candidate_key(candidate_id, candidate_sha)
    requested = Path(runtime_root).resolve()
    requested_max = projected_maximum_path(requested, key)
    effective = requested
    if requested_max > path_limit:
        effective = _short_runtime_root().resolve()
    effective_max = projected_maximum_path(effective, key)
    if effective_max > path_limit:
        raise ValueError(f"provider workspace remains unsafe: {effective_max} > {path_limit}")
    root = effective / "c" / key
    return ProviderWorkspace(
        candidate_id=candidate_id,
        candidate_sha=candidate_sha,
        candidate_key=key,
        requested_runtime_root=str(requested),
        effective_runtime_root=str(effective),
        candidate_root=str(root),
        source_root=str(root / "src"),
        build_root=str(root / "build"),
        wheelhouse=str(root / "whl"),
        environment_one=str(root / "env1"),
        environment_two=str(root / "env2"),
        arms_root=str(root / "arms"),
        requested_projected_maximum_path_length=requested_max,
        effective_projected_maximum_path_length=effective_max,
        path_limit=path_limit,
        relocated=effective != requested,
    )


def materialize_provider_workspace(plan: ProviderWorkspace) -> ProviderWorkspace:
    for value in (
        plan.source_root,
        plan.build_root,
        plan.wheelhouse,
        plan.environment_one,
        plan.environment_two,
        plan.arms_root,
    ):
        Path(value).mkdir(parents=True, exist_ok=True)
    return plan
