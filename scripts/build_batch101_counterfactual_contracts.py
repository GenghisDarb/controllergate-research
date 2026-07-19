#!/usr/bin/env python3
"""Freeze Batch101 semantic, predicate, provider, program, and cell contracts."""

from __future__ import annotations

import hashlib
import json
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "configs"
OUT = ROOT / "outputs" / "post_v2_37_hardening_batch101_canonical_semantic_replay_exact_incident_salvage_ownership_closure"


def digest(value: object) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n" for row in rows), encoding="utf-8", newline="\n")


def eq(field: str, value: object) -> dict:
    return {"eq": [{"field": field}, value]}


def main() -> int:
    stamp = "2026-07-19T00:00:00Z"
    old_programs = read_jsonl(CONFIG / "batch100_candidate_counterfactual_programs_v2.jsonl")
    old_cells = read_jsonl(CONFIG / "batch100_counterfactual_cell_registry_v2.jsonl")
    programs = deepcopy(old_programs)
    cells = deepcopy(old_cells)

    predicates = {
        "batch100-darker-112-git-dir": ({"eq": [{"field": "not_a_git_repository"}, True]}, {"eq": [{"field": "not_a_git_repository"}, False]}),
        "batch100-py-bugger-65-accounting": (
            {"all": [
                {"gt": [{"field": "cli_reported_inserted_count"}, {"field": "successful_mutation_count"}]},
                {"gt": [{"field": "cli_reported_inserted_count"}, {"field": "persisted_source_diff_mutation_count"}]},
            ]},
            {"all": [
                {"ge": [{"field": "attempted_mutation_count"}, {"field": "successful_mutation_count"}]},
                {"ge": [{"field": "successful_mutation_count"}, {"field": "persisted_source_diff_mutation_count"}]},
            ]},
        ),
        "batch100-cloudpickle-507-typevar": (
            eq("typevar_weakref_error", True),
            eq("failed_node_count", 0),
        ),
        "batch100-cloudpickle-507-distutils": (
            {"all": [eq("exception_type", "ModuleNotFoundError"), eq("distutils_import_error", True)]},
            eq("distutils_import_error", False),
        ),
        "batch100-freezegun-547-three-nodes": (
            {"all": [eq("failed_node_count", 3), eq("fake_date_mismatch", True)]},
            eq("failed_node_count", 0),
        ),
        "batch100-audioread-144-aifc": (
            {"all": [eq("exception_type", "ModuleNotFoundError"), eq("module", "aifc")]},
            eq("rawread_import", "success"),
        ),
        "batch100-pytest-13480-warning-mode": (
            {"all": [eq("outer_pytest_exit_code", 1), eq("collection_return_code_4", False)]},
            eq("outer_pytest_exit_code", 0),
        ),
        "batch100-openbb-7585-topology": (
            {"all": [eq("exit_code", 0), eq("command_count", 0), eq("parse_status", "success")]},
            {"all": [eq("exit_code", 0), {"gt": [{"field": "command_count"}, 0]}, eq("semantic_input_equivalence", True)]},
        ),
        "batch100-poetry-10974-path-name": (
            {"all": [eq("exit_code", 0), {"ne": [{"field": "generated_project_name"}, {"field": "cwd_basename"}]}]},
            {"all": [eq("exit_code", 0), eq("generated_project_name", {"field": "cwd_basename"})]},
        ),
    }

    # Finish the Cloudpickle 2x2 provider factorial without claiming execution.
    template = next(row for row in cells if row["cell_id"].endswith("python311-no-setuptools"))
    extra = deepcopy(template)
    extra["cell_id"] = "cell:batch101-cloudpickle-507-distutils:python311-with-setuptools"
    extra["cell_name"] = "python311-with-setuptools"
    extra["cell_role"] = "exclusion"
    extra["factor_values"] = {"python": "3.11", "setuptools": "present"}
    extra["exact_environment"] = {"SETUPTOOLS_COMPATIBILITY": "present"}
    extra["exact_cwd"] = "${RUNTIME_ROOT}/batch101/cloudpickle_507_py313_typevar_distutils/python311-with-setuptools/consumer"
    extra["cell_hash"] = digest({k: v for k, v in extra.items() if k != "cell_hash"})
    cells.append(extra)
    cloud = next(row for row in programs if row["program_id"] == "batch100-cloudpickle-507-distutils")
    cloud["additional_exclusion_cells"].append(extra["cell_id"])
    cloud["negative_controls"].append(extra["cell_id"])
    cloud["provider_capsule_ids"] = sorted(set(cloud["provider_capsule_ids"] + ["provider:cloudpickle_507_py313_typevar_distutils:python311-with-setuptools"]))

    for program in programs:
        incident, control = predicates[program["program_id"]]
        old_hash = program["program_hash"]
        program["contract_version"] = "batch101-counterfactual-v3"
        program["incident_predicate"] = incident
        program["control_predicate"] = control
        program["semantic_projection_id"] = "controllergate-semantic-projection-v1"
        program["predicate_language_id"] = "DeclarativePredicateV1"
        program["old_program_hash"] = old_hash
        program["program_hash"] = digest({k: v for k, v in program.items() if k != "program_hash"})

    semantics = []
    supersessions = []
    for program in programs:
        semantic = {
            "program_id": program["program_id"],
            "candidate_id": program["candidate_id"],
            "schema_id": program["expected_semantic_schema"],
            "projection_id": "controllergate-semantic-projection-v1",
            "incident_predicate": program["incident_predicate"],
            "control_predicate": program["control_predicate"],
            "frozen_before_execution": True,
            "truth_derived": False,
            "producer": "build_batch101_counterfactual_contracts",
            "execution_depth": "pre-execution contract freeze",
            "semantic_scope": "candidate outcome semantics",
            "authority_allowed": "declarative semantic classification",
            "authority_forbidden": ["sealed truth access", "causal ownership without matched evidence", "patch", "repair count"],
        }
        semantic["registry_hash"] = digest(semantic)
        semantics.append(semantic)
        supersession = {
            "old_contract_id": program["program_id"] + ":v2",
            "old_contract_hash": program["old_program_hash"],
            "new_contract_id": program["program_id"] + ":v3",
            "new_contract_hash": program["program_hash"],
            "reason": "replace hardcoded outcome authority with declarative predicates and semantic replay projection",
            "batch100_evidence": "official Batch100 extracted evidence plus sealed Batch101 expected-red findings",
            "scientific_meaning_changed": program["program_id"] == "batch100-py-bugger-65-accounting",
            "execution_mechanics_changed": True,
            "approval_boundary": "contract freeze only; no patch or repair-count authority",
            "supersession_timestamp": stamp,
        }
        supersession["supersession_receipt"] = digest(supersession)
        supersessions.append(supersession)

    projection = [{
        "projection_id": "controllergate-semantic-projection-v1",
        "module": "controllergate.evidence.semantic_projection_v1",
        "scientific_fields": ["return_code", "exception_type", "failed_node_count", "semantic_observation", "observed_sentinels", "source_tree_hash_before", "source_tree_hash_after", "test_tree_hash_before", "test_tree_hash_after", "provider_identity", "runtime_attestation_hash", "candidate_state"],
        "raw_evidence_retained": True,
        "frozen_before_execution": True,
        "authority_allowed": "semantic normalization",
        "authority_forbidden": ["discard raw evidence", "ownership", "patch", "repair count"],
    }]
    volatile = [{"field": field, "reason": "execution-local identity or timing", "semantic_authority": False} for field in sorted(("actual_start_time", "actual_end_time", "start_timestamp", "end_timestamp", "monotonic_duration", "operation_id", "execution_id", "nonce", "record_hash", "workspace_identity", "receipt_hash", "semantic_verifier_receipt", "order_position"))]
    predicate_schema = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": "controllergate://DeclarativePredicateV1",
        "title": "DeclarativePredicateV1",
        "supported_operators": ["eq", "ne", "gt", "ge", "lt", "le", "contains", "in", "regex", "exists", "missing", "count", "all", "any", "not", "implies", "derived_relation"],
        "candidate_specific_code_allowed": False,
        "truth_derived_predicates_allowed": False,
    }
    provider_policy = {
        "schema": "controllergate-provider-match-policy-v3",
        "modes": ["EXACT_PROVIDER", "SERIES_LIMITED_PROVIDER", "NEAREST_REPRODUCIBLE_PROVIDER", "UNAVAILABLE_PROVIDER"],
        "exact_fields": ["implementation", "major", "minor", "micro", "prerelease", "operating_system", "architecture", "abi", "soabi"],
        "prefix_matching_authority": False,
        "authority_allowed": "provider classification",
        "authority_forbidden": ["exact parity from prefix matching", "ownership", "patch", "repair count"],
    }

    write_jsonl(CONFIG / "batch101_semantic_projection_registry_v1.jsonl", projection)
    write_jsonl(CONFIG / "batch101_volatile_field_registry_v1.jsonl", volatile)
    write_json(CONFIG / "batch101_predicate_language_schema_v1.json", predicate_schema)
    write_jsonl(CONFIG / "batch101_candidate_outcome_semantics_v1.jsonl", semantics)
    write_jsonl(CONFIG / "batch101_candidate_counterfactual_programs_v3.jsonl", programs)
    write_jsonl(CONFIG / "batch101_counterfactual_cell_registry_v3.jsonl", cells)
    write_jsonl(CONFIG / "batch101_outcome_semantic_registry_v3.jsonl", semantics)
    write_jsonl(CONFIG / "batch101_batch100_contract_supersession_registry_v1.jsonl", supersessions)
    write_jsonl(OUT / "candidate_predicate_registry_v1.jsonl", semantics)
    write_json(OUT / "provider_match_policy_v3.json", provider_policy)
    write_json(OUT / "setuptools_scm_metadata_custody_v1.json", {
        "status": "ENFORCED",
        "allowed_methods": ["exact_tag_object", "exact_reachable_tag_metadata", "preregistered_issue_time_version_environment", "fixed_source_archive_metadata"],
        "candidate_source_mutation_allowed": False,
        "producer": "build_batch101_counterfactual_contracts",
        "execution_depth": "contract freeze",
        "semantic_scope": "source-build version identity",
        "authority_allowed": "build metadata custody",
        "authority_forbidden": ["source mutation", "version fabrication", "causal ownership"],
    })
    print(json.dumps({"programs": len(programs), "cells": len(cells), "predicates": len(semantics), "supersessions": len(supersessions)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
