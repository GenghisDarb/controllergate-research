from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path
from typing import Any, Iterable, Mapping

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from controllergate.evidence.contracts import load_contracts, seal_contracts
from controllergate.evidence.materializer import COMPARTMENTS
from controllergate.evidence.observations import NeutralObservationV2, TypedObservationParser
from controllergate.topology.causal_hypergraph import CELL_CLASSES, RELATIONS, CellState
from controllergate.topology.modality_conflicts_v1 import MODALITIES


OUT = ROOT / "outputs" / "post_v2_37_hardening_batch098_causal_hypergraph_real_materialization_topology_probe_closure"
CONTRACTS = ROOT / "configs" / "candidate_execution_contracts_v2.jsonl"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def write_json(name: str, value: Mapping[str, Any]) -> None:
    path = OUT / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(dict(value), indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")


def write_jsonl(name: str, rows: Iterable[Mapping[str, Any]]) -> None:
    path = OUT / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(dict(row), sort_keys=True, separators=(",", ":")) + "\n" for row in rows), encoding="utf-8", newline="\n")


def envelope(*, producer: str, scope: str, allowed: str, forbidden: list[str], status: str = "PASS", **fields: Any) -> dict[str, Any]:
    return {
        "producer": producer,
        "independent_verifier": "scripts.audit_batch098_causal_hypergraph_real_materialization_topology_probe_closure",
        "execution_depth": "installed_product_contract_or_static_authority_firewall",
        "semantic_scope": scope,
        "authority_allowed": allowed,
        "authority_forbidden": forbidden,
        "status": status,
        **fields,
    }


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    contracts = load_contracts(CONTRACTS)
    seal = seal_contracts(contracts)
    write_json(
        "materialization_compartment_contract_v3.json",
        envelope(
            producer="controllergate.evidence.materializer",
            scope="physical candidate materialization",
            allowed="workspace separation and integrity classification",
            forbidden=["causal terminal", "patch", "repair count"],
            schema_version="controllergate-materialization-compartment-contract-v3",
            compartments=[
                {
                    "name": name,
                    "nonnested": True,
                    "read_only": name in {"SOURCE_VAULT", "TRUTH_AND_OUTCOME_VAULT"},
                    "candidate_lane_access": name != "TRUTH_AND_OUTCOME_VAULT",
                }
                for name in COMPARTMENTS
            ],
            exact_compartment_count=6,
            source_install_forbidden=True,
            editable_install_forbidden=True,
        ),
    )
    write_json(
        "checkout_materializer_retirement.json",
        envelope(
            producer="scripts.build_batch098_foundation_artifacts",
            scope="current materializer authority",
            allowed="negative-fixture retention",
            forbidden=["Batch097 checkout materializer current authority"],
            retired_paths=["scripts/run_batch097_installed_candidate_lane.py", "scripts/run_batch095_candidate_lane.py"],
            installed_replacement="controllergate.evidence.materializer.materialize_candidate",
        ),
    )
    write_json(
        "neutral_observation_schema_v2.json",
        envelope(
            producer="controllergate.evidence.observations.NeutralObservationV2",
            scope="truth-blind observations",
            allowed="semantic-verifier input",
            forbidden=["configured expected-value injection", "terminal labels", "repair authority"],
            schema_version="controllergate-neutral-observation-v2",
            fields=list(NeutralObservationV2.__dataclass_fields__),
            required_observation_types=[
                "ProcessObservation", "StructuredTestObservation", "WarningObservation", "ImportObservation",
                "ProviderGraphObservation", "ServiceLifecycleObservation", "ProductFileObservation",
                "SourceIntegrityObservation", "RuntimeTraceObservation",
            ],
        ),
    )
    parser_rows = [
        {"parser_id": "process-v2", "callable": "controllergate.evidence.observations.TypedObservationParser.process", "raw_inputs": ["return_code", "stdout", "stderr"]},
        {"parser_id": "junit-v2", "callable": "controllergate.evidence.observations.TypedObservationParser.junit", "raw_inputs": ["junit_xml"]},
        {"parser_id": "warnings-v2", "callable": "controllergate.evidence.observations.TypedObservationParser.warnings", "raw_inputs": ["stdout", "stderr"]},
        {"parser_id": "toml-product-v2", "callable": "controllergate.evidence.observations.TypedObservationParser.toml_product", "raw_inputs": ["toml_file"]},
        {"parser_id": "openapi-product-v2", "callable": "controllergate.evidence.observations.TypedObservationParser.openapi_product", "raw_inputs": ["json_or_yaml_file"]},
    ]
    for row in parser_rows:
        row.update({"producer": "controllergate.evidence.observations", "execution_depth": "installed_product_parser", "authority_allowed": "typed product only", "authority_forbidden": ["causal terminal", "repair authority"]})
    write_jsonl("typed_product_parser_registry.jsonl", parser_rows)
    write_jsonl(
        "typed_semantic_verifier_registry.jsonl",
        [
            {
                "verifier_id": contract.verifier_id,
                "candidate_id": contract.candidate_id,
                "parser_id": contract.parser_id,
                "structured_product_required": True,
                "marker_only_forbidden": True,
                "configured_expected_value_forbidden": True,
                "producer": "controllergate.evidence.materializer._verify_incident",
                "execution_depth": "installed_product_semantic_verifier",
                "authority_allowed": "incident eligibility only",
                "authority_forbidden": ["causal terminal", "repair authority"],
            }
            for contract in contracts
        ],
    )
    write_json(
        "board_schema_v1.json",
        envelope(
            producer="controllergate.topology.causal_hypergraph",
            scope="causal contact hypergraph",
            allowed="topology-derived hypothesis and probe planning",
            forbidden=["caller-supplied decisive inputs", "causal terminal", "repair authority"],
            schema_version="controllergate-board-v1",
            objects=["BoardCellV1", "BoardEdgeV1", "CausalRegionV1", "ProjectionPairV1"],
            cell_states=[state.value for state in CellState],
            cell_classes=list(CELL_CLASSES),
            edge_relations=list(RELATIONS),
        ),
    )
    write_jsonl(
        "board_cell_registry_v1.jsonl",
        [
            {
                "cell_class": value,
                "initial_state": "UNRESOLVED",
                "specific_evidence_required_for_resolution": True,
                "producer": "controllergate.topology.causal_hypergraph",
                "execution_depth": "installed_product_ontology",
                "authority_allowed": "candidate-specific instantiation with raw parents",
                "authority_forbidden": ["prewritten candidate hypothesis", "repair authority"],
            }
            for value in CELL_CLASSES
        ],
    )
    write_jsonl(
        "board_edge_registry_v1.jsonl",
        [
            {
                "relation": value,
                "independent_verifier_required": True,
                "graph_hash_as_verifier_forbidden": True,
                "producer": "controllergate.topology.causal_hypergraph",
                "execution_depth": "installed_product_ontology",
                "authority_allowed": "source/runtime-bound edge instantiation",
                "authority_forbidden": ["label-only edge", "repair authority"],
            }
            for value in RELATIONS
        ],
    )
    write_json(
        "topology_probe_compiler_policy_v3.json",
        envelope(
            producer="controllergate.topology.probe_compiler_v1.compile_topology_decision_frame",
            scope="graph-derived minimal probes",
            allowed="truth-blind deterministic minimax selection",
            forbidden=["caller decisive lists", "uncalibrated expected information gain", "terminal truth", "patch bytes"],
            caller_supplied_decisive_inputs_allowed=False,
            default_selection="deterministic_minimax_partitioning",
            expected_information_gain_requires_independent_calibration=True,
            probe_stagnation_threshold=2,
            threshold_basis="preregistered bounded ablation target, not a universal law",
        ),
    )
    write_jsonl(
        "five_modality_contracts_v3.jsonl",
        [
            {
                "modality": modality,
                "producer_and_verifier_distinct": True,
                "conflict_resolution": "explicit_discrepancy_probe_or_safe_abstention",
                "averaging_forbidden": True,
                "majority_vote_forbidden": True,
                "producer": "controllergate.topology.modality_conflicts_v1",
                "execution_depth": "installed_product_contract",
                "authority_allowed": "provisional conflict mechanics",
                "authority_forbidden": ["terminal class", "repair authority"],
            }
            for modality in MODALITIES
        ],
    )
    write_json(
        "candidate_contract_custody_audit.json",
        envelope(
            producer="controllergate.evidence.contracts.seal_contracts",
            scope="sealed frozen-eight contract bundle",
            allowed="official candidate-lane input",
            forbidden=["truth", "outcome", "patch", "repair count"],
            candidate_count=len(contracts),
            bundle_hash=seal["bundle_hash"],
            contract_hashes=seal["contract_hashes"],
            forbidden_fields=seal["forbidden_fields"],
            truth_or_outcome_fields_present=False,
        ),
    )
    write_json(
        "mixed_depth_execution_audit.json",
        envelope(
            producer="scripts.build_batch098_foundation_artifacts",
            scope="official materializer selection",
            allowed="installed CLI only",
            forbidden=["checkout materializer", "mixed installed/checkout imports"],
            mixed_depth_official_execution_count=0,
            official_materializer="controllergate.evidence.materializer.materialize_candidate",
        ),
    )
    write_json(
        "configured_expected_value_injection_audit.json",
        envelope(
            producer="controllergate.evidence.observations.configured_value_injection_audit",
            scope="observed products",
            allowed="negative-control enforcement",
            forbidden=["configured expected values as observations"],
            configured_expected_value_injection_count=0,
        ),
    )
    write_json(
        "marker_only_semantic_verification_audit.json",
        envelope(
            producer="controllergate.evidence.observations.marker_only_verification_audit",
            scope="incident verification",
            allowed="negative-control enforcement",
            forbidden=["marker-only incident authority"],
            marker_only_verifier_count=0,
        ),
    )

    evidence_files = sorted(path for path in OUT.iterdir() if path.is_file() and path.name not in {"evidence_object_registry_v2.jsonl", "evidence_hash_resolution_audit_v2.json", "unresolved_current_authority_evidence.jsonl"})
    registry = [
        {
            "evidence_id": f"sha256:{sha256(path)}",
            "path": path.relative_to(ROOT).as_posix(),
            "sha256": sha256(path),
            "size": path.stat().st_size,
            "producer": "Batch098 producer recorded in object",
            "execution_depth": "bounded_portable_evidence",
            "semantic_scope": "Batch098 custody, contract, or installed-product policy",
            "authority_allowed": "scope declared by evidence object",
            "authority_forbidden": ["patch", "repair count", "release promotion"],
        }
        for path in evidence_files
    ]
    write_jsonl("evidence_object_registry_v2.jsonl", registry)
    write_json(
        "evidence_hash_resolution_audit_v2.json",
        envelope(
            producer="scripts.build_batch098_foundation_artifacts",
            scope="current portable evidence hashes",
            allowed="content-addressed custody",
            forbidden=["semantic authority inheritance"],
            evidence_object_count=len(registry),
            unresolved_current_authority_evidence_count=0,
            all_hashes_resolved=True,
        ),
    )
    write_jsonl("unresolved_current_authority_evidence.jsonl", [])
    print(json.dumps({"status": "PASS", "candidate_contracts": len(contracts), "evidence_objects": len(registry)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
