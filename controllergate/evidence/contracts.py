from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Iterable, Mapping


FORBIDDEN_FIELDS = frozenset(
    {
        "terminal_class",
        "gold_patch",
        "post_repair_result",
        "post_validation_result",
        "future_revision",
        "count_outcome",
        "source_owned_label",
        "repair_patch",
        "truth_class",
    }
)


def canonical_bytes(value: object) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")


def hash_value(value: object) -> str:
    return hashlib.sha256(canonical_bytes(value)).hexdigest()


@dataclass(frozen=True)
class CandidateExecutionContract:
    candidate_id: str
    repository: str
    source_commit: str
    candidate_class: str
    provider_python: str
    provider_install_specs: tuple[str, ...]
    project_build_source: str
    additional_project_install_paths: tuple[str, ...]
    project_build_argv: tuple[str, ...]
    target_argv: tuple[str, ...]
    target_paths: tuple[str, ...]
    target_working_compartment: str
    target_environment: Mapping[str, str]
    parser_id: str
    verifier_id: str
    positive_controls: tuple[Mapping[str, Any], ...]
    negative_controls: tuple[Mapping[str, Any], ...]
    adversarial_controls: tuple[Mapping[str, Any], ...]
    acquisition_network_policy: str
    execution_network_policy: str
    environment_allowlist: tuple[str, ...]
    resource_budget: Mapping[str, int]
    source_path_classes: Mapping[str, tuple[str, ...]]
    secondary_source: Mapping[str, Any] | None = None

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> "CandidateExecutionContract":
        forbidden = sorted(FORBIDDEN_FIELDS.intersection(value))
        if forbidden:
            raise ValueError(f"forbidden CandidateExecutionContract fields: {forbidden}")
        required = {field.name for field in __import__("dataclasses").fields(cls) if field.default is __import__("dataclasses").MISSING}
        missing = sorted(required.difference(value))
        if missing:
            raise ValueError(f"missing CandidateExecutionContract fields: {missing}")
        if len(str(value["source_commit"])) != 40 or any(ch not in "0123456789abcdef" for ch in str(value["source_commit"]).lower()):
            raise ValueError("source_commit must be 40 lowercase hexadecimal characters")
        return cls(
            candidate_id=str(value["candidate_id"]), repository=str(value["repository"]), source_commit=str(value["source_commit"]).lower(),
            candidate_class=str(value["candidate_class"]), provider_python=str(value["provider_python"]),
            provider_install_specs=tuple(value["provider_install_specs"]), project_build_source=str(value["project_build_source"]),
            additional_project_install_paths=tuple(value["additional_project_install_paths"]), project_build_argv=tuple(value["project_build_argv"]),
            target_argv=tuple(value["target_argv"]), target_paths=tuple(value["target_paths"]),
            target_working_compartment=str(value["target_working_compartment"]), target_environment=dict(value["target_environment"]),
            parser_id=str(value["parser_id"]), verifier_id=str(value["verifier_id"]),
            positive_controls=tuple(dict(row) for row in value["positive_controls"]),
            negative_controls=tuple(dict(row) for row in value["negative_controls"]),
            adversarial_controls=tuple(dict(row) for row in value["adversarial_controls"]),
            acquisition_network_policy=str(value["acquisition_network_policy"]), execution_network_policy=str(value["execution_network_policy"]),
            environment_allowlist=tuple(value["environment_allowlist"]), resource_budget=dict(value["resource_budget"]),
            source_path_classes={key: tuple(paths) for key, paths in value["source_path_classes"].items()},
            secondary_source=dict(value["secondary_source"]) if value.get("secondary_source") else None,
        )

    def record(self) -> dict[str, Any]:
        value = asdict(self)
        value["contract_hash"] = hash_value(value)
        value["truth_or_outcome_fields_present"] = False
        value["authority_allowed"] = "candidate acquisition, materialization, and neutral observation"
        value["authority_forbidden"] = ["causal terminal", "repair authorization", "count mutation", "release promotion"]
        return value


def load_contracts(path: str | Path) -> list[CandidateExecutionContract]:
    source = Path(path)
    rows = []
    if source.suffix == ".jsonl":
        rows = [json.loads(line) for line in source.read_text(encoding="utf-8").splitlines() if line.strip()]
    else:
        value = json.loads(source.read_text(encoding="utf-8"))
        rows = value.get("contracts", value if isinstance(value, list) else [])
    contracts = [CandidateExecutionContract.from_mapping(row) for row in rows]
    identifiers = [row.candidate_id for row in contracts]
    if len(identifiers) != len(set(identifiers)):
        raise ValueError("duplicate candidate contract")
    return contracts


def seal_contracts(contracts: Iterable[CandidateExecutionContract]) -> dict[str, Any]:
    rows = [contract.record() for contract in contracts]
    return {
        "schema_version": "controllergate-candidate-execution-contract-v2",
        "contract_count": len(rows),
        "contract_hashes": {row["candidate_id"]: row["contract_hash"] for row in rows},
        "bundle_hash": hash_value(rows),
        "forbidden_fields": sorted(FORBIDDEN_FIELDS),
        "truth_or_outcome_fields_present": False,
        "status": "PASS",
    }
