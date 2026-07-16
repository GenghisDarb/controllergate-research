from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BATCH092 = ROOT / "outputs/post_v2_37_hardening_batch092_reactome_complete_pathway_ir_external_review_correction"
OUTPUT = ROOT / "outputs/post_v2_37_hardening_batch093_structured_rpir_executable_isomorphism_amds_role_cohort_closure"
EXPECTED = "BATCH093_PRE_FIX_AUDIT_FAIL_EXPECTED"


def _sha(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _finding(finding_id: str, path: str, symbol: str, line_range: str, raw_evidence: object, risk: str, correction: str, test: str) -> dict[str, object]:
    return {
        "finding_id": finding_id,
        "commit": "09626d3e994a6f397f4e14f83032a3f781d16047",
        "path": path,
        "symbol": symbol,
        "line_range": line_range,
        "raw_evidence": raw_evidence,
        "risk": risk,
        "required_correction": correction,
        "red_to_green_test": test,
        "status": "EXPECTED_RED",
    }


def main() -> int:
    coverage = json.loads((BATCH092 / "reactome_source_coverage.json").read_text(encoding="utf-8"))
    quality = json.loads((BATCH092 / "amds_quality_gate.json").read_text(encoding="utf-8"))
    translation = json.loads((BATCH092 / "reactome_translation_coverage.json").read_text(encoding="utf-8"))
    role_rows = [json.loads(line) for line in (BATCH092 / "amds_role_identity_receipts.jsonl").read_text(encoding="utf-8").splitlines() if line]
    findings = [
        _finding("B093-PREF-001", "controllergate/reactome_ir/ingest.py", "PARSER_IDENTITY", "14", "pymupdf_text_v1", "PDF text occurrences are not a structured reaction graph.", "Bind RPIR v2 to exact release-97 structured exports.", "test_structured_source_receipts"),
        _finding("B093-PREF-002", "controllergate/reactome_ir/ingest.py", "_field", "50-54", "label extraction from page text", "Missing labels collapse not-exposed and explicit-empty states.", "Use typed field-state wrappers.", "test_field_state_distinctions"),
        _finding("B093-PREF-003", "controllergate/reactome_ir/ingest.py", "_event_record", "77-139", "participant fields originate in PDF labels", "Participants, catalysts, regulators, and compartments are not machine-grounded.", "Populate fields from structured edges.", "test_structured_participant_grounding"),
        _finding("B093-PREF-004", "controllergate/reactome_ir/ingest.py", "_insert_event", "143-205", "one synthetic reaction_subject per event", "Synthetic subjects are not Reactome physical entities.", "Persist real stable entity identities.", "test_entity_identity_from_export"),
        _finding("B093-PREF-005", "controllergate/reactome_ir/ingest.py", "_insert_event", "187-190", "UNRESOLVED_NORMAL_EVENT_ID", "Disease variants are not linked to structured normal events.", "Resolve normalReaction and normalPathway edges.", "test_normal_variant_links"),
        _finding("B093-PREF-006", "controllergate/reactome_ir/schema.py", "RPIR_VERSION", "6", "controllergate-rpir-v1", "The schema cannot encode field provenance states.", "Create controllergate-rpir-v2.", "test_rpir_v2_schema"),
        _finding("B093-PREF-007", "controllergate/reactome_ir/schema.py", "rpir_schema", "18-39", "untyped empty properties", "Empty schema properties permit semantic collapse.", "Define typed wrappers and constraints.", "test_rpir_v2_validation"),
        _finding("B093-PREF-008", "controllergate/isomorphism/primitives.py", "apply_primitive", "35-46", "all primitive IDs append the same trace", "Named primitives have no distinct transition semantics.", "Implement primitive-specific preconditions and state changes.", "test_primitive_semantic_distinctness"),
        _finding("B093-PREF-009", "controllergate/isomorphism/primitives.py", "primitive_registry", "19-32", "one repeated input/output contract", "Vocabulary registration is not executable semantics.", "Publish distinct primitive contracts.", "test_primitive_contract_distinctness"),
        _finding("B093-PREF-010", "controllergate/isomorphism/compiler.py", "compile_translation", "1-220", translation, "Keyword routing does not derive contracts from structured topology.", "Compile from RPIR v2 participants, controls, and edges.", "test_structural_translation_compiler"),
        _finding("B093-PREF-011", "outputs/.../reactome_translation_coverage.json", "dispositions", "n/a", translation["dispositions"], "Schema coverage can be mistaken for execution.", "Separate structural, shadow, installed, and product depths.", "test_translation_depth_firewall"),
        _finding("B093-PREF-012", "controllergate/isomorphism/scenarios.py", "chapter_scenarios", "1-260", "representative scenarios are registry-defined", "Scenario inputs are not proved source-derived.", "Derive scenarios from RPIR v2 stable IDs.", "test_source_derived_scenarios"),
        _finding("B093-PREF-013", "scripts/run_batch092_installed_scenarios.py", "main", "1-220", "installed wrapper executes scenario summaries", "Installed reachability does not prove canonical stage integration.", "Route through canonical registry, broker, and SQLite events.", "test_installed_canonical_reachability"),
        _finding("B093-PREF-014", "scripts/run_batch092_causal_authority.py", "role evidence mapping", "1-420", {"receipt_count": len(role_rows)}, "Legacy files are assigned fresh semantic role names.", "Create role-specific decision-time producers and verifiers.", "test_role_measurement_producers"),
        _finding("B093-PREF-015", "outputs/.../amds_role_identity_receipts.jsonl", "role receipts", "n/a", {"reuse_without_equivalence": quality["role_identity_reuse_without_equivalence_count"]}, "Receipt reuse prevents cohort eligibility.", "Measure each role or prove equivalence.", "test_no_unproved_role_reuse"),
        _finding("B093-PREF-016", "scripts/run_batch092_causal_authority.py", "candidate_paths", "1-420", "Batch014/Batch039 legacy summaries", "Decision-time facts are not reconstructed from raw candidate trees.", "Use frozen raw decision-time capsules.", "test_frozen_decision_time_inputs"),
        _finding("B093-PREF-017", "outputs/.../amds_quality_gate.json", "eligible_cohort_count", "n/a", quality["eligible_cohort_count"], "The eight-episode minimum cohort is not eligible.", "Freeze and verify the exact cohort before probing.", "test_exact_eight_episode_cohort"),
        _finding("B093-PREF-018", "outputs/.../amds_quality_gate.json", "executed_episode_count", "n/a", quality["executed_episode_count"], "No historical AMDS episode executed.", "Execute canonical causal-board episodes only after eligibility.", "test_amds_execution_gate"),
        _finding("B093-PREF-019", "outputs/.../amds_quality_gate.json", "contradiction_count", "n/a", quality["contradiction_count"], "Contradiction/backtracking remains unexercised.", "Execute reachable contradiction fixtures.", "test_reachable_contradiction_backtrack"),
        _finding("B093-PREF-020", "outputs/.../amds_executed_baselines.json", "baseline results", "n/a", "NOT_RUN under cohort block", "Baseline quality is not established.", "Run equal-budget baselines only for a frozen eligible cohort.", "test_actual_baseline_execution"),
        _finding("B093-PREF-021", "outputs/.../human_authorization_receipts.jsonl", "authorization", "n/a", "PENDING_OFFICIAL_WORKFLOW_BINDING", "Repository-generated intent is not external human authority.", "Consume protected-environment or detached external approval.", "test_external_human_authority"),
        _finding("B093-PREF-022", "outputs/.../historical_lifecycle_results.json", "lifecycles", "n/a", "BLOCKED_BY_AMDS_AND_AUTHORITY", "Historical lifecycles have no corrected authority chain.", "Keep actuation blocked until AMDS and authorization pass.", "test_historical_actuation_gate"),
        _finding("B093-PREF-023", "outputs/.../canary_and_rollback_decision.json", "deployment", "n/a", "NOT_RUN", "Real package-slot lifecycle is not revalidated under corrected authority.", "Run broker-backed slots only after authority.", "test_slot_lifecycle_gate"),
        _finding("B093-PREF-024", "scripts/batch092_standalone_critic.py", "critic inputs", "1-420", "compact evidence reconstruction", "Mutation depth does not include structured RPIR v2 and fresh role receipts.", "Rebuild critic over copied raw Batch093 evidence.", "test_batch093_raw_critic"),
        _finding("B093-PREF-025", "outputs/.../reactome_source_coverage.json", "source coverage", "n/a", coverage, "Occurrence coverage can be laundered into semantic-graph coverage.", "Publish a dimension-specific reconciliation.", "test_coverage_dimension_reconciliation"),
        _finding("B093-PREF-026", "outputs/.../reactome_reactions.jsonl", "reaction rows", "n/a", {"occurrences": 16814, "unique_stable_ids": 16107}, "Shared chapter occurrences are not structural duplicates.", "Join occurrence coverage to one canonical structured event per stable ID.", "test_occurrence_structural_join"),
        _finding("B093-PREF-027", "outputs/.../batch092_internal_release_decision.json", "release boundary", "n/a", "PRODUCT_BETA_RC_BLOCKED_EXACT", "Release remains blocked and must not be promoted by source coverage alone.", "Require all Batch093 internal criteria and keep external review pending.", "test_external_review_pending_v3_boundary"),
    ]
    result = {
        "status": EXPECTED,
        "producer": "scripts/audit_batch093_pre_fix_structured_rpir_and_role_cohort.py",
        "execution_depth": "source_and_artifact_external_review_reconstruction",
        "semantic_scope": "Batch092 structured-semantic and AMDS role-cohort authority",
        "authority_allowed": "expected-red implementation requirements",
        "authority_forbidden": ["release approval", "repair authority", "production promotion"],
        "observed_head": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
        "finding_count": len(findings),
        "findings": findings,
        "input_hashes": {
            "reactome_source_coverage": _sha(BATCH092 / "reactome_source_coverage.json"),
            "reactome_translation_coverage": _sha(BATCH092 / "reactome_translation_coverage.json"),
            "amds_quality_gate": _sha(BATCH092 / "amds_quality_gate.json"),
            "amds_role_identity_receipts": _sha(BATCH092 / "amds_role_identity_receipts.jsonl"),
        },
    }
    OUTPUT.mkdir(parents=True, exist_ok=True)
    target = OUTPUT / "batch093_pre_fix_structured_rpir_and_role_cohort_expected_failure.json"
    target.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    print(EXPECTED)
    print(target)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
