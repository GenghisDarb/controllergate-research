from __future__ import annotations

from dataclasses import dataclass, field
from hashlib import sha256
import json
from typing import Any


@dataclass(frozen=True)
class ThreatAssessment:
    classification: str
    confidence: float
    response: str
    assessment_hash: str


@dataclass
class DefenseController:
    trusted_identities: set[str] = field(default_factory=set)
    signatures: dict[str, set[str]] = field(default_factory=dict)

    def assess(self, identity: str, features: set[str], *, corroborating_channels: int = 1) -> ThreatAssessment:
        altered_trusted = identity in self.trusted_identities and "identity_integrity_failure" in features
        expected_self = identity in self.trusted_identities and not altered_trusted
        matches = [name for name, required in self.signatures.items() if required <= features]
        if expected_self:
            classification, confidence, response = "EXPECTED_SELF", 1.0, "TOLERATE"
        elif altered_trusted:
            classification, confidence, response = "ALTERED_TRUSTED_COMPONENT", .95, "QUARANTINE"
        elif matches and corroborating_channels >= 2:
            classification, confidence, response = matches[0], min(1.0, .6 + .15 * corroborating_channels), "CONTAIN"
        elif matches:
            classification, confidence, response = "WEAK_UNCORROBORATED_SIGNAL", .5, "OBSERVE"
        else:
            classification, confidence, response = "UNKNOWN", .2, "OBSERVE"
        payload = {"identity": identity, "features": sorted(features), "classification": classification, "confidence": confidence, "response": response}
        return ThreatAssessment(classification, confidence, response, sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest())
