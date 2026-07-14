from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path

from controllergate.reactions.stable_identity import stable_hash


@dataclass(frozen=True)
class ProviderPlanV4:
    candidate_id: str
    source_identity: str
    python_abi: str
    platform_tag: str
    roots: tuple[str, ...]
    required_imports: tuple[str, ...]
    required_entrypoints: tuple[str, ...]

    def record(self) -> dict[str, object]:
        value = asdict(self)
        value["state"] = "PROVIDER_PLAN_BOUND"
        value["plan_hash"] = stable_hash(value)
        return value


def immutable_source_hash(root: Path) -> str:
    files = [(str(p.relative_to(root)).replace("\\", "/"), stable_hash(p.read_bytes().hex()))
             for p in sorted(root.rglob("*")) if p.is_file() and ".git" not in p.parts]
    return stable_hash(files)
