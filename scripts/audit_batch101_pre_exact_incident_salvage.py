"""Expected-red audit of the untouched Batch100 execution semantics."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "outputs/post_v2_37_hardening_batch101_canonical_semantic_replay_exact_incident_salvage_ownership_closure/batch101_pre_exact_incident_salvage_expected_failure.json"
BOUNDARY_COMMIT = "82e11eb4116516a15ba442456dd89ad53ee6c76e"


FINDINGS = [
    ("batch100_artifact_not_officially_ingested_at_boundary", "outputs/post_v2_37_hardening_batch100_matched_counterfactual_execution_causal_ownership_architecture_gain_master_roadmap_lock", "official_ingest_boundary", "1-1", "The Batch100 handoff explicitly left its artifact un-ingested.", "Officially ingest the exact ZIP before Batch101 science.", "test_official_batch100_ingest"),
    ("hardcoded_candidate_predicate_rules", "scripts/run_batch100_candidate_program.py", "predicate_satisfied", "242-263", "Candidate branches, not the frozen registry, decide scientific predicates.", "Use a frozen declarative predicate evaluator.", "test_hardcoded_candidate_predicates_retired"),
    ("pybugger_inverted_accounting_predicate", "scripts/run_batch100_candidate_program.py", "predicate_satisfied", "245-248", "The predicate requires reported count equality despite the reported inflation incident.", "Use field-to-field inequality and numeric excess predicates.", "test_pybugger_corrected_incident_predicate"),
    ("pybugger_reproducible_evidence_misclassified", "outputs/post_v2_37_hardening_batch101_canonical_semantic_replay_exact_incident_salvage_ownership_closure/batch100_official_ingest/extracted_public_artifact/batch100_clean_replay_registry_v1.jsonl", "py_bugger_issue_65 observations", "1-1", "Reported/successful/persisted counts were 62/7/1 and 49/5/1 but incident materialization was false.", "Re-evaluate raw evidence under the corrected frozen predicate.", "test_pybugger_raw_evidence_salvage"),
    ("whole_dictionary_replay_comparison", "scripts/run_batch100_candidate_program.py", "main replay join", "352-354", "Complete semantic-observation dictionaries are compared directly.", "Compare canonical semantic fingerprints only.", "test_replay_uses_semantic_fingerprint"),
    ("volatile_fields_drive_replay", "scripts/run_batch100_candidate_program.py", "semantic_observation", "211-240", "Output hashes, timings, traces, paths, addresses, and installation paths can vary without semantic change.", "Declare and normalize volatile fields while retaining raw custody.", "test_volatile_fields_excluded"),
    ("raw_and_semantic_identity_conflated", "scripts/run_batch100_candidate_program.py", "execution receipt", "326-354", "One observation object serves both byte custody and scientific reproducibility.", "Persist RawExecutionObservationV1 and CanonicalSemanticObservationV1 separately.", "test_raw_and_semantic_observations_separate"),
    ("pair_valid_before_predicates", "scripts/finalize_batch100_public_execution.py", "pair compilation", "105-143", "Pair labels can be assigned before both incident and control predicates are satisfied.", "Require both predicate receipts before a valid-pair status.", "test_pair_requires_both_materializations"),
    ("factorial_valid_without_complete_cells", "scripts/finalize_batch100_public_execution.py", "factorial join", "105-143", "Factorial validity is not gated on every registered factor corner executing.", "Require complete registered factorial inventory and estimand.", "test_factorial_completeness"),
    ("sensitivity_from_dictionary_inequality", "scripts/finalize_batch100_public_execution.py", "pair compilation", "105-143", "Whole-observation inequality substitutes for a preregistered outcome projection.", "Compute sensitivity from stable projected outcomes.", "test_sensitivity_uses_projection"),
    ("causal_relations_not_computed", "scripts/finalize_batch100_public_execution.py", "evidence receipts", "105-203", "Necessity, sufficiency, and interaction are emitted as not established without executed estimands.", "Compute each relation only from valid executed cells.", "test_causal_relation_computation"),
    ("openbb_unconditional_block", "scripts/run_batch100_candidate_program.py", "main", "295-299", "OpenBB exits before any target execution.", "Materialize the secondary source and brokered loopback fixture.", "test_openbb_no_early_block"),
    ("openbb_secondary_source_absent", "scripts/run_batch100_candidate_program.py", "OpenBB branch", "295-299", "The secondary source is not cloned, served, flattened, or compared.", "Freeze and verify its exact source capsule.", "test_openbb_secondary_capsule"),
    ("openbb_registered_cells_unexecuted", "configs/batch100_counterfactual_cell_registry_v2.jsonl", "OpenBB cell inventory", "1-32", "Four OpenBB cells were registered and none executed.", "Execute or explicitly block every registered cell.", "test_complete_registered_cell_accounting"),
    ("poetry_fixture_basename_not_used", "scripts/run_batch100_candidate_program.py", "prepare_fixture", "176-209", "Fixture metadata names the requested directory but execution uses a generic consumer directory.", "Create and enter the registered basename.", "test_poetry_exact_cwd_basename"),
    ("poetry_generated_consumer_name", "scripts/run_batch100_candidate_program.py", "main cwd selection", "307-326", "Poetry generated project name consumer rather than the incident basename.", "Bind cwd identity to the cell fixture.", "test_poetry_generated_name_matrix"),
    ("poetry_predicates_not_exactly_tested", "scripts/run_batch100_candidate_program.py", "predicate_satisfied", "259-263", "The intended spaces/hyphen incident and control predicates never ran from their declared directories.", "Run the Windows 2x2 and Linux exclusion.", "test_poetry_exact_predicates"),
    ("audioread_pytest_missing", "scripts/run_batch100_candidate_program.py", "install_provider", "159-161", "The Audioread provider omitted pytest.", "Install and independently preflight pytest.", "test_audioread_pytest_preflight"),
    ("audioread_missing_marker_treated_as_control", "scripts/run_batch100_candidate_program.py", "predicate_satisfied", "254-257", "Missing structured evidence was interpreted as a satisfied control predicate.", "Require a structured observation marker for every route.", "test_audioread_missing_marker_blocks"),
    ("pytest_minversion_preflight_failure", "scripts/run_batch100_candidate_program.py", "pytest execution", "229-230", "The installed source identified as pytest 0.1.dev1 and failed its own minversion gate.", "Preserve exact source version metadata and preflight collection.", "test_pytest_source_version_preflight"),
    ("pytest_git_version_metadata_missing", "scripts/build_batch100_source_capsules.py", "source capsule acquisition", "1-240", "Tagless or shallow source custody did not preserve setuptools-scm version identity.", "Freeze exact reachable tag metadata or preregistered packaging-only version input.", "test_setuptools_scm_metadata_custody"),
    ("darker_unrelated_preflight_failure", "scripts/run_batch100_candidate_program.py", "Darker execution", "179-188", "Configuration loading failed before the Git-directory incident layer.", "Require source-derived incident-layer reachability before execution.", "test_darker_incident_layer_preflight"),
    ("darker_release_identity_not_exact", "outputs/post_v2_37_hardening_batch101_canonical_semantic_replay_exact_incident_salvage_ownership_closure/batch100_official_ingest/extracted_public_artifact/matched_counterfactual/source_capsule_registry_v1.jsonl", "Darker source capsule", "1-8", "Parity with reported release 1.2.2 was not established.", "Freeze and verify the exact 1.2.2 tag/commit.", "test_darker_122_identity"),
    ("git_trace_timestamps_semantic", "scripts/run_batch100_candidate_program.py", "semantic_observation", "211-219", "Raw Git trace variation contributes to replay identity.", "Normalize trace timestamps, PIDs, and paths in the semantic projection.", "test_git_trace_normalization"),
    ("cloudpickle_typevar_not_exact", "scripts/run_batch100_candidate_program.py", "Cloudpickle observation", "222-225", "TypeVar tests passed under the selected source/provider combination.", "Resolve the issue-time source and Python provider or block exactly.", "test_cloudpickle_typevar_exact_pair"),
    ("cloudpickle_source_provider_not_tightly_bound", "configs/batch100_incident_provider_registry_v2.jsonl", "Cloudpickle provider identity", "1-13", "The issue-time failing source/provider state is not independently established.", "Freeze source and provider identities at the issue cutoff.", "test_cloudpickle_source_provider_identity"),
    ("cloudpickle_distutils_evidence_understated", "outputs/post_v2_37_hardening_batch101_canonical_semantic_replay_exact_incident_salvage_ownership_closure/batch100_official_ingest/extracted_public_artifact/matched_counterfactual_evidence_v2.jsonl", "batch100-cloudpickle-507-distutils", "1-9", "The executed 3-cell pattern is stronger than presence-only evidence.", "Complete and evaluate the registered 2x2 factorial.", "test_cloudpickle_distutils_factorial"),
    ("cloudpickle_warning_volatility_false_negative", "scripts/run_batch100_candidate_program.py", "replay join", "352-354", "Python 3.11 replay differences were warning-path or timing variation.", "Exclude warning paths and timing from semantic identity.", "test_cloudpickle_warning_normalization"),
    ("freezegun_duration_false_negative", "scripts/run_batch100_candidate_program.py", "replay join", "352-354", "Exact incident/control materialized but pytest duration variation caused nonreproducibility.", "Fingerprint node outcomes and value relations, not duration text.", "test_freezegun_semantic_replay"),
    ("provider_prefix_false_parity", "scripts/run_batch100_candidate_program.py", "provider_matches", "110-142", "Any stable microrelease beginning with the requested major/minor can match.", "Separate exact, series-limited, nearest, and unavailable provider modes.", "test_provider_prefix_false_parity"),
    ("provider_scope_status_conflated", "scripts/run_batch100_candidate_program.py", "provider_matches", "110-142", "Exact parity and series-limited compatibility share one Boolean result.", "Emit explicit provider exactness receipts.", "test_provider_exactness_statuses"),
    ("tagless_build_version_collapse", "scripts/build_batch100_source_capsules.py", "source acquisition", "1-240", "Shallow tagless metadata can collapse a setuptools-scm version.", "Preserve immutable Git version metadata.", "test_tagless_build_version_negative_control"),
    ("raw_output_removed_before_independent_verification", "scripts/build_batch100_counterfactual_contracts.py", "cleanup contract", "78-78", "Workspaces are deleted before a separately isolated verifier can reconstruct raw output.", "Seal raw custody before cleanup and verify independently.", "test_raw_output_custody_before_cleanup"),
    ("semantic_registry_not_sole_authority", "configs/batch100_outcome_semantic_registry_v2.jsonl", "outcome registry", "1-9", "The registry exists but hardcoded candidate branches decide outcomes.", "Make the declarative registry the sole predicate authority.", "test_registry_is_sole_predicate_authority"),
    ("semantic_registry_no_generic_language", "configs/batch100_outcome_semantic_registry_v2.jsonl", "predicate documents", "1-9", "Predicates are descriptive objects without frozen generic evaluation semantics.", "Adopt DeclarativePredicateV1 operators and schema.", "test_declarative_predicate_language"),
    ("stable_volatile_fields_undeclared", "scripts/run_batch100_candidate_program.py", "semantic_observation", "211-240", "Structured observations do not declare stable versus volatile fields.", "Freeze per-cell semantic projection contracts.", "test_projection_declares_stability"),
    ("held_invariants_not_observed", "scripts/finalize_batch100_public_execution.py", "pair compilation", "105-143", "Declared held invariants are copied from contracts rather than proven from observed receipts.", "Join observed invariant receipts before pair validity.", "test_held_invariant_observation_audit"),
    ("pair_stage_concepts_conflated", "scripts/finalize_batch100_public_execution.py", "pair compilation", "105-143", "Materialization, validity, effect, sensitivity, causal relations, and ownership are not distinct stages.", "Emit explicit stage statuses and receipts.", "test_pair_stage_semantic_reconstruction"),
    ("master_ledger_missing_exact_defects", "configs/controllergate_master_completion_ledger_v2.json", "Batch100 goal state", "1-904", "The ledger records readiness and broad blockers but not all exact execution-semantic defects.", "Append defect-bound transition receipts.", "test_batch101_master_ledger_defects"),
    ("batch101_workflow_absent", ".github/workflows", "Batch101 exact salvage workflow", "1-1", "No workflow exists for corrected-cell execution without broad rematerialization.", "Create an isolated Batch101 workflow and matrices.", "test_batch101_workflow_contract"),
]


def main() -> int:
    findings = []
    for index, (finding_id, path, symbol, lines, observed, correction, test) in enumerate(FINDINGS, 1):
        findings.append(
            {
                "finding_number": index,
                "finding_id": finding_id,
                "commit": BOUNDARY_COMMIT,
                "path": path,
                "symbol": symbol,
                "line_range": lines,
                "risk": "Batch100 evidence can be misclassified or overinterpreted without this correction.",
                "observed_batch100_evidence": observed,
                "required_correction": correction,
                "red_to_green_test": test,
            }
        )
    if len(findings) != 40:
        raise RuntimeError(f"expected 40 findings, observed {len(findings)}")
    payload = {
        "status": "BATCH101_PRE_EXACT_INCIDENT_SALVAGE_FAIL_EXPECTED",
        "boundary_commit": BOUNDARY_COMMIT,
        "finding_count": len(findings),
        "findings": findings,
        "authority_allowed": "expected-red implementation planning",
        "authority_forbidden": ["candidate patch", "repair count", "truth inference", "release promotion"],
    }
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    payload["seal_sha256"] = hashlib.sha256(canonical).hexdigest()
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({"status": payload["status"], "finding_count": len(findings), "seal_sha256": payload["seal_sha256"]}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
