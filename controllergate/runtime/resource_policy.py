from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class ResourcePolicy:
    cpus: str = "2"
    memory: str = "2g"
    memory_swap: str = "2g"
    pids_limit: int = 256
    nofile_soft: int = 1024
    nofile_hard: int = 1024
    timeout_seconds: int = 300

    def as_dict(self) -> dict[str, object]:
        return asdict(self)

    def docker_args(self) -> list[str]:
        return [
            "--cpus", self.cpus,
            "--memory", self.memory,
            "--memory-swap", self.memory_swap,
            "--pids-limit", str(self.pids_limit),
            "--ulimit", f"nofile={self.nofile_soft}:{self.nofile_hard}",
        ]
