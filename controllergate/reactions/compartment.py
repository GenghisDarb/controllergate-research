from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Compartment:
    compartment_id: str
    root: Path
    writable: bool
    network_policy: str

    def verify(self) -> dict[str, object]:
        absolute = self.root.resolve()
        prohibited = str(absolute).upper().startswith("E:\\")
        return {"status": "PASS" if absolute.is_absolute() and not prohibited else "BLOCK",
                "compartment_id": self.compartment_id, "root": str(absolute),
                "writable": self.writable, "network_policy": self.network_policy,
                "prohibited_runtime_root": prohibited}
