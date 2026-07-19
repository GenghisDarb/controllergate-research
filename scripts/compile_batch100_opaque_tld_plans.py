#!/usr/bin/env python3
"""Compile public-safe E/F ordering from the frozen private source identity."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


EXPECTED_TLD = "e18d208e0428944674d6ca6aa9d50609e2256e28ab83dad92ad583dc1ad8a644"


def digest(value: object) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def rows(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--private-tld-bundle", type=Path, required=True)
    parser.add_argument("--requirement-registry", type=Path, required=True)
    parser.add_argument("--cell-registry", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--audit-output", type=Path, required=True)
    args = parser.parse_args()
    tld_hash = hashlib.sha256(args.private_tld_bundle.read_bytes()).hexdigest()
    if tld_hash != EXPECTED_TLD:
        raise SystemExit("private TLD bundle identity mismatch")
    requirement_hash = hashlib.sha256(args.requirement_registry.read_bytes()).hexdigest()
    cells = rows(args.cell_registry)
    candidates = sorted({row["candidate_id"] for row in cells})
    output: list[dict] = []
    for candidate in candidates:
        legal = sorted(row["cell_id"] for row in cells if row["candidate_id"] == candidate)
        for arm_id in ("E", "F"):
            ordered = sorted(legal, key=lambda cell_id: digest([tld_hash, requirement_hash, candidate, arm_id, cell_id]))
            row = {
                "schema": "Batch100PublicSafeOpaqueOrderingV1", "candidate_id": candidate, "arm_id": arm_id,
                "legal_probe_inventory_hash": digest(legal), "ordered_opaque_probe_ids": ordered,
                "tld_bundle_identity_hash": tld_hash, "requirement_registry_hash": requirement_hash,
                "private_tld_passage_count": 0, "truth_field_count": 0, "created_before_execution": True,
                "authority_allowed": "ordering of already registered legal counterfactual cells only",
                "authority_forbidden": ["probe creation", "predicate mutation", "fact mutation", "ownership", "truth", "repair", "count", "release"],
            }
            row["plan_hash"] = digest(row)
            output.append(row)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text("".join(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n" for row in output), encoding="utf-8", newline="\n")
    plan_ids = [probe for row in output for probe in row["ordered_opaque_probe_ids"]]
    allowed_ids = {row["cell_id"] for row in cells}
    audit = {
        "status": "PASS_PUBLIC_SAFE_OPAQUE_ORDERING", "plan_count": len(output),
        "candidate_count": len(candidates), "created_probe_count": len(set(plan_ids) - allowed_ids),
        "missing_legal_probe_count": sum(set(row["cell_id"] for row in cells if row["candidate_id"] == plan["candidate_id"]) != set(plan["ordered_opaque_probe_ids"]) for plan in output),
        "semantic_predicate_mutation_count": 0, "truth_access": 0, "private_text_export_count": 0,
        "producer": "scripts/compile_batch100_opaque_tld_plans.py",
        "execution_depth": "private bundle identity plus frozen requirement-registry digest",
        "semantic_scope": "E/F ordering only", "authority_allowed": "public-safe ordering",
        "authority_forbidden": ["TLD content disclosure", "probe creation", "predicate mutation", "fact", "ownership", "repair", "release"],
    }
    args.audit_output.write_text(json.dumps(audit, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
