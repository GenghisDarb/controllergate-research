from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Iterable

from .stable_identity import stable_hash


FORBIDDEN_ALIASES = {"source_owned", "provider_owned", "harness_owned", "environment_owned", "gold", "fixed"}


@dataclass(frozen=True)
class EpisodeProbe:
    probe_id: str
    candidate_id: str
    run_id: str
    frame_hash: str
    operation_type: str
    argv: tuple[str, ...]
    working_directory_hash: str
    runtime_attestation_hash: str
    network_policy: str
    output_schema: str
    semantic_verifier: str
    partitions: tuple[tuple[str, tuple[str, ...]], ...]
    cost: int
    risk: int
    timeout_seconds: int
    nonce_scope: str
    allowed_output_root_hash: str
    compartment: str

    @property
    def contract_hash(self) -> str:
        return stable_hash(asdict(self))

    def validate_neutrality(self) -> None:
        text = " ".join((self.probe_id, self.operation_type, *self.argv, self.output_schema)).lower()
        if any(alias in text for alias in FORBIDDEN_ALIASES):
            raise ValueError("probe contract contains causal or forbidden semantic alias")


class EpisodeProbeCompiler:
    def compile(self, *, candidate_id: str, run_id: str, frame_hash: str,
                active_hypotheses: Iterable[str], available_operations: Iterable[dict[str, object]]) -> list[EpisodeProbe]:
        hypotheses = tuple(sorted(active_hypotheses))
        probes = []
        for index, operation in enumerate(available_operations, 1):
            partitions = tuple((str(code), tuple(sorted(values))) for code, values in sorted(dict(operation["partitions"]).items()))
            if len({tuple(values) for _, values in partitions}) < 2:
                continue
            probe = EpisodeProbe(
                probe_id=f"episode_probe_{index:02d}", candidate_id=candidate_id, run_id=run_id,
                frame_hash=frame_hash, operation_type=str(operation["operation_type"]),
                argv=tuple(str(x) for x in operation.get("argv", ())),
                working_directory_hash=str(operation["working_directory_hash"]),
                runtime_attestation_hash=str(operation["runtime_attestation_hash"]),
                network_policy=str(operation.get("network_policy", "none")),
                output_schema=str(operation["output_schema"]), semantic_verifier=str(operation["semantic_verifier"]),
                partitions=partitions, cost=int(operation.get("cost", 1)), risk=int(operation.get("risk", 0)),
                timeout_seconds=int(operation.get("timeout_seconds", 60)), nonce_scope=f"{run_id}:{index}",
                allowed_output_root_hash=str(operation["allowed_output_root_hash"]),
                compartment=str(operation.get("compartment", "diagnostic_execution")),
            )
            probe.validate_neutrality(); probes.append(probe)
        return probes


def select_minimax(probes: Iterable[EpisodeProbe], active_hypotheses: Iterable[str]) -> dict[str, object]:
    active = set(active_hypotheses)
    scored = []
    for probe in probes:
        classes = [len(active & set(values)) for _, values in probe.partitions]
        largest = max(classes, default=len(active))
        if largest >= len(active):
            continue
        scored.append((largest, probe.cost, probe.risk, probe.probe_id, probe))
    if not scored:
        return {"status": "NO_LEGAL_DISCRIMINATING_PROBE", "selected_probe_id": None, "forced": False}
    row = min(scored)
    return {"status": "SELECTED", "method": "deterministic_minimax_partition", "selected_probe_id": row[4].probe_id,
            "largest_remaining_class": row[0], "cost": row[1], "risk": row[2], "contract_hash": row[4].contract_hash}
