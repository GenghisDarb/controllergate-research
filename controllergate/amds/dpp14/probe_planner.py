from __future__ import annotations

from dataclasses import dataclass

from controllergate.state.integrity import canonical_hash

from .posterior import expected_information_gain
from .probe_contract import ProbeContract


@dataclass(frozen=True)
class ProbePlanningRecord:
    active_hypotheses: tuple[str, ...]
    candidate_id: str
    selected_contract_hash: str | None
    selected_probe_id: str | None
    selection_method: str
    scores: tuple[dict[str, object], ...]
    status: str
    tie_break: str

    @property
    def planning_hash(self) -> str:
        return canonical_hash(self.record(include_hash=False))

    def record(self, *, include_hash: bool = True) -> dict[str, object]:
        value: dict[str, object] = {
            "active_hypotheses": list(self.active_hypotheses),
            "candidate_id": self.candidate_id,
            "scores": list(self.scores),
            "selected_contract_hash": self.selected_contract_hash,
            "selected_probe_id": self.selected_probe_id,
            "selection_method": self.selection_method,
            "status": self.status,
            "tie_break": self.tie_break,
        }
        if include_hash:
            value["planning_hash"] = self.planning_hash
        return value


def select_probe(
    *,
    active_hypotheses: set[str],
    contracts: list[ProbeContract],
    spent_contract_hashes: set[str],
    prior: dict[str, float] | None = None,
) -> ProbePlanningRecord:
    candidates: list[tuple[tuple[object, ...], ProbeContract, dict[str, object], str]] = []
    active = tuple(sorted(active_hypotheses))
    for contract in contracts:
        contract.validate()
        if contract.contract_hash in spent_contract_hashes:
            continue
        partitions = {
            outcome: sorted(active_hypotheses.intersection(members))
            for outcome, members in contract.predicted_outcome_partitions.items()
        }
        distinct = {tuple(value) for value in partitions.values() if value}
        if len(distinct) < 2:
            continue
        if contract.calibrated_likelihoods is not None:
            if prior is None:
                continue
            ig, detail = expected_information_gain(prior, contract.calibrated_likelihoods)
            utility = ig / max(1.0, contract.cost + contract.risk)
            score = {
                "contract_hash": contract.contract_hash,
                "cost": contract.cost,
                "information_gain": ig,
                "intermediate": detail,
                "probe_id": contract.probe_id,
                "risk": contract.risk,
                "utility": utility,
            }
            key = (-utility, contract.cost, contract.risk, contract.probe_id)
            candidates.append((key, contract, score, "expected_information_gain"))
        else:
            largest = max(len(value) for value in partitions.values())
            score = {
                "contract_hash": contract.contract_hash,
                "cost": contract.cost,
                "largest_remaining_equivalence_class": largest,
                "partitions": partitions,
                "probe_id": contract.probe_id,
                "risk": contract.risk,
            }
            key = (largest, contract.cost, contract.risk, contract.probe_id)
            candidates.append((key, contract, score, "deterministic_minimax_partition"))
    if not candidates:
        return ProbePlanningRecord(
            active_hypotheses=active,
            candidate_id=contracts[0].candidate_id if contracts else "unknown",
            selected_contract_hash=None,
            selected_probe_id=None,
            selection_method="none",
            scores=(),
            status="NO_LEGAL_DISCRIMINATING_PROBE",
            tie_break="largest_partition_then_cost_then_risk_then_probe_id",
        )
    candidates.sort(key=lambda row: row[0])
    _, selected, _, method = candidates[0]
    return ProbePlanningRecord(
        active_hypotheses=active,
        candidate_id=selected.candidate_id,
        selected_contract_hash=selected.contract_hash,
        selected_probe_id=selected.probe_id,
        selection_method=method,
        scores=tuple(row[2] for row in candidates),
        status="SELECTED",
        tie_break="largest_partition_then_cost_then_risk_then_probe_id"
        if method == "deterministic_minimax_partition"
        else "utility_then_cost_then_risk_then_probe_id",
    )
