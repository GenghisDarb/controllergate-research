from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ConnectorContract:
    connector_id: str
    allowed_resources: tuple[str, ...]
    write_authority: bool = False

    def validate(self) -> dict[str, object]:
        return {"status": "CONNECTOR_SCHEMA_VALIDATED" if self.allowed_resources and not self.write_authority else "BLOCK",
                "connector_id": self.connector_id, "write_authority": self.write_authority}
