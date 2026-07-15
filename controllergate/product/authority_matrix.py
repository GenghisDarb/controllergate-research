from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class AuthorityDecision:
    status: str
    winner: str | None
    reason: str


class CrossSystemAuthorityMatrix:
    def __init__(self, precedence: tuple[str, ...]) -> None:
        if len(set(precedence)) != len(precedence):
            raise ValueError("authority_precedence_duplicate")
        self.precedence = precedence

    def resolve(self, requests: dict[str, str]) -> AuthorityDecision:
        known = [name for name in self.precedence if name in requests]
        if not known:
            return AuthorityDecision("BLOCK", None, "no_authorized_subsystem")
        winner = known[0]
        return AuthorityDecision("RESOLVED", winner, f"restrictive_precedence:{winner}")

    def validate_escalation(self, subsystem: str, requested: str, authorized: set[str]) -> AuthorityDecision:
        if requested not in authorized:
            return AuthorityDecision("BLOCK", None, "authority_escalation_forbidden")
        return AuthorityDecision("PASS", subsystem, "explicit_authority_present")
