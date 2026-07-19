"""Build the compact Batch100 public claim boundary and package-ready evidence."""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
AUTHORITY_FORBIDDEN = ["ordinary patch", "repair count mutation", "historical increment", "Product Beta promotion", "production readiness", "self-maintaining software claim"]


def read_json(path: Path, default: object = None):
    return json.loads(path.read_text(encoding="utf-8")) if path.is_file() else default


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()] if path.is_file() else []


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--workflow-run-id", default="local")
    args = parser.parse_args()
    out = args.output_root
    programs = read_jsonl(ROOT / "configs/batch100_candidate_counterfactual_programs_v2.jsonl")
    cells = read_jsonl(ROOT / "configs/batch100_counterfactual_cell_registry_v2.jsonl")
    evidence = read_jsonl(out / "matched_counterfactual_evidence_v2.jsonl")
    terminals = read_jsonl(out / "controller_audit_counterfactual_terminal_records_v3.jsonl")
    clean = read_jsonl(out / "batch100_clean_replay_registry_v1.jsonl")
    ownership = read_jsonl(out / "ownership_support_receipts_v1.jsonl")
    blockers = read_jsonl(out / "batch100_active_blockers_v1.jsonl")
    critic = read_json(out / "critic/batch100_semantic_mutation_campaign_summary.json", {})
    parity = read_jsonl(ROOT / "configs/batch100_incident_provider_registry_v2.jsonl")
    protocols = read_json(out / "future_protocol_readiness.json", {})
    terminal_distribution = dict(sorted(Counter(row["terminal_class"] for row in terminals).items()))
    pair_classes = dict(sorted(Counter(row["single_factor_status"] for row in evidence).items()))
    materialized = sum(bool(row.get("incident_materialized")) for row in evidence)
    sensitivity = sum(row.get("evidence_level") == "DIMENSION_SENSITIVITY_VERIFIED" for row in evidence)
    ownership_count = sum(bool(row.get("ownership_supported")) for row in evidence)
    unresolved = sum(len(row.get("unresolved_alternatives", [])) for row in evidence)
    unique_clean_cells = len({row.get("cell_id") for row in clean if row.get("reproducibility_status") == "REPRODUCIBLE"})
    exact_blockers = sorted({row.get("blocker", "unspecified_blocker") for row in blockers} | ({"ownership_grade_differential_evidence_missing"} if ownership_count == 0 else set()))
    claim = {
        "status": "PRODUCT_BETA_BLOCKED_EXACT",
        "protocol": "v2.19", "package_version": "0.2.0b2.dev0",
        "issue_derived_repair_count": 6, "native_external_repair_count": 4, "historical_increment": 0,
        "ordinary_patch_count": 0, "full_scoring": "NOT_RUN/disallowed",
        "prospective_effectiveness": "NOT_ESTABLISHED", "memory": "not demonstrated",
        "public_writes": "inactive", "automatic_merge": "inactive", "production_readiness": False,
        "self_maintaining_software": "false/not demonstrated",
        "authority_allowed": "truth-blind public counterfactual evidence and safe abstention at recorded scope",
        "authority_forbidden": AUTHORITY_FORBIDDEN,
        "exact_blockers": exact_blockers,
        "producer": "scripts/finalize_batch100_release_outputs.py", "execution_depth": "public receipt and critic reconstruction",
        "semantic_scope": "Batch100 public claim boundary",
    }
    state = {
        "batch": "Batch100", "workflow_run_id": args.workflow_run_id,
        "program_count": len(programs), "cell_count": len(cells), "clean_replay_cell_count": unique_clean_cells,
        "typed_incident_materialized_count": materialized, "sensitivity_receipt_count": sensitivity,
        "necessity_receipt_count": 0, "sufficiency_receipt_count": 0, "interaction_receipt_count": 0,
        "ownership_receipt_count": ownership_count, "unresolved_alternative_count": unresolved,
        "pair_classification_distribution": pair_classes, "terminal_distribution": terminal_distribution,
        "incident_parity": {row["candidate_id"]: row["parity_status"] for row in parity},
        "architecture_gain": read_json(out / "architecture_component_gain_gate_v2.json", {}).get("status", "NOT_ESTABLISHED"),
        "tld_ordering_gain": "NOT_ESTABLISHED", "private_truth_join": "PENDING_LOCAL_POST_PUBLIC_TERMINAL_JOIN",
        "causal_differential_feasibility": "NOT_ESTABLISHED" if ownership_count == 0 else "PENDING_PRIVATE_TRUTH_JOIN",
        "historical_calibration": "NOT_ESTABLISHED", "protected_repair_eligible_count": 0,
        "semantic_mutations_executed": critic.get("semantic_mutations_executed", 0),
        "semantic_mutations_rejected": critic.get("semantic_mutations_rejected", 0),
        "future_protocol_ready_count": protocols.get("protocol_ready_count", 0),
        "patch_operations": 0, "repair_count_increment": 0, "historical_increment": 0,
        "truth_access_during_public_execution": 0, "private_tld_access_during_candidate_execution": 0,
        "claim_boundary": claim, "active_blockers": exact_blockers,
        "producer": "scripts/finalize_batch100_release_outputs.py", "execution_depth": "public workflow evidence aggregation",
        "semantic_scope": "Batch100 consolidated public state", "authority_allowed": "scientific reporting",
        "authority_forbidden": AUTHORITY_FORBIDDEN,
    }
    write_json(out / "batch100_claim_boundary.json", claim)
    write_json(out / "batch100_consolidated_state.json", state)
    write_json(out / "batch100_private_truth_join_status.json", {
        "status": "PENDING_LOCAL_POST_PUBLIC_TERMINAL_JOIN", "public_truth_access": 0,
        "expected_private_bundle_sha256": "08c73e862910f2d314addaf19cca39674b129b1e40a3b38f8e12c58c7ca1c37b",
        "authority_allowed": "private calibration after artifact verification", "authority_forbidden": AUTHORITY_FORBIDDEN,
        "producer": "scripts/finalize_batch100_release_outputs.py", "execution_depth": "dependency-boundary record", "semantic_scope": "private calibration handoff",
    })
    summary = f"""# Batch100 matched counterfactual execution

Batch099 was officially ingested with verified byte custody. Batch100 froze {len(programs)} candidate-bound programs and {len(cells)} cells, then executed the provider slices available in the public workflow. The public evidence materialized {materialized} incident program(s), established {sensitivity} sensitivity-level result(s), and established {ownership_count} ownership-grade result(s).

The independent critic rejected {critic.get('semantic_mutations_rejected', 0)} of {critic.get('semantic_mutations_executed', 0)} copied-tree semantic mutations. No candidate patch was generated or applied, no repair count changed, and no private truth or private ordering corpus entered public candidate execution.

Current boundary: `PRODUCT_BETA_BLOCKED_EXACT`. Prospective effectiveness is `NOT_ESTABLISHED`; memory remains `not demonstrated`; production readiness is false; self-maintaining software is false/not demonstrated.

Exact blockers: {', '.join(exact_blockers) if exact_blockers else 'none recorded'}.
"""
    (out / "campaign_summary.md").write_text(summary, encoding="utf-8", newline="\n")
    # Portable manifest deliberately excludes every manifest file from its own list.
    rows = []
    for path in sorted(out.rglob("*")):
        if path.is_file() and path.name not in {"SHA256SUMS.txt", "ARTIFACT_SHA256SUMS.txt", "PORTABLE_ARTIFACT_SHA256SUMS.txt"}:
            rel = path.relative_to(out).as_posix()
            rows.append(f"{hashlib.sha256(path.read_bytes()).hexdigest()}  {rel}")
    manifest = "\n".join(rows) + "\n"
    for name in ("SHA256SUMS.txt", "ARTIFACT_SHA256SUMS.txt", "PORTABLE_ARTIFACT_SHA256SUMS.txt"):
        (out / name).write_text(manifest, encoding="utf-8", newline="\n")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
