from __future__ import annotations

from enum import Enum


class ProviderState(str, Enum):
    PLAN_CREATED = "PROVIDER_PLAN_CREATED"
    DRY_LOCK_CREATED = "PROVIDER_DRY_LOCK_CREATED"
    BYTES_ACQUIRED = "PROVIDER_BYTES_ACQUIRED"
    MATERIALIZED = "PROVIDER_MATERIALIZED"
    VERIFIED = "PROVIDER_VERIFIED"
    EXECUTION_READY = "PROVIDER_EXECUTION_READY"


ORDER = list(ProviderState)


def valid_transition(previous: ProviderState | None, current: ProviderState) -> bool:
    if previous is None:
        return current is ProviderState.PLAN_CREATED
    return ORDER.index(current) == ORDER.index(previous) + 1
