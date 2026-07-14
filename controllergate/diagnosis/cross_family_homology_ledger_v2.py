from __future__ import annotations

from dataclasses import dataclass, field

from .contact_topology_signature import contact_topology_signature


@dataclass
class CrossFamilyHomologyLedger:
    rows: list[dict[str, object]] = field(default_factory=list)

    def append(self, repository_family: str, proof_group: str, structural_record: dict[str, object]) -> None:
        self.rows.append({"repository_family": repository_family, "proof_group": proof_group, **contact_topology_signature(structural_record)})

    def training_fold(self, holdout_family: str, excluded_proof_groups: set[str]) -> list[dict[str, object]]:
        return [row for row in self.rows if row["repository_family"] != holdout_family and row["proof_group"] not in excluded_proof_groups]
