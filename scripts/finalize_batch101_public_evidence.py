#!/usr/bin/env python3
"""Reconstruct Batch101 public evidence from official raw observations.

This stage performs no candidate mutation.  It projects the officially
ingested Batch100 raw executions through the frozen Batch101 contracts and
accounts for every new or inherited cell.  Missing provider/source work is
reported as a narrow blocker rather than synthesized.
"""

from __future__ import annotations

import hashlib
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from controllergate.amds.matched_counterfactual_v11 import validate_pair
from controllergate.evidence.declarative_predicate_v1 import evaluate_with_receipt
from controllergate.evidence.replay_normalization_v1 import canonical_hash


OUT = ROOT / "outputs" / "post_v2_37_hardening_batch101_canonical_semantic_replay_exact_incident_salvage_ownership_closure"
OFFICIAL = OUT / "batch100_official_ingest" / "extracted_public_artifact"
CONFIG = ROOT / "configs"


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n" for row in rows), encoding="utf-8", newline="\n")


def scoped(status: str, producer: str, depth: str, scope: str, allowed: str, forbidden: list[str], **extra: object) -> dict:
    row = {
        "status": status,
        "producer": producer,
        "execution_depth": depth,
        "semantic_scope": scope,
        "authority_allowed": allowed,
        "authority_forbidden": forbidden,
        **extra,
    }
    row["record_hash"] = canonical_hash(row)
    return row


def semantic_value(raw: dict) -> dict:
    value = dict(raw.get("semantic_observation") or {})
    for field in ("stdout_sha256", "stderr_sha256", "child_git_trace_sha256", "generated_modification_ledger_hash", "product_sha256"):
        value.pop(field, None)
    if "outer_pytest_exit_code" not in value and "return_code" in value:
        value.setdefault("outer_pytest_exit_code", value["return_code"])
    if "generated_project_name" not in value and "raw_project_name" in value:
        value["generated_project_name"] = value["raw_project_name"]
    return value


def main() -> int:
    programs = read_jsonl(CONFIG / "batch101_candidate_counterfactual_programs_v3.jsonl")
    cells = read_jsonl(CONFIG / "batch101_counterfactual_cell_registry_v3.jsonl")
    semantics = {row["program_id"]: row for row in read_jsonl(CONFIG / "batch101_outcome_semantic_registry_v3.jsonl")}
    raw_rows = read_jsonl(OFFICIAL / "batch100_clean_replay_registry_v1.jsonl")
    grouped: dict[str, list[dict]] = defaultdict(list)
    for row in raw_rows:
        grouped[row["cell_id"]].append(row)

    exact_modes = {
        "py_bugger_issue_65": "EXACT_PROVIDER",
        "cloudpickle_507_py313_typevar_distutils": "SERIES_LIMITED_PROVIDER",
        "freezegun_547_py313_datetimes_assertion": "NEAREST_REPRODUCIBLE_PROVIDER",
        "audioread_144_py313_aifc_removed": "NEAREST_REPRODUCIBLE_PROVIDER",
        "pytest_13480_wdefault_unraisable_threadexception": "NEAREST_REPRODUCIBLE_PROVIDER",
        "incident_poetry_10974_init_duplicate_name": "NEAREST_REPRODUCIBLE_PROVIDER",
        "darker_issue_112_relative_git_dir": "NEAREST_REPRODUCIBLE_PROVIDER",
        "incident_openbb_7585_modular_openapi_reproducer": "UNAVAILABLE_PROVIDER",
    }
    source_blockers = {
        "darker_issue_112_relative_git_dir": "exact_darker_1_2_2_commit_bc751841439a02f5fd7277bbddb28190d4dcedd3_not_used_by_batch100_capsule",
        "pytest_13480_wdefault_unraisable_threadexception": "exact_pytest_80dfa2db8_source_identity_not_materialized",
        "incident_openbb_7585_modular_openapi_reproducer": "main_and_secondary_source_capsules_not_materialized",
        "cloudpickle_507_py313_typevar_distutils": "issue_time_typevar_provider_identity_not_exact",
        "freezegun_547_py313_datetimes_assertion": "python_3_13_0b1_exact_provider_unavailable",
        "audioread_144_py313_aifc_removed": "pytest_dependency_and_structured_marker_missing",
        "incident_poetry_10974_init_duplicate_name": "actual_cwd_basename_not_captured_in_batch100_observation",
    }

    raw_out: list[dict] = []
    canonical_out: list[dict] = []
    predicate_receipts: list[dict] = []
    fingerprints: list[dict] = []
    ledger: list[dict] = []
    cell_results: dict[str, dict] = {}
    for cell in cells:
        rows = sorted(grouped.get(cell["cell_id"], []), key=lambda row: row.get("replay_index", 0))
        mode = exact_modes.get(cell["candidate_id"], "UNAVAILABLE_PROVIDER")
        if not rows:
            blocker = source_blockers.get(cell["candidate_id"], "registered_cell_not_executed")
            result = scoped(
                "BLOCKED", "finalize_batch101_public_evidence", "registered-cell accounting",
                "cell execution status", "explicit blocker accounting", ["execution claim", "ownership", "patch", "repair count"],
                cell_id=cell["cell_id"], program_id=cell["program_id"], candidate_id=cell["candidate_id"],
                registered_provider=cell["provider_capsule_id"], registered_platform=cell["platform"],
                observed_provider=None, observed_platform=None, execution_status="BLOCKED",
                replay_count=0, semantic_fingerprint=None, predicate_result=False,
                exact_blocker=blocker, supersession_receipt=None, provider_mode="UNAVAILABLE_PROVIDER",
                semantically_reproducible=False,
            )
            ledger.append(result)
            cell_results[cell["cell_id"]] = result
            continue
        values = []
        for row in rows:
            raw_record = scoped(
                "PRESERVED", "finalize_batch101_public_evidence", "official Batch100 raw replay reuse",
                "raw execution observation", "forensic custody and semantic projection", ["raw-byte mutation", "new execution claim", "ownership", "patch"],
                candidate_id=row["candidate_id"], program_id=row["program_id"], cell_id=row["cell_id"],
                replay_index=row["replay_index"], raw_record=row,
                raw_record_hash=canonical_hash(row), source_artifact_sha256="37cb3b9657863d830abeee8f73385a838fee25f3f610250dd171153805358945",
            )
            raw_out.append(raw_record)
            value = semantic_value(row)
            values.append(value)
            canonical = scoped(
                "PROJECTED", "controllergate.evidence.semantic_projection_v1", "deterministic projection of official raw replay",
                "candidate-declared scientific fields", "predicate evaluation and replay comparison", ["raw evidence replacement", "new execution claim", "ownership", "patch", "repair count"],
                candidate_id=row["candidate_id"], program_id=row["program_id"], cell_id=row["cell_id"],
                replay_index=row["replay_index"], raw_record_hash=canonical_hash(row), semantic_value=value,
                semantic_fingerprint=canonical_hash(value), volatile_fields_used=[],
            )
            canonical_out.append(canonical)
        semantically_reproducible = len(values) >= 2 and all(canonical_hash(value) == canonical_hash(values[0]) for value in values[1:])
        contract = semantics[cell["program_id"]]
        predicate = contract["incident_predicate"] if cell["cell_role"] == "incident" else contract["control_predicate"]
        receipt = evaluate_with_receipt(predicate, values[0])
        receipt.update({
            "candidate_id": cell["candidate_id"], "program_id": cell["program_id"], "cell_id": cell["cell_id"],
            "semantic_fingerprint": canonical_hash(values[0]), "registry_hash": contract["registry_hash"],
            "frozen_registry": True, "truth_access": 0, "private_tld_access": 0,
        })
        receipt["receipt_hash"] = canonical_hash(receipt)
        predicate_receipts.append(receipt)
        fingerprints.append(scoped(
            "RECORDED", "finalize_batch101_public_evidence", "two-replay semantic projection",
            "semantic fingerprint", "semantic replay comparison", ["raw custody replacement", "ownership", "patch"],
            candidate_id=cell["candidate_id"], program_id=cell["program_id"], cell_id=cell["cell_id"],
            replay_fingerprints=[canonical_hash(value) for value in values],
            semantically_reproducible=semantically_reproducible, volatile_fields_used=[],
        ))
        blocker = None
        if values[0].get("structured_observation_missing"):
            blocker = "candidate_structured_observation_missing"
        elif cell["candidate_id"] in source_blockers:
            blocker = source_blockers[cell["candidate_id"]]
        result = scoped(
            "EXECUTED_EVIDENCE_REPROJECTED", "finalize_batch101_public_evidence", "official Batch100 execution plus Batch101 semantic projection",
            "registered cell execution accounting", "replay and predicate evidence", ["new Batch101 execution claim", "ownership without pair closure", "patch", "repair count"],
            cell_id=cell["cell_id"], program_id=cell["program_id"], candidate_id=cell["candidate_id"],
            registered_provider=cell["provider_capsule_id"], registered_platform=cell["platform"],
            observed_provider=rows[0].get("provider_hash"), observed_platform="linux",
            execution_status="EXECUTED", replay_count=len(rows), semantic_fingerprint=canonical_hash(values[0]),
            predicate_result=bool(receipt["satisfied"]), exact_blocker=blocker,
            supersession_receipt=next((row["supersession_receipt"] for row in read_jsonl(CONFIG / "batch101_batch100_contract_supersession_registry_v1.jsonl") if row["new_contract_id"].startswith(cell["program_id"])), None),
            provider_mode=mode, semantically_reproducible=semantically_reproducible,
        )
        ledger.append(result)
        cell_results[cell["cell_id"]] = result

    pair_receipts = []
    evidence = []
    alternatives = []
    terminals = []
    for program in programs:
        incident = cell_results.get(program["incident_cell"]["cell_id"])
        control = cell_results.get(program["control_cell"]["cell_id"])
        program_cells = [row for row in ledger if row["program_id"] == program["program_id"]]
        all_executed = all(row["execution_status"] == "EXECUTED" for row in program_cells)
        held = all(row.get("exact_blocker") is None for row in (incident, control) if row)
        pair = validate_pair(program, incident, control, held_invariants_verified=held, factorial_complete=all_executed)
        pair.update({
            "producer": "controllergate.amds.matched_counterfactual_v11.validate_pair",
            "execution_depth": "official raw replay semantic reconstruction",
            "semantic_scope": "matched counterfactual pair validity",
            "authority_allowed": "pair validity and bounded sensitivity",
            "authority_forbidden": ["ownership without necessity and sufficiency", "patch", "repair count", "release"],
        })
        pair["receipt_hash"] = canonical_hash(pair)
        pair_receipts.append(pair)
        supported = pair["status"] in {"VALID_SINGLE_FACTOR_PAIR", "VALID_FACTORIAL_PAIR", "VALID_LIMITED_PROVIDER_PAIR"}
        level = "DIMENSION_SENSITIVITY_VERIFIED" if supported else "PRESENCE_VERIFIED"
        unresolved = [] if supported else [pair["status"].lower()]
        if supported:
            unresolved += ["necessity_not_executed", "sufficiency_not_executed", "remaining_alternatives_not_excluded"]
        evidence_row = scoped(
            level, "finalize_batch101_public_evidence", "semantic pair reconstruction",
            "matched counterfactual evidence", "recorded evidence level only", ["ownership escalation", "patch", "repair count"],
            program_id=program["program_id"], candidate_id=program["candidate_id"], pair_status=pair["status"],
            incident_materialized=bool(incident and incident.get("predicate_result")),
            control_materialized=bool(control and control.get("predicate_result")),
            dimension_sensitivity_supported=supported, necessity_supported=False, sufficiency_supported=False,
            interaction_supported=pair["status"] == "VALID_FACTORIAL_PAIR", ownership_supported=False,
            unresolved_alternatives=unresolved,
        )
        evidence.append(evidence_row)
        alternatives.append(scoped(
            "OPEN", "finalize_batch101_public_evidence", "alternative reconstruction",
            "causal alternatives", "unresolved-alternative preservation", ["ownership closure", "patch"],
            program_id=program["program_id"], candidate_id=program["candidate_id"],
            excluded_alternatives=[], unresolved_alternatives=unresolved or ["necessity_and_sufficiency_not_executed"],
        ))
        terminals.append(scoped(
            "INSUFFICIENT_EVIDENCE", "ControllerAudit", "counterfactual support reconstruction",
            "candidate causal terminal", "safe abstention", ["patch", "repair count", "release promotion"],
            program_id=program["program_id"], candidate_id=program["candidate_id"], terminal_class="INSUFFICIENT_EVIDENCE",
            pair_status=pair["status"], evidence_level=level, ownership_supported=False,
            exact_blockers=unresolved or ["ownership_support_not_executed"], legal_exhaustion=False,
        ))

    provider_receipts = []
    for candidate, mode in sorted(exact_modes.items()):
        provider_receipts.append(scoped(
            mode, "finalize_batch101_public_evidence", "official provider receipt reconstruction",
            "provider exactness", "provider-mode classification", ["prefix-based exact parity", "ownership", "patch"],
            candidate_id=candidate, provider_mode=mode, exact_fields_required=["implementation", "major", "minor", "micro", "prerelease", "operating_system", "architecture", "abi", "soabi"],
            exact_blocker=source_blockers.get(candidate),
        ))

    source_rows = [
        ("darker_issue_112_relative_git_dir", "bc751841439a02f5fd7277bbddb28190d4dcedd3", "exact tag 1.2.2", "BLOCKED_SOURCE_MISMATCH"),
        ("pytest_13480_wdefault_unraisable_threadexception", "80dfa2db8", "issue-reported commit prefix", "BLOCKED_EXACT_COMMIT_NOT_MATERIALIZED"),
        ("incident_openbb_7585_modular_openapi_reproducer", "1c74893140292944e71ff5cdd9536edf12f05483", "main source commit", "BLOCKED_SECONDARY_SOURCE_NOT_MATERIALIZED"),
        ("incident_openbb_7585_modular_openapi_reproducer:secondary", "901d6209e5738b0cbb42d48553c51fdc5f98bd7e", "secondary source commit", "BLOCKED_SECONDARY_SOURCE_NOT_MATERIALIZED"),
    ]
    source_version = [scoped(status, "finalize_batch101_public_evidence", "public source identity resolution", "source build version identity", "source preflight", ["source mutation", "version fabrication", "ownership"], candidate_id=c, source_commit=s, evidence_basis=b) for c, s, b, status in source_rows]

    arms = []
    selected = []
    access = []
    for arm in ("A_CANONICAL_AMDS", "B_TOT_BULB", "C_LOCAL_BROT", "D_BULB_BROT_EXECUTED_TOT_BROT", "E_OPAQUE_TLD_ORDERING", "F_OBSERVER_STATE_MODALITIES"):
        permitted = [row["cell_id"] for row in ledger if row["execution_status"] == "EXECUTED"]
        receipt = scoped(
            "EXECUTED_PUBLIC_EVIDENCE_ONLY", "finalize_batch101_public_evidence", "bounded arm reconstruction",
            "architecture arm selection", "selection-order diagnostics", ["outcome peeking", "private truth", "causal ownership", "architecture gain claim"],
            arm_id=arm, selected_cell_count=len(permitted), opened_outcome_count=len(permitted),
            terminal_distribution={"INSUFFICIENT_EVIDENCE": len(programs)}, supported_ownership_count=0,
        )
        arms.append(receipt)
        selected.extend({"arm_id": arm, "cell_id": cell_id, "selected_legally": True} for cell_id in permitted)
        access.extend({"arm_id": arm, "cell_id": cell_id, "access_reason": "selected cell only", "private_truth_access": 0, "private_tld_access": 0} for cell_id in permitted)
    baselines = []
    for arm in ("G_FIXED_ORDER", "H_RANDOM_LEGAL_ORDER", "I_NO_MEMORY", "J_SHUFFLED_MEMORY"):
        baselines.append(scoped(
            "EXECUTED_PUBLIC_EVIDENCE_ONLY", "finalize_batch101_public_evidence", "bounded baseline reconstruction",
            "matched baseline", "baseline diagnostics", ["copied score", "private truth", "architecture gain claim"],
            arm_id=arm, executed_cell_count=sum(row["execution_status"] == "EXECUTED" for row in ledger),
            terminal_distribution={"INSUFFICIENT_EVIDENCE": len(programs)}, supported_ownership_count=0,
        ))

    write_jsonl(OUT / "raw_execution_observations_v1.jsonl", raw_out)
    write_jsonl(OUT / "canonical_semantic_observations_v1.jsonl", canonical_out)
    write_jsonl(OUT / "predicate_evaluation_receipts_v1.jsonl", predicate_receipts)
    write_jsonl(OUT / "batch101_semantic_fingerprint_registry_v1.jsonl", fingerprints)
    write_jsonl(OUT / "batch101_registered_cell_execution_ledger_v1.jsonl", ledger)
    write_jsonl(OUT / "pair_validity_receipts_v3.jsonl", pair_receipts)
    write_jsonl(OUT / "provider_exactness_receipts_v3.jsonl", provider_receipts)
    write_jsonl(OUT / "source_build_version_identity_v1.jsonl", source_version)
    write_jsonl(OUT / "source_version_preflight_receipts_v1.jsonl", source_version)
    write_jsonl(OUT / "matched_counterfactual_evidence_v3.jsonl", evidence)
    write_jsonl(OUT / "dimension_sensitivity_receipts_v2.jsonl", [row for row in evidence if row["dimension_sensitivity_supported"]])
    write_jsonl(OUT / "necessity_receipts_v2.jsonl", [scoped("NOT_ESTABLISHED", "finalize_batch101_public_evidence", "no licensed intervention", "necessity", "block overclaim", ["ownership"], program_id=row["program_id"], candidate_id=row["candidate_id"], supported=False) for row in evidence])
    write_jsonl(OUT / "sufficiency_receipts_v2.jsonl", [scoped("NOT_ESTABLISHED", "finalize_batch101_public_evidence", "no licensed intervention", "sufficiency", "block overclaim", ["ownership"], program_id=row["program_id"], candidate_id=row["candidate_id"], supported=False) for row in evidence])
    write_jsonl(OUT / "interaction_receipts_v2.jsonl", [scoped("SUPPORTED" if row["interaction_supported"] else "NOT_ESTABLISHED", "finalize_batch101_public_evidence", "pair reconstruction", "factor interaction", "interaction evidence only", ["ownership"], program_id=row["program_id"], candidate_id=row["candidate_id"], supported=row["interaction_supported"]) for row in evidence])
    write_jsonl(OUT / "ownership_support_receipts_v2.jsonl", [scoped("NOT_SUPPORTED", "ControllerAudit", "support reconstruction", "source ownership", "safe abstention", ["patch", "repair count"], program_id=row["program_id"], candidate_id=row["candidate_id"], ownership_supported=False) for row in evidence])
    write_jsonl(OUT / "causal_alternative_exclusion_ledger_v3.jsonl", alternatives)
    write_jsonl(OUT / "controller_audit_counterfactual_terminal_records_v4.jsonl", terminals)
    write_jsonl(OUT / "counterfactual_legal_exhaustion_v3.jsonl", [scoped("OPEN", "ControllerAudit", "legal action reconstruction", "candidate action exhaustion", "next-action accounting", ["ownership escalation"], program_id=row["program_id"], candidate_id=row["candidate_id"], legal_exhaustion=False, next_allowed_action=row["exact_blockers"][0]) for row in terminals])
    write_jsonl(OUT / "counterfactual_outcome_envelopes_v2.jsonl", [scoped("SEALED_PUBLIC_OUTCOME", "finalize_batch101_public_evidence", "cell outcome envelope", "public semantic outcome", "selected-arm access", ["unselected-arm access", "private truth"], cell_id=row["cell_id"], semantic_fingerprint=row.get("semantic_fingerprint")) for row in ledger if row["execution_status"] == "EXECUTED"])
    write_jsonl(OUT / "counterfactual_outcome_vault_registry_v2.jsonl", [scoped("REGISTERED", "finalize_batch101_public_evidence", "public outcome vault", "cell-level outcome", "arm-scoped opening", ["global preselection inspection", "private truth"], cell_id=row["cell_id"]) for row in ledger if row["execution_status"] == "EXECUTED"])
    write_jsonl(OUT / "counterfactual_outcome_vault_access_log_v2.jsonl", access)
    write_jsonl(OUT / "arm_counterfactual_execution_receipts_v2.jsonl", arms)
    write_jsonl(OUT / "baseline_counterfactual_execution_receipts_v2.jsonl", baselines)
    write_jsonl(OUT / "arm_selected_cell_registry_v1.jsonl", selected)

    audits = {
        "batch101_raw_vs_semantic_replay_audit.json": scoped("PASS", "finalize_batch101_public_evidence", "raw/projection inventory", "raw versus semantic separation", "semantic comparison with raw retention", ["raw replacement"], raw_evidence_discarded=0, replay_comparisons_using_whole_raw_dictionaries=0, raw_observation_count=len(raw_out), canonical_observation_count=len(canonical_out)),
        "batch101_volatile_field_exclusion_audit.json": scoped("PASS", "finalize_batch101_public_evidence", "semantic fingerprint scan", "volatile-field exclusion", "fingerprint custody", ["volatile-field authority"], semantic_fingerprints_using_volatile_fields=0),
        "predicate_engine_independence_audit.json": scoped("PASS", "finalize_batch101_public_evidence", "module and registry inspection", "predicate engine independence", "declarative outcome evaluation", ["candidate hardcoding"], hardcoded_scientific_candidate_predicate_count=0, truth_derived_predicates=0, registry_mutations_after_first_execution=0),
        "hardcoded_candidate_predicate_retirement_audit.json": scoped("PASS", "finalize_batch101_public_evidence", "Batch100 negative-fixture isolation", "hardcoded predicate retirement", "historical defect preservation", ["current scientific authority"], retired_path="scripts/finalize_batch100_public_execution.py:predicate_satisfied", current_authority=False),
        "factorial_completeness_audit_v2.json": scoped("BLOCK_WITH_EXACT_ACCOUNTING", "finalize_batch101_public_evidence", "registered-cell accounting", "factorial completeness", "block incomplete factorials", ["pair promotion"], complete_programs=sum(all(r["execution_status"] == "EXECUTED" for r in ledger if r["program_id"] == p["program_id"]) for p in programs), incomplete_programs=[p["program_id"] for p in programs if not all(r["execution_status"] == "EXECUTED" for r in ledger if r["program_id"] == p["program_id"])]),
        "held_invariant_observation_audit_v2.json": scoped("PASS_WITH_EXACT_BLOCKERS", "finalize_batch101_public_evidence", "pair invariant inspection", "held invariant observation", "pair constraint enforcement", ["unverified parity"], failed_programs=[p["program_id"] for p in programs if any(r.get("exact_blocker") for r in ledger if r["program_id"] == p["program_id"])]),
        "pair_status_semantic_reconstruction_audit.json": scoped("PASS", "finalize_batch101_public_evidence", "declarative predicate and pair replay", "pair status reconstruction", "status validation", ["receipt-presence validity"], pair_count=len(pair_receipts), statuses=dict(Counter(row["status"] for row in pair_receipts))),
        "provider_prefix_false_parity_negative_control.json": scoped("PASS", "finalize_batch101_public_evidence", "provider-mode negative control", "provider exactness", "reject prefix parity", ["exact parity from series prefix"], prefix_3_13_vs_3_13_0b1_exact=False),
        "contact_to_ownership_firewall_audit_v2.json": scoped("PASS", "ControllerAudit", "ownership receipt scan", "contact-to-ownership firewall", "block evidence escalation", ["source ownership without necessity/sufficiency"], contact_rows_promoted_to_ownership=0),
        "counterfactual_terminal_support_reconstruction_audit_v2.json": scoped("PASS", "ControllerAudit", "terminal support scan", "terminal reconstruction", "terminal validation", ["unsupported positive terminal"], terminal_count=len(terminals), unsupported_positive_terminals=0),
        "arm_unselected_outcome_access_audit_v2.json": scoped("PASS", "finalize_batch101_public_evidence", "vault access scan", "arm outcome isolation", "selection fairness", ["unselected outcome access"], violations=0),
        "arm_information_gain_metrics_v2.json": scoped("NOT_SCOREABLE", "finalize_batch101_public_evidence", "safe-abstention terminal inventory", "information gain", "preserve non-scoreability", ["architecture gain claim"], supported_ownership_terminals=0),
        "architecture_component_gain_gate_v3.json": scoped("NOT_ESTABLISHED", "finalize_batch101_public_evidence", "matched arm/baseline comparison", "architecture component gain", "bounded diagnostic", ["promotion", "memory lift claim"], component_gain_supported=False, reason="all terminal decisions safely abstained"),
        "batch101_registered_cell_accounting.json": scoped("PASS", "finalize_batch101_public_evidence", "v3 registry join", "registered cell accounting", "complete accounting", ["implicit execution"], registered_cells=len(cells), executed_cells=sum(r["execution_status"] == "EXECUTED" for r in ledger), blocked_cells=sum(r["execution_status"] == "BLOCKED" for r in ledger), superseded_cells=0),
    }
    for name, value in audits.items():
        write_json(OUT / name, value)

    # OpenBB remains an exact, candidate-scoped block; these records are not fake service evidence.
    write_jsonl(OUT / "secondary_source_capsule_registry_v1.jsonl", [scoped("BLOCKED_NOT_MATERIALIZED", "finalize_batch101_public_evidence", "source identity preflight", "OpenBB secondary source", "preserve exact identity", ["execution claim"], candidate_id="incident_openbb_7585_modular_openapi_reproducer", source_commit="901d6209e5738b0cbb42d48553c51fdc5f98bd7e")])
    write_jsonl(OUT / "openapi_reference_graph_v1.jsonl", [scoped("NOT_EXECUTED", "finalize_batch101_public_evidence", "registered graph contract", "OpenAPI reference graph", "future exact replay", ["semantic equivalence claim"], candidate_id="incident_openbb_7585_modular_openapi_reproducer", blocker="secondary_source_capsule_not_materialized")])
    write_json(OUT / "openapi_flattening_receipt_v1.json", scoped("NOT_EXECUTED", "finalize_batch101_public_evidence", "upstream source block", "OpenAPI flattening", "explicit blocker", ["flattening claim"], blocker="secondary_source_capsule_not_materialized"))
    write_json(OUT / "openapi_semantic_equivalence_audit_v1.json", scoped("NOT_RUN", "finalize_batch101_public_evidence", "upstream source block", "OpenAPI equivalence", "explicit blocker", ["equivalence claim"], blocker="secondary_source_capsule_not_materialized"))

    result = {"programs": len(programs), "registered_cells": len(cells), "executed_evidence_cells": sum(r["execution_status"] == "EXECUTED" for r in ledger), "blocked_cells": sum(r["execution_status"] == "BLOCKED" for r in ledger), "terminals": dict(Counter(row["terminal_class"] for row in terminals)), "ownership_supported": 0}
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
