from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from hashlib import sha256
import json
from typing import Any


class DamageClass(str, Enum):
    EXACT_REVERSIBLE = "EXACT_REVERSIBLE"
    TEMPLATE_GUIDED = "TEMPLATE_GUIDED"
    LOSSY = "LOSSY"
    BYPASS_ONLY = "BYPASS_ONLY"
    UNKNOWN = "UNKNOWN"


@dataclass(frozen=True)
class RepairDecision:
    strategy: str
    authorized: bool
    fidelity: float
    repair_debt: tuple[str, ...]
    decision_hash: str


class RepairStrategySelector:
    def classify(self, damage: dict[str, Any]) -> DamageClass:
        if damage.get("exact_inverse"):
            return DamageClass.EXACT_REVERSIBLE
        if damage.get("authoritative_template") and damage.get("bounded_delta"):
            return DamageClass.TEMPLATE_GUIDED
        if damage.get("bypass"):
            return DamageClass.BYPASS_ONLY
        if damage.get("partial_recovery"):
            return DamageClass.LOSSY
        return DamageClass.UNKNOWN

    def select(self, damage: dict[str, Any], *, license_token: str | None) -> RepairDecision:
        kind = self.classify(damage)
        fidelity = {DamageClass.EXACT_REVERSIBLE: 1.0, DamageClass.TEMPLATE_GUIDED: .98, DamageClass.LOSSY: .5, DamageClass.BYPASS_ONLY: 0.0, DamageClass.UNKNOWN: 0.0}[kind]
        authorized = bool(license_token) and kind in {DamageClass.EXACT_REVERSIBLE, DamageClass.TEMPLATE_GUIDED}
        debt = () if fidelity >= .95 else ("residual_damage_or_bypass_debt",)
        body = {"class": kind.value, "authorized": authorized, "fidelity": fidelity, "debt": debt, "license": license_token}
        return RepairDecision(kind.value, authorized, fidelity, debt, sha256(json.dumps(body, sort_keys=True).encode()).hexdigest())
