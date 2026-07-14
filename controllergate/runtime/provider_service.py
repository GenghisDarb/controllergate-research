from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from controllergate.reactions.token_kernel import ReactionToken, require_tokens
from controllergate.state.integrity import canonical_hash


HISTORICAL_PROVIDER_STATES = {
    "HISTORICAL_EXACT_PROVIDER_BYTES_VERIFIED", "HISTORICAL_PROVIDER_ARTIFACT_EXPIRED",
    "HISTORICAL_PROVIDER_RECONSTRUCTED_EQUIVALENT", "HISTORICAL_PROVIDER_RECONSTRUCTION_FAILED",
}


@dataclass(frozen=True)
class ProviderPlan:
    dependency_graph_hash: str
    platform: str
    runtime: str
    abi: str
    artifact_hashes: tuple[str, ...]
    network_policy: str

    @property
    def seal(self) -> str:
        return canonical_hash(self.__dict__)


def verify_provider_ready(*, candidate_id: str, run_id: str, source_token: ReactionToken,
                          plan: ProviderPlan, offline_install_hashes: tuple[str, str],
                          dependency_check: bool, import_probes: bool, entry_point_probes: bool,
                          read_only_execution_view: bool) -> ReactionToken:
    require_tokens((source_token,), ("SOURCE_ACQUIRED_TOKEN",), candidate_id=candidate_id, run_id=run_id)
    if len(set(offline_install_hashes)) != 1 or not all((dependency_check, import_probes, entry_point_probes, read_only_execution_view)):
        raise ValueError("full provider lifecycle did not pass")
    payload = {"plan_seal": plan.seal, "offline_install_hash": offline_install_hashes[0], "dependency_check": dependency_check, "import_probes": import_probes, "entry_point_probes": entry_point_probes, "read_only_execution_view": read_only_execution_view}
    return ReactionToken.mint(token_type="PROVIDER_EXECUTION_READY_TOKEN", candidate_id=candidate_id, run_id=run_id, producer_event="provider_execution_ready", input_tokens=(source_token,), payload=payload, independent_verifier="controllergate.runtime.provider_service")
