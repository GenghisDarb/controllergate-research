"""Copy the public Batch100 contracts into the compact scientific artifact."""

from __future__ import annotations

import argparse
import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PUBLIC_CONFIGS = (
    "batch100_prompt_contract.json",
    "controllergate_master_completion_ledger_v2.json",
    "controllergate_master_completion_ledger_schema_v2.json",
    "batch100_incident_identity_registry_v2.jsonl",
    "batch100_incident_provider_registry_v2.jsonl",
    "batch100_candidate_contract_supersession_registry_v1.jsonl",
    "batch100_candidate_counterfactual_programs_v2.jsonl",
    "batch100_counterfactual_cell_registry_v2.jsonl",
    "batch100_outcome_semantic_registry_v2.jsonl",
    "batch100_opaque_tld_ordering_registry_v1.jsonl",
    "historical_cohort_expansion_protocol_v1.json",
    "abstention_required_cohort_protocol_v1.json",
    "mixed_failure_cohort_protocol_v1.json",
    "prospective_validation_protocol_v1.json",
    "memory_lift_validation_protocol_v1.json",
    "protected_repair_protocol_v1.json",
    "external_replication_protocol_v1.json",
    "product_beta_exit_criteria_v1.json",
    "self_maintaining_software_evidence_protocol_v1.json",
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-root", type=Path, required=True)
    args = parser.parse_args()
    target = args.output_root / "public_contracts"
    target.mkdir(parents=True, exist_ok=True)
    for name in PUBLIC_CONFIGS:
        source = ROOT / "configs" / name
        if not source.is_file():
            raise FileNotFoundError(source)
        shutil.copy2(source, target / name)
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
