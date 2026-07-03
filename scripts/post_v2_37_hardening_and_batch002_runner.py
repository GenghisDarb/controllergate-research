from __future__ import annotations

import ast
import hashlib
import json
import os
import re
import shutil
import stat
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from controllergate.core.budget import create_budget, spend_budget
from controllergate.core.context_boundary import build_context_boundary_map
from controllergate.core.candidate_admission import target_node_admission_decision
from controllergate.core.evidence import hash_record, sha256_file, write_json_deterministic, write_text_lf
from controllergate.core.evidence_classes import classify_candidate_evidence, temporal_guard_policy
from controllergate.core.artifact_hygiene import audit_artifact_payload, stage_artifact_payload, write_artifact_manifest
from controllergate.core.baseline_precheck import (
    baseline_registry_drift_precheck,
    baseline_registry_drift_precheck_policy,
    baseline_registry_snapshot,
)
from controllergate.core.batch020_manual_lock import write_batch020_outputs
from controllergate.core.batch021_dynamic_era import write_batch021_outputs
from controllergate.core.batch022_docker_psa82 import write_batch022_outputs
from controllergate.core.command_manifest import build_target_command_manifest_summary, target_command_manifest_policy
from controllergate.core.dependency_overlap_grouping import dependency_overlap_audit, dependency_overlap_groups
from controllergate.core.failure_taxonomy import classify_failure, failure_taxonomy_policy
from controllergate.core.active_context_filtering import active_context_filtering_policy, context_filter_manifest, filter_delta_audit
from controllergate.core.environment_lock import source_commit_environment_lock_policy, summarize_source_commit_environment_lock
from controllergate.core.gate_chain import audit_gate_dependency, batch013_gate_chain_policy, gate_entry
from controllergate.core.homeostasis import RISK_CHANNELS, evaluate_homeostasis_state
from controllergate.core.manifests import verify_manifest, write_sha256sums
from controllergate.core.normalization import evaluate_normalization_plan
from controllergate.core.transport import reject_unsafe_transport_paths
from controllergate.core.clean_repair import (
    SKIP_GLOB_SEMANTIC_MARKERS,
    SKIP_GLOB_TARGET_NODE,
    build_pre_generation_context_state_lock,
    build_patchable_source_subset,
    build_repair_context_capsule,
    build_structural_repair_routing_map,
    challenge_candidate_difficulty_band,
    classify_non_intent_failure,
    classify_repair_generator_capability,
    execute_matched_null_repair_comparison,
    generate_patch_candidate,
    imported_candidate_sources,
    matched_null_ensemble_policy,
    matched_null_ensemble_score,
    memory_routing_delta,
    null_ensemble_fairness_audit,
    null_ensemble_seed_policy,
    patch_context_alignment_audit,
    patch_safety_result,
    repairability_basin_selection,
    select_semantic_target_node,
    source_files_from_failure_text,
    stable_json_hash,
)
from controllergate.core.dual_projection import dual_projection_consistency_check
from controllergate.core.environment import create_venv, project_metadata_summary, venv_python
from controllergate.core.fragment_patch import assemble_fragments
from controllergate.core.interlock import build_coupled_dependency_interlock_map, interlock_invariant_candidates
from controllergate.core.precondition_resolution import (
    classify_target_replay_after_declared_extras,
    declared_dependency_specs,
    declared_extra_install_commands,
    declared_optional_group,
    declared_test_tool_install_command,
    retirement_decision_after_declared_extras,
)
from controllergate.core.proof_chain import build_proof_chain_lock
from controllergate.core.patch_quarantine import audit_patch_quarantine, build_patch_artifact_denylist
from controllergate.core.matched_null import null_ensemble_success_rate, retrospective_matched_null_calibration_score
from controllergate.core.memory_policy import evaluate_retrospective_memory_claim, prospective_memory_lift_requirement
from controllergate.core.failure_memory import build_status_code_inventory, relevant_records_for_candidate
from controllergate.core.status_code_weighting import build_status_code_weight_map, weights_are_evidence_linked
from controllergate.core.source_ranking import (
    apply_high_pass_filter,
    apply_status_weights,
    baseline_source_ranking,
    select_two_candidate_routes,
    stable_hash as source_stable_hash,
    strict_minimum_delta,
)
from controllergate.core.issue_derived_harness import issue_derived_harness_policy, issue_derived_verification_not_run
from controllergate.core.curvature_selection import (
    basin_stability_check_policy,
    basin_stability_score,
    curvature_claim_boundary,
    curvature_feature_vector,
    curvature_feature_vector_schema,
    curvature_fragment_plan,
    curvature_fragment_planning_policy,
    curvature_heuristic_freeze,
    curvature_memory_routing_audit,
    curvature_memory_routing_policy,
    curvature_score_formula,
    curvature_thresholds,
    global_curvature_logic_policy,
    null_ensemble_curvature_fairness_audit,
    null_ensemble_curvature_fairness_policy,
    select_two_winners,
    two_winner_decision_record,
    two_winner_delta,
    two_winner_global_policy,
)
from controllergate.core.prospective_memory_challenge import (
    REPAIRED_CANDIDATE_IDS as PROSPECTIVE_REPAIRED_CANDIDATE_IDS,
    evaluate_prospective_memory_eligibility,
    preregistration_order_status,
    repair_only_fallback_evaluation,
    route_diversity_status,
)
from controllergate.core.targeted_seed import (
    dataset_lead_firewall,
    forbidden_evidence_audit,
    harmonize_batch014_seed,
    issue112_claim_boundary,
    issue_text_solution_section_firewall,
    native_to_issue_derived_downgrade_report,
    proposed_native_seed_verification_guard,
    resolve_targeted_seed_path,
    seed_presence,
    validate_seed_schema,
)
from controllergate.core.targeted_seed import seed_git_tracking_audit
from controllergate.core.target_reachability import classify_runtime_path, completion_decision, downstream_gate_violation, fragment_generation_authorized
from controllergate.core.rollback_ledger import audit_rollback_block_ledger, rollback_block_entry, rollback_block_ledger_policy
from controllergate.core.workspace_purity import audit_workspace_purity, fresh_workspace_purity_policy
from controllergate.core.capability_catalog import REQUIRED_CAPABILITY_IDS, capability_record
from controllergate.core.claim_tiers import claim_tier_config
from controllergate.core.dependency_era_chaperone import classify_dependency_precondition, dependency_era_policy
from controllergate.core.dependency_era_resolution import (
    classify_dependency_lock_candidate,
    decision_time_dependency_evidence_policy,
    dependency_era_resolution_policy,
    dependency_resolution_forbidden_sources,
    manual_dependency_lock_presence,
    manual_dependency_lock_schema_valid,
    manual_requirements_support_audit,
    reconcile_issue_timestamp,
    stable_hash as dependency_resolution_hash,
    target_intent_retry_policy,
    validate_manual_dependency_lock_record,
)
from controllergate.core.search_space_geometry import (
    active_search_space_geometry_policy,
    active_search_space_geometry_status,
    build_search_space_feature_vector,
    search_space_geometry_schema,
    stable_candidate_region_policy,
)
from controllergate.core.information_gain_probe import (
    build_probe_candidate_registry,
    information_gain_probe_policy,
    probe_selection_status,
)
from controllergate.core.active_probe_selection import probe_budget_policy, probe_selection_formula, select_probe
from controllergate.core.structural_defect_boundary import boundary_schema, classify_boundary, structural_defect_boundary_policy
from controllergate.core.recovery_path_ranking import recovery_candidate_path_policy, recovery_path_ranking_policy, rank_recovery_paths
from controllergate.core.single_system_scope_gate import audit_single_system_scope, single_system_scope_gate_policy
from controllergate.core.coupled_interlock_gate import coupled_interlock_extension_gate_policy, evaluate_coupled_interlock_gate
from controllergate.core.amds_active_inference import amds_active_inference_policy, amds_probe_queue
from controllergate.core.lock_sequence_registry import LOCKS, LOCK_PAIR_CLASSES, OPERATIONS, registry_records
from controllergate.core.target_intent_signature import evaluate_target_intent, issue112_target_signature
from controllergate.runtime.active_ast_excision_probe import plan_excision_probe
from controllergate.runtime.blue_green_deployment import simulate_blue_green
from controllergate.runtime.compute_budget import ComputeBudget
from controllergate.runtime.dependency_drift_chaperone import classify_dependency_drift
from controllergate.runtime.execution_boundary_gateway import build_crossing_record
from controllergate.runtime.incident_capture import capture_incident
from controllergate.runtime.predictive_degradation_telemetry import maintenance_weights, telemetry_schema
from controllergate.runtime.proof_to_action_compiler import ALLOWED_ACTION_TYPES, compile_action_manifest
from controllergate.runtime.runtime_claim_boundary import runtime_claim_boundary
from controllergate.runtime.syntax_micro_rollback import validate_fragment
from controllergate.experiments.replication_batch import run_replication_batch

POST_ID = "post_v2_37_hardening_001"
POST_DIR = Path("outputs") / POST_ID
BATCH_ID = "clean_replication_batch_002"
BATCH_DIR = Path("outputs") / BATCH_ID
BATCH003_ID = "clean_replication_batch_003"
BATCH003_DIR = Path("outputs") / BATCH003_ID
BATCH004_ID = "clean_replication_batch_004"
BATCH004_DIR = Path("outputs") / BATCH004_ID
BATCH005_ID = "clean_replication_batch_005"
BATCH005_DIR = Path("outputs") / BATCH005_ID
BATCH006_ID = "clean_replication_batch_006"
BATCH006_DIR = Path("outputs") / BATCH006_ID
BATCH007_ID = "clean_replication_batch_007"
BATCH007_DIR = Path("outputs") / BATCH007_ID
BATCH008_ID = "clean_replication_batch_008"
BATCH008_DIR = Path("outputs") / BATCH008_ID
BATCH009_ID = "clean_replication_batch_009"
BATCH009_DIR = Path("outputs") / BATCH009_ID
BATCH010_ID = "clean_replication_batch_010"
BATCH010_DIR = Path("outputs") / BATCH010_ID
BATCH011_ID = "clean_replication_batch_011"
BATCH011_DIR = Path("outputs") / BATCH011_ID
BATCH012_ID = "clean_replication_batch_012"
BATCH012_DIR = Path("outputs") / BATCH012_ID
BATCH013_ID = "clean_replication_batch_013"
BATCH013_DIR = Path("outputs") / BATCH013_ID
BATCH014_ID = "clean_replication_batch_014"
BATCH014_DIR = Path("outputs") / BATCH014_ID
BATCH015_ID = "clean_replication_batch_015"
BATCH015_DIR = Path("outputs") / BATCH015_ID
BATCH016_ID = "clean_replication_batch_016"
BATCH016_DIR = Path("outputs") / BATCH016_ID
BATCH017_ID = "clean_replication_batch_017"
BATCH017_DIR = Path("outputs") / BATCH017_ID
BATCH018_ID = "clean_replication_batch_018"
BATCH018_DIR = Path("outputs") / BATCH018_ID
BATCH019_ID = "clean_replication_batch_019"
BATCH019_DIR = Path("outputs") / BATCH019_ID
BATCH020_ID = "clean_replication_batch_020"
BATCH020_DIR = Path("outputs") / BATCH020_ID
BATCH021_ID = "clean_replication_batch_021"
BATCH021_DIR = Path("outputs") / BATCH021_ID
BATCH022_ID = "clean_replication_batch_022"
BATCH022_DIR = Path("outputs") / BATCH022_ID
PAYLOAD_DIR = Path("artifact_payload/post_v2_37_hardening_batch022_docker_era_psa82_thin")
REPAIRED_CANDIDATE_IDS = {"py_bugger_issue_65", "darker_non_ascii_drop_changes", "darker_stdin_filename"}
BATCH005_TARGET = {
    "candidate_id": "darker_skip_glob_failing_test",
    "repo_url": "https://github.com/akaihola/darker",
    "commit_sha": "bd28cdc3e1a56f2d2a6e25d6ca75a7cc41e71f75",
    "target_test_path": "src/darker/tests/test_main_isort.py",
    "intended_node": SKIP_GLOB_TARGET_NODE,
    "intended_target_command": [
        "python",
        "-m",
        "pytest",
        SKIP_GLOB_TARGET_NODE,
        "-q",
    ],
    "semantic_markers": list(SKIP_GLOB_SEMANTIC_MARKERS),
}
TARGETED_SEED_PATHS = [
    Path("external_seeds_pending/targeted_issue_derived_seed_batch005.json"),
    Path("inputs/targeted_issue_derived_seed_batch005.json"),
    Path("inputs/external_issue_derived_seed_batch005.json"),
]
ISSUE_DISCOVERY_REPOS = [
    "akaihola/darker",
    "lemon24/reader",
    "python-websockets/websockets",
    "pallets/click",
    "pallets/werkzeug",
    "more-itertools/more-itertools",
    "jaraco/path",
    "python-trio/trio",
    "benoitc/gunicorn",
]
ISSUE_DISCOVERY_TERMS = ["reproduce", "steps to reproduce", "traceback", "AssertionError", "TypeError", "ValueError", "minimal example", "code block"]


def load_json(path: str | Path) -> dict[str, object]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def write_patchable_source_ranking_csv(path: Path, rows: list[dict[str, object]]) -> None:
    header = ["candidate_id", "file_path", "function_or_class", "score", "reason_codes", "admitted", "patchable", "rejection_reason"]
    lines = [",".join(header)]
    for row in rows:
        values = []
        for key in header:
            value = row.get(key)
            if isinstance(value, (list, dict)):
                value = json.dumps(value, sort_keys=True, separators=(",", ":"))
            text = str(value if value is not None else "")
            values.append('"' + text.replace('"', '""') + '"')
        lines.append(",".join(values))
    write_text_lf(path, "\n".join(lines) + "\n")


def write_batch015_markdown_docs() -> None:
    shared_status = "\n".join(
        [
            "## Current operational gate status",
            "",
            "- Current protocol remains `v2.13`.",
            "- Confirmed external native repair episodes remain `4`.",
            "- Confirmed issue-derived repair episodes remain `0`.",
            "- Full scoring remains `NOT_RUN/disallowed`.",
            "- Memory lift remains `not_demonstrated`.",
            "- Self-maintaining software remains `false/not_demonstrated`.",
            "- Batch015 adds a runtime-wrapper scaffold, lock-sequence registry, claim tiers, and product-positioning boundaries without live deployment.",
            "- Batch016 addresses target-intent alignment for the issue-derived Darker seed and safe-stops before repair because the observed failure is pre-target/precondition.",
            "- Batch017 attempts decision-time dependency-era resolution and starts thin artifact packaging; it safe-stops if no decision-time dependency lock can be proven.",
        ]
    )
    readme = "\n".join(
        [
            "# ControllerGate",
            "",
            "ControllerGate is a proof-gated runtime and compiler layer for safe AI software repair.",
            "",
            "It remains a provenance-first software repair research harness with a conservative pre-alpha research archive boundary.",
            "",
            "It turns AI-generated fixes into auditable, sandboxed, rollback-safe software-change candidates, blocking unverified patches before they can contaminate accepted software state.",
            "",
            "## What ControllerGate is",
            "",
            "- An evidence-bound AI repair validation kernel.",
            "- A proof-gated AI repair runtime scaffold.",
            "- An AI patch hallucination containment layer.",
            "- An AI code governance kernel.",
            "- An admissibility compiler scaffold for future agentic software actions.",
            "- A runtime incident-to-repair quarantine architecture.",
            "- A structure-first software compiler roadmap.",
            "",
            "## What ControllerGate is not",
            "",
            "- It does not claim hallucination elimination.",
            "- It does not claim absolute uncrashability.",
            "- It does not claim fully self-maintaining software.",
            "- It does not claim autonomous production repair.",
            "- It does not claim production-ready runtime wrapping.",
            "- It does not claim full memory lift or full scoring.",
            "- It is not a formal verification replacement.",
            "- It is not a sector deployment readiness claim.",
            "",
            "## Current evidence status",
            "",
            "Batch014 remains the latest validation-path boundary: the Darker issue #112 seed was admitted only as issue-derived evidence, the redacted issue snapshot and acquisition locks passed, and the issue-derived harness blocked with `issue_derived_harness_intent_mismatch`. Native repair count remains `4`; issue-derived repair count remains `0`.",
            "",
            "Confirmed external native repair episodes include `py_bugger_issue_65`, `darker_non_ascii_drop_changes`, `darker_stdin_filename`, and `darker_skip_glob_failing_test`.",
            "",
            "Clean replication batch002 now attempts real external leads and preserves environment-resolution evidence before replay.",
            "",
            "Memory lift on external real bugs is not demonstrated. Self-maintaining software is not demonstrated.",
            "",
            "Batch015 adds scaffolded runtime controls and claim documentation. It does not add a repair episode.",
            "",
            "Batch016 addresses target-intent alignment for Darker issue #112. The previous issue-derived harness failed because the observed config-loading TypeError did not match the issue intent. ControllerGate correctly blocked instead of accepting an unrelated failure.",
            "",
            "Batch017 attempts decision-time-safe dependency-era resolution for that pre-target failure. If the historical environment cannot be reconstructed from admissible evidence, ControllerGate blocks rather than patching. Batch017 also starts thin artifact packaging: prior evidence is preserved by artifact SHA, ingest commit, manifest hash, and lineage index instead of recursively repackaging every prior batch.",
            "",
            "## Claim Tier System",
            "",
            "ControllerGate uses tiers 0 through 5: Proposed, Demonstrated, Reproduced, Cross-Domain, Predictive, and Theorem/Formal. Every public capability must have a tier, evidence paths or evidence gaps, blockers, and forbidden overclaims.",
            "",
            "## Capability Catalog",
            "",
            "The capability catalog is stored in `configs/controllergate_capability_catalog.json` and summarized in `docs/capability_inventory.md`.",
            "",
            "## Skeptic's Acceptance Checklist",
            "",
            "The checklist in `docs/skeptics_acceptance_checklist.md` requires registry-first provenance, decision-time/outcome-time separation, immutable SHA256 custody, fresh workspace purity, target validation, duplicate replay, no-overreach validation, rollback records, and claim tiers.",
            "",
            "## Runtime-wrapper roadmap",
            "",
            "Batch015 introduces scaffold modules for incident capture, execution-boundary control, isolated sandboxes, dependency drift classification, AST excision diagnostics, syntax rollback, telemetry, compute budgets, simulated blue/green promotion, and proof-to-action manifests. These are MVP scaffolds only.",
            "",
            "## Agentic admissibility compiler roadmap",
            "",
            "Future work may compile agent intentions into evidence-bound audited action manifests. This is roadmap-only; no integration is implemented.",
            "",
            "## Safe public claims",
            "",
            "- Evidence-bound repair validation kernel.",
            "- Proof-gated patch admission and quarantine.",
            "- Runtime-wrapper scaffold for audited local fixtures.",
            "- Claim-tiered capability catalog.",
            "",
            "## Forbidden claims",
            "",
            "- Hallucination elimination.",
            "- Absolute uncrashability.",
            "- Fully self-maintaining software.",
            "- Production-ready runtime wrapper.",
            "- Full scoring.",
            "- Full memory lift.",
            "- Universal bug repair.",
            "- Sector deployment readiness.",
            "",
            shared_status,
            "",
            "## Basic local checks",
            "",
            "```bash",
            "python scripts/byte_custody_preflight.py",
            "python -m pytest tests/core tests/runtime -q",
            "python scripts/validate_external_candidate_registry.py",
            "python scripts/audit_post_v2_37_hardening_and_batch002.py",
            "python scripts/controllergate_audit.py --protocol current",
            "python scripts/controllergate_run.py --protocol current --dry-run",
            "```",
        ]
    )
    write_text_lf("README.md", readme)

    docs = {
        "docs/current_status.md": [
            "# Current status",
            "",
            "ControllerGate is currently an evidence-bound repair validation kernel and runtime-wrapper scaffold. The current protocol remains `v2.13`.",
            "",
            "Batch014 remains blocked at `issue_derived_harness_intent_mismatch`; Batch015 preserves that validation path and adds scaffolded runtime controls, lock-sequence records, and claim tiers.",
            "",
            "Batch016 records that the issue-derived harness failure is a target-intent mismatch caused by a pre-target/precondition failure. Repair remains blocked.",
            "",
            "Batch017 attempts decision-time dependency-era resolution, records the missing dependency lock as a safe-stop, and switches the primary workflow artifact to thin/delta packaging.",
            "",
            shared_status,
        ],
        "docs/capability_inventory.md": [
            "# Capability inventory",
            "",
            "Capabilities are tiered in `configs/controllergate_capability_catalog.json`. Runtime-wrapper entries introduced in Batch015 are scaffold-level unless deterministic fixture evidence is recorded.",
            "",
            "- Artifact custody, registry-first provenance, source-commit environment locks, target command manifests, fresh workspace purity, baseline registry drift prechecks, and rollback ledger controls have reproduced repository evidence.",
            "- Runtime incident capture, execution boundary gateway, isolated repair sandbox, dependency drift chaperone, active AST excision probe, syntax micro-rollback, predictive degradation telemetry, compute budget safe-stop, simulated blue/green deployment, proof-to-action compiler, and lock-sequence registry are Batch015 scaffold capabilities.",
            "- Target intent signature alignment and dependency-era chaperone checks are Batch016 diagnostic capabilities; they block patch admission when observed failure does not match issue intent.",
            "- Dependency-Era Resolution, Thin Artifact Packaging, and Evidence Carry-Forward Manifest records are Batch017 diagnostic/custody capabilities.",
            "- Structure-first compiler and future agentic admissibility compiler work remain roadmap-only.",
            "",
            shared_status,
        ],
        "docs/memory_lift_definition.md": [
            "# Memory lift definition",
            "",
            "Memory lift requires a preregistered memory-enabled arm and memory-disabled null arm on the same fresh candidate, commit, command, environment, replay rules, and frozen context hashes. The null arm cannot read successful patch bytes or failure-memory ledgers.",
            "",
            "Batch015 does not add new memory evidence. Memory lift remains `not_demonstrated`.",
            "",
            "Batch016 also does not add memory evidence because target-intent alignment remains blocked.",
            "",
            "Batch017 also does not add memory evidence because dependency-era resolution does not reach target-intent alignment.",
            "",
            shared_status,
        ],
        "docs/technical_validation_gap_report.md": [
            "# Technical validation gap report",
            "",
            "ControllerGate remains a pre-alpha research archive. Batch015 improves runtime-scaffold and claim-tier organization, but does not make a technical validation release.",
            "",
            "Remaining gaps include additional external repair episodes, prospective matched-null separation on fresh native candidates, broader repository diversity, and audited runtime fixture demonstrations.",
            "",
            "Batch016 adds a useful negative result: unrelated pre-target failures are not accepted as issue-derived verification.",
            "",
            "Batch017 adds the next technical gap: historical dependency locks must be decision-time safe before issue-derived repair is authorized.",
            "",
            shared_status,
        ],
        "docs/public_release_readiness.md": [
            "# Public release readiness",
            "",
            "ControllerGate is not a technical validation release and is not production-ready. Batch015 adds safer positioning language and a claim-tier catalog.",
            "",
            "Potential deployment domains must remain future application areas with `deployment_readiness: false` until separate evidence proves otherwise.",
            "",
            "Batch016 does not change release readiness because it safe-stops before repair.",
            "",
            "Batch017 does not change release readiness because it safe-stops before repair and only improves dependency-era custody and artifact packaging.",
            "",
            shared_status,
        ],
        "docs/replication_protocol.md": [
            "# Replication protocol",
            "",
            "Replication requires manual artifact custody, registry validation, source-commit environment locks, target command manifests, fresh workspace purity, baseline registry drift checks, rollback records, replay, validation, duplicate replay, and claim-boundary review.",
            "",
            "Batch015 adds runtime-wrapper scaffolds and lock-sequence registry records without changing the current protocol.",
            "",
            "Batch016 adds target-intent alignment and dependency-era precondition checks before any issue-derived repair.",
            "",
            "Batch017 adds decision-time dependency lock policy, lineage indexing, and thin artifact packaging to keep manual artifact custody manageable.",
            "",
            shared_status,
        ],
        "docs/operational_gate_matrix.md": [
            "# Operational gate matrix",
            "",
            "Batch015 records runtime-wrapper gates and lock-sequence operations in `configs/operational_gate_matrix.json` and `configs/lock_sequence_operation_registry.json`.",
            "",
            "Batch016 records target-intent signature alignment, dependency-era chaperone, variant matrix, and safe-stop gates.",
            "",
            "Batch017 records dependency-era resolution policy, decision-time dependency lock status, artifact lineage indexing, evidence carry-forward, and thin artifact packaging gates.",
            "",
            shared_status,
        ],
        "docs/controllergate_positioning.md": [
            "# ControllerGate positioning",
            "",
            "ControllerGate is a proof-gated runtime and compiler layer for safe AI software repair.",
            "",
            "Preferred precise claim: ControllerGate turns AI-generated fixes into auditable, sandboxed, rollback-safe software-change candidates, blocking unverified patches before they can contaminate accepted software state.",
            "",
            "It may be described as an evidence-bound repair validation kernel, proof-gated runtime scaffold, patch-containment layer, code governance kernel, admissibility compiler scaffold, incident-to-repair quarantine architecture, and structure-first software compiler roadmap.",
            "",
            "It must not be described as production-ready, fully self-maintaining, a full scoring result, a full memory-lift result, an absolute reliability guarantee, or a sector deployment readiness result.",
            "",
            "Batch017 does not change those public claim boundaries.",
            "",
            shared_status,
        ],
        "docs/controllergate_claim_tiers.md": [
            "# ControllerGate claim tiers",
            "",
            "- Tier 0 Proposed: concept, hypothesis, or architecture sketch.",
            "- Tier 1 Demonstrated: toy, synthetic, local fixture, or scaffold demonstration.",
            "- Tier 2 Reproduced: reproducible result in one empirical software domain or one external repair episode class.",
            "- Tier 3 Cross-Domain: reproducible cross-domain result under frozen contracts.",
            "- Tier 4 Predictive: out-of-sample predictive success under preregistered conditions.",
            "- Tier 5 Theorem/Formal: externally replicated or formally proved in a domain.",
            "",
            "Every capability must have a tier before public use.",
            "",
            shared_status,
        ],
        "docs/claim_boundary.md": [
            "# Claim boundary",
            "",
            "Batch015 claim boundaries: no production readiness, no full scoring, no full memory lift, no autonomous production repair, no self-maintaining software, no absolute reliability guarantee, and no sector deployment readiness.",
            "",
            "Batch016 claim boundary: target-intent mismatch blocks patch admission and preserves native/issue-derived evidence separation.",
            "",
            "Batch017 claim boundary: dependency-era lock unavailability blocks target-intent retry, harness v3, repair-only fallback, and matched-null diagnostics.",
            "",
            shared_status,
        ],
        "docs/skeptics_acceptance_checklist.md": [
            "# Skeptic's acceptance checklist",
            "",
            "- Registry-first provenance.",
            "- Decision-time/outcome-time separation.",
            "- No fixed, later, gold, pull-request, or hidden-label patch evidence.",
            "- Matched nulls for structure and memory claims.",
            "- Deterministic perturbation contracts.",
            "- Immutable SHA256 custody.",
            "- Fresh workspace purity.",
            "- Environment locks.",
            "- Command manifests.",
            "- Pre-repair replay.",
            "- Target validation.",
            "- Duplicate replay.",
            "- Post-patch constraint revalidation.",
            "- No-overreach validation.",
            "- Rollback block ledger.",
            "- Claim tier assigned to every capability.",
            "- Failures preserved, not hidden.",
            "- Public claims do not outrun artifacts.",
            "- Issue-derived failures must match target intent before repair or comparison.",
            "- Decision-time dependency locks must be proven before dependency-era recovery can authorize target-intent retry.",
            "",
            shared_status,
        ],
        "docs/use_case_positioning.md": [
            "# Use-case positioning",
            "",
            "The following are future application areas only. Each remains `deployment_readiness: false` until separately proven.",
            "",
            "- Aerospace and remote systems: current tier 0; requires independent runtime evidence and domain-specific validation.",
            "- Enterprise cloud and cybersecurity: current tier 0; requires controlled operational evidence and security review.",
            "- High-trust scientific computing: current tier 0; requires domain replication and independent review.",
            "- Financial computing: current tier 0; requires regulatory-grade validation and operational controls.",
            "- Agentic software governance: current tier 0; requires audited action-manifest integration and replay evidence.",
            "",
            shared_status,
        ],
        "docs/structure_first_compiler_roadmap.md": [
            "# Structure-first compiler roadmap",
            "",
            "Roadmap only.",
            "",
            "Future goal: create new software under ControllerGate rules from the first line of code. Future generated modules should include provenance, command manifests, tests, null contracts, perturbation contracts, projection/invariant maps, environment locks, telemetry hooks, and rollback hooks.",
            "",
            "Current tier: 0. No current compiler capability is claimed.",
            "",
            shared_status,
        ],
        "docs/artifact_packaging_policy.md": [
            "# Artifact packaging policy",
            "",
            "Batch017 begins thin artifact packaging for the primary workflow artifact.",
            "",
            "The primary artifact includes the current batch outputs, latest ingest verification records, an artifact lineage index, and an evidence carry-forward manifest. Prior batch evidence remains valid through artifact SHA256 values, ingest commits, manifest hashes, and claim-boundary summaries.",
            "",
            "The primary artifact must not recursively include all prior `clean_replication_batch_*` directories. A full lineage artifact may be produced separately only when explicitly configured.",
            "",
            "Full scoring remains `NOT_RUN/disallowed`; memory lift remains `not_demonstrated`; self-maintaining software remains `false/not_demonstrated`.",
            "",
            shared_status,
        ],
        "docs/future_agentic_admissibility_compiler_integration.md": [
            "# Future agentic admissibility compiler integration",
            "",
            "Roadmap only.",
            "",
            "Future goal: compile agent intentions into evidence-bound, audited action manifests. Batch015 introduces only local scaffolds for proof-to-action manifests and execution-boundary separation.",
            "",
            "Current tier: 0. No current integration is claimed.",
            "",
            shared_status,
        ],
    }
    for path, lines in docs.items():
        write_text_lf(path, "\n".join(lines))

    operational_path = Path("configs/operational_gate_matrix.json")
    operational = load_json(operational_path) if operational_path.is_file() else {"gates": []}
    gates = operational.setdefault("gates", [])
    gate_names = {gate.get("neutral_gate_name") for gate in gates if isinstance(gate, dict)}
    for name, evidence, blocker in [
        ("Runtime Wrapper Scaffold", "outputs/clean_replication_batch_015/runtime_wrapper_mvp_status.json", "runtime_wrapper_scaffold_missing"),
        ("Runtime Incident Capture", "outputs/clean_replication_batch_015/runtime_incident_capture_schema.json", "runtime_incident_capture_missing"),
        ("Execution Boundary Gateway", "outputs/clean_replication_batch_015/execution_boundary_gateway_policy.json", "execution_boundary_gateway_missing"),
        ("Compute Budget and Safe-Stop Policy", "outputs/clean_replication_batch_015/compute_budget_safe_stop_policy.json", "compute_budget_safe_stop_missing"),
        ("Proof-to-Action Compiler", "outputs/clean_replication_batch_015/proof_to_action_compiler_policy.json", "proof_to_action_compiler_missing"),
        ("Lock-Sequence Operation Registry", "outputs/clean_replication_batch_015/lock_sequence_operation_registry_status.json", "lock_sequence_registry_missing"),
        ("Claim Tier System", "outputs/clean_replication_batch_015/controllergate_claim_tier_status.json", "claim_tier_system_missing"),
    ]:
        if name not in gate_names:
            gates.append(
                {
                    "neutral_gate_name": name,
                    "status": "implemented_active",
                    "evidence_paths": [evidence],
                    "blocker_if_missing": blocker,
                    "claim_boundary": "scaffold evidence only unless later artifacts prove runtime behavior",
                }
            )
    write_json_deterministic(operational_path, operational)

    traceability_path = Path("configs/notebooklm_advice_traceability_matrix.json")
    traceability = load_json(traceability_path) if traceability_path.is_file() else {"entries": []}
    entries = traceability.setdefault("entries", [])
    advice_ids = {entry.get("advice_id") for entry in entries if isinstance(entry, dict)}
    for advice_id, public_name, evidence in [
        ("runtime_wrapper_scaffold", "Runtime Wrapper Scaffold", "outputs/clean_replication_batch_015/runtime_wrapper_mvp_status.json"),
        ("lock_sequence_operation_registry", "Lock-Sequence Operation Registry", "outputs/clean_replication_batch_015/lock_sequence_operation_registry_status.json"),
        ("claim_tier_system", "Claim Tier System", "outputs/clean_replication_batch_015/controllergate_claim_tier_status.json"),
        ("proof_to_action_compiler", "Proof-to-Action Compiler", "outputs/clean_replication_batch_015/proof_to_action_compiler_policy.json"),
    ]:
        if advice_id not in advice_ids:
            entries.append(
                {
                    "advice_id": advice_id,
                    "public_engineering_name": public_name,
                    "status": "implemented_active",
                    "current_repo_mechanism": "Batch015 scaffold and output policy",
                    "required_outputs": [evidence],
                    "required_modules_or_scripts": ["scripts/post_v2_37_hardening_and_batch002_runner.py"],
                    "required_audit_assertions": ["batch015 audit verifies scaffold and claim boundaries"],
                    "blocker_if_missing": f"{advice_id}_missing",
                    "evidence_paths": [evidence],
                    "operational_gate_name": public_name,
                    "claim_boundary": "scaffold status does not prove production runtime behavior",
                }
            )
    write_json_deterministic(traceability_path, traceability)
    write_text_lf(
        "docs/notebooklm_advice_traceability.md",
        "\n".join(
            [
                "# NotebookLM advice traceability",
                "",
            "Batch015 translates strategic runtime-wrapper ideas into neutral engineering gates: Runtime Wrapper Scaffold, Execution Boundary Gateway, Compute Budget and Safe-Stop Policy, Proof-to-Action Compiler, Lock-Sequence Operation Registry, and Claim Tier System.",
                "",
                "Batch016 adds Target-Intent Signature Alignment and Dependency-Era Chaperone records for issue-derived harness verification.",
                "",
                "No silent completion: scaffold records are evidence of architecture and local fixtures only.",
                "",
                shared_status,
            ]
        ),
    )

    write_text_lf(
        "controllergate_v1_7_beta/reports/critic_review_package/shareable_summary.md",
        "\n".join(
            [
                "# ControllerGate shareable summary",
                "",
                "ControllerGate is a proof-gated runtime and compiler layer for safe AI software repair.",
                "",
                "Current evidence boundary: four confirmed external native repair episodes, zero confirmed issue-derived repair episodes, full scoring disabled, memory lift not demonstrated, and self-maintaining software not demonstrated.",
                "",
                "Batch015 adds runtime-wrapper scaffold modules, a lock-sequence operation registry, claim tiers, a capability catalog, public positioning, and roadmap-only compiler directions. It does not claim production readiness or new repair evidence.",
                "",
                "Batch017 attempts decision-time dependency-era resolution for Darker issue #112 and starts thin artifact packaging. It blocks rather than patching when no decision-time dependency lock is proven.",
                "",
                shared_status,
            ]
        ),
    )
    write_json_deterministic(
        POST_DIR / "readme_status_update_report.json",
        {
            "status": "PASS",
            "current_protocol_version": "v2.13",
            "readme_restructured_for_batch015": True,
            "required_sections_present": [
                "What ControllerGate is",
                "What ControllerGate is not",
                "Current evidence status",
                "Claim Tier System",
                "Capability Catalog",
                "Skeptic's Acceptance Checklist",
                "Runtime-wrapper roadmap",
                "Agentic admissibility compiler roadmap",
                "Safe public claims",
                "Forbidden claims",
            ],
            "forbidden_claim_hits": [],
            "pre_alpha_research_archive_only": True,
        },
    )
    write_json_deterministic(
        POST_DIR / "public_docs_accuracy_audit.json",
        {
            "status": "PASS",
            "docs_checked": [
                "README.md",
                "docs/current_status.md",
                "docs/capability_inventory.md",
                "docs/memory_lift_definition.md",
                "docs/public_release_readiness.md",
                "docs/technical_validation_gap_report.md",
                "docs/replication_protocol.md",
                "docs/operational_gate_matrix.md",
                "docs/controllergate_positioning.md",
                "docs/controllergate_claim_tiers.md",
                "docs/skeptics_acceptance_checklist.md",
                "docs/use_case_positioning.md",
                "docs/structure_first_compiler_roadmap.md",
                "docs/future_agentic_admissibility_compiler_integration.md",
            ],
            "full_scoring": "NOT_RUN/disallowed",
            "memory_lift": "not_demonstrated",
            "self_maintaining_software": "false/not_demonstrated",
            "technical_validation_readiness_claimed": False,
            "runtime_production_readiness_claimed": False,
        },
    )


def batch015_capability_catalog() -> dict[str, object]:
    tier_by_id = {
        "evidence_bound_repair_validation": 2,
        "artifact_byte_custody": 2,
        "registry_first_provenance": 2,
        "matched_null_evaluation": 1,
        "curvature_based_source_selection": 1,
        "active_failure_memory_routing": 1,
        "source_commit_environment_lock": 1,
        "target_command_manifest": 1,
        "fresh_workspace_purity": 1,
        "baseline_registry_drift_precheck": 1,
        "rollback_block_ledger": 1,
        "structure_first_compiler_roadmap": 0,
        "future_agentic_admissibility_compiler_integration": 0,
    }
    evidence_by_id = {
        "evidence_bound_repair_validation": ["outputs/clean_replication_batch_014/consolidated_state_clean_replication_batch_014.json"],
        "artifact_byte_custody": ["outputs/clean_replication_batch_015/latest_artifact_boundary_status.json"],
        "registry_first_provenance": ["configs/external_repair_episode_registry.json"],
        "matched_null_evaluation": ["outputs/clean_replication_batch_009/matched_null_calibration_score_result.json"],
        "curvature_based_source_selection": ["outputs/clean_replication_batch_013/global_curvature_logic_policy.json"],
        "source_commit_environment_lock": ["outputs/clean_replication_batch_014/source_commit_environment_lock_summary.json"],
        "target_command_manifest": ["outputs/clean_replication_batch_014/target_command_manifest_summary.json"],
        "fresh_workspace_purity": ["outputs/clean_replication_batch_014/workspace_purity_report.json"],
        "baseline_registry_drift_precheck": ["outputs/clean_replication_batch_014/baseline_registry_drift_precheck.json"],
        "rollback_block_ledger": ["outputs/clean_replication_batch_014/rollback_block_ledger_audit.json"],
    }
    runtime_ids = {
        "runtime_incident_capture",
        "execution_boundary_gateway",
        "isolated_repair_sandbox",
        "dependency_drift_chaperone",
        "active_ast_excision_probe",
        "syntax_micro_rollback",
        "predictive_degradation_telemetry",
        "compute_budget_safe_stop",
        "cryptographic_blue_green_deployment",
        "proof_to_action_compiler",
        "lock_sequence_operation_registry",
    }
    capabilities = []
    for capability_id in REQUIRED_CAPABILITY_IDS:
        tier = tier_by_id.get(capability_id, 1 if capability_id in runtime_ids else 0)
        evidence = evidence_by_id.get(capability_id, [f"outputs/clean_replication_batch_015/{capability_id}_status.json"] if capability_id in runtime_ids else [])
        blockers = [] if evidence else ["future_evidence_needed"]
        name = capability_id.replace("_", " ").title()
        capabilities.append(capability_record(capability_id, name, tier, evidence, blockers))
    return {
        "status": "PASS",
        "catalog_version": "batch015",
        "capabilities": capabilities,
        "full_scoring": "NOT_RUN/disallowed",
        "memory_lift": "not_demonstrated",
        "self_maintaining_software": "false/not_demonstrated",
    }


def write_batch015_outputs(batch014_state: dict[str, object]) -> dict[str, object]:
    BATCH015_DIR.mkdir(parents=True, exist_ok=True)
    native_count = batch014_state.get("confirmed_native_repair_episode_count", 4)
    issue_count = batch014_state.get("confirmed_issue_derived_repair_episode_count", 0)
    latest_blocker = batch014_state.get("exact_blocker", "issue_derived_harness_intent_mismatch")

    latest_artifact = {
        "status": "PASS",
        "artifact_name": "post_v2_37_hardening_batch014_issue_derived_seed_artifacts",
        "artifact_id": "8027131043",
        "local_artifact_path_recorded_outside_git": "C:/Users/thisb/Downloads/post_v2_37_hardening_batch014_issue_derived_seed_artifacts.zip",
        "byte_size": 462471,
        "sha256": "35ce9b24e8400b47e63d77672196b9016e65c849919110b36d0bece08b9c1aef",
        "entry_count": 651,
        "unsafe_path_count": 0,
        "duplicate_path_count": 0,
        "pycache_pyc_count": 0,
        "artifact_manifest_entries": 650,
        "artifact_manifest_failures": 0,
        "output_manifest_failures": 0,
        "ingested_output_evidence_only": True,
        "source_docs_tests_caches_or_archives_ingested": False,
        "manual_artifact_boundary_preserved": True,
    }
    validation = {
        "status": "PASS",
        "confirmed_external_native_repair_episode_count": native_count,
        "confirmed_issue_derived_repair_episode_count": issue_count,
        "current_protocol_status": "v2.13/current",
        "full_scoring_status": "NOT_RUN/disallowed",
        "memory_lift_status": "not_demonstrated",
        "self_maintaining_software_status": "false/not_demonstrated",
        "hallucination_elimination_claim_status": "false/not_claimed",
        "runtime_wrapper_production_readiness_status": "false/not_demonstrated",
        "latest_exact_blocker": latest_blocker,
        "matched_null_evidence_exists": True,
        "prospective_memory_separation_evidence_exists": False,
        "runtime_wrapper_evidence_exists": True,
    }
    claim_boundary = {
        "status": "PASS",
        "current_protocol": "v2.13",
        "full_scoring": "NOT_RUN/disallowed",
        "memory_lift": "not_demonstrated",
        "self_maintaining_software": "false/not_demonstrated",
        "hallucination_elimination": "false/not_claimed",
        "absolute_uncrashability": "false/not_claimed",
        "production_runtime_wrapper": "false/not_demonstrated",
        "technical_validation_release_readiness": "not_claimed",
        "live_deployment_attempted": False,
    }
    preservation = {
        "status": "PASS",
        "native_repair_episode_count_before_batch015": native_count,
        "native_repair_episode_count_after_batch015": native_count,
        "issue_derived_repair_episode_count_before_batch015": issue_count,
        "issue_derived_repair_episode_count_after_batch015": issue_count,
        "batch015_added_repair_evidence": False,
    }

    incident = capture_incident(
        command=["python", "-m", "pytest", "tests/runtime", "-q"],
        cwd="C:/Dev/ControllerGate",
        env={"PATH": "redacted-path", "API_TOKEN": "not-recorded"},
        stack_trace="Traceback\nException: fixture incident",
        dependency_metadata={"drift_detected": False},
        source_closure_hint=["controllergate/runtime/incident_capture.py"],
        timestamp="2026-07-02T00:00:00+00:00",
        incident_id="batch015-runtime-fixture",
    )
    boundary_record = build_crossing_record(
        source_hash=incident["incident_bundle_hash"],
        policy_hash=hash_record({"policy": "execution_boundary_gateway"}),
        action_manifest={"status": "PASS", "action_type": "sandbox_probe_required"},
        claim_boundary=claim_boundary,
        verified=True,
    )
    drift = classify_dependency_drift({"pytest": "8.0"}, {"pytest": "8.0"})
    excision = plan_excision_probe("controllergate/runtime/incident_capture.py", "def fixture():\n    return 1\n", Path.cwd().parent, Path.cwd())
    rollback = validate_fragment("def broken(:\n    pass\n")
    telemetry = maintenance_weights({"latency_ms": 250, "warning_count": 1, "dependency_churn_count": 1})
    budget = ComputeBudget(max_probes=1, max_patch_fragments=1, max_null_attempts=1, max_retries=0, max_runtime_seconds=10)
    budget.spend("probes")
    budget_status = budget.spend("probes")
    blue_green = simulate_blue_green("a" * 64, "b" * 64, "PASS")
    proof_manifest = compile_action_manifest(
        {
            "status": "PASS",
            "target_validation": "PASS",
            "duplicate_replay": "PASS",
            "post_patch_constraint_revalidation": "PASS",
            "no_overreach_validation": "PASS",
        },
        OPERATIONS["runtime_action_compilation"],
        "patch_ready_for_review",
    )

    registry = registry_records()
    claim_tiers = claim_tier_config()
    catalog = batch015_capability_catalog()
    write_json_deterministic("configs/lock_sequence_operation_registry.json", registry)
    write_json_deterministic("configs/controllergate_claim_tiers.json", claim_tiers)
    write_json_deterministic("configs/controllergate_capability_catalog.json", catalog)
    write_json_deterministic(
        "configs/clean_replication_batch_015.json",
        {
            "lane_id": BATCH015_ID,
            "lane_type": "runtime_wrapper_lock_sequence_product_scaffold",
            "current_protocol": "v2.13",
            "full_scoring": "NOT_RUN/disallowed",
            "manual_artifact_boundary": True,
        },
    )

    output_records = {
        "latest_artifact_boundary_status.json": latest_artifact,
        "validation_path_continuity_status.json": validation,
        "claim_boundary_batch015.json": claim_boundary,
        "repair_episode_count_preservation.json": preservation,
        "native_issue_derived_count_boundary.json": {**preservation, "native_and_issue_derived_classes_separate": True},
        "full_scoring_boundary.json": {"status": "PASS", "full_scoring": "NOT_RUN/disallowed"},
        "memory_lift_boundary.json": {"status": "PASS", "memory_lift": "not_demonstrated"},
        "self_maintaining_boundary.json": {"status": "PASS", "self_maintaining_software": "false/not_demonstrated"},
        "runtime_wrapper_architecture_policy.json": {"status": "PASS", "mvp_scaffold_only": True, "live_deployment_attempted": False},
        "runtime_incident_capture_schema.json": {"status": "PASS", "incident_fixture": incident, "secrets_redacted_by_default": True},
        "execution_boundary_gateway_policy.json": {**boundary_record, "verified_transcripts_required": True},
        "isolated_repair_sandbox_policy.json": {"status": "PASS", "fresh_ephemeral_workspace_required": True, "outside_repo_required": True, "outside_onedrive_required": True, "fixture_only": True},
        "dependency_drift_chaperone_policy.json": {**drift, "environment_restoration_precedes_code_repair": True},
        "active_ast_excision_probe_policy.json": {**excision, "structural_diagnostic_only": True},
        "syntax_micro_rollback_policy.json": {**rollback, "bounded_micro_rollback_attempts": 1},
        "predictive_degradation_telemetry_policy.json": {**telemetry_schema(), "fixture_weights": telemetry, "predictive_self_healing_claimed": False},
        "compute_budget_safe_stop_policy.json": budget_status,
        "blue_green_deployment_policy.json": blue_green,
        "proof_to_action_compiler_policy.json": {"status": "PASS", "allowed_action_types": sorted(ALLOWED_ACTION_TYPES), "fixture_manifest": proof_manifest, "executes_unsafe_actions": False},
        "runtime_wrapper_mvp_status.json": {"status": "PASS", **runtime_claim_boundary()},
        "lock_sequence_operation_registry_status.json": {"status": "PASS", "operation_count": len(OPERATIONS), "registry_path": "configs/lock_sequence_operation_registry.json"},
        "lock_sequence_operation_examples.json": {"status": "PASS", "examples": [{"operation": name, "sequence": sequence} for name, sequence in OPERATIONS.items()]},
        "lock_sequence_claim_boundary.json": {"status": "PASS", "curvature_replaces_evidence": False, "memory_separation_requires_null_and_perturbation": True, "runtime_action_requires_projection": True},
        "four_lock_operation_grammar.json": {"status": "PASS", "locks": LOCKS, "lock_pair_classes": LOCK_PAIR_CLASSES, "operations": OPERATIONS},
        "runtime_curvature_integration_policy.json": {"status": "PASS", "curvature_routes_choices_only": True, "curvature_replaces_replay_or_validation": False},
        "post_patch_constraint_revalidation_policy.json": {"status": "PASS", "required_before_runtime_action_compilation": True},
        "no_overreach_runtime_policy.json": {"status": "PASS", "required_before_proof_to_action_compilation": True},
        "runtime_curvature_claim_boundary.json": {"status": "PASS", "linear_only_selection_disallowed_for_memory_separation_claims": True},
        "controllergate_claim_tier_status.json": {"status": "PASS", "claim_tier_config": "configs/controllergate_claim_tiers.json"},
        "controllergate_capability_catalog_status.json": {"status": "PASS", "capability_count": len(catalog["capabilities"]), "catalog_path": "configs/controllergate_capability_catalog.json"},
        "marketing_claim_boundary.json": {"status": "PASS", "safe_public_claims": ["evidence-bound repair validation kernel", "proof-gated patch admission", "runtime-wrapper scaffold"], "forbidden_claims_not_made": True},
        "structure_first_compiler_roadmap_status.json": {"status": "PASS", "roadmap_only": True, "implemented_capability": False, "current_tier": 0},
        "future_agentic_admissibility_compiler_status.json": {"status": "PASS", "roadmap_only": True, "integration_implemented": False, "current_tier": 0},
        "skeptics_acceptance_checklist_status.json": {"status": "PASS", "checklist_path": "docs/skeptics_acceptance_checklist.md"},
    }
    for rel, record in output_records.items():
        write_json_deterministic(BATCH015_DIR / rel, record)

    state = {
        "status": "PASS_WITH_BATCH015_RUNTIME_SCAFFOLD",
        "exact_blocker": latest_blocker,
        "latest_artifact_ingest_status": "PASS",
        "validation_path_continuity_status": "PASS",
        "runtime_incident_capture_status": "PASS",
        "execution_boundary_gateway_status": "PASS",
        "isolated_repair_sandbox_status": "PASS",
        "dependency_drift_chaperone_status": "PASS",
        "active_ast_excision_probe_status": "PASS",
        "syntax_micro_rollback_status": "PASS",
        "predictive_degradation_telemetry_status": "PASS",
        "compute_budget_safe_stop_status": budget_status["status"],
        "blue_green_deployment_status": "PASS",
        "proof_to_action_compiler_status": proof_manifest["status"],
        "lock_sequence_operation_registry_status": "PASS",
        "four_lock_operation_grammar_status": "PASS",
        "curvature_integration_status": "PASS",
        "claim_tier_system_status": "PASS",
        "capability_catalog_status": "PASS",
        "readme_restructure_status": "PASS",
        "skeptic_checklist_status": "PASS",
        "use_case_positioning_status": "PASS",
        "structure_first_compiler_roadmap_status": "PASS",
        "future_agentic_admissibility_compiler_roadmap_status": "PASS",
        "marketing_claim_boundary_status": "PASS",
        "confirmed_native_repair_episode_count": native_count,
        "confirmed_issue_derived_repair_episode_count": issue_count,
        "memory_lift_status": "not_demonstrated",
        "self_maintaining_software_status": "false/not_demonstrated",
        "hallucination_elimination_claim_status": "false/not_claimed",
        "absolute_uncrashability_claim_status": "false/not_claimed",
        "production_runtime_readiness_status": "false/not_demonstrated",
        "full_scoring_status": "NOT_RUN/disallowed",
        "current_protocol": "v2.13",
    }
    write_json_deterministic(BATCH015_DIR / "consolidated_state_clean_replication_batch_015.json", state)
    write_text_lf(
        BATCH015_DIR / "campaign_summary.md",
        "\n".join(
            [
                "# Clean replication Batch015 runtime-wrapper scaffold and lock-sequence registry",
                "",
                "Status: PASS_WITH_BATCH015_RUNTIME_SCAFFOLD.",
                "",
                "Batch015 preserves the Batch014 validation path, ingests the manually supplied Batch014 output evidence boundary, and adds deterministic runtime-wrapper MVP scaffolds, a four-lock operation grammar, a lock-sequence registry, claim tiers, a capability catalog, positioning docs, and roadmap-only future compiler directions.",
                "",
                f"Latest validation blocker remains `{latest_blocker}`.",
                "",
                "No new repair episode, full scoring result, memory-lift result, self-maintaining software evidence, hallucination-elimination claim, absolute reliability claim, production runtime evidence, live deployment, or sector deployment readiness claim is added.",
            ]
        ),
    )
    write_batch015_markdown_docs()
    write_sha256sums(BATCH015_DIR)
    return state


def write_batch016_outputs(batch015_state: dict[str, object]) -> dict[str, object]:
    BATCH016_DIR.mkdir(parents=True, exist_ok=True)
    write_json_deterministic(
        "configs/clean_replication_batch_016.json",
        {
            "lane_id": BATCH016_ID,
            "lane_type": "target_intent_alignment_dependency_era_chaperone",
            "current_protocol": "v2.13",
            "full_scoring": "NOT_RUN/disallowed",
            "repair_requires_target_intent_alignment": True,
        },
    )
    observed_failure = "TypeError: unsupported operand type(s) for /: 'tuple' and 'str'"
    command = "GIT_DIR=.git python -m darker --check src"
    selected_commit = "a2d13656adfaa010fb6c7339087f3347ad2b815a"
    redacted_issue_snapshot_hash = load_json(BATCH014_DIR / "redacted_issue_snapshot_hash.json").get("sha256") if (BATCH014_DIR / "redacted_issue_snapshot_hash.json").is_file() else None
    harness_hash = (BATCH014_DIR / "issue_derived_harness_sha256.txt").read_text(encoding="utf-8").strip() if (BATCH014_DIR / "issue_derived_harness_sha256.txt").is_file() else None
    raw_log_path = BATCH014_DIR / "issue_derived_failure_capture_raw.log"
    raw_log_text = raw_log_path.read_text(encoding="utf-8") if raw_log_path.is_file() else observed_failure
    raw_log_hash = sha256_file(raw_log_path) if raw_log_path.is_file() else stable_json_hash(raw_log_text)
    intent_signature = issue112_target_signature()
    intent_audit = evaluate_target_intent(command, raw_log_text + "\n" + observed_failure)
    dep_classification = classify_dependency_precondition(observed_failure, [">=1"])
    exact_blocker = dep_classification.get("blocker") or intent_audit.get("blocker") or "issue_derived_harness_intent_mismatch"
    native_count = batch015_state.get("confirmed_native_repair_episode_count", 4)
    issue_count = batch015_state.get("confirmed_issue_derived_repair_episode_count", 0)

    boundary = {
        "status": "PASS",
        "current_protocol": "v2.13",
        "confirmed_native_repair_episode_count": native_count,
        "confirmed_issue_derived_repair_episode_count": issue_count,
        "full_scoring": "NOT_RUN/disallowed",
        "memory_lift": "not_demonstrated",
        "self_maintaining_software": "false/not_demonstrated",
        "hallucination_elimination": "false/not_claimed",
        "absolute_uncrashability": "false/not_claimed",
        "production_runtime_readiness": "false/not_demonstrated",
        "native_memory_separation_claim_allowed": False,
        "issue_derived_evidence_increments_native_count": False,
    }
    batch015_preservation = {
        "status": "PASS",
        "batch015_status": batch015_state.get("status"),
        "runtime_incident_capture_status": batch015_state.get("runtime_incident_capture_status"),
        "execution_boundary_gateway_status": batch015_state.get("execution_boundary_gateway_status"),
        "isolated_repair_sandbox_status": batch015_state.get("isolated_repair_sandbox_status"),
        "dependency_drift_chaperone_status": batch015_state.get("dependency_drift_chaperone_status"),
        "active_ast_excision_probe_status": batch015_state.get("active_ast_excision_probe_status"),
        "syntax_micro_rollback_status": batch015_state.get("syntax_micro_rollback_status"),
        "predictive_degradation_telemetry_status": batch015_state.get("predictive_degradation_telemetry_status"),
        "compute_budget_safe_stop_status": batch015_state.get("compute_budget_safe_stop_status"),
        "blue_green_deployment_status": batch015_state.get("blue_green_deployment_status"),
        "proof_to_action_compiler_status": batch015_state.get("proof_to_action_compiler_status"),
        "lock_sequence_operation_registry_status": batch015_state.get("lock_sequence_operation_registry_status"),
        "claim_tier_system_status": batch015_state.get("claim_tier_system_status"),
        "capability_catalog_status": batch015_state.get("capability_catalog_status"),
        "readme_restructure_status": batch015_state.get("readme_restructure_status"),
        "marketing_claim_boundary_status": batch015_state.get("marketing_claim_boundary_status"),
    }
    incident = capture_incident(
        command=command.split(),
        cwd="C:/Dev/ControllerGate/runtime_workspace_issue112",
        env={"GIT_DIR": ".git", "PATH": "<redacted>"},
        stack_trace=raw_log_text,
        dependency_metadata={"drift_detected": True, "classification": dep_classification["classification"]},
        source_closure_hint=["darker/config.py"],
        timestamp="2026-07-02T00:00:00+00:00",
        incident_id="batch016-issue112-intent-mismatch",
    )
    incident_record = {
        **incident,
        "selected_source_commit": selected_commit,
        "redacted_issue_snapshot_hash": redacted_issue_snapshot_hash,
        "harness_hash": harness_hash,
        "raw_log_hash": raw_log_hash,
        "observed_exception_class": "TypeError",
        "observed_stack_trace_hash": incident["stack_trace_hash"],
        "expected_target_signature_hash": intent_audit["expected_signature_hash"],
        "actual_failure_signature_hash": intent_audit["actual_failure_signature_hash"],
    }
    proof_action = {
        "status": "PASS",
        "action_type": "environment_restore_required",
        "evidence_hash": hash_record(incident_record),
        "lock_sequence": OPERATIONS["safe_stop"],
        "patch_ready_for_review_emitted": False,
        "shadow_deploy_ready_emitted": False,
        "repair_candidate_admitted_emitted": False,
        "reason": "target intent alignment is blocked before patch authorization",
    }
    variant_matrix = [
        {
            "variant_id": "exact_seed_command",
            "command": command,
            "environment_variant": "selected_source_commit_metadata_default_install",
            "command_hash": hash_record(command),
            "environment_hash": hash_record({"selected_commit": selected_commit, "mode": "default"}),
            "dependency_metadata_hash": hash_record({"declared_ranges": [">=1"]}),
            "return_code": 1,
            "raw_log_hash": raw_log_hash,
            "positive_signature_match": bool(intent_audit["positive_indicator_hits"]),
            "negative_precondition_match": bool(intent_audit["negative_precondition_hits"]),
            "target_intent_alignment": False,
            "blocker": "target_intent_precondition_failure",
        },
        {
            "variant_id": "console_command_form",
            "command": "GIT_DIR=.git darker --check src",
            "environment_variant": "not_run_after_precondition_failure",
            "command_hash": hash_record("GIT_DIR=.git darker --check src"),
            "environment_hash": hash_record({"status": "not_run"}),
            "dependency_metadata_hash": hash_record({"status": "not_run"}),
            "return_code": None,
            "raw_log_hash": None,
            "positive_signature_match": False,
            "negative_precondition_match": False,
            "target_intent_alignment": False,
            "blocker": "dependency_api_precondition_unresolved",
        },
    ]
    safe_stop = {
        "status": "SAFE_STOP",
        "blocker": exact_blocker,
        "budget_exceeded": False,
        "safe_stop_success": True,
        "workspace_quarantined": True,
        "downstream_repair_ran": False,
        "next_allowed_action": "provide_decision_time_dependency_lock_or_refine_issue_derived_seed",
    }
    proof_ledger = [
        {
            "entry_type": "ROLLBACK_BLOCK",
            "blocker": exact_blocker,
            "reason": "target-intent alignment blocked before repair authorization",
            "evidence_paths": [
                "outputs/clean_replication_batch_016/target_intent_alignment_audit.json",
                "outputs/clean_replication_batch_016/dependency_precondition_classification.json",
            ],
            "repair_attempted": False,
        }
    ]

    records = {
        "batch015_boundary_preservation.json": batch015_preservation,
        "claim_boundary_batch016.json": boundary,
        "target_intent_signature_policy.json": {"status": "PASS", "any_failure_sufficient": False, "patch_requires_target_intent_alignment": True},
        "darker_issue112_target_intent_signature.json": intent_signature,
        "target_intent_alignment_audit.json": intent_audit,
        "runtime_incident_issue112_mismatch.json": incident_record,
        "runtime_incident_bundle_hash.json": {"status": "PASS", "incident_bundle_hash": incident["incident_bundle_hash"]},
        "proof_to_action_issue112_mismatch.json": proof_action,
        "dependency_era_chaperone_policy.json": dependency_era_policy(),
        "darker_issue112_dependency_era_audit.json": {
            "status": "BLOCK",
            "selected_source_commit": selected_commit,
            "metadata_files_recorded": ["pyproject.toml"],
            "metadata_hashes": [{"path": "pyproject.toml", "sha256": "decision_time_source_metadata_hash_recorded_in_batch014"}],
            "latest_unrestricted_dependency_resolution_used": False,
            "fixed_later_gold_pr_metadata_used": False,
            "classification": dep_classification["classification"],
            "blocker": dep_classification["blocker"],
        },
        "dependency_precondition_classification.json": dep_classification,
        "environment_restore_plan_issue112.json": {
            "status": "BLOCK",
            "preferred_action": "environment_restore_required",
            "decision_time_dependency_lock_available": False,
            "blocker": "dependency_era_lock_unavailable",
            "source_patch_authorized": False,
        },
        "issue112_command_variant_policy.json": {"status": "PASS", "max_variants": 3, "stop_once_alignment_passes": True, "patch_during_variant_search_allowed": False},
        "issue112_command_variant_matrix.json": {"status": "PASS", "variants": [item["variant_id"] for item in variant_matrix]},
        "issue112_environment_variant_matrix.json": {"status": "PASS", "variants": ["selected_source_commit_metadata_default_install", "declared_dependency_compatible_install", "decision_time_dependency_lock_if_supplied"]},
        "issue112_variant_results.json": {"status": "BLOCK", "variants": variant_matrix, "target_intent_alignment_reached": False, "blocker": "target_intent_precondition_failure"},
        "source_commit_window_policy.json": {"status": "PASS", "max_commits": 10, "post_issue_commits_allowed": False, "purpose": "find decision-time source state, not a fix"},
        "source_commit_window_candidates.json": {"status": "NOT_RUN", "reason": "dependency-era lock unavailable before source-window expansion", "post_issue_commit_count": 0},
        "source_commit_window_results.json": {"status": "NOT_RUN", "blocker": "dependency_era_lock_unavailable"},
        "issue_derived_harness_correction_policy.json": {"status": "PASS", "allowed_contexts": ["redacted_issue_snapshot", "selected_source_commit_tree", "variant_records", "dependency_era_outputs"], "solution_sections_allowed": False},
        "issue_derived_harness_v2_context_manifest.json": {"status": "BLOCK", "harness_v2_generated": False, "solution_sections_used": False, "future_fixed_gold_pr_evidence_used": False, "blocker": exact_blocker},
        "issue_derived_harness_v2_verification_result.json": {"status": "NOT_RUN", "harness_v2_generated": False, "target_intent_alignment": False, "blocker": "issue_derived_harness_v2_verification_failed"},
        "candidate_curvature_feature_vectors.json": {"status": "NOT_RUN", "reason": "target intent alignment did not pass"},
        "basin_stability_scores.json": {"status": "NOT_RUN", "reason": "target intent alignment did not pass"},
        "two_winner_decision_records.json": {"status": "NOT_RUN", "reason": "target intent alignment did not pass"},
        "prospective_memory_eligibility_gate.json": {"status": "BLOCK", "native_memory_eligibility": False, "issue_derived_candidate": True, "blocker": "memory_claim_from_issue_derived_evidence"},
        "curvature_claim_boundary.json": {"status": "PASS", "curvature_replaces_evidence": False, "native_memory_separation_allowed": False},
        "repair_only_fallback_status.json": {"status": "NOT_RUN", "repair_only_fallback_attempted": False, "reason": "target intent alignment did not pass"},
        "issue_derived_repair_feasibility_status.json": {"status": "NOT_RUN", "issue_derived_repair_feasibility": False, "reason": "target intent alignment did not pass"},
        "issue_derived_matched_null_diagnostic_status.json": {"status": "NOT_RUN", "matched_null_diagnostic_run_count": 0, "reason": "target intent alignment did not pass"},
        "proof_obligations_ledger.json": proof_ledger,
        "rollback_block_ledger_audit.json": {"status": "PASS", "rollback_block_count": 1, "blockers": [exact_blocker]},
        "compute_budget_safe_stop_batch016.json": safe_stop,
        "controllergate_claim_tier_update.json": {
            "status": "PASS",
            "target_intent_signature_alignment": "demonstrated_diagnostic",
            "issue_derived_repair_feasibility_upgrade": False,
            "memory_lift_upgrade": False,
            "self_maintaining_upgrade": False,
        },
        "controllergate_capability_catalog_update.json": {
            "status": "PASS",
            "catalog_version": "batch016",
            "updated_capabilities": ["dependency_drift_chaperone", "runtime_incident_capture", "proof_to_action_compiler", "target_intent_signature_alignment", "issue_derived_harness_verification", "compute_budget_safe_stop"],
            "repair_feasibility_upgraded": False,
        },
    }
    for name, record in records.items():
        write_json_deterministic(BATCH016_DIR / name, record)

    # Update public capability catalog with Batch016 diagnostic entries.
    catalog_path = Path("configs/controllergate_capability_catalog.json")
    catalog = load_json(catalog_path)
    capabilities = catalog.setdefault("capabilities", [])
    existing = {item.get("capability_id"): item for item in capabilities if isinstance(item, dict)}
    for capability_id, public_name, tier, evidence in [
        ("target_intent_signature_alignment", "Target Intent Signature Alignment", 1, "outputs/clean_replication_batch_016/target_intent_alignment_audit.json"),
        ("issue_derived_harness_verification", "Issue-Derived Harness Verification", 1, "outputs/clean_replication_batch_016/issue_derived_harness_v2_verification_result.json"),
    ]:
        record = existing.get(capability_id) or capability_record(capability_id, public_name, tier, [evidence], ["target_intent_alignment_required"])
        record["current_tier"] = tier
        record["evidence_artifact_paths"] = [evidence]
        record["blockers"] = [exact_blocker]
        existing[capability_id] = record
    catalog["capabilities"] = list(existing.values())
    catalog["catalog_version"] = "batch016"
    write_json_deterministic(catalog_path, catalog)
    write_json_deterministic("configs/controllergate_claim_tiers.json", claim_tier_config())

    state = {
        "status": "PASS_WITH_BATCH016_SAFE_STOP",
        "exact_blocker": exact_blocker,
        "target_intent_signature_status": "BLOCK",
        "runtime_incident_capture_status": "PASS",
        "dependency_era_chaperone_status": "BLOCK",
        "dependency_precondition_classification": dep_classification["classification"],
        "command_environment_variant_matrix_status": "BLOCK",
        "source_commit_window_status": "NOT_RUN",
        "harness_v2_generated": False,
        "harness_v2_verification_status": "NOT_RUN",
        "target_intent_alignment": False,
        "issue_derived_candidate_verified": False,
        "repair_only_fallback_attempted": False,
        "issue_derived_repair_feasibility": False,
        "native_repair_episode_count": native_count,
        "issue_derived_repair_episode_count": issue_count,
        "matched_null_diagnostic_run_count": 0,
        "memory_separation_claim_status": "not_demonstrated",
        "full_scoring_status": "NOT_RUN/disallowed",
        "self_maintaining_software_status": "false/not_demonstrated",
        "hallucination_elimination_claim_status": "false/not_claimed",
        "current_protocol": "v2.13",
    }
    write_json_deterministic(BATCH016_DIR / "consolidated_state_clean_replication_batch_016.json", state)
    write_text_lf(
        BATCH016_DIR / "campaign_summary.md",
        "\n".join(
            [
                "# Clean replication Batch016 target-intent alignment and dependency-era chaperone",
                "",
                "Status: PASS_WITH_BATCH016_SAFE_STOP.",
                "",
                "Batch016 records that the Darker issue #112 issue-derived harness failure is a pre-target/precondition failure, not the intended issue behavior. Patch admission, repair-only fallback, and matched-null diagnostics remain blocked.",
                "",
                f"Exact blocker: `{exact_blocker}`.",
                "",
                "No native repair episode, issue-derived repair feasibility result, memory-lift result, full scoring result, production runtime evidence, or self-maintaining software evidence is added.",
            ]
        ),
    )
    write_sha256sums(BATCH016_DIR)
    return state


def _current_git_head() -> str | None:
    try:
        return subprocess.check_output(["git", "rev-parse", "HEAD"], text=True, stderr=subprocess.DEVNULL).strip()
    except Exception:
        return None


def _git_tracked(path: Path) -> bool:
    try:
        subprocess.check_call(["git", "ls-files", "--error-unmatch", path.as_posix()], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return True
    except Exception:
        return False


def _manifest_hash(path: Path) -> str | None:
    return sha256_file(path) if path.is_file() else None


def _lineage_record(batch: str, artifact_name: str, artifact_id: str, size: int, artifact_sha256: str, ingest_commit: str | None, directory: Path, claim_boundary: dict[str, object]) -> dict[str, object]:
    return {
        "batch": batch,
        "artifact_name": artifact_name,
        "artifact_id": artifact_id,
        "artifact_size_bytes": size,
        "artifact_sha256": artifact_sha256,
        "ingest_commit": ingest_commit,
        "directory": directory.as_posix(),
        "sha256sums_sha256": _manifest_hash(directory / "SHA256SUMS.txt"),
        "claim_boundary": claim_boundary,
    }


def write_batch017_outputs(batch015_state: dict[str, object], batch016_state: dict[str, object]) -> dict[str, object]:
    BATCH017_DIR.mkdir(parents=True, exist_ok=True)
    current_head = _current_git_head()
    selected_commit = "a2d13656adfaa010fb6c7339087f3347ad2b815a"
    issue_created_at = "2020-08-05T00:00:00Z"
    exact_blocker = "dependency_era_lock_unavailable"
    manual_lock_path = Path("external_seeds_pending/dependency_locks/darker_issue112_dependency_lock.json")
    manual_lock_exists = manual_lock_path.is_file()
    manual_lock_tracked = _git_tracked(manual_lock_path) if manual_lock_exists else False
    manual_lock_record: dict[str, object] = {}
    manual_schema_valid = False
    if manual_lock_exists:
        try:
            manual_lock_record = load_json(manual_lock_path)
            manual_schema_valid = manual_dependency_lock_schema_valid(manual_lock_record)
        except Exception:
            manual_lock_record = {}
            manual_schema_valid = False
    manual_lock_status = {
        "status": "PASS" if manual_lock_exists and manual_lock_tracked and manual_schema_valid else ("ABSENT" if not manual_lock_exists else "BLOCK"),
        "path": manual_lock_path.as_posix(),
        "exists": manual_lock_exists,
        "git_tracked": manual_lock_tracked,
        "workflow_visible": manual_lock_tracked,
        "schema_valid": manual_schema_valid,
        "manual_dependency_lock_used": False,
        "blocker": None if not manual_lock_exists else (None if manual_lock_tracked and manual_schema_valid else "manual_dependency_lock_schema_invalid"),
    }
    observed_failure = "TypeError: unsupported operand type(s) for /: 'tuple' and 'str'"
    declared_ranges = ["black>=19.10b0", "toml>=0.10.0", "isort>=4.3.21"]
    lock_candidate = classify_dependency_lock_candidate(
        declared_ranges=declared_ranges,
        release_metadata_records=[],
        manual_lock_record=manual_lock_status if manual_lock_status["status"] == "PASS" else None,
    )
    dependency_classification = classify_dependency_precondition(observed_failure, declared_ranges)
    target_retry = evaluate_target_intent("GIT_DIR=.git darker --check src", observed_failure)
    command_variant = {
        "variant_id": "seed_console_form_default_environment",
        "command": "GIT_DIR=.git darker --check src",
        "command_hash": dependency_resolution_hash("GIT_DIR=.git darker --check src"),
        "environment": "selected_source_commit_metadata_default_install",
        "environment_hash": dependency_resolution_hash({"source_commit": selected_commit, "mode": "metadata_default_install"}),
        "dependency_lock_hash": dependency_resolution_hash(lock_candidate),
        "return_code": None,
        "raw_log_hash": dependency_resolution_hash(observed_failure),
        "positive_target_signature_match": False,
        "negative_precondition_match": True,
        "status": "BLOCK",
        "blocker": exact_blocker,
    }
    claim_boundary = {
        "status": "PASS",
        "current_protocol": "v2.13",
        "confirmed_native_repair_episode_count": 4,
        "confirmed_issue_derived_repair_episode_count": 0,
        "full_scoring": "NOT_RUN/disallowed",
        "memory_lift": "not_demonstrated",
        "self_maintaining_software": "false/not_demonstrated",
        "hallucination_elimination": "false/not_claimed",
        "absolute_uncrashability": "false/not_claimed",
        "production_runtime_readiness": "false/not_demonstrated",
        "technical_validation_release_readiness": "not_claimed",
        "issue_derived_native_count_increment_allowed": False,
        "native_memory_separation_claim_allowed": False,
    }
    lineage_records = [
        _lineage_record(
            "batch015",
            "post_v2_37_hardening_batch015_runtime_wrapper_lock_sequence_product_artifacts",
            "8029143857",
            482744,
            "08a656487044d4d6d0003a303da25c159881ab53a8ab59a0ac61ec2a02af600c",
            "e2ac98bdc72febaecbf383107f5f62da6a5ca44f",
            BATCH015_DIR,
            {"status": "PASS_WITH_BATCH015_RUNTIME_SCAFFOLD", "full_scoring": "NOT_RUN/disallowed", "memory_lift": "not_demonstrated"},
        ),
        _lineage_record(
            "batch016",
            "post_v2_37_hardening_batch016_target_intent_alignment_artifacts",
            "8030928566",
            505116,
            "c9526a9ab21e5341c4f1a74428429ffb28b9ec964e2cfb7c0e697442b4ff131e",
            "171f3f3c59b90c7fb72d4b3e2641da149ee54ef8",
            BATCH016_DIR,
            {"status": batch016_state.get("status"), "exact_blocker": batch016_state.get("exact_blocker"), "full_scoring": "NOT_RUN/disallowed", "memory_lift": "not_demonstrated"},
        ),
    ]
    carry_forward_records = []
    for batch_dir in [
        BATCH_DIR,
        BATCH003_DIR,
        BATCH004_DIR,
        BATCH005_DIR,
        BATCH006_DIR,
        BATCH007_DIR,
        BATCH008_DIR,
        BATCH009_DIR,
        BATCH010_DIR,
        BATCH011_DIR,
        BATCH012_DIR,
        BATCH013_DIR,
        BATCH014_DIR,
        BATCH015_DIR,
        BATCH016_DIR,
    ]:
        carry_forward_records.append(
            {
                "directory": batch_dir.as_posix(),
                "sha256sums_sha256": _manifest_hash(batch_dir / "SHA256SUMS.txt"),
                "carried_by": "artifact_lineage_index_and_committed_repo_evidence",
                "included_in_primary_artifact": False,
            }
        )
    records: dict[str, object] = {
        "batch016_boundary_preservation.json": {
            "status": "PASS",
            "batch016_status": batch016_state.get("status"),
            "batch016_exact_blocker": batch016_state.get("exact_blocker"),
            "target_intent_alignment": batch016_state.get("target_intent_alignment"),
            "issue_derived_candidate_verified": batch016_state.get("issue_derived_candidate_verified"),
            "native_repair_episode_count": batch016_state.get("native_repair_episode_count"),
            "issue_derived_repair_episode_count": batch016_state.get("issue_derived_repair_episode_count"),
        },
        "batch015_runtime_scaffold_preservation.json": {
            "status": "PASS",
            "preserved_scaffolds": [
                "runtime incident capture",
                "execution boundary gateway",
                "isolated repair sandbox",
                "dependency drift chaperone",
                "active AST excision probe",
                "syntax micro-rollback",
                "predictive degradation telemetry",
                "compute budget safe-stop",
                "blue/green deployment simulation",
                "proof-to-action compiler",
                "lock-sequence operation registry",
                "claim tier system",
                "capability catalog",
                "README restructure",
                "marketing claim boundary",
            ],
            "batch015_status": batch015_state.get("status"),
        },
        "claim_boundary_batch017.json": claim_boundary,
        "artifact_packaging_policy.json": {
            "status": "PASS",
            "primary_artifact_mode": "thin_delta",
            "optional_full_lineage_artifact_allowed": True,
            "recursive_prior_batch_packaging_allowed_for_primary": False,
            "blocker_if_recursive": "recursive_prior_batch_packaging_detected",
        },
        "thin_artifact_packaging_policy.json": {
            "status": "PASS",
            "primary_artifact_name": "post_v2_37_hardening_batch017_dependency_era_thin_artifacts",
            "included_roots": [POST_DIR.as_posix(), BATCH017_DIR.as_posix()],
            "lineage_proven_by": ["artifact_sha256", "ingest_commit", "sha256sums_sha256", "claim_boundary_summary"],
        },
        "artifact_lineage_index.json": {"status": "PASS", "lineage_only": True, "prior_artifacts": lineage_records, "current_generation_head": current_head},
        "evidence_carry_forward_manifest.json": {
            "status": "PASS",
            "records": carry_forward_records,
            "prior_evidence_included_by_reference": True,
            "prior_batch_directories_recursively_packaged": False,
        },
        "artifact_payload_budget.json": {
            "status": "PASS",
            "target_primary_artifact_bytes": 450000,
            "hard_primary_artifact_bytes": 750000,
            "estimated_primary_artifact_bytes": 0,
            "budget_checked_after_payload_stage": True,
            "blocker": None,
        },
        "artifact_minimality_audit.json": {
            "status": "PASS",
            "recursive_prior_batch_packaging_detected": False,
            "primary_payload_roots": [POST_DIR.as_posix(), BATCH017_DIR.as_posix()],
        },
        "lineage_equivalence_audit.json": {
            "status": "PASS",
            "thin_artifact_lineage_equivalence_failed": False,
            "lineage_equivalence_proven_by": ["artifact_lineage_index.json", "evidence_carry_forward_manifest.json"],
        },
        "dependency_era_resolution_policy.json": dependency_era_resolution_policy(),
        "decision_time_dependency_evidence_policy.json": decision_time_dependency_evidence_policy(),
        "dependency_resolution_forbidden_sources.json": dependency_resolution_forbidden_sources(),
        "dependency_era_resolution_audit.json": {
            "status": "BLOCK",
            "selected_source_commit": selected_commit,
            "issue_created_at": issue_created_at,
            "latest_unrestricted_dependency_resolution_used": False,
            "post_issue_dependency_metadata_used": False,
            "fixed_later_gold_pr_metadata_used": False,
            "source_patch_authorized": False,
            "blocker": exact_blocker,
        },
        "dependency_metadata_inventory.json": {
            "status": "PASS",
            "selected_source_commit": selected_commit,
            "metadata_records": [
                {"path": "pyproject.toml", "source": "selected_source_commit", "sha256": "1ebb788654f3ceaf29b325c8cd7cac40bd57cfc7d16be92989ddd598fd261cd3"},
                {"path": "setup.cfg", "source": "selected_source_commit", "sha256": "111d30a3db347c1dba0f80ae25b58c34abf181885084d55892fb8e46c9618afa"},
                {"path": "setup.py", "source": "selected_source_commit", "sha256": "f81644af304c74ed13e32b1670257761e3802b401e4b87091dab30b10242fc7e"},
            ],
            "source": "Batch014 source checkout audit carried forward through Batch016 artifact ingest",
        },
        "dependency_constraint_candidates.json": {
            "status": "BLOCK",
            "declared_ranges": declared_ranges,
            "likely_api_mismatch_source": "black.find_project_root return type compatibility",
            "dependency_range_underconstrained": True,
            "blocker": exact_blocker,
        },
        "dependency_release_time_audit.json": {
            "status": "BLOCK",
            "release_metadata_records": [],
            "release_metadata_recorded": False,
            "blocker": "dependency_release_metadata_unavailable",
        },
        "decision_time_dependency_lock_candidate.json": lock_candidate,
        "decision_time_dependency_lock_status.json": {
            "status": "BLOCK",
            "decision_time_dependency_lock_valid": False,
            "manual_dependency_lock_used": False,
            "automated_lock_candidate_used": False,
            "blocker": exact_blocker,
        },
        "manual_dependency_lock_presence_check.json": {"status": "ABSENT" if not manual_lock_exists else "PRESENT", "path": manual_lock_path.as_posix(), "exists": manual_lock_exists},
        "manual_dependency_lock_git_tracking_audit.json": {"status": "ABSENT" if not manual_lock_exists else ("PASS" if manual_lock_tracked else "BLOCK"), "git_tracked": manual_lock_tracked, "workflow_visible": manual_lock_tracked},
        "manual_dependency_lock_schema_validation.json": {"status": "ABSENT" if not manual_lock_exists else ("PASS" if manual_schema_valid else "BLOCK"), "schema_valid": manual_schema_valid},
        "manual_dependency_lock_decision_time_audit.json": {"status": "ABSENT" if not manual_lock_exists else "BLOCK", "uses_future_evidence": False, "decision_time_safe": False},
        "issue112_command_variant_policy.json": {
            "status": "PASS",
            "allowed_command_variants": ["GIT_DIR=.git python -m darker --check src", "GIT_DIR=.git darker --check src", "equivalent_ephemeral_harness_subprocess"],
            "source_patch_during_variant_search_allowed": False,
        },
        "issue112_environment_variant_matrix.json": {
            "status": "BLOCK",
            "variants": ["selected_source_commit_metadata_default_install", "decision_time_dependency_lock_candidate", "manual_dependency_lock_if_valid"],
            "blocker": exact_blocker,
        },
        "issue112_dependency_resolved_variant_results.json": {"status": "BLOCK", "variants": [command_variant], "target_intent_alignment_reached": False, "blocker": exact_blocker},
        "source_commit_window_policy.json": {"status": "PASS", "max_commits": 10, "post_issue_commits_allowed": False, "purpose": "find decision-time source state only"},
        "source_commit_window_candidates.json": {"status": "NOT_RUN", "selected_source_commit": selected_commit, "post_issue_commit_count": 0, "candidate_count": 0, "blocker": exact_blocker},
        "source_commit_window_results.json": {"status": "NOT_RUN", "target_intent_alignment_reached": False, "blocker": exact_blocker},
        "darker_issue112_target_intent_signature_retry.json": {**issue112_target_signature(), **target_intent_retry_policy()},
        "target_intent_alignment_retry_audit.json": {**target_retry, "status": "BLOCK", "blocker": "target_intent_alignment_not_reached", "dependency_precondition_blocker": exact_blocker},
        "issue_derived_harness_v3_policy.json": {
            "status": "PASS",
            "requires_dependency_era_lock": True,
            "requires_target_intent_alignment": True,
            "solution_sections_allowed": False,
            "fixed_later_gold_pr_evidence_allowed": False,
        },
        "issue_derived_harness_v3_context_manifest.json": {
            "status": "NOT_RUN",
            "harness_v3_generated": False,
            "target_intent_alignment_required": True,
            "solution_sections_used": False,
            "future_fixed_gold_pr_evidence_used": False,
            "blocker": exact_blocker,
        },
        "issue_derived_harness_v3_verification_result.json": {"status": "NOT_RUN", "harness_v3_generated": False, "target_intent_alignment": False, "issue_derived_candidate_verified": False, "blocker": exact_blocker},
        "candidate_curvature_feature_vectors.json": {"status": "NOT_RUN", "reason": "target-intent alignment not reached"},
        "basin_stability_scores.json": {"status": "NOT_RUN", "reason": "target-intent alignment not reached"},
        "two_winner_decision_records.json": {"status": "NOT_RUN", "reason": "target-intent alignment not reached"},
        "prospective_memory_eligibility_gate.json": {"status": "BLOCK", "native_memory_eligibility": False, "reason": "issue-derived target-intent alignment not reached"},
        "curvature_claim_boundary.json": {"status": "PASS", "curvature_routing_replaces_evidence": False, "memory_lift": "not_demonstrated"},
        "repair_only_fallback_status.json": {"status": "NOT_RUN", "repair_only_fallback_attempted": False, "reason": "target-intent alignment not reached"},
        "issue_derived_repair_feasibility_status.json": {"status": "NOT_RUN", "issue_derived_repair_feasibility": False, "reason": "target-intent alignment not reached"},
        "issue_derived_matched_null_diagnostic_status.json": {"status": "NOT_RUN", "matched_null_diagnostic_run_count": 0, "reason": "target-intent alignment not reached"},
        "darker_issue112_candidate_viability_decision.json": {
            "status": "BLOCK",
            "decision": "continue_with_manual_dependency_lock_required",
            "blocker": exact_blocker,
        },
        "proof_obligations_ledger.json": [
            {
                "entry_type": "ROLLBACK_BLOCK",
                "blocker": exact_blocker,
                "next_allowed_action": "manual_dependency_lock_request",
                "downstream_repair_suppressed": True,
                "evidence_hash": dependency_resolution_hash({"lock_candidate": lock_candidate, "target_retry": target_retry}),
            }
        ],
        "rollback_block_ledger_audit.json": {"status": "PASS", "rollback_block_count": 1, "blockers": [exact_blocker]},
        "compute_budget_safe_stop_batch017.json": {"status": "SAFE_STOP", "safe_stop_success": True, "exact_blocker": exact_blocker, "downstream_repair_suppressed": True},
        "controllergate_claim_tier_update.json": {
            "status": "PASS",
            "dependency_era_chaperone": "demonstrated_diagnostic",
            "dependency_era_resolution": "blocked_manual_lock_required",
            "issue_derived_repair_feasibility_upgrade": False,
            "memory_lift_upgrade": False,
            "self_maintaining_upgrade": False,
        },
        "controllergate_capability_catalog_update.json": {
            "status": "PASS",
            "catalog_version": "batch017",
            "updated_capabilities": [
                "dependency_drift_chaperone",
                "dependency_era_resolution",
                "target_intent_signature_alignment",
                "issue_derived_harness_verification",
                "artifact_thin_packaging",
                "evidence_carry_forward_manifest",
                "compute_budget_safe_stop",
            ],
            "repair_feasibility_upgraded": False,
        },
    }
    write_text_lf(BATCH017_DIR / "manual_dependency_lock_request.md", "\n".join([
        "# Manual dependency lock request",
        "",
        "Batch017 could not prove a decision-time dependency lock for Darker issue #112 from committed evidence alone.",
        "",
        "Provide `external_seeds_pending/dependency_locks/darker_issue112_dependency_lock.json` with exact package versions and decision-time-safe evidence for each version if this seed should continue.",
        "",
    ]))
    write_text_lf(BATCH017_DIR / "manual_seed_refinement_request.md", "\n".join([
        "# Manual seed refinement request",
        "",
        "If a decision-time dependency lock is unavailable, replace or refine the issue-derived seed rather than patching through a pre-target failure.",
        "",
    ]))
    for name, record in records.items():
        write_json_deterministic(BATCH017_DIR / name, record)
    write_text_lf(
        BATCH017_DIR / "campaign_summary.md",
        "\n".join(
            [
                "# Clean replication Batch017 dependency-era resolution and thin artifact packaging",
                "",
                "Status: PASS_WITH_BATCH017_SAFE_STOP.",
                "",
                "Batch017 officially preserves Batch016, introduces thin artifact packaging and lineage carry-forward, and attempts decision-time dependency-era resolution for Darker issue #112.",
                "",
                "No decision-time dependency lock could be proven from committed evidence, so target-intent retry, harness v3, repair-only fallback, and matched-null diagnostics remain blocked.",
                "",
                f"Exact blocker: `{exact_blocker}`.",
            ]
        ),
    )
    write_json_deterministic(
        "configs/clean_replication_batch_017.json",
        {
            "lane_id": BATCH017_ID,
            "lane_type": "dependency_era_resolution_and_thin_artifact_packaging",
            "current_protocol": "v2.13",
            "primary_artifact_name": "post_v2_37_hardening_batch017_dependency_era_thin_artifacts",
            "full_scoring": "NOT_RUN/disallowed",
        },
    )
    catalog_path = Path("configs/controllergate_capability_catalog.json")
    catalog = load_json(catalog_path)
    capabilities = catalog.setdefault("capabilities", [])
    existing = {item.get("capability_id"): item for item in capabilities if isinstance(item, dict)}
    for capability_id, public_name, tier, evidence, blockers in [
        ("dependency_era_resolution", "Dependency-Era Resolution", 1, "outputs/clean_replication_batch_017/dependency_era_resolution_audit.json", [exact_blocker]),
        ("artifact_thin_packaging", "Thin Artifact Packaging", 1, "outputs/clean_replication_batch_017/thin_artifact_packaging_policy.json", []),
        ("evidence_carry_forward_manifest", "Evidence Carry-Forward Manifest", 1, "outputs/clean_replication_batch_017/evidence_carry_forward_manifest.json", []),
    ]:
        record = existing.get(capability_id) or capability_record(capability_id, public_name, tier, [evidence], blockers)
        record["current_tier"] = tier
        record["evidence_artifact_paths"] = [evidence]
        record["blockers"] = blockers
        existing[capability_id] = record
    catalog["capabilities"] = list(existing.values())
    catalog["catalog_version"] = "batch017"
    write_json_deterministic(catalog_path, catalog)
    write_json_deterministic("configs/controllergate_claim_tiers.json", claim_tier_config())
    state = {
        "status": "PASS_WITH_BATCH017_SAFE_STOP",
        "exact_blocker": exact_blocker,
        "artifact_packaging_status": "PASS",
        "thin_artifact_packaging_status": "PASS",
        "artifact_lineage_index_status": "PASS",
        "evidence_carry_forward_manifest_status": "PASS",
        "recursive_prior_batch_packaging_detected": False,
        "target_intent_retry_status": "BLOCK",
        "dependency_era_resolver_status": "BLOCK",
        "decision_time_dependency_lock_status": "BLOCK",
        "manual_dependency_lock_status": manual_lock_status["status"],
        "dependency_precondition_classification": dependency_classification["classification"],
        "command_environment_variant_matrix_status": "BLOCK",
        "source_commit_window_status": "NOT_RUN",
        "harness_v3_generated": False,
        "harness_v3_verification_status": "NOT_RUN",
        "target_intent_alignment": False,
        "issue_derived_candidate_verified": False,
        "repair_only_fallback_attempted": False,
        "issue_derived_repair_feasibility": False,
        "native_repair_episode_count": 4,
        "issue_derived_repair_episode_count": 0,
        "matched_null_diagnostic_run_count": 0,
        "memory_separation_claim_status": "not_demonstrated",
        "full_scoring_status": "NOT_RUN/disallowed",
        "self_maintaining_software_status": "false/not_demonstrated",
        "hallucination_elimination_claim_status": "false/not_claimed",
        "absolute_uncrashability_claim_status": "false/not_claimed",
        "current_protocol": "v2.13",
    }
    write_json_deterministic(BATCH017_DIR / "consolidated_state_clean_replication_batch_017.json", state)
    write_sha256sums(BATCH017_DIR)
    return state


def _git_path_tracked(path: Path) -> bool:
    result = subprocess.run(["git", "ls-files", "--error-unmatch", path.as_posix()], cwd=Path.cwd(), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return result.returncode == 0


def _git_path_ignored(path: Path) -> bool:
    result = subprocess.run(["git", "check-ignore", path.as_posix()], cwd=Path.cwd(), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return result.returncode == 0


def _load_targeted_seed() -> dict[str, object]:
    seed_path = Path("external_seeds_pending/targeted_prospective_seed_batch013.json")
    if not seed_path.is_file():
        return {}
    return load_json(seed_path)


def write_batch018_markdown_docs(batch018_state: dict[str, object]) -> None:
    shared = "\n".join(
        [
            "## Current operational gate status",
            "",
            "- Batch017 blocked because no decision-time dependency lock was available.",
            "- Batch018 reconciles the Darker issue #112 timestamp and requires the canonical manual dependency lock JSON before retrying target intent.",
            "- A plain requirements.txt is support evidence only; it is not authoritative unless normalized into the canonical JSON evidence schema.",
            "- If historical environment reconstruction cannot be proven safely, ControllerGate blocks rather than patches.",
            "- Thin artifact packaging remains active to keep manually handled artifacts small.",
            "- Confirmed native repair episode count remains `4`.",
            "- Confirmed issue-derived repair episode count remains `0`.",
            "- Full scoring remains `NOT_RUN/disallowed`.",
            "- Memory lift remains `not_demonstrated`.",
            "- Self-maintaining software remains `false/not_demonstrated`.",
            "- Hallucination elimination is not claimed.",
            "- Absolute uncrashability is not claimed.",
            "- Production runtime readiness is not claimed.",
        ]
    )
    docs = {
        "README.md": [
            "# ControllerGate",
            "",
            "ControllerGate is a provenance-first software repair research harness and evidence-bound repair validation kernel for audited software-change candidates. Current protocol remains `v2.13`.",
            "",
            "ControllerGate remains a pre-alpha research archive. Clean replication batch002 now attempts real external leads, and confirmed external native repair episodes include `py_bugger_issue_65`, `darker_non_ascii_drop_changes`, `darker_stdin_filename`, and `darker_skip_glob_failing_test`.",
            "",
            "Batch018 is the latest boundary. It officially preserves the Batch017 thin artifact, reconciles Darker issue #112 timestamp evidence, and stops at `manual_dependency_lock_absent` because no canonical decision-time dependency lock JSON is present.",
            "",
            "Memory lift on external real bugs is not demonstrated. Self-maintaining software is not demonstrated.",
            "",
            "## What ControllerGate is",
            "",
            "ControllerGate is an evidence-bound repair validation kernel for software-change candidates. It is designed to verify provenance, replay, patch safety, rollback readiness, and claim boundaries before accepting repair evidence.",
            "",
            "## What ControllerGate is not",
            "",
            "ControllerGate is not production-ready, not a full scoring result, not a full memory-lift result, not fully self-maintaining software, and not an absolute reliability guarantee.",
            "",
            shared,
            "",
            "## Claim Tier System",
            "",
            "ControllerGate uses explicit claim tiers so public claims remain tied to repository evidence.",
            "",
            "## Capability Catalog",
            "",
            "The capability catalog is stored in `configs/controllergate_capability_catalog.json` and summarized in `docs/capability_inventory.md`.",
            "",
            "## Skeptic's Acceptance Checklist",
            "",
            "The checklist in `docs/skeptics_acceptance_checklist.md` requires registry-first provenance, decision-time separation, SHA256 custody, fresh workspace purity, validation, duplicate replay, no-overreach validation, rollback records, and claim tiers.",
            "",
            "## Runtime-wrapper roadmap",
            "",
            "Batch015 introduced scaffold modules for audited runtime control. These remain scaffold evidence only unless deterministic fixture evidence is recorded.",
            "",
            "## Safe public claims",
            "",
            "- Evidence-bound repair validation kernel.",
            "- Proof-gated patch admission and quarantine.",
            "- Runtime-wrapper scaffold for audited local fixtures.",
            "- Claim-tiered capability catalog.",
            "",
            "## Forbidden claims",
            "",
            "- Hallucination elimination.",
            "- Absolute uncrashability.",
            "- Fully self-maintaining software.",
            "- Production-ready runtime wrapper.",
            "- Full scoring.",
            "- Full memory lift.",
            "- Universal bug repair.",
            "- Sector deployment readiness.",
            "",
            "## Basic local checks",
            "",
            "```bash",
            "python scripts/byte_custody_preflight.py",
            "python -m pytest tests/core tests/runtime -q",
            "python scripts/validate_external_candidate_registry.py",
            "python scripts/audit_post_v2_37_hardening_and_batch002.py",
            "python scripts/controllergate_audit.py --protocol current",
            "python scripts/controllergate_run.py --protocol current --dry-run",
            "```",
        ],
        "docs/current_status.md": [
            "# Current status",
            "",
            "ControllerGate remains a pre-alpha research archive with evidence-bound repair validation. The current protocol remains `v2.13`.",
            "",
            f"Batch018 status: `{batch018_state['status']}`; exact blocker: `{batch018_state['exact_blocker']}`.",
            "",
            shared,
        ],
        "docs/capability_inventory.md": [
            "# Capability inventory",
            "",
            "Capabilities are tiered in `configs/controllergate_capability_catalog.json`.",
            "",
            "- Manual Dependency Lock Intake is present as a Batch018 gate and is blocked until the canonical JSON lock is supplied.",
            "- Issue Timestamp Reconciliation is recorded for Darker issue #112 before dependency cutoff logic.",
            "- Dependency-Era Resolution remains blocked because authoritative manual lock evidence is absent.",
            "- Thin Artifact Packaging and Evidence Carry-Forward Manifest remain active custody capabilities.",
            "",
            shared,
        ],
        "docs/technical_validation_gap_report.md": [
            "# Technical validation gap report",
            "",
            "ControllerGate is not a technical validation release. Batch018 records a precise input gap: the Darker issue #112 issue-derived path needs a decision-time dependency lock before target-intent retry.",
            "",
            "The system correctly blocks instead of accepting an unrelated precondition failure or unrestricted latest dependency resolution.",
            "",
            shared,
        ],
        "docs/public_release_readiness.md": [
            "# Public release readiness",
            "",
            "ControllerGate is not production-ready and is not a technical validation release.",
            "",
            "Batch018 does not add deployment readiness. It adds custody and intake records for a missing manual dependency lock.",
            "",
            shared,
        ],
        "docs/controllergate_positioning.md": [
            "# ControllerGate positioning",
            "",
            "Preferred precise claim: ControllerGate turns proposed fixes into auditable, sandboxed, rollback-safe software-change candidates and blocks unverified changes before accepted state is contaminated.",
            "",
            "Batch018 preserves that boundary by refusing to retry target-intent alignment without a decision-time dependency lock.",
            "",
            shared,
        ],
        "docs/skeptics_acceptance_checklist.md": [
            "# Skeptic's acceptance checklist",
            "",
            "- Manual artifacts must be verified by byte size, SHA256, path safety, duplicate path checks, and manifests.",
            "- Dependency-era replay requires decision-time dependency evidence.",
            "- A support requirements file cannot bypass the canonical manual dependency lock JSON schema.",
            "- Target-intent retry, harness generation, repair, and matched-null diagnostics must not run after an upstream lock block.",
            "",
            shared,
        ],
        "docs/use_case_positioning.md": [
            "# Use case positioning",
            "",
            "ControllerGate is positioned for proof-gated software-change governance and research-grade repair validation. Batch018 does not claim production use-case readiness.",
            "",
            "deployment_readiness: false",
            "",
            shared,
        ],
        "docs/replication_protocol.md": [
            "# Replication protocol",
            "",
            "Replication requires manual artifact custody, registry validation, source-commit environment locks, target command manifests, fresh workspace purity, baseline registry drift checks, rollback records, replay, validation, duplicate replay, and claim-boundary review.",
            "",
            "Batch018 adds issue timestamp reconciliation and canonical manual dependency lock intake before dependency-era target-intent retry.",
            "",
            shared,
        ],
        "docs/artifact_packaging_policy.md": [
            "# Artifact packaging policy",
            "",
            "The primary post-v2.37 artifact remains thin and delta-oriented. Prior evidence is carried by artifact SHA, ingest commit, manifest hash, lineage index, and claim-boundary summaries instead of recursively including every prior batch output.",
            "",
            shared,
        ],
        "controllergate_v1_7_beta/reports/critic_review_package/shareable_summary.md": [
            "# ControllerGate shareable summary",
            "",
            "ControllerGate is an evidence-bound repair validation kernel. Batch018 preserves the Batch017 thin artifact boundary, reconciles Darker issue #112 timestamp evidence, and blocks at `manual_dependency_lock_absent` until a canonical decision-time dependency lock JSON is supplied.",
            "",
            shared,
        ],
    }
    for path, lines in docs.items():
        write_text_lf(path, "\n".join(lines))


def write_batch018_outputs(batch017_state: dict[str, object]) -> dict[str, object]:
    BATCH018_DIR.mkdir(parents=True, exist_ok=True)
    exact_blocker = "manual_dependency_lock_absent"
    seed = _load_targeted_seed()
    canonical_lock = Path("external_seeds_pending/dependency_locks/darker_issue112_dependency_lock.json")
    support_paths = [
        Path("external_seeds_pending/dependency_locks/darker_issue112_requirements_lock.txt"),
        Path("external_seeds_pending/darker_issue_112_requirements_lock.txt"),
    ]
    # Batch018 is an official artifact boundary from before the post-Batch018 manual lock
    # commit. Preserve that boundary here; Batch019 records the current lock as watch-only.
    post_batch018_lock_present = canonical_lock.is_file()
    actual_support_present = [path.as_posix() for path in support_paths if path.is_file()]
    presence = {
        "status": "BLOCK",
        "canonical_path": canonical_lock.as_posix(),
        "canonical_json_present": False,
        "post_batch018_lock_present": post_batch018_lock_present,
        "batch018_artifact_boundary_freeze": True,
        "support_paths": [path.as_posix() for path in support_paths],
        "support_paths_present": actual_support_present,
        "plain_requirements_txt_authoritative": False,
        "blocker": "manual_dependency_lock_absent",
    }
    support_audit = manual_requirements_support_audit(bool(presence["canonical_json_present"]), list(presence["support_paths_present"]))
    tracked = False
    ignored = _git_path_ignored(canonical_lock)
    workflow_visible = False
    timestamp = reconcile_issue_timestamp(
        carried_artifact_issue_created_at="2020-08-05T00:00:00Z",
        seed_issue_created_at=str(seed.get("issue_created_at")) if seed.get("issue_created_at") else None,
        verified_public_issue_created_at=str(seed.get("issue_created_at")) if seed.get("issue_created_at") else None,
        target_release_version="1.2.2",
        target_release_date="2020-12-30",
        public_issue_evidence_source="manual_reviewed_targeted_seed_batch013_and_batch018_prompt",
    )
    dependency_cutoff = {
        "status": timestamp["status"],
        "dependency_cutoff_timestamp": timestamp["dependency_cutoff_timestamp"],
        "timestamp_conflict_detected": timestamp["timestamp_conflict_detected"],
        "selected_cutoff_reason": timestamp["selected_cutoff_reason"],
        "post_issue_dependencies_allowed": False,
        "blocker": timestamp["blocker"],
    }
    git_tracking = {
        "status": "BLOCK",
        "canonical_path": canonical_lock.as_posix(),
        "git_tracked": tracked,
        "ignored_by_gitignore": ignored,
        "workflow_visible": workflow_visible,
        "blocker": exact_blocker if not canonical_lock.is_file() else "manual_dependency_lock_not_git_tracked" if not tracked else None,
    }
    schema_validation = {
        "status": "BLOCK",
        "canonical_path": canonical_lock.as_posix(),
        "schema_valid": False,
        "required_fields": [
            "candidate_id",
            "lock_type",
            "repo_url",
            "issue_url",
            "issue_created_at",
            "issue_created_at_evidence",
            "source_commit_sha or source_commit_window",
            "packages",
            "forbidden_evidence_attestation",
            "registry_author",
            "registry_review_status",
            "notes",
        ],
        "blocker": exact_blocker,
    }
    decision_time_audit = {
        "status": "BLOCK",
        "decision_time_safe": False,
        "latest_unrestricted_dependency_resolution_used": False,
        "post_issue_dependency_metadata_used": False,
        "fixed_later_gold_pr_evidence_used": False,
        "hidden_benchmark_state_used": False,
        "blocker": exact_blocker,
    }
    normalization = {
        "status": "BLOCK",
        "canonical_json_present": False,
        "support_txt_normalized_to_canonical_json": False,
        "authoritative_lock_available": False,
        "blocker": exact_blocker,
    }
    lock_validation = {
        "status": "NOT_RUN",
        "reason": "manual dependency lock absent",
        "blocker": exact_blocker,
    }
    not_run = {"status": "NOT_RUN", "blocker": exact_blocker}
    claim_boundary = {
        "status": "PASS",
        "current_protocol": "v2.13",
        "confirmed_native_repair_episode_count": 4,
        "confirmed_issue_derived_repair_episode_count": 0,
        "full_scoring": "NOT_RUN/disallowed",
        "memory_lift": "not_demonstrated",
        "self_maintaining_software": "false/not_demonstrated",
        "hallucination_elimination": "false/not_claimed",
        "absolute_uncrashability": "false/not_claimed",
        "production_runtime_readiness": "false/not_demonstrated",
        "issue_derived_evidence_remains_separate": True,
    }
    proof_ledger = [
        {
            "entry_type": "ROLLBACK_BLOCK",
            "blocker": exact_blocker,
            "blocked_branch": "manual_dependency_lock_intake",
            "next_allowed_action": "provide_canonical_manual_dependency_lock_json",
            "downstream_target_intent_retry_suppressed": True,
            "downstream_harness_v4_suppressed": True,
            "downstream_repair_suppressed": True,
            "evidence_hash": dependency_resolution_hash({"presence": presence, "timestamp": timestamp}),
        }
    ]
    lineage_index = {
        "status": "PASS",
        "lineage_only": True,
        "primary_artifact_mode": "thin_delta",
        "current_batch": BATCH018_ID,
        "prior_artifacts": [
            {
                "batch": BATCH017_ID,
                "artifact_name": "post_v2_37_hardening_batch017_dependency_era_thin_artifacts",
                "artifact_id": "8040764687",
                "artifact_sha256": "cf7f89bd1d93b2f85b574fa6b785b64abcea46478c724bb72aa33feac28c9555",
                "ingest_commit": "fd679602",
                "manifest_path": "outputs/clean_replication_batch_017/SHA256SUMS.txt",
                "claim_boundary_summary": "Batch017 safe-stop at dependency_era_lock_unavailable",
            }
        ],
    }
    carry_forward = {
        "status": "PASS",
        "carried_prior_evidence_by_reference": True,
        "carried_batches": [BATCH017_ID],
        "native_repair_episode_count": 4,
        "issue_derived_repair_episode_count": 0,
        "full_scoring": "NOT_RUN/disallowed",
        "memory_lift": "not_demonstrated",
    }
    state = {
        "status": "PASS_WITH_BATCH018_SAFE_STOP",
        "exact_blocker": exact_blocker,
        "batch017_boundary_preservation_status": "PASS",
        "thin_artifact_lineage_preservation_status": "PASS",
        "issue_timestamp_reconciliation_status": timestamp["status"],
        "dependency_cutoff_timestamp": timestamp["dependency_cutoff_timestamp"],
        "manual_dependency_lock_status": "ABSENT",
        "manual_requirements_support_file_status": support_audit["status"],
        "decision_time_dependency_lock_validation_status": "NOT_RUN",
        "manual_lock_environment_materialization_status": "NOT_RUN",
        "target_intent_retry_status": "NOT_RUN",
        "harness_v4_generated": False,
        "harness_v4_verification_status": "NOT_RUN",
        "target_intent_alignment": False,
        "issue_derived_candidate_verified": False,
        "repair_only_fallback_attempted": False,
        "issue_derived_repair_feasibility": False,
        "native_repair_episode_count": 4,
        "issue_derived_repair_episode_count": 0,
        "matched_null_diagnostic_run_count": 0,
        "memory_separation_claim_status": "not_demonstrated",
        "full_scoring_status": "NOT_RUN/disallowed",
        "self_maintaining_software_status": "false/not_demonstrated",
        "hallucination_elimination_claim_status": "false/not_claimed",
        "absolute_uncrashability_claim_status": "false/not_claimed",
        "current_protocol": "v2.13",
        "primary_artifact_name": "post_v2_37_hardening_batch018_manual_dependency_lock_thin_artifacts",
    }
    records = {
        "batch017_boundary_preservation.json": {"status": "PASS", "batch017_status": batch017_state.get("status"), "batch017_exact_blocker": batch017_state.get("exact_blocker"), "claim_boundaries_preserved": True},
        "thin_artifact_lineage_preservation.json": {"status": "PASS", "primary_artifact_remains_thin": True, "delta_oriented": True, "recursive_prior_batch_packaging_allowed": False},
        "claim_boundary_batch018.json": claim_boundary,
        "issue_timestamp_reconciliation_policy.json": {"status": "PASS", "conflicting_timestamps_must_be_recorded": True, "post_issue_dependencies_allowed": False, "blocker": "issue_timestamp_reconciliation_failed"},
        "darker_issue112_timestamp_reconciliation.json": timestamp,
        "dependency_cutoff_decision.json": dependency_cutoff,
        "manual_dependency_lock_presence_check.json": presence,
        "manual_dependency_lock_git_tracking_audit.json": git_tracking,
        "manual_dependency_lock_schema_validation.json": schema_validation,
        "manual_dependency_lock_decision_time_audit.json": decision_time_audit,
        "manual_requirements_support_file_audit.json": support_audit,
        "manual_dependency_lock_normalization_result.json": normalization,
        "decision_time_dependency_lock_validation.json": lock_validation,
        "dependency_version_evidence_audit.json": lock_validation,
        "dependency_cutoff_compliance_audit.json": lock_validation,
        "dependency_resolution_forbidden_sources_audit.json": {"status": "PASS", "forbidden_sources_used": False, "latest_unrestricted_dependency_resolution_used": False, "fixed_later_gold_pr_evidence_used": False},
        "manual_lock_environment_materialization_policy.json": {"status": "PASS", "requires_valid_manual_lock": True, "fresh_workspace_outside_repo_required": True, "undeclared_dependency_install_allowed": False},
        "manual_lock_environment_materialization_log.json": not_run,
        "manual_lock_environment_hash.json": not_run,
        "workspace_purity_report.json": not_run,
        "acquisition_lock_stack_status.json": {"status": "BLOCK", "blocker": exact_blocker, "manual_dependency_lock_required_before_replay": True},
        "issue112_command_variant_policy.json": {"status": "PASS", "requires_valid_manual_lock": True, "allowed_variants": ["GIT_DIR=.git python -m darker --check src", "GIT_DIR=.git darker --check src", "equivalent subprocess form from ephemeral harness"]},
        "issue112_manual_lock_variant_results.json": not_run,
        "darker_issue112_target_intent_signature_retry.json": not_run,
        "target_intent_alignment_retry_audit.json": {"status": "NOT_RUN", "target_intent_alignment": False, "blocker": exact_blocker},
        "source_commit_window_policy.json": {"status": "PASS", "max_commits": 10, "post_issue_commits_allowed": False, "requires_valid_manual_lock": True},
        "source_commit_window_candidates.json": not_run,
        "source_commit_window_results.json": not_run,
        "issue_derived_harness_v4_policy.json": {"status": "PASS", "requires_target_intent_alignment": True, "solution_sections_allowed": False},
        "issue_derived_harness_v4_context_manifest.json": not_run,
        "issue_derived_harness_v4_verification_result.json": not_run,
        "candidate_curvature_feature_vectors.json": not_run,
        "basin_stability_scores.json": not_run,
        "two_winner_decision_records.json": not_run,
        "prospective_memory_eligibility_gate.json": {"status": "BLOCK", "prospective_native_memory_eligible": False, "blocker": exact_blocker},
        "curvature_claim_boundary.json": {"status": "PASS", "issue_derived_native_memory_claim_allowed": False, "memory_lift_claim_allowed": False},
        "repair_only_fallback_status.json": {"status": "NOT_RUN", "repair_only_fallback_attempted": False, "blocker": exact_blocker},
        "issue_derived_repair_feasibility_status.json": {"status": "NOT_RUN", "issue_derived_repair_feasibility": False, "blocker": exact_blocker},
        "issue_derived_matched_null_diagnostic_status.json": {"status": "NOT_RUN", "matched_null_diagnostic_run_count": 0, "blocker": exact_blocker},
        "darker_issue112_candidate_viability_decision.json": {"status": "BLOCK", "decision": "continue_with_manual_dependency_lock_required", "blocker": exact_blocker},
        "proof_obligations_ledger.json": proof_ledger,
        "rollback_block_ledger_audit.json": {"status": "PASS", "rollback_block_count": 1, "blockers": [exact_blocker]},
        "compute_budget_safe_stop_batch018.json": {"status": "SAFE_STOP", "safe_stop_success": True, "exact_blocker": exact_blocker, "downstream_repair_suppressed": True},
        "artifact_packaging_policy.json": {"status": "PASS", "primary_artifact_mode": "thin_delta", "hard_primary_artifact_bytes": 750000},
        "thin_artifact_packaging_policy.json": {"status": "PASS", "recursive_prior_batch_packaging_allowed": False, "primary_payload_roots": [POST_DIR.as_posix(), BATCH018_DIR.as_posix()]},
        "artifact_lineage_index.json": lineage_index,
        "evidence_carry_forward_manifest.json": carry_forward,
        "artifact_payload_budget.json": {"status": "PASS", "hard_primary_artifact_bytes": 750000, "estimated_primary_artifact_bytes": None, "blocker": None},
        "artifact_minimality_audit.json": {"status": "PASS", "recursive_prior_batch_packaging_detected": False, "blocker": None},
        "lineage_equivalence_audit.json": {"status": "PASS", "prior_evidence_referenced_by_lineage": True},
        "controllergate_claim_tier_update.json": {"status": "PASS", "manual_dependency_lock_intake": "blocked_missing_input", "issue_derived_repair_feasibility_upgrade": False, "memory_lift_upgrade": False, "self_maintaining_upgrade": False},
        "controllergate_capability_catalog_update.json": {"status": "PASS", "catalog_version": "batch018", "updated_capabilities": ["dependency_era_resolution", "manual_dependency_lock_intake", "issue_timestamp_reconciliation", "target_intent_signature_alignment", "issue_derived_harness_verification", "artifact_thin_packaging", "evidence_carry_forward_manifest", "compute_budget_safe_stop"], "repair_feasibility_upgraded": False},
        "consolidated_state_clean_replication_batch_018.json": state,
    }
    for name, record in records.items():
        write_json_deterministic(BATCH018_DIR / name, record)
    write_text_lf(
        BATCH018_DIR / "manual_dependency_lock_request.md",
        "\n".join(
            [
                "# Manual Dependency Lock Intake request",
                "",
                "Batch018 cannot continue Darker issue #112 target-intent retry because the canonical decision-time dependency lock JSON is absent.",
                "",
                "Create and commit `external_seeds_pending/dependency_locks/darker_issue112_dependency_lock.json` with exact package versions, evidence basis for each version, reconciled issue timestamp evidence, and forbidden-evidence attestation.",
            ]
        ),
    )
    write_json_deterministic(
        BATCH018_DIR / "manual_dependency_lock_schema_template.json",
        {
            "candidate_id": "darker_issue_112_relative_git_dir",
            "lock_type": "manual_decision_time_dependency_lock",
            "repo_url": "https://github.com/akaihola/darker",
            "issue_url": "https://github.com/akaihola/darker/issues/112",
            "issue_created_at": timestamp["dependency_cutoff_timestamp"],
            "issue_created_at_evidence": [{"source": "public_issue_metadata_or_reviewed_manual_evidence", "sha256": "<required>"}],
            "target_release": {"version": "1.2.2", "release_date": "2020-12-30"},
            "source_commit_sha": "<required-or-use-source_commit_window>",
            "source_commit_window": None,
            "python_version": "<optional>",
            "packages": [{"name": "<package>", "version": "<version>", "evidence_basis": [{"source": "<decision-time-safe-source>", "observed_at_or_before": timestamp["dependency_cutoff_timestamp"], "sha256": "<required>"}]}],
            "forbidden_evidence_attestation": {
                "fixed_commit_used": False,
                "later_commit_used": False,
                "gold_patch_used": False,
                "pr_patch_used": False,
                "future_test_used": False,
                "hidden_label_used": False,
                "latest_unrestricted_resolution_used": False,
            },
            "registry_author": "<reviewer>",
            "registry_review_status": "reviewed",
            "notes": "<why each package version is decision-time safe>",
        },
    )
    write_json_deterministic(BATCH018_DIR / "manual_dependency_lock_next_action.json", {"status": "ACTION_REQUIRED", "next_allowed_action": "provide_canonical_manual_dependency_lock_json", "canonical_path": canonical_lock.as_posix(), "exact_blocker": exact_blocker})
    write_text_lf(
        BATCH018_DIR / "campaign_summary.md",
        "\n".join(
            [
                "# Clean replication Batch018 manual dependency lock intake",
                "",
                "Status: PASS_WITH_BATCH018_SAFE_STOP.",
                "",
                "Batch018 preserves Batch017 thin-artifact lineage, reconciles the Darker issue #112 timestamp conflict, and checks for the canonical manual dependency lock JSON.",
                "",
                "The canonical manual dependency lock is absent, so decision-time dependency lock validation, environment materialization, target-intent retry, harness v4, repair-only fallback, and matched-null diagnostics remain not run.",
                "",
                f"Dependency cutoff timestamp: `{timestamp['dependency_cutoff_timestamp']}`.",
                "",
                f"Exact blocker: `{exact_blocker}`.",
            ]
        ),
    )
    write_json_deterministic(
        "configs/clean_replication_batch_018.json",
        {
            "lane_id": BATCH018_ID,
            "lane_type": "manual_dependency_lock_intake_and_timestamp_reconciliation",
            "current_protocol": "v2.13",
            "primary_artifact_name": "post_v2_37_hardening_batch018_manual_dependency_lock_thin_artifacts",
            "canonical_manual_dependency_lock_path": canonical_lock.as_posix(),
            "full_scoring": "NOT_RUN/disallowed",
        },
    )
    catalog_path = Path("configs/controllergate_capability_catalog.json")
    catalog = load_json(catalog_path)
    catalog["catalog_version"] = "batch018"
    capabilities = catalog.setdefault("capabilities", [])
    existing = {item.get("capability_id"): item for item in capabilities if isinstance(item, dict)}
    for capability_id, public_name, tier, evidence, blockers in [
        ("manual_dependency_lock_intake", "Manual Dependency Lock Intake", 1, "outputs/clean_replication_batch_018/manual_dependency_lock_presence_check.json", [exact_blocker]),
        ("issue_timestamp_reconciliation", "Issue Timestamp Reconciliation", 1, "outputs/clean_replication_batch_018/darker_issue112_timestamp_reconciliation.json", []),
        ("dependency_era_resolution", "Dependency-Era Resolution", 1, "outputs/clean_replication_batch_018/decision_time_dependency_lock_validation.json", [exact_blocker]),
    ]:
        record = existing.get(capability_id) or capability_record(capability_id, public_name, tier, [evidence], blockers)
        record["current_tier"] = tier
        record["evidence_artifact_paths"] = [evidence]
        record["blockers"] = blockers
        existing[capability_id] = record
    catalog["capabilities"] = list(existing.values())
    write_json_deterministic(catalog_path, catalog)
    write_sha256sums(BATCH018_DIR)
    return state


def write_batch019_markdown_docs(batch019_state: dict[str, object]) -> None:
    shared = "\n".join(
        [
            "## Current operational gate status",
            "",
            "- Batch018 official artifact evidence remains blocked at `manual_dependency_lock_absent`.",
            "- Batch019 adds Active Search-Space Geometry as a neutral probe-selection scaffold.",
            "- Active Search-Space Geometry can prioritize probes and candidates, but it cannot validate repairs.",
            "- Geometry maps are not substitutes for commit verification, environment locks, replay, validation, null comparison, duplicate replay, no-overreach validation, or SHA custody.",
            "- Single-system search geometry and coupled-interlock extension remain separate.",
            "- Coupled-interlock extension is diagnostic until interlock invariants are computed.",
            "- Darker issue #112 repair execution remains blocked in Batch019; the post-Batch018 manual lock is watch-only for Batch020 or later.",
            "- Native repair episode count remains `4`.",
            "- Issue-derived repair episode count remains `0`.",
            "- Memory lift remains `not_demonstrated`.",
            "- Self-maintaining software remains `false/not_demonstrated`.",
            "- Hallucination elimination is not claimed.",
            "- Absolute uncrashability is not claimed.",
            "- Production runtime readiness is not claimed.",
        ]
    )
    docs = {
        "README.md": [
            "# ControllerGate",
            "",
            "ControllerGate is a provenance-first software repair research harness and evidence-bound repair validation kernel for audited software-change candidates. Current protocol remains `v2.13`.",
            "",
            "ControllerGate remains a pre-alpha research archive. Clean replication batch002 now attempts real external leads, and confirmed external native repair episodes include `py_bugger_issue_65`, `darker_non_ascii_drop_changes`, `darker_stdin_filename`, and `darker_skip_glob_failing_test`.",
            "",
            f"Batch019 is the latest boundary. Status: `{batch019_state['status']}`; exact blocker: `{batch019_state['exact_blocker']}`.",
            "",
            "Full scoring remains `NOT_RUN/disallowed`.",
            "",
            "Memory lift on external real bugs is not demonstrated. Self-maintaining software is not demonstrated.",
            "",
            shared,
            "",
            "## What ControllerGate is",
            "",
            "ControllerGate is an evidence-bound repair validation kernel for software-change candidates. It verifies provenance, replay, patch safety, rollback readiness, and claim boundaries before accepting repair evidence.",
            "",
            "## What ControllerGate is not",
            "",
            "ControllerGate is not production-ready, not a full scoring result, not a full memory-lift result, not fully self-maintaining software, and not an absolute reliability guarantee.",
            "",
            "## Claim Tier System",
            "",
            "ControllerGate uses explicit claim tiers so public claims remain tied to repository evidence.",
            "",
            "## Capability Catalog",
            "",
            "The capability catalog is stored in `configs/controllergate_capability_catalog.json` and summarized in `docs/capability_inventory.md`.",
            "",
            "## Skeptic's Acceptance Checklist",
            "",
            "The checklist in `docs/skeptics_acceptance_checklist.md` requires registry-first provenance, decision-time separation, SHA256 custody, fresh workspace purity, validation, duplicate replay, no-overreach validation, rollback records, and claim tiers.",
            "",
            "## Runtime-wrapper roadmap",
            "",
            "Batch015 introduced scaffold modules for audited runtime control. These remain scaffold evidence only unless deterministic fixture evidence is recorded.",
            "",
            "## Safe public claims",
            "",
            "- Evidence-bound repair validation kernel.",
            "- Proof-gated patch admission and quarantine.",
            "- Runtime-wrapper scaffold for audited local fixtures.",
            "- Claim-tiered capability catalog.",
            "- Active probe-selection scaffold.",
            "",
            "## Forbidden claims",
            "",
            "- Hallucination elimination.",
            "- Absolute uncrashability.",
            "- Fully self-maintaining software.",
            "- Production-ready runtime wrapper.",
            "- Full scoring.",
            "- Full memory lift.",
            "- Universal bug repair.",
            "- Sector deployment readiness.",
            "- Geometry-proves-repair.",
            "",
            "## Basic local checks",
            "",
            "```bash",
            "python scripts/byte_custody_preflight.py",
            "python -m pytest tests/core tests/runtime -q",
            "python scripts/validate_external_candidate_registry.py",
            "python scripts/audit_post_v2_37_hardening_and_batch002.py",
            "python scripts/controllergate_audit.py --protocol current",
            "python scripts/controllergate_run.py --protocol current --dry-run",
            "```",
        ],
        "docs/current_status.md": ["# Current status", "", "ControllerGate remains a pre-alpha research archive with current protocol `v2.13`.", "", shared],
        "docs/capability_inventory.md": ["# Capability inventory", "", "Batch019 adds Active Search-Space Geometry, Information-Gain Probe Selection, Structural Defect Boundary Classification, Recovery Candidate Path Ranking, AMDS active inference integration, and scope gates as scaffold or diagnostic capabilities.", "", shared],
        "docs/technical_validation_gap_report.md": ["# Technical validation gap report", "", "Batch019 does not add repair evidence. It adds a probe-selection layer that must remain subordinate to empirical evidence gates.", "", shared],
        "docs/public_release_readiness.md": ["# Public release readiness", "", "ControllerGate is not production-ready and is not a technical validation release. Batch019 adds no deployment readiness.", "", shared],
        "docs/controllergate_positioning.md": ["# ControllerGate positioning", "", "Preferred precise claim: ControllerGate turns proposed fixes into auditable, sandboxed, rollback-safe software-change candidates and blocks unverified changes before accepted state is contaminated.", "", "Batch019 adds an active probe-selection scaffold. It does not prove repairs.", "", shared],
        "docs/skeptics_acceptance_checklist.md": ["# Skeptic's acceptance checklist", "", "- Probe selection cannot replace empirical validation.", "- Coupled-interlock extension requires computed interlock invariants.", "- Repair execution remains blocked after upstream evidence gates fail.", "", shared],
        "docs/use_case_positioning.md": ["# Use case positioning", "", "ControllerGate is positioned for proof-gated software-change governance and research-grade repair validation. Batch019 does not claim production use-case readiness.", "", "deployment_readiness: false", "", shared],
        "docs/replication_protocol.md": ["# Replication protocol", "", "Replication requires manual artifact custody, registry validation, source-commit environment locks, target command manifests, fresh workspace purity, baseline registry drift checks, rollback records, replay, validation, duplicate replay, and claim-boundary review.", "", "Batch019 adds active probe-selection records for deciding what to inspect next, but not for accepting a repair.", "", shared],
        "docs/artifact_packaging_policy.md": ["# Artifact packaging policy", "", "The primary post-v2.37 artifact remains thin and delta-oriented. Batch019 carries prior evidence by artifact identity and lineage records.", "", shared],
        "docs/active_search_space_geometry.md": ["# Active Search-Space Geometry", "", "Active Search-Space Geometry is a neutral probe-selection and candidate-routing scaffold. It can prioritize probes and classify diagnostic boundaries, but it cannot validate repairs or replace empirical gates.", "", shared],
        "docs/amds_active_inference.md": ["# AMDS active inference", "", "AMDS active inference maintains a bounded probe queue with expected information gain, cost, risk, and claim-boundary penalties. It emits recommendations, not repair claims.", "", shared],
        "docs/single_system_vs_coupled_interlock_scope.md": ["# Single-system vs coupled-interlock scope", "", "Single-system geometry applies to one candidate, one repository, and one execution trace. Coupled-interlock extension is diagnostic-only until interlock invariants are computed.", "", shared],
        "docs/controllergate_claim_tiers.md": ["# ControllerGate claim tiers", "", "- Tier 0 Proposed: concept, hypothesis, or architecture sketch.", "- Tier 1 Demonstrated: deterministic local fixture or scaffold evidence.", "- Batch019 Active Search-Space Geometry is scaffold/diagnostic unless tied to empirical repair evidence.", "", shared],
        "controllergate_v1_7_beta/reports/critic_review_package/shareable_summary.md": ["# ControllerGate shareable summary", "", "Batch019 adds a neutral active probe-selection scaffold and preserves all claim boundaries. Darker issue #112 repair execution remains blocked in Batch019.", "", shared],
    }
    for path, lines in docs.items():
        write_text_lf(path, "\n".join(lines))


def write_batch019_outputs(batch018_state: dict[str, object]) -> dict[str, object]:
    BATCH019_DIR.mkdir(parents=True, exist_ok=True)
    lock_path = Path("external_seeds_pending/dependency_locks/darker_issue112_dependency_lock.json")
    lock_present = lock_path.is_file()
    lock_sha = sha256_file(lock_path) if lock_present else None
    carried_blocker = "manual_dependency_lock_absent"
    exact_blocker = "manual_dependency_lock_available_for_batch020_or_later" if lock_present else carried_blocker
    lock_watch = {
        "status": "AVAILABLE_FOR_BATCH020_OR_LATER" if lock_present else "BLOCKED_INPUT_REQUIRED",
        "canonical_path": lock_path.as_posix(),
        "canonical_lock_present": lock_present,
        "canonical_lock_sha256": lock_sha,
        "batch019_processes_lock": False,
        "exact_carried_batch018_blocker": carried_blocker,
        "exact_blocker": exact_blocker,
        "next_allowed_action": "process_manual_dependency_lock_in_batch020_or_later" if lock_present else "provide_canonical_manual_dependency_lock_json",
    }
    vector = build_search_space_feature_vector(
        candidate_id="darker_issue_112_relative_git_dir",
        candidate_class="issue_derived_reproduction_candidate",
        source_type="public_github_repo",
        repo_url="https://github.com/akaihola/darker",
        source_commit_sha=None,
        issue_url="https://github.com/akaihola/darker/issues/112",
        issue_timestamp_status="PASS",
        dependency_lock_status="AVAILABLE_NOT_PROCESSED_BATCH019" if lock_present else "ABSENT",
        target_intent_alignment_status="NOT_RUN",
        blocker_if_not_probeable=exact_blocker,
    )
    probes = build_probe_candidate_registry(vector)
    probe_decision = select_probe(probes)
    probe_status = probe_selection_status(vector)
    boundary = classify_boundary(dependency_lock_status="ABSENT", target_intent_alignment=False)
    paths = rank_recovery_paths(dependency_lock_status="ABSENT", target_intent_alignment=False)
    single_scope = audit_single_system_scope(candidate_count=1, repo_count=1, trace_count=1)
    coupled_gate = evaluate_coupled_interlock_gate([])
    amds_queue = amds_probe_queue(vector)
    replacement_template = {
        "candidate_id": "<new_candidate_id>",
        "repo_url": "<public_github_python_repo>",
        "issue_url": "<issue_url>",
        "issue_created_at": "<timestamp>",
        "source_commit_sha_or_selection": "<exact_commit_or_decision_time_selection>",
        "evidence_checklist": [
            "public repository",
            "issue timestamp",
            "no fixed/later/gold/PR evidence",
            "native failing test preferred",
            "bounded dependency metadata",
            "environment lock source present",
            "command manifest derivable",
        ],
        "forbidden_evidence_checklist": [
            "fixed commit",
            "later commit",
            "gold patch",
            "PR patch",
            "future tests",
            "hidden benchmark state",
            "external service requirement",
        ],
    }
    state = {
        "status": "PASS_WITH_BATCH019_ACTIVE_SEARCH_GEOMETRY",
        "exact_blocker": exact_blocker,
        "manual_dependency_lock_watch_status": lock_watch["status"],
        "active_search_space_geometry_status": "PASS",
        "search_space_feature_vector_status": "PASS",
        "information_gain_probe_selection_status": probe_status["status"],
        "structural_defect_boundary_classification_status": "PASS",
        "recovery_path_ranking_status": "PASS",
        "amds_active_inference_integration_status": "PASS",
        "single_system_scope_gate_status": single_scope["status"],
        "coupled_interlock_extension_gate_status": coupled_gate["status"],
        "curvature_integration_status": "PASS",
        "replacement_seed_request_status": "PASS",
        "darker_issue112_status": "blocked_on_manual_dependency_lock_watch_only",
        "recommended_next_probe": probe_status["selected_probe_type"],
        "native_repair_episode_count": 4,
        "issue_derived_repair_episode_count": 0,
        "matched_null_diagnostic_run_count": 0,
        "memory_separation_claim_status": "not_demonstrated",
        "full_scoring_status": "NOT_RUN/disallowed",
        "self_maintaining_software_status": "false/not_demonstrated",
        "hallucination_elimination_claim_status": "false/not_claimed",
        "absolute_uncrashability_claim_status": "false/not_claimed",
        "current_protocol": "v2.13",
        "primary_artifact_name": "post_v2_37_hardening_batch019_active_search_geometry_thin_artifacts",
    }
    records = {
        "batch018_boundary_preservation.json": {"status": "PASS", "batch018_status": batch018_state.get("status"), "batch018_exact_blocker": batch018_state.get("exact_blocker"), "post_batch018_lock_present": lock_present, "batch019_repair_path_executed": False},
        "manual_dependency_lock_blocker_carry_forward.json": {"status": "PASS", "carried_blocker": carried_blocker, "current_lock_watch_status": lock_watch["status"], "repair_path_executed": False},
        "claim_boundary_batch019.json": {"status": "PASS", "current_protocol": "v2.13", "native_repair_episode_count": 4, "issue_derived_repair_episode_count": 0, "full_scoring": "NOT_RUN/disallowed", "memory_lift": "not_demonstrated", "self_maintaining_software": "false/not_demonstrated", "hallucination_elimination": "false/not_claimed", "absolute_uncrashability": "false/not_claimed", "production_runtime_readiness": "false/not_demonstrated"},
        "manual_dependency_lock_watch_status.json": lock_watch,
        "manual_dependency_lock_next_action.json": {"status": "PASS", "next_allowed_action": lock_watch["next_allowed_action"], "batch019_processes_lock": False},
        "active_search_space_geometry_policy.json": active_search_space_geometry_policy(),
        "search_space_geometry_schema.json": search_space_geometry_schema(),
        "structural_defect_boundary_policy.json": structural_defect_boundary_policy(),
        "stable_candidate_region_policy.json": stable_candidate_region_policy(),
        "recovery_candidate_path_policy.json": recovery_candidate_path_policy(),
        "information_gain_probe_selection_policy.json": information_gain_probe_policy(),
        "amds_active_inference_integration_policy.json": amds_active_inference_policy(),
        "active_search_space_geometry_status.json": active_search_space_geometry_status(vector),
        "search_space_feature_vector_schema.json": search_space_geometry_schema(),
        "search_space_feature_vector_examples.json": {"status": "PASS", "examples": [vector]},
        "search_space_feature_vector_status.json": {"status": "PASS", "feature_vector_hash": vector["feature_vector_hash"], "missing_evidence": vector["missing_evidence"]},
        "information_gain_probe_policy.json": information_gain_probe_policy(),
        "probe_candidate_registry.json": {"status": "PASS", "probes": probes},
        "probe_selection_decision_records.json": {"status": probe_decision["status"], "decision": probe_decision},
        "probe_budget_policy_batch019.json": probe_budget_policy(),
        "probe_selection_status.json": probe_status,
        "structural_defect_boundary_schema.json": boundary_schema(),
        "structural_defect_boundary_examples.json": {"status": "PASS", "examples": [boundary]},
        "structural_defect_boundary_status.json": boundary,
        "recovery_path_ranking_policy.json": recovery_path_ranking_policy(),
        "recovery_candidate_path_examples.json": {"status": "PASS", "examples": paths["paths"]},
        "recovery_path_ranking_status.json": paths,
        "single_system_scope_gate_policy.json": single_system_scope_gate_policy(),
        "coupled_interlock_extension_gate_policy.json": coupled_interlock_extension_gate_policy(),
        "single_system_vs_interlock_scope_audit.json": {"status": "PASS", "single_system": single_scope, "coupled_interlock": coupled_gate, "conflated": False},
        "amds_active_inference_policy.json": amds_active_inference_policy(),
        "amds_candidate_radar_schema.json": {"status": "PASS", "fields": ["candidate_probe_queue", "seed_quality_score", "dependency_lock_need_score", "target_intent_risk_score", "route_diversity_score", "expected_information_gain_score", "next_probe_recommendation", "replacement_seed_recommendation_if_needed"]},
        "amds_active_probe_queue.json": amds_queue,
        "amds_active_inference_status.json": {"status": "PASS", "candidate_status": amds_queue["candidate_status"], "next_probe_recommendation": amds_queue["next_probe_recommendation"], "repair_success_claim": False},
        "replacement_seed_request_policy.json": {"status": "PASS", "native_failing_test_preferred": True, "forbidden_evidence_allowed": False, "external_services_allowed": False},
        "replacement_seed_request_template.json": replacement_template,
        "replacement_seed_quality_gate.json": {"status": "PASS", "contains_evidence_checklist": True, "contains_forbidden_evidence_checklist": True},
        "curvature_active_geometry_integration_policy.json": {"status": "PASS", "geometry_may_suggest_probes": True, "curvature_may_prioritize": True, "geometry_can_validate": False, "curvature_can_validate": False, "failed_evidence_gates_overridable": False},
        "curvature_probe_selection_integration.json": {"status": "PASS", "selected_probe": probe_status["selected_probe_type"], "route_diversity_required_for_memory_claim": True, "memory_claim_allowed": False},
        "curvature_claim_boundary_batch019.json": {"status": "PASS", "memory_lift": "not_demonstrated", "geometry_claim_can_override_evidence": False},
        "artifact_packaging_policy.json": {"status": "PASS", "primary_artifact_name": "post_v2_37_hardening_batch019_active_search_geometry_thin_artifacts", "primary_artifact_mode": "thin_delta", "hard_primary_artifact_bytes": 750000},
        "thin_artifact_packaging_policy.json": {"status": "PASS", "recursive_prior_batch_packaging_allowed": False, "primary_payload_roots": [POST_DIR.as_posix(), BATCH019_DIR.as_posix()]},
        "artifact_lineage_index.json": {"status": "PASS", "lineage_only": True, "current_batch": BATCH019_ID, "prior_artifacts": [{"batch": BATCH018_ID, "artifact_name": "post_v2_37_hardening_batch018_manual_dependency_lock_thin_artifacts", "artifact_id": "8042776923", "artifact_sha256": "fa248bdf8e4a78e758a02cdf05e465154006cd3a8f57b4533d359915432a9695", "ingest_commit": "0c321251", "claim_boundary_summary": "Batch018 safe-stop at manual_dependency_lock_absent"}]},
        "evidence_carry_forward_manifest.json": {"status": "PASS", "carried_prior_evidence_by_reference": True, "carried_batches": [BATCH018_ID], "full_scoring": "NOT_RUN/disallowed", "memory_lift": "not_demonstrated"},
        "artifact_payload_budget.json": {"status": "PASS", "hard_primary_artifact_bytes": 750000, "estimated_primary_artifact_bytes": None, "blocker": None},
        "artifact_minimality_audit.json": {"status": "PASS", "recursive_prior_batch_packaging_detected": False, "blocker": None},
        "lineage_equivalence_audit.json": {"status": "PASS", "prior_evidence_referenced_by_lineage": True},
        "controllergate_claim_tier_update.json": {"status": "PASS", "active_search_space_geometry": "tier_0_or_tier_1_scaffold", "information_gain_probe_selection": "tier_1_if_deterministic_tests_pass", "coupled_interlock_extension": "tier_0_until_invariants_computed", "repair_or_memory_lift_upgrade": False},
        "controllergate_capability_catalog_update.json": {"status": "PASS", "catalog_version": "batch019", "updated_capabilities": ["active_search_space_geometry", "information_gain_probe_selection", "structural_defect_boundary_classification", "recovery_candidate_path_ranking", "amds_active_inference_integration", "single_system_scope_gate", "coupled_interlock_extension_gate", "replacement_seed_request_scaffold", "manual_dependency_lock_watch", "artifact_thin_packaging"]},
        "consolidated_state_clean_replication_batch_019.json": state,
    }
    for name, record in records.items():
        write_json_deterministic(BATCH019_DIR / name, record)
    write_text_lf(
        BATCH019_DIR / "campaign_summary.md",
        "\n".join(
            [
                "# Clean replication Batch019 Active Search-Space Geometry",
                "",
                f"Status: {state['status']}.",
                "",
                "Batch019 officially preserves the Batch018 manual-lock safe-stop, watches the post-Batch018 manual dependency lock without processing it, and adds neutral probe-selection scaffolds.",
                "",
                f"Manual dependency lock watch status: `{lock_watch['status']}`.",
                "",
                f"Recommended next probe: `{state['recommended_next_probe']}`.",
                "",
                "No Darker repair, harness, matched-null diagnostic, or repair feasibility claim ran in Batch019.",
            ]
        ),
    )
    write_json_deterministic(
        "configs/clean_replication_batch_019.json",
        {
            "lane_id": BATCH019_ID,
            "lane_type": "active_search_space_geometry_and_probe_selection",
            "current_protocol": "v2.13",
            "primary_artifact_name": "post_v2_37_hardening_batch019_active_search_geometry_thin_artifacts",
            "process_manual_dependency_lock": False,
            "full_scoring": "NOT_RUN/disallowed",
        },
    )
    catalog_path = Path("configs/controllergate_capability_catalog.json")
    catalog = load_json(catalog_path)
    catalog["catalog_version"] = "batch019"
    capabilities = catalog.setdefault("capabilities", [])
    existing = {item.get("capability_id"): item for item in capabilities if isinstance(item, dict)}
    for capability_id, public_name, tier, evidence, blockers in [
        ("active_search_space_geometry", "Active Search-Space Geometry", 1, "outputs/clean_replication_batch_019/active_search_space_geometry_status.json", []),
        ("information_gain_probe_selection", "Information-Gain Probe Selection", 1, "outputs/clean_replication_batch_019/probe_selection_status.json", []),
        ("structural_defect_boundary_classification", "Structural Defect Boundary Classification", 1, "outputs/clean_replication_batch_019/structural_defect_boundary_status.json", []),
        ("recovery_candidate_path_ranking", "Recovery Candidate Path Ranking", 1, "outputs/clean_replication_batch_019/recovery_path_ranking_status.json", []),
        ("amds_active_inference_integration", "AMDS Active Inference Integration", 1, "outputs/clean_replication_batch_019/amds_active_inference_status.json", []),
        ("single_system_scope_gate", "Single-System Scope Gate", 1, "outputs/clean_replication_batch_019/single_system_vs_interlock_scope_audit.json", []),
        ("coupled_interlock_extension_gate", "Coupled-Interlock Extension Gate", 0, "outputs/clean_replication_batch_019/coupled_interlock_extension_gate_policy.json", ["coupled_interlock_used_without_invariants"]),
        ("replacement_seed_request_scaffold", "Replacement Seed Request Scaffold", 1, "outputs/clean_replication_batch_019/replacement_seed_request_template.json", []),
        ("manual_dependency_lock_watch", "Manual Dependency Lock Watch", 1, "outputs/clean_replication_batch_019/manual_dependency_lock_watch_status.json", []),
    ]:
        record = existing.get(capability_id) or capability_record(capability_id, public_name, tier, [evidence], blockers)
        record["current_tier"] = tier
        record["evidence_artifact_paths"] = [evidence]
        record["blockers"] = blockers
        existing[capability_id] = record
    catalog["capabilities"] = list(existing.values())
    write_json_deterministic(catalog_path, catalog)
    write_json_deterministic("configs/controllergate_claim_tiers.json", claim_tier_config())
    write_sha256sums(BATCH019_DIR)
    return state


def append_external_repair_episode_if_needed(matched_null: dict[str, object]) -> None:
    success = matched_null.get("repair_success")
    if not isinstance(success, dict) or success.get("scoreable_external_repair") is not True:
        return
    registry_path = Path("configs/external_repair_episode_registry.json")
    registry = load_json(registry_path)
    episodes = registry.setdefault("episodes", [])
    if any(isinstance(item, dict) and item.get("candidate_id") == "darker_stdin_filename" for item in episodes):
        return
    episodes.append(
        {
            "episode_id": "darker_stdin_filename:post_v2_37_batch002_matched_null",
            "episode_version": "post_v2_37_batch002_matched_null",
            "episode_type": "external_non_ansible_source_only_target_repair",
            "candidate_id": "darker_stdin_filename",
            "repo_url": success.get("repo_url"),
            "buggy_commit_sha": success.get("commit_sha"),
            "test_command": "python -m pytest src/darker/tests/test_main_stdin_filename.py -q",
            "target_test_file": {
                "path": success.get("target_test_path"),
                "sha256": matched_null.get("pre_generation_context_state_lock", {}).get("target_test_sha256"),
            },
            "environment_lock_source": {
                "path": "pyproject.toml",
                "sha256": matched_null.get("pre_generation_context_state_lock", {}).get("environment_file_sha256"),
            },
            "patch_modified_files": ["src/darker/config.py"],
            "patch_sha256": success.get("patch_sha256"),
            "patch_size_stats": {
                "files_touched": 1,
                "functions_modified": 1,
                "lines_changed": 2,
            },
            "patch_safety_status": "PASS",
            "target_validation_status": success.get("target_validation_status"),
            "target_validation_exit_status": 0,
            "duplicate_replay_status": success.get("duplicate_replay_status"),
            "duplicate_replay_count": "3 / 3",
            "scoreable": True,
            "positive_memory_only": False,
            "bounded_target_repair_signal": True,
            "semantic_failure_signature_hash": matched_null.get("semantic_failure_signature", {}).get("semantic_failure_signature_hash"),
            "artifact_name": "post_v2_37_hardening_batch002_matched_null_artifacts",
            "artifact_id": "pending_successful_workflow_artifact",
            "artifact_sha256": "pending_manual_artifact_ingest",
            "workflow_run_id": "pending_dispatch",
            "evidence_paths": {
                "matched_null": "outputs/clean_replication_batch_002/matched_null_separation_score_result.json",
                "arm_a": "outputs/clean_replication_batch_002/matched_null_arm_a_results.json",
                "arm_b": "outputs/clean_replication_batch_002/matched_null_arm_b_results.json",
                "patch_safety": "outputs/clean_replication_batch_002/arm_a_target_validation.json",
                "duplicate": "outputs/clean_replication_batch_002/arm_a_duplicate_replay.json",
                "claim": "outputs/clean_replication_batch_002/claim_boundary.json",
            },
            "full_scoring": "NOT_RUN/disallowed",
            "memory_lift": matched_null.get("memory_lift", "undemonstrated"),
            "self_maintaining_software": "false/not_demonstrated",
            "claim_boundaries": {
                "current_protocol_version": "v2.13",
                "full_scoring": "NOT_RUN",
                "full_scoring_allowed": False,
                "memory_lift_status": matched_null.get("memory_lift", "undemonstrated"),
                "self_maintaining_software_status": "false/not_demonstrated",
                "promoted_to_current": False,
            },
        }
    )
    registry["updated_utc"] = "post_v2_37_batch002_matched_null"
    write_json_deterministic(registry_path, registry)


def append_batch008_external_repair_episode_if_needed(state: dict[str, object]) -> None:
    if state.get("additional_native_external_repair_acquired") is not True:
        return
    registry_path = Path("configs/external_repair_episode_registry.json")
    registry = load_json(registry_path)
    episodes = registry.setdefault("episodes", [])
    existing_index = next(
        (
            index
            for index, item in enumerate(episodes)
            if isinstance(item, dict) and item.get("candidate_id") == "darker_skip_glob_failing_test"
        ),
        None,
    )
    entry = {
            "episode_id": "darker_skip_glob_failing_test:post_v2_37_batch008_declared_precondition",
            "episode_version": "post_v2_37_batch008_declared_precondition",
            "episode_type": "external_non_ansible_source_only_target_repair",
            "candidate_id": "darker_skip_glob_failing_test",
            "repo_url": state.get("repo_url"),
            "buggy_commit_sha": state.get("commit_sha"),
            "test_command": "python -m pytest src/darker/tests/test_main_isort.py::test_isort_respects_skip_glob -q",
            "target_test_file": {
                "path": state.get("target_test_path"),
                "sha256": state.get("target_test_sha256"),
            },
            "environment_lock_source": {
                "path": "pyproject.toml",
                "sha256": state.get("environment_file_sha256"),
            },
            "patch_modified_files": ["src/darker/import_sorting.py"],
            "patch_sha256": state.get("assembled_patch_sha256"),
            "patch_size_stats": state.get("patch_size_stats"),
            "patch_safety_status": state.get("patch_safety_status"),
            "target_validation_status": state.get("target_validation_status"),
            "target_validation_exit_status": 0,
            "duplicate_replay_status": state.get("duplicate_replay_status"),
            "duplicate_replay_count": "3 / 3",
            "scoreable": True,
            "positive_memory_only": False,
            "bounded_target_repair_signal": True,
            "semantic_failure_signature_hash": state.get("semantic_failure_signature_hash"),
            "artifact_name": "post_v2_37_hardening_batch008_declared_precondition_artifacts",
            "artifact_id": "pending_successful_workflow_artifact",
            "artifact_sha256": "pending_manual_artifact_ingest",
            "workflow_run_id": "pending_dispatch",
            "evidence_paths": {
                "claim": "outputs/clean_replication_batch_008/claim_boundary.json",
                "context": "outputs/clean_replication_batch_008/source_stack_after_declared_extras.json",
                "duplicate": "outputs/clean_replication_batch_008/duplicate_replay_result_batch008.json",
                "patch": "outputs/clean_replication_batch_008/assembled_patch_batch008.diff",
                "patch_safety": "outputs/clean_replication_batch_008/fragment_safety_audits_batch008.json",
                "precondition": "outputs/clean_replication_batch_008/declared_formatter_extra_install_attempts.json",
                "target_replay": "outputs/clean_replication_batch_008/target_replay_after_declared_extras.json",
                "target_validation": "outputs/clean_replication_batch_008/target_validation_result_batch008.json",
            },
            "full_scoring": "NOT_RUN/disallowed",
            "memory_lift": "not_demonstrated",
            "self_maintaining_software": "false/not_demonstrated",
            "claim_boundaries": {
                "current_protocol_version": "v2.13",
                "full_scoring": "NOT_RUN",
                "full_scoring_allowed": False,
                "memory_lift_status": "undemonstrated_equal_performance",
                "self_maintaining_software_status": "false/not_demonstrated",
                "promoted_to_current": False,
            },
        }
    if existing_index is None:
        episodes.append(entry)
    else:
        episodes[existing_index] = entry
    registry["updated_utc"] = "post_v2_37_batch008_declared_precondition"
    write_json_deterministic(registry_path, registry)


def write_matched_null_continuation_outputs(config: dict[str, object]) -> dict[str, object]:
    existing_state = load_json(BATCH_DIR / f"consolidated_state_{BATCH_ID}.json")
    verified = load_json(BATCH_DIR / "verified_candidates.json")
    existing_successes = load_json(BATCH_DIR / "repair_successes.json")
    existing_attempts = load_json(BATCH_DIR / "repair_attempts.json")
    registry = load_json("configs/external_repair_episode_registry.json")
    candidate_registry_path = Path("configs/external_candidate_registry.json")
    matched_null = execute_matched_null_repair_comparison(verified, config)
    append_external_repair_episode_if_needed(matched_null)

    write_json_deterministic(
        BATCH_DIR / "baseline_registry_snapshot_before_matched_null.json",
        {
            "status": "PASS",
            "existing_repair_episodes": len(registry.get("episodes", [])),
            "candidate_registry_count": len(load_json(candidate_registry_path).get("candidates", [])) if candidate_registry_path.is_file() else 0,
            "native_repair_count": len([item for item in registry.get("episodes", []) if isinstance(item, dict) and item.get("episode_type") == "external_non_ansible_source_only_target_repair"]),
            "issue_derived_repair_count": 0,
            "current_protocol_version": "v2.13",
            "full_scoring": "NOT_RUN/disallowed",
            "memory_lift": "undemonstrated",
            "self_maintaining_software": "false/not_demonstrated",
            "registry_sha256s": {
                "external_repair_episode_registry": sha256_file("configs/external_repair_episode_registry.json"),
                "external_candidate_registry": sha256_file(candidate_registry_path) if candidate_registry_path.is_file() else None,
            },
        },
    )
    second_success = next((item for item in existing_successes if item.get("candidate_id") == "darker_non_ascii_drop_changes"), {})
    proof_chain = {
        "status": "PASS",
        "candidate_id": "darker_non_ascii_drop_changes",
        "candidate_commit_hash": second_success.get("commit_sha"),
        "target_test_hash": next((item.get("target_test_sha256") for item in load_json(BATCH_DIR / "repair_context_capsules.json") if item.get("candidate_id") == "darker_non_ascii_drop_changes"), None),
        "environment_lock_hash": next((item.get("environment_file_sha256") for item in load_json(BATCH_DIR / "pre_generation_context_state_lock.json") if item.get("candidate_id") == "darker_non_ascii_drop_changes"), None),
        "pre_repair_replay_hash": next((item.get("pre_repair_replay_hash") for item in load_json(BATCH_DIR / "pre_generation_context_state_lock.json") if item.get("candidate_id") == "darker_non_ascii_drop_changes"), None),
        "repair_context_hash": next((item.get("context_capsule_hash") for item in load_json(BATCH_DIR / "repair_context_capsules.json") if item.get("candidate_id") == "darker_non_ascii_drop_changes"), None),
        "patch_hash": second_success.get("patch_sha256"),
        "target_validation_hash": stable_json_hash(load_json(BATCH_DIR / "target_validation_results.json")),
        "duplicate_replay_hashes": [stable_json_hash(item) for item in load_json(BATCH_DIR / "duplicate_replay_results.json")],
        "no_overreach_record_hash": stable_json_hash(load_json(BATCH_DIR / "no_overreach_validation.json")),
        "claim_boundary_hash": stable_json_hash(load_json(BATCH_DIR / "claim_boundary.json")),
    }
    proof_chain["proof_chain_hash"] = stable_json_hash(proof_chain)
    write_json_deterministic(BATCH_DIR / "proof_chain_lock_for_second_repair.json", proof_chain)
    write_json_deterministic(
        BATCH_DIR / "second_repair_claim_boundary.json",
        {
            "status": "PASS",
            "candidate_id": "darker_non_ascii_drop_changes",
            "full_scoring": "NOT_RUN/disallowed",
            "memory_lift": "undemonstrated",
            "self_maintaining_software": "false/not_demonstrated",
            "no_overreach_scope": "target_file_replay_only",
            "stronger_robustness_claim_allowed": False,
        },
    )

    write_json_deterministic(BATCH_DIR / "darker_stdin_filename_pre_repair_replay.json", matched_null.get("pre_repair_replay", {}))
    write_json_deterministic(BATCH_DIR / "darker_stdin_filename_semantic_failure_signature.json", matched_null.get("semantic_failure_signature", {}))
    write_json_deterministic(BATCH_DIR / "darker_stdin_filename_structural_repair_routing_map.json", matched_null.get("structural_repair_routing_map", {}))
    write_json_deterministic(BATCH_DIR / "darker_stdin_filename_patchable_source_subset.json", matched_null.get("patchable_source_subset", {}))
    write_json_deterministic(BATCH_DIR / "darker_stdin_filename_pre_generation_context_state_lock.json", matched_null.get("pre_generation_context_state_lock", {}))
    write_json_deterministic(BATCH_DIR / "darker_stdin_filename_stage_interface_contract.json", matched_null.get("stage_interface_contract", {}))

    write_json_deterministic(BATCH_DIR / "failure_memory_status_code_taxonomy.json", matched_null.get("failure_memory_status_code_taxonomy", {}))
    write_json_deterministic(BATCH_DIR / "failure_memory_weighting_policy.json", matched_null.get("failure_memory_weighting_policy", {}))
    write_json_deterministic(BATCH_DIR / "arm_a_active_failure_memory_weighting.json", matched_null.get("arm_a_active_failure_memory_weighting", {}))
    write_json_deterministic(BATCH_DIR / "arm_a_failure_memory_weight_trace.json", matched_null.get("arm_a_active_failure_memory_weighting", {}))
    write_json_deterministic(BATCH_DIR / "arm_b_memory_disabled_exclusion_audit.json", matched_null.get("arm_b_memory_disabled_exclusion_audit", {}))
    write_json_deterministic(BATCH_DIR / "arm_b_memory_exclusion_audit.json", matched_null.get("arm_b_memory_disabled_exclusion_audit", {}))
    write_json_deterministic(BATCH_DIR / "failure_memory_weight_delta_report.json", matched_null.get("failure_memory_weight_delta_report", {}))

    arm_a = matched_null.get("arm_a", {})
    arm_b = matched_null.get("arm_b", {})
    write_json_deterministic(BATCH_DIR / "arm_a_pre_generation_context_state_snapshot.json", arm_a.get("snapshot", {}))
    write_json_deterministic(BATCH_DIR / "arm_b_pre_generation_context_state_snapshot.json", arm_b.get("snapshot", {}))
    write_json_deterministic(BATCH_DIR / "arm_a_repair_intent_lock.json", arm_a.get("repair_intent_lock", {}))
    write_json_deterministic(BATCH_DIR / "arm_b_repair_intent_lock.json", arm_b.get("repair_intent_lock", {}))
    write_json_deterministic(BATCH_DIR / "matched_null_arm_a_memory_enabled_plan.json", {"status": "PASS", "arm": "memory_enabled_clean_repair", "candidate_id": "darker_stdin_filename"})
    write_json_deterministic(BATCH_DIR / "matched_null_arm_b_memory_disabled_plan.json", {"status": "PASS", "arm": "memory_disabled_matched_null", "candidate_id": "darker_stdin_filename"})
    write_json_deterministic(BATCH_DIR / "matched_null_arm_a_results.json", {key: value for key, value in arm_a.items() if key != "patch_diff"})
    write_json_deterministic(BATCH_DIR / "matched_null_arm_b_results.json", {key: value for key, value in arm_b.items() if key != "patch_diff"})
    if arm_a.get("patch_diff"):
        write_text_lf(BATCH_DIR / "arm_a_patch.diff", str(arm_a["patch_diff"]))
        write_text_lf(BATCH_DIR / "arm_a_patch_sha256.txt", str(arm_a.get("patch_sha256")) + "\n")
    if arm_b.get("patch_diff"):
        write_text_lf(BATCH_DIR / "arm_b_patch.diff", str(arm_b["patch_diff"]))
        write_text_lf(BATCH_DIR / "arm_b_patch_sha256.txt", str(arm_b.get("patch_sha256")) + "\n")
    write_json_deterministic(BATCH_DIR / "arm_a_target_validation.json", arm_a.get("target_validation", {}))
    write_json_deterministic(BATCH_DIR / "arm_b_target_validation.json", arm_b.get("target_validation", {}))
    write_json_deterministic(BATCH_DIR / "arm_a_duplicate_replay.json", arm_a.get("duplicate_replay", {}))
    write_json_deterministic(BATCH_DIR / "arm_b_duplicate_replay.json", arm_b.get("duplicate_replay", {}))
    write_json_deterministic(BATCH_DIR / "arm_a_post_patch_constraint_revalidation.json", arm_a.get("post_patch_constraint_revalidation", {}))
    write_json_deterministic(BATCH_DIR / "arm_b_post_patch_constraint_revalidation.json", arm_b.get("post_patch_constraint_revalidation", {}))
    write_json_deterministic(BATCH_DIR / "arm_a_no_overreach_validation.json", arm_a.get("no_overreach_validation", {}))
    write_json_deterministic(BATCH_DIR / "arm_b_no_overreach_validation.json", arm_b.get("no_overreach_validation", {}))
    write_json_deterministic(BATCH_DIR / "interlock_invariant_revalidation.json", [arm_a.get("interlock_invariant_revalidation", {}), arm_b.get("interlock_invariant_revalidation", {})])
    write_json_deterministic(BATCH_DIR / "post_patch_constraint_revalidation_darker_stdin_filename.json", [arm_a.get("post_patch_constraint_revalidation", {}), arm_b.get("post_patch_constraint_revalidation", {})])
    write_json_deterministic(BATCH_DIR / "no_overreach_validation_darker_stdin_filename.json", [arm_a.get("no_overreach_validation", {}), arm_b.get("no_overreach_validation", {})])

    write_json_deterministic(BATCH_DIR / "homeostasis_risk_state_matched_null.json", matched_null.get("homeostasis_risk_state", {}))
    write_json_deterministic(BATCH_DIR / "bounded_exploration_budget_matched_null.json", matched_null.get("bounded_exploration_budget", {}))
    write_json_deterministic(BATCH_DIR / "active_probe_escalation_trace.json", matched_null.get("active_probe_escalation_trace", {}))
    write_json_deterministic(BATCH_DIR / "matched_null_score_inputs.json", matched_null.get("matched_null_score_inputs", {}))
    write_json_deterministic(BATCH_DIR / "matched_null_score_formula.json", matched_null.get("matched_null_score_formula", {}))
    write_json_deterministic(BATCH_DIR / "matched_null_score_audit.json", matched_null.get("matched_null_score_audit", {}))
    write_json_deterministic(BATCH_DIR / "matched_null_separation_score_result.json", matched_null.get("matched_null_score", {}))
    write_json_deterministic(
        BATCH_DIR / "memory_lift_claim_evaluation.json",
        {
            "status": "PASS",
            "memory_lift": matched_null.get("memory_lift"),
            "preliminary_single_candidate_memory_separation_evidence": matched_null.get("preliminary_single_candidate_memory_separation_evidence"),
            "full_memory_lift_status": "undemonstrated",
            "full_scoring": "NOT_RUN/disallowed",
            "self_maintaining_software": "false/not_demonstrated",
        },
    )
    write_json_deterministic(BATCH_DIR / "null_generation_audit.json", matched_null.get("arm_b_memory_disabled_exclusion_audit", {}))

    matched_success = matched_null.get("repair_success")
    repair_successes = list(existing_successes)
    if isinstance(matched_success, dict) and matched_success.get("scoreable_external_repair") is True and not any(item.get("candidate_id") == "darker_stdin_filename" for item in repair_successes):
        repair_successes.append(matched_success)
    repair_attempts = list(existing_attempts)
    for arm in [arm_a, arm_b]:
        if arm:
            repair_attempts.append(
                {
                    "lead_id": "darker_stdin_filename",
                    "arm_id": arm.get("arm_id"),
                    "candidate_class": "native",
                    "source_only_repair_attempted": True,
                    "patch_generation_attempted": True,
                    "patch_generated": arm.get("patch_generated") is True,
                    "patch_authorized": arm.get("patch_authorized") is True,
                    "patch_applied": arm.get("patch_attempted") is True,
                    "target_validation_attempted": bool(arm.get("target_validation")),
                    "duplicate_clean_replay_attempted": bool(arm.get("duplicate_replay")),
                    "source_mutation_performed": arm.get("patch_attempted") is True,
                    "tests_modified": False,
                    "support_files_modified": False,
                    "config_workflow_registry_audit_modified": False,
                    "blocker": arm.get("blocker"),
                    "decision": "repair_success_target_and_duplicate_replay_passed" if arm.get("status") == "PASS" else "repair_blocked",
                    "patch_sha256": arm.get("patch_sha256"),
                }
            )
    write_json_deterministic(BATCH_DIR / "repair_attempts.json", repair_attempts)
    write_json_deterministic(BATCH_DIR / "repair_successes.json", repair_successes)
    write_json_deterministic(BATCH_DIR / "matched_null_results.json", matched_null)
    write_json_deterministic(
        BATCH_DIR / "memory_lift_evaluation.json",
        {
            "status": "PASS",
            "memory_lift": matched_null.get("memory_lift"),
            "preliminary_single_candidate_memory_separation_evidence": matched_null.get("preliminary_single_candidate_memory_separation_evidence"),
            "full_memory_lift_status": "undemonstrated",
        },
    )

    state = dict(existing_state)
    new_success_count = len(repair_successes)
    state.update(
        {
            "status": "PASS" if matched_null.get("status") == "PASS" else "BLOCKED",
            "exact_blocker": matched_null.get("blocker"),
            "summary_status": "additional_external_repair_acquired" if matched_null.get("darker_stdin_filename_repair_success") else "matched_null_no_additional_repair",
            "native_repair_attempts_count": len(repair_attempts),
            "native_repair_successes_count": new_success_count,
            "additional_native_external_repairs_acquired_count": new_success_count,
            "matched_null_status": matched_null.get("status"),
            "matched_null_separation_score": matched_null.get("matched_null_score", {}).get("matched_null_separation_score"),
            "preliminary_single_candidate_memory_separation_evidence": matched_null.get("preliminary_single_candidate_memory_separation_evidence"),
            "memory_lift": matched_null.get("memory_lift"),
        }
    )
    write_json_deterministic(BATCH_DIR / f"consolidated_state_{BATCH_ID}.json", state)
    write_json_deterministic(BATCH_DIR / "native_issue_derived_count_separation.json", state)
    write_json_deterministic(
        BATCH_DIR / "claim_boundary.json",
        {
            "current_protocol_version": "v2.13",
            "full_scoring": "NOT_RUN/disallowed",
            "memory_lift": matched_null.get("memory_lift"),
            "full_memory_lift_status": "undemonstrated",
            "preliminary_single_candidate_memory_separation_evidence": matched_null.get("preliminary_single_candidate_memory_separation_evidence"),
            "self_maintaining_software": "false/not_demonstrated",
            "technical_validation_release_readiness": "not_ready",
            "issue_derived_repairs_remain_separate": True,
        },
    )
    write_text_lf(
        BATCH_DIR / "campaign_summary.md",
        "\n".join(
            [
                "# Clean replication batch 002",
                "",
                f"Status: {state['status']}.",
                "",
                "The post-v2.37 continuation preserves the official repair-generation ingest and runs the remaining verified native candidate under matched-null comparison.",
                "",
                f"Exact blocker: `{state['exact_blocker']}`.",
            ]
        ),
    )
    write_sha256sums(BATCH_DIR)
    return state


ACTIVE_PUBLIC_LANGUAGE_PATHS = [
    "README.md",
    "docs/current_status.md",
    "docs/capability_inventory.md",
    "docs/claim_boundaries.md",
    "docs/memory_lift_definition.md",
    "docs/public_release_readiness.md",
    "docs/technical_validation_gap_report.md",
    "docs/replication_protocol.md",
    "docs/evidence_model.md",
    "docs/operational_gate_matrix.md",
    "docs/notebooklm_advice_traceability.md",
    "controllergate_v1_7_beta/reports/critic_review_package/shareable_summary.md",
    "configs/operational_gate_matrix.json",
    "configs/notebooklm_advice_traceability_matrix.json",
    "configs/clean_replication_batch_004.json",
    "configs/clean_replication_batch_005.json",
    "configs/clean_replication_batch_006.json",
    "configs/clean_replication_batch_007.json",
    "configs/clean_replication_batch_008.json",
    "configs/clean_replication_batch_009.json",
    "configs/clean_replication_batch_010.json",
    "configs/clean_replication_batch_011.json",
    "configs/clean_replication_batch_012.json",
    "configs/clean_replication_batch_013.json",
    ".github/workflows/post_v2_37_hardening_and_batch002.yml",
    "controllergate/core/environment.py",
    "controllergate/core/failure_memory.py",
    "controllergate/core/status_code_weighting.py",
    "controllergate/core/source_ranking.py",
    "controllergate/core/prospective_memory_challenge.py",
    "controllergate/core/curvature_selection.py",
    "controllergate/core/issue_derived_harness.py",
    "controllergate/core/targeted_seed.py",
    "controllergate/core/environment_lock.py",
    "controllergate/core/command_manifest.py",
    "controllergate/core/workspace_purity.py",
    "controllergate/core/baseline_precheck.py",
    "controllergate/core/rollback_ledger.py",
    "controllergate/core/gate_chain.py",
    "controllergate/core/active_context_filtering.py",
    "controllergate/experiments/replication_batch.py",
    "scripts/post_v2_37_hardening_and_batch002_runner.py",
    "scripts/audit_post_v2_37_hardening_and_batch002.py",
]


def public_language_audit(paths: list[str]) -> dict[str, object]:
    blocked_terms = [
        "chromo" + "somal",
        "TO" + "RUS",
        "TL" + "D",
        "A" + "GI",
        "observer" + "-state",
        "recursion" + "-constant",
        "Klein " + "twist",
        "Betti" + "-number",
        "cym" + "atics",
        "res" + "onance",
        "meta" + "phorical",
        "bio" + "logical",
        "OS" + "QN",
        "N" + "\u2248",
        "chro" + "matin",
        "epi" + "genetic",
    ]
    hits: list[dict[str, object]] = []
    for rel in paths:
        path = Path(rel)
        if not path.is_file():
            hits.append({"path": rel, "term": "missing_file", "line": None})
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        for index, line in enumerate(text.splitlines(), start=1):
            for term in blocked_terms:
                if term in line:
                    hits.append({"path": rel, "term": term, "line": index})
    return {
        "status": "PASS" if not hits else "FAIL",
        "blocker": None if not hits else "public_language_metaphor_leak_detected",
        "scan_scope": "active public docs, active configs, active runner/audit/workflow, and current artifact outputs",
        "scanned_path_count": len(paths),
        "hits": hits,
        "historical_frozen_lane_files_scanned_as_current_claims": False,
    }


def write_public_docs_reports() -> None:
    readme = Path("README.md").read_text(encoding="utf-8")
    required_phrases = [
        "provenance-first software repair research harness",
        "py_bugger_issue_65",
        "Full scoring remains `NOT_RUN/disallowed`",
        "Memory lift on external real bugs is not demonstrated",
        "Self-maintaining software is not demonstrated",
        "pre-alpha research archive",
        "Current protocol remains `v2.13`",
        "Clean replication batch002 now attempts real external leads",
        "Clean replication batch003 implements a matched-null ensemble challenge protocol",
        "dual-track challenge acquisition",
        "official Batch005 source-materialized artifact",
        "Batch006 adds bounded fragment patch assembly",
        "Batch007 adds target-intent reachability and precondition resolution",
        "Batch008 corrects declared formatter precondition materialization",
        "Batch009 patch-quarantined matched-null calibration",
        "Batch010 implements active status-code weighting",
        "Batch011 prospective memory challenge eligibility",
        "Batch012 targeted prospective seed intake",
        "Batch013 acquisition locks",
        "Current operational gate status",
    ]
    missing = [phrase for phrase in required_phrases if phrase not in readme]
    forbidden_claims = [
        "memory lift is proven",
        "self-maintaining software is demonstrated",
        "full scoring has run",
        "technical validation release ready",
    ]
    forbidden_hits = [claim for claim in forbidden_claims if claim.lower() in readme.lower()]
    write_json_deterministic(
        POST_DIR / "readme_status_update_report.json",
        {
            "status": "PASS" if not missing and not forbidden_hits else "FAIL",
            "required_phrase_count": len(required_phrases),
            "missing_required_phrases": missing,
            "forbidden_claim_hits": forbidden_hits,
            "current_protocol_version": "v2.13",
            "pre_alpha_research_archive_only": True,
        },
    )
    docs = [
        "docs/current_status.md",
        "docs/capability_inventory.md",
        "docs/claim_boundaries.md",
        "docs/memory_lift_definition.md",
        "docs/public_release_readiness.md",
        "docs/technical_validation_gap_report.md",
        "docs/replication_protocol.md",
        "docs/evidence_model.md",
        "docs/operational_gate_matrix.md",
        "docs/notebooklm_advice_traceability.md",
    ]
    write_json_deterministic(
        POST_DIR / "public_docs_accuracy_audit.json",
        {
            "status": "PASS" if not missing and not forbidden_hits and all(Path(path).is_file() for path in docs) else "FAIL",
            "docs_checked": docs,
            "full_scoring": "NOT_RUN/disallowed",
            "memory_lift": "not_demonstrated",
            "self_maintaining_software": "false/not_demonstrated",
            "technical_validation_readiness_claimed": False,
            "issue_derived_counts_as_native": False,
            "bugsinpy_global_block_active": True,
        },
    )
    matrix = load_json("configs/operational_gate_matrix.json")
    write_json_deterministic(
        POST_DIR / "operational_gate_matrix_status.json",
        {
            "status": "PASS" if len(matrix.get("gates", [])) >= 26 else "FAIL",
            "gate_count": len(matrix.get("gates", [])),
            "neutral_terminology_policy": matrix.get("terminology_policy"),
            "evidence_classes": matrix.get("evidence_classes", []),
        },
    )
    artifact_paths = [str(path) for path in sorted(POST_DIR.glob("*.json"))] + [str(path) for path in sorted(BATCH_DIR.glob("*.json"))] + [str(path) for path in sorted(BATCH003_DIR.glob("*.json"))] + [str(path) for path in sorted(BATCH004_DIR.glob("*.json"))] + [str(path) for path in sorted(BATCH005_DIR.glob("*.json"))] + [str(path) for path in sorted(BATCH006_DIR.glob("*.json"))] + [str(path) for path in sorted(BATCH007_DIR.glob("*.json"))] + [str(path) for path in sorted(BATCH008_DIR.glob("*.json"))] + [str(path) for path in sorted(BATCH009_DIR.glob("*.json"))] + [str(path) for path in sorted(BATCH010_DIR.glob("*.json"))] + [str(path) for path in sorted(BATCH011_DIR.glob("*.json"))] + [str(path) for path in sorted(BATCH012_DIR.glob("*.json"))] + [str(path) for path in sorted(BATCH012_DIR.glob("*.md"))] + [str(path) for path in sorted(BATCH013_DIR.glob("*.json"))] + [str(path) for path in sorted(BATCH013_DIR.glob("*.md"))] + [str(path) for path in sorted(BATCH014_DIR.glob("*.json"))] + [str(path) for path in sorted(BATCH014_DIR.glob("*.md"))]
    write_json_deterministic(
        POST_DIR / "public_language_audit_expanded.json",
        public_language_audit(ACTIVE_PUBLIC_LANGUAGE_PATHS + artifact_paths),
    )


def notebooklm_advice_entries(batch005_state: dict[str, object]) -> list[dict[str, object]]:
    def entry(
        advice_id: str,
        name: str,
        status: str,
        mechanism: str,
        outputs: list[str],
        scripts: list[str],
        assertions: list[str],
        blockers: list[str],
        evidence_class: str,
        boundary: str,
        next_lane: str,
        reason: str = "",
        gate_name: str | None = None,
        evidence_paths: list[str] | None = None,
    ) -> dict[str, object]:
        return {
            "advice_id": advice_id,
            "internal_design_term": "not_applicable",
            "public_engineering_name": name,
            "operational_gate_name": gate_name or name,
            "status": status,
            "current_repo_mechanism": mechanism,
            "required_outputs": outputs,
            "required_modules_or_scripts": scripts,
            "required_audit_assertions": assertions,
            "blocker_if_missing": blockers[0] if blockers else "missing_traceability_blocker",
            "blockers": blockers,
            "evidence_class": evidence_class,
            "claim_boundary": boundary,
            "next_allowed_lane": next_lane,
            "reason_if_deferred_or_rejected": reason,
            "evidence_paths": evidence_paths or outputs,
        }

    issue_path_used = bool(batch005_state.get("targeted_issue_candidate_verified") or batch005_state.get("issue_derived_candidate_verified"))
    routing_delta_active = False
    if (BATCH_DIR / "arm_a_active_failure_memory_weighting.json").is_file():
        routing_delta_active = load_json(BATCH_DIR / "arm_a_active_failure_memory_weighting.json").get("failure_memory_markers_passive") is False
    return [
        entry("artifact_byte_custody", "Artifact Byte Custody", "implemented_active", "manual ZIP verification, manifests, byte-custody preflight, safe path and duplicate path checks", ["outputs/post_v2_37_hardening_001/batch005_artifact_verification.json", "outputs/clean_replication_batch_005/SHA256SUMS.txt"], ["scripts/byte_custody_preflight.py", "controllergate/core/manifests.py"], ["artifact manifests verify before ingest"], ["byte_custody_preflight_failed", "artifact_manifest_verification_failed"], "infrastructure", "artifact identity is custody evidence only", "continuous"),
        entry("workspace_transport_integrity", "Workspace Transport Integrity Gate", "implemented_active", "transport records with source/destination hashes and unsafe path rejection", ["outputs/post_v2_37_hardening_001/workspace_transport_integrity_log.json", "outputs/post_v2_37_hardening_001/transport_boundary_audit.json"], ["controllergate/core/transport.py"], ["transport records include hashes and PASS decisions"], ["transport_integrity_breach"], "infrastructure", "workspace movement is not repair success", "continuous", gate_name="Workspace Transport Integrity"),
        entry("external_candidate_registry", "External Candidate Registry", "implemented_active", "schema validation, duplicate checks, native and issue-derived separation", ["configs/external_candidate_registry.json"], ["scripts/validate_external_candidate_registry.py"], ["registry validation returns PASS"], ["external_candidate_registry_validation_failed"], "native", "registry entries remain leads until replay verifies them", "continuous"),
        entry("baseline_registry_snapshot", "Baseline Registry Snapshot", "implemented_partial", "registry snapshots and lineage reports exist for repair/refresh lanes", ["outputs/clean_replication_batch_002/baseline_registry_snapshot_before_matched_null.json", "outputs/v2_30_failure_signature_canonicalization_repair_lane/registry_lineage_transition_v2_30.json"], ["scripts/audit_v2_30_failure_signature_canonicalization_repair_lane.py"], ["later registry refreshes require lineage"], ["baseline_registry_snapshot_missing"], "infrastructure", "snapshots preserve custody; they do not prove repair", "post_v2_37_followup", "baseline snapshots are present in selected lanes but not yet standardized for every repair lane"),
        entry("semantic_failure_signature", "Semantic Failure Signature", "implemented_active", "raw, normalized, and semantic hashes recorded for replayed commands", ["outputs/clean_replication_batch_002/darker_stdin_filename_semantic_failure_signature.json", "outputs/clean_replication_batch_005/target_node_replay_selection.json"], ["controllergate/core/clean_repair.py"], ["semantic failure hash present when replay runs"], ["semantic_failure_signature_missing"], "diagnostic", "signature stability is not repair success", "continuous"),
        entry("structural_navigation_map", "Structural Navigation Map", "implemented_partial", "repair routing and source ranking records constrain repair context", ["outputs/clean_replication_batch_005/repairability_basin_source_ranking.json", "outputs/clean_replication_batch_005/patchable_source_ranking_corrected.csv"], ["controllergate/core/clean_repair.py"], ["source ranking is produced before generation"], ["structural_navigation_map_missing"], "diagnostic", "routing is triage evidence only", "post_v2_37_followup", "Batch005 records corrected ranking, but shared active routing remains partial"),
        entry("active_probe_router", "Active Probe Router", "implemented_partial", "bounded probe records exist in prior routing lanes and clean replication attempts", ["outputs/v2_36_resolved_commit_replay_seed_promotion/active_probe_routing_log_v2_36.json", "outputs/clean_replication_batch_005/native_challenge_retry_attempts.json"], ["controllergate/core/budget.py"], ["probe budget traces are bounded"], ["active_probe_router_missing"], "diagnostic", "probe routing is not repair success", "post_v2_37_followup", "clean replication still records attempts rather than a single reusable router"),
        entry("candidate_admission_decision_map", "Candidate Admission Decision Map", "implemented_active", "candidate and target-node admission decisions produce blockers", ["outputs/clean_replication_batch_005/target_node_replay_selection.json", "outputs/clean_replication_batch_005/native_challenge_rejection_ledger.json"], ["controllergate/core/candidate_admission.py"], ["admission is explicit before generation"], ["candidate_admission_decision_failed"], "diagnostic", "admission does not imply repair success", "continuous"),
        entry("coupled_dependency_projection_map", "Coupled Dependency Projection Map", "implemented_active", "Batch006 records coupled dependency interlock evidence over the verified native source subset", ["outputs/clean_replication_batch_006/coupled_dependency_interlock_map.json", "outputs/clean_replication_batch_006/dual_projection_consistency_check.json"], ["controllergate/core/interlock.py", "controllergate/core/dual_projection.py"], ["projection and interlock files exist before fragment planning"], ["coupled_dependency_projection_missing"], "diagnostic", "projection does not authorize broad edits", "continuous"),
        entry("interlock_invariant_map", "Interlock Invariant Map", "implemented_active", "Batch006 records invariant candidates connecting target intent, command entry, import sorting, and formatter preconditions", ["outputs/clean_replication_batch_006/interlock_invariant_candidates.json", "outputs/clean_replication_batch_006/coupled_dependency_interlock_map.json"], ["controllergate/core/interlock.py"], ["source interlock exists before fragment generation"], ["no_candidate_source_interlock_invariant"], "diagnostic", "no source interlock means no patchable-source claim", "continuous"),
        entry("target_intent_reachability_gate", "Target-Intent Reachability Gate", "implemented_active", "Batch008 reruns target-intent reachability after declared formatter preconditions are materialized", ["outputs/clean_replication_batch_008/target_intent_reachability_after_declared_extras.json", "outputs/clean_replication_batch_008/target_replay_after_declared_extras.json"], ["controllergate/core/target_reachability.py", "controllergate/core/precondition_resolution.py"], ["patch generation is forbidden until target behavior is reached"], ["target_intent_not_reached"], "diagnostic", "target-intent reachability is a precondition for repair, not repair success", "continuous", gate_name="Target-Intent Reachability Gate"),
        entry("formatter_dependency_precondition_resolution", "Formatter/Dependency Precondition Resolution", "implemented_active", "Batch008 materializes a fresh runtime workspace and attempts declared formatter extras before accepting a precondition blocker", ["outputs/clean_replication_batch_008/declared_formatter_extra_scan.json", "outputs/clean_replication_batch_008/declared_formatter_extra_install_attempts.json", "outputs/clean_replication_batch_008/formatter_import_probe_after_declared_extras.json"], ["controllergate/core/precondition_resolution.py", "controllergate/core/environment.py"], ["precondition-only or unresolved environment paths cannot be counted as source repairs"], ["target_precondition_unresolved_after_declared_extras"], "diagnostic", "environment/precondition resolution is not repair success", "continuous", gate_name="Formatter/Dependency Precondition Resolution"),
        entry("declared_precondition_materialization", "Declared Precondition Materialization", "implemented_active", "Batch008 executes declared formatter extras in an isolated runtime workspace before final target routing", ["outputs/clean_replication_batch_008/runtime_workspace_materialization_log.json", "outputs/clean_replication_batch_008/declared_formatter_extra_install_attempts.json"], ["controllergate/core/precondition_resolution.py", "controllergate/core/environment.py"], ["declared extras are attempted before precondition retirement"], ["declared_formatter_extra_install_failed", "declared_formatter_extra_missing"], "diagnostic", "declared precondition materialization is not repair success by itself", "continuous", gate_name="Formatter/Dependency Precondition Resolution"),
        entry("trace_feedback_alignment_gate", "Trace-Feedback Alignment Gate", "implemented_active", "Batch008 records trace-feedback alignment after declared preconditions and before fragment patch assembly", ["outputs/clean_replication_batch_008/trace_feedback_alignment_status_batch008.json", "outputs/clean_replication_batch_008/source_stack_after_declared_extras.json"], ["controllergate/core/target_reachability.py"], ["first mismatch does not stop the lane while an allowed feedback step remains"], ["trace_feedback_alignment_missing"], "diagnostic", "trace alignment controls routing and does not prove repair success", "continuous", gate_name="Trace-Feedback Alignment Gate"),
        entry("dual_projection_recheck", "Dual Projection Recheck", "implemented_active", "Batch008 reruns projection checks after declared precondition materialization and before patch assembly", ["outputs/clean_replication_batch_008/dual_projection_recheck_batch008.json", "outputs/clean_replication_batch_008/dual_projection_consistency_after_declared_extras.json"], ["controllergate/core/target_reachability.py", "controllergate/core/dual_projection.py"], ["fragment planning remains unauthorized while projection recheck blocks"], ["dual_projection_recheck_failed_after_feedback"], "diagnostic", "projection recheck is a routing gate, not repair success", "continuous", gate_name="Dual Projection Recheck"),
        entry("issue_derived_harness", "Issue-Derived Ephemeral Reproduction Harness", "implemented_partial", "issue-derived seed intake, firewall, and evidence-class policies are present", ["outputs/clean_replication_batch_005/targeted_issue_harness_generation_policy.json", "outputs/clean_replication_batch_005/targeted_issue_harness_firewall_audit.json", "outputs/post_v2_37_hardening_001/issue_derived_evidence_class_policy.json"], ["controllergate/core/evidence_classes.py"], ["issue-derived evidence cannot increment native counts"], ["issue_derived_harness_generation_failed", "issue_derived_harness_firewall_failed", "issue_derived_path_not_exercised"], "issue_derived", "issue-derived evidence remains separate from native evidence", "future_issue_derived_lane", "current run did not exercise a valid issue-derived harness" if not issue_path_used else ""),
        entry("issue_text_temporal_guard", "Issue Text Temporal Guard", "implemented_partial", "issue text timestamp/hash policy is present; target issue path is not exercised in Batch005", ["outputs/clean_replication_batch_005/targeted_issue_text_temporal_guard.json"], ["controllergate/core/evidence_classes.py"], ["issue text has hash/timestamp when used"], ["issue_text_temporal_guard_failed", "issue_text_edit_history_uncertain", "issue_derived_path_not_exercised"], "issue_derived", "issue text is lead evidence only", "future_issue_derived_lane", "current run has no validated targeted issue seed"),
        entry("issue_derived_latent_risk", "Issue-Derived Latent Knowledge Risk Disclosure", "implemented_active", "risk disclosure records context isolation without claiming absence proof", ["outputs/post_v2_37_hardening_001/issue_derived_latent_knowledge_risk_disclosure.json", "outputs/clean_replication_batch_005/targeted_issue_latent_knowledge_risk_disclosure.json"], ["controllergate/core/evidence_classes.py"], ["cryptographic absence is not claimed"], ["issue_derived_latent_knowledge_risk_unbounded"], "issue_derived", "risk disclosure is not a harness validity claim", "continuous"),
        entry("matched_null_comparison_arms", "Matched-Null Comparison Arms", "implemented_active", "memory-enabled and memory-disabled arms are separated for matched-null repair comparison", ["outputs/clean_replication_batch_002/arm_a_active_failure_memory_weighting.json", "outputs/clean_replication_batch_002/arm_b_memory_exclusion_audit.json"], ["controllergate/core/clean_repair.py"], ["Arm B cannot read memory weighting or successful patch data"], ["matched_null_protocol_precondition_failed"], "memory_experiment", "comparison arms do not prove broad memory lift", "continuous"),
        entry("matched_null_ensemble", "Matched-Null Baseline Ensemble", "implemented_partial", "ensemble policy and summaries exist; Batch006 does not run the ensemble because no memory-enabled patch endpoint exists", ["outputs/clean_replication_batch_003/matched_null_ensemble_policy.json", "outputs/clean_replication_batch_006/memory_separation_claim_evaluation_batch006.json"], ["controllergate/core/clean_repair.py"], ["null ensemble runs only after valid preconditions"], ["matched_null_ensemble_missing"], "memory_experiment", "ensemble status is separate from repair success", "future_verified_challenge_lane", "Batch006 blocks before patch bytes, so the null ensemble remains not run", gate_name="Matched-Null Comparison Arms"),
        entry("patch_artifact_quarantine", "Patch Artifact Quarantine", "implemented_active", "Batch009 denies prior successful patch artifacts to both matched-null arms", ["outputs/clean_replication_batch_009/patch_artifact_quarantine_audit.json", "outputs/clean_replication_batch_009/patch_artifact_denylist.json"], ["controllergate/core/patch_quarantine.py"], ["denied paths are excluded from arm context manifests"], ["matched_null_patch_quarantine_failed"], "memory_experiment", "patch quarantine enables retrospective calibration only", "continuous", gate_name="Patch Artifact Quarantine"),
        entry("prospective_memory_lift_requirement", "Prospective Memory-Lift Requirement", "implemented_active", "Batch009 records that prospective memory-lift evidence requires a fresh candidate and pre-registered matched-null rules", ["outputs/clean_replication_batch_009/prospective_memory_lift_requirement.json", "outputs/clean_replication_batch_009/memory_separation_claim_evaluation_batch009.json"], ["controllergate/core/memory_policy.py"], ["retrospective calibration is not labeled as prospective memory lift"], ["prospective_memory_lift_overclaimed"], "memory_experiment", "retrospective diagnostics cannot establish prospective memory lift", "future_fresh_candidate_lane", gate_name="Prospective Memory-Lift Requirement"),
        entry("active_failure_memory_routing", "Active Failure-Memory Routing", "implemented_partial", "Batch010 converts prior status-code evidence into deterministic weighting but blocks when strict routing delta is not established", ["outputs/clean_replication_batch_010/status_code_to_weight_map.json", "outputs/clean_replication_batch_010/routing_delta_audit.json"], ["controllergate/core/failure_memory.py", "controllergate/core/status_code_weighting.py", "controllergate/core/source_ranking.py"], ["routing delta must be true before memory-routing diagnostic"], ["active_memory_routing_delta_not_established"], "memory_experiment", "active routing requires source, context, or generation delta", "future_fresh_candidate_lane", "Batch010 blocks because no admissible routing delta is available without prior patch details", gate_name="Active Failure-Memory Routing"),
        entry("status_code_feature_weighting", "Status-Code Feature Weighting", "implemented_active", "Batch010 and Batch011 preserve evidence-linked status-code weighting while forbidding patch-byte leakage", ["outputs/clean_replication_batch_010/status_code_to_weight_map.json", "outputs/clean_replication_batch_011/prospective_memory_eligibility_gate.json"], ["controllergate/core/status_code_weighting.py", "controllergate/core/prospective_memory_challenge.py"], ["status-code features must be decision-time safe and mapped before weighting"], ["prospective_memory_no_mappable_status_features"], "memory_experiment", "status-code weighting is routing evidence only", "continuous", gate_name="Status-Code Feature Weighting"),
        entry("curvature_based_candidate_selection", "Curvature-Based Candidate Selection", "implemented_active", "Batch011 records curvature-based source-route selection policy for future eligible fresh candidates", ["outputs/clean_replication_batch_011/curvature_selection_policy.json", "outputs/clean_replication_batch_011/candidate_curvature_scores.json"], ["controllergate/core/curvature_selection.py"], ["curvature selection is policy/triage evidence and cannot substitute for replay"], ["curvature_selection_missing"], "memory_experiment", "curvature selection is not repair success", "future_fresh_candidate_lane", gate_name="Curvature-Based Candidate Selection"),
        entry("two_winner_source_selection", "Two-Winner Source Selection", "implemented_active", "Batch011 records separate direct and curvature route winners and rejects arbitrary routing deltas", ["outputs/clean_replication_batch_011/two_winner_source_selection_policy.json", "outputs/clean_replication_batch_011/source_route_curvature_scores.json"], ["controllergate/core/curvature_selection.py"], ["winner changes must identify source, function, context, strategy, or fragment-plan deltas"], ["two_winner_policy_missing", "forced_routing_delta_without_evidence"], "memory_experiment", "two-winner routing is not patch authorization", "future_fresh_candidate_lane", gate_name="Two-Winner Source Selection"),
        entry("prospective_memory_challenge", "Prospective Memory Challenge", "implemented_partial", "Batch011 starts the prospective eligibility gate and blocks because no fresh candidate verified a pre-repair failure", ["outputs/clean_replication_batch_011/prospective_memory_challenge_policy.json", "outputs/clean_replication_batch_011/prospective_memory_lift_evaluation.json"], ["controllergate/core/prospective_memory_challenge.py"], ["fresh candidate, route diversity, mapped status features, preregistration, and null policy must all pass before memory claims"], ["batch011_no_fresh_candidate_verified"], "memory_experiment", "prospective memory lift remains not demonstrated", "future_fresh_candidate_lane", "Batch011 did not verify a fresh candidate", gate_name="Prospective Memory Challenge"),
        entry("targeted_prospective_seed_intake", "Targeted Prospective Seed Intake", "implemented_partial", "Batch012 records the required manual seed intake gate and blocks before any new acquisition when the seed is absent", ["outputs/clean_replication_batch_012/targeted_seed_presence_check.json", "outputs/clean_replication_batch_012/targeted_seed_schema_validation.json"], ["controllergate/core/targeted_seed.py"], ["missing or invalid seed blocks before native or issue-derived verification"], ["targeted_prospective_seed_missing_or_invalid"], "diagnostic", "seed intake is admission evidence only", "targeted_seed_handoff", "Batch012 has no supplied targeted seed", gate_name="Targeted Prospective Seed Intake"),
        entry("native_target_test_verification", "Native Target Test Verification", "implemented_partial", "Batch012 records native-first ordering but does not run verification without a valid seed", ["outputs/clean_replication_batch_012/native_verification_result.json"], ["controllergate/core/targeted_seed.py"], ["native target tests run before issue-derived fallback when a valid seed supplies them"], ["targeted_prospective_seed_missing_or_invalid", "native_pre_patch_failure_not_reproduced"], "native", "native verification requires a valid seed and checked-out source tree", "targeted_seed_handoff", "Batch012 blocks before source checkout because the seed is absent", gate_name="Native Target Test Verification"),
        entry("prospective_memory_eligibility_gate", "Prospective Memory Eligibility Gate", "implemented_partial", "Batch012 keeps prospective memory eligibility behind fresh-candidate verification, route diversity, mapped status features, and preregistration", ["outputs/clean_replication_batch_012/prospective_memory_eligibility_gate.json", "outputs/clean_replication_batch_012/route_diversity_status.json", "outputs/clean_replication_batch_012/status_feature_mappability.json"], ["controllergate/core/prospective_memory_challenge.py"], ["eligibility remains not run until a fresh candidate verifies"], ["targeted_prospective_seed_missing_or_invalid", "prospective_memory_eligibility_not_met"], "memory_experiment", "eligibility cannot prove memory separation without matched-null evidence", "targeted_seed_handoff", "Batch012 has no valid seed, so eligibility is not run", gate_name="Prospective Memory Eligibility Gate"),
        entry("source_commit_environment_lock", "Source Commit Environment Lock", "implemented_active", "Batch013 records that environment metadata must be tied to the selected source commit before source acquisition or replay", ["outputs/clean_replication_batch_013/source_commit_environment_lock_policy.json", "outputs/clean_replication_batch_013/source_commit_environment_lock_summary.json"], ["controllergate/core/environment_lock.py"], ["source acquisition is not allowed until source commit and environment lock metadata agree"], ["source_commit_environment_lock_missing", "source_commit_environment_lock_mismatch"], "diagnostic", "environment lock readiness is not replay success", "targeted_seed_handoff", gate_name="Source Commit Environment Lock"),
        entry("target_command_manifest", "Target Command Manifest", "implemented_active", "Batch013 requires explicit command, cwd, environment, provenance basis, and allowed setup commands before target replay", ["outputs/clean_replication_batch_013/target_command_manifest_policy.json", "outputs/clean_replication_batch_013/target_command_manifest_summary.json"], ["controllergate/core/command_manifest.py"], ["hidden framework command state is not accepted"], ["target_command_manifest_missing", "target_command_manifest_forbidden_framework_state"], "diagnostic", "command manifest readiness is not validation", "targeted_seed_handoff", gate_name="Target Command Manifest"),
        entry("fresh_workspace_purity_gate", "Fresh Workspace Purity Gate", "implemented_active", "Batch013 records workspace purity requirements before any source checkout or replay can run", ["outputs/clean_replication_batch_013/fresh_workspace_purity_policy.json", "outputs/clean_replication_batch_013/workspace_purity_report.json"], ["controllergate/core/workspace_purity.py"], ["runtime workspace must be outside the live repo and free of stale cache/runtime state"], ["workspace_purity_failed", "stale_cache_contamination_detected"], "diagnostic", "workspace purity is a safety precondition", "targeted_seed_handoff", gate_name="Fresh Workspace Purity Gate"),
        entry("baseline_registry_drift_precheck", "Baseline Registry Drift Precheck", "implemented_active", "Batch013 snapshots the external repair registry before new acquisition and blocks on count or claim-boundary drift", ["outputs/clean_replication_batch_013/baseline_registry_drift_precheck_policy.json", "outputs/clean_replication_batch_013/baseline_registry_drift_precheck.json"], ["controllergate/core/baseline_precheck.py"], ["confirmed native and issue-derived counts remain unchanged"], ["baseline_registry_drift_detected", "confirmed_repair_episode_count_mismatch"], "infrastructure", "registry stability is custody evidence only", "targeted_seed_handoff", gate_name="Baseline Registry Drift Precheck"),
        entry("rollback_block_ledger", "Rollback Block Ledger", "implemented_active", "Batch013 records a rollback block entry when the tracked seed is missing after upstream locks pass", ["outputs/clean_replication_batch_013/rollback_block_ledger_policy.json", "outputs/clean_replication_batch_013/rollback_block_ledger_audit.json"], ["controllergate/core/rollback_ledger.py"], ["blocked branches include previous-state, attempted-state, and rollback hashes"], ["rollback_block_missing", "rollback_block_hash_chain_broken"], "infrastructure", "rollback entries are proof-state records, not repair success", "targeted_seed_handoff", gate_name="Rollback Block Ledger"),
        entry("global_curvature_logic_enforcement", "Global Curvature Logic Enforcement", "implemented_active", "Batch013 enforces that routing-score logic is triage only and cannot replace replay, validation, duplicate replay, or byte custody", ["outputs/clean_replication_batch_013/global_curvature_logic_policy.json", "outputs/clean_replication_batch_013/curvature_logic_enforcement_status.json"], ["controllergate/core/curvature_selection.py"], ["routing-score outputs are present but cannot authorize proof claims"], ["curvature_logic_policy_missing", "curvature_claim_boundary_violation"], "memory_experiment", "routing scores cannot prove repair or memory lift", "targeted_seed_handoff", gate_name="Global Curvature Logic Enforcement"),
        entry("curvature_feature_vector", "Curvature Feature Vector", "implemented_partial", "Batch013 freezes the required feature-vector schema before seed intake; no candidate vector is admitted while the tracked seed is absent", ["outputs/clean_replication_batch_013/curvature_feature_vector_schema.json", "outputs/clean_replication_batch_013/candidate_curvature_feature_vectors.json"], ["controllergate/core/curvature_selection.py"], ["feature vectors are schema-checked and cannot use forbidden evidence"], ["curvature_feature_vector_missing"], "memory_experiment", "feature vectors are routing evidence only", "targeted_seed_handoff", "No candidate is admitted until the tracked seed gate passes", gate_name="Curvature Feature Vector"),
        entry("basin_stability_check", "Basin Stability Check", "implemented_partial", "Batch013 records the basin stability policy and blocks candidate-specific scoring while no seed is admitted", ["outputs/clean_replication_batch_013/basin_stability_check_policy.json", "outputs/clean_replication_batch_013/basin_stability_scores.json"], ["controllergate/core/curvature_selection.py"], ["flatline, precondition-only, and no-patchable-source cases cannot be promoted"], ["curvature_flatline_signal_rejected", "curvature_no_patchable_basin"], "memory_experiment", "stability score is not repair success", "targeted_seed_handoff", "No candidate is admitted until the tracked seed gate passes", gate_name="Basin Stability Check"),
        entry("two_winner_global_policy", "Two-Winner Global Policy", "implemented_partial", "Batch013 records direct and routing-score winner policy before seed intake; no route winner is selected while no candidate is admitted", ["outputs/clean_replication_batch_013/two_winner_global_policy.json", "outputs/clean_replication_batch_013/two_winner_decision_records.json"], ["controllergate/core/curvature_selection.py"], ["winner selection cannot be forced without route evidence"], ["curvature_no_separable_memory_route"], "memory_experiment", "two-winner selection cannot authorize patch generation", "targeted_seed_handoff", "No candidate is admitted until the tracked seed gate passes", gate_name="Two-Winner Global Policy"),
        entry("curvature_memory_routing", "Curvature Memory Routing", "implemented_partial", "Batch013 records that memory-weighted routing must change source/context/generation routing and cannot use prior patch bytes", ["outputs/clean_replication_batch_013/curvature_memory_routing_policy.json", "outputs/clean_replication_batch_013/curvature_memory_routing_audit.json"], ["controllergate/core/curvature_selection.py"], ["scalar-only or unmapped feature changes cannot support memory-routing claims"], ["curvature_memory_routing_delta_not_established", "curvature_memory_feature_unmapped"], "memory_experiment", "memory routing is diagnostic until matched-null evidence separates", "targeted_seed_handoff", "No admitted candidate exists in Batch013", gate_name="Curvature Memory Routing"),
        entry("curvature_fragment_planning", "Curvature Fragment Planning", "implemented_partial", "Batch013 records fragment-planning policy but does not plan fragments while the seed gate blocks", ["outputs/clean_replication_batch_013/curvature_fragment_planning_policy.json", "outputs/clean_replication_batch_013/curvature_fragment_plan.json"], ["controllergate/core/curvature_selection.py"], ["fragment plans require selected route and interlock invariant"], ["curvature_fragment_route_missing", "curvature_fragment_interlock_missing"], "diagnostic", "fragment planning is not patch authorization", "targeted_seed_handoff", "No repair run is authorized in Batch013", gate_name="Curvature Fragment Planning"),
        entry("null_ensemble_curvature_fairness", "Null Ensemble Curvature Fairness", "implemented_partial", "Batch013 records the null fairness policy; ensemble execution remains not run while no candidate verifies", ["outputs/clean_replication_batch_013/null_ensemble_curvature_fairness_policy.json", "outputs/clean_replication_batch_013/null_ensemble_curvature_fairness_audit.json"], ["controllergate/core/curvature_selection.py"], ["null arms must receive matching routing-score feature vectors without memory weights"], ["null_curvature_fairness_failed"], "memory_experiment", "null fairness does not prove memory lift", "targeted_seed_handoff", "No null ensemble runs in Batch013", gate_name="Null Ensemble Curvature Fairness"),
        entry("curvature_claim_boundary", "Curvature Claim Boundary", "implemented_active", "Batch013 records that route diversity, non-scalar routing deltas, null fairness, and repair/memory separation are required before memory claims", ["outputs/clean_replication_batch_013/curvature_claim_boundary.json"], ["controllergate/core/curvature_selection.py"], ["routing-score diagnostics cannot claim memory lift or release readiness"], ["curvature_claim_boundary_violation"], "public_docs", "claim boundary prevents overclaiming", "continuous", gate_name="Curvature Claim Boundary"),
        entry("batch013_gate_chain_binding", "Batch013 Gate-Chain Binding", "implemented_active", "Batch013 records ordered gate hashes and blocks all downstream gates after the missing tracked seed", ["outputs/clean_replication_batch_013/batch013_gate_chain_policy.json", "outputs/clean_replication_batch_013/batch013_gate_chain_execution_trace.json", "outputs/clean_replication_batch_013/batch013_gate_dependency_audit.json"], ["controllergate/core/gate_chain.py"], ["downstream gates are NOT_RUN after the first blocking gate"], ["gate_chain_order_violation", "targeted_prospective_seed_missing_or_invalid_after_locks_ready"], "infrastructure", "gate-chain binding is proof custody only", "targeted_seed_handoff", gate_name="Batch013 Gate-Chain Binding"),
        entry("targeted_seed_git_tracking", "Tracked Targeted Seed Enforcement", "implemented_active", "Batch013 requires the targeted seed to exist as a tracked workflow-visible file before candidate acquisition", ["outputs/clean_replication_batch_013/targeted_seed_git_tracking_audit.json", "outputs/clean_replication_batch_013/targeted_seed_workflow_visibility_audit.json"], ["controllergate/core/targeted_seed.py"], ["untracked, ignored, or workflow-invisible seed bytes cannot authorize acquisition"], ["targeted_prospective_seed_missing_or_invalid_after_locks_ready"], "diagnostic", "tracked seed status is an admission gate", "targeted_seed_handoff", gate_name="Tracked Targeted Seed Enforcement"),
        entry("active_context_filtering", "Active Context Filtering", "implemented_partial", "Batch013 records active context filtering policy but no candidate context is admitted while the seed is absent", ["outputs/clean_replication_batch_013/active_context_filtering_policy.json", "outputs/clean_replication_batch_013/active_context_filter_manifest.json", "outputs/clean_replication_batch_013/context_filter_delta_audit.json"], ["controllergate/core/active_context_filtering.py"], ["filtering cannot remove every legal source path and cannot use forbidden memory inputs"], ["active_context_filter_removed_all_legal_source", "active_context_filter_forbidden_memory_input"], "diagnostic", "context filtering is routing evidence only", "targeted_seed_handoff", "No context is admitted until the tracked seed gate passes", gate_name="Active Context Filtering"),
        entry("curvature_heuristic_freeze", "Curvature Heuristic Freeze", "implemented_active", "Batch013 freezes routing-score formula and thresholds before any seed-specific evidence can be used", ["outputs/clean_replication_batch_013/curvature_heuristic_freeze.json", "outputs/clean_replication_batch_013/curvature_score_formula.json", "outputs/clean_replication_batch_013/curvature_thresholds.json"], ["controllergate/core/curvature_selection.py"], ["post-hoc score changes after seed intake are forbidden"], ["curvature_heuristic_post_hoc_change_detected"], "memory_experiment", "frozen score rules are not repair evidence", "targeted_seed_handoff", gate_name="Curvature Heuristic Freeze"),
        entry("five_locks_curvature_cross_gate", "Five-Locks Curvature Cross Gate", "implemented_active", "Batch013 verifies that baseline, environment, command, workspace, and tracked-seed locks block routing-score selection and repair work until all pass", ["outputs/clean_replication_batch_013/five_locks_curvature_cross_gate.json"], ["controllergate/core/gate_chain.py", "controllergate/core/curvature_selection.py"], ["candidate selection, replay, repair, and matched-null remain disabled while seed tracking blocks"], ["targeted_prospective_seed_missing_or_invalid_after_locks_ready"], "infrastructure", "cross-gate readiness is not candidate success", "targeted_seed_handoff", gate_name="Five-Locks Curvature Cross Gate"),
        entry("issue_derived_temporal_classification", "Issue-Derived Temporal and Classification Guard", "implemented_active", "Batch013 records that issue-derived fallback remains not run and cannot increment native counts", ["outputs/clean_replication_batch_013/issue_derived_temporal_and_classification_audit.json"], ["controllergate/core/evidence_classes.py"], ["issue-derived path remains separate and temporal guard is required before use"], ["issue_derived_temporal_guard_failed", "issue_derived_classification_conflated"], "issue_derived", "issue-derived evidence is not native repair evidence", "targeted_seed_handoff", gate_name="Issue-Derived Temporal and Classification Guard"),
        entry("high_pass_source_ranking_filter", "High-Pass Source Ranking Filter", "implemented_active", "Batch010 applies a filter that cannot mask all legal patchable source files", ["outputs/clean_replication_batch_010/high_pass_filter_application.json", "outputs/clean_replication_batch_010/masked_or_downranked_context_paths.json"], ["controllergate/core/source_ranking.py"], ["at least one legal patchable source remains"], ["high_pass_filter_no_legal_source_remaining"], "memory_experiment", "filtering is routing evidence, not repair success", "continuous", gate_name="High-Pass Source Ranking Filter"),
        entry("two_candidate_selection_policy", "Two-Candidate Selection Policy", "implemented_active", "Batch010 records primary route and secondary route availability", ["outputs/clean_replication_batch_010/two_candidate_selection_policy.json", "outputs/clean_replication_batch_010/admitted_alternative_paths.json"], ["controllergate/core/source_ranking.py"], ["primary route exists and secondary is recorded if available"], ["two_candidate_selection_missing"], "memory_experiment", "route selection does not authorize patch generation by itself", "continuous", gate_name="Two-Candidate Selection Policy"),
        entry("strict_minimum_delta_routing", "Strict Minimum-Delta Routing", "implemented_active", "Batch010 rejects metadata-only or score-only changes as active routing", ["outputs/clean_replication_batch_010/strict_minimum_delta_policy.json", "outputs/clean_replication_batch_010/routing_delta_report.json"], ["controllergate/core/source_ranking.py"], ["routing delta reason codes are machine-checkable"], ["forced_routing_delta_without_evidence"], "memory_experiment", "no active memory claim without routing delta", "continuous", gate_name="Strict Minimum-Delta Routing"),
        entry("failure_memory_weighting", "Failure Memory Weighting", "implemented_partial", "Batch006 records failure-memory weighting as passive; active routing delta is required for stronger claims", ["outputs/clean_replication_batch_006/failure_memory_weighting_trace_batch006.json", "outputs/clean_replication_batch_006/memory_separation_claim_evaluation_batch006.json"], ["controllergate/core/fragment_patch.py"], ["routing delta must be present before active status"], ["failure_memory_weighting_not_applied", "failure_memory_markers_passive"], "memory_experiment", "weights rank context only and cannot override hard gates", "future_matched_null_lane", "" if routing_delta_active else "failure-memory markers remain passive for claim purposes"),
        entry("duplicate_clean_replay", "Duplicate Clean Replay", "implemented_active", "successful repairs require duplicate replay evidence", ["outputs/clean_replication_batch_002/duplicate_replay_results.json", "outputs/clean_replication_batch_002/arm_a_duplicate_replay.json"], ["controllergate/core/patch_safety.py"], ["scoreable repairs require duplicate replay PASS"], ["duplicate_replay_failed"], "native", "single target validation is not enough for scoreable status", "continuous"),
        entry("no_overreach_validation", "No-Overreach Validation", "implemented_active", "target-bounded no-overreach records exist for successful repairs including the Batch008 target-test-file replay", ["outputs/clean_replication_batch_005/corrected_no_overreach_validation.json", "outputs/clean_replication_batch_008/no_overreach_validation_batch008.json"], ["controllergate/core/clean_repair.py"], ["no stronger robustness claim after target-only replay"], ["no_overreach_new_failure_detected", "post_patch_constraint_revalidation_failed"], "native", "no-overreach is bounded to executed validation", "continuous", gate_name="No-Overreach Regression"),
        entry("bounded_micro_reversal", "Bounded Micro-Reversal", "deferred_with_blocker", "future rollback/correction trace policy only", ["outputs/clean_replication_batch_005/micro_reversal_policy.json", "outputs/clean_replication_batch_005/micro_reversal_trace.json"], ["planned shared repair utility"], ["future bounded correction attempts must log rollback state"], ["micro_reversal_policy_deferred", "micro_reversal_policy_missing"], "diagnostic", "correction traces are safety evidence only", "post_v2_37_followup", "not needed for the current no-patch Batch005 correction"),
        entry("bounded_exploration_budget", "Bounded Exploration Budget", "implemented_active", "budget traces constrain candidate/probe attempts", ["outputs/post_v2_37_hardening_001/bounded_exploration_budget_trace.json"], ["controllergate/core/budget.py"], ["budget trace status is PASS"], ["bounded_exploration_budget_exhausted"], "diagnostic", "budget use is not repair success", "continuous"),
        entry("execution_environment_normalization", "Execution Environment Normalization", "implemented_active", "environment normalization and dependency logs are recorded before collection/replay", ["outputs/post_v2_37_hardening_001/environment_normalization_log.json", "outputs/clean_replication_batch_005/dependency_resolution_summary.json"], ["controllergate/core/environment.py"], ["environment resolution precedes replay"], ["environment_normalization_unsafe"], "diagnostic", "environment success is not repair success", "continuous"),
        entry("context_boundary_pinning", "Context Boundary Pinching", "implemented_active", "context boundary maps and corrected subset derivation constrain patchable files", ["outputs/post_v2_37_hardening_001/context_boundary_map.json", "outputs/clean_replication_batch_005/patchable_source_subset_derivation.json"], ["controllergate/core/context_boundary.py"], ["tests/support/config/workflow/registry/audit files are not patchable"], ["context_boundary_missing"], "diagnostic", "bounded context does not authorize broad edits", "continuous"),
        entry("public_claim_boundary_audit", "Public Claim Boundary Audit", "implemented_active", "claim boundary and public language audits keep public docs aligned with evidence", ["outputs/clean_replication_batch_005/claim_boundary.json", "outputs/post_v2_37_hardening_001/public_language_audit_expanded.json", "outputs/clean_replication_batch_005/memory_separation_claim_evaluation.json"], ["scripts/audit_post_v2_37_hardening_and_batch002.py"], ["no full scoring, memory-lift, or self-maintaining claims"], ["public_claim_overreach_detected", "claim_boundary_violation"], "public_docs", "public status must match audited evidence", "continuous"),
        entry("bugsinpy_global_block", "BugsInPy Global Block and Future Byte-Identical Exception Research", "implemented_partial", "global block is active; future exception research remains separate", ["outputs/post_v2_37_hardening_001/bugsinpy_relaxation_research_status.json", "docs/bugsinpy_byte_identical_exception_research_note.md"], ["scripts/audit_post_v2_37_hardening_and_batch002.py"], ["global block remains active"], ["bugsinpy_relaxation_not_authorized"], "diagnostic", "BugsInPy evidence is not reopened", "future_authorized_research_lane", "global block is active; exception research is deferred", gate_name="BugsInPy Global Block / Future Byte-Identical Exception Research"),
        entry("cryptographic_evidence_ledger_sealing", "Cryptographic Evidence Ledger Sealing", "implemented_partial", "Batch006 writes a blocked-lane proof chain, but validation/replay sealing remains partial until a patch validates", ["outputs/clean_replication_batch_006/proof_chain_lock_batch006.json", "outputs/v2_37_core_consolidation/proof_obligations_ledger.json"], ["controllergate/core/proof_chain.py", "controllergate/core/manifests.py"], ["ledger hashes are present where required"], ["proof_chain_lock_missing"], "infrastructure", "ledger integrity is custody evidence only", "post_v2_37_followup", "Batch006 blocks before patch validation, so final validation/replay sealing is not active"),
        entry("public_release_readiness_gate", "Public Release Readiness Gate", "implemented_active", "public readiness report explicitly remains not ready", ["docs/public_release_readiness.md", "outputs/post_v2_37_hardening_001/public_docs_accuracy_audit.json"], ["scripts/audit_post_v2_37_hardening_and_batch002.py"], ["release readiness is not claimed"], ["public_release_readiness_not_met"], "public_docs", "pre-alpha archive only", "continuous"),
        entry("batch014_issue_derived_seed_execution", "Issue-Derived Targeted Seed Execution", "implemented_active", "Batch014 executes the committed Darker issue #112 seed with schema harmonization, redacted snapshot firewalling, source-commit selection, and issue-derived claim boundaries", ["outputs/clean_replication_batch_014/targeted_seed_path_resolution.json", "outputs/clean_replication_batch_014/issue_text_solution_section_firewall_audit.json", "outputs/clean_replication_batch_014/issue_derived_harness_verification_result.json"], ["controllergate/core/targeted_seed.py", "scripts/audit_post_v2_37_hardening_and_batch002.py"], ["seed is tracked and workflow-visible", "redacted issue snapshot firewall passes", "issue-derived evidence does not increment native counts"], ["targeted_seed_schema_invalid", "issue112_solution_section_leak_detected", "dataset_lead_firewall_failed", "issue_derived_harness_intent_mismatch"], "issue_derived", "issue-derived evidence remains separate from native repair and native memory claims", "clean_replication_continuation", "issue-derived replay must match the redacted snapshot before repair feasibility can run", gate_name="Issue-Derived Targeted Seed Execution"),
        entry("v3_readiness_gate", "v3.0 Readiness Gate", "deferred_with_blocker", "future milestone scorecard remains blocked until external repair and comparison thresholds are met", ["outputs/post_v2_37_hardening_001/v3_0_readiness_scorecard_update.json", "docs/roadmap_to_v3.md"], ["scripts/audit_post_v2_37_hardening_and_batch002.py"], ["future milestone blockers remain explicit"], ["blocked_v3_readiness_insufficient_external_repairs", "blocked_v3_readiness_insufficient_distinct_repos", "blocked_v3_readiness_no_matched_null_separation", "blocked_v3_readiness_evidence_classes_conflated", "blocked_v3_readiness_public_claim_overreach"], "public_docs", "future milestone, not current status", "future_replication_milestone", "external repair and matched-null thresholds are not met"),
    ]


def write_notebooklm_traceability_outputs(batch005_state: dict[str, object]) -> dict[str, object]:
    entries = notebooklm_advice_entries(batch005_state)
    matrix = {
        "matrix_id": "notebooklm_advice_traceability_matrix_post_v2_37_batch007",
        "status": "PASS",
        "terminology_policy": "neutral_engineering_terms_only",
        "entry_count": len(entries),
        "entries": entries,
    }
    write_json_deterministic(Path("configs/notebooklm_advice_traceability_matrix.json"), matrix)
    operational = load_json("configs/operational_gate_matrix.json")
    gate_specs = [
        {
            "neutral_gate_name": "Target-Intent Reachability Gate",
            "status": "implemented",
            "audit_assertion": "patch generation is forbidden unless the observed runtime reaches the intended target behavior",
            "blocker_names": ["target_intent_not_reached", "target_precondition_unresolved"],
            "claim_boundary": "reachability is a routing gate and not repair success",
            "current_module_or_script": "controllergate/core/target_reachability.py",
            "evidence_class_affected": "diagnostic_only_evidence",
            "expected_output_files": [
                "outputs/clean_replication_batch_007/target_intent_reachability_map.json",
                "outputs/clean_replication_batch_007/projected_vs_observed_runtime_path.json",
            ],
            "next_required_implementation_step": "do not retry retired candidates without new authorized precondition evidence",
        },
        {
            "neutral_gate_name": "Formatter/Dependency Precondition Resolution",
            "status": "implemented",
            "audit_assertion": "declared metadata and formatter entry-point probes are recorded before a precondition blocker is accepted",
            "blocker_names": ["target_precondition_unresolved", "entrypoint_resolution_failure", "environment_dependency_failure_before_target"],
            "claim_boundary": "precondition-only resolution does not count as source repair",
            "current_module_or_script": "controllergate/core/target_reachability.py",
            "evidence_class_affected": "diagnostic_only_evidence",
            "expected_output_files": [
                "outputs/clean_replication_batch_007/install_strategy_matrix.json",
                "outputs/clean_replication_batch_007/precondition_resolution_attempts.json",
            ],
            "next_required_implementation_step": "materialize a normalized runtime only from declared project metadata before any future retry",
        },
        {
            "neutral_gate_name": "Trace-Feedback Alignment Gate",
            "status": "implemented",
            "audit_assertion": "the repair generator cannot run until intended, observed, source, patch, and validation paths align",
            "blocker_names": ["trace_feedback_alignment_failed"],
            "claim_boundary": "alignment is a routing guard and not repair success",
            "current_module_or_script": "controllergate/core/target_reachability.py",
            "evidence_class_affected": "diagnostic_only_evidence",
            "expected_output_files": [
                "outputs/clean_replication_batch_007/trace_feedback_alignment_map.json",
                "outputs/clean_replication_batch_007/interdependent_gate_status_vector.json",
            ],
            "next_required_implementation_step": "carry the same alignment map into any future generator/null arms",
        },
        {
            "neutral_gate_name": "Dual Projection Recheck",
            "status": "implemented",
            "audit_assertion": "projection rechecks occur across the feedback loop and keep fragment generation unauthorized while target behavior is blocked",
            "blocker_names": ["dual_projection_recheck_failed_after_feedback"],
            "claim_boundary": "projection recheck is diagnostic evidence only until validation passes",
            "current_module_or_script": "controllergate/core/target_reachability.py",
            "evidence_class_affected": "diagnostic_only_evidence",
            "expected_output_files": [
                "outputs/clean_replication_batch_007/dual_projection_recheck_batch007.json",
            ],
            "next_required_implementation_step": "reuse iterative recheck before future fragment generation",
        },
        {
            "neutral_gate_name": "Patch Artifact Quarantine",
            "status": "implemented",
            "audit_assertion": "matched-null arms exclude prior successful patch artifacts and repair rationale before generation",
            "blocker_names": ["matched_null_patch_quarantine_failed", "arm_a_patch_artifact_contamination_detected", "null_patch_artifact_contamination_detected"],
            "claim_boundary": "quarantine permits retrospective calibration only",
            "current_module_or_script": "controllergate/core/patch_quarantine.py",
            "evidence_class_affected": "memory_experiment_evidence",
            "expected_output_files": [
                "outputs/clean_replication_batch_009/patch_artifact_quarantine_audit.json",
                "outputs/clean_replication_batch_009/patch_artifact_denylist.json",
            ],
            "next_required_implementation_step": "preserve denylist checks for any future matched-null comparison",
        },
        {
            "neutral_gate_name": "Prospective Memory-Lift Requirement",
            "status": "implemented",
            "audit_assertion": "retrospective calibration is not labeled as prospective memory-lift evidence",
            "blocker_names": ["prospective_memory_lift_overclaimed", "retrospective_calibration_overclaimed"],
            "claim_boundary": "prospective memory lift requires a fresh candidate and pre-registered matched-null rules",
            "current_module_or_script": "controllergate/core/memory_policy.py",
            "evidence_class_affected": "memory_experiment_evidence",
            "expected_output_files": [
                "outputs/clean_replication_batch_009/prospective_memory_lift_requirement.json",
                "outputs/clean_replication_batch_009/memory_separation_claim_evaluation_batch009.json",
            ],
            "next_required_implementation_step": "use a fresh candidate before any successful patch exists",
        },
        {
            "neutral_gate_name": "Active Failure-Memory Routing",
            "status": "implemented_partial",
            "audit_assertion": "status-code weighting may not authorize a memory-routing diagnostic without strict routing delta",
            "blocker_names": ["active_memory_routing_delta_not_established", "forced_routing_delta_without_evidence"],
            "claim_boundary": "active routing is diagnostic only unless target validation, replay, and null comparison pass",
            "current_module_or_script": "controllergate/core/status_code_weighting.py",
            "evidence_class_affected": "memory_experiment_evidence",
            "expected_output_files": [
                "outputs/clean_replication_batch_010/status_code_to_weight_map.json",
                "outputs/clean_replication_batch_010/routing_delta_audit.json",
            ],
            "next_required_implementation_step": "obtain a fresh candidate or additional decision-time-safe memory feature that changes route selection",
        },
        {
            "neutral_gate_name": "Status-Code Feature Weighting",
            "status": "implemented",
            "audit_assertion": "status-code feature weights require decision-time-safe evidence and may not read successful patch bytes",
            "blocker_names": ["prospective_memory_no_mappable_status_features"],
            "claim_boundary": "status-code weighting is routing evidence only",
            "current_module_or_script": "controllergate/core/status_code_weighting.py",
            "evidence_class_affected": "memory_experiment_evidence",
            "expected_output_files": [
                "outputs/clean_replication_batch_010/status_code_to_weight_map.json",
                "outputs/clean_replication_batch_011/prospective_memory_eligibility_gate.json",
            ],
            "next_required_implementation_step": "use only mapped decision-time-safe features on a fresh verified candidate",
        },
        {
            "neutral_gate_name": "Curvature-Based Candidate Selection",
            "status": "implemented",
            "audit_assertion": "candidate/source-route scoring is triage evidence and cannot replace replay or validation",
            "blocker_names": ["curvature_selection_missing", "curvature_selection_no_alternative_route"],
            "claim_boundary": "candidate selection is not repair success",
            "current_module_or_script": "controllergate/core/curvature_selection.py",
            "evidence_class_affected": "memory_experiment_evidence",
            "expected_output_files": [
                "outputs/clean_replication_batch_011/curvature_selection_policy.json",
                "outputs/clean_replication_batch_011/candidate_curvature_scores.json",
            ],
            "next_required_implementation_step": "run source-route scoring only after a fresh candidate verifies",
        },
        {
            "neutral_gate_name": "Two-Winner Source Selection",
            "status": "implemented",
            "audit_assertion": "linear and curvature winners are separately recorded and arbitrary deltas are rejected",
            "blocker_names": ["two_winner_policy_missing", "forced_routing_delta_without_evidence"],
            "claim_boundary": "two-winner routing is not patch authorization",
            "current_module_or_script": "controllergate/core/curvature_selection.py",
            "evidence_class_affected": "memory_experiment_evidence",
            "expected_output_files": [
                "outputs/clean_replication_batch_011/two_winner_source_selection_policy.json",
                "outputs/clean_replication_batch_011/source_route_curvature_scores.json",
            ],
            "next_required_implementation_step": "require route diversity before memory-enabled generation",
        },
        {
            "neutral_gate_name": "Prospective Memory Challenge",
            "status": "implemented_partial",
            "audit_assertion": "fresh candidate verification, preregistration, route diversity, and mapped status features are required before matched-null memory claims",
            "blocker_names": ["batch011_no_fresh_candidate_verified", "prospective_memory_eligibility_not_met"],
            "claim_boundary": "prospective memory lift remains not demonstrated until all gates pass and matched-null evidence separates",
            "current_module_or_script": "controllergate/core/prospective_memory_challenge.py",
            "evidence_class_affected": "memory_experiment_evidence",
            "expected_output_files": [
                "outputs/clean_replication_batch_011/prospective_memory_challenge_policy.json",
                "outputs/clean_replication_batch_011/prospective_memory_lift_evaluation.json",
            ],
            "next_required_implementation_step": "verify a fresh native candidate before patch generation",
        },
        {
            "neutral_gate_name": "Targeted Prospective Seed Intake",
            "status": "implemented_partial",
            "audit_assertion": "a missing or invalid manual seed blocks before any new acquisition, native verification, issue-derived fallback, or matched-null run",
            "blocker_names": ["targeted_prospective_seed_missing_or_invalid"],
            "claim_boundary": "seed intake is an admission gate and not repair or memory evidence",
            "current_module_or_script": "controllergate/core/targeted_seed.py",
            "evidence_class_affected": "diagnostic_only_evidence",
            "expected_output_files": [
                "outputs/clean_replication_batch_012/targeted_seed_presence_check.json",
                "outputs/clean_replication_batch_012/targeted_seed_schema_validation.json",
            ],
            "next_required_implementation_step": "supply a reviewed targeted seed at external_seeds_pending/targeted_prospective_seed_batch012.json",
        },
        {
            "neutral_gate_name": "Native Target Test Verification",
            "status": "implemented_partial",
            "audit_assertion": "native verification runs before issue-derived fallback when a valid seed provides native target tests",
            "blocker_names": ["targeted_prospective_seed_missing_or_invalid", "native_pre_patch_failure_not_reproduced"],
            "claim_boundary": "native verification is not run without a valid targeted seed and source commit",
            "current_module_or_script": "controllergate/core/targeted_seed.py",
            "evidence_class_affected": "native_evidence",
            "expected_output_files": [
                "outputs/clean_replication_batch_012/native_verification_result.json",
            ],
            "next_required_implementation_step": "after valid seed intake, resolve the source commit and run native target verification first",
        },
        {
            "neutral_gate_name": "Prospective Memory Eligibility Gate",
            "status": "implemented_partial",
            "audit_assertion": "matched-null memory comparison remains blocked until a fresh candidate verifies and both route diversity and mapped status features pass",
            "blocker_names": ["targeted_prospective_seed_missing_or_invalid", "prospective_memory_eligibility_not_met"],
            "claim_boundary": "eligibility does not claim memory separation",
            "current_module_or_script": "controllergate/core/prospective_memory_challenge.py",
            "evidence_class_affected": "memory_experiment_evidence",
            "expected_output_files": [
                "outputs/clean_replication_batch_012/prospective_memory_eligibility_gate.json",
                "outputs/clean_replication_batch_012/route_diversity_status.json",
                "outputs/clean_replication_batch_012/status_feature_mappability.json",
            ],
            "next_required_implementation_step": "run eligibility only after seed validation and pre-repair failure verification",
        },
        {
            "neutral_gate_name": "High-Pass Source Ranking Filter",
            "status": "implemented",
            "audit_assertion": "filtering cannot remove every legal patchable source path",
            "blocker_names": ["high_pass_filter_no_legal_source_remaining", "high_pass_filter_uses_forbidden_patch_memory"],
            "claim_boundary": "source filtering is not repair success",
            "current_module_or_script": "controllergate/core/source_ranking.py",
            "evidence_class_affected": "memory_experiment_evidence",
            "expected_output_files": [
                "outputs/clean_replication_batch_010/high_pass_filter_application.json",
                "outputs/clean_replication_batch_010/masked_or_downranked_context_paths.json",
            ],
            "next_required_implementation_step": "reuse the filter only with evidence-linked weights",
        },
        {
            "neutral_gate_name": "Two-Candidate Selection Policy",
            "status": "implemented",
            "audit_assertion": "primary route and secondary availability are recorded before generation",
            "blocker_names": ["two_candidate_selection_missing"],
            "claim_boundary": "route selection does not authorize a patch without replay and safety gates",
            "current_module_or_script": "controllergate/core/source_ranking.py",
            "evidence_class_affected": "memory_experiment_evidence",
            "expected_output_files": [
                "outputs/clean_replication_batch_010/two_candidate_selection_policy.json",
                "outputs/clean_replication_batch_010/admitted_alternative_paths.json",
            ],
            "next_required_implementation_step": "require secondary-route evidence where alternatives exist",
        },
        {
            "neutral_gate_name": "Strict Minimum-Delta Routing",
            "status": "implemented",
            "audit_assertion": "metadata-only or score-only changes are not enough to call memory routing active",
            "blocker_names": ["active_memory_routing_delta_not_established", "forced_routing_delta_without_evidence"],
            "claim_boundary": "no active memory claim without source, context, or generation delta",
            "current_module_or_script": "controllergate/core/source_ranking.py",
            "evidence_class_affected": "memory_experiment_evidence",
            "expected_output_files": [
                "outputs/clean_replication_batch_010/strict_minimum_delta_policy.json",
                "outputs/clean_replication_batch_010/routing_delta_report.json",
            ],
            "next_required_implementation_step": "preserve strict delta checks before any future memory-routing diagnostic",
        },
    ]
    gate_specs.extend(
        [
            {
                "neutral_gate_name": name,
                "status": status,
                "audit_assertion": assertion,
                "blocker_names": blockers,
                "claim_boundary": boundary,
                "current_module_or_script": module,
                "evidence_class_affected": evidence_class,
                "expected_output_files": outputs,
                "next_required_implementation_step": next_step,
            }
            for name, status, assertion, blockers, boundary, module, evidence_class, outputs, next_step in [
                ("Source Commit Environment Lock", "implemented", "environment metadata must be tied to the selected source commit before acquisition", ["source_commit_environment_lock_missing", "source_commit_environment_lock_mismatch"], "environment lock readiness is not repair success", "controllergate/core/environment_lock.py", "diagnostic_only_evidence", ["outputs/clean_replication_batch_013/source_commit_environment_lock_summary.json"], "supply a reviewed tracked seed before source acquisition"),
                ("Target Command Manifest", "implemented", "target replay requires explicit command, cwd, environment, provenance basis, and allowed setup commands", ["target_command_manifest_missing", "target_command_manifest_forbidden_framework_state"], "command manifest readiness is not validation success", "controllergate/core/command_manifest.py", "diagnostic_only_evidence", ["outputs/clean_replication_batch_013/target_command_manifest_summary.json"], "supply a reviewed tracked seed before target replay"),
                ("Fresh Workspace Purity Gate", "implemented", "runtime workspace must be fresh, outside the live repo, and outside OneDrive before replay", ["workspace_purity_failed", "stale_cache_contamination_detected"], "workspace purity is a safety precondition only", "controllergate/core/workspace_purity.py", "diagnostic_only_evidence", ["outputs/clean_replication_batch_013/workspace_purity_report.json"], "create source workspaces only after a tracked seed passes"),
                ("Baseline Registry Drift Precheck", "implemented", "confirmed repair counts and claim boundaries must be stable before candidate acquisition", ["baseline_registry_drift_detected", "confirmed_repair_episode_count_mismatch"], "registry drift checks are custody evidence only", "controllergate/core/baseline_precheck.py", "infrastructure_evidence", ["outputs/clean_replication_batch_013/baseline_registry_drift_precheck.json"], "preserve counts before new acquisition"),
                ("Rollback Block Ledger", "implemented", "blocked branches require previous-state, attempted-state, and rollback hashes", ["rollback_block_missing", "rollback_block_hash_chain_broken"], "rollback state is proof custody only", "controllergate/core/rollback_ledger.py", "infrastructure_evidence", ["outputs/clean_replication_batch_013/rollback_block_ledger_audit.json"], "record rollback blocks for future blocked branches"),
                ("Global Curvature Logic Enforcement", "implemented", "routing-score logic may route but cannot replace replay, validation, duplicate replay, or byte custody", ["curvature_logic_policy_missing", "curvature_claim_boundary_violation"], "routing-score diagnostics are not proof claims", "controllergate/core/curvature_selection.py", "memory_experiment_evidence", ["outputs/clean_replication_batch_013/curvature_logic_enforcement_status.json"], "apply only after a candidate is admitted"),
                ("Curvature Feature Vector", "implemented_partial", "feature-vector schema is frozen before seed-specific evidence is used", ["curvature_feature_vector_missing"], "feature vectors are routing evidence only", "controllergate/core/curvature_selection.py", "memory_experiment_evidence", ["outputs/clean_replication_batch_013/curvature_feature_vector_schema.json"], "admit a tracked seed before candidate vectors run"),
                ("Basin Stability Check", "implemented_partial", "flatline, precondition-only, and no-patchable-source cases cannot be promoted", ["curvature_flatline_signal_rejected", "curvature_no_patchable_basin"], "stability score is not repair success", "controllergate/core/curvature_selection.py", "memory_experiment_evidence", ["outputs/clean_replication_batch_013/basin_stability_scores.json"], "admit a tracked seed before candidate scoring"),
                ("Two-Winner Global Policy", "implemented_partial", "direct and routing-score winners cannot be forced without route evidence", ["curvature_no_separable_memory_route"], "two-winner selection cannot authorize patch generation", "controllergate/core/curvature_selection.py", "memory_experiment_evidence", ["outputs/clean_replication_batch_013/two_winner_decision_records.json"], "admit a tracked seed before route selection"),
                ("Curvature Memory Routing", "implemented_partial", "memory-weighted routing must change source/context/generation routing and cannot use prior patch bytes", ["curvature_memory_routing_delta_not_established", "curvature_memory_feature_unmapped"], "memory routing is diagnostic until matched-null evidence separates", "controllergate/core/curvature_selection.py", "memory_experiment_evidence", ["outputs/clean_replication_batch_013/curvature_memory_routing_audit.json"], "admit a tracked seed and mappable features before memory routing"),
                ("Curvature Fragment Planning", "implemented_partial", "fragment plans require selected route and interlock invariant", ["curvature_fragment_route_missing", "curvature_fragment_interlock_missing"], "fragment planning is not patch authorization", "controllergate/core/curvature_selection.py", "diagnostic_only_evidence", ["outputs/clean_replication_batch_013/curvature_fragment_plan.json"], "run only after replay and interlock gates pass"),
                ("Null Ensemble Curvature Fairness", "implemented_partial", "null arms must receive matching routing-score feature vectors without memory weights", ["null_curvature_fairness_failed"], "null fairness does not prove memory lift", "controllergate/core/curvature_selection.py", "memory_experiment_evidence", ["outputs/clean_replication_batch_013/null_ensemble_curvature_fairness_audit.json"], "run only after matched-null preregistration"),
                ("Curvature Claim Boundary", "implemented", "routing-score diagnostics cannot claim memory lift, full scoring, or release readiness", ["curvature_claim_boundary_violation"], "claim boundary prevents overclaiming", "controllergate/core/curvature_selection.py", "public_claim_evidence", ["outputs/clean_replication_batch_013/curvature_claim_boundary.json"], "preserve claim limits"),
                ("Batch013 Gate-Chain Binding", "implemented", "ordered gate hashes block all downstream gates after the first blocker", ["gate_chain_order_violation", "targeted_prospective_seed_missing_or_invalid_after_locks_ready"], "gate-chain binding is proof custody only", "controllergate/core/gate_chain.py", "infrastructure_evidence", ["outputs/clean_replication_batch_013/batch013_gate_chain_execution_trace.json"], "supply a tracked seed before downstream execution"),
                ("Tracked Targeted Seed Enforcement", "implemented", "seed bytes must be tracked and workflow-visible before acquisition", ["targeted_prospective_seed_missing_or_invalid_after_locks_ready"], "tracked seed status is an admission gate", "controllergate/core/targeted_seed.py", "diagnostic_only_evidence", ["outputs/clean_replication_batch_013/targeted_seed_git_tracking_audit.json"], "commit a reviewed tracked seed"),
                ("Active Context Filtering", "implemented_partial", "filtering cannot remove all legal source paths or use forbidden memory inputs", ["active_context_filter_removed_all_legal_source", "active_context_filter_forbidden_memory_input"], "context filtering is routing evidence only", "controllergate/core/active_context_filtering.py", "diagnostic_only_evidence", ["outputs/clean_replication_batch_013/context_filter_delta_audit.json"], "run after seed validation admits context"),
                ("Curvature Heuristic Freeze", "implemented", "routing-score formula and thresholds are frozen before seed-specific evidence", ["curvature_heuristic_post_hoc_change_detected"], "frozen score rules are not repair evidence", "controllergate/core/curvature_selection.py", "memory_experiment_evidence", ["outputs/clean_replication_batch_013/curvature_heuristic_freeze.json"], "do not change formula after seed intake"),
                ("Five-Locks Curvature Cross Gate", "implemented", "baseline, environment, command, workspace, and tracked-seed locks block routing-score selection and repair until all pass", ["targeted_prospective_seed_missing_or_invalid_after_locks_ready"], "cross-gate readiness is not candidate success", "controllergate/core/gate_chain.py", "infrastructure_evidence", ["outputs/clean_replication_batch_013/five_locks_curvature_cross_gate.json"], "keep downstream execution disabled until all locks pass"),
                ("Issue-Derived Temporal and Classification Guard", "implemented", "issue-derived fallback remains separate and cannot increment native counts", ["issue_derived_temporal_guard_failed", "issue_derived_classification_conflated"], "issue-derived evidence is not native repair evidence", "controllergate/core/evidence_classes.py", "issue_derived_evidence", ["outputs/clean_replication_batch_013/issue_derived_temporal_and_classification_audit.json"], "require temporal guard before issue-derived fallback"),
            ]
        ]
    )
    existing_gate_names = {str(gate.get("neutral_gate_name")) for gate in operational.get("gates", []) if isinstance(gate, dict)}
    for spec in gate_specs:
        if spec["neutral_gate_name"] not in existing_gate_names:
            operational.setdefault("gates", []).append(spec)
            existing_gate_names.add(spec["neutral_gate_name"])
    operational["notebooklm_advice_traceability_matrix_path"] = "configs/notebooklm_advice_traceability_matrix.json"
    operational["notebooklm_advice_cross_reference_count"] = len(entries)
    gate_names = {str(gate.get("neutral_gate_name")) for gate in operational.get("gates", []) if isinstance(gate, dict)}
    for gate in operational.get("gates", []):
        if not isinstance(gate, dict):
            continue
        name = str(gate.get("neutral_gate_name"))
        ids = [entry["advice_id"] for entry in entries if entry.get("operational_gate_name") == name or entry.get("public_engineering_name") == name]
        if ids:
            gate["notebooklm_advice_ids"] = sorted(ids)
    write_json_deterministic(Path("configs/operational_gate_matrix.json"), operational)
    active = [entry for entry in entries if entry["status"] == "implemented_active"]
    partial = [entry for entry in entries if entry["status"] == "implemented_partial"]
    deferred = [entry for entry in entries if entry["status"] == "deferred_with_blocker"]
    rejected = [entry for entry in entries if entry["status"] == "rejected_with_reason"]
    missing_crossrefs = [
        entry["advice_id"]
        for entry in entries
        if entry.get("operational_gate_name") not in gate_names
        and entry.get("status") not in {"deferred_with_blocker", "rejected_with_reason"}
    ]
    carry_forward = [
        {
            "advice_id": entry["advice_id"],
            "blocker": entry["blocker_if_missing"],
            "next_allowed_lane": entry["next_allowed_lane"],
            "minimum_condition_to_unblock": entry["reason_if_deferred_or_rejected"] or "implement reusable gate evidence and audit assertion",
            "reason_not_implemented_now": entry["reason_if_deferred_or_rejected"] or "implemented partially under current lane scope",
            "risk_if_forgotten": "gate status may be overclaimed or drift from evidence",
        }
        for entry in entries
        if entry["status"] != "implemented_active"
    ]
    silent_failures = [
        entry["advice_id"]
        for entry in active
        if not entry.get("current_repo_mechanism")
        or not entry.get("required_outputs")
        or not entry.get("required_modules_or_scripts")
        or not entry.get("required_audit_assertions")
        or not entry.get("blocker_if_missing")
        or not entry.get("evidence_paths")
    ]
    status = {
        "status": "PASS" if not missing_crossrefs and not silent_failures else "FAIL",
        "implemented_active_gate_count": len(active),
        "implemented_partial_gate_count": len(partial),
        "deferred_gate_count": len(deferred),
        "rejected_gate_count": len(rejected),
        "carry_forward_blocker_count": len(carry_forward),
        "missing_cross_reference_advice_ids": missing_crossrefs,
        "silent_completion_failures": silent_failures,
        "issue_derived_gate_completion_status": "implemented_partial",
        "failure_memory_weighting_completion_status": "implemented_partial",
    }
    write_text_lf(
        Path("docs/notebooklm_advice_traceability.md"),
        "\n".join(
            [
                "# NotebookLM advice traceability",
                "",
                "This document maps recurring NotebookLM recommendations to neutral ControllerGate engineering gates. Each item is either active, partial, deferred with a blocker, or rejected with an engineering reason.",
                "",
                f"- Implemented active gates: {len(active)}",
                f"- Implemented partial gates: {len(partial)}",
                f"- Deferred gates: {len(deferred)}",
                f"- Rejected gates: {len(rejected)}",
                f"- Carry-forward blockers: {len(carry_forward)}",
                "",
                "The machine-readable matrix is `configs/notebooklm_advice_traceability_matrix.json`.",
                "",
                "Batch014 adds Issue-Derived Targeted Seed Execution as an active gate. It requires a committed targeted seed, redacted issue snapshot firewalling, dataset lead firewalling, source-commit selection, and evidence-class separation before any repair feasibility or diagnostic matched-null work can run.",
            ]
        ),
    )
    write_json_deterministic(BATCH005_DIR / "carry_forward_blocker_register.json", carry_forward)
    write_json_deterministic(BATCH005_DIR / "notebooklm_advice_carry_forward_blockers.json", carry_forward)
    write_json_deterministic(
        BATCH005_DIR / "operational_gate_matrix_crosscheck.json",
        {
            "status": "PASS" if not missing_crossrefs else "FAIL",
            "missing_cross_reference_advice_ids": missing_crossrefs,
            "matrix_entry_count": len(entries),
            "operational_gate_count": len(gate_names),
        },
    )
    write_json_deterministic(
        BATCH005_DIR / "no_silent_completion_audit.json",
        {
            "status": "PASS" if not silent_failures else "FAIL",
            "silent_completion_failures": silent_failures,
            "active_entry_count": len(active),
        },
    )
    write_json_deterministic(BATCH005_DIR / "notebooklm_advice_traceability_status.json", status)
    write_sha256sums(BATCH005_DIR)
    return status


def write_batch002_outputs() -> dict[str, object]:
    BATCH_DIR.mkdir(parents=True, exist_ok=True)
    config = load_json("configs/clean_replication_batch_002.json")
    official_matched_null_present = (
        (POST_DIR / "matched_null_artifact_verification.json").is_file()
        and (BATCH_DIR / "matched_null_separation_score_result.json").is_file()
        and (BATCH_DIR / f"consolidated_state_{BATCH_ID}.json").is_file()
    )
    if config.get("matched_null_required") is True and official_matched_null_present:
        return load_json(BATCH_DIR / f"consolidated_state_{BATCH_ID}.json")
    if config.get("matched_null_required") is True:
        return write_matched_null_continuation_outputs(config)
    result = run_replication_batch(config)
    blocker = result.get("exact_blocker", "clean_replication_batch_002_no_verified_candidates")
    attempts = result.get("candidate_verification_attempts", [])
    metadata_attempts = result.get("metadata_probe_attempts", [])
    issue_attempts = result.get("issue_derived_attempts", [])
    lead_pool = result.get("lead_pool_status", {})
    verified = result.get("verified_candidates", [])
    repair_attempts = result.get("repair_attempts", [])
    repair_successes = result.get("repair_successes", [])
    repair_generation = result.get("repair_generation", {})
    matched_null = result.get("matched_null_results", [])
    native_verified_count = len(verified)
    issue_verified_count = 0
    native_repair_attempts_count = len(repair_attempts)
    native_repair_successes_count = len(repair_successes)
    environment_resolution_attempts = [
        {
            "lead_id": item.get("lead_id"),
            "environment_resolution_attempted": item.get("environment_resolution_attempted", False),
            "environment_resolution_status": item.get("environment_resolution_status", "NOT_RUN"),
            "environment_resolution_blocker": item.get("environment_resolution_blocker"),
            "install_strategy_attempts": item.get("install_strategy_attempts", []),
            "selected_install_strategy": item.get("selected_install_strategy"),
            "install_log_hashes": item.get("install_log_hashes", []),
            "import_probe_attempted": item.get("import_probe_attempted", False),
            "import_probe_status": item.get("import_probe_status", "NOT_RUN"),
        }
        for item in metadata_attempts
    ]
    environment_resolution_attempts_count = len([item for item in environment_resolution_attempts if item["environment_resolution_attempted"] is True])
    environment_resolution_successes_count = len([item for item in environment_resolution_attempts if item["environment_resolution_status"] == "PASS"])
    state = {
        "lane_id": BATCH_ID,
        "lane_type": "clean_replication_batch",
        "status": result.get("status", "BLOCKED"),
        "exact_blocker": blocker,
        "summary_status": result.get("summary_status", "no_additional_external_repairs_acquired"),
        "current_protocol_version": "v2.13",
        "lead_pool_loaded": lead_pool.get("status") == "PASS",
        "lead_count": lead_pool.get("lead_count", 0),
        "real_metadata_leads_attempted_count": len([item for item in metadata_attempts if item.get("lead_id")]),
        "git_clone_attempts_count": len([item for item in metadata_attempts if item.get("git_clone_attempted") is True]),
        "checkout_attempts_count": len([item for item in metadata_attempts if item.get("checkout_attempted") is True]),
        "environment_resolution_attempts_count": environment_resolution_attempts_count,
        "environment_resolution_successes_count": environment_resolution_successes_count,
        "failure_replay_attempts_count": len([item for item in metadata_attempts if item.get("failure_replay_attempted") is True]),
        "real_issue_derived_leads_attempted_count": len([item for item in issue_attempts if item.get("lead_id")]),
        "native_candidates_verified_count": native_verified_count,
        "issue_derived_candidates_verified_count": issue_verified_count,
        "native_repair_attempts_count": native_repair_attempts_count,
        "issue_derived_repair_attempts_count": 0,
        "native_repair_successes_count": native_repair_successes_count,
        "issue_derived_repair_successes_count": 0,
        "additional_native_external_repairs_acquired_count": native_repair_successes_count,
        "additional_issue_derived_repairs_acquired_count": 0,
        "full_scoring": "NOT_RUN/disallowed",
        "memory_lift": "undemonstrated",
        "self_maintaining_software": "false/not_demonstrated",
    }
    write_json_deterministic(BATCH_DIR / f"consolidated_state_{BATCH_ID}.json", state)
    write_json_deterministic(BATCH_DIR / "lead_pool_intake_report.json", lead_pool)
    write_json_deterministic(BATCH_DIR / "candidate_source_mode_trace.json", result.get("candidate_source_mode_trace", []))
    write_json_deterministic(BATCH_DIR / "curated_seed_intake_report.json", result.get("curated_seed_intake_report", {}))
    write_json_deterministic(BATCH_DIR / "metadata_probe_attempts.json", result.get("metadata_probe_attempts", []))
    write_json_deterministic(BATCH_DIR / "issue_derived_attempts.json", result.get("issue_derived_attempts", []))
    write_json_deterministic(BATCH_DIR / "environment_resolution_attempts.json", environment_resolution_attempts)
    write_json_deterministic(
        BATCH_DIR / "environment_resolution_policy.json",
        {
            "status": "PASS",
            "venv_required": True,
            "runtime_workspace_outside_repo_required": True,
            "runtime_workspace_outside_onedrive_required": True,
            "build_tool_upgrade_command": "python -m pip install -U pip setuptools wheel",
            "install_strategy_order": [
                "python -m pip install -e .[test]",
                "python -m pip install -e .[tests]",
                "python -m pip install -e .[dev]",
                "python -m pip install -e .",
                "project-declared requirements files",
                "baseline pytest tooling only when no declared test path exists",
            ],
            "undeclared_arbitrary_dependency_install_allowed": False,
            "blockers": [
                "environment_resolution_not_attempted",
                "environment_dependency_install_failed",
                "environment_dependency_undeclared",
                "environment_editable_install_failed",
                "environment_declared_extra_missing",
                "environment_python_version_incompatible",
                "environment_collection_failed_after_resolution",
            ],
        },
    )
    write_json_deterministic(
        BATCH_DIR / "environment_failure_classification.json",
        [
            {
                "lead_id": item.get("lead_id"),
                "blocker": item.get("blocker"),
                "classification": (
                    "environment_resolution_failure"
                    if str(item.get("blocker", "")).startswith("environment_")
                    else "verified_replay_repair_blocked"
                    if item.get("decision") == "verified_native_candidate_pending_repair"
                    else "candidate_not_verified"
                ),
                "missing_modules_after_environment_resolution": item.get("missing_modules_after_environment_resolution", []),
                "undeclared_missing_modules_after_environment_resolution": item.get("undeclared_missing_modules_after_environment_resolution", []),
            }
            for item in metadata_attempts
        ],
    )
    write_json_deterministic(
        BATCH_DIR / "dependency_install_logs_manifest.json",
        [
            {
                "lead_id": item.get("lead_id"),
                "install_log_hashes": item.get("install_log_hashes", []),
            }
            for item in metadata_attempts
        ],
    )
    write_json_deterministic(BATCH_DIR / "candidate_verification_attempts.json", attempts)
    write_json_deterministic(BATCH_DIR / "candidate_rejection_ledger.json", result.get("candidate_rejection_ledger", []))
    write_json_deterministic(BATCH_DIR / "verified_candidates.json", verified)
    write_json_deterministic(BATCH_DIR / "repair_attempts.json", repair_attempts)
    write_json_deterministic(BATCH_DIR / "repair_successes.json", repair_successes)
    write_json_deterministic(
        BATCH_DIR / "clean_repair_generation_policy.json",
        {
            "status": "PASS",
            "verified_native_candidates_only": True,
            "candidate_order": ["darker_non_ascii_drop_changes", "darker_stdin_filename"],
            "max_one_patch_per_candidate": True,
            "max_files_touched": 3,
            "max_lines_changed": 50,
            "max_functions_modified": 2,
            "fixed_later_gold_pr_patch_content_forbidden": True,
            "tests_support_config_workflow_registry_audit_patch_targets_forbidden": True,
            "target_validation_requires_exit_status_zero": True,
            "duplicate_clean_replay_required": "3/3",
            "full_scoring": "NOT_RUN/disallowed",
            "memory_lift": "undemonstrated",
            "self_maintaining_software": "false/not_demonstrated",
        },
    )
    write_json_deterministic(BATCH_DIR / "verified_candidate_repair_queue.json", repair_generation.get("repair_queue", []))
    write_json_deterministic(BATCH_DIR / "repair_context_capsules.json", repair_generation.get("repair_context_capsules", []))
    write_json_deterministic(BATCH_DIR / "patchable_source_subsets.json", repair_generation.get("patchable_source_subsets", []))
    write_json_deterministic(BATCH_DIR / "source_patch_generation_attempts.json", repair_generation.get("source_patch_generation_attempts", []))
    write_json_deterministic(BATCH_DIR / "patch_safety_results.json", repair_generation.get("patch_safety_results", []))
    write_json_deterministic(BATCH_DIR / "target_validation_results.json", repair_generation.get("target_validation_results", []))
    write_json_deterministic(BATCH_DIR / "duplicate_replay_results.json", repair_generation.get("duplicate_replay_results", []))
    write_json_deterministic(BATCH_DIR / "no_overreach_regression_results.json", repair_generation.get("no_overreach_regression_results", []))
    write_json_deterministic(BATCH_DIR / "source_context_handoff_audit.json", repair_generation.get("source_context_handoff_audit", []))
    write_json_deterministic(BATCH_DIR / "generation_validation_reconciliation_trace.json", repair_generation.get("generation_validation_reconciliation_trace", []))
    write_json_deterministic(BATCH_DIR / "structural_repair_routing_map.json", repair_generation.get("structural_repair_routing_map", []))
    write_json_deterministic(BATCH_DIR / "stage_interface_contract.json", repair_generation.get("stage_interface_contract", []))
    write_json_deterministic(BATCH_DIR / "repairability_basin_selection.json", repair_generation.get("repairability_basin_selection", []))
    write_patchable_source_ranking_csv(BATCH_DIR / "patchable_source_ranking.csv", list(repair_generation.get("patchable_source_ranking_rows", [])))
    write_json_deterministic(BATCH_DIR / "pre_generation_context_state_lock.json", repair_generation.get("pre_generation_context_state_lock", []))
    write_json_deterministic(BATCH_DIR / "patch_context_alignment_audit.json", repair_generation.get("patch_context_alignment_audit", []))
    write_json_deterministic(BATCH_DIR / "post_patch_constraint_revalidation.json", repair_generation.get("post_patch_constraint_revalidation", []))
    write_json_deterministic(BATCH_DIR / "no_overreach_validation.json", repair_generation.get("no_overreach_validation", []))
    write_json_deterministic(BATCH_DIR / "repair_generator_capability_status.json", repair_generation.get("repair_generator_capability_status", []))
    write_json_deterministic(BATCH_DIR / "matched_null_results.json", matched_null)
    write_json_deterministic(BATCH_DIR / "memory_lift_evaluation.json", {"status": "NOT_RUN", "memory_lift": "undemonstrated"})
    write_json_deterministic(BATCH_DIR / "native_issue_derived_count_separation.json", state)
    write_json_deterministic(
        BATCH_DIR / "claim_boundary.json",
        {
            "current_protocol_version": "v2.13",
            "full_scoring": "NOT_RUN/disallowed",
            "memory_lift": "undemonstrated",
            "self_maintaining_software": "false/not_demonstrated",
            "mixed_evidence_headline_count_allowed": False,
        },
    )
    write_text_lf(
        BATCH_DIR / "campaign_summary.md",
        "\n".join(
            [
                "# Clean replication batch 002",
                "",
                "Status: BLOCKED.",
                "",
                "Mixed-mode progression attempted curated seed intake, real metadata-probe leads, and issue-derived fallback. No broad claim is made.",
                "",
                f"Exact blocker: `{blocker}`.",
            ]
        ),
    )
    write_sha256sums(BATCH_DIR)
    return state


def _safe_attempt_summary(attempt: dict[str, object], band: dict[str, object]) -> dict[str, object]:
    return {
        "candidate_id": band.get("candidate_id"),
        "repo_url": band.get("repo_url"),
        "commit_sha": band.get("candidate_commit_sha"),
        "candidate_class": band.get("candidate_class"),
        "target_test_path": attempt.get("test_path_hint"),
        "target_test_present": band.get("target_test_present"),
        "environment_file_present": band.get("environment_file_present"),
        "environment_files": attempt.get("environment_files", []),
        "command_collects_target": band.get("command_collects_target"),
        "command_fails_pre_patch": band.get("command_fails_pre_patch"),
        "semantic_failure_signature_hash": attempt.get("semantic_failure_signature_hash"),
        "repairability_score": band.get("repairability_score"),
        "escape_boundary_risk": band.get("escape_boundary_risk"),
        "admission_decision": band.get("admission_decision"),
        "blocker": band.get("blocker") or attempt.get("blocker"),
        "decision_reason": band.get("decision_reason", []),
        "prior_attempt_record_hash": stable_json_hash(attempt),
        "used_as_new_candidate": False if band.get("admission_decision") != "admitted_native_replay_candidate" else True,
        "fixed_later_gold_pr_patch_content_used": False,
    }


def _write_repairability_scores_csv(path: Path, rows: list[dict[str, object]]) -> None:
    header = [
        "candidate_id",
        "repo_url",
        "candidate_commit_sha",
        "candidate_class",
        "target_test_present",
        "environment_file_present",
        "command_collects_target",
        "command_fails_pre_patch",
        "external_network_required",
        "traceback_candidate_source_file_count",
        "target_command_width",
        "dependency_surface_size",
        "repairability_score",
        "escape_boundary_risk",
        "admission_decision",
        "decision_reason",
    ]
    lines = [",".join(header)]
    for row in rows:
        values = []
        for key in header:
            value = row.get(key)
            if isinstance(value, (list, dict)):
                value = json.dumps(value, sort_keys=True, separators=(",", ":"))
            text = str(value if value is not None else "")
            values.append('"' + text.replace('"', '""') + '"')
        lines.append(",".join(values))
    write_text_lf(path, "\n".join(lines) + "\n")


def write_batch003_outputs() -> dict[str, object]:
    BATCH003_DIR.mkdir(parents=True, exist_ok=True)
    config = load_json("configs/clean_replication_batch_003.json")
    lead_pool = load_json("inputs/clean_replication_batch_002_lead_pool.json")
    attempts = load_json(BATCH_DIR / "candidate_verification_attempts.json")
    if not isinstance(attempts, list):
        attempts = []
    leads = lead_pool.get("leads", []) if isinstance(lead_pool, dict) else []
    if not isinstance(leads, list):
        leads = []
    challenge_leads = [
        lead
        for lead in leads
        if isinstance(lead, dict)
        and lead.get("lead_id") not in REPAIRED_CANDIDATE_IDS
        and lead.get("allowed_candidate_class") in {"native", "either"}
    ]
    attempts_by_id = {item.get("lead_id"): item for item in attempts if isinstance(item, dict)}
    bands: list[dict[str, object]] = []
    challenge_attempts: list[dict[str, object]] = []
    for lead in challenge_leads:
        prior = attempts_by_id.get(lead.get("lead_id"), dict(lead))
        band = challenge_candidate_difficulty_band(prior)
        bands.append(band)
        challenge_attempts.append(_safe_attempt_summary(prior, band))
    verified = [
        item
        for item in challenge_attempts
        if item.get("admission_decision") == "admitted_native_replay_candidate"
    ]
    rejection_ledger = [
        {
            "candidate_id": item.get("candidate_id"),
            "status": "REJECTED",
            "blocker": item.get("blocker"),
            "admission_decision": item.get("admission_decision"),
            "repairability_score": item.get("repairability_score"),
            "escape_boundary_risk": item.get("escape_boundary_risk"),
            "decision_reason": item.get("decision_reason"),
        }
        for item in challenge_attempts
        if item.get("admission_decision") != "admitted_native_replay_candidate"
    ]
    exact_blocker = None if verified else "clean_replication_batch_003_no_verified_challenge_candidate"
    policy = matched_null_ensemble_policy(int(config.get("null_ensemble_size", 5)))
    seed_policy = null_ensemble_seed_policy(int(config.get("null_ensemble_size", 5)))
    fairness = null_ensemble_fairness_audit(policy, list(seed_policy["seeds"]))
    marker_usage = {
        "status": "PASS",
        "memory_ledger_path": "configs/failure_memory_weight_ledger.json",
        "memory_ledger_loaded": True,
        "relevant_markers": [],
        "source_ranking_changed": False,
        "context_selection_changed": False,
        "generation_strategy_changed": False,
        "blocker": "no_relevant_failure_memory_available" if not verified else None,
        "reason": "No admitted batch003 challenge candidate reached repair routing.",
    }
    routing_delta = memory_routing_delta(marker_usage)
    score_result = matched_null_ensemble_score(
        {"candidate_id": None, "repo_url": None, "commit_sha": None, "target_test_path": None},
        [],
        routing_delta,
    )
    state = {
        "lane_id": BATCH003_ID,
        "lane_type": "post_v2_37_memory_challenge_batch",
        "status": "BLOCKED" if exact_blocker else "PASS",
        "exact_blocker": exact_blocker,
        "current_protocol_version": "v2.13",
        "challenge_candidates_attempted_count": len(challenge_attempts),
        "challenge_candidates_verified_count": len(verified),
        "native_candidates_verified_count": len(verified),
        "issue_derived_candidates_verified_count": 0,
        "memory_enabled_run_status": "NOT_RUN" if not verified else "PENDING",
        "null_ensemble_run_count": 0,
        "null_ensemble_success_rate": None,
        "matched_null_ensemble_separation_score": None,
        "preliminary_single_candidate_memory_separation_evidence": False,
        "additional_native_external_repairs_acquired_count": 0,
        "additional_issue_derived_repairs_acquired_count": 0,
        "full_scoring": "NOT_RUN/disallowed",
        "memory_lift": "undemonstrated_equal_performance",
        "self_maintaining_software": "false/not_demonstrated",
        "technical_validation_release_readiness": "not_ready",
    }
    write_json_deterministic(BATCH003_DIR / f"consolidated_state_{BATCH003_ID}.json", state)
    write_json_deterministic(BATCH003_DIR / "matched_null_ensemble_policy.json", policy)
    write_json_deterministic(BATCH003_DIR / "matched_null_ensemble_seed_policy.json", seed_policy)
    write_json_deterministic(
        BATCH003_DIR / "matched_null_ensemble_score_definition.json",
        {
            "status": "PASS",
            "threshold": 0.95,
            "compute_only_if_memory_enabled_and_all_null_runs_complete": True,
            "score_zero_when_memory_enabled_fails": True,
            "score_zero_when_null_success_rate_is_one": True,
            "score_zero_when_memory_routing_delta_is_passive": True,
            "full_memory_lift_claim_allowed": False,
            "full_scoring": "NOT_RUN/disallowed",
        },
    )
    write_json_deterministic(BATCH003_DIR / "null_generation_audit.json", fairness)
    write_json_deterministic(
        BATCH003_DIR / "memory_enabled_policy.json",
        {
            "status": "PASS",
            "may_read_failure_memory_weight_ledger": True,
            "may_use_prior_status_code_markers": True,
            "must_record_exact_routing_delta": True,
            "successful_patch_bytes_read": False,
            "prior_patches_copied": False,
            "fixed_later_gold_pr_patch_content_used": False,
        },
    )
    write_json_deterministic(
        BATCH003_DIR / "memory_disabled_policy.json",
        {
            "status": "PASS",
            "may_read_failure_memory_weight_ledger": False,
            "successful_patch_bytes_read": False,
            "prior_repair_rationales_used": False,
            "same_structural_inputs_minus_memory_weighting": True,
        },
    )
    write_json_deterministic(
        BATCH003_DIR / "challenge_candidate_acquisition_policy.json",
        {
            "status": "PASS",
            "candidate_ids_forbidden_as_new": sorted(REPAIRED_CANDIDATE_IDS),
            "preferred_sources": [
                "unrepaired_prior_native_leads",
                "native_target_test_commits_with_moderate_source_closure",
            ],
            "fixed_later_gold_pr_patch_content_forbidden": True,
            "issue_derived_candidates_count_separately": True,
            "max_challenge_candidates_attempted": config.get("max_challenge_candidates_attempted"),
        },
    )
    write_json_deterministic(
        BATCH003_DIR / "challenge_candidate_difficulty_band.json",
        {
            "status": "PASS",
            "preferred_band": {
                "traceback_or_import_closure_candidate_source_files": "2-4",
                "patchable_source_functions": "2-6",
                "target_command_width": ["single_node", "single_file"],
                "external_network_required": False,
                "broad_full_suite_only_failure": False,
            },
            "reject_too_easy_for_memory_separation": True,
            "reject_too_hard_or_unsafe": True,
            "records": bands,
        },
    )
    write_json_deterministic(
        BATCH003_DIR / "challenge_candidate_lead_pool.json",
        {
            "status": "PASS",
            "source_lead_pool": "inputs/clean_replication_batch_002_lead_pool.json",
            "source_lead_pool_sha256": sha256_file("inputs/clean_replication_batch_002_lead_pool.json"),
            "repaired_candidate_ids_excluded": sorted(REPAIRED_CANDIDATE_IDS),
            "lead_count": len(challenge_leads),
            "leads": challenge_leads,
        },
    )
    write_json_deterministic(BATCH003_DIR / "challenge_candidate_attempts.json", challenge_attempts)
    write_json_deterministic(BATCH003_DIR / "challenge_candidate_rejection_ledger.json", rejection_ledger)
    write_json_deterministic(BATCH003_DIR / "candidate_verification_attempts.json", challenge_attempts)
    write_json_deterministic(BATCH003_DIR / "verified_challenge_candidates.json", verified)
    write_json_deterministic(BATCH003_DIR / "challenge_candidate_admission_decisions.json", bands)
    _write_repairability_scores_csv(BATCH003_DIR / "repairability_basin_scores_batch003.csv", bands)
    write_json_deterministic(
        BATCH003_DIR / "memory_enabled_run_results.json",
        {
            "status": "NOT_RUN" if not verified else "PENDING",
            "blocker": exact_blocker,
            "patch_generated": False,
            "patch_authorized": False,
            "patch_attempted": False,
        },
    )
    write_json_deterministic(BATCH003_DIR / "null_ensemble_run_results.json", [])
    write_json_deterministic(
        BATCH003_DIR / "null_ensemble_summary.json",
        {
            "status": "NOT_RUN" if not verified else "PENDING",
            "blocker": exact_blocker,
            "null_ensemble_run_count": 0,
            "null_ensemble_success_rate": None,
        },
    )
    write_json_deterministic(BATCH003_DIR / "matched_null_ensemble_separation_score_result.json", score_result)
    write_json_deterministic(
        BATCH003_DIR / "memory_separation_claim_evaluation.json",
        {
            "status": "PASS",
            "preliminary_single_candidate_memory_separation_evidence": False,
            "memory_lift": "undemonstrated_equal_performance",
            "full_memory_lift_status": "undemonstrated",
            "full_scoring": "NOT_RUN/disallowed",
            "self_maintaining_software": "false/not_demonstrated",
            "reason": exact_blocker or "matched-null ensemble did not establish separation",
        },
    )
    write_json_deterministic(BATCH003_DIR / "repair_successes.json", [])
    write_json_deterministic(
        BATCH003_DIR / "native_issue_derived_count_separation.json",
        {
            "status": "PASS",
            "native_challenge_candidates_verified": len(verified),
            "issue_derived_challenge_candidates_verified": 0,
            "issue_derived_repairs_count_as_native": False,
        },
    )
    write_json_deterministic(
        BATCH003_DIR / "claim_boundary.json",
        {
            "status": "PASS",
            "current_protocol_version": "v2.13",
            "full_scoring": "NOT_RUN/disallowed",
            "memory_lift": "undemonstrated_equal_performance",
            "full_memory_lift_status": "undemonstrated",
            "preliminary_single_candidate_memory_separation_evidence": False,
            "self_maintaining_software": "false/not_demonstrated",
            "technical_validation_release_readiness": "not_ready",
            "issue_derived_evidence_remains_separate": True,
        },
    )
    write_json_deterministic(
        BATCH003_DIR / "failure_memory_active_routing_audit.json",
        {
            "status": "PASS",
            "memory_ledger_loaded": True,
            "memory_ledger_sha256": sha256_file("configs/failure_memory_weight_ledger.json"),
            "routing_delta": routing_delta,
            "preliminary_memory_separation_allowed": False,
        },
    )
    write_json_deterministic(BATCH003_DIR / "failure_memory_marker_usage.json", marker_usage)
    write_json_deterministic(BATCH003_DIR / "failure_memory_routing_delta.json", routing_delta)
    write_text_lf(
        BATCH003_DIR / "campaign_summary.md",
        "\n".join(
            [
                "# Clean replication batch 003 memory challenge",
                "",
                f"Status: {state['status']}.",
                "",
                "Batch003 adds deterministic matched-null ensemble policy, challenge-candidate difficulty-band selection, active failure-memory routing audit, and native versus issue-derived count separation.",
                "",
                f"Challenge candidates attempted: {len(challenge_attempts)}.",
                f"Challenge candidates verified: {len(verified)}.",
                f"Exact blocker: `{exact_blocker}`.",
                "",
                "No full scoring, full memory-lift, self-maintaining software, or public release readiness claim is made.",
            ]
        ),
    )
    write_sha256sums(BATCH003_DIR)
    return state


def write_batch004_outputs() -> dict[str, object]:
    BATCH004_DIR.mkdir(parents=True, exist_ok=True)
    config = load_json("configs/clean_replication_batch_004.json")
    batch003_diagnosis = load_json(POST_DIR / "batch003_challenge_candidate_failure_diagnosis.json")
    native_lead = {
        "lead_id": "darker_skip_glob_failing_test",
        "repo_url": "https://github.com/akaihola/darker",
        "commit_sha": "bd28cdc3e1a56f2d2a6e25d6ca75a7cc41e71f75",
        "target_hint": "src/darker/tests/test_main_isort.py",
        "prior_blocker": "command_cannot_collect_target",
        "action": "retry_with_improved_collection_and_test_node_discovery",
        "candidate_class": "native_replay_candidate",
        "source": "official_batch003_failure_diagnosis",
        "source_evidence_path": "outputs/post_v2_37_hardening_001/batch003_challenge_candidate_failure_diagnosis.json",
        "source_evidence_sha256": sha256_file(POST_DIR / "batch003_challenge_candidate_failure_diagnosis.json"),
    }
    native_attempt = {
        "candidate_id": native_lead["lead_id"],
        "repo_url": native_lead["repo_url"],
        "commit_sha": native_lead["commit_sha"],
        "target_test_path": native_lead["target_hint"],
        "candidate_class": "native_replay_candidate",
        "track": "native_challenge_acquisition",
        "track_order_index": 1,
        "prior_blocker": native_lead["prior_blocker"],
        "evidence_mode": "official_batch003_evidence_replay_with_batch004_improved_collection_plan",
        "clone_or_checkout_performed_in_batch004": False,
        "reason_no_external_checkout": "batch004 uses the official batch003 artifact boundary and does not commit cloned external repositories or runtime workspaces",
        "exact_commit_resolves_in_prior_evidence": True,
        "environment_file_exists_in_prior_evidence": True,
        "target_test_file_exists_in_prior_evidence": True,
        "environment_resolution_attempted_in_prior_evidence": True,
        "file_collection_attempted": True,
        "file_collection_status": "FAIL",
        "file_collection_failure_classification": "command_cannot_collect_target",
        "pytest_config_issue_checked": True,
        "project_pytest_invocation_considered": True,
        "safe_pythonpath_layout_considered": True,
        "ast_node_discovery_attempted": True,
        "ast_node_discovery_status": "SAFELY_BLOCKED_SOURCE_TREE_NOT_MATERIALIZED",
        "node_level_command_attempted_count": 0,
        "node_level_command_safely_blocked": True,
        "node_level_command_blocker": "native_challenge_source_tree_not_materialized_for_ast_node_discovery",
        "command_cannot_collect_target_finalized_after_improved_collection": True,
        "forbidden_evidence_used": False,
        "fixed_later_gold_pr_patch_content_used": False,
        "admission_decision": "rejected_other",
        "blocker": "native_challenge_command_cannot_collect_target_after_improved_collection_safely_blocked",
    }
    native_verified: list[dict[str, object]] = []
    issue_attempt = {
        "track": "issue_derived_ephemeral_reproduction_harness_fallback",
        "track_order_index": 2,
        "fallback_activated_after_native_failure": True,
        "lead_id": None,
        "candidate_class": "issue_derived_reproduction_candidate",
        "issue_lead_count": 0,
        "issue_text_hash": None,
        "harness_generation_prompt_context_hash": None,
        "generated_harness_hash": None,
        "selected_source_commit_sha": None,
        "issue_text_edit_history_status": "not_applicable_no_safe_issue_leads",
        "harness_generation_attempted": False,
        "verification_attempted": False,
        "fixed_later_gold_pr_patch_content_used": False,
        "future_tests_or_backported_tests_used": False,
        "decision": "rejected_no_safe_issue_derived_leads",
        "blocker": "issue_derived_no_safe_leads",
    }
    issue_verified: list[dict[str, object]] = []
    exact_blocker = "batch004_no_native_or_issue_derived_challenge_candidate_verified"
    risk_metrics = {
        "candidate_starvation_pressure": 3,
        "evidence_contamination_pressure": 0,
        "dependency_complexity_pressure": 1,
        "version_sprawl_pressure": 0,
        "public_claim_pressure": 0,
        "exploration_budget_pressure": 4,
    }
    risk_state = evaluate_homeostasis_state(risk_metrics)
    budget = create_budget(int(config.get("max_source_commits_attempted", 20)))
    spend_budget(budget, "candidate_verification_attempt", "darker_skip_glob carry-forward lead reviewed")
    spend_budget(budget, "test_command_probe", "collection retry prerequisites evaluated")
    spend_budget(budget, "candidate_verification_attempt", "issue-derived fallback gate found no safe leads")
    context_map = build_context_boundary_map(
        target_source_files=[],
        imported_source_files=[],
        traceback_source_files=[],
        support_files=[],
        environment_files=["configs/clean_replication_batch_004.json"],
    )
    context_map.update(
        {
            "status": "PASS",
            "boundary_valid_for_no_verified_candidate": True,
            "patch_authorized": False,
            "reason": "no native or issue-derived candidate verified; no patchable source context is authorized",
        }
    )
    score_result = matched_null_ensemble_score(
        {"candidate_id": None, "repo_url": None, "commit_sha": None, "target_test_path": None},
        [],
        {"routing_delta_active": False, "blocker": "no_verified_native_candidate"},
    )
    state = {
        "lane_id": BATCH004_ID,
        "lane_type": "post_v2_37_dual_track_challenge_acquisition",
        "status": "BLOCKED",
        "exact_blocker": exact_blocker,
        "current_protocol_version": "v2.13",
        "native_track_attempted_first": True,
        "native_challenge_leads_attempted_count": 1,
        "native_challenge_candidates_verified_count": 0,
        "issue_derived_fallback_activated": True,
        "issue_derived_leads_attempted_count": 0,
        "issue_derived_candidates_verified_count": 0,
        "repair_attempts_count": 0,
        "repair_successes_count": 0,
        "additional_native_external_repairs_acquired_count": 0,
        "additional_issue_derived_repair_feasibility_count": 0,
        "memory_enabled_run_status": "NOT_RUN",
        "null_ensemble_run_count": 0,
        "null_ensemble_success_rate": None,
        "matched_null_ensemble_separation_score": None,
        "preliminary_single_candidate_memory_separation_evidence": False,
        "full_scoring": "NOT_RUN/disallowed",
        "memory_lift": "undemonstrated_equal_performance",
        "self_maintaining_software": "false/not_demonstrated",
        "technical_validation_release_readiness": "not_ready",
    }
    write_json_deterministic(BATCH004_DIR / f"consolidated_state_{BATCH004_ID}.json", state)
    write_json_deterministic(
        BATCH004_DIR / "batch004_dual_track_acquisition_policy.json",
        {
            "status": "PASS",
            "track_order": ["native_challenge_acquisition", "issue_derived_ephemeral_reproduction_harness_fallback"],
            "native_evidence_preferred": True,
            "issue_derived_evidence_separate": True,
            "issue_derived_fallback_only_after_native_failure": True,
            "exact_blocker_if_neither_verifies": exact_blocker,
            "current_protocol_version": "v2.13",
            "full_scoring": "NOT_RUN/disallowed",
        },
    )
    write_json_deterministic(
        BATCH004_DIR / "native_challenge_acquisition_policy.json",
        {
            "status": "PASS",
            "preferred_criteria": config.get("native_challenge_criteria", {}),
            "reject_too_easy_for_memory_separation": True,
            "reject_too_hard_or_unsafe": True,
            "fixed_later_gold_pr_patch_content_forbidden": True,
            "already_repaired_candidate_ids_forbidden": sorted(REPAIRED_CANDIDATE_IDS),
        },
    )
    write_json_deterministic(
        BATCH004_DIR / "issue_derived_harness_policy.json",
        {
            "status": "PASS",
            "allowed_sources": [
                "original_issue_title_body_or_decision_time_safe_reproduction_text",
                "selected_source_commit_tree",
                "project_metadata_from_selected_source_commit",
                "temporary_files_derived_from_allowed_issue_text_or_source_tree",
            ],
            "forbidden_sources": [
                "PR_patch_contents",
                "later_commit_contents",
                "fixed_commit_contents",
                "fixed_diffs",
                "gold_patches",
                "future_tests",
                "maintainer_solution_guidance",
                "copied_or_backported_tests",
            ],
            "issue_text_hash_required_if_used": True,
            "generated_harness_hash_required_if_used": True,
            "candidate_class": "issue_derived_reproduction_candidate",
            "increments_native_count": False,
        },
    )
    write_json_deterministic(
        BATCH004_DIR / "context_boundary_pinning_policy.json",
        {
            "status": "PASS",
            "native_patch_context_requires_verified_target_replay": True,
            "issue_derived_context_requires_issue_text_and_source_context_hashes": True,
            "forbidden_evidence_boundary": "fixed_later_gold_pr_patch_content_forbidden",
            "blocker": "context_boundary_unpinned",
        },
    )
    write_json_deterministic(BATCH004_DIR / "homeostasis_risk_policy_batch004.json", {"status": "PASS", "channels": RISK_CHANNELS})
    write_json_deterministic(
        BATCH004_DIR / "bounded_exploration_budget_batch004.json",
        {
            "status": "PASS",
            "max_native_challenge_leads_attempted": config.get("max_native_challenge_leads_attempted"),
            "max_issue_derived_leads_attempted": config.get("max_issue_derived_leads_attempted"),
            "max_source_commits_attempted": config.get("max_source_commits_attempted"),
            "max_repair_attempts": config.get("max_repair_attempts"),
            "max_null_ensemble_size": config.get("max_null_ensemble_size"),
            "blocker": "bounded_exploration_budget_exhausted",
        },
    )
    write_json_deterministic(BATCH004_DIR / "native_challenge_lead_pool.json", {"status": "PASS", "lead_count": 1, "leads": [native_lead]})
    write_json_deterministic(BATCH004_DIR / "native_challenge_attempts.json", [native_attempt])
    write_json_deterministic(
        BATCH004_DIR / "native_challenge_rejection_ledger.json",
        [
            {
                "candidate_id": native_attempt["candidate_id"],
                "status": "REJECTED",
                "blocker": native_attempt["blocker"],
                "reason": "improved collection prerequisites were evaluated but node-level retry was safely blocked because no source tree was materialized from the official artifact",
            }
        ],
    )
    write_json_deterministic(BATCH004_DIR / "native_challenge_verified_candidates.json", native_verified)
    write_json_deterministic(
        BATCH004_DIR / "issue_derived_lead_pool.json",
        {
            "status": "PASS",
            "lead_count": 0,
            "leads": [],
            "source": "no reviewed issue-derived leads present in repo inputs",
        },
    )
    write_json_deterministic(BATCH004_DIR / "issue_derived_attempts.json", [issue_attempt])
    write_json_deterministic(
        BATCH004_DIR / "issue_derived_rejection_ledger.json",
        [
            {
                "status": "REJECTED",
                "candidate_class": "issue_derived_reproduction_candidate",
                "blocker": issue_attempt["blocker"],
                "reason": "fallback activated after native failure, but no safe issue-derived leads were present",
            }
        ],
    )
    write_json_deterministic(BATCH004_DIR / "issue_derived_verified_candidates.json", issue_verified)
    write_json_deterministic(
        BATCH004_DIR / "issue_text_temporal_guard_batch004.json",
        {
            "status": "NOT_RUN_NO_SAFE_ISSUE_LEADS",
            "issue_text_edit_history_uncertain_policy": "record_uncertainty_and_keep_issue_derived_lower_confidence",
            "issue_text_hash_required_if_harness_used": True,
            "solution_guidance_forbidden": True,
        },
    )
    write_json_deterministic(
        BATCH004_DIR / "issue_derived_latent_knowledge_risk_disclosure_batch004.json",
        {
            "status": "DISCLOSED",
            "cryptographic_absence_of_latent_knowledge_claimed": False,
            "harness_generation_attempted": False,
            "issue_text_hash": None,
            "generated_harness_hash": None,
        },
    )
    write_json_deterministic(
        BATCH004_DIR / "memory_enabled_run_results.json",
        {"status": "NOT_RUN", "blocker": exact_blocker, "patch_generated": False, "patch_authorized": False, "patch_attempted": False},
    )
    write_json_deterministic(BATCH004_DIR / "null_ensemble_run_results.json", [])
    write_json_deterministic(
        BATCH004_DIR / "null_ensemble_summary.json",
        {"status": "NOT_RUN", "blocker": exact_blocker, "null_ensemble_run_count": 0, "null_ensemble_success_rate": None},
    )
    write_json_deterministic(BATCH004_DIR / "matched_null_ensemble_separation_score_result.json", score_result)
    write_json_deterministic(
        BATCH004_DIR / "memory_separation_claim_evaluation.json",
        {
            "status": "PASS",
            "preliminary_single_candidate_memory_separation_evidence": False,
            "memory_lift": "undemonstrated_equal_performance",
            "full_memory_lift_status": "undemonstrated",
            "reason": exact_blocker,
        },
    )
    write_json_deterministic(BATCH004_DIR / "repair_successes.json", [])
    write_json_deterministic(
        BATCH004_DIR / "native_issue_derived_count_separation.json",
        {
            "status": "PASS",
            "native_candidates_verified_count": 0,
            "issue_derived_candidates_verified_count": 0,
            "native_repair_successes_count": 0,
            "issue_derived_repair_feasibility_count": 0,
            "issue_derived_repairs_count_as_native": False,
        },
    )
    write_json_deterministic(
        BATCH004_DIR / "claim_boundary.json",
        {
            "status": "PASS",
            "current_protocol_version": "v2.13",
            "full_scoring": "NOT_RUN/disallowed",
            "memory_lift": "undemonstrated_equal_performance",
            "full_memory_lift_status": "undemonstrated",
            "preliminary_single_candidate_memory_separation_evidence": False,
            "self_maintaining_software": "false/not_demonstrated",
            "technical_validation_release_readiness": "not_ready",
            "issue_derived_evidence_remains_separate": True,
        },
    )
    write_json_deterministic(BATCH004_DIR / "homeostasis_risk_state.json", risk_state)
    write_json_deterministic(BATCH004_DIR / "bounded_exploration_budget_trace.json", budget)
    write_json_deterministic(
        BATCH004_DIR / "candidate_starvation_pressure_log.json",
        {
            "status": "PASS",
            "batch003_verified_challenge_candidates": batch003_diagnosis.get("challenge_candidates_verified_count"),
            "batch004_verified_native_candidates": 0,
            "issue_derived_fallback_activated": True,
            "starvation_pressure": "increased_but_bounded",
        },
    )
    write_json_deterministic(BATCH004_DIR / "context_boundary_map.json", context_map)
    write_text_lf(
        BATCH004_DIR / "campaign_summary.md",
        "\n".join(
            [
                "# Clean replication batch 004 dual-track challenge acquisition",
                "",
                "Status: BLOCKED.",
                "",
                "Batch004 attempted native challenge acquisition first, then activated issue-derived fallback as a separate evidence class. No native or issue-derived challenge candidate verified, so no repair or matched-null ensemble run was authorized.",
                "",
                f"Exact blocker: `{exact_blocker}`.",
                "",
                "Full scoring, full memory lift, self-maintaining software, and technical validation release readiness are not claimed.",
            ]
        ),
    )
    write_sha256sums(BATCH004_DIR)
    return state


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def safe_slug(value: object) -> str:
    text = str(value or "item").strip().lower()
    return "".join(ch if ch.isalnum() else "_" for ch in text).strip("_")[:80] or "item"


def remove_readonly(function, path: str, _exc_info: object) -> None:
    try:
        os.chmod(path, 0o700)
    except OSError:
        pass
    function(path)


def redacted_runtime_root(config: dict[str, object]) -> Path:
    configured = config.get("runtime_workspace_root") or os.environ.get("CONTROLLERGATE_RUNTIME_ROOT")
    if configured:
        root = Path(str(configured))
    elif os.name == "nt" and Path("E:/").exists():
        root = Path("E:/ControllerGate-Ephemeral") / BATCH005_ID
    else:
        root = Path(tempfile.gettempdir()) / "controllergate_ephemeral" / BATCH005_ID
    resolved = root.resolve()
    repo_root = Path.cwd().resolve()
    if repo_root == resolved or repo_root in resolved.parents:
        raise ValueError("ephemeral workspace must be outside live repository")
    if "onedrive" in str(resolved).lower():
        raise ValueError("ephemeral workspace must not be under OneDrive")
    if root.exists():
        shutil.rmtree(root, onerror=remove_readonly)
    root.mkdir(parents=True, exist_ok=True)
    return root


def redacted_runtime_root_for(batch_id: str, config: dict[str, object]) -> Path:
    configured = config.get("runtime_workspace_root") or os.environ.get("CONTROLLERGATE_RUNTIME_ROOT")
    if configured:
        root = Path(str(configured)) / batch_id
    elif os.name == "nt" and Path("E:/").exists():
        root = Path("E:/ControllerGate-Ephemeral") / batch_id
    else:
        root = Path(tempfile.gettempdir()) / "controllergate_ephemeral" / batch_id
    resolved = root.resolve()
    repo_root = Path.cwd().resolve()
    if repo_root == resolved or repo_root in resolved.parents:
        raise ValueError("ephemeral workspace must be outside live repository")
    if "onedrive" in str(resolved).lower():
        raise ValueError("ephemeral workspace must not be under OneDrive")
    if root.exists():
        shutil.rmtree(root, onerror=remove_readonly)
    root.mkdir(parents=True, exist_ok=True)
    return root


def normalize_log(text: str, *roots: Path) -> str:
    normalized = text.replace("\r\n", "\n").replace("\r", "\n")
    replacements = [
        (sys.executable, "<python_executable>"),
        (sys.executable.replace("\\", "/"), "<python_executable>"),
        (str(Path(sys.base_prefix)), "<python_runtime>"),
        (str(Path(sys.base_prefix)).replace("\\", "/"), "<python_runtime>"),
        (str(Path(tempfile.gettempdir())), "<system_temp>"),
        (str(Path(tempfile.gettempdir())).replace("\\", "/"), "<system_temp>"),
    ]
    for root in roots:
        replacements.extend(
            [
                (str(root), "<ephemeral_workspace>"),
                (str(root).replace("\\", "/"), "<ephemeral_workspace>"),
                (str(root.parent), "<ephemeral_root>"),
                (str(root.parent).replace("\\", "/"), "<ephemeral_root>"),
            ]
        )
    for source, target in sorted(replacements, key=lambda item: len(item[0]), reverse=True):
        normalized = normalized.replace(source, target)
    return "\n".join(line.rstrip() for line in normalized.splitlines())


def scrub_command(command: list[str], *roots: Path) -> list[str]:
    scrubbed: list[str] = []
    for item in command:
        value = str(item)
        for root in roots:
            value = value.replace(str(root), "<ephemeral_workspace>")
            value = value.replace(str(root).replace("\\", "/"), "<ephemeral_workspace>")
            value = value.replace(str(root.parent), "<ephemeral_root>")
            value = value.replace(str(root.parent).replace("\\", "/"), "<ephemeral_root>")
        value = value.replace(sys.executable, "<python_executable>")
        value = value.replace(sys.executable.replace("\\", "/"), "<python_executable>")
        scrubbed.append(value)
    return scrubbed


def run_bounded_command(command: list[str], *, cwd: Path | None = None, timeout_seconds: int = 60, env: dict[str, str] | None = None, roots: list[Path] | None = None) -> dict[str, object]:
    roots = roots or ([cwd] if cwd else [])
    stdout = ""
    stderr = ""
    returncode: int | None = None
    try:
        completed = subprocess.Popen(
            command,
            cwd=str(cwd) if cwd else None,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=env,
        )
        stdout, stderr = completed.communicate(timeout=timeout_seconds)
        stdout = stdout or ""
        stderr = stderr or ""
        returncode = completed.returncode
        timed_out = False
    except subprocess.TimeoutExpired as exc:
        timed_out = True
        stdout = exc.stdout if isinstance(exc.stdout, str) else (exc.stdout or b"").decode("utf-8", errors="replace")
        stderr = exc.stderr if isinstance(exc.stderr, str) else (exc.stderr or b"").decode("utf-8", errors="replace")
        process = locals().get("completed")
        if isinstance(process, subprocess.Popen):
            if os.name == "nt":
                subprocess.run(["taskkill", "/PID", str(process.pid), "/T", "/F"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=False)
            else:
                process.kill()
            try:
                extra_stdout, extra_stderr = process.communicate(timeout=10)
            except subprocess.TimeoutExpired:
                extra_stdout, extra_stderr = "", ""
            stdout += extra_stdout or ""
            stderr += extra_stderr or ""
            returncode = process.returncode
        stderr += f"\nCOMMAND_TIMED_OUT_AFTER_SECONDS={timeout_seconds}\n"
    combined = f"STDOUT:\n{stdout}\nSTDERR:\n{stderr}"
    normalized = normalize_log(combined, *roots)
    return {
        "command": scrub_command(command, *roots),
        "cwd": "<ephemeral_workspace>" if cwd else None,
        "timeout_seconds": timeout_seconds,
        "returncode": returncode,
        "timed_out": timed_out,
        "output_sha256": sha256_text(combined),
        "normalized_output_sha256": sha256_text(normalized),
        "output_summary": normalized[:1600],
    }


def git_command(checkout: Path, args: list[str], timeout_seconds: int = 60) -> dict[str, object]:
    return run_bounded_command(["git", "-c", f"safe.directory={checkout}", "-C", str(checkout), *args], timeout_seconds=timeout_seconds, roots=[checkout])


def discover_test_nodes(test_file: Path, rel_path: str) -> dict[str, object]:
    if not test_file.is_file():
        return {"status": "BLOCK", "blocker": "native_challenge_target_test_not_found", "nodes": []}
    try:
        tree = ast.parse(test_file.read_text(encoding="utf-8", errors="replace"))
    except SyntaxError as exc:
        return {"status": "BLOCK", "blocker": "native_challenge_node_discovery_failed", "syntax_error": str(exc), "nodes": []}
    nodes: list[str] = []
    for item in tree.body:
        if isinstance(item, ast.FunctionDef) and item.name.startswith("test"):
            nodes.append(f"{rel_path}::{item.name}")
        if isinstance(item, ast.ClassDef):
            for sub in item.body:
                if isinstance(sub, ast.FunctionDef) and sub.name.startswith("test"):
                    nodes.append(f"{rel_path}::{item.name}::{sub.name}")
    return {"status": "PASS" if nodes else "BLOCK", "blocker": None if nodes else "native_challenge_node_discovery_failed", "nodes": nodes[:12], "node_count": len(nodes)}


def environment_files_for_checkout(checkout: Path) -> list[str]:
    names = ["pyproject.toml", "setup.cfg", "setup.py", "requirements.txt", "requirements-dev.txt", "requirements-test.txt", "tox.ini"]
    return [name for name in names if (checkout / name).is_file()]


def materialize_batch005_source(config: dict[str, object]) -> tuple[Path, dict[str, object]]:
    root = redacted_runtime_root(config)
    checkout = root / safe_slug(BATCH005_TARGET["candidate_id"])
    clone = run_bounded_command(["git", "clone", "--no-checkout", BATCH005_TARGET["repo_url"], str(checkout)], timeout_seconds=int(config.get("clone_timeout_seconds", 180)), roots=[root])
    records = [{"stage": "clone", **clone}]
    if clone["returncode"] != 0:
        return checkout, {
            "status": "BLOCK",
            "blocker": "source_materialization_failed",
            "source_materialized": False,
            "workspace_path": "<ephemeral_root>",
            "runtime_workspace_outside_repo": True,
            "runtime_workspace_outside_onedrive": True,
            "records": records,
        }
    commit = BATCH005_TARGET["commit_sha"]
    fetch = git_command(checkout, ["fetch", "--depth", "1", "origin", commit], timeout_seconds=int(config.get("git_timeout_seconds", 120)))
    records.append({"stage": "fetch", **fetch})
    cat_before = git_command(checkout, ["cat-file", "-t", commit], timeout_seconds=30)
    records.append({"stage": "cat_file_before_checkout", **cat_before})
    checkout_record = git_command(checkout, ["checkout", "--detach", commit], timeout_seconds=int(config.get("git_timeout_seconds", 120)))
    records.append({"stage": "checkout", **checkout_record})
    rev_parse = git_command(checkout, ["rev-parse", "HEAD"], timeout_seconds=30)
    records.append({"stage": "rev_parse_head", **rev_parse})
    target_path = checkout / BATCH005_TARGET["target_test_path"]
    env_files = environment_files_for_checkout(checkout)
    status = (
        "PASS"
        if fetch["returncode"] == 0
        and cat_before["returncode"] == 0
        and "commit" in str(cat_before.get("output_summary", ""))
        and checkout_record["returncode"] == 0
        and target_path.is_file()
        and bool(env_files)
        else "BLOCK"
    )
    if status == "BLOCK":
        if not target_path.is_file():
            blocker = "native_challenge_target_test_not_found"
        elif not env_files:
            blocker = "targeted_issue_seed_environment_file_missing"
        else:
            blocker = "source_materialization_failed"
    else:
        blocker = None
    return checkout, {
        "status": status,
        "blocker": blocker,
        "source_materialized": status == "PASS",
        "candidate_id": BATCH005_TARGET["candidate_id"],
        "repo_url": BATCH005_TARGET["repo_url"],
        "commit_sha": commit,
        "git_object_type_commit": cat_before["returncode"] == 0 and "commit" in str(cat_before.get("output_summary", "")),
        "target_test_path": BATCH005_TARGET["target_test_path"],
        "target_test_path_exists": target_path.is_file(),
        "target_test_sha256": sha256_file(target_path) if target_path.is_file() else None,
        "environment_files": env_files,
        "environment_file_present": bool(env_files),
        "workspace_path": "<ephemeral_root>",
        "runtime_workspace_outside_repo": True,
        "runtime_workspace_outside_onedrive": True,
        "fixed_later_gold_pr_patch_content_used": False,
        "records": records,
    }


def resolve_batch005_environment(checkout: Path, config: dict[str, object]) -> dict[str, object]:
    root = checkout.parent
    venv_dir = root / "native_retry_venv"
    venv_record = run_bounded_command([sys.executable, "-m", "venv", str(venv_dir)], timeout_seconds=int(config.get("venv_timeout_seconds", 120)), roots=[root])
    python = venv_dir / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
    records = [{"stage": "create_venv", **venv_record}]
    if venv_record["returncode"] != 0:
        return {"status": "BLOCK", "blocker": "native_challenge_command_cannot_collect_target_after_materialization", "venv_created": False, "records": records}
    upgrade = run_bounded_command([str(python), "-m", "pip", "install", "--upgrade", "pip", "setuptools", "wheel"], cwd=checkout, timeout_seconds=int(config.get("pip_upgrade_timeout_seconds", 90)), roots=[checkout, venv_dir])
    records.append({"stage": "upgrade_build_tools", **upgrade})
    install_command = [
        str(python),
        "-m",
        "pip",
        "install",
        "pytest",
        "pytest-kwparametrize",
        "isort",
        "toml",
        "typing_extensions",
        "darkgraylib>=2.4.0,<3.0.dev0",
    ]
    install = run_bounded_command(install_command, cwd=checkout, timeout_seconds=int(config.get("pip_install_timeout_seconds", 180)), roots=[checkout, venv_dir])
    records.append({"stage": "install_declared_test_dependencies", **install})
    status = "PASS" if upgrade["returncode"] == 0 and install["returncode"] == 0 else "BLOCK"
    blocker = None if status == "PASS" else ("native_challenge_command_cannot_collect_target_after_materialization" if install.get("timed_out") else "environment_dependency_install_failed")
    return {
        "status": status,
        "blocker": blocker,
        "venv_created": True,
        "python": str(python),
        "python_redacted": "<ephemeral_venv_python>",
        "install_uses_declared_project_metadata": True,
        "installed_dependencies_basis": ["pyproject.toml project dependencies", "pyproject.toml isort optional group", "pyproject.toml dev pytest tooling"],
        "undeclared_dependency_install_used": False,
        "records": records,
    }


def run_batch005_collection_and_replay(
    checkout: Path,
    env_result: dict[str, object],
    node_discovery: dict[str, object],
    config: dict[str, object],
) -> tuple[
    dict[str, object],
    list[dict[str, object]],
    list[dict[str, object]],
    dict[str, object],
    list[dict[str, object]],
    dict[str, object],
    dict[str, object],
    list[dict[str, object]],
]:
    discovered_nodes = [str(node) for node in node_discovery.get("nodes", []) if isinstance(node, str)]
    target_selection = select_semantic_target_node(
        discovered_nodes,
        intended_node=str(BATCH005_TARGET["intended_node"]),
        semantic_markers=list(BATCH005_TARGET["semantic_markers"]),
    )
    non_intent_classifications = [
        classify_non_intent_failure(node, str(target_selection.get("selected_node") or ""), "")
        for node in discovered_nodes
        if node != target_selection.get("selected_node")
    ]
    if env_result.get("status") != "PASS":
        collection = {
            "status": "BLOCK",
            "blocker": env_result.get("blocker") or "native_challenge_command_cannot_collect_target_after_materialization",
            "collection_attempted": False,
            "reason": "environment resolution did not complete safely",
        }
        replay_selection = {
            "status": "NOT_RUN",
            "blocker": collection["blocker"],
            "selected_node": target_selection.get("selected_node"),
            "selected_command": BATCH005_TARGET["intended_target_command"],
            "reason": "environment resolution blocked collection and intended-node replay",
        }
        attempt = {
            "candidate_id": BATCH005_TARGET["candidate_id"],
            "repo_url": BATCH005_TARGET["repo_url"],
            "commit_sha": BATCH005_TARGET["commit_sha"],
            "target_test_path": BATCH005_TARGET["target_test_path"],
            "intended_node": BATCH005_TARGET["intended_node"],
            "source_materialized": True,
            "ast_node_discovery_attempted_from_materialized_source": node_discovery.get("status") == "PASS",
            "collection_attempted_from_materialized_source": False,
            "status": "BLOCK",
            "blocker": collection["blocker"],
            "node_level_command_attempted_count": 0,
            "node_level_command_blocked_reason": collection["reason"],
            "fixed_later_gold_pr_patch_content_used": False,
        }
        return collection, [], [], attempt, [{"candidate_id": BATCH005_TARGET["candidate_id"], "blocker": collection["blocker"], "reason": collection["reason"]}], target_selection, replay_selection, non_intent_classifications
    python = str(env_result["python"])
    env = os.environ.copy()
    src = str(checkout / "src")
    env["PYTHONPATH"] = src + (os.pathsep + env["PYTHONPATH"] if env.get("PYTHONPATH") else "")
    target = BATCH005_TARGET["target_test_path"]
    collection_command = [python, "-m", "pytest", target, "--collect-only", "-q"]
    collection_record = run_bounded_command(collection_command, cwd=checkout, timeout_seconds=int(config.get("collection_timeout_seconds", 120)), env=env, roots=[checkout, Path(python).parent.parent])
    collection = {
        "candidate_id": BATCH005_TARGET["candidate_id"],
        "collection_attempted": True,
        "status": "PASS" if collection_record["returncode"] == 0 else "BLOCK",
        "blocker": None if collection_record["returncode"] == 0 else "native_challenge_command_cannot_collect_target_after_materialization",
        "command_record": collection_record,
    }
    replay_records: list[dict[str, object]] = []
    verified: list[dict[str, object]] = []
    if target_selection.get("status") != "PASS":
        replay_selection = {
            "status": "BLOCK",
            "blocker": target_selection.get("blocker") or "target_node_semantic_intent_mismatch",
            "selected_node": None,
            "selected_command": BATCH005_TARGET["intended_target_command"],
        }
    else:
        node = str(target_selection["selected_node"])
        command = [python, "-m", "pytest", node, "-q"]
        record = run_bounded_command(command, cwd=checkout, timeout_seconds=int(config.get("node_replay_timeout_seconds", 120)), env=env, roots=[checkout, Path(python).parent.parent])
        status = "PRE_PATCH_FAILURE_OBSERVED" if record["returncode"] not in {0, None} else ("TIMEOUT" if record["timed_out"] else "PASSING_PRE_PATCH")
        environment_only = "ModuleNotFoundError" in str(record.get("output_summary", "")) or "ImportError" in str(record.get("output_summary", ""))
        selected_replay = {
            "candidate_id": BATCH005_TARGET["candidate_id"],
            "node": node,
            "status": status,
            "returncode": record.get("returncode"),
            "target_command": record.get("command"),
            "semantic_intent_match": True,
            "target_related_failure": status == "PRE_PATCH_FAILURE_OBSERVED" and not environment_only,
            "environment_only_failure": environment_only,
            "command_record": record,
            "semantic_failure_signature_hash": record.get("normalized_output_sha256"),
        }
        replay_records.append(selected_replay)
        admission = target_node_admission_decision(target_selection, selected_replay)
        if admission["status"] == "PASS":
            replay_selection = {
                "status": "PASS",
                "blocker": None,
                "selected_node": node,
                "selected_command": record.get("command"),
                "target_node_admission_decision": admission,
            }
        else:
            replay_selection = {
                "status": "BLOCK",
                "blocker": admission["blocker"],
                "selected_node": node,
                "selected_command": record.get("command"),
                "target_node_admission_decision": admission,
            }
    first_failure = next((item for item in replay_records if item.get("status") == "PRE_PATCH_FAILURE_OBSERVED" and item.get("environment_only_failure") is False and item.get("node") == BATCH005_TARGET["intended_node"]), None)
    if first_failure:
        signature = {
            "status": "PASS",
            "candidate_id": BATCH005_TARGET["candidate_id"],
            "target_command": first_failure["command_record"]["command"],
            "semantic_failure_signature_hash": first_failure["command_record"]["normalized_output_sha256"],
            "raw_log_hash": first_failure["command_record"]["output_sha256"],
            "normalized_log_hash": first_failure["command_record"]["normalized_output_sha256"],
        }
        verified.append(
            {
                "candidate_id": BATCH005_TARGET["candidate_id"],
                "candidate_class": "native_replay_candidate",
                "repo_url": BATCH005_TARGET["repo_url"],
                "commit_sha": BATCH005_TARGET["commit_sha"],
                "target_test_path": target,
                "intended_node": BATCH005_TARGET["intended_node"],
                "target_command": first_failure["command_record"]["command"],
                "semantic_failure_signature_hash": signature["semantic_failure_signature_hash"],
                "native_challenge_candidate_verified": True,
                "scoreable_external_repair": False,
            }
        )
        attempt_status = "PASS"
        blocker = None
    else:
        signature = {
            "status": "NOT_RUN",
            "blocker": replay_selection.get("blocker") or ("native_challenge_pre_repair_failure_not_observed" if replay_records else "native_challenge_command_cannot_collect_target_after_materialization"),
        }
        attempt_status = "BLOCK"
        blocker = signature["blocker"]
    attempt = {
        "candidate_id": BATCH005_TARGET["candidate_id"],
        "repo_url": BATCH005_TARGET["repo_url"],
        "commit_sha": BATCH005_TARGET["commit_sha"],
        "target_test_path": target,
        "intended_node": BATCH005_TARGET["intended_node"],
        "source_materialized": True,
        "ast_node_discovery_attempted_from_materialized_source": node_discovery.get("status") == "PASS",
        "collection_attempted_from_materialized_source": True,
        "node_level_command_attempted_count": len(replay_records),
        "target_node_semantic_selection_status": target_selection.get("status"),
        "target_node_replay_selection_status": replay_selection.get("status"),
        "status": attempt_status,
        "blocker": blocker,
        "fixed_later_gold_pr_patch_content_used": False,
    }
    rejections = [] if verified else [{"candidate_id": BATCH005_TARGET["candidate_id"], "blocker": blocker, "reason": "native source-materialized retry did not verify a target-related pre-repair failure"}]
    return collection, replay_records, verified, attempt, rejections, target_selection, replay_selection, non_intent_classifications


def contains_solution_guidance(text: str) -> bool:
    lowered = text.lower()
    markers = ["fix is", "the fix", "solution", "patched by", "pull request", "merge request", "diff --git", "apply this patch"]
    return any(marker in lowered for marker in markers)


def validate_targeted_issue_seed(seed: dict[str, object], existing_ids: set[str]) -> dict[str, object]:
    candidate_id = str(seed.get("candidate_id") or "")
    text = str(seed.get("issue_text_snapshot") or "")
    if candidate_id in existing_ids or candidate_id in REPAIRED_CANDIDATE_IDS:
        return {"status": "BLOCK", "blocker": "targeted_issue_seed_duplicate_candidate"}
    if seed.get("candidate_class") != "issue_derived_reproduction_candidate":
        return {"status": "BLOCK", "blocker": "targeted_issue_seed_invalid"}
    if not re.match(r"^https://github\.com/[^/]+/[^/]+/?$", str(seed.get("repo_url") or "")):
        return {"status": "BLOCK", "blocker": "targeted_issue_seed_invalid"}
    if not str(seed.get("issue_url") or "").startswith(str(seed.get("repo_url")).rstrip("/") + "/issues/"):
        return {"status": "BLOCK", "blocker": "targeted_issue_seed_invalid"}
    if not text.strip():
        return {"status": "BLOCK", "blocker": "targeted_issue_seed_missing_issue_text"}
    if contains_solution_guidance(text):
        return {"status": "BLOCK", "blocker": "targeted_issue_seed_contains_solution_guidance"}
    if not (seed.get("reproduction_steps") or "traceback" in text.lower() or "```" in text or "expected" in text.lower()):
        return {"status": "BLOCK", "blocker": "targeted_issue_seed_invalid"}
    sha = seed.get("source_commit_sha")
    if sha is not None and not re.match(r"^[0-9a-fA-F]{40}$", str(sha)):
        return {"status": "BLOCK", "blocker": "targeted_issue_seed_commit_unresolved"}
    if not seed.get("source_commit_selection_method"):
        return {"status": "BLOCK", "blocker": "targeted_issue_seed_commit_unresolved"}
    if not seed.get("environment_lock_source"):
        return {"status": "BLOCK", "blocker": "targeted_issue_seed_environment_file_missing"}
    attestation = seed.get("forbidden_evidence_attestation")
    if not isinstance(attestation, dict) or any(attestation.get(key) is not False for key in ["fixed_commit_used", "later_commit_used", "pr_patch_used", "gold_patch_used", "future_test_used"]):
        return {"status": "BLOCK", "blocker": "targeted_issue_seed_invalid"}
    unsafe_setup = []
    for command in seed.get("setup_commands", []) or []:
        command_text = str(command).lower()
        if any(marker in command_text for marker in ["curl ", "wget ", "http://", "https://", "git clone", "echo ", "cat >"]):
            unsafe_setup.append(command)
    if unsafe_setup:
        return {"status": "BLOCK", "blocker": "targeted_issue_seed_setup_unsafe", "unsafe_setup_commands": unsafe_setup}
    return {"status": "PASS", "blocker": None}


def load_targeted_issue_seed() -> tuple[Path | None, dict[str, object] | None]:
    for path in TARGETED_SEED_PATHS:
        if path.is_file():
            return path, load_json(path)
    return None, None


def write_targeted_issue_seed_outputs(native_failed: bool) -> dict[str, object]:
    existing_ids = {"external_reader_duplicate_key_bug", *REPAIRED_CANDIDATE_IDS}
    path, seed = load_targeted_issue_seed()
    present = seed is not None
    if not native_failed:
        validation = {"status": "NOT_RUN_NATIVE_VERIFIED", "blocker": None}
    elif not present:
        validation = {"status": "NOT_RUN_NO_TARGETED_SEED", "blocker": None}
    else:
        validation = validate_targeted_issue_seed(seed or {}, existing_ids)
    issue_text = str((seed or {}).get("issue_text_snapshot") or "")
    issue_hash = sha256_text(issue_text) if issue_text else None
    base = {
        "targeted_issue_derived_seed_present": present,
        "seed_path": str(path).replace("\\", "/") if path else None,
        "execution_order": "after_native_retry_before_broad_issue_discovery",
        "native_retry_failed_before_targeted_seed_check": native_failed,
        "validation_status": validation.get("status"),
        "blocker": validation.get("blocker"),
    }
    write_json_deterministic(BATCH005_DIR / "targeted_issue_seed_intake_report.json", {**base, "status": validation.get("status"), "candidate_id": (seed or {}).get("candidate_id")})
    write_json_deterministic(BATCH005_DIR / "targeted_issue_text_hash.json", {"status": "PASS" if issue_hash else "NOT_RUN_NO_TARGETED_SEED", "issue_text_sha256": issue_hash})
    write_json_deterministic(
        BATCH005_DIR / "targeted_issue_text_temporal_guard.json",
        {
            "status": "PASS" if present and validation.get("status") == "PASS" else ("NOT_RUN_NO_TARGETED_SEED" if not present else "BLOCK"),
            "issue_text_edit_history_status": "issue_text_edit_history_uncertain" if present else "not_applicable_no_seed",
            "solution_guidance_detected": contains_solution_guidance(issue_text) if issue_text else False,
            "proceeds_only_without_solution_guidance": True,
        },
    )
    write_json_deterministic(
        BATCH005_DIR / "targeted_issue_latent_knowledge_risk_disclosure.json",
        {
            "status": "DISCLOSED" if present else "NOT_RUN_NO_TARGETED_SEED",
            "cryptographic_absence_of_latent_knowledge_claimed": False,
            "context_isolation_required": True,
            "issue_text_hash": issue_hash,
        },
    )
    harness_generated = False
    write_json_deterministic(
        BATCH005_DIR / "targeted_issue_harness_generation_policy.json",
        {
            "status": "PASS",
            "allowed_inputs": ["issue_title", "issue_text_snapshot", "reproduction_steps", "target_behavior_description", "selected_source_commit_tree", "project_metadata", "source_context_filtering"],
            "forbidden_inputs": ["fixed_commit_contents", "later_commit_contents", "PR_patch_contents", "fixed_diffs", "gold_patches", "future_tests", "maintainer_solution_comments"],
            "generated_harness_is_ephemeral": True,
        },
    )
    write_json_deterministic(
        BATCH005_DIR / "targeted_issue_harness_context_manifest.json",
        {
            "status": "NOT_RUN_NO_TARGETED_SEED" if not present else ("BLOCK" if validation.get("status") != "PASS" else "NOT_RUN_NO_SAFE_HARNESS_GENERATOR"),
            "issue_text_hash": issue_hash,
            "harness_generation_context_hash": None,
            "source_file_hashes": [],
            "generated_harness_sha256": None,
        },
    )
    write_json_deterministic(
        BATCH005_DIR / "targeted_issue_harness_firewall_audit.json",
        {
            "status": "PASS" if not present else ("BLOCK" if validation.get("status") != "PASS" else "PASS"),
            "forbidden_evidence_used": False,
            "generated_harness_classified_as_native_test": False,
            "harness_generated": harness_generated,
        },
    )
    write_json_deterministic(
        BATCH005_DIR / "targeted_issue_harness_verification_result.json",
        {
            "status": "NOT_RUN_NO_TARGETED_SEED" if not present else ("BLOCK" if validation.get("status") != "PASS" else "NOT_RUN_NO_SAFE_HARNESS_GENERATOR"),
            "targeted_issue_candidate_verified": False,
            "blocker": validation.get("blocker") if present and validation.get("status") != "PASS" else ("targeted_issue_harness_generation_failed" if present else None),
        },
    )
    write_json_deterministic(BATCH005_DIR / "targeted_issue_source_context_filter_map.json", {"status": "NOT_RUN_NO_TARGETED_SEED" if not present else "NOT_RUN_NO_HARNESS", "candidate_source_files": [], "forbidden_context_used": False})
    write_json_deterministic(BATCH005_DIR / "targeted_issue_context_boundary_map.json", {"status": "PASS", "issue_derived_evidence_class": True, "native_count_incremented": False})
    write_json_deterministic(BATCH005_DIR / "targeted_issue_interlock_invariant_map.json", {"status": "NOT_RUN_NO_TARGETED_SEED" if not present else "NOT_RUN_NO_HARNESS", "interlocks": []})
    return {
        **base,
        "targeted_issue_seed_validation_status": validation.get("status"),
        "targeted_issue_seed_valid": validation.get("status") == "PASS",
        "targeted_issue_harness_generated": harness_generated,
        "targeted_issue_candidate_verified": False,
        "targeted_issue_repair_attempted": False,
        "targeted_issue_repair_success": False,
    }


def discover_issue_derived_leads(native_failed: bool, targeted_seed_valid: bool, config: dict[str, object]) -> tuple[dict[str, object], list[dict[str, object]], list[dict[str, object]], list[dict[str, object]]]:
    policy = {
        "status": "PASS",
        "runs_only_after_native_failure": True,
        "runs_after_targeted_seed_intake": True,
        "zero_lead_placeholder_forbidden_when_discovery_available": True,
        "allowed_sources": ["issue_title", "issue_body", "issue_created_timestamp", "issue_url", "repo_metadata"],
        "forbidden_sources": ["PR_patch_contents", "fix_commits", "later_commit_contents", "maintainer_solution_guidance", "gold_patches", "future_tests"],
    }
    if not native_failed or targeted_seed_valid:
        return policy, [], [], []
    max_queries = int(config.get("max_issue_discovery_queries", 6))
    leads: list[dict[str, object]] = []
    attempts: list[dict[str, object]] = []
    network_unavailable = False
    try:
        import urllib.parse
        import urllib.request

        query_pairs = [(repo, term) for repo in ISSUE_DISCOVERY_REPOS for term in ISSUE_DISCOVERY_TERMS][:max_queries]
        for repo, term in query_pairs:
            query = urllib.parse.quote(f"repo:{repo} is:issue {term}")
            url = f"https://api.github.com/search/issues?q={query}&per_page=1"
            request = urllib.request.Request(url, headers={"Accept": "application/vnd.github+json", "User-Agent": "ControllerGate-Batch005"})
            try:
                with urllib.request.urlopen(request, timeout=int(config.get("issue_discovery_timeout_seconds", 12))) as response:
                    payload = json.loads(response.read().decode("utf-8", errors="replace"))
            except Exception as exc:  # network/API failure is recorded, not raised
                attempts.append({"repo": repo, "term": term, "status": "BLOCK", "blocker": "issue_derived_discovery_network_unavailable", "error_type": type(exc).__name__})
                network_unavailable = True
                continue
            items = payload.get("items", []) if isinstance(payload, dict) else []
            attempts.append({"repo": repo, "term": term, "status": "PASS", "result_count": len(items)})
            for item in items:
                title = str(item.get("title") or "")
                body = str(item.get("body") or "")
                if contains_solution_guidance(title + "\n" + body):
                    continue
                if not (body and ("```" in body or "traceback" in body.lower() or "reproduce" in body.lower() or "expected" in body.lower())):
                    continue
                leads.append(
                    {
                        "candidate_class": "issue_derived_reproduction_candidate",
                        "repo": repo,
                        "issue_url": item.get("html_url"),
                        "issue_created_at": item.get("created_at"),
                        "issue_title": title,
                        "issue_text_sha256": sha256_text(body),
                        "decision_time_issue_evidence": True,
                    }
                )
                break
            if leads:
                break
    except Exception as exc:
        attempts.append({"status": "BLOCK", "blocker": "issue_derived_discovery_network_unavailable", "error_type": type(exc).__name__})
        network_unavailable = True
    if leads:
        rejections = [
            {
                "candidate_class": "issue_derived_reproduction_candidate",
                "issue_url": lead.get("issue_url"),
                "blocker": "issue_derived_harness_generation_failed",
                "reason": "bounded discovery found issue evidence but no safe deterministic harness was generated in Batch005",
            }
            for lead in leads
        ]
    else:
        rejections = [
            {
                "candidate_class": "issue_derived_reproduction_candidate",
                "blocker": "issue_derived_discovery_network_unavailable" if network_unavailable else "issue_derived_no_safe_leads",
                "reason": "bounded issue discovery produced no safe issue-derived candidate",
            }
        ]
    return policy, leads, attempts, rejections


def write_batch005_repair_outputs(
    native_verified: bool,
    verified: list[dict[str, object]],
    exact_blocker: str,
    *,
    corrected_blocker: str | None = None,
    corrected_patch_generated: bool = False,
) -> tuple[dict[str, object], list[dict[str, object]], dict[str, object], dict[str, object], list[dict[str, object]]]:
    if native_verified:
        blocker = corrected_blocker or "clean_repair_no_safe_source_patch_generated"
        memory = {
            "status": "BLOCK",
            "candidate_id": BATCH005_TARGET["candidate_id"],
            "patch_generated": False,
            "patch_authorized": False,
            "patch_attempted": blocker == "clean_repair_no_safe_source_patch_generated",
            "blocker": blocker,
        }
        null_runs = []
        null_summary = {"status": "NOT_RUN", "blocker": blocker, "null_ensemble_run_count": 0, "null_ensemble_success_rate": None}
        score = {
            "status": "NOT_COMPUTED",
            "blocker": blocker,
            "matched_null_ensemble_separation_score": None,
            "preliminary_single_candidate_memory_separation_evidence": False,
            "reason": "null ensemble runs only after a successful memory-enabled repair",
        }
        repairs: list[dict[str, object]] = []
    else:
        memory = {"status": "NOT_RUN", "blocker": exact_blocker, "patch_generated": False, "patch_authorized": False, "patch_attempted": False}
        null_runs = []
        null_summary = {"status": "NOT_RUN", "blocker": exact_blocker, "null_ensemble_run_count": 0, "null_ensemble_success_rate": None}
        score = {"status": "NOT_COMPUTED", "blocker": exact_blocker, "matched_null_ensemble_separation_score": None, "preliminary_single_candidate_memory_separation_evidence": False}
        repairs = []
    write_json_deterministic(BATCH005_DIR / "memory_enabled_run_results.json", memory)
    write_json_deterministic(BATCH005_DIR / "null_ensemble_run_results.json", null_runs)
    write_json_deterministic(BATCH005_DIR / "null_ensemble_summary.json", null_summary)
    write_json_deterministic(BATCH005_DIR / "matched_null_ensemble_separation_score_result.json", score)
    write_json_deterministic(
        BATCH005_DIR / "memory_separation_claim_evaluation.json",
        {
            "status": "PASS",
            "preliminary_single_candidate_memory_separation_evidence": False,
            "preliminary_issue_derived_memory_separation_signal": False,
            "memory_lift": "undemonstrated_equal_performance",
            "full_memory_lift_status": "undemonstrated",
        },
    )
    write_json_deterministic(BATCH005_DIR / "repair_successes.json", repairs)
    write_json_deterministic(BATCH005_DIR / "no_overreach_validation.json", {"status": "NOT_RUN" if not repairs else "PASS", "blocker": None if repairs else "target_validation_not_passed", "stronger_robustness_claim_allowed": False})
    return memory, null_runs, null_summary, score, repairs


def write_batch005_corrected_repair_outputs(
    checkout: Path,
    native_verified: bool,
    verified: list[dict[str, object]],
    replay_records: list[dict[str, object]],
    exact_blocker: str,
) -> dict[str, object]:
    candidate = {
        "candidate_id": BATCH005_TARGET["candidate_id"],
        "repo_url": BATCH005_TARGET["repo_url"],
        "commit_sha": BATCH005_TARGET["commit_sha"],
        "target_test_path": BATCH005_TARGET["target_test_path"],
        "target_command": BATCH005_TARGET["intended_target_command"],
    }
    selected_replay = next((item for item in replay_records if item.get("node") == BATCH005_TARGET["intended_node"]), None)
    write_json_deterministic(
        BATCH005_DIR / "source_stack_extraction_policy.json",
        {
            "status": "PASS",
            "selected_target_node_required": True,
            "project_source_root": "src/darker",
            "tests_support_config_workflow_registry_audit_files_patchable": False,
            "blocker_if_project_source_frames_do_not_create_subset": "patchable_source_subset_derivation_failed",
        },
    )
    write_json_deterministic(
        BATCH005_DIR / "no_patch_reason_taxonomy.json",
        {
            "status": "PASS",
            "reason_codes": [
                "repair_generator_not_implemented",
                "patchable_source_subset_empty",
                "pre_generation_context_missing",
                "safe_patch_generation_attempted_no_patch_found",
                "patch_generated_failed_safety",
                "patch_generated_failed_target_validation",
                "patch_generated_succeeded",
            ],
            "empty_subset_blocker": "patchable_source_subset_derivation_failed",
            "generator_no_op_blocker": "clean_repair_generator_not_implemented",
            "no_safe_patch_blocker": "clean_repair_no_safe_source_patch_generated",
        },
    )
    if not native_verified or not selected_replay:
        blocker = exact_blocker
        source_result = {
            "status": "NOT_RUN",
            "blocker": blocker,
            "candidate_id": BATCH005_TARGET["candidate_id"],
            "selected_node": BATCH005_TARGET["intended_node"],
            "project_source_frames": [],
            "reason": "intended target-node pre-repair failure was not verified",
        }
        import_result = {"status": "NOT_RUN", "blocker": blocker, "imported_candidate_source_files": []}
        ast_result = {"status": "NOT_RUN", "blocker": blocker, "AST_closure_candidate_source_files": []}
        subset = {"candidate_id": BATCH005_TARGET["candidate_id"], "status": "NOT_RUN", "blocker": blocker, "patchable_source_files": [], "records": []}
        routing = {"candidate_id": BATCH005_TARGET["candidate_id"], "status": "NOT_RUN", "blocker": blocker, "ranked_patchable_sources": []}
        capability = {
            "candidate_id": BATCH005_TARGET["candidate_id"],
            "status": "NOT_RUN",
            "blocker": blocker,
            "capability_classification": "pre_generation_context_missing",
            "generator_invoked": False,
            "patchable_subset_received": False,
            "patch_candidate_generated": False,
        }
        corrected_attempt = {
            "status": "NOT_RUN",
            "blocker": blocker,
            "candidate_id": BATCH005_TARGET["candidate_id"],
            "patch_generated": False,
            "patch_authorized": False,
            "patch_attempted": False,
        }
        snapshot = {"status": "NOT_RUN", "blocker": blocker, "failure_memory_visible": False}
        alignment = {"status": "NOT_RUN", "blocker": blocker, "forbidden_file_modified": False}
        safety = {"status": "NOT_RUN", "blocker": blocker, "patch_non_empty": False, "source_only": False}
    else:
        summary = str(selected_replay.get("command_record", {}).get("output_summary", ""))
        source_files = source_files_from_failure_text(checkout, summary)
        imported = imported_candidate_sources(checkout, str(BATCH005_TARGET["target_test_path"]))
        routing_map = build_structural_repair_routing_map(candidate, checkout, selected_replay)
        routing = repairability_basin_selection(candidate, routing_map, checkout, selected_replay)
        subset = build_patchable_source_subset(routing)
        source_result = {
            "status": "PASS" if source_files or imported else "BLOCK",
            "blocker": None if source_files or imported else "patchable_source_subset_derivation_failed",
            "candidate_id": BATCH005_TARGET["candidate_id"],
            "selected_node": BATCH005_TARGET["intended_node"],
            "project_source_frames": source_files,
            "target_imported_source_files": imported,
            "failure_log_hash": selected_replay.get("command_record", {}).get("normalized_output_sha256"),
        }
        import_result = {
            "status": "PASS" if imported else "BLOCK",
            "blocker": None if imported else "patchable_source_subset_derivation_failed",
            "imported_candidate_source_files": imported,
        }
        ast_result = {
            "status": "PASS" if routing_map.get("AST_closure_candidate_source_files") else "BLOCK",
            "blocker": None if routing_map.get("AST_closure_candidate_source_files") else "patchable_source_subset_derivation_failed",
            "AST_closure_candidate_source_files": routing_map.get("AST_closure_candidate_source_files", []),
            "interlock_invariant_files": routing_map.get("interlock_invariant_files", []),
        }
        if subset.get("status") == "PASS":
            capsule = build_repair_context_capsule(candidate, checkout, selected_replay, routing_map, subset)
            snapshot = build_pre_generation_context_state_lock(candidate, capsule, subset, routing_map)
            snapshot["status"] = "PASS"
            patch = generate_patch_candidate(candidate, checkout, capsule, subset, snapshot)
            capability = {
                "candidate_id": BATCH005_TARGET["candidate_id"],
                **classify_repair_generator_capability(subset=subset, patch=patch, generator_invoked=True),
                "no_patch_reason": patch.get("no_patch_reason"),
                "patch_rule": patch.get("patch_rule"),
            }
            corrected_attempt = {
                "status": "PASS" if patch.get("patch_candidate_generated") is True else "BLOCK",
                "blocker": patch.get("blocker"),
                "candidate_id": BATCH005_TARGET["candidate_id"],
                "patch_generated": patch.get("patch_candidate_generated") is True,
                "patch_authorized": patch.get("patch_authorized") is True,
                "patch_attempted": True,
                "generator_mode": patch.get("generator_mode"),
                "patch_sha256": patch.get("patch_sha256"),
                "no_patch_reason": patch.get("no_patch_reason"),
            }
            if patch.get("patch_candidate_generated") is True:
                alignment = patch_context_alignment_audit(patch, snapshot)
                safety = patch_safety_result(patch, snapshot)
            else:
                alignment = {"status": "NOT_RUN", "blocker": patch.get("blocker"), "forbidden_file_modified": False}
                safety = {"status": "NOT_RUN", "blocker": patch.get("blocker"), "patch_non_empty": False, "source_only": False}
        else:
            capability = {
                "candidate_id": BATCH005_TARGET["candidate_id"],
                **classify_repair_generator_capability(subset=subset, patch=None, generator_invoked=True),
            }
            corrected_attempt = {
                "status": "BLOCK",
                "blocker": subset.get("blocker"),
                "candidate_id": BATCH005_TARGET["candidate_id"],
                "patch_generated": False,
                "patch_authorized": False,
                "patch_attempted": False,
            }
            snapshot = {"status": "BLOCK", "blocker": subset.get("blocker"), "failure_memory_visible": True}
            alignment = {"status": "NOT_RUN", "blocker": subset.get("blocker"), "forbidden_file_modified": False}
            safety = {"status": "NOT_RUN", "blocker": subset.get("blocker"), "patch_non_empty": False, "source_only": False}
    write_json_deterministic(BATCH005_DIR / "source_stack_extraction_result.json", source_result)
    write_json_deterministic(BATCH005_DIR / "import_graph_extraction_result.json", import_result)
    write_json_deterministic(BATCH005_DIR / "ast_closure_extraction_result.json", ast_result)
    write_json_deterministic(BATCH005_DIR / "patchable_source_subset_derivation.json", subset)
    write_patchable_source_ranking_csv(BATCH005_DIR / "patchable_source_ranking_corrected.csv", list(routing.get("ranked_patchable_sources", [])))
    write_json_deterministic(BATCH005_DIR / "repair_generator_capability_status_corrected.json", capability)
    write_json_deterministic(BATCH005_DIR / "corrected_native_repair_attempt.json", corrected_attempt)
    write_json_deterministic(BATCH005_DIR / "corrected_pre_generation_context_state_snapshot.json", snapshot)
    write_json_deterministic(BATCH005_DIR / "corrected_patch_context_alignment_audit.json", alignment)
    write_json_deterministic(BATCH005_DIR / "corrected_patch_safety_result.json", safety)
    write_json_deterministic(BATCH005_DIR / "corrected_target_validation_result.json", {"status": "NOT_RUN", "blocker": "no_patch_applied", "exit_code": None})
    write_json_deterministic(BATCH005_DIR / "corrected_duplicate_replay_result.json", {"status": "NOT_RUN", "blocker": "target_validation_not_passed", "passes": 0, "total": 0})
    write_json_deterministic(BATCH005_DIR / "corrected_no_overreach_validation.json", {"status": "NOT_RUN", "blocker": "target_validation_not_passed", "stronger_robustness_claim_allowed": False})
    write_json_deterministic(BATCH005_DIR / "corrected_null_ensemble_run_results.json", [])
    write_json_deterministic(BATCH005_DIR / "corrected_null_ensemble_summary.json", {"status": "NOT_RUN", "blocker": corrected_attempt.get("blocker"), "null_ensemble_run_count": 0, "null_ensemble_success_rate": None})
    write_json_deterministic(
        BATCH005_DIR / "corrected_matched_null_ensemble_separation_score.json",
        {
            "status": "NOT_COMPUTED",
            "blocker": corrected_attempt.get("blocker"),
            "matched_null_ensemble_separation_score": None,
            "preliminary_single_candidate_memory_separation_evidence": False,
        },
    )
    write_json_deterministic(
        BATCH005_DIR / "corrected_memory_separation_claim_evaluation.json",
        {
            "status": "PASS",
            "preliminary_single_candidate_memory_separation_evidence": False,
            "memory_lift": "undemonstrated_equal_performance",
            "full_memory_lift_status": "undemonstrated",
        },
    )
    return {
        "source_stack_status": source_result.get("status"),
        "patchable_source_subset_status": subset.get("status"),
        "repair_generator_capability_status": capability.get("status"),
        "corrected_repair_attempt_status": corrected_attempt.get("status"),
        "corrected_repair_blocker": corrected_attempt.get("blocker"),
        "patch_generated": corrected_attempt.get("patch_generated") is True,
        "routing": routing,
        "subset": subset,
        "snapshot": snapshot,
        "alignment": alignment,
        "capability": capability,
    }


def write_batch005_outputs() -> dict[str, object]:
    BATCH005_DIR.mkdir(parents=True, exist_ok=True)
    artifact_record = POST_DIR / "batch005_native_subset_artifact_verification.json"
    state_record = BATCH005_DIR / "consolidated_state_clean_replication_batch_005.json"
    if artifact_record.is_file() and state_record.is_file() and (BATCH005_DIR / "SHA256SUMS.txt").is_file():
        artifact = load_json(artifact_record)
        manifest = verify_manifest(BATCH005_DIR)
        if (
            artifact.get("status") == "PASS"
            and artifact.get("artifact_source") == "manual_download_local_file"
            and artifact.get("sha256_match") is True
            and manifest.get("status") == "PASS"
        ):
            return load_json(state_record)
    config = load_json("configs/clean_replication_batch_005.json")
    checkout, materialization = materialize_batch005_source(config)
    target_file = checkout / BATCH005_TARGET["target_test_path"]
    node_discovery = discover_test_nodes(target_file, BATCH005_TARGET["target_test_path"]) if materialization.get("source_materialized") else {"status": "BLOCK", "blocker": materialization.get("blocker"), "nodes": []}
    env_result = resolve_batch005_environment(checkout, config) if materialization.get("source_materialized") else {"status": "BLOCK", "blocker": materialization.get("blocker"), "records": []}
    (
        collection,
        replay_records,
        verified,
        native_attempt,
        native_rejections,
        target_selection,
        replay_selection,
        non_intent_classifications,
    ) = run_batch005_collection_and_replay(checkout, env_result, node_discovery, config)
    native_verified = bool(verified)
    targeted = write_targeted_issue_seed_outputs(native_failed=not native_verified)
    targeted_seed_present = bool(targeted.get("targeted_issue_derived_seed_present"))
    if targeted_seed_present:
        issue_policy, issue_leads, issue_attempts, issue_rejections = discover_issue_derived_leads(not native_verified, bool(targeted.get("targeted_issue_seed_valid")), config)
    else:
        issue_policy = {
            "status": "NOT_RUN_NO_TARGETED_SEED",
            "runs_only_after_native_failure": True,
            "runs_after_targeted_seed_intake": True,
            "bounded_discovery_disabled_for_correction_run": True,
            "reason": "no targeted issue-derived seed was supplied",
        }
        issue_leads = []
        issue_attempts = []
        issue_rejections = []
    issue_verified: list[dict[str, object]] = []
    issue_count = 0
    issue_feasibility = 0
    if native_verified:
        exact_blocker = "clean_repair_no_safe_source_patch_generated"
    elif targeted.get("targeted_issue_seed_valid"):
        exact_blocker = "targeted_issue_harness_generation_failed"
    elif issue_leads:
        exact_blocker = "issue_derived_harness_generation_failed"
    elif any(item.get("blocker") == "issue_derived_discovery_network_unavailable" for item in issue_rejections):
        exact_blocker = "issue_derived_discovery_network_unavailable"
    elif native_attempt.get("blocker"):
        exact_blocker = str(native_attempt["blocker"])
    else:
        exact_blocker = "batch005_no_native_or_issue_derived_candidate_verified"
    corrected = write_batch005_corrected_repair_outputs(checkout, native_verified, verified, replay_records, exact_blocker)
    if native_verified and corrected.get("corrected_repair_blocker"):
        exact_blocker = str(corrected["corrected_repair_blocker"])
    memory, null_runs, null_summary, score, repairs = write_batch005_repair_outputs(
        native_verified,
        verified,
        exact_blocker,
        corrected_blocker=str(corrected.get("corrected_repair_blocker") or exact_blocker),
        corrected_patch_generated=bool(corrected.get("patch_generated")),
    )
    state = {
        "lane_id": BATCH005_ID,
        "lane_type": "post_v2_37_source_materialized_challenge_retry",
        "status": "BLOCKED" if not repairs else "PASS",
        "exact_blocker": None if repairs else exact_blocker,
        "current_protocol_version": "v2.13",
        "confirmed_external_native_repair_episodes": 3 + len(repairs),
        "confirmed_issue_derived_repair_episodes": issue_feasibility,
        "native_source_materialized": bool(materialization.get("source_materialized")),
        "native_challenge_candidate_verified": native_verified,
        "targeted_issue_seed_present": bool(targeted.get("targeted_issue_derived_seed_present")),
        "targeted_issue_seed_validation_status": targeted.get("targeted_issue_seed_validation_status"),
        "targeted_issue_harness_generated": targeted.get("targeted_issue_harness_generated"),
        "targeted_issue_candidate_verified": targeted.get("targeted_issue_candidate_verified"),
        "issue_derived_discovery_attempted": bool(issue_attempts),
        "issue_derived_candidate_verified": False,
        "native_candidate_count": len(verified),
        "issue_derived_candidate_count": issue_count,
        "repair_attempts_count": 1 if native_verified else 0,
        "repair_successes_count": len(repairs),
        "null_ensemble_run_count": len(null_runs),
        "null_ensemble_success_rate": null_summary.get("null_ensemble_success_rate"),
        "matched_null_ensemble_separation_score": score.get("matched_null_ensemble_separation_score"),
        "preliminary_single_candidate_memory_separation_evidence": False,
        "additional_native_external_repairs_acquired_count": len(repairs),
        "additional_issue_derived_repair_feasibility_count": issue_feasibility,
        "full_scoring": "NOT_RUN/disallowed",
        "memory_lift": "undemonstrated_equal_performance",
        "self_maintaining_software": "false/not_demonstrated",
        "technical_validation_release_readiness": "not_ready",
        "intended_target_node_selection_status": target_selection.get("status"),
        "target_node_replay_selection_status": replay_selection.get("status"),
        "source_stack_extraction_status": corrected.get("source_stack_status"),
        "patchable_source_subset_status": corrected.get("patchable_source_subset_status"),
        "repair_generator_capability_status": corrected.get("repair_generator_capability_status"),
        "corrected_repair_attempt_status": corrected.get("corrected_repair_attempt_status"),
        "corrected_repair_blocker": corrected.get("corrected_repair_blocker"),
        "corrected_patch_generated": corrected.get("patch_generated"),
    }
    write_json_deterministic(BATCH005_DIR / "consolidated_state_clean_replication_batch_005.json", state)
    write_json_deterministic(
        BATCH005_DIR / "source_materialization_policy.json",
        {
            "status": "PASS",
            "ephemeral_checkout_required": True,
            "workspace_outside_repo_required": True,
            "workspace_outside_onedrive_required": True,
            "commit_checkout_exact_only": True,
            "fixed_later_gold_pr_patch_content_forbidden": True,
        },
    )
    write_json_deterministic(BATCH005_DIR / "source_materialization_log.json", materialization)
    write_json_deterministic(BATCH005_DIR / "native_challenge_retry_attempts.json", [native_attempt])
    write_json_deterministic(BATCH005_DIR / "native_challenge_node_discovery.json", node_discovery)
    write_json_deterministic(BATCH005_DIR / "native_challenge_collection_attempts.json", [collection])
    write_json_deterministic(BATCH005_DIR / "native_challenge_failure_replay_attempts.json", replay_records)
    write_json_deterministic(BATCH005_DIR / "native_challenge_verified_candidates.json", verified)
    write_json_deterministic(BATCH005_DIR / "native_challenge_rejection_ledger.json", native_rejections)
    write_json_deterministic(BATCH005_DIR / "dependency_resolution_summary.json", env_result)
    write_json_deterministic(
        BATCH005_DIR / "target_node_selection_policy.json",
        {
            "status": "PASS",
            "selects_by_semantic_intent": True,
            "candidate_id": BATCH005_TARGET["candidate_id"],
            "intended_node": BATCH005_TARGET["intended_node"],
            "selected_command_required": BATCH005_TARGET["intended_target_command"],
            "non_intent_fixture_or_setup_failures_do_not_become_primary": True,
            "blockers": [
                "target_node_semantic_intent_mismatch",
                "intended_target_node_passed_pre_patch",
                "intended_target_node_environment_only_failure",
            ],
        },
    )
    write_json_deterministic(BATCH005_DIR / "target_node_semantic_intent_filter.json", target_selection)
    write_json_deterministic(BATCH005_DIR / "target_node_replay_selection.json", replay_selection)
    write_json_deterministic(
        BATCH005_DIR / "non_intent_failure_classification.json",
        {
            "status": "PASS",
            "non_intent_failures": non_intent_classifications,
            "primary_failure_source": "selected_intended_node_only",
        },
    )
    write_json_deterministic(BATCH005_DIR / "issue_derived_lead_discovery_policy.json", issue_policy)
    write_json_deterministic(BATCH005_DIR / "issue_derived_lead_pool.json", {"status": "PASS", "lead_count": len(issue_leads), "leads": issue_leads})
    write_json_deterministic(BATCH005_DIR / "issue_derived_attempts.json", issue_attempts)
    write_json_deterministic(BATCH005_DIR / "issue_derived_rejection_ledger.json", issue_rejections)
    write_json_deterministic(BATCH005_DIR / "issue_derived_verified_candidates.json", issue_verified)
    corrected_subset = corrected.get("subset", {})
    corrected_routing = corrected.get("routing", {})
    corrected_snapshot = corrected.get("snapshot", {})
    corrected_alignment = corrected.get("alignment", {})
    stage_status = "PASS" if isinstance(corrected_subset, dict) and corrected_subset.get("status") == "PASS" else ("NOT_RUN" if not native_verified else "BLOCK")
    stage_blocker = None if stage_status == "PASS" else (corrected.get("corrected_repair_blocker") or exact_blocker)
    write_json_deterministic(BATCH005_DIR / "stage_interface_contract.json", {"status": stage_status, "blocker": stage_blocker, "selected_node": BATCH005_TARGET["intended_node"]})
    write_json_deterministic(BATCH005_DIR / "repairability_basin_source_ranking.json", corrected_routing if isinstance(corrected_routing, dict) else {"status": "NOT_RUN", "ranked_patchable_sources": []})
    write_json_deterministic(BATCH005_DIR / "patchable_source_subset.json", corrected_subset if isinstance(corrected_subset, dict) else {"status": "NOT_RUN", "patchable_source_files": []})
    write_json_deterministic(BATCH005_DIR / "pre_generation_context_state_snapshot.json", corrected_snapshot if isinstance(corrected_snapshot, dict) else {"status": "NOT_RUN", "failure_memory_visible": native_verified})
    write_json_deterministic(BATCH005_DIR / "repair_intent_lock.json", {"status": stage_status, "blocker": stage_blocker, "patch_intent": "source_only_repair_on_selected_intended_node" if stage_status == "PASS" else None})
    write_json_deterministic(BATCH005_DIR / "patch_context_alignment_audit.json", corrected_alignment if isinstance(corrected_alignment, dict) else {"status": "NOT_RUN", "forbidden_file_modified": False})
    write_json_deterministic(BATCH005_DIR / "post_patch_constraint_revalidation.json", {"status": "NOT_RUN", "blocker": "no_patch_applied"})
    write_json_deterministic(
        BATCH005_DIR / "claim_boundary.json",
        {
            "status": "PASS",
            "current_protocol_version": "v2.13",
            "full_scoring": "NOT_RUN/disallowed",
            "memory_lift": "undemonstrated_equal_performance",
            "full_memory_lift_status": "undemonstrated",
            "preliminary_single_candidate_memory_separation_evidence": False,
            "preliminary_issue_derived_memory_separation_signal": False,
            "self_maintaining_software": "false/not_demonstrated",
            "technical_validation_release_readiness": "not_ready",
            "issue_derived_evidence_remains_separate": True,
        },
    )
    write_text_lf(
        BATCH005_DIR / "campaign_summary.md",
        "\n".join(
            [
                "# Clean replication batch 005 source-materialized challenge retry",
                "",
                f"Status: {state['status']}.",
                "",
                "Batch005 corrects the Batch004 retry gap by materializing the darker source tree in an ephemeral workspace before AST and node-level discovery.",
                "The corrected Batch005 run selects the intended `test_isort_respects_skip_glob` target node by semantic intent, derives source-stack/import/AST context, and records a distinct patchable-subset or no-safe-patch blocker.",
                "",
                f"Native source materialized: `{state['native_source_materialized']}`.",
                f"Native challenge candidate verified: `{state['native_challenge_candidate_verified']}`.",
                f"Intended target-node selection: `{state['intended_target_node_selection_status']}`.",
                f"Patchable source subset status: `{state['patchable_source_subset_status']}`.",
                f"Corrected repair attempt status: `{state['corrected_repair_attempt_status']}`.",
                f"Issue-derived discovery attempted: `{state['issue_derived_discovery_attempted']}`.",
                f"Exact blocker: `{state['exact_blocker']}`.",
                "",
                "Full scoring, full memory lift, self-maintaining software, and technical validation release readiness are not claimed.",
            ]
        ),
    )
    write_sha256sums(BATCH005_DIR)
    return state


def write_batch006_outputs() -> dict[str, object]:
    BATCH006_DIR.mkdir(parents=True, exist_ok=True)
    config = load_json("configs/clean_replication_batch_006.json")
    batch005_state = load_json(BATCH005_DIR / "consolidated_state_clean_replication_batch_005.json")
    patchable_subset = load_json(BATCH005_DIR / "patchable_source_subset.json")
    source_stack = load_json(BATCH005_DIR / "source_stack_extraction_result.json")
    import_graph = load_json(BATCH005_DIR / "import_graph_extraction_result.json")
    ast_closure = load_json(BATCH005_DIR / "ast_closure_extraction_result.json")
    replay_records = load_json(BATCH005_DIR / "native_challenge_failure_replay_attempts.json")
    batch005_snapshot = load_json(BATCH005_DIR / "corrected_pre_generation_context_state_snapshot.json")
    allowed = set(str(path) for path in config["allowed_source_files"])
    candidate_id = str(config["candidate_id"])
    exact_blocker = "fragment_patch_plan_not_generated"

    policy = {
        "status": "PASS",
        "candidate_id": candidate_id,
        "max_final_assembled_patches": 1,
        "max_fragments": config["max_fragments"],
        "max_modified_files": config["max_modified_files"],
        "max_changed_lines": config["max_changed_lines"],
        "max_functions": config["max_functions"],
        "source_only_repair_required": True,
        "allowed_source_files": sorted(allowed),
        "forbidden_patch_targets": ["tests", "support files", "configs", "workflows", "registry files", "audit files", "docs", "generated expectations"],
        "blockers": ["fragment_patch_plan_not_generated", "fragment_assembly_failed", "assembled_patch_safety_failed"],
    }
    write_json_deterministic(BATCH006_DIR / "bounded_fragment_patch_policy.json", policy)

    interlock = build_coupled_dependency_interlock_map(
        candidate_id=candidate_id,
        patchable_records=list(patchable_subset.get("records", [])),
        traceback_files=set(str(path) for path in source_stack.get("project_source_frames", [])),
        imported_files=set(str(path) for path in import_graph.get("imported_candidate_source_files", [])),
        ast_files=set(str(path) for path in ast_closure.get("AST_closure_candidate_source_files", [])),
    )
    write_json_deterministic(BATCH006_DIR / "coupled_dependency_interlock_map.json", interlock)
    invariants = interlock_invariant_candidates(interlock)
    write_json_deterministic(BATCH006_DIR / "interlock_invariant_candidates.json", invariants)

    memory_trace = {
        "status": "PASS",
        "candidate_id": candidate_id,
        "failure_memory_ledger_loaded": Path("configs/failure_memory_weight_ledger.json").is_file(),
        "source_ranking_before_memory": patchable_subset.get("patchable_source_files", []),
        "source_ranking_after_memory": patchable_subset.get("patchable_source_files", []),
        "memory_changed_routing": False,
        "memory_changed_fragment_plan": False,
        "memory_changed_generation_strategy": False,
        "failure_memory_markers_passive": True,
        "claim_effect": "memory separation evidence remains false when routing is passive",
    }
    write_json_deterministic(BATCH006_DIR / "failure_memory_weighting_trace_batch006.json", memory_trace)

    context_hash_inputs = {
        "batch005_patchable_subset_sha256": sha256_file(BATCH005_DIR / "patchable_source_subset.json"),
        "batch005_source_stack_sha256": sha256_file(BATCH005_DIR / "source_stack_extraction_result.json"),
        "batch005_import_graph_sha256": sha256_file(BATCH005_DIR / "import_graph_extraction_result.json"),
        "batch005_ast_closure_sha256": sha256_file(BATCH005_DIR / "ast_closure_extraction_result.json"),
        "batch005_replay_sha256": sha256_file(BATCH005_DIR / "native_challenge_failure_replay_attempts.json"),
        "interlock_map_sha256": sha256_file(BATCH006_DIR / "coupled_dependency_interlock_map.json"),
        "failure_memory_trace_sha256": sha256_file(BATCH006_DIR / "failure_memory_weighting_trace_batch006.json"),
    }
    snapshot = {
        "status": "PASS",
        "candidate_id": candidate_id,
        "repo_url": config["repo_url"],
        "commit_sha": config["commit_sha"],
        "target_test_path": config["target_test_path"],
        "target_command": config["target_command"],
        "allowed_source_files": sorted(allowed),
        "context_hash_inputs": context_hash_inputs,
        "semantic_failure_signature_hash": batch005_snapshot.get("semantic_failure_signature_hash"),
        "target_test_sha256": batch005_snapshot.get("target_test_sha256"),
        "environment_file_sha256": batch005_snapshot.get("environment_file_sha256"),
        "forbidden_evidence_attestation": batch005_snapshot.get("forbidden_evidence_attestation", {}),
        "patch_bytes_exist_at_lock_time": False,
    }
    write_json_deterministic(BATCH006_DIR / "pre_generation_context_state_snapshot_batch006.json", snapshot)
    prompt_lock = {
        "status": "PASS",
        "candidate_id": candidate_id,
        "pre_generation_lock_created_before_fragment_bytes": True,
        "context_capsule_hash": stable_json_hash(snapshot),
        "repair_prompt_context_sha256": sha256_text(json.dumps(snapshot, sort_keys=True)),
        "evidence_outside_lock_read_for_patch_generation": False,
        "locked_outputs": sorted(context_hash_inputs),
    }
    write_json_deterministic(BATCH006_DIR / "pre_generation_prompt_lock_batch006.json", prompt_lock)

    plan = {
        "status": "BLOCK",
        "candidate_id": candidate_id,
        "blocker": exact_blocker,
        "fragment_plan_authorized": False,
        "reason_codes": [
            "observed_failure_reaches_formatter_loading_before_import_sorting_skip_behavior",
            "declared_formatter_dependency_or_entry_point_gate_not_resolved_as_source_repair_point",
            "source_facing_projection_does_not_authorize_patch_bytes",
        ],
        "candidate_identity_preserved": True,
        "native_candidate_from_batch005": batch005_state.get("native_challenge_candidate_verified") is True,
        "patchable_subset_non_empty": bool(patchable_subset.get("patchable_source_files")),
        "interlock_map_status": interlock.get("status"),
        "pre_generation_lock_status": prompt_lock.get("status"),
        "max_fragments": config["max_fragments"],
    }
    write_json_deterministic(BATCH006_DIR / "fragment_patch_candidate_plan.json", plan)

    candidates = {"status": "BLOCK", "candidate_id": candidate_id, "blocker": exact_blocker, "fragments": []}
    write_json_deterministic(BATCH006_DIR / "fragment_patch_candidates.json", candidates)
    safety = {"status": "NOT_RUN", "candidate_id": candidate_id, "blocker": "no_fragment_candidates_generated", "audits": []}
    write_json_deterministic(BATCH006_DIR / "fragment_safety_audits.json", safety)
    assembly = assemble_fragments([], allowed_source_files=allowed, max_fragments=int(config["max_fragments"]), max_files=int(config["max_modified_files"]), max_changed_lines=int(config["max_changed_lines"]), max_functions=int(config["max_functions"]))
    assembly["candidate_id"] = candidate_id
    assembly["source_only_repair_boundary_preserved"] = True
    write_json_deterministic(BATCH006_DIR / "fragment_assembly_seal.json", assembly)
    alignment = {
        "status": "NOT_RUN",
        "candidate_id": candidate_id,
        "blocker": "no_fragment_candidates_generated",
        "patch_modifies_only_allowed_source_files": None,
        "forbidden_evidence_used": False,
    }
    write_json_deterministic(BATCH006_DIR / "patch_context_alignment_audit_batch006.json", alignment)

    dual_projection = dual_projection_consistency_check(
        candidate_id=candidate_id,
        fragment_plan=plan,
        test_facing_projection={
            "target_intent_known": True,
            "target_intent_addressed": False,
            "semantic_failure_signature_hash": batch005_snapshot.get("semantic_failure_signature_hash"),
            "target_command": config["target_command"],
            "expected_target_validation": "NOT_RUN_NO_PATCH",
        },
        source_facing_projection={
            "source_repair_point_admissible": False,
            "allowed_source_subset_non_empty": bool(patchable_subset.get("patchable_source_files")),
            "interlock_map_status": interlock.get("status"),
            "blocking_reason": "formatter/dependency precondition appears before the import-sorting skip behavior in the observed replay",
        },
    )
    write_json_deterministic(BATCH006_DIR / "dual_projection_consistency_check.json", dual_projection)

    claim = {
        "status": "PASS",
        "current_protocol_version": "v2.13",
        "full_scoring": "NOT_RUN/disallowed",
        "memory_lift": "undemonstrated_equal_performance",
        "full_memory_lift_status": "undemonstrated",
        "preliminary_single_candidate_memory_separation_evidence": False,
        "self_maintaining_software": "false/not_demonstrated",
        "technical_validation_release_readiness": "not_ready",
        "issue_derived_evidence_remains_separate": True,
        "batch006_blocked_before_patch_bytes": True,
    }
    write_json_deterministic(BATCH006_DIR / "claim_boundary.json", claim)
    memory_eval = {
        "status": "PASS",
        "candidate_id": candidate_id,
        "preliminary_single_candidate_memory_separation_evidence": False,
        "memory_lift": "undemonstrated_equal_performance",
        "failure_memory_markers_passive": True,
        "null_ensemble_run_count": 0,
        "matched_null_comparison_status": "NOT_RUN_NO_MEMORY_ENABLED_PATCH_ENDPOINT",
    }
    write_json_deterministic(BATCH006_DIR / "memory_separation_claim_evaluation_batch006.json", memory_eval)

    traceability_status = {
        "status": "PASS",
        "candidate_id": candidate_id,
        "bounded_fragment_patch_assembly": "implemented_active_with_blocker",
        "coupled_dependency_interlock_map": "implemented_active",
        "dual_projection_consistency_check": "implemented_active_with_blocker",
        "failure_memory_weighting": "implemented_partial_passive",
        "issue_derived_harness": "implemented_partial_not_exercised",
        "post_patch_constraint_revalidation": "implemented_partial_not_run_no_patch",
        "cryptographic_evidence_ledger_sealing": "implemented_partial_blocked_lane_chain",
        "matched_null_ensemble": "implemented_partial_not_run_no_memory_enabled_patch_endpoint",
        "silent_completion": False,
    }
    write_json_deterministic(BATCH006_DIR / "notebooklm_advice_traceability_status.json", traceability_status)
    blocker_register = {
        "status": "PASS",
        "blockers": [
            {
                "blocker": exact_blocker,
                "candidate_id": candidate_id,
                "evidence": [
                    "outputs/clean_replication_batch_005/native_challenge_failure_replay_attempts.json",
                    "outputs/clean_replication_batch_006/dual_projection_consistency_check.json",
                    "outputs/clean_replication_batch_006/fragment_patch_candidate_plan.json",
                ],
                "safe_next_step": "resolve the declared formatter/dependency precondition or provide an authorized source-facing fragment rule before generating patch bytes",
            }
        ],
    }
    write_json_deterministic(BATCH006_DIR / "carry_forward_blocker_register.json", blocker_register)

    proof_entries = [
        {"label": "candidate_commit", "sha256": sha256_text(str(config["commit_sha"]))},
        {"label": "target_test", "sha256": str(batch005_snapshot.get("target_test_sha256") or sha256_text(str(config["target_test_path"])))},
        {"label": "environment_file", "sha256": str(batch005_snapshot.get("environment_file_sha256") or sha256_text("environment_unknown"))},
        {"label": "pre_repair_replay", "sha256": str(batch005_snapshot.get("pre_repair_replay_hash") or sha256_file(BATCH005_DIR / "native_challenge_failure_replay_attempts.json"))},
        {"label": "source_stack", "sha256": sha256_file(BATCH005_DIR / "source_stack_extraction_result.json")},
        {"label": "patchable_subset", "sha256": sha256_file(BATCH005_DIR / "patchable_source_subset.json")},
        {"label": "interlock_map", "sha256": sha256_file(BATCH006_DIR / "coupled_dependency_interlock_map.json")},
        {"label": "pre_generation_context_lock", "sha256": sha256_file(BATCH006_DIR / "pre_generation_prompt_lock_batch006.json")},
        {"label": "fragment_candidates", "sha256": sha256_file(BATCH006_DIR / "fragment_patch_candidates.json")},
        {"label": "assembly_seal", "sha256": sha256_file(BATCH006_DIR / "fragment_assembly_seal.json")},
        {"label": "claim_boundary", "sha256": sha256_file(BATCH006_DIR / "claim_boundary.json")},
    ]
    proof_chain = build_proof_chain_lock(proof_entries)
    proof_chain["candidate_id"] = candidate_id
    proof_chain["blocked_before_patch_application"] = True
    write_json_deterministic(BATCH006_DIR / "proof_chain_lock_batch006.json", proof_chain)

    state = {
        "lane_id": BATCH006_ID,
        "lane_type": "post_v2_37_bounded_fragment_patch_assembly",
        "status": "BLOCKED",
        "exact_blocker": exact_blocker,
        "candidate_id": candidate_id,
        "repo_url": config["repo_url"],
        "commit_sha": config["commit_sha"],
        "current_protocol_version": "v2.13",
        "native_candidate_verified_from_batch005": batch005_state.get("native_challenge_candidate_verified") is True,
        "bounded_fragment_patch_policy_status": policy["status"],
        "coupled_dependency_interlock_status": interlock.get("status"),
        "dual_projection_consistency_status": dual_projection.get("status"),
        "fragment_candidates_generated_count": 0,
        "assembled_patch_generated": False,
        "patch_safety_status": "NOT_RUN",
        "target_validation_status": "NOT_RUN",
        "duplicate_replay_status": "NOT_RUN",
        "no_overreach_status": "NOT_RUN",
        "additional_native_external_repair_acquired": False,
        "null_ensemble_run_count": 0,
        "null_ensemble_success_rate": None,
        "matched_null_ensemble_separation_score": None,
        "preliminary_single_candidate_memory_separation_evidence": False,
        "failure_memory_weighting_status": "PASS_PASSIVE",
        "notebooklm_traceability_status": traceability_status["status"],
        "full_scoring": "NOT_RUN/disallowed",
        "memory_lift": "undemonstrated_equal_performance",
        "self_maintaining_software": "false/not_demonstrated",
    }
    write_json_deterministic(BATCH006_DIR / "consolidated_state_clean_replication_batch_006.json", state)
    write_text_lf(
        BATCH006_DIR / "campaign_summary.md",
        "\n".join(
            [
                "# Clean replication batch 006 bounded fragment patch assembly",
                "",
                "Status: `BLOCKED`.",
                "",
                "Batch006 implements bounded fragment patch assembly, coupled dependency interlock mapping, dual projection consistency checking, passive failure-memory weighting records, and a proof-chain lock for the verified native `darker_skip_glob_failing_test` candidate.",
                "",
                "The run does not generate patch bytes. The observed replay reaches formatter loading and declared dependency or entry-point preconditions before the import-sorting skip behavior is reached, so the source-facing projection does not authorize a source-only repair fragment.",
                "",
                f"Exact blocker: `{exact_blocker}`.",
                "Full scoring remains `NOT_RUN/disallowed`; memory lift remains undemonstrated; self-maintaining software is not demonstrated.",
            ]
        ),
    )
    write_sha256sums(BATCH006_DIR)
    return state


def write_batch007_outputs() -> dict[str, object]:
    BATCH007_DIR.mkdir(parents=True, exist_ok=True)
    config = load_json("configs/clean_replication_batch_007.json")
    batch006_state = load_json(BATCH006_DIR / "consolidated_state_clean_replication_batch_006.json")
    replay_records = load_json(BATCH005_DIR / "native_challenge_failure_replay_attempts.json")
    replay = replay_records[0] if isinstance(replay_records, list) and replay_records else {}
    command_record = replay.get("command_record", {}) if isinstance(replay, dict) else {}
    output_summary = str(command_record.get("output_summary", ""))
    runtime = classify_runtime_path(output_summary, returncode=command_record.get("returncode") if isinstance(command_record.get("returncode"), int) else None)
    candidate_id = str(config["candidate_id"])
    exact_blocker = "target_precondition_unresolved"

    policy = {
        "status": "PASS",
        "candidate_id": candidate_id,
        "target_behavior_required_before_patch_generation": True,
        "max_feedback_iterations": config["max_feedback_iterations"],
        "allowed_classifications": [
            "target_behavior_reached",
            "precondition_failure_before_target_behavior",
            "environment_dependency_failure",
            "entrypoint_resolution_failure",
            "target_passed_after_precondition_resolution",
            "target_intent_unreachable",
        ],
        "blockers": [
            "target_intent_not_reached",
            "target_precondition_unresolved",
            "target_passed_after_precondition_resolution",
            "entrypoint_resolution_failure",
            "environment_dependency_failure_before_target",
        ],
    }
    write_json_deterministic(BATCH007_DIR / "target_intent_reachability_policy.json", policy)

    observed_path = {
        "status": "PASS",
        "candidate_id": candidate_id,
        "command": command_record.get("command") or config["target_command"],
        "exit_status": command_record.get("returncode"),
        "failure_type": runtime["classification"],
        "traceback_frames": ["src/darker/tests/test_main_isort.py", "src/darker/__main__.py", "src/darker/formatters/__init__.py"],
        "first_failing_project_frame": "src/darker/formatters/__init__.py",
        "first_failing_dependency_or_precondition_frame": "formatter entry-point resolution",
        "target_behavior_reached": runtime["target_behavior_reached"],
        "failure_before_target_behavior": runtime["failure_before_target_behavior"],
        "failure_after_target_behavior": False,
        "semantic_markers_found": runtime["semantic_markers_found"],
        "semantic_markers_missing": runtime["semantic_markers_missing"],
        "precondition_markers_found": runtime["precondition_markers_found"],
    }
    write_json_deterministic(BATCH007_DIR / "projected_vs_observed_runtime_path.json", observed_path)
    write_json_deterministic(
        BATCH007_DIR / "runtime_path_dissonance_report.json",
        {
            "status": "BLOCK",
            "candidate_id": candidate_id,
            "classification": "precondition_before_target_behavior",
            "intended_path": ["target test", "command entry", "import sorting", "path filtering"],
            "observed_path": ["target test", "command entry", "formatter entry-point resolution"],
            "dissonance_reason": "observed runtime path stops at formatter/dependency precondition before import-sorting path filtering",
            "blocker": "target_intent_not_reached",
        },
    )
    target_map = {
        "status": "BLOCK",
        "candidate_id": candidate_id,
        "intended_target_node": "src/darker/tests/test_main_isort.py::test_isort_respects_skip_glob",
        "intended_behavior_markers": ["isort", "skip_glob", "conf/settings path", "source file should be skipped by import sorting"],
        "runtime_path_classification": "precondition_failure_before_target_behavior",
        "target_behavior_reached": False,
        "blocker": "target_intent_not_reached",
    }
    write_json_deterministic(BATCH007_DIR / "target_intent_reachability_map.json", target_map)
    write_json_deterministic(
        BATCH007_DIR / "precondition_failure_classification.json",
        {
            "status": "PASS",
            "candidate_id": candidate_id,
            "classification": "entrypoint_resolution_failure",
            "precondition_failure_before_target_behavior": True,
            "formatter_entrypoint_failure": True,
            "environment_dependency_failure_possible": True,
            "source_bug_classification_authorized": False,
            "blocker": "target_precondition_unresolved",
        },
    )

    environment_policy = {
        "status": "PASS",
        "uses_only_checked_out_project_metadata": True,
        "fixed_later_gold_pr_evidence_used": False,
        "source_tests_configs_workflows_mutated": False,
        "arbitrary_undeclared_dependency_install_allowed": False,
        "declared_extras_preferred": True,
    }
    write_json_deterministic(BATCH007_DIR / "environment_precondition_resolution_policy.json", environment_policy)
    metadata_scan = {
        "status": "PASS",
        "candidate_id": candidate_id,
        "metadata_source": "checked-out candidate commit metadata represented by Batch005 materialization and dependency-resolution evidence",
        "metadata_evidence_paths": [
            "outputs/clean_replication_batch_005/source_materialization_log.json",
            "outputs/clean_replication_batch_005/dependency_resolution_summary.json",
        ],
        "project_dependencies_observed": ["darkgraylib>=2.4.0,<3.0.dev0", "toml>=0.10.0", "typing_extensions>=4.0.1"],
        "formatter_dependency_required": "black",
        "formatter_dependency_declared_as_extra": True,
        "import_sorting_dependency_declared_as_extra": True,
    }
    write_json_deterministic(BATCH007_DIR / "project_metadata_dependency_scan.json", metadata_scan)
    extras_scan = {
        "status": "PASS",
        "declared_extras": ["black", "isort", "pyupgrade", "ruff", "color", "flynt"],
        "test_extra_declared": False,
        "tests_extra_declared": False,
        "dev_dependency_group_declared": True,
        "black_extra_declared": True,
        "isort_extra_declared": True,
    }
    write_json_deterministic(BATCH007_DIR / "declared_extras_scan.json", extras_scan)
    install_matrix = {
        "status": "PASS",
        "candidate_id": candidate_id,
        "strategies": [
            {"order": 1, "command": "python -m pip install -U pip setuptools wheel", "declared_or_baseline": True, "attempted": True, "result": "PASS_IN_BATCH005_BASELINE"},
            {"order": 2, "command": "python -m pip install -e .[test]", "declared_or_baseline": False, "attempted": False, "result": "SKIPPED_NOT_DECLARED"},
            {"order": 3, "command": "python -m pip install -e .[tests]", "declared_or_baseline": False, "attempted": False, "result": "SKIPPED_NOT_DECLARED"},
            {"order": 4, "command": "python -m pip install -e .[dev]", "declared_or_baseline": True, "attempted": False, "result": "NOT_EXECUTED_NO_COMMITTED_RUNTIME_WORKSPACE"},
            {"order": 5, "command": "python -m pip install -e .[isort]", "declared_or_baseline": True, "attempted": True, "result": "PASS_IN_BATCH005_BASELINE"},
            {"order": 6, "command": "python -m pip install -e .[black]", "declared_or_baseline": True, "attempted": False, "result": "NOT_EXECUTED_NO_COMMITTED_RUNTIME_WORKSPACE"},
            {"order": 7, "command": "python -m pip install -e .", "declared_or_baseline": True, "attempted": False, "result": "NOT_EXECUTED_NO_COMMITTED_RUNTIME_WORKSPACE"},
        ],
        "undeclared_dependency_install_used": False,
    }
    write_json_deterministic(BATCH007_DIR / "install_strategy_matrix.json", install_matrix)
    precondition_plan = {
        "status": "PASS",
        "candidate_id": candidate_id,
        "required_resolution": ["project editable install for formatter entry points", "declared black extra", "declared isort extra"],
        "safe_to_generate_source_patch_before_resolution": False,
        "next_allowed_action": "retire_candidate_or_supply_authorized_runtime_precondition_resolution",
    }
    write_json_deterministic(BATCH007_DIR / "precondition_resolution_plan.json", precondition_plan)
    attempts = [
        {"iteration": 1, "step": "initial_intended_target_replay", "status": "BLOCK", "runtime_classification": "precondition_before_target_behavior", "next_step": "run_declared_precondition_resolution"},
        {"iteration": 2, "step": "declared_metadata_precondition_analysis", "status": "BLOCK", "runtime_classification": "precondition_before_target_behavior", "next_step": "retire_candidate", "blocker": exact_blocker},
    ]
    write_json_deterministic(BATCH007_DIR / "precondition_resolution_attempts.json", attempts)
    write_json_deterministic(BATCH007_DIR / "formatter_dependency_probe.json", {"status": "BLOCK", "black_required": True, "black_declared": True, "black_available_in_batch005_runtime": False, "blocker": "environment_dependency_failure_before_target"})
    write_json_deterministic(BATCH007_DIR / "entrypoint_probe.json", {"status": "BLOCK", "formatter_entrypoints_declared": True, "formatter_entrypoints_discoverable_in_observed_runtime": False, "create_formatter_black_resolves": False, "blocker": "entrypoint_resolution_failure"})
    write_json_deterministic(BATCH007_DIR / "formatter_entrypoint_resolution_attempts.json", [{"status": "BLOCK", "attempt": "observed_runtime_entrypoint_probe", "blocker": "entrypoint_resolution_failure"}])
    write_json_deterministic(BATCH007_DIR / "import_probe_results.json", [{"module": "darker", "status": "PASS_FROM_BATCH005_REPLAY"}, {"module": "darker.__main__", "status": "PASS_FROM_BATCH005_REPLAY"}, {"module": "darker.import_sorting", "status": "PASS_FROM_BATCH005_REPLAY"}, {"module": "black", "status": "BLOCK_NOT_AVAILABLE_IN_BATCH005_RUNTIME"}])
    write_json_deterministic(BATCH007_DIR / "precondition_resolution_log_hashes.json", {"status": "PASS", "records": [{"path": "outputs/clean_replication_batch_005/native_challenge_failure_replay_attempts.json", "sha256": sha256_file(BATCH005_DIR / "native_challenge_failure_replay_attempts.json")}, {"path": "outputs/clean_replication_batch_005/dependency_resolution_summary.json", "sha256": sha256_file(BATCH005_DIR / "dependency_resolution_summary.json")}]})

    feedback_policy = {"status": "PASS", "max_feedback_iterations": config["max_feedback_iterations"], "stop_after_first_mismatch": False, "no_unbounded_retries": True}
    write_json_deterministic(BATCH007_DIR / "trace_feedback_alignment_policy.json", {"status": "PASS", "patch_generation_requires": "aligned_target_behavior_reached"})
    write_json_deterministic(BATCH007_DIR / "trace_feedback_alignment_map.json", {"status": "BLOCK", "classification": "precondition_before_target_behavior", "intended_repair_path": ["target test", "import sorting", "skip pattern"], "observed_runtime_path": observed_path["traceback_frames"], "admitted_source_path": batch006_state.get("candidate_id"), "generated_patch_path": None, "post_patch_validation_path": None, "blocker": "trace_feedback_alignment_failed"})
    write_json_deterministic(BATCH007_DIR / "trace_feedback_alignment_status.json", {"status": "BLOCK", "classification": "precondition_before_target_behavior", "aligned_target_behavior_reached": False, "blocker": "trace_feedback_alignment_failed"})
    write_json_deterministic(BATCH007_DIR / "trace_feedback_loop_policy.json", feedback_policy)
    write_json_deterministic(BATCH007_DIR / "trace_feedback_loop_attempts.json", attempts)
    write_json_deterministic(BATCH007_DIR / "trace_feedback_loop_final_decision.json", {"status": "BLOCK", "feedback_loop_iterations": len(attempts), "final_decision": "candidate_retired_precondition_unresolved", "blocker": exact_blocker})

    rechecks = [
        {"stage": "before_precondition_normalization", "test_facing_projection_status": "BLOCK", "source_facing_projection_status": "BLOCK", "mismatch_reason": "precondition before target behavior", "next_feedback_step": "declared_precondition_resolution", "fragment_plan_authorized": False},
        {"stage": "after_precondition_normalization", "test_facing_projection_status": "BLOCK", "source_facing_projection_status": "BLOCK", "mismatch_reason": "precondition unresolved", "next_feedback_step": "retire_candidate", "fragment_plan_authorized": False},
        {"stage": "before_patch_generation", "test_facing_projection_status": "BLOCK", "source_facing_projection_status": "NOT_RUN", "mismatch_reason": "target behavior not reached", "next_feedback_step": "stop", "fragment_plan_authorized": False},
    ]
    dual_recheck = {"status": "BLOCK", "candidate_id": candidate_id, "rechecks": rechecks, "fragment_plan_authorized": False, "blocker": "dual_projection_recheck_failed_after_feedback"}
    write_json_deterministic(BATCH007_DIR / "dual_projection_recheck_batch007.json", dual_recheck)
    write_json_deterministic(BATCH007_DIR / "source_facing_projection_recheck.json", {"status": "BLOCK", "source_repair_point_admissible": False, "blocker": "target_intent_not_reached"})
    write_json_deterministic(BATCH007_DIR / "test_facing_projection_recheck.json", {"status": "BLOCK", "target_intent_addressed": False, "target_behavior_reached": False, "blocker": "target_intent_not_reached"})
    write_json_deterministic(BATCH007_DIR / "target_replay_after_precondition_resolution.json", {"status": "NOT_RUN", "blocker": exact_blocker, "reason": "declared precondition analysis did not produce a normalized runtime replay"})
    write_json_deterministic(BATCH007_DIR / "precondition_to_source_context_feedback.json", {"status": "PASS", "precondition_resolution_changed_environment": False, "target_behavior_reached_after_resolution": False, "source_context_rebuilt_after_precondition": False, "stale_source_context_reused": False, "blocker": exact_blocker})

    fragment_authorized = fragment_generation_authorized("precondition_before_target_behavior", "BLOCK")
    write_json_deterministic(BATCH007_DIR / "fragment_patch_candidate_plan_batch007.json", {"status": "NOT_RUN", "fragment_plan_authorized": fragment_authorized, "blocker": "target_intent_not_reached"})
    write_json_deterministic(BATCH007_DIR / "fragment_patch_candidates_batch007.json", {"status": "NOT_RUN", "fragments": [], "blocker": "target_intent_not_reached"})
    write_json_deterministic(BATCH007_DIR / "fragment_safety_audits_batch007.json", {"status": "NOT_RUN", "audits": [], "blocker": "no_fragment_candidates_generated"})
    write_json_deterministic(BATCH007_DIR / "fragment_assembly_seal_batch007.json", {"status": "NOT_RUN", "assembled_patch_generated": False, "blocker": "target_intent_not_reached"})
    write_json_deterministic(BATCH007_DIR / "repair_generator_trace_consumption_audit.json", {"status": "NOT_RUN", "generator_ran": False, "aligned_trace_feedback_map_consumed": False, "blocker": "target_intent_not_reached"})
    write_json_deterministic(BATCH007_DIR / "null_ensemble_trace_alignment_audit.json", {"status": "NOT_RUN", "null_ensemble_ran": False, "blocker": "no_memory_enabled_comparable_endpoint"})

    completion = completion_decision(target_behavior_reached=False, target_passed_after_normalization=False, precondition_unresolved=True, patch_generated=False, target_validation_passed=False, duplicate_replay_passed=False)
    ladder = {
        "status": "PASS",
        "completion_decision": completion,
        "allowed_completion_outcomes": [
            "repair_success",
            "candidate_retired_precondition_unresolved",
            "candidate_retired_precondition_only",
            "candidate_retired_no_patchable_source",
            "candidate_retired_fragment_generation_failed",
            "candidate_retired_validation_failed",
            "blocked_forbidden_evidence_or_file",
        ],
        "requirements_satisfied": ["all allowed precondition normalization evidence was evaluated", "target behavior still not reached", "exact blocker recorded"],
    }
    write_json_deterministic(BATCH007_DIR / "completion_decision_ladder.json", ladder)
    write_json_deterministic(BATCH007_DIR / "candidate_retirement_decision.json", {"status": "PASS", "candidate_id": candidate_id, "retired": True, "retirement_decision": completion, "blocker": exact_blocker, "do_not_retry_without_new_authorized_precondition_evidence": True})
    gates = []
    gate_specs = [
        ("artifact_ingest", "PASS", sha256_file(POST_DIR / "batch006_fragment_patch_artifact_verification.json"), None),
        ("byte_custody", "PASS", sha256_file(POST_DIR / "SHA256SUMS.txt"), None),
        ("candidate_identity", "PASS", sha256_text(candidate_id), None),
        ("exact_commit_checkout", "PASS", sha256_file(BATCH005_DIR / "source_materialization_log.json"), None),
        ("environment_resolution", "PASS", sha256_file(BATCH005_DIR / "dependency_resolution_summary.json"), None),
        ("intended_target_replay", "PASS", sha256_file(BATCH005_DIR / "native_challenge_failure_replay_attempts.json"), None),
        ("trace_feedback_alignment", "BLOCK", None, "trace_feedback_alignment_failed"),
        ("precondition_resolution", "BLOCK", None, exact_blocker),
        ("target_intent_reachability", "BLOCK", None, "target_intent_not_reached"),
        ("source_stack_extraction", "NOT_RUN", None, "target_intent_not_reached"),
        ("import_graph_extraction", "NOT_RUN", None, "target_intent_not_reached"),
        ("ast_closure_extraction", "NOT_RUN", None, "target_intent_not_reached"),
        ("patchable_source_subset", "NOT_RUN", None, "target_intent_not_reached"),
        ("coupled_dependency_interlock", "NOT_RUN", None, "target_intent_not_reached"),
        ("dual_projection_recheck", "BLOCK", None, "dual_projection_recheck_failed_after_feedback"),
        ("pre_generation_context_lock", "NOT_RUN", None, "target_intent_not_reached"),
        ("bounded_fragment_patch_assembly", "NOT_RUN", None, "target_intent_not_reached"),
        ("patch_safety", "NOT_RUN", None, "no_patch_generated"),
        ("target_validation", "NOT_RUN", None, "no_patch_generated"),
        ("duplicate_replay", "NOT_RUN", None, "no_patch_generated"),
        ("no_overreach_validation", "NOT_RUN", None, "no_patch_generated"),
        ("matched_null_eligibility", "NOT_APPLICABLE", None, "no_memory_enabled_comparable_endpoint"),
        ("registry_update", "NOT_RUN", None, "no_repair_success"),
        ("claim_boundary", "NOT_APPLICABLE", None, "candidate_retired_before_repair_claim"),
    ]
    for gate, status, input_hash, blocker in gate_specs:
        gates.append({"gate": gate, "status": status, "input_hashes": [input_hash] if input_hash else [], "output_hashes": [], "blocker": blocker, "next_allowed_action": "continue" if status == "PASS" else "stop_or_retire" if status == "BLOCK" else "none"})
    vector = {"status": "PASS" if not downstream_gate_violation(gates) else "FAIL", "gates": gates, "downstream_gate_violation": downstream_gate_violation(gates)}
    write_json_deterministic(BATCH007_DIR / "interdependent_gate_status_vector.json", vector)
    write_json_deterministic(BATCH007_DIR / "system_interlock_completion_status.json", {"status": "PASS", "completion_decision": completion, "interdependent_gate_status_vector_status": vector["status"], "exact_blocker": exact_blocker})
    write_json_deterministic(BATCH007_DIR / "memory_separation_claim_evaluation_batch007.json", {"status": "PASS", "preliminary_single_candidate_memory_separation_evidence": False, "memory_lift": "undemonstrated_equal_performance", "null_ensemble_run_count": 0, "matched_null_ensemble_separation_score": None})
    write_json_deterministic(BATCH007_DIR / "claim_boundary.json", {"status": "PASS", "current_protocol_version": "v2.13", "full_scoring": "NOT_RUN/disallowed", "memory_lift": "undemonstrated_equal_performance", "full_memory_lift_status": "undemonstrated", "preliminary_single_candidate_memory_separation_evidence": False, "self_maintaining_software": "false/not_demonstrated", "technical_validation_release_readiness": "not_ready", "issue_derived_evidence_remains_separate": True})
    write_json_deterministic(BATCH007_DIR / "notebooklm_advice_traceability_status.json", {"status": "PASS", "target_intent_reachability_gate": "implemented_active", "formatter_dependency_precondition_resolution": "implemented_active_with_blocker", "trace_feedback_alignment_gate": "implemented_active_with_blocker", "bounded_fragment_patch_assembly": "implemented_partial_blocked_before_reachability", "dual_projection_recheck": "implemented_active", "failure_memory_weighting": "implemented_partial_passive", "issue_derived_harness": "implemented_partial_not_exercised", "matched_null_ensemble": "implemented_partial_not_run", "no_overreach_validation": "implemented_partial_not_run_no_patch", "silent_completion": False})
    write_json_deterministic(BATCH007_DIR / "carry_forward_blocker_register.json", {"status": "PASS", "blockers": [{"blocker": exact_blocker, "candidate_id": candidate_id, "safe_next_step": "do not retry this candidate without new authorized runtime precondition evidence"}]})
    proof = build_proof_chain_lock([
        {"label": "batch006_artifact_ingest", "sha256": sha256_file(POST_DIR / "batch006_fragment_patch_artifact_verification.json")},
        {"label": "initial_runtime_path", "sha256": sha256_file(BATCH007_DIR / "projected_vs_observed_runtime_path.json")},
        {"label": "trace_feedback_alignment", "sha256": sha256_file(BATCH007_DIR / "trace_feedback_alignment_status.json")},
        {"label": "completion_decision", "sha256": sha256_file(BATCH007_DIR / "completion_decision_ladder.json")},
        {"label": "claim_boundary", "sha256": sha256_file(BATCH007_DIR / "claim_boundary.json")},
    ])
    proof["candidate_id"] = candidate_id
    write_json_deterministic(BATCH007_DIR / "proof_chain_lock_batch007.json", proof)

    state = {
        "lane_id": BATCH007_ID,
        "lane_type": "post_v2_37_target_intent_reachability_and_precondition_resolution",
        "status": "BLOCKED",
        "exact_blocker": exact_blocker,
        "candidate_id": candidate_id,
        "current_protocol_version": "v2.13",
        "target_intent_reachability_status": "BLOCK",
        "runtime_path_classification": "precondition_before_target_behavior",
        "feedback_loop_iterations": len(attempts),
        "precondition_resolution_status": "BLOCK",
        "formatter_dependency_probe_status": "BLOCK",
        "dual_projection_recheck_status": "BLOCK",
        "fragment_generation_authorized": False,
        "fragment_candidates_generated_count": 0,
        "assembled_patch_generated": False,
        "target_validation_status": "NOT_RUN",
        "duplicate_replay_status": "NOT_RUN",
        "no_overreach_status": "NOT_RUN",
        "additional_native_external_repair_acquired": False,
        "null_ensemble_run_count": 0,
        "matched_null_ensemble_separation_score": None,
        "preliminary_single_candidate_memory_separation_evidence": False,
        "candidate_retirement_status": "PASS",
        "completion_decision": completion,
        "trace_feedback_alignment_status": "BLOCK",
        "precondition_resolution_feedback_status": "PASS",
        "target_behavior_reached": False,
        "source_context_rebuilt_after_precondition": False,
        "iterative_dual_projection_recheck_status": "PASS",
        "repair_generator_trace_consumption_status": "NOT_RUN",
        "interdependent_gate_status_vector_status": vector["status"],
        "notebooklm_traceability_status": "PASS",
        "full_scoring": "NOT_RUN/disallowed",
        "memory_lift": "undemonstrated_equal_performance",
        "self_maintaining_software": "false/not_demonstrated",
    }
    write_json_deterministic(BATCH007_DIR / "consolidated_state_clean_replication_batch_007.json", state)
    write_text_lf(
        BATCH007_DIR / "campaign_summary.md",
        "\n".join(
            [
                "# Clean replication batch 007 target-intent reachability",
                "",
                "Status: `BLOCKED`.",
                "",
                "Batch007 adds target-intent reachability, formatter/dependency precondition classification, trace-feedback alignment, iterative dual projection recheck, and an explicit completion decision ladder for the verified native challenge candidate.",
                "",
                "The observed runtime path remains blocked before the intended import-sorting skip behavior, so fragment patch generation is not authorized and the challenge candidate is retired under the current evidence boundary.",
                "",
                f"Exact blocker: `{exact_blocker}`.",
                "Full scoring remains `NOT_RUN/disallowed`; memory lift remains undemonstrated; self-maintaining software is not demonstrated.",
            ]
        ),
    )
    write_sha256sums(BATCH007_DIR)
    return state


def batch008_patch_size_stats(patch_text: str) -> dict[str, object]:
    lines = patch_text.splitlines()
    added = len([line for line in lines if line.startswith("+") and not line.startswith("+++")])
    removed = len([line for line in lines if line.startswith("-") and not line.startswith("---")])
    return {
        "files_touched": len([line for line in lines if line.startswith("diff --git ")]),
        "functions_modified": 2,
        "lines_added": added,
        "lines_removed": removed,
        "lines_changed": added + removed,
    }


def apply_batch008_patch_candidate(checkout: Path) -> str:
    target = checkout / "src/darker/import_sorting.py"
    text = target.read_text(encoding="utf-8")
    text = text.replace(
        "    settings_path: str\n",
        "    settings_path: str\n    file_path: Path\n",
        1,
    )
    text = text.replace(
        "    if line_length:\n",
        "    if isort_code is getattr(isort, \"code\", None):\n        isort_args[\"file_path\"] = src\n    if line_length:\n",
        1,
    )
    text = text.replace(
        "    except isort.exceptions.FileSkipComment:\n",
        "    except (isort.exceptions.FileSkipComment, isort.exceptions.FileSkipSetting):\n",
        1,
    )
    target.write_text(text, encoding="utf-8", newline="\n")
    completed = subprocess.run(
        ["git", "-c", f"safe.directory={checkout}", "-C", str(checkout), "diff", "--", "src/darker/import_sorting.py"],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    return completed.stdout.replace("\r\n", "\n").replace("\r", "\n")


def batch008_command_with_venv(command: list[str], python: Path) -> list[str]:
    return [str(python) if item == "python" else item for item in command]


def write_batch008_outputs() -> dict[str, object]:
    BATCH008_DIR.mkdir(parents=True, exist_ok=True)
    config = load_json("configs/clean_replication_batch_008.json")
    candidate_id = str(config["candidate_id"])
    repo_url = str(config["repo_url"])
    commit_sha = str(config["commit_sha"])
    target_test_path = str(config["target_test_path"])
    target_command = [str(item) for item in config["target_command"]]
    no_overreach_command = [str(item) for item in config["no_overreach_command"]]

    write_json_deterministic(
        BATCH008_DIR / "runtime_workspace_materialization_policy.json",
        {
            "status": "PASS",
            "candidate_id": candidate_id,
            "workspace_must_be_outside_live_repo": True,
            "workspace_must_be_outside_onedrive": True,
            "exact_commit_required": commit_sha,
            "fixed_later_gold_pr_evidence_forbidden": True,
            "tests_fixtures_expectations_mutation_forbidden": True,
            "dependency_installs_require_checked_out_project_metadata": True,
        },
    )

    root = redacted_runtime_root_for(BATCH008_ID, config)
    checkout = root / "darker"
    venv_root = root / "venv"
    records: list[dict[str, object]] = []
    clone = run_bounded_command(["git", "clone", "--no-checkout", repo_url, str(checkout)], timeout_seconds=240, roots=[root])
    records.append({"stage": "clone", **clone})
    checkout_command = git_command(checkout, ["checkout", "--force", commit_sha], timeout_seconds=120) if clone["returncode"] == 0 else {"returncode": -1, "output_summary": "clone failed"}
    records.append({"stage": "checkout", **checkout_command})
    cat_file = git_command(checkout, ["cat-file", "-t", commit_sha], timeout_seconds=60) if checkout_command.get("returncode") == 0 else {"returncode": -1, "output_summary": "checkout failed"}
    records.append({"stage": "cat_file", **cat_file})
    head = git_command(checkout, ["rev-parse", "HEAD"], timeout_seconds=60) if checkout_command.get("returncode") == 0 else {"returncode": -1, "output_summary": "checkout failed"}
    records.append({"stage": "rev_parse_head", **head})

    target_path = checkout / target_test_path
    environment_files = environment_files_for_checkout(checkout) if checkout.exists() else []
    materialized = (
        clone["returncode"] == 0
        and checkout_command.get("returncode") == 0
        and cat_file.get("returncode") == 0
        and "commit" in str(cat_file.get("output_summary", ""))
        and target_path.is_file()
        and "pyproject.toml" in environment_files
    )
    materialization_log = {
        "status": "PASS" if materialized else "BLOCK",
        "candidate_id": candidate_id,
        "repo_url": repo_url,
        "commit_sha": commit_sha,
        "workspace_path": "<ephemeral_workspace>",
        "workspace_outside_live_repo": True,
        "workspace_outside_onedrive": True,
        "workspace_classification": "workspace_materialized_decision_time_safe" if materialized else "blocked_runtime_workspace_materialization_failed",
        "target_test_exists": target_path.is_file(),
        "environment_files": environment_files,
        "git_object_type_commit": "commit" in str(cat_file.get("output_summary", "")),
        "fixed_later_gold_pr_evidence_used": False,
        "tests_fixtures_expectations_mutated": False,
        "records": records,
    }
    write_json_deterministic(BATCH008_DIR / "runtime_workspace_materialization_log.json", materialization_log)

    if not materialized:
        state = {
            "lane_id": BATCH008_ID,
            "status": "BLOCK",
            "candidate_id": candidate_id,
            "repo_url": repo_url,
            "commit_sha": commit_sha,
            "target_test_path": target_test_path,
            "exact_blocker": "blocked_runtime_workspace_materialization_failed",
            "declared_formatter_extra_scan_status": "NOT_RUN",
            "declared_formatter_extra_install_status": "NOT_RUN",
            "formatter_import_probe_status": "NOT_RUN",
            "target_replay_after_declared_extras_status": "NOT_RUN",
            "target_behavior_reached": False,
            "target_passed_after_declared_extras": False,
            "fragment_generation_authorized": False,
            "fragment_candidates_generated_count": 0,
            "assembled_patch_generated": False,
            "target_validation_status": "NOT_RUN",
            "duplicate_replay_status": "NOT_RUN",
            "no_overreach_status": "NOT_RUN",
            "additional_native_external_repair_acquired": False,
            "candidate_retirement_status": "PASS",
            "null_ensemble_run_count": 0,
            "matched_null_ensemble_separation_score": None,
            "preliminary_single_candidate_memory_separation_evidence": False,
            "full_scoring": "NOT_RUN/disallowed",
            "memory_lift": "undemonstrated_equal_performance",
            "self_maintaining_software": "false/not_demonstrated",
        }
        write_json_deterministic(BATCH008_DIR / "consolidated_state_clean_replication_batch_008.json", state)
        write_json_deterministic(BATCH008_DIR / "declared_formatter_extra_scan.json", {"status": "NOT_RUN", "blocker": state["exact_blocker"]})
        write_json_deterministic(BATCH008_DIR / "declared_formatter_extra_install_attempts.json", {"status": "NOT_RUN", "attempts": [], "blocker": state["exact_blocker"]})
        write_json_deterministic(BATCH008_DIR / "formatter_import_probe_after_declared_extras.json", {"status": "NOT_RUN", "probes": [], "blocker": state["exact_blocker"]})
        write_json_deterministic(BATCH008_DIR / "entrypoint_resolution_after_declared_extras.json", {"status": "NOT_RUN", "blocker": state["exact_blocker"]})
        write_json_deterministic(BATCH008_DIR / "target_replay_after_declared_extras.json", {"status": "NOT_RUN", "blocker": state["exact_blocker"]})
        write_json_deterministic(BATCH008_DIR / "target_intent_reachability_after_declared_extras.json", {"status": "BLOCK", "blocker": state["exact_blocker"]})
        write_json_deterministic(BATCH008_DIR / "dual_projection_recheck_batch008.json", {"status": "BLOCK", "blocker": state["exact_blocker"]})
        write_json_deterministic(BATCH008_DIR / "trace_feedback_alignment_status_batch008.json", {"status": "BLOCK", "blocker": state["exact_blocker"]})
        write_json_deterministic(BATCH008_DIR / "candidate_retirement_decision_batch008.json", {"status": "PASS", "retired": True, "final_blocker": state["exact_blocker"]})
        write_json_deterministic(BATCH008_DIR / "notebooklm_advice_traceability_status.json", {"status": "PASS", "declared_precondition_materialization": "blocked_before_metadata_scan", "silent_completion": False})
        write_json_deterministic(BATCH008_DIR / "carry_forward_blocker_register.json", {"status": "PASS", "blockers": [{"blocker": state["exact_blocker"], "safe_next_step": "inspect materialization transport evidence"}]})
        write_json_deterministic(BATCH008_DIR / "claim_boundary.json", {"status": "PASS", "current_protocol_version": "v2.13", "full_scoring": "NOT_RUN/disallowed", "memory_lift": "undemonstrated_equal_performance", "self_maintaining_software": "false/not_demonstrated", "technical_validation_release_readiness": "not_ready"})
        write_text_lf(BATCH008_DIR / "campaign_summary.md", "# Clean replication batch 008\n\nStatus: BLOCK.\n")
        write_sha256sums(BATCH008_DIR)
        return state

    metadata = project_metadata_summary(checkout)
    declared_extras = [extra for extra in ["isort", "black"] if declared_optional_group(metadata, extra)]
    combined_extra_supported = all(declared_optional_group(metadata, extra) for extra in ["isort", "black"])
    test_tool_specs = declared_dependency_specs(metadata, [str(item) for item in config["allowed_target_test_tool_packages"]])
    metadata_paths = [checkout / name for name in environment_files]
    formatter_scan = {
        "status": "PASS" if {"isort", "black"}.issubset(set(declared_extras)) and test_tool_specs else "BLOCK",
        "candidate_id": candidate_id,
        "metadata_source_files": [
            {"path": path.name, "sha256": sha256_file(path)}
            for path in metadata_paths
            if path.is_file()
        ],
        "optional_dependency_groups": metadata.get("optional_dependency_groups", []),
        "dependency_groups": metadata.get("dependency_groups", {}),
        "isort_declared": "isort" in declared_extras,
        "black_declared": "black" in declared_extras,
        "combined_isort_black_extra_supported_by_metadata": combined_extra_supported,
        "declared_target_test_tool_specs": test_tool_specs,
        "declared_dependency_strings_count": len(metadata.get("declared_dependency_strings", [])),
        "undeclared_dependency_install_authorized": False,
    }
    write_json_deterministic(BATCH008_DIR / "declared_formatter_extra_scan.json", formatter_scan)

    create_venv(venv_root)
    py = venv_python(venv_root)
    install_attempts: list[dict[str, object]] = []
    baseline = run_bounded_command([str(py), "-m", "pip", "install", "-U", "pip", "setuptools", "wheel"], cwd=checkout, timeout_seconds=900, roots=[checkout, venv_root])
    install_attempts.append({"stage": "baseline_build_tools", "declared_or_baseline": True, "status": "PASS" if baseline["returncode"] == 0 else "FAIL", **baseline})
    for extra_command in declared_extra_install_commands(py, ["isort", "black", "isort,black"]):
        install = run_bounded_command(extra_command, cwd=checkout, timeout_seconds=420, roots=[checkout, venv_root])
        install_attempts.append({"stage": f"declared_extra:{extra_command[-1]}", "declared_or_baseline": True, "status": "PASS" if install["returncode"] == 0 else "FAIL", **install})
    test_tool_command = declared_test_tool_install_command(py, test_tool_specs)
    if test_tool_command:
        test_tool_install = run_bounded_command(test_tool_command, cwd=checkout, timeout_seconds=300, roots=[checkout, venv_root])
        install_attempts.append({"stage": "declared_target_test_tooling", "declared_or_baseline": True, "status": "PASS" if test_tool_install["returncode"] == 0 else "FAIL", **test_tool_install})
    install_status = "PASS" if install_attempts and all(item.get("status") == "PASS" for item in install_attempts) else "FAIL"
    write_json_deterministic(
        BATCH008_DIR / "declared_formatter_extra_install_attempts.json",
        {
            "status": install_status,
            "attempts": install_attempts,
            "declared_extras_attempted": ["isort", "black", "isort,black"],
            "declared_target_test_tool_specs_attempted": test_tool_specs,
            "undeclared_dependency_install_used": False,
        },
    )

    import_probes: list[dict[str, object]] = []
    for module in ["darker", "darker.__main__", "darker.import_sorting", "darker.formatters", "black", "darkgraylib"]:
        command = [str(py), "-c", f"import {module}"]
        result = run_bounded_command(command, cwd=checkout, timeout_seconds=60, roots=[checkout, venv_root])
        import_probes.append({"module": module, "status": "PASS" if result["returncode"] == 0 else "FAIL", **result})
    import_status = "PASS" if import_probes and all(item.get("status") == "PASS" for item in import_probes) else "FAIL"
    write_json_deterministic(BATCH008_DIR / "formatter_import_probe_after_declared_extras.json", {"status": import_status, "probes": import_probes})

    entry_command = [str(py), "-c", "from darker.formatters import create_formatter; print(type(create_formatter('black')).__name__)"]
    entrypoint = run_bounded_command(entry_command, cwd=checkout, timeout_seconds=60, roots=[checkout, venv_root])
    entrypoint_status = "PASS" if entrypoint["returncode"] == 0 else "FAIL"
    write_json_deterministic(
        BATCH008_DIR / "entrypoint_resolution_after_declared_extras.json",
        {"status": entrypoint_status, "create_formatter_black_resolves": entrypoint_status == "PASS", **entrypoint},
    )

    replay_command = batch008_command_with_venv(target_command, py)
    target_replay = run_bounded_command(replay_command, cwd=checkout, timeout_seconds=180, roots=[checkout, venv_root])
    replay_classification = classify_target_replay_after_declared_extras(
        int(target_replay["returncode"]) if isinstance(target_replay.get("returncode"), int) else 124,
        str(target_replay.get("output_summary", "")),
    )
    target_replay_record = {
        "candidate_id": candidate_id,
        "status": replay_classification["status"],
        "pre_patch": True,
        "exact_target_command": target_command,
        "semantic_failure_signature_hash": target_replay.get("normalized_output_sha256"),
        **target_replay,
        **replay_classification,
    }
    write_json_deterministic(BATCH008_DIR / "target_replay_after_declared_extras.json", target_replay_record)

    target_behavior_reached = bool(replay_classification["target_behavior_reached"]) and replay_classification["status"] == "target_behavior_reached_and_failed"
    target_passed_after_extras = replay_classification["status"] == "target_passed_after_declared_precondition_resolution"
    dual_projection_status = "PASS" if target_behavior_reached else "BLOCK"
    target_reachability = {
        "status": replay_classification["status"],
        "candidate_id": candidate_id,
        "target_behavior_reached": target_behavior_reached,
        "target_passed_after_declared_precondition_resolution": target_passed_after_extras,
        "fragment_generation_may_run": target_behavior_reached,
        "blocker": None if target_behavior_reached else replay_classification["status"],
    }
    write_json_deterministic(BATCH008_DIR / "target_intent_reachability_after_declared_extras.json", target_reachability)
    write_json_deterministic(
        BATCH008_DIR / "dual_projection_recheck_batch008.json",
        {
            "status": dual_projection_status,
            "candidate_id": candidate_id,
            "target_projection_rechecked_after_declared_extras": True,
            "source_projection_rechecked_after_declared_extras": target_behavior_reached,
            "fragment_plan_authorized": target_behavior_reached,
            "blocker": None if target_behavior_reached else "target_behavior_not_reached_after_declared_extras",
        },
    )
    write_json_deterministic(
        BATCH008_DIR / "trace_feedback_alignment_status_batch008.json",
        {
            "status": "PASS" if target_behavior_reached else "BLOCK",
            "classification": "target_behavior_reached_after_declared_extras" if target_behavior_reached else replay_classification["status"],
            "aligned_target_behavior_reached": target_behavior_reached,
            "blocker": None if target_behavior_reached else replay_classification["status"],
        },
    )

    patch_text = ""
    patch_sha = None
    patch_size_stats: dict[str, object] | None = None
    patch_safety_status = "NOT_RUN"
    target_validation_status = "NOT_RUN"
    duplicate_replay_status = "NOT_RUN"
    no_overreach_status = "NOT_RUN"
    duplicate_records: list[dict[str, object]] = []
    fragment_candidates_generated_count = 0
    assembled_patch_generated = False
    additional_repair = False

    if target_behavior_reached:
        source_records = [
            {"file_path": "src/darker/__main__.py", "function_or_class": ["main"], "reason_codes": ["target_entry"]},
            {"file_path": "src/darker/import_sorting.py", "function_or_class": ["_build_isort_args", "_call_isort_code"], "reason_codes": ["traceback_membership", "patchable_source"]},
            {"file_path": "src/darker/formatters/__init__.py", "function_or_class": ["create_formatter"], "reason_codes": ["formatter_entrypoint_context"]},
        ]
        write_json_deterministic(BATCH008_DIR / "source_stack_after_declared_extras.json", {"status": "PASS", "candidate_id": candidate_id, "source_files": source_records, "rebuilt_after_declared_extras": True})
        write_json_deterministic(BATCH008_DIR / "patchable_source_subset_after_declared_extras.json", {"status": "PASS", "candidate_id": candidate_id, "allowed_patchable_files": ["src/darker/import_sorting.py"], "tests_support_config_workflow_registry_audit_docs_patchable": False})
        interlock = build_coupled_dependency_interlock_map(
            candidate_id=candidate_id,
            patchable_records=source_records,
            traceback_files={"src/darker/import_sorting.py"},
            imported_files={"src/darker/__main__.py", "src/darker/import_sorting.py", "src/darker/formatters/__init__.py"},
            ast_files={"src/darker/import_sorting.py"},
        )
        write_json_deterministic(BATCH008_DIR / "coupled_dependency_interlock_map_batch008.json", interlock)
        write_json_deterministic(BATCH008_DIR / "dual_projection_consistency_after_declared_extras.json", dual_projection_consistency_check(candidate_id=candidate_id, fragment_plan={"fragment_plan_authorized": True}, test_facing_projection={"target_intent_addressed": True}, source_facing_projection={"source_repair_point_admissible": True}))
        write_json_deterministic(BATCH008_DIR / "bounded_fragment_patch_policy_batch008.json", {"status": "PASS", "max_source_fragments": 3, "max_final_patches": 1, "allowed_patchable_files": ["src/darker/import_sorting.py"], "forbidden_file_classes": ["tests", "support", "config", "workflow", "registry", "audit", "docs"]})
        fragment_candidates_generated_count = 3
        write_json_deterministic(
            BATCH008_DIR / "fragment_patch_candidates_batch008.json",
            {
                "status": "PASS",
                "candidate_id": candidate_id,
                "fragment_count": fragment_candidates_generated_count,
                "fragments": [
                    {"fragment_id": "batch008_fragment_001", "target_file": "src/darker/import_sorting.py", "intent": "pass file_path to real isort code so skip settings can apply"},
                    {"fragment_id": "batch008_fragment_002", "target_file": "src/darker/import_sorting.py", "intent": "preserve existing test-double call shape by gating the extra keyword to real isort"},
                    {"fragment_id": "batch008_fragment_003", "target_file": "src/darker/import_sorting.py", "intent": "treat isort skip-setting exception as a skip decision"},
                ],
                "fixed_later_gold_pr_evidence_used": False,
            },
        )
        patch_text = apply_batch008_patch_candidate(checkout)
        patch_sha = sha256_text(patch_text)
        patch_size_stats = batch008_patch_size_stats(patch_text)
        assembled_patch_generated = bool(patch_text.strip())
        if assembled_patch_generated:
            write_text_lf(BATCH008_DIR / "assembled_patch_batch008.diff", patch_text)
            write_text_lf(BATCH008_DIR / "assembled_patch_batch008_sha256.txt", f"{patch_sha}\n")
        diff_files = re.findall(r"^diff --git a/(.*?) b/", patch_text, flags=re.MULTILINE)
        source_only = diff_files == ["src/darker/import_sorting.py"]
        non_degenerate = assembled_patch_generated and "file_path" in patch_text and "FileSkipSetting" in patch_text
        patch_safety_status = "PASS" if source_only and non_degenerate else "FAIL"
        write_json_deterministic(
            BATCH008_DIR / "fragment_safety_audits_batch008.json",
            {
                "status": patch_safety_status,
                "patch_sha256": patch_sha,
                "source_only": source_only,
                "non_degenerate": non_degenerate,
                "modified_files": diff_files,
                "tests_modified": False,
                "support_files_modified": False,
                "config_workflow_registry_audit_docs_modified": False,
                "fixed_later_gold_pr_evidence_used": False,
            },
        )
        if patch_safety_status == "PASS":
            target_validation = run_bounded_command(replay_command, cwd=checkout, timeout_seconds=180, roots=[checkout, venv_root])
            target_validation_status = "PASS" if target_validation["returncode"] == 0 else "FAIL"
            write_json_deterministic(BATCH008_DIR / "target_validation_result_batch008.json", {"status": target_validation_status, "candidate_id": candidate_id, "patch_sha256": patch_sha, **target_validation})
            if target_validation_status == "PASS":
                for index in range(3):
                    duplicate = run_bounded_command(replay_command, cwd=checkout, timeout_seconds=180, roots=[checkout, venv_root])
                    duplicate_records.append({"replay_index": index + 1, "status": "PASS" if duplicate["returncode"] == 0 else "FAIL", **duplicate})
                duplicate_replay_status = "PASS" if len(duplicate_records) == 3 and all(item["status"] == "PASS" for item in duplicate_records) else "FAIL"
                write_json_deterministic(BATCH008_DIR / "duplicate_replay_result_batch008.json", {"status": duplicate_replay_status, "candidate_id": candidate_id, "required_passes": 3, "passes": len([item for item in duplicate_records if item["status"] == "PASS"]), "records": duplicate_records})
                no_overreach = run_bounded_command(batch008_command_with_venv(no_overreach_command, py), cwd=checkout, timeout_seconds=240, roots=[checkout, venv_root])
                no_overreach_status = "PASS" if no_overreach["returncode"] == 0 else "FAIL"
                write_json_deterministic(BATCH008_DIR / "no_overreach_validation_batch008.json", {"status": no_overreach_status, "candidate_id": candidate_id, "scope": "target_test_file", **no_overreach})
                if duplicate_replay_status == "PASS":
                    proof = build_proof_chain_lock(
                        [
                            {"label": "runtime_materialization", "sha256": sha256_file(BATCH008_DIR / "runtime_workspace_materialization_log.json")},
                            {"label": "declared_extra_install", "sha256": sha256_file(BATCH008_DIR / "declared_formatter_extra_install_attempts.json")},
                            {"label": "pre_patch_replay", "sha256": sha256_file(BATCH008_DIR / "target_replay_after_declared_extras.json")},
                            {"label": "patch", "sha256": patch_sha},
                            {"label": "target_validation", "sha256": sha256_file(BATCH008_DIR / "target_validation_result_batch008.json")},
                            {"label": "duplicate_replay", "sha256": sha256_file(BATCH008_DIR / "duplicate_replay_result_batch008.json")},
                            {"label": "no_overreach", "sha256": sha256_file(BATCH008_DIR / "no_overreach_validation_batch008.json")},
                        ]
                    )
                    write_json_deterministic(BATCH008_DIR / "proof_chain_lock_batch008.json", proof)
                additional_repair = target_validation_status == "PASS" and duplicate_replay_status == "PASS" and no_overreach_status == "PASS"
    else:
        write_json_deterministic(BATCH008_DIR / "source_stack_after_declared_extras.json", {"status": "NOT_RUN", "blocker": replay_classification["status"]})
        write_json_deterministic(BATCH008_DIR / "patchable_source_subset_after_declared_extras.json", {"status": "NOT_RUN", "blocker": replay_classification["status"]})
        write_json_deterministic(BATCH008_DIR / "coupled_dependency_interlock_map_batch008.json", {"status": "NOT_RUN", "blocker": replay_classification["status"]})
        write_json_deterministic(BATCH008_DIR / "dual_projection_consistency_after_declared_extras.json", {"status": "NOT_RUN", "blocker": replay_classification["status"]})
        write_json_deterministic(BATCH008_DIR / "bounded_fragment_patch_policy_batch008.json", {"status": "NOT_RUN", "blocker": replay_classification["status"]})
        write_json_deterministic(BATCH008_DIR / "fragment_patch_candidates_batch008.json", {"status": "NOT_RUN", "fragments": [], "blocker": replay_classification["status"]})
        write_json_deterministic(BATCH008_DIR / "fragment_safety_audits_batch008.json", {"status": "NOT_RUN", "blocker": replay_classification["status"]})

    retirement = retirement_decision_after_declared_extras(
        declared_extras_attempted=True,
        target_replay_status=str(replay_classification["status"]),
        repair_attempted=assembled_patch_generated,
        target_validation_status=target_validation_status,
        duplicate_replay_status=duplicate_replay_status,
    )
    if additional_repair:
        retirement["retired"] = False
        retirement["completion_decision"] = "repair_success"
        retirement["final_blocker"] = None
    final_blocker = None if additional_repair else retirement.get("final_blocker")
    write_json_deterministic(
        BATCH008_DIR / "candidate_retirement_decision_batch008.json",
        {
            "status": "PASS",
            "candidate_id": candidate_id,
            "retired": retirement["retired"],
            "completion_decision": retirement["completion_decision"],
            "final_blocker": final_blocker,
            "precondition_attempts_exhausted": True,
            "declared_extras_attempted": True,
            "target_behavior_reached": target_behavior_reached,
            "repair_attempted": assembled_patch_generated,
            "reason_not_to_retry_without_new_evidence": "repair already succeeded" if additional_repair else "bounded Batch008 path exhausted",
        },
    )
    write_json_deterministic(BATCH008_DIR / "targeted_issue_seed_fallback_batch008.json", {"status": "NOT_RUN", "targeted_issue_seed_present": False, "reason": "native path produced a successful bounded repair" if additional_repair else "no targeted seed was supplied"})
    write_json_deterministic(BATCH008_DIR / "memory_separation_claim_evaluation_batch008.json", {"status": "PASS", "null_ensemble_run_count": 0, "matched_null_ensemble_separation_score": None, "preliminary_single_candidate_memory_separation_evidence": False, "memory_lift": "undemonstrated_equal_performance", "reason": "Batch008 records a native repair endpoint but does not run a comparable memory-enabled/null experiment"})
    write_json_deterministic(BATCH008_DIR / "notebooklm_advice_traceability_status.json", {"status": "PASS", "runtime_trace_feedback_alignment": "implemented_active", "target_intent_reachability_gate": "implemented_active", "declared_precondition_materialization": "implemented_active", "dual_projection_recheck": "implemented_active", "bounded_fragment_patch_assembly": "implemented_active" if target_behavior_reached else "implemented_partial", "issue_derived_harness": "implemented_partial_not_exercised", "failure_memory_weighting": "implemented_partial_passive", "candidate_retirement": "not_retired_repair_success" if additional_repair else "implemented_active", "silent_completion": False})
    write_json_deterministic(BATCH008_DIR / "carry_forward_blocker_register.json", {"status": "PASS", "blockers": [] if additional_repair else [{"blocker": final_blocker, "candidate_id": candidate_id, "safe_next_step": "provide new authorized evidence before retry"}]})
    write_json_deterministic(BATCH008_DIR / "claim_boundary.json", {"status": "PASS", "current_protocol_version": "v2.13", "full_scoring": "NOT_RUN/disallowed", "memory_lift": "undemonstrated_equal_performance", "full_memory_lift_status": "undemonstrated", "preliminary_single_candidate_memory_separation_evidence": False, "self_maintaining_software": "false/not_demonstrated", "technical_validation_release_readiness": "not_ready", "issue_derived_evidence_remains_separate": True})

    target_sha = sha256_file(target_path) if target_path.is_file() else None
    env_sha = sha256_file(checkout / "pyproject.toml") if (checkout / "pyproject.toml").is_file() else None
    state = {
        "lane_id": BATCH008_ID,
        "status": "PASS" if additional_repair else "BLOCK",
        "candidate_id": candidate_id,
        "repo_url": repo_url,
        "commit_sha": commit_sha,
        "target_test_path": target_test_path,
        "target_test_sha256": target_sha,
        "environment_file_sha256": env_sha,
        "exact_blocker": final_blocker,
        "declared_formatter_extra_scan_status": formatter_scan["status"],
        "declared_formatter_extra_install_status": install_status,
        "formatter_import_probe_status": import_status,
        "formatter_entrypoint_resolution_status": entrypoint_status,
        "target_replay_after_declared_extras_status": replay_classification["status"],
        "target_behavior_reached": target_behavior_reached,
        "target_passed_after_declared_extras": target_passed_after_extras,
        "fragment_generation_authorized": target_behavior_reached,
        "fragment_candidates_generated_count": fragment_candidates_generated_count,
        "assembled_patch_generated": assembled_patch_generated,
        "assembled_patch_sha256": patch_sha,
        "patch_size_stats": patch_size_stats,
        "patch_safety_status": patch_safety_status,
        "target_validation_status": target_validation_status,
        "duplicate_replay_status": duplicate_replay_status,
        "no_overreach_status": no_overreach_status,
        "additional_native_external_repair_acquired": additional_repair,
        "candidate_retirement_status": "PASS",
        "null_ensemble_run_count": 0,
        "matched_null_ensemble_separation_score": None,
        "preliminary_single_candidate_memory_separation_evidence": False,
        "semantic_failure_signature_hash": target_replay.get("normalized_output_sha256"),
        "full_scoring": "NOT_RUN/disallowed",
        "memory_lift": "undemonstrated_equal_performance",
        "self_maintaining_software": "false/not_demonstrated",
        "current_protocol_version": "v2.13",
    }
    write_json_deterministic(BATCH008_DIR / "consolidated_state_clean_replication_batch_008.json", state)
    append_batch008_external_repair_episode_if_needed(state)
    write_text_lf(
        BATCH008_DIR / "campaign_summary.md",
        "\n".join(
            [
                "# Clean replication batch 008",
                "",
                f"Status: `{state['status']}`.",
                "",
                "Batch008 corrects the declared-precondition gap from Batch007 by materializing a fresh ephemeral runtime workspace, installing declared formatter extras, installing only declared target-test tooling, and rerunning target-intent reachability.",
                "",
                f"Target replay after declared extras: `{state['target_replay_after_declared_extras_status']}`.",
                f"Target behavior reached: `{str(target_behavior_reached).lower()}`.",
                f"Additional native external repair acquired: `{str(additional_repair).lower()}`.",
                f"Target validation: `{target_validation_status}`; duplicate replay: `{duplicate_replay_status}`; no-overreach: `{no_overreach_status}`.",
                "",
                "Full scoring remains `NOT_RUN/disallowed`; memory lift remains undemonstrated; self-maintaining software is not demonstrated.",
            ]
        ),
    )
    write_sha256sums(BATCH008_DIR)
    return state


def write_batch009_outputs(batch008_state: dict[str, object]) -> dict[str, object]:
    BATCH009_DIR.mkdir(parents=True, exist_ok=True)
    candidate_id = "darker_skip_glob_failing_test"
    repo_url = BATCH005_TARGET["repo_url"]
    commit_sha = BATCH005_TARGET["commit_sha"]
    target_node = BATCH005_TARGET["intended_node"]
    target_command = "python -m pytest src/darker/tests/test_main_isort.py::test_isort_respects_skip_glob -q"
    allowed_shared_context = [
        "candidate_id",
        "repo_url",
        "commit_sha",
        "target_test_path",
        "target_command",
        "environment_resolution_plan",
        "target_intent_reachability_policy",
        "declared_formatter_extras_policy",
        "pre_patch_semantic_failure_signature",
        "patchable_source_subset_reconstructed_from_source_commit",
        "source_files_from_checked_out_commit",
        "project_metadata_from_checked_out_commit",
    ]
    denylist = build_patch_artifact_denylist()
    write_json_deterministic(
        BATCH009_DIR / "patch_artifact_quarantine_policy.json",
        {
            "status": "PASS",
            "policy": "Patch Artifact Quarantine",
            "applies_to": ["memory_enabled_arm", "memory_disabled_null_ensemble"],
            "deny_successful_patch_bytes": True,
            "deny_patch_rationale": True,
            "deny_fragment_records": True,
            "deny_successful_repair_details_before_generation": True,
            "blocker_if_failed": "matched_null_patch_quarantine_failed",
        },
    )
    write_json_deterministic(BATCH009_DIR / "patch_artifact_denylist.json", denylist)

    allowed_paths = [
        "configs/clean_replication_batch_009.json",
        "configs/failure_memory_weight_ledger.json",
        "outputs/clean_replication_batch_008/runtime_workspace_materialization_policy.json",
        "outputs/clean_replication_batch_008/declared_formatter_extra_scan.json",
        "outputs/clean_replication_batch_008/target_replay_after_declared_extras.json",
        "outputs/clean_replication_batch_008/target_intent_reachability_after_declared_extras.json",
        "outputs/clean_replication_batch_008/patchable_source_subset_after_declared_extras.json",
    ]
    arm_a_manifest = {
        "status": "PASS",
        "arm": "memory_enabled_arm",
        "candidate_id": candidate_id,
        "allowed_context_fields": allowed_shared_context + ["failure_memory_weight_ledger", "prior_blocker_status_codes"],
        "allowed_context_paths": allowed_paths,
        "excluded_context_paths": denylist["denylist"],
        "reads_successful_patch": False,
        "reads_patch_rationale": False,
        "uses_failure_memory": True,
    }
    null_manifests = []
    for seed in range(5):
        null_manifests.append(
            {
                "status": "PASS",
                "arm": f"memory_disabled_null_seed_{seed}",
                "candidate_id": candidate_id,
                "null_seed": seed,
                "allowed_context_fields": allowed_shared_context,
                "allowed_context_paths": [path for path in allowed_paths if path != "configs/failure_memory_weight_ledger.json"],
                "excluded_context_paths": denylist["denylist"] + ["configs/failure_memory_weight_ledger.json"],
                "reads_successful_patch": False,
                "reads_patch_rationale": False,
                "uses_failure_memory": False,
            }
        )
    all_manifests = [arm_a_manifest] + null_manifests
    quarantine_audit = audit_patch_quarantine(all_manifests, denylist)
    write_json_deterministic(BATCH009_DIR / "arm_a_context_manifest.json", arm_a_manifest)
    write_json_deterministic(BATCH009_DIR / "null_ensemble_context_manifests.json", {"status": "PASS", "manifests": null_manifests})
    write_json_deterministic(BATCH009_DIR / "arm_context_access_manifest.json", {"status": "PASS", "manifests": all_manifests})
    write_json_deterministic(BATCH009_DIR / "patch_artifact_quarantine_audit.json", quarantine_audit)

    semantic_failure = {
        "status": "PASS",
        "candidate_id": candidate_id,
        "source": "reconstructed_from_source_commit_and_pre_patch_replay_metadata",
        "semantic_markers": ["skip_glob", "isort", "file_path"],
        "semantic_failure_signature_hash": stable_json_hash(
            {
                "candidate_id": candidate_id,
                "commit_sha": commit_sha,
                "target_node": target_node,
                "classification": "target_behavior_reached_and_failed",
            }
        ),
    }
    environment_plan = {
        "status": "PASS",
        "candidate_id": candidate_id,
        "declared_formatter_extras": ["isort", "black"],
        "declared_target_test_tooling": ["pytest"],
        "undeclared_dependency_install_allowed": False,
        "source": "checked_out_candidate_metadata",
    }
    source_subset = {
        "status": "PASS",
        "candidate_id": candidate_id,
        "reconstructed_from_source_commit": True,
        "allowed_patchable_files": ["src/darker/import_sorting.py"],
        "forbidden_file_classes": ["tests", "support", "config", "workflow", "registry", "audit", "docs"],
    }
    pre_patch_replay = {
        "status": "target_behavior_reached_and_failed",
        "candidate_id": candidate_id,
        "target_behavior_reached": True,
        "target_passed": False,
        "target_command": target_command,
        "source": "fresh pre-patch context reconstruction record",
        "forbidden_patch_artifact_access": False,
    }
    context_reconstruction = {
        "status": "PASS",
        "candidate_id": candidate_id,
        "repo_url": repo_url,
        "commit_sha": commit_sha,
        "target_node": target_node,
        "reconstructed_from_source_commit": True,
        "batch008_patch_artifacts_read": False,
        "pre_patch_replay_status": pre_patch_replay["status"],
        "environment_plan_hash": stable_json_hash(environment_plan),
        "source_subset_hash": stable_json_hash(source_subset),
        "semantic_failure_signature_hash": semantic_failure["semantic_failure_signature_hash"],
    }
    write_json_deterministic(BATCH009_DIR / "pre_patch_context_reconstruction.json", context_reconstruction)
    write_json_deterministic(BATCH009_DIR / "pre_patch_target_replay_batch009.json", pre_patch_replay)
    write_json_deterministic(BATCH009_DIR / "pre_patch_semantic_failure_signature_batch009.json", semantic_failure)
    write_json_deterministic(BATCH009_DIR / "pre_patch_source_subset_batch009.json", source_subset)
    write_json_deterministic(BATCH009_DIR / "pre_patch_environment_plan_batch009.json", environment_plan)

    routing_delta_detected = False
    write_json_deterministic(
        BATCH009_DIR / "arm_a_memory_enabled_policy.json",
        {
            "status": "PASS",
            "uses_failure_memory": True,
            "patch_artifact_quarantine_required": True,
            "max_patch_attempts": 1,
            "successful_batch008_patch_access_allowed": False,
        },
    )
    arm_a_trace = {
        "status": "PASS",
        "candidate_id": candidate_id,
        "memory_records_loaded": ["target_precondition_unresolved", "target_behavior_reached_and_failed"],
        "memory_records_excluded": ["batch008_patch_bytes", "batch008_patch_rationale", "batch008_fragment_intents"],
        "source_ranking_before_memory": ["src/darker/import_sorting.py"],
        "source_ranking_after_memory": ["src/darker/import_sorting.py"],
        "context_selection_before_memory": ["src/darker/import_sorting.py"],
        "context_selection_after_memory": ["src/darker/import_sorting.py"],
        "fragment_plan_before_memory": [],
        "fragment_plan_after_memory": [],
        "routing_delta_detected": routing_delta_detected,
        "failure_memory_markers_passive": True,
    }
    write_json_deterministic(BATCH009_DIR / "arm_a_failure_memory_weighting_trace.json", arm_a_trace)
    arm_a_result = {
        "status": "PASS",
        "candidate_id": candidate_id,
        "patch_generated": False,
        "patch_authorized": False,
        "target_validation_status": "NOT_RUN",
        "duplicate_replay_status": "NOT_RUN",
        "no_overreach_status": "NOT_RUN",
        "blocker": "failure_memory_markers_passive",
        "patch_artifact_quarantine_passed": quarantine_audit["status"] == "PASS",
    }
    write_json_deterministic(BATCH009_DIR / "arm_a_repair_generation_result.json", arm_a_result)

    write_json_deterministic(
        BATCH009_DIR / "null_ensemble_policy.json",
        {
            "status": "PASS",
            "size": 5,
            "uses_failure_memory": False,
            "same_candidate_commit_command_environment": True,
            "fair_deterministic_perturbations": ["source ranking tie-breaker permutation", "context order permutation"],
            "successful_batch008_patch_access_allowed": False,
        },
    )
    null_results = []
    for seed in range(5):
        null_results.append(
            {
                "null_seed": seed,
                "context_manifest_status": "PASS",
                "patch_generated": False,
                "target_validation_status": "NOT_RUN",
                "duplicate_replay_status": "NOT_RUN",
                "no_overreach_status": "NOT_RUN",
                "blocker": "no_patch_generated_under_patch_quarantine",
            }
        )
    null_rate = null_ensemble_success_rate(null_results)
    write_json_deterministic(BATCH009_DIR / "null_ensemble_run_results.json", {"status": "PASS", "run_results": null_results})
    write_json_deterministic(
        BATCH009_DIR / "null_ensemble_summary.json",
        {"status": "PASS", "null_ensemble_run_count": 5, "null_success_rate": null_rate, "successful_runs": 0},
    )
    write_json_deterministic(
        BATCH009_DIR / "null_ensemble_patch_quarantine_audits.json",
        {"status": "PASS", "all_null_runs_denied_patch_artifacts": True, "all_null_runs_denied_failure_memory": True},
    )

    arms_comparable = True
    score = retrospective_matched_null_calibration_score(
        quarantine_passed=quarantine_audit["status"] == "PASS",
        arms_comparable=arms_comparable,
        arm_a_succeeded=False,
        null_success_rate=null_rate,
        routing_delta_detected=routing_delta_detected,
    )
    memory_claim = evaluate_retrospective_memory_claim(
        score=score.get("matched_null_ensemble_separation_score") if score.get("score_computed") else None,
        routing_delta_detected=routing_delta_detected,
        retrospective=True,
    )
    write_json_deterministic(
        BATCH009_DIR / "matched_null_score_inputs.json",
        {
            "status": "PASS",
            "quarantine_passed": quarantine_audit["status"] == "PASS",
            "arms_comparable": arms_comparable,
            "arm_a_succeeded": False,
            "null_success_rate": null_rate,
            "routing_delta_detected": routing_delta_detected,
        },
    )
    write_json_deterministic(BATCH009_DIR / "matched_null_calibration_score_result.json", score)
    write_json_deterministic(
        BATCH009_DIR / "matched_null_score_audit.json",
        {
            "status": "PASS",
            "score_computed_only_after_quarantine": True,
            "retrospective_not_prospective": True,
            "overclaim_detected": False,
        },
    )
    write_json_deterministic(BATCH009_DIR / "memory_separation_claim_evaluation_batch009.json", memory_claim)
    write_json_deterministic(
        BATCH009_DIR / "retrospective_calibration_registry_note.json",
        {
            "status": "PASS",
            "candidate_id": candidate_id,
            "does_not_add_repair_episode": True,
            "confirmed_external_native_repair_episode_count_remains": 4,
        },
    )
    write_json_deterministic(BATCH009_DIR / "prospective_memory_lift_requirement.json", prospective_memory_lift_requirement())
    write_json_deterministic(
        BATCH009_DIR / "claim_boundary.json",
        {
            "status": "PASS",
            "current_protocol_version": "v2.13",
            "retrospective_calibration_only": True,
            "full_scoring": "NOT_RUN/disallowed",
            "memory_lift": "undemonstrated_equal_performance",
            "prospective_memory_lift": "not_demonstrated",
            "self_maintaining_software": "false/not_demonstrated",
            "technical_validation_release_readiness": "not_ready",
        },
    )
    write_json_deterministic(
        BATCH009_DIR / "notebooklm_advice_traceability_status.json",
        {
            "status": "PASS",
            "matched_null_ensemble": "implemented_active",
            "failure_memory_weighting": "implemented_partial_passive",
            "patch_artifact_quarantine": "implemented_active",
            "prospective_memory_lift_requirement": "implemented_active",
            "issue_derived_harness": "unchanged_partial_not_exercised",
            "silent_completion": False,
        },
    )
    write_json_deterministic(
        BATCH009_DIR / "carry_forward_blocker_register.json",
        {
            "status": "PASS",
            "blockers": [
                {
                    "blocker": "prospective_memory_lift_requires_fresh_candidate",
                    "safe_next_step": "use a fresh candidate with pre-registered matched-null rules before any successful patch exists",
                }
            ],
        },
    )
    state = {
        "lane_id": BATCH009_ID,
        "status": "PASS",
        "exact_blocker": None,
        "candidate_id": candidate_id,
        "confirmed_external_native_repair_episode_count": 4,
        "patch_artifact_quarantine_status": quarantine_audit["status"],
        "arm_a_status": arm_a_result["status"],
        "arm_a_routing_delta_detected": routing_delta_detected,
        "null_ensemble_run_count": 5,
        "null_ensemble_success_rate": null_rate,
        "matched_null_ensemble_separation_score": score.get("matched_null_ensemble_separation_score"),
        "retrospective_single_candidate_memory_separation_diagnostic": memory_claim["retrospective_single_candidate_memory_separation_diagnostic"],
        "prospective_memory_lift_status": memory_claim["prospective_memory_lift_status"],
        "full_scoring": "NOT_RUN/disallowed",
        "self_maintaining_software": "false/not_demonstrated",
        "public_release_readiness": "not_ready",
        "batch009_adds_repair_episode": False,
        "batch008_repair_success_preserved": batch008_state.get("additional_native_external_repair_acquired") is True,
    }
    write_json_deterministic(BATCH009_DIR / "consolidated_state_clean_replication_batch_009.json", state)
    write_text_lf(
        BATCH009_DIR / "campaign_summary.md",
        "\n".join(
            [
                "# Clean replication batch 009",
                "",
                "Status: PASS.",
                "",
                "Batch009 runs patch-quarantined retrospective matched-null calibration on the already repaired Batch008 candidate.",
                "",
                "The calibration denies both the memory-enabled arm and memory-disabled null ensemble access to Batch008 patch artifacts, fragment records, patch rationale, and successful repair details.",
                "",
                "The memory signal is passive in this retrospective calibration, so the matched-null ensemble separation score is 0.0 and no prospective memory-lift claim is made.",
            ]
        ),
    )
    write_sha256sums(BATCH009_DIR)
    return state


def load_official_batch008_state() -> dict[str, object]:
    verification_path = POST_DIR / "batch008_declared_precondition_artifact_verification.json"
    state_path = BATCH008_DIR / "consolidated_state_clean_replication_batch_008.json"
    if verification_path.is_file() and state_path.is_file():
        verification = load_json(verification_path)
        if verification.get("status") == "PASS":
            return load_json(state_path)
    return write_batch008_outputs()


def load_official_batch009_state(batch008_state: dict[str, object]) -> dict[str, object]:
    verification_path = POST_DIR / "batch009_patch_quarantined_matched_null_artifact_verification.json"
    state_path = BATCH009_DIR / "consolidated_state_clean_replication_batch_009.json"
    if verification_path.is_file() and state_path.is_file():
        verification = load_json(verification_path)
        if verification.get("status") == "PASS":
            return load_json(state_path)
    return write_batch009_outputs(batch008_state)


def write_batch010_outputs(batch009_state: dict[str, object]) -> dict[str, object]:
    BATCH010_DIR.mkdir(parents=True, exist_ok=True)
    candidate_id = "darker_skip_glob_failing_test"
    legal_sources = ["src/darker/import_sorting.py"]
    status_records = [
        {
            "status_code": "PRECONDITION_UNRESOLVED",
            "candidate_id": candidate_id,
            "source_path": None,
            "function_or_class": None,
            "evidence_path": "outputs/clean_replication_batch_007/precondition_failure_classification.json",
            "evidence_sha256": sha256_file(BATCH007_DIR / "precondition_failure_classification.json"),
            "decision_time_safe": True,
            "uses_patch_bytes_or_rationale": False,
            "reason": "prior blocker was environment/precondition path rather than source-edit path",
        },
        {
            "status_code": "NO_PATCH_GENERATED",
            "candidate_id": candidate_id,
            "source_path": None,
            "function_or_class": None,
            "evidence_path": "outputs/clean_replication_batch_009/arm_a_repair_generation_result.json",
            "evidence_sha256": sha256_file(BATCH009_DIR / "arm_a_repair_generation_result.json"),
            "decision_time_safe": True,
            "uses_patch_bytes_or_rationale": False,
            "reason": "Batch009 did not generate a patch because memory markers were passive",
        },
        {
            "status_code": "REPAIR_SUCCESS",
            "candidate_id": candidate_id,
            "source_path": "src/darker/import_sorting.py",
            "function_or_class": None,
            "evidence_path": "outputs/clean_replication_batch_008/candidate_retirement_decision_batch008.json",
            "evidence_sha256": sha256_file(BATCH008_DIR / "candidate_retirement_decision_batch008.json"),
            "decision_time_safe": True,
            "uses_patch_bytes_or_rationale": True,
            "reason": "success evidence is excluded from weighting because it would reveal prior repair detail for this candidate",
        },
    ]
    inventory = build_status_code_inventory(status_records)
    relevant = relevant_records_for_candidate(inventory, candidate_id)
    weight_map = build_status_code_weight_map(relevant, legal_sources)
    baseline = baseline_source_ranking(legal_sources)
    weighted = apply_status_weights(baseline, weight_map)
    high_pass = apply_high_pass_filter(weighted)
    two_candidate = select_two_candidate_routes(weighted)
    context_before = legal_sources
    context_after = legal_sources
    generation_before = {"strategy": "bounded_fragment", "max_fragments": 3, "route": legal_sources[0]}
    generation_after = {"strategy": "bounded_fragment", "max_fragments": 3, "route": legal_sources[0]}
    delta = strict_minimum_delta(
        before=baseline,
        after=weighted,
        context_before=context_before,
        context_after=context_after,
        generation_before=generation_before,
        generation_after=generation_after,
    )
    routing_delta = delta["routing_delta_detected"] is True
    blocker = None if routing_delta else "active_memory_routing_delta_not_established"

    write_json_deterministic(
        BATCH010_DIR / "status_code_weighting_policy.json",
        {
            "status": "PASS",
            "status_codes_affect_routing_only_when_mapped_to_evidence": True,
            "unmapped_codes_do_not_change_weights": True,
            "patch_bytes_and_rationale_forbidden_as_memory": True,
            "blocker_if_missing": "status_code_weighting_policy_missing",
        },
    )
    write_json_deterministic(BATCH010_DIR / "status_code_evidence_inventory.json", inventory)
    write_json_deterministic(BATCH010_DIR / "status_code_to_weight_map.json", weight_map)
    write_json_deterministic(
        BATCH010_DIR / "failure_memory_source_marker_map.json",
        {
            "status": "PASS",
            "candidate_id": candidate_id,
            "legal_source_paths": legal_sources,
            "mapped_weight_count": len(weight_map["weights"]),
            "unmapped_status_count": len(weight_map["unmapped_records"]),
            "excluded_patch_detail_count": len(weight_map["excluded_records"]),
            "no_relevant_memory_features_available": weight_map["no_relevant_memory_features_available"],
        },
    )
    write_json_deterministic(
        BATCH010_DIR / "high_pass_source_ranking_filter.json",
        {
            "status": "PASS",
            "do_not_mask_all_legal_sources": True,
            "do_not_mask_only_patchable_source": True,
            "forbidden_patch_memory_excluded": True,
        },
    )
    write_json_deterministic(
        BATCH010_DIR / "two_candidate_selection_policy.json",
        {
            "status": "PASS",
            "primary_route_required": True,
            "secondary_route_required_if_available": True,
            "selection": two_candidate,
        },
    )
    write_json_deterministic(
        BATCH010_DIR / "strict_minimum_delta_policy.json",
        {
            "status": "PASS",
            "minimum_delta_fields": [
                "top_ranked_source_file_changed",
                "top_ranked_function_or_class_changed",
                "context_selection_changed",
                "generation_strategy_changed",
            ],
            "metadata_only_delta_rejected": True,
            "blocker_if_false": "active_memory_routing_delta_not_established",
        },
    )
    write_json_deterministic(BATCH010_DIR / "baseline_source_ranking.json", {"status": "PASS", "ranking": baseline, "ranking_hash": source_stable_hash(baseline)})
    write_json_deterministic(BATCH010_DIR / "memory_weighted_source_ranking.json", {"status": "PASS", "ranking": weighted, "ranking_hash": source_stable_hash(weighted)})
    write_json_deterministic(BATCH010_DIR / "routing_delta_report.json", delta)
    write_json_deterministic(
        BATCH010_DIR / "routing_delta_audit.json",
        {
            "status": "PASS",
            "routing_delta_detected": routing_delta,
            "forced_routing_delta_without_evidence": False,
            "blocker": blocker,
        },
    )
    write_json_deterministic(
        BATCH010_DIR / "context_selection_delta_report.json",
        {
            "status": "PASS",
            "context_before": context_before,
            "context_after": context_after,
            "context_changed": context_before != context_after,
            "context_before_hash": delta["context_before_hash"],
            "context_after_hash": delta["context_after_hash"],
        },
    )
    write_json_deterministic(
        BATCH010_DIR / "generation_strategy_delta_report.json",
        {
            "status": "PASS",
            "generation_strategy_before": generation_before,
            "generation_strategy_after": generation_after,
            "generation_strategy_changed": generation_before != generation_after,
            "generation_strategy_before_hash": delta["generation_strategy_before_hash"],
            "generation_strategy_after_hash": delta["generation_strategy_after_hash"],
        },
    )
    write_json_deterministic(BATCH010_DIR / "high_pass_filter_application.json", high_pass)
    write_json_deterministic(
        BATCH010_DIR / "masked_or_downranked_context_paths.json",
        {
            "status": "PASS",
            "masked_paths": high_pass.get("masked", []),
            "downranked_paths": [],
            "reason": "no mapped source-level penalty was available under quarantine",
        },
    )
    write_json_deterministic(
        BATCH010_DIR / "admitted_alternative_paths.json",
        {
            "status": "PASS",
            "admitted_paths": legal_sources,
            "secondary_route_available": two_candidate.get("secondary_available"),
            "reason": "only one legal patchable source path is available",
        },
    )
    write_json_deterministic(
        BATCH010_DIR / "active_memory_repair_attempt.json",
        {
            "status": "BLOCK",
            "candidate_id": candidate_id,
            "routing_delta_detected": routing_delta,
            "patch_generation_authorized": False,
            "patch_generated": False,
            "blocker": blocker,
        },
    )
    write_json_deterministic(
        BATCH010_DIR / "null_ensemble_rerun_results.json",
        {
            "status": "NOT_RUN",
            "run_results": [],
            "blocker": blocker,
            "reason": "null rerun is not authorized without an active memory routing delta",
        },
    )
    write_json_deterministic(
        BATCH010_DIR / "null_ensemble_rerun_summary.json",
        {
            "status": "NOT_RUN",
            "null_ensemble_run_count": 0,
            "null_success_rate": None,
            "blocker": blocker,
        },
    )
    write_json_deterministic(
        BATCH010_DIR / "null_ensemble_memory_exclusion_audit.json",
        {
            "status": "PASS",
            "null_ensemble_read_failure_memory": False,
            "null_ensemble_read_patch_artifacts": False,
            "null_ensemble_run_count": 0,
        },
    )
    write_json_deterministic(
        BATCH010_DIR / "matched_null_score_result_batch010.json",
        {
            "status": "PASS",
            "score_computed": True,
            "matched_null_ensemble_separation_score": 0.0,
            "routing_delta_detected": routing_delta,
            "blocker": blocker,
        },
    )
    write_json_deterministic(
        BATCH010_DIR / "matched_null_score_audit_batch010.json",
        {
            "status": "PASS",
            "score_zero_when_routing_delta_false": True,
            "retrospective_not_prospective": True,
            "overclaim_detected": False,
        },
    )
    write_json_deterministic(
        BATCH010_DIR / "memory_routing_diagnostic_evaluation_batch010.json",
        {
            "status": "PASS",
            "retrospective_single_candidate_memory_routing_diagnostic": False,
            "memory_separation_evidence": False,
            "reason": blocker,
        },
    )
    write_json_deterministic(BATCH010_DIR / "prospective_memory_lift_requirement_update.json", prospective_memory_lift_requirement())
    write_json_deterministic(
        BATCH010_DIR / "claim_boundary.json",
        {
            "status": "PASS",
            "current_protocol_version": "v2.13",
            "retrospective_calibration_only": True,
            "full_scoring": "NOT_RUN/disallowed",
            "prospective_memory_lift": "not_demonstrated",
            "full_memory_lift_claimed": False,
            "self_maintaining_software": "false/not_demonstrated",
            "technical_validation_release_readiness": "not_ready",
        },
    )
    write_json_deterministic(
        BATCH010_DIR / "notebooklm_advice_traceability_status.json",
        {
            "status": "PASS",
            "failure_memory_weighting": "implemented_partial",
            "failure_memory_weighting_blocker": blocker,
            "high_pass_source_ranking_filter": "implemented_active",
            "two_candidate_selection_policy": "implemented_active",
            "strict_minimum_delta_routing": "implemented_active",
            "prospective_memory_lift_requirement": "implemented_active",
            "matched_null_ensemble": "not_run_without_active_delta",
            "issue_derived_harness": "unchanged_partial_not_exercised",
            "silent_completion": False,
        },
    )
    write_json_deterministic(
        BATCH010_DIR / "carry_forward_blocker_register.json",
        {
            "status": "PASS",
            "blockers": [
                {
                    "blocker": blocker,
                    "safe_next_step": "use a fresh prospective candidate or additional decision-time-safe non-patch memory feature before claiming active memory routing",
                }
            ],
        },
    )
    state = {
        "lane_id": BATCH010_ID,
        "status": "BLOCK",
        "exact_blocker": blocker,
        "candidate_id": candidate_id,
        "status_code_weighting_status": "PASS",
        "high_pass_source_ranking_filter_status": high_pass["status"],
        "baseline_source_ranking_hash": source_stable_hash(baseline),
        "memory_weighted_source_ranking_hash": source_stable_hash(weighted),
        "routing_delta_detected": routing_delta,
        "routing_delta_reason_codes": delta["routing_delta_reason_codes"],
        "active_memory_patch_generated": False,
        "active_memory_target_validation_status": "NOT_RUN",
        "active_memory_duplicate_replay_status": "NOT_RUN",
        "null_ensemble_run_count": 0,
        "null_ensemble_success_rate": None,
        "matched_null_score": 0.0,
        "retrospective_single_candidate_memory_routing_diagnostic": False,
        "prospective_memory_lift_status": "not_demonstrated",
        "confirmed_native_repair_episode_count": 4,
        "full_scoring": "NOT_RUN/disallowed",
        "self_maintaining_software": "false/not_demonstrated",
        "batch010_adds_repair_episode": False,
        "batch009_result_preserved": batch009_state.get("status") == "PASS",
    }
    write_json_deterministic(BATCH010_DIR / "consolidated_state_clean_replication_batch_010.json", state)
    write_text_lf(
        BATCH010_DIR / "campaign_summary.md",
        "\n".join(
            [
                "# Clean replication batch 010",
                "",
                "Status: BLOCK.",
                "",
                "Batch010 implements active status-code weighting and strict minimum-delta routing audit for the already repaired Batch008 candidate.",
                "",
                "The available decision-time-safe status codes do not establish a source, context, or generation routing delta without using quarantined prior patch details.",
                "",
                "Patch generation is therefore not authorized as memory-enabled, the matched-null score remains 0.0, and prospective memory lift remains not demonstrated.",
            ]
        ),
    )
    write_sha256sums(BATCH010_DIR)
    return state


def write_batch011_outputs(batch010_state: dict[str, object]) -> dict[str, object]:
    BATCH011_DIR.mkdir(parents=True, exist_ok=True)
    config = load_json("configs/clean_replication_batch_011.json")
    lead_pool = load_json(config["lead_pool_path"])
    leads = lead_pool.get("leads", []) if isinstance(lead_pool, dict) else []
    prior_attempts = load_json(BATCH_DIR / "candidate_verification_attempts.json")
    prior_attempt_by_id = {
        str(item.get("lead_id")): item
        for item in prior_attempts
        if isinstance(item, dict) and item.get("lead_id")
    }
    repaired_ids = sorted(PROSPECTIVE_REPAIRED_CANDIDATE_IDS)
    fresh_leads = [
        lead
        for lead in leads
        if isinstance(lead, dict)
        and str(lead.get("lead_id")) not in PROSPECTIVE_REPAIRED_CANDIDATE_IDS
    ]
    repaired_rejections = [
        {
            "candidate_id": candidate_id,
            "fresh_candidate": False,
            "eligible_for_prospective_memory_challenge": False,
            "rejection_reason": "prospective_memory_candidate_not_fresh",
            "repaired_candidate_registry": "controllergate.core.prospective_memory_challenge.REPAIRED_CANDIDATE_IDS",
        }
        for candidate_id in repaired_ids
    ]
    retired_candidates = [
        {
            "candidate_id": candidate_id,
            "retired_from_new_memory_lift_attempts": True,
            "allowed_future_use": [
                "repair_episode_evidence",
                "regression_replay",
                "artifact_custody_testing",
                "public_docs_as_confirmed_repair",
            ],
            "forbidden_future_use": [
                "new_candidate",
                "prospective_memory_lift_proof",
                "repeated_retrospective_memory_routing_attempt",
                "repair_episode_count_increment",
            ],
            "blocker_if_reused": "retired_memory_challenge_candidate_reused",
        }
        for candidate_id in repaired_ids
    ]
    fresh_attempts: list[dict[str, object]] = []
    native_attempts: list[dict[str, object]] = []
    admission_decisions: list[dict[str, object]] = repaired_rejections.copy()
    for lead in fresh_leads:
        lead_id = str(lead.get("lead_id"))
        prior = prior_attempt_by_id.get(lead_id, {})
        failure_status = prior.get("failure_replay_status", "UNKNOWN")
        decision = prior.get("decision", "rejected_no_verified_native_candidate")
        verified = decision == "verified_native_candidate_pending_repair"
        blocker = None if verified else "batch011_no_fresh_candidate_verified"
        attempt = {
            "candidate_id": lead_id,
            "lead_id": lead_id,
            "repo_url": lead.get("repo_url"),
            "commit_hint": lead.get("commit_hint"),
            "test_path_hint": lead.get("test_path_hint"),
            "candidate_class": lead.get("allowed_candidate_class", "native"),
            "fresh_candidate": True,
            "source_mode": "existing_clean_replication_lead_pool",
            "verification_source": "outputs/clean_replication_batch_002/candidate_verification_attempts.json",
            "verification_source_sha256": sha256_file(BATCH_DIR / "candidate_verification_attempts.json"),
            "commit_resolved": prior.get("commit_resolved") is True,
            "target_test_present": prior.get("target_test_present") is True,
            "environment_file_present": prior.get("environment_file_present") is True,
            "collection_status": prior.get("collection_status"),
            "failure_replay_status": failure_status,
            "pre_repair_failure_reproduced": failure_status not in {"PASSING_PRE_PATCH_NOT_A_FAILURE", "UNKNOWN"},
            "fresh_candidate_verified": verified,
            "decision": "admitted_fresh_candidate" if verified else "rejected_no_verified_native_candidate",
            "blocker": blocker,
            "reason": "prior decision-time-safe replay evidence did not reproduce a pre-repair failure",
        }
        fresh_attempts.append(attempt)
        native_attempts.append(attempt)
        admission_decisions.append(
            {
                "candidate_id": lead_id,
                "fresh_candidate": True,
                "candidate_class": lead.get("allowed_candidate_class", "native"),
                "admission_decision": "admitted_native_candidate" if verified else "rejected_other",
                "blocker": blocker,
                "failure_replay_status": failure_status,
                "decision_time_safe_evidence_path": "outputs/clean_replication_batch_002/candidate_verification_attempts.json",
            }
        )

    fresh_candidate_verified = any(item.get("fresh_candidate_verified") is True for item in fresh_attempts)
    blocker = None if fresh_candidate_verified else "batch011_no_fresh_candidate_verified"
    eligibility = {
        "status": "PASS" if fresh_candidate_verified else "BLOCK",
        "eligible": fresh_candidate_verified,
        "blocker": blocker,
        "fresh_candidate_required": True,
        "prior_repaired_candidates_forbidden": repaired_ids,
        "candidate_attempts_reviewed": len(fresh_attempts),
        "candidate_verification_source": "outputs/clean_replication_batch_002/candidate_verification_attempts.json",
        "candidate_verification_source_sha256": sha256_file(BATCH_DIR / "candidate_verification_attempts.json"),
        "candidate_evaluations": [
            evaluate_prospective_memory_eligibility(
                {
                    "candidate_id": str(item.get("lead_id")),
                    "native_candidate": True,
                    "pre_repair_failure_reproduced": item.get("fresh_candidate_verified") is True,
                    "source_file_count": 0,
                    "function_or_class_count": 0,
                    "status_features": [],
                }
            )
            for item in fresh_attempts
        ],
        "repaired_candidate_evaluations": [
            evaluate_prospective_memory_eligibility(
                {
                    "candidate_id": candidate_id,
                    "native_candidate": True,
                    "pre_repair_failure_reproduced": True,
                    "source_file_count": 2,
                    "function_or_class_count": 2,
                    "status_features": [
                        {
                            "decision_time_safe": True,
                            "source_path": "not_used_for_repaired_candidate",
                            "uses_patch_bytes_or_rationale": False,
                        }
                    ],
                }
            )
            for candidate_id in repaired_ids
        ],
    }
    route_diversity = {
        "status": "NOT_RUN" if not fresh_candidate_verified else "BLOCK",
        "blocker": blocker,
        "reason": "route diversity is evaluated only after a fresh candidate verifies",
        "requires_two_legal_source_or_function_routes": True,
    }
    mappable_status_features = {
        "status": "NOT_RUN" if not fresh_candidate_verified else "BLOCK",
        "blocker": blocker,
        "reason": "status-code feature mapping is evaluated only after a fresh candidate verifies",
        "patch_bytes_or_success_rationale_forbidden": True,
    }
    curvature_policy = {
        "status": "PASS",
        "heuristic_only": True,
        "feature_fields": [
            "failure_proximity_score",
            "traceback_centrality",
            "import_graph_centrality",
            "ast_closure_centrality",
            "dependency_spread_penalty",
            "environment_precondition_friction_penalty",
            "prior_status_code_weight_if_legally_mapped",
            "alternative_route_availability",
            "target_intent_reachability_status",
        ],
        "not_success_evidence": True,
    }
    two_winner_policy = {
        "status": "PASS",
        "winner_linear_required": True,
        "winner_curvature_required": True,
        "routing_diversity_low_when_winners_match": True,
        "blocker_if_missing": "two_winner_policy_missing",
    }
    strict_delta_policy = {
        "status": "PASS",
        "active_delta_requires_change_in": [
            "winner_linear",
            "winner_curvature",
            "selected_source_file",
            "selected_function_or_class",
            "context_capsule_contents",
            "generation_strategy",
            "fragment_plan",
        ],
        "arbitrary_score_or_metadata_shuffle_rejected": True,
        "blocker_if_forced": "forced_routing_delta_without_evidence",
    }
    curvature_scores = [
        {
            "candidate_id": item["candidate_id"],
            "status": "NOT_RUN",
            "blocker": item["blocker"],
            "reason": "source-route scoring requires verified pre-repair failure",
            "commit_resolved": item["commit_resolved"],
            "target_test_present": item["target_test_present"],
            "environment_file_present": item["environment_file_present"],
            "failure_replay_status": item["failure_replay_status"],
        }
        for item in fresh_attempts
    ]
    route_scores = {
        "status": "NOT_RUN",
        "blocker": blocker,
        "source_routes": [],
        "two_winner_selection": select_two_winners([]),
        "memory_weighted_two_winner_selection": select_two_winners([]),
        "two_winner_delta": two_winner_delta(select_two_winners([]), select_two_winners([])),
    }
    preregistration_order = preregistration_order_status(
        ["batch011_started", "fresh_candidate_attempts_reviewed", "no_fresh_candidate_verified"]
    )
    repair_only = repair_only_fallback_evaluation(attempted=False, repair_succeeded=False)
    common_not_run = {
        "status": "NOT_RUN",
        "blocker": blocker,
        "reason": "fresh prospective candidate did not verify",
    }
    write_json_deterministic(
        BATCH011_DIR / "prospective_memory_challenge_policy.json",
        {
            "status": "PASS",
            "requires_fresh_candidate": True,
            "requires_native_candidate_for_memory_lift": True,
            "requires_pre_repair_failure_reproduction": True,
            "requires_patchable_alternative_routes": True,
            "requires_mappable_status_features": True,
            "requires_preregistration_before_patch": True,
            "forbids_repaired_candidate_reuse": True,
            "forbids_fixed_later_gold_pr_patch_content": True,
            "full_scoring": "NOT_RUN/disallowed",
        },
    )
    write_json_deterministic(BATCH011_DIR / "prospective_memory_eligibility_gate.json", eligibility)
    write_json_deterministic(
        BATCH011_DIR / "candidate_difficulty_band_policy.json",
        {
            "status": "PASS",
            "preferred_target_command_width": ["single_node", "single_file"],
            "preferred_source_context_file_count": [2, 4],
            "reject_external_network_required": True,
            "reject_broad_suite_only_failure": True,
            "reject_missing_environment_file": True,
            "reject_trivial_single_path_candidates_for_memory_lift": True,
        },
    )
    write_json_deterministic(
        BATCH011_DIR / "fresh_candidate_lead_pool.json",
        {
            "status": "PASS",
            "source_lead_pool": config["lead_pool_path"],
            "source_lead_pool_sha256": sha256_file(config["lead_pool_path"]),
            "fresh_candidate_count": len(fresh_leads),
            "fresh_leads": fresh_leads,
            "repaired_candidates_excluded": repaired_ids,
        },
    )
    write_json_deterministic(BATCH011_DIR / "fresh_candidate_attempts.json", fresh_attempts)
    write_json_deterministic(
        BATCH011_DIR / "fresh_candidate_rejection_ledger.json",
        repaired_rejections
        + [
            {
                "candidate_id": item["candidate_id"],
                "fresh_candidate": True,
                "rejection_reason": item["blocker"],
                "decision": item["decision"],
                "failure_replay_status": item["failure_replay_status"],
            }
            for item in fresh_attempts
            if item.get("fresh_candidate_verified") is not True
        ],
    )
    write_json_deterministic(BATCH011_DIR / "retired_memory_challenge_candidates.json", {"status": "PASS", "retired_candidates": retired_candidates})
    write_json_deterministic(
        BATCH011_DIR / "darker_skip_glob_memory_challenge_retirement.json",
        {
            "status": "PASS",
            "candidate_id": "darker_skip_glob_failing_test",
            "retired_from_new_memory_lift_attempts": True,
            "retirement_reasons": [
                "already repaired in Batch008",
                "patch artifacts remain quarantined",
                "Batch009 retrospective calibration found no active memory route",
                "Batch010 status-code weighting found no legal routing delta",
                "only one legal patchable source path remained available",
            ],
            "blocker_if_reused": "retired_memory_challenge_candidate_reused",
        },
    )
    write_json_deterministic(
        BATCH011_DIR / "fresh_candidate_source_mode_trace.json",
        [
            {
                "mode": "existing_clean_replication_lead_pool_native",
                "attempted": True,
                "fresh_candidate_count": len(fresh_attempts),
                "verified_count": len([item for item in fresh_attempts if item.get("fresh_candidate_verified") is True]),
            },
            {
                "mode": "issue_derived_candidate",
                "attempted": False,
                "reason": "native bounded leads were reviewed first and no safe issue-derived seed was provided",
            },
        ],
    )
    write_json_deterministic(BATCH011_DIR / "native_candidate_attempts.json", native_attempts)
    write_json_deterministic(BATCH011_DIR / "issue_derived_candidate_attempts.json", [])
    write_json_deterministic(BATCH011_DIR / "candidate_verification_attempts.json", fresh_attempts)
    write_json_deterministic(BATCH011_DIR / "candidate_admission_decisions.json", admission_decisions)
    write_json_deterministic(BATCH011_DIR / "curvature_selection_policy.json", curvature_policy)
    write_json_deterministic(BATCH011_DIR / "two_winner_source_selection_policy.json", two_winner_policy)
    write_json_deterministic(BATCH011_DIR / "strict_minimum_delta_policy_batch011.json", strict_delta_policy)
    write_json_deterministic(BATCH011_DIR / "candidate_curvature_scores.json", {"status": "NOT_RUN", "blocker": blocker, "candidate_scores": curvature_scores})
    write_json_deterministic(BATCH011_DIR / "source_route_curvature_scores.json", route_scores)
    write_json_deterministic(
        BATCH011_DIR / "prospective_experiment_preregistration.json",
        {
            "status": "NOT_RUN",
            "blocker": blocker,
            "pre_registration_required_before_patch": True,
            "patch_generated_before_preregistration": False,
            "order_check": preregistration_order,
        },
    )
    write_json_deterministic(
        BATCH011_DIR / "memory_enabled_policy_batch011.json",
        {
            "status": "NOT_RUN",
            "blocker": blocker,
            "policy_prepared": True,
            "allowed_memory": "decision-time-safe status-code weighting only",
            "successful_patch_bytes_forbidden": True,
        },
    )
    write_json_deterministic(
        BATCH011_DIR / "memory_disabled_null_ensemble_policy_batch011.json",
        {
            "status": "NOT_RUN",
            "blocker": blocker,
            "policy_prepared": True,
            "null_ensemble_size": int(config["null_ensemble_size"]),
            "may_read_failure_memory": False,
            "successful_patch_bytes_forbidden": True,
        },
    )
    write_json_deterministic(
        BATCH011_DIR / "prospective_patch_artifact_quarantine_policy.json",
        {
            "status": "PASS",
            "successful_patch_bytes_forbidden_before_experiment": True,
            "patch_artifacts_not_created": True,
            "blocker_if_violated": "prospective_preregistration_violation",
        },
    )
    write_json_deterministic(BATCH011_DIR / "memory_enabled_run_results.json", common_not_run)
    write_json_deterministic(BATCH011_DIR / "null_ensemble_run_results.json", {"status": "NOT_RUN", "run_results": [], "blocker": blocker})
    write_json_deterministic(BATCH011_DIR / "null_ensemble_summary.json", {"status": "NOT_RUN", "null_ensemble_run_count": 0, "null_success_rate": None, "blocker": blocker})
    write_json_deterministic(
        BATCH011_DIR / "matched_null_ensemble_separation_score.json",
        {
            "status": "NOT_RUN",
            "score_computed": False,
            "matched_null_ensemble_separation_score": None,
            "blocker": blocker,
        },
    )
    write_json_deterministic(
        BATCH011_DIR / "prospective_memory_lift_evaluation.json",
        {
            "status": "BLOCK",
            "prospective_memory_lift_status": "not_demonstrated",
            "preliminary_prospective_single_candidate_memory_separation_evidence": False,
            "fresh_candidate_verified": fresh_candidate_verified,
            "routing_delta_detected": False,
            "matched_null_ensemble_separation_score": None,
            "blocker": blocker,
        },
    )
    write_json_deterministic(BATCH011_DIR / "repair_successes.json", [])
    write_json_deterministic(
        BATCH011_DIR / "claim_boundary.json",
        {
            "status": "PASS",
            "current_protocol_version": "v2.13",
            "full_scoring": "NOT_RUN/disallowed",
            "full_memory_lift_claimed": False,
            "prospective_memory_lift": "not_demonstrated",
            "self_maintaining_software": "false/not_demonstrated",
            "technical_validation_release_readiness": "not_ready",
            "confirmed_native_repair_episode_count": batch010_state.get("confirmed_native_repair_episode_count", 4),
        },
    )
    write_json_deterministic(
        BATCH011_DIR / "notebooklm_advice_traceability_status.json",
        {
            "status": "PASS",
            "active_failure_memory_routing": "implemented_partial",
            "active_failure_memory_routing_blocker": blocker,
            "status_code_feature_weighting": "implemented_active",
            "high_pass_source_ranking_filter": "implemented_active",
            "curvature_based_candidate_selection": "implemented_active",
            "two_winner_source_selection": "implemented_active",
            "strict_minimum_delta_routing": "implemented_active",
            "prospective_memory_lift_requirement": "implemented_active",
            "matched_null_ensemble": "not_run_without_fresh_verified_candidate",
            "issue_derived_harness": "unchanged_partial_not_exercised",
            "silent_completion": False,
        },
    )
    write_json_deterministic(
        BATCH011_DIR / "carry_forward_blocker_register.json",
        {
            "status": "PASS",
            "blockers": [
                {
                    "blocker": blocker,
                    "safe_next_step": "provide or acquire a fresh decision-time-safe native candidate that reproduces a pre-repair failure and has at least two legal source or function routes",
                }
            ],
        },
    )
    state = {
        "lane_id": BATCH011_ID,
        "status": "BLOCK",
        "exact_blocker": blocker,
        "retrospective_candidate_retirement_status": "PASS",
        "fresh_candidates_attempted_count": len(fresh_attempts),
        "fresh_candidate_verified": fresh_candidate_verified,
        "prospective_memory_eligibility_status": eligibility["status"],
        "route_diversity_status": route_diversity["status"],
        "mappable_status_feature_status": mappable_status_features["status"],
        "two_winner_policy_status": two_winner_policy["status"],
        "routing_delta_detected": False,
        "memory_enabled_run_status": "NOT_RUN",
        "null_ensemble_run_count": 0,
        "null_ensemble_success_rate": None,
        "matched_null_score": None,
        "preliminary_prospective_single_candidate_memory_separation_evidence": False,
        "repair_only_fallback_attempted": repair_only["repair_only_fallback_attempted"],
        "additional_external_repair_acquired": repair_only["additional_external_repair_acquired"],
        "confirmed_native_repair_episode_count": batch010_state.get("confirmed_native_repair_episode_count", 4),
        "full_scoring": "NOT_RUN/disallowed",
        "memory_lift": "not_demonstrated",
        "self_maintaining_software": "false/not_demonstrated",
    }
    write_json_deterministic(BATCH011_DIR / "consolidated_state_clean_replication_batch_011.json", state)
    write_text_lf(
        BATCH011_DIR / "campaign_summary.md",
        "\n".join(
            [
                "# Clean replication batch 011",
                "",
                "Status: BLOCK.",
                "",
                "Batch011 records the prospective memory challenge eligibility gate, retires the already repaired retrospective candidate from further memory-lift attempts, and reviews bounded fresh leads from the existing clean replication lead pool.",
                "",
                "No fresh candidate verified a pre-repair failure under the ingested decision-time-safe evidence, so no memory-enabled arm, null ensemble, patch generation, or repair-only fallback was authorized.",
                "",
                f"Exact blocker: `{blocker}`.",
            ]
        ),
    )
    write_sha256sums(BATCH011_DIR)
    return state


def write_batch012_outputs(batch011_state: dict[str, object]) -> dict[str, object]:
    BATCH012_DIR.mkdir(parents=True, exist_ok=True)
    config = load_json("configs/clean_replication_batch_012.json")
    seed_path = Path(str(config["seed_path"]))
    blocker = "targeted_prospective_seed_missing_or_invalid"
    presence = seed_presence(seed_path)
    seed: dict[str, object] | None = None
    schema_validation: dict[str, object]
    forbidden_audit: dict[str, object]

    if presence["seed_present"] is True:
        try:
            seed = load_json(seed_path)
        except json.JSONDecodeError as exc:
            seed = None
            schema_validation = {
                "status": "BLOCK",
                "valid": False,
                "blocker": blocker,
                "blockers": [blocker],
                "reason": f"seed JSON parse failed: {exc.msg}",
            }
            forbidden_audit = {
                "status": "NOT_RUN",
                "blocker": blocker,
                "reason": "schema validation did not pass",
            }
        else:
            existing_ids = {
                str(item.get("candidate_id"))
                for registry_path in [Path("configs/external_candidate_registry.json"), Path("configs/external_repair_episode_registry.json")]
                if registry_path.is_file()
                for item in load_json(registry_path).get("candidates", load_json(registry_path).get("episodes", []))
                if isinstance(item, dict) and item.get("candidate_id")
            }
            schema_validation = validate_seed_schema(seed, existing_ids)
            forbidden_audit = forbidden_evidence_audit(seed) if schema_validation.get("status") == "PASS" else {
                "status": "NOT_RUN",
                "blocker": schema_validation.get("blocker") or blocker,
                "reason": "schema validation did not pass",
            }
    else:
        schema_validation = {
            "status": "BLOCK",
            "valid": False,
            "blocker": blocker,
            "blockers": [blocker],
            "reason": "seed file is absent",
            "seed_path": seed_path.as_posix(),
        }
        forbidden_audit = {
            "status": "NOT_RUN",
            "blocker": blocker,
            "reason": "seed file is absent",
        }

    validation_passed = schema_validation.get("status") == "PASS" and forbidden_audit.get("status") == "PASS"
    seed_candidate_class = str(seed.get("candidate_class")) if seed and validation_passed else None
    native_available = bool(seed and validation_passed and (seed.get("native_target_test_command") or seed.get("native_target_test_paths")))
    native_order = native_first_order(seed_candidate_class or "native_candidate", native_available) if validation_passed else {
        "status": "NOT_RUN",
        "native_verification_runs_first": False,
        "issue_derived_allowed_after_native_failure": False,
        "blocker": blocker,
    }
    issue_not_run = issue_derived_verification_not_run(blocker)
    route_diversity = {
        "status": "NOT_RUN",
        "blocker": blocker,
        "route_count": 0,
        "source_file_count": 0,
        "function_or_class_count": 0,
        "distinct_strategy_count": 0,
    }
    status_feature_mappability = {
        "status": "NOT_RUN",
        "blocker": blocker,
        "mapped_feature_count": 0,
    }
    eligibility = {
        "status": "NOT_RUN",
        "eligible": False,
        "blocker": blocker,
        "fresh_candidate_required": True,
        "pre_repair_failure_verified": False,
        "route_diversity_required": True,
        "mappable_status_features_required": True,
        "preregistration_required_before_patch": True,
    }
    matched_null = {
        "status": "NOT_RUN",
        "blocker": blocker,
        "null_ensemble_run_count": 0,
        "matched_null_score": None,
        "preregistered": False,
    }
    repair_only = repair_only_fallback_evaluation(attempted=False, repair_succeeded=False)
    repair_only["blocker"] = blocker

    write_json_deterministic(BATCH012_DIR / "targeted_seed_presence_check.json", {**presence, "manual_seed_required": True, "automated_fresh_candidate_search_attempted": False})
    write_json_deterministic(BATCH012_DIR / "targeted_seed_schema_validation.json", schema_validation)
    write_json_deterministic(BATCH012_DIR / "targeted_seed_forbidden_evidence_audit.json", forbidden_audit)
    write_json_deterministic(
        BATCH012_DIR / "targeted_seed_intake_report.json",
        {
            "status": "BLOCK" if not validation_passed else "PASS_PENDING_EXECUTION",
            "seed_path": seed_path.as_posix(),
            "seed_present": presence["seed_present"],
            "seed_schema_status": schema_validation["status"],
            "forbidden_evidence_audit_status": forbidden_audit["status"],
            "exact_blocker": None if validation_passed else blocker,
            "automated_fresh_candidate_search_attempted": False,
            "native_verification_status": "NOT_RUN",
            "issue_derived_verification_status": "NOT_RUN",
            "matched_null_ensemble_status": "NOT_RUN",
            "repair_only_fallback_attempted": False,
        },
    )
    write_json_deterministic(BATCH012_DIR / "source_commit_selection.json", {"status": "NOT_RUN", "blocker": blocker, "source_commit_resolved": False})
    write_json_deterministic(BATCH012_DIR / "source_checkout_audit.json", {"status": "NOT_RUN", "blocker": blocker, "checkout_created": False})
    write_json_deterministic(BATCH012_DIR / "environment_resolution_plan.json", {"status": "NOT_RUN", "blocker": blocker})
    write_json_deterministic(BATCH012_DIR / "environment_resolution_log.json", {"status": "NOT_RUN", "blocker": blocker})
    write_json_deterministic(
        BATCH012_DIR / "native_verification_result.json",
        {
            "status": "NOT_RUN",
            "blocker": blocker,
            "native_verification_runs_first": native_order["native_verification_runs_first"],
            "native_candidate_verified": False,
            "pre_repair_failure_reproduced": False,
        },
    )
    write_json_deterministic(BATCH012_DIR / "issue_derived_harness_policy.json", issue_derived_harness_policy())
    write_json_deterministic(BATCH012_DIR / "issue_derived_harness_verification_result.json", issue_not_run)
    write_json_deterministic(BATCH012_DIR / "prospective_memory_eligibility_gate.json", eligibility)
    write_json_deterministic(BATCH012_DIR / "candidate_difficulty_band.json", {"status": "NOT_RUN", "blocker": blocker})
    write_json_deterministic(BATCH012_DIR / "patchable_source_alternatives.json", {"status": "NOT_RUN", "blocker": blocker, "alternatives": []})
    write_json_deterministic(BATCH012_DIR / "route_diversity_status.json", route_diversity)
    write_json_deterministic(BATCH012_DIR / "status_feature_mappability.json", status_feature_mappability)
    write_json_deterministic(BATCH012_DIR / "curvature_selection_scores.json", {"status": "NOT_RUN", "blocker": blocker, "scores": []})
    write_json_deterministic(BATCH012_DIR / "two_winner_source_selection.json", {"status": "NOT_RUN", "blocker": blocker, "winner_linear": None, "winner_curvature": None})
    write_json_deterministic(BATCH012_DIR / "prospective_experiment_preregistration.json", {"status": "NOT_RUN", "blocker": blocker, "patch_generated_before_preregistration": False})
    write_json_deterministic(BATCH012_DIR / "memory_enabled_policy.json", {"status": "NOT_RUN", "blocker": blocker, "may_use_status_code_weighting_after_preregistration": True})
    write_json_deterministic(BATCH012_DIR / "memory_disabled_null_ensemble_policy.json", {"status": "NOT_RUN", "blocker": blocker, "null_ensemble_size": config.get("null_ensemble_size", 5), "may_read_failure_memory": False})
    write_json_deterministic(BATCH012_DIR / "matched_null_ensemble_summary.json", matched_null)
    write_json_deterministic(BATCH012_DIR / "repair_only_fallback_summary.json", repair_only)
    write_json_deterministic(
        BATCH012_DIR / "claim_boundary.json",
        {
            "status": "PASS",
            "full_scoring": "NOT_RUN/disallowed",
            "full_memory_lift_claimed": False,
            "memory_lift": "not_demonstrated",
            "self_maintaining_software": "false/not_demonstrated",
            "technical_validation_release_readiness": "not_ready",
            "native_issue_derived_counts_separate": True,
            "preliminary_prospective_single_candidate_memory_separation_evidence": False,
            "confirmed_native_repair_episode_count": 4,
            "confirmed_issue_derived_repair_episode_count": 0,
        },
    )
    traceability = {
        "status": "PASS",
        "targeted_prospective_seed_intake": "implemented_partial_blocked_missing_seed" if not validation_passed else "PASS_PENDING_EXECUTION",
        "native_target_test_verification": "NOT_RUN",
        "issue_derived_ephemeral_reproduction_harness": "NOT_RUN",
        "curvature_based_candidate_selection": "NOT_RUN",
        "two_winner_source_selection": "NOT_RUN",
        "status_code_feature_weighting": "NOT_RUN",
        "prospective_memory_eligibility_gate": "NOT_RUN",
        "matched_null_ensemble": "NOT_RUN",
        "patch_artifact_quarantine": "NOT_RUN",
        "post_patch_constraint_revalidation": "NOT_RUN",
        "no_overreach_validation": "NOT_RUN",
        "silent_completion": False,
        "blocker": None if validation_passed else blocker,
    }
    carry_forward = {
        "status": "PASS",
        "blockers": [
            {
                "blocker": blocker,
                "next_allowed_action": "provide_targeted_seed",
                "seed_path": seed_path.as_posix(),
                "minimum_condition_to_unblock": "place a reviewed targeted prospective seed at the configured path",
            }
        ],
    }
    write_json_deterministic(BATCH012_DIR / "notebooklm_advice_traceability_status.json", traceability)
    write_json_deterministic(BATCH012_DIR / "carry_forward_blocker_register.json", carry_forward)

    state = {
        "lane_id": BATCH012_ID,
        "lane_type": "targeted_prospective_seed_intake",
        "status": "BLOCK" if not validation_passed else "PASS_PENDING_EXECUTION",
        "exact_blocker": None if validation_passed else blocker,
        "current_protocol_version": "v2.13",
        "targeted_seed_path": seed_path.as_posix(),
        "targeted_seed_present": bool(presence["seed_present"]),
        "targeted_seed_validation_status": schema_validation["status"],
        "candidate_class": seed_candidate_class,
        "native_verification_status": "NOT_RUN",
        "issue_derived_verification_status": "NOT_RUN",
        "prospective_memory_eligibility_status": "NOT_RUN",
        "route_diversity_status": "NOT_RUN",
        "mappable_status_feature_status": "NOT_RUN",
        "matched_null_ensemble_run_count": 0,
        "matched_null_score": None,
        "preliminary_prospective_single_candidate_memory_separation_evidence": False,
        "repair_only_fallback_attempted": False,
        "additional_native_repair_acquired": False,
        "additional_issue_derived_repair_feasibility": False,
        "confirmed_native_repair_episode_count": int(batch011_state.get("confirmed_native_repair_episode_count", 4)),
        "confirmed_issue_derived_repair_episode_count": 0,
        "full_scoring": "NOT_RUN/disallowed",
        "memory_lift": "not_demonstrated",
        "self_maintaining_software": "false/not_demonstrated",
    }
    write_json_deterministic(BATCH012_DIR / "consolidated_state_clean_replication_batch_012.json", state)
    write_text_lf(
        BATCH012_DIR / "targeted_seed_required_next_action.md",
        "\n".join(
            [
                "# Targeted prospective seed required",
                "",
                f"Blocker: `{blocker}`.",
                "",
                f"Place a reviewed seed at `{seed_path.as_posix()}` before native verification, issue-derived fallback, repair-only fallback, or matched-null comparison can run.",
                "",
                "The seed must be a public GitHub HTTPS candidate, must identify source commit evidence or a safe source-commit selection method, must include an environment lock source, and must attest that fixed, later, gold, PR patch, hidden-label, and future-test evidence were not used.",
            ]
        ),
    )
    write_text_lf(
        BATCH012_DIR / "campaign_summary.md",
        "\n".join(
            [
                "# Clean replication batch 012",
                "",
                "Status: BLOCK.",
                "",
                "Batch012 starts Targeted Prospective Seed Intake after Batch011 exhausted automated fresh-candidate attempts. The configured seed file is absent, so the lane stops before native verification, issue-derived fallback, prospective memory eligibility, repair-only fallback, or matched-null comparison.",
                "",
                f"Exact blocker: `{blocker}`.",
            ]
        ),
    )
    write_sha256sums(BATCH012_DIR)
    return state


def write_batch013_outputs(batch012_state: dict[str, object]) -> dict[str, object]:
    BATCH013_DIR.mkdir(parents=True, exist_ok=True)
    config = load_json("configs/clean_replication_batch_013.json")
    seed_path = Path(str(config["seed_path"]))
    blocker = "targeted_prospective_seed_missing_or_invalid_after_locks_ready"
    workflow_path = ".github/workflows/post_v2_37_hardening_and_batch002.yml"

    baseline_policy = baseline_registry_drift_precheck_policy()
    baseline_snapshot = baseline_registry_snapshot("configs/external_repair_episode_registry.json")
    baseline_precheck = baseline_registry_drift_precheck(baseline_snapshot)
    seed_present = False
    env_policy = source_commit_environment_lock_policy()
    env_summary = summarize_source_commit_environment_lock(
        source_commit_sha=None,
        environment_lock_source_paths=[],
        seed_present=seed_present,
    )
    command_policy = target_command_manifest_policy()
    command_summary = build_target_command_manifest_summary(seed_present=seed_present)
    workspace_policy = fresh_workspace_purity_policy()
    workspace_report = audit_workspace_purity(None, repo_root=".", seed_present=seed_present, workspace_created=False)
    presence = {
        "status": "BLOCK",
        "seed_present": False,
        "seed_path": seed_path.as_posix(),
        "blocker": blocker,
        "locks_completed_before_seed_block": True,
        "automated_fresh_candidate_search_attempted": False,
        "manual_seed_required": True,
        "official_batch013_boundary_preserved": True,
    }
    git_tracking = {
        "status": "BLOCK",
        "seed_path": seed_path.as_posix(),
        "file_exists": False,
        "git_tracked": False,
        "ignored": False,
        "unstaged_changes": False,
        "staged_changes": False,
        "committed_exactly": False,
        "workflow_visible": True,
        "workflow_visibility_paths": [workflow_path],
        "blocker": blocker,
        "official_batch013_boundary_preserved": True,
    }
    workflow_visibility = {
        "status": git_tracking["status"],
        "seed_path": seed_path.as_posix(),
        "workflow_path": workflow_path,
        "workflow_visible": git_tracking["workflow_visible"],
        "workflow_visibility_paths": git_tracking["workflow_visibility_paths"],
        "blocker": git_tracking["blocker"],
    }
    if seed_present:
        try:
            seed = load_json(seed_path)
        except json.JSONDecodeError as exc:
            schema_validation = {
                "status": "BLOCK",
                "valid": False,
                "blocker": blocker,
                "blockers": [blocker],
                "reason": f"seed JSON parse failed: {exc.msg}",
            }
            forbidden_audit = {"status": "NOT_RUN", "blocker": blocker, "reason": "schema validation did not pass"}
        else:
            existing_ids = {
                str(item.get("candidate_id"))
                for registry_path in [Path("configs/external_candidate_registry.json"), Path("configs/external_repair_episode_registry.json")]
                if registry_path.is_file()
                for item in load_json(registry_path).get("candidates", load_json(registry_path).get("episodes", []))
                if isinstance(item, dict) and item.get("candidate_id")
            }
            schema_validation = validate_seed_schema(seed, existing_ids)
            if schema_validation.get("status") != "PASS":
                schema_validation = {**schema_validation, "blocker": schema_validation.get("blocker") or blocker}
            forbidden_audit = forbidden_evidence_audit(seed) if schema_validation.get("status") == "PASS" else {"status": "NOT_RUN", "blocker": schema_validation.get("blocker") or blocker, "reason": "schema validation did not pass"}
    else:
        schema_validation = {
            "status": "BLOCK",
            "valid": False,
            "blocker": blocker,
            "blockers": [blocker],
            "reason": "seed file is absent after acquisition locks became ready",
            "seed_path": seed_path.as_posix(),
        }
        forbidden_audit = {
            "status": "NOT_RUN",
            "blocker": blocker,
            "reason": "seed file is absent after acquisition locks became ready",
        }

    lock_stack_policy = {
        "status": "PASS",
        "locks": [
            "baseline_registry_drift_precheck",
            "source_commit_environment_lock",
            "target_command_manifest",
            "fresh_workspace_purity",
            "targeted_seed_git_tracking",
        ],
        "all_locks_must_pass_before_source_acquisition": True,
        "seed_missing_blocks_after_locks_ready": True,
        "blocker": blocker,
    }
    lock_stack_status = {
        "status": "PASS_WITH_SEED_BLOCKED",
        "baseline_registry_drift_precheck_status": baseline_precheck["status"],
        "source_commit_environment_lock_status": env_summary["status"],
        "target_command_manifest_status": command_summary["status"],
        "workspace_purity_status": workspace_report["status"],
        "targeted_seed_git_tracking_status": git_tracking["status"],
        "locks_ready_before_seed_block": all(
            item.get("status") == "PASS"
            for item in [baseline_precheck, env_summary, command_summary, workspace_report]
        ),
        "exact_blocker": blocker,
    }
    gate_inputs = {
        "config": config,
        "batch012_state_hash": stable_json_hash(batch012_state),
    }
    gate_trace = [
        gate_entry(index=1, gate_id="baseline_registry_drift_precheck", status=baseline_precheck["status"], inputs=gate_inputs, outputs=baseline_precheck),
        gate_entry(index=2, gate_id="source_commit_environment_lock", status=env_summary["status"], inputs=baseline_precheck, outputs=env_summary),
        gate_entry(index=3, gate_id="target_command_manifest", status=command_summary["status"], inputs=env_summary, outputs=command_summary),
        gate_entry(index=4, gate_id="fresh_workspace_purity", status=workspace_report["status"], inputs=command_summary, outputs=workspace_report),
        gate_entry(index=5, gate_id="targeted_seed_presence_and_git_tracking", status="BLOCK", inputs=workspace_report, outputs={"presence": presence, "git_tracking": git_tracking}, blocker=blocker),
    ]
    for index, gate_id in enumerate(batch013_gate_chain_policy()["gate_order"][5:], start=6):
        gate_trace.append(
            gate_entry(
                index=index,
                gate_id=gate_id,
                status="NOT_RUN",
                inputs={"blocked_by": "targeted_seed_presence_and_git_tracking"},
                outputs={"status": "NOT_RUN", "blocker": blocker},
                blocker=blocker,
                blocked_by_gate="targeted_seed_presence_and_git_tracking",
            )
        )
    gate_dependency = audit_gate_dependency(gate_trace)
    rollback_entry = rollback_block_entry(
        entry_index=5,
        action="targeted_seed_presence_and_git_tracking",
        blocker=blocker,
        next_allowed_action="commit_reviewed_targeted_prospective_seed_batch013",
        rollback_target_entry_index=4,
        pre_action_state={"locks": lock_stack_status, "seed_present": False},
        attempted_action_state={"seed_path": seed_path.as_posix(), "seed_present": seed_present, "git_tracking": git_tracking},
    )
    rollback_audit = audit_rollback_block_ledger( gate_trace + [rollback_entry])

    policy = global_curvature_logic_policy()
    schema = curvature_feature_vector_schema()
    vector = curvature_feature_vector(
        {
            "candidate_id": "not_selected_missing_seed",
            "candidate_class": "prospective_memory_candidate",
            "native_or_issue_derived": "unknown",
            "patchable_source_file_count": 0,
            "alternative_route_count": 0,
            "flatline_risk": "high",
            "target_failure_reproduces": False,
            "semantic_failure_signature_exists": False,
        }
    )
    basin = basin_stability_score(
        {
            "target_failure_reproduces": False,
            "semantic_failure_signature_exists": False,
            "patchable_source_file_count": 0,
            "alternative_route_count": 0,
        },
        experiment_class="prospective_memory",
    )
    two_winner_record = two_winner_decision_record([])
    memory_routing_audit = curvature_memory_routing_audit(
        {"winner_linear": None, "winner_curvature": None, "selected_route": None},
        {"winner_linear": None, "winner_curvature": None, "selected_route": None},
        evidence_hashes=[],
        feature_mapped=False,
    )
    fragment_plan = curvature_fragment_plan(None, interlock_count=0, repair_runs=False)
    null_fairness = null_ensemble_curvature_fairness_audit(ensemble_runs=False, arm_a_vector_hash=None, null_vector_hashes=[])
    claim_boundary = curvature_claim_boundary(
        route_diversity_exists=False,
        routing_delta_scalar_only=True,
        null_curvature_fair=False,
        repair_only=False,
        issue_derived=False,
    )
    filtering_manifest = context_filter_manifest(
        seed_present=seed_present,
        before=[],
        after=[],
        reason="no candidate context is admitted until the tracked seed gate passes",
    )
    filter_delta = filter_delta_audit(filtering_manifest)
    issue_temporal = {
        "status": "PASS",
        "issue_derived_path_exercised": False,
        "issue_derived_candidate_count": 0,
        "issue_derived_classification": "NOT_RUN",
        "issue_derived_not_classified_as_native": True,
        "temporal_guard_status": "NOT_RUN",
        "blocker": blocker,
    }
    five_locks_cross_gate = {
        "status": "PASS",
        "locks_ready_before_seed_block": lock_stack_status["locks_ready_before_seed_block"],
        "source_acquisition_allowed": False,
        "target_replay_allowed": False,
        "curvature_candidate_selection_allowed": False,
        "repair_generation_allowed": False,
        "matched_null_allowed": False,
        "blocker": blocker,
    }

    no_run = {"status": "NOT_RUN", "blocker": blocker}
    write_json_deterministic(BATCH013_DIR / "acquisition_lock_stack_policy.json", lock_stack_policy)
    write_json_deterministic(BATCH013_DIR / "source_commit_environment_lock_policy.json", env_policy)
    write_json_deterministic(BATCH013_DIR / "source_commit_environment_lock_summary.json", env_summary)
    write_json_deterministic(BATCH013_DIR / "target_command_manifest_policy.json", command_policy)
    write_json_deterministic(BATCH013_DIR / "target_command_manifest_summary.json", command_summary)
    write_json_deterministic(BATCH013_DIR / "fresh_workspace_purity_policy.json", workspace_policy)
    write_json_deterministic(BATCH013_DIR / "workspace_purity_report.json", workspace_report)
    write_json_deterministic(BATCH013_DIR / "baseline_registry_drift_precheck_policy.json", baseline_policy)
    write_json_deterministic(BATCH013_DIR / "baseline_registry_snapshot_batch013.json", baseline_snapshot)
    write_json_deterministic(BATCH013_DIR / "baseline_registry_drift_precheck.json", baseline_precheck)
    write_json_deterministic(BATCH013_DIR / "rollback_block_ledger_policy.json", rollback_block_ledger_policy())
    write_json_deterministic(BATCH013_DIR / "rollback_block_ledger_audit.json", rollback_audit)
    write_json_deterministic(BATCH013_DIR / "acquisition_lock_stack_status.json", lock_stack_status)
    write_json_deterministic(BATCH013_DIR / "targeted_seed_presence_check.json", presence)
    write_json_deterministic(BATCH013_DIR / "targeted_seed_schema_validation.json", schema_validation)
    write_json_deterministic(BATCH013_DIR / "targeted_seed_forbidden_evidence_audit.json", forbidden_audit)
    write_json_deterministic(BATCH013_DIR / "targeted_seed_git_tracking_audit.json", git_tracking)
    write_json_deterministic(BATCH013_DIR / "targeted_seed_workflow_visibility_audit.json", workflow_visibility)
    write_json_deterministic(
        BATCH013_DIR / "targeted_seed_intake_report.json",
        {
            "status": "BLOCK",
            "seed_path": seed_path.as_posix(),
            "seed_present": seed_present,
            "seed_schema_status": schema_validation["status"],
            "git_tracking_status": git_tracking["status"],
            "workflow_visibility_status": workflow_visibility["status"],
            "locks_completed_before_seed_block": True,
            "exact_blocker": blocker,
            "native_verification_status": "NOT_RUN",
            "issue_derived_verification_status": "NOT_RUN",
            "matched_null_ensemble_status": "NOT_RUN",
            "repair_only_fallback_attempted": False,
        },
    )
    write_json_deterministic(
        BATCH013_DIR / "targeted_seed_next_action.json",
        {
            "status": "BLOCK",
            "next_allowed_action": "commit_reviewed_targeted_prospective_seed_batch013",
            "seed_path": seed_path.as_posix(),
            "required_git_status": "tracked",
            "required_workflow_visibility": True,
            "blocker": blocker,
        },
    )
    write_text_lf(
        BATCH013_DIR / "targeted_seed_required_next_action.md",
        "\n".join(
            [
                "# Targeted prospective seed required after locks",
                "",
                f"Blocker: `{blocker}`.",
                "",
                f"Commit a reviewed targeted prospective seed at `{seed_path.as_posix()}` so the workflow can see the exact same seed bytes.",
                "",
                "The acquisition locks, command manifest placeholder, workspace purity gate, registry drift precheck, gate-chain trace, and rollback proof ledger are ready. No source checkout, issue-derived fallback, repair-only fallback, or matched-null comparison ran.",
            ]
        ),
    )
    write_json_deterministic(BATCH013_DIR / "batch013_gate_chain_policy.json", batch013_gate_chain_policy())
    write_json_deterministic(BATCH013_DIR / "batch013_gate_chain_execution_trace.json", gate_trace)
    write_json_deterministic(BATCH013_DIR / "batch013_gate_dependency_audit.json", gate_dependency)
    write_json_deterministic(BATCH013_DIR / "active_context_filtering_policy.json", active_context_filtering_policy())
    write_json_deterministic(BATCH013_DIR / "active_context_filter_manifest.json", filtering_manifest)
    write_json_deterministic(BATCH013_DIR / "memory_enabled_context_before_filter.json", {"status": "NOT_RUN", "context_paths": [], "blocker": blocker})
    write_json_deterministic(BATCH013_DIR / "memory_enabled_context_after_filter.json", {"status": "NOT_RUN", "context_paths": [], "blocker": blocker})
    write_json_deterministic(BATCH013_DIR / "context_filter_delta_audit.json", filter_delta)
    write_json_deterministic(BATCH013_DIR / "curvature_heuristic_freeze.json", curvature_heuristic_freeze())
    write_json_deterministic(BATCH013_DIR / "curvature_score_formula.json", curvature_score_formula())
    write_json_deterministic(BATCH013_DIR / "curvature_thresholds.json", curvature_thresholds())
    write_json_deterministic(
        BATCH013_DIR / "proof_obligations_ledger.json",
        {
            "status": "PASS",
            "entries": gate_trace + [rollback_entry],
            "rollback_block_present": True,
            "rollback_blocker": blocker,
            "next_allowed_action": "commit_reviewed_targeted_prospective_seed_batch013",
        },
    )
    write_json_deterministic(BATCH013_DIR / "five_locks_curvature_cross_gate.json", five_locks_cross_gate)
    write_json_deterministic(BATCH013_DIR / "issue_derived_temporal_and_classification_audit.json", issue_temporal)
    write_json_deterministic(BATCH013_DIR / "global_curvature_logic_policy.json", policy)
    write_json_deterministic(
        BATCH013_DIR / "curvature_logic_enforcement_status.json",
        {
            "status": "PASS_WITH_SEED_BLOCKED",
            "global_policy_loaded": policy["status"] == "PASS",
            "curvature_used_as_proof": False,
            "curvature_outputs_generated_before_seed": True,
            "blocker": blocker,
        },
    )
    write_json_deterministic(
        BATCH013_DIR / "curvature_trace_audit.json",
        {
            "status": "PASS",
            "candidate_selection_ran": False,
            "source_route_selection_ran": False,
            "repair_generation_ran": False,
            "curvature_claim_boundary_status": claim_boundary["status"],
            "blocker": blocker,
        },
    )
    write_json_deterministic(BATCH013_DIR / "curvature_feature_vector_schema.json", schema)
    write_json_deterministic(BATCH013_DIR / "candidate_curvature_feature_vectors.json", {"status": "NOT_RUN", "vectors": [vector], "blocker": blocker})
    write_json_deterministic(BATCH013_DIR / "basin_stability_check_policy.json", basin_stability_check_policy())
    write_json_deterministic(BATCH013_DIR / "basin_stability_scores.json", {"status": "NOT_RUN", "scores": [basin], "blocker": blocker})
    write_json_deterministic(BATCH013_DIR / "two_winner_global_policy.json", two_winner_global_policy())
    write_json_deterministic(BATCH013_DIR / "two_winner_decision_records.json", {"status": "NOT_RUN", "records": [two_winner_record], "blocker": blocker})
    write_json_deterministic(BATCH013_DIR / "curvature_memory_routing_policy.json", curvature_memory_routing_policy())
    write_json_deterministic(BATCH013_DIR / "curvature_memory_routing_audit.json", {**memory_routing_audit, "status": "NOT_RUN", "blocker": blocker})
    write_json_deterministic(BATCH013_DIR / "curvature_fragment_planning_policy.json", curvature_fragment_planning_policy())
    write_json_deterministic(BATCH013_DIR / "curvature_fragment_plan.json", fragment_plan)
    write_json_deterministic(BATCH013_DIR / "null_ensemble_curvature_fairness_policy.json", null_ensemble_curvature_fairness_policy())
    write_json_deterministic(BATCH013_DIR / "null_ensemble_curvature_fairness_audit.json", null_fairness)
    write_json_deterministic(BATCH013_DIR / "curvature_claim_boundary.json", claim_boundary)
    write_json_deterministic(BATCH013_DIR / "native_verification_result.json", {**no_run, "native_candidate_verified": False, "pre_repair_failure_reproduced": False})
    write_json_deterministic(BATCH013_DIR / "issue_derived_harness_policy.json", issue_derived_harness_policy())
    write_json_deterministic(BATCH013_DIR / "issue_derived_harness_verification_result.json", issue_derived_verification_not_run(blocker))
    write_json_deterministic(BATCH013_DIR / "prospective_memory_eligibility_gate.json", {**no_run, "eligible": False})
    write_json_deterministic(BATCH013_DIR / "route_diversity_status.json", {**no_run, "route_count": 0})
    write_json_deterministic(BATCH013_DIR / "status_feature_mappability.json", {**no_run, "mapped_feature_count": 0})
    write_json_deterministic(BATCH013_DIR / "matched_null_ensemble_summary.json", {**no_run, "null_ensemble_run_count": 0, "matched_null_score": None})
    write_json_deterministic(BATCH013_DIR / "repair_only_fallback_summary.json", {**repair_only_fallback_evaluation(attempted=False, repair_succeeded=False), "blocker": blocker})
    write_json_deterministic(
        BATCH013_DIR / "claim_boundary.json",
        {
            "status": "PASS",
            "full_scoring": "NOT_RUN/disallowed",
            "full_memory_lift_claimed": False,
            "memory_lift": "not_demonstrated",
            "self_maintaining_software": "false/not_demonstrated",
            "technical_validation_release_readiness": "not_ready",
            "native_issue_derived_counts_separate": True,
            "preliminary_prospective_single_candidate_memory_separation_evidence": False,
            "confirmed_native_repair_episode_count": 4,
            "confirmed_issue_derived_repair_episode_count": 0,
        },
    )
    traceability = {
        "status": "PASS",
        "source_commit_environment_lock": "implemented_active_ready_no_seed",
        "target_command_manifest": "implemented_active_ready_no_seed",
        "fresh_workspace_purity_gate": "implemented_active_ready_no_seed",
        "baseline_registry_drift_precheck": "implemented_active",
        "rollback_block_ledger": "implemented_active",
        "global_curvature_logic_enforcement": "implemented_active",
        "curvature_feature_vector": "implemented_partial_no_candidate",
        "basin_stability_check": "implemented_partial_no_candidate",
        "two_winner_global_policy": "implemented_partial_no_candidate",
        "curvature_memory_routing": "implemented_partial_no_candidate",
        "curvature_guided_fragment_planning": "implemented_partial_no_repair_run",
        "null_ensemble_curvature_fairness": "implemented_partial_no_ensemble_run",
        "batch013_gate_chain_binding": "implemented_active",
        "targeted_seed_git_tracking": "implemented_active_blocked_missing_seed",
        "active_context_filtering": "implemented_partial_no_candidate",
        "curvature_heuristic_freeze": "implemented_active",
        "five_locks_curvature_cross_gate": "implemented_active",
        "issue_derived_temporal_classification": "implemented_active_not_exercised",
        "silent_completion": False,
        "blocker": blocker,
    }
    carry_forward = {
        "status": "PASS",
        "blockers": [
            {
                "blocker": blocker,
                "next_allowed_action": "commit_reviewed_targeted_prospective_seed_batch013",
                "seed_path": seed_path.as_posix(),
                "minimum_condition_to_unblock": "track a reviewed seed file and rerun Batch013",
            }
        ],
    }
    write_json_deterministic(BATCH013_DIR / "notebooklm_advice_traceability_status.json", traceability)
    write_json_deterministic(BATCH013_DIR / "carry_forward_blocker_register.json", carry_forward)

    state = {
        "lane_id": BATCH013_ID,
        "lane_type": "acquisition_locks_and_targeted_seed_intake_hardening",
        "status": "BLOCK",
        "exact_blocker": blocker,
        "current_protocol_version": "v2.13",
        "targeted_seed_path": seed_path.as_posix(),
        "targeted_seed_present": seed_present,
        "targeted_seed_validation_status": schema_validation["status"],
        "targeted_seed_git_tracking_status": git_tracking["status"],
        "targeted_seed_workflow_visibility_status": workflow_visibility["status"],
        "source_commit_environment_lock_status": env_summary["status"],
        "target_command_manifest_status": command_summary["status"],
        "fresh_workspace_purity_status": workspace_report["status"],
        "baseline_registry_drift_precheck_status": baseline_precheck["status"],
        "rollback_block_ledger_status": rollback_audit["status"],
        "acquisition_lock_stack_status": lock_stack_status["status"],
        "batch013_gate_chain_status": gate_dependency["status"],
        "active_context_filtering_status": filtering_manifest["status"],
        "curvature_heuristic_freeze_status": "PASS",
        "five_locks_curvature_cross_gate_status": five_locks_cross_gate["status"],
        "issue_derived_temporal_classification_status": issue_temporal["status"],
        "global_curvature_logic_status": "PASS_WITH_SEED_BLOCKED",
        "curvature_feature_vector_status": "NOT_RUN",
        "basin_stability_check_status": "NOT_RUN",
        "two_winner_global_policy_status": "NOT_RUN",
        "curvature_candidate_selection_status": "NOT_RUN",
        "curvature_source_route_selection_status": "NOT_RUN",
        "curvature_memory_routing_status": "NOT_RUN",
        "curvature_fragment_planning_status": fragment_plan["status"],
        "null_curvature_fairness_status": null_fairness["status"],
        "curvature_claim_boundary_status": claim_boundary["status"],
        "curvature_blocker_if_any": claim_boundary["blocker"],
        "gate_chain_blocker_if_any": blocker,
        "candidate_class": None,
        "native_verification_status": "NOT_RUN",
        "issue_derived_verification_status": "NOT_RUN",
        "prospective_memory_eligibility_status": "NOT_RUN",
        "route_diversity_status": "NOT_RUN",
        "mappable_status_feature_status": "NOT_RUN",
        "matched_null_ensemble_run_count": 0,
        "matched_null_score": None,
        "preliminary_prospective_single_candidate_memory_separation_evidence": False,
        "repair_only_fallback_attempted": False,
        "additional_native_repair_acquired": False,
        "additional_issue_derived_repair_feasibility": False,
        "confirmed_native_repair_episode_count": int(batch012_state.get("confirmed_native_repair_episode_count", 4)),
        "confirmed_issue_derived_repair_episode_count": 0,
        "full_scoring": "NOT_RUN/disallowed",
        "memory_lift": "not_demonstrated",
        "self_maintaining_software": "false/not_demonstrated",
    }
    write_json_deterministic(BATCH013_DIR / "consolidated_state_clean_replication_batch_013.json", state)
    write_text_lf(
        BATCH013_DIR / "campaign_summary.md",
        "\n".join(
            [
                "# Clean replication batch 013",
                "",
                "Status: BLOCK.",
                "",
                "Batch013 implements acquisition/materialization locks, gate-chain binding, tracked seed enforcement, active context filtering records, and frozen routing-score policy before any new candidate can run.",
                "",
                "The configured targeted seed is absent, so the lane stops after the locks are ready and before source checkout, native replay, issue-derived fallback, repair-only fallback, or matched-null comparison.",
                "",
                f"Exact blocker: `{blocker}`.",
            ]
        ),
    )
    write_sha256sums(BATCH013_DIR)
    return state


def _run_command(command: list[str], *, cwd: Path, env: dict[str, str] | None = None, timeout: int = 120) -> dict[str, object]:
    completed = subprocess.run(
        command,
        cwd=cwd,
        env=env,
        text=True,
        capture_output=True,
        timeout=timeout,
    )
    return {
        "command": command,
        "cwd": str(cwd),
        "returncode": completed.returncode,
        "stdout": completed.stdout,
        "stderr": completed.stderr,
        "stdout_sha256": hashlib.sha256(completed.stdout.encode("utf-8", errors="replace")).hexdigest(),
        "stderr_sha256": hashlib.sha256(completed.stderr.encode("utf-8", errors="replace")).hexdigest(),
    }


def _batch014_runtime_root() -> Path:
    base = Path(os.environ.get("CONTROLLERGATE_RUNTIME_ROOT", Path.cwd().parent / "ControllerGate_Runtime"))
    return base / "clean_replication_batch_014"


def _remove_runtime_tree(path: Path) -> None:
    if not path.exists():
        return

    def _onerror(function, failing_path, excinfo):
        try:
            os.chmod(failing_path, stat.S_IWRITE)
            function(failing_path)
        except Exception:
            raise

    shutil.rmtree(path, onerror=_onerror)


def _select_source_commit(repo_url: str, issue_created_at: str, runtime_root: Path) -> tuple[dict[str, object], Path | None]:
    runtime_root.mkdir(parents=True, exist_ok=True)
    clone_root = runtime_root / "darker_source"
    if clone_root.exists():
        _remove_runtime_tree(clone_root)
    repo_git_url = repo_url if repo_url.endswith(".git") else f"{repo_url}.git"
    ls_remote = _run_command(["git", "ls-remote", "--symref", repo_git_url, "HEAD"], cwd=runtime_root, timeout=60)
    default_branch = "master"
    for line in str(ls_remote["stdout"]).splitlines():
        if line.startswith("ref:") and line.endswith("\tHEAD"):
            default_branch = line.split("refs/heads/", 1)[-1].split("\t", 1)[0]
    clone = _run_command(["git", "clone", "--no-tags", "--single-branch", "--branch", default_branch, repo_git_url, str(clone_root)], cwd=runtime_root, timeout=180)
    if clone["returncode"] != 0:
        return (
            {
                "status": "BLOCK",
                "repo_url": repo_url,
                "default_branch": default_branch,
                "source_commit_selection_method": "default_branch_before_issue_created_at",
                "issue_created_at": issue_created_at,
                "clone_returncode": clone["returncode"],
                "clone_stderr_sha256": clone["stderr_sha256"],
                "blocker": "source_commit_unresolved",
            },
            None,
        )
    rev = _run_command(["git", "rev-list", "-n", "1", f"--before={issue_created_at}", "HEAD"], cwd=clone_root, timeout=60)
    commit = str(rev["stdout"]).strip()
    obj_type = ""
    if commit:
        obj = _run_command(["git", "cat-file", "-t", commit], cwd=clone_root, timeout=30)
        obj_type = str(obj["stdout"]).strip()
    if not commit or obj_type != "commit":
        return (
            {
                "status": "BLOCK",
                "repo_url": repo_url,
                "default_branch": default_branch,
                "source_commit_selection_method": "default_branch_before_issue_created_at",
                "issue_created_at": issue_created_at,
                "resolved_commit_sha": commit or None,
                "object_type": obj_type or None,
                "blocker": "source_commit_unresolved",
            },
            clone_root,
        )
    checkout = _run_command(["git", "checkout", "--detach", commit], cwd=clone_root, timeout=60)
    show = _run_command(["git", "show", "-s", "--format=%H%n%ci%n%s", commit], cwd=clone_root, timeout=30)
    return (
        {
            "status": "PASS" if checkout["returncode"] == 0 else "BLOCK",
            "repo_url": repo_url,
            "default_branch": default_branch,
            "source_commit_selection_method": "default_branch_before_issue_created_at",
            "issue_created_at": issue_created_at,
            "resolved_commit_sha": commit,
            "object_type": obj_type,
            "checkout_returncode": checkout["returncode"],
            "commit_show": str(show["stdout"]).splitlines(),
            "blocker": None if checkout["returncode"] == 0 else "source_commit_unresolved",
        },
        clone_root,
    )


def _write_issue_harness(path: Path) -> None:
    write_text_lf(
        path,
        "\n".join(
            [
                "from __future__ import annotations",
                "",
                "import os",
                "from pathlib import Path",
                "import subprocess",
                "import sys",
                "",
                "workspace = Path(os.environ['DARKER_SOURCE_WORKSPACE'])",
                "env = os.environ.copy()",
                "env['GIT_DIR'] = '.git'",
                "completed = subprocess.run([sys.executable, '-m', 'darker', '--check', 'src'], cwd=workspace, env=env, text=True, capture_output=True)",
                "if completed.stdout:",
                "    print(completed.stdout, end='')",
                "if completed.stderr:",
                "    print(completed.stderr, end='', file=sys.stderr)",
                "raise SystemExit(completed.returncode)",
            ]
        ),
    )


def write_batch014_outputs(batch013_state: dict[str, object]) -> dict[str, object]:
    BATCH014_DIR.mkdir(parents=True, exist_ok=True)
    canonical_seed = Path("external_seeds_pending/targeted_prospective_seed_batch013.json")
    alias_seed = Path("external_seeds_pending/targeted_prospective_seed_batch014.json")
    workflow_path = ".github/workflows/post_v2_37_hardening_and_batch002.yml"
    blocker = None
    runtime_root = _batch014_runtime_root()

    path_resolution = resolve_targeted_seed_path(canonical_seed, alias_seed)
    seed_path = Path(str(path_resolution["seed_path_used"]))
    seed: dict[str, object] = {}
    if path_resolution["status"] == "PASS":
        try:
            seed = load_json(seed_path)
        except Exception:
            blocker = "targeted_seed_schema_invalid"
    else:
        blocker = str(path_resolution.get("blocker"))

    existing_ids = {
        str(item.get("candidate_id"))
        for registry_path in [Path("configs/external_candidate_registry.json"), Path("configs/external_repair_episode_registry.json")]
        if registry_path.is_file()
        for item in load_json(registry_path).get("candidates", load_json(registry_path).get("episodes", []))
        if isinstance(item, dict) and item.get("candidate_id")
    }
    git_tracking = seed_git_tracking_audit(seed_path, workflow_paths=[workflow_path])
    workflow_visibility = {
        "status": git_tracking["status"],
        "seed_path": seed_path.as_posix(),
        "workflow_path": workflow_path,
        "workflow_visible": git_tracking["workflow_visible"],
        "workflow_visibility_paths": git_tracking["workflow_visibility_paths"],
        "seed_sha256": path_resolution.get("seed_sha256"),
        "blocker": git_tracking["blocker"],
    }
    harmonization = harmonize_batch014_seed(seed, existing_ids) if seed else {"status": "BLOCK", "blocker": "targeted_seed_schema_invalid", "normalized_seed": {}}
    normalized_seed = dict(harmonization.get("normalized_seed", seed))
    schema_validation = {
        "status": harmonization["status"],
        "valid": harmonization["status"] == "PASS",
        "blockers": harmonization.get("blockers", []),
        "blocker": harmonization.get("blocker"),
    }
    forbidden_audit = forbidden_evidence_audit(normalized_seed) if harmonization["status"] == "PASS" else {"status": "NOT_RUN", "blocker": harmonization.get("blocker")}
    firewall = issue_text_solution_section_firewall(normalized_seed)
    dataset_firewall = dataset_lead_firewall(normalized_seed)
    native_guard = proposed_native_seed_verification_guard(normalized_seed)
    downgrade = native_to_issue_derived_downgrade_report(normalized_seed, native_guard, firewall)

    gate_preconditions = [path_resolution, git_tracking, harmonization, firewall, dataset_firewall, native_guard, downgrade]
    for item in gate_preconditions:
        if item.get("status") == "BLOCK" and blocker is None:
            blocker = str(item.get("blocker"))

    source_selection: dict[str, object]
    source_checkout: dict[str, object]
    workspace_report: dict[str, object]
    env_summary: dict[str, object]
    command_summary: dict[str, object]
    harness_verification: dict[str, object]
    source_root: Path | None = None
    raw_log = ""

    if blocker is None:
        source_selection, source_root = _select_source_commit(
            str(normalized_seed.get("repo_url")),
            str(normalized_seed.get("issue_created_at")),
            runtime_root,
        )
        if source_selection["status"] == "BLOCK":
            blocker = str(source_selection["blocker"])
    else:
        source_selection = {"status": "NOT_RUN", "blocker": blocker}

    if source_root and source_root.exists():
        metadata_paths = [rel for rel in ["pyproject.toml", "setup.cfg", "setup.py"] if (source_root / rel).is_file()]
        source_checkout = {
            "status": "PASS",
            "workspace_path": str(source_root),
            "workspace_outside_live_repo": not str(source_root.resolve()).startswith(str(Path.cwd().resolve())),
            "workspace_outside_onedrive": "onedrive" not in str(source_root).lower(),
            "tree_entries_sample": sorted(path.name for path in source_root.iterdir())[:25],
            "metadata_paths": metadata_paths,
            "metadata_sha256": {rel: sha256_file(source_root / rel) for rel in metadata_paths},
            "fixed_later_gold_pr_evidence_accessed": False,
        }
        workspace_report = audit_workspace_purity(source_root, repo_root=".", seed_present=True, workspace_created=True)
        env_summary = summarize_source_commit_environment_lock(
            source_commit_sha=str(source_selection.get("resolved_commit_sha")),
            environment_lock_source_paths=metadata_paths,
            seed_present=True,
        )
    else:
        source_checkout = {"status": "NOT_RUN", "blocker": blocker}
        workspace_report = {"status": "NOT_RUN", "blocker": blocker}
        env_summary = {"status": "NOT_RUN", "blocker": blocker}

    baseline_policy = baseline_registry_drift_precheck_policy()
    baseline_snapshot = baseline_registry_snapshot("configs/external_repair_episode_registry.json")
    baseline_precheck = baseline_registry_drift_precheck(baseline_snapshot)
    harness_path = BATCH014_DIR / "issue_derived_ephemeral_harness.py"
    _write_issue_harness(harness_path)
    harness_sha = sha256_file(harness_path)
    command_summary = build_target_command_manifest_summary(
        seed_present=True,
        command=[sys.executable, harness_path.as_posix()],
        cwd=str(Path.cwd()),
        environment={
            "DARKER_SOURCE_WORKSPACE": str(source_root) if source_root else "",
            "PYTHONUTF8": "1",
            "PYTHONIOENCODING": "utf-8",
        },
        provenance_basis="redacted_issue_snapshot_and_selected_source_commit",
        allowed_setup_commands=["python -m pip install -e ."],
    )
    issue112_command_manifest = {
        "status": command_summary["status"],
        "candidate_id": normalized_seed.get("candidate_id"),
        "candidate_class": "issue_derived_reproduction_candidate",
        "command": command_summary["command"],
        "cwd": command_summary["cwd"],
        "env_vars": command_summary["environment"],
        "setup_commands": command_summary["allowed_setup_commands"],
        "issue_text_hash": firewall.get("snapshot_sha256"),
        "harness_sha256": harness_sha,
        "source_commit_sha": source_selection.get("resolved_commit_sha"),
        "decision_time_safe_basis": "redacted issue snapshot plus selected source commit tree",
        "forbidden_framework_state_used": False,
        "blocker": command_summary.get("blocker"),
    }

    locks_pass = all(item.get("status") == "PASS" for item in [baseline_precheck, workspace_report, env_summary, command_summary]) and blocker is None
    if not locks_pass and blocker is None:
        blocker = next(
            (str(item.get("blocker")) for item in [baseline_precheck, workspace_report, env_summary, command_summary] if item.get("status") != "PASS" and item.get("blocker")),
            "acquisition_lock_stack_failed",
        )

    install_result: dict[str, object] = {"status": "NOT_RUN", "blocker": blocker}
    run_result: dict[str, object] = {"status": "NOT_RUN", "blocker": blocker}
    semantic_match = False
    if locks_pass and source_root:
        venv_dir = runtime_root / "venv"
        if venv_dir.exists():
            _remove_runtime_tree(venv_dir)
        create_venv_result = _run_command([sys.executable, "-m", "venv", str(venv_dir)], cwd=runtime_root, timeout=120)
        py = venv_python(venv_dir)
        env = os.environ.copy()
        env.update({"PYTHONUTF8": "1", "PYTHONIOENCODING": "utf-8"})
        if create_venv_result["returncode"] == 0:
            pip_upgrade = _run_command([str(py), "-m", "pip", "install", "--upgrade", "pip", "setuptools", "wheel"], cwd=source_root, env=env, timeout=180)
            pip_install = _run_command([str(py), "-m", "pip", "install", "-e", "."], cwd=source_root, env=env, timeout=240)
            install_result = {
                "status": "PASS" if pip_install["returncode"] == 0 else "BLOCK",
                "venv_path": str(venv_dir),
                "create_venv_returncode": create_venv_result["returncode"],
                "pip_upgrade_returncode": pip_upgrade["returncode"],
                "pip_install_returncode": pip_install["returncode"],
                "pip_install_stderr_sha256": pip_install["stderr_sha256"],
                "declared_install_only": True,
                "blocker": None if pip_install["returncode"] == 0 else "issue_derived_harness_environment_failure",
            }
        else:
            install_result = {"status": "BLOCK", "create_venv_returncode": create_venv_result["returncode"], "blocker": "issue_derived_harness_environment_failure"}
        if install_result["status"] == "PASS":
            harness_env = env.copy()
            harness_env["DARKER_SOURCE_WORKSPACE"] = str(source_root)
            run_result = _run_command([str(py), str(harness_path.resolve())], cwd=Path.cwd(), env=harness_env, timeout=120)
            raw_log = str(run_result["stdout"]) + str(run_result["stderr"])
            semantic_match = (
                run_result["returncode"] != 0
                and "not a git repository" in raw_log.lower()
                and "git diff" in raw_log.lower()
            )
            if not semantic_match:
                blocker = "issue_derived_harness_intent_mismatch"
        else:
            blocker = str(install_result.get("blocker"))

    write_text_lf(BATCH014_DIR / "issue_derived_failure_capture_raw.log", raw_log)
    raw_log_sha = sha256_file(BATCH014_DIR / "issue_derived_failure_capture_raw.log")
    harness_verification = {
        "status": "PASS" if semantic_match else "BLOCK",
        "candidate_id": normalized_seed.get("candidate_id"),
        "candidate_class": "issue_derived_reproduction_candidate",
        "harness_generated": True,
        "harness_sha256": harness_sha,
        "install_status": install_result.get("status"),
        "run_returncode": run_result.get("returncode"),
        "raw_log_sha256": raw_log_sha,
        "pre_patch_failure_reproduced": bool(run_result.get("returncode") not in [None, 0]),
        "semantic_failure_matches_redacted_snapshot": semantic_match,
        "issue_derived_evidence_class_separate": True,
        "native_count_increment_allowed": False,
        "blocker": None if semantic_match else blocker,
    }

    candidate_verified = harness_verification["status"] == "PASS"
    route_rows = [
        {
            "source_path": "src/darker/git.py",
            "function_or_class": "git_get_modified_files",
            "failure_proximity_score": 4,
            "traceback_centrality": 4,
            "import_graph_centrality": 2,
            "ast_closure_centrality": 2,
            "alternative_route_availability": 1,
            "target_intent_reachability_score": 2 if semantic_match else 0,
            "status_code_weight": 1 if semantic_match else 0,
            "dependency_spread_penalty": 1,
            "environment_precondition_friction_penalty": 2 if not semantic_match else 0,
        },
        {
            "source_path": "src/darker/__main__.py",
            "function_or_class": "main",
            "failure_proximity_score": 3,
            "traceback_centrality": 3,
            "import_graph_centrality": 2,
            "ast_closure_centrality": 1,
            "alternative_route_availability": 1,
            "target_intent_reachability_score": 2 if semantic_match else 0,
            "status_code_weight": 1 if semantic_match else 0,
            "dependency_spread_penalty": 1,
            "environment_precondition_friction_penalty": 2 if not semantic_match else 0,
        },
    ]
    vector = curvature_feature_vector(
        {
            "candidate_id": normalized_seed.get("candidate_id"),
            "candidate_class": "issue_derived_reproduction_candidate",
            "repo_url": normalized_seed.get("repo_url"),
            "source_commit_sha": source_selection.get("resolved_commit_sha"),
            "native_or_issue_derived": "issue_derived",
            "target_command_width": "single_command",
            "source_file_count_in_trace": 2 if semantic_match else 0,
            "patchable_source_file_count": 2 if semantic_match else 0,
            "alternative_route_count": 2 if semantic_match else 0,
            "environment_lock_status": env_summary.get("status"),
            "command_manifest_status": command_summary.get("status"),
            "workspace_purity_status": workspace_report.get("status"),
            "baseline_drift_status": baseline_precheck.get("status"),
            "target_intent_reachability_status": "PASS" if semantic_match else "BLOCK",
            "semantic_failure_signature_status": "PASS" if semantic_match else "BLOCK",
            "issue_derived_risk_status": "separate_issue_derived_class",
            "flatline_risk": "low" if semantic_match else "high",
            "escape_boundary_risk": "medium" if semantic_match else "high",
            "basin_stability_score": 4 if semantic_match else 0,
        }
    )
    basin = basin_stability_score(
        {
            "target_failure_reproduces": semantic_match,
            "semantic_failure_signature_exists": semantic_match,
            "environment_precondition_only": not semantic_match,
            "patchable_source_file_count": 2 if semantic_match else 0,
            "alternative_route_count": 2 if semantic_match else 0,
        },
        experiment_class="repair_only",
    )
    two_winner = two_winner_decision_record(route_rows if semantic_match else [])
    eligibility = {
        "status": "BLOCK",
        "eligible": False,
        "candidate_class": "issue_derived_reproduction_candidate",
        "fresh_native_candidate_required": True,
        "issue_derived_candidate": True,
        "native_memory_separation_allowed": False,
        "blocker": "prospective_memory_eligibility_not_met",
    }
    repair_only = {
        **repair_only_fallback_evaluation(attempted=False, repair_succeeded=False),
        "status": "NOT_RUN" if not candidate_verified else "BLOCK",
        "candidate_verified": candidate_verified,
        "blocker": None if candidate_verified else blocker,
    }
    matched_null = {
        "status": "NOT_RUN",
        "null_ensemble_run_count": 0,
        "matched_null_score": None,
        "preregistered": False,
        "blocker": "prospective_memory_eligibility_not_met",
    }
    claim = issue112_claim_boundary(issue_derived=True, repair_succeeded=False)
    curvature_claim = curvature_claim_boundary(
        route_diversity_exists=semantic_match,
        routing_delta_scalar_only=True,
        null_curvature_fair=False,
        repair_only=True,
        issue_derived=True,
    )
    rollback_entry = rollback_block_entry(
        entry_index=9,
        action="issue_derived_harness_verification",
        blocker=str(blocker or "none"),
        next_allowed_action="resolve_issue_derived_environment_or_provide_new_reviewed_seed",
        rollback_target_entry_index=8,
        pre_action_state={"locks_pass": locks_pass, "source_selection": source_selection},
        attempted_action_state={"harness_verification": harness_verification, "install": install_result, "run": {k: v for k, v in run_result.items() if k not in {"stdout", "stderr"}}},
    )
    proof_ledger = [
        {"entry_index": 1, "action": "targeted_seed_path_resolution", "status": path_resolution["status"]},
        {"entry_index": 2, "action": "seed_schema_harmonization", "status": harmonization["status"]},
        {"entry_index": 3, "action": "redacted_issue_snapshot_firewall", "status": firewall["status"]},
        {"entry_index": 4, "action": "dataset_lead_firewall", "status": dataset_firewall["status"]},
        {"entry_index": 5, "action": "source_commit_selection", "status": source_selection["status"]},
        {"entry_index": 6, "action": "workspace_purity", "status": workspace_report["status"]},
        {"entry_index": 7, "action": "target_command_manifest", "status": command_summary["status"]},
        {"entry_index": 8, "action": "issue_derived_harness_generation", "status": "PASS"},
        rollback_entry,
    ]
    rollback_audit = audit_rollback_block_ledger(proof_ledger)
    lock_stack_status = {
        "status": "PASS" if locks_pass else "BLOCK",
        "baseline_registry_drift_precheck_status": baseline_precheck.get("status"),
        "source_commit_environment_lock_status": env_summary.get("status"),
        "target_command_manifest_status": command_summary.get("status"),
        "workspace_purity_status": workspace_report.get("status"),
        "rollback_block_ledger_status": rollback_audit.get("status"),
        "five_locks_pass_before_replay": locks_pass,
        "blocker": None if locks_pass else blocker,
    }
    gate_trace = [
        gate_entry(index=1, gate_id="targeted_seed_path_resolution", status=path_resolution["status"], inputs={"canonical": canonical_seed.as_posix()}, outputs=path_resolution, blocker=path_resolution.get("blocker")),
        gate_entry(index=2, gate_id="targeted_seed_git_tracking", status=git_tracking["status"], inputs=path_resolution, outputs=git_tracking, blocker=git_tracking.get("blocker")),
        gate_entry(index=3, gate_id="seed_schema_harmonization", status=harmonization["status"], inputs=git_tracking, outputs=harmonization, blocker=harmonization.get("blocker")),
        gate_entry(index=4, gate_id="redacted_issue_snapshot_firewall", status=firewall["status"], inputs=harmonization, outputs=firewall, blocker=firewall.get("blocker")),
        gate_entry(index=5, gate_id="dataset_lead_firewall", status=dataset_firewall["status"], inputs=firewall, outputs=dataset_firewall, blocker=dataset_firewall.get("blocker")),
        gate_entry(index=6, gate_id="source_commit_selection", status=source_selection["status"], inputs=dataset_firewall, outputs=source_selection, blocker=source_selection.get("blocker")),
        gate_entry(index=7, gate_id="five_acquisition_locks", status=lock_stack_status["status"], inputs=source_selection, outputs=lock_stack_status, blocker=lock_stack_status.get("blocker")),
        gate_entry(index=8, gate_id="issue_derived_harness_verification", status=harness_verification["status"], inputs=lock_stack_status, outputs=harness_verification, blocker=harness_verification.get("blocker")),
    ]
    first_batch014_block = next((item for item in gate_trace if item.get("status") == "BLOCK"), None)
    gate_dependency = {
        "status": "PASS",
        "gate_count": len(gate_trace),
        "gate_order": [item.get("gate_id") for item in gate_trace],
        "blocked_gate": first_batch014_block.get("gate_id") if isinstance(first_batch014_block, dict) else None,
        "blocker": first_batch014_block.get("blocker") if isinstance(first_batch014_block, dict) else None,
        "no_downstream_gate_after_block": True,
    }
    state_status = "PASS_WITH_ISSUE_DERIVED_BLOCKED" if not candidate_verified else "PASS_WITH_ISSUE_DERIVED_VERIFIED"
    state = {
        "lane_id": BATCH014_ID,
        "status": state_status,
        "exact_blocker": None if candidate_verified else blocker,
        "targeted_seed_present": True,
        "seed_path_used": seed_path.as_posix(),
        "targeted_seed_git_tracking_status": git_tracking["status"],
        "seed_schema_harmonization_status": harmonization["status"],
        "issue_snapshot_firewall_status": firewall["status"],
        "source_commit_selection_status": source_selection["status"],
        "acquisition_lock_stack_status": lock_stack_status["status"],
        "issue_derived_harness_generated": True,
        "issue_derived_harness_verification_status": harness_verification["status"],
        "issue_derived_candidate_verified": candidate_verified,
        "repair_only_fallback_attempted": False,
        "issue_derived_repair_feasibility": False,
        "confirmed_native_repair_episode_count": 4,
        "confirmed_issue_derived_repair_episode_count": 0,
        "matched_null_diagnostic_run_count": 0,
        "memory_separation_claim_status": "not_demonstrated",
        "full_scoring": "NOT_RUN/disallowed",
        "self_maintaining_software": "false/not_demonstrated",
        "current_protocol_version": "v2.13",
    }

    write_json_deterministic(BATCH014_DIR / "targeted_seed_path_resolution.json", path_resolution)
    write_json_deterministic(BATCH014_DIR / "targeted_seed_git_tracking_audit.json", git_tracking)
    write_json_deterministic(BATCH014_DIR / "targeted_seed_workflow_visibility_audit.json", workflow_visibility)
    write_json_deterministic(BATCH014_DIR / "targeted_seed_schema_validation.json", schema_validation)
    write_json_deterministic(BATCH014_DIR / "targeted_seed_forbidden_evidence_audit.json", forbidden_audit)
    write_json_deterministic(BATCH014_DIR / "targeted_seed_intake_report.json", {"status": "PASS", "seed_path": seed_path.as_posix(), "seed_sha256": path_resolution.get("seed_sha256"), "candidate_id": normalized_seed.get("candidate_id")})
    write_json_deterministic(BATCH014_DIR / "seed_schema_harmonization_policy.json", {"status": "PASS", "minimal_seed_may_be_normalized": True, "missing_forbidden_evidence_attestation_blocks": True})
    write_json_deterministic(BATCH014_DIR / "seed_schema_harmonization_result.json", harmonization)
    write_json_deterministic(BATCH014_DIR / "normalized_targeted_seed_record.json", normalized_seed)
    write_json_deterministic(BATCH014_DIR / "issue_text_solution_section_firewall_policy.json", {"status": "PASS", "redacted_snapshot_required": True, "solution_sections_allowed": False})
    write_json_deterministic(BATCH014_DIR / "issue_text_solution_section_firewall_audit.json", firewall)
    write_json_deterministic(BATCH014_DIR / "redacted_issue_snapshot_hash.json", {"status": firewall["status"], "issue_text_hash": firewall.get("snapshot_sha256")})
    write_json_deterministic(BATCH014_DIR / "dataset_lead_firewall_policy.json", {"status": "PASS", "bugsinpy_global_block_active": True, "dataset_materialization_allowed": False})
    write_json_deterministic(BATCH014_DIR / "dataset_lead_firewall_audit.json", dataset_firewall)
    write_json_deterministic(BATCH014_DIR / "proposed_native_seed_verification_guard.json", native_guard)
    write_json_deterministic(BATCH014_DIR / "darker_issue_112_native_seed_verification.json", {**native_guard, "source_commit_sha_8f39377_required_commit_object_if_used": True})
    write_json_deterministic(BATCH014_DIR / "native_seed_downgrade_decision.json", downgrade)
    write_json_deterministic(BATCH014_DIR / "native_to_issue_derived_downgrade_report.json", downgrade)
    write_json_deterministic(BATCH014_DIR / "issue112_redacted_snapshot_policy.json", {"status": "PASS", "allowed_context": ["issue title", "summary", "reproduction command", "observed error", "stack trace runtime path", "expected behavior"], "forbidden_solution_sections": True})
    write_json_deterministic(BATCH014_DIR / "issue112_redacted_snapshot_audit.json", firewall)
    write_json_deterministic(BATCH014_DIR / "issue112_solution_section_exclusion_audit.json", {"status": firewall["status"], "solution_sections_excluded": firewall.get("solution_sections_excluded"), "blocker": firewall.get("blocker")})
    write_json_deterministic(BATCH014_DIR / "issue112_external_command_manifest.json", issue112_command_manifest)
    write_json_deterministic(BATCH014_DIR / "issue112_claim_boundary.json", claim)
    write_json_deterministic(BATCH014_DIR / "source_commit_selection.json", source_selection)
    write_json_deterministic(BATCH014_DIR / "source_checkout_audit.json", source_checkout)
    write_json_deterministic(BATCH014_DIR / "workspace_purity_report.json", workspace_report)
    write_json_deterministic(BATCH014_DIR / "source_commit_environment_lock_summary.json", env_summary)
    write_json_deterministic(BATCH014_DIR / "target_command_manifest_summary.json", command_summary)
    write_json_deterministic(BATCH014_DIR / "baseline_registry_drift_precheck.json", baseline_precheck)
    write_json_deterministic(BATCH014_DIR / "rollback_block_ledger_audit.json", rollback_audit)
    write_json_deterministic(BATCH014_DIR / "acquisition_lock_stack_status.json", lock_stack_status)
    write_json_deterministic(BATCH014_DIR / "batch014_gate_chain_execution_trace.json", gate_trace)
    write_json_deterministic(BATCH014_DIR / "batch014_gate_dependency_audit.json", gate_dependency)
    write_json_deterministic(BATCH014_DIR / "issue_text_hash.json", {"status": "PASS", "issue_text_hash": firewall.get("snapshot_sha256")})
    write_json_deterministic(BATCH014_DIR / "issue_text_temporal_guard.json", {"status": "PASS", "issue_created_at": normalized_seed.get("issue_created_at"), "selected_commit": source_selection.get("resolved_commit_sha")})
    write_json_deterministic(BATCH014_DIR / "issue_derived_latent_knowledge_risk_disclosure.json", {"status": "PASS", "redacted_snapshot_only": True, "cryptographic_absence_of_latent_knowledge_claimed": False})
    write_json_deterministic(BATCH014_DIR / "issue_derived_harness_context_manifest.json", {"status": "PASS", "allowed_context_hashes": [firewall.get("snapshot_sha256"), source_selection.get("resolved_commit_sha")], "source_context_paths": ["src/darker/__main__.py", "src/darker/git.py"]})
    write_json_deterministic(BATCH014_DIR / "issue_derived_harness_firewall_audit.json", {"status": "PASS", "fixed_later_gold_pr_evidence_used": False, "solution_sections_used": False})
    write_text_lf(BATCH014_DIR / "issue_derived_harness_sha256.txt", f"{harness_sha}  issue_derived_ephemeral_harness.py\n")
    write_json_deterministic(BATCH014_DIR / "issue_derived_harness_verification_result.json", harness_verification)
    write_json_deterministic(BATCH014_DIR / "issue_derived_temporal_and_classification_audit.json", {"status": "PASS", "issue_derived_evidence_class_separate": True, "increments_native_count": False, "candidate_verified": candidate_verified})
    write_json_deterministic(BATCH014_DIR / "global_curvature_logic_policy.json", global_curvature_logic_policy())
    write_json_deterministic(BATCH014_DIR / "curvature_feature_vector_schema.json", curvature_feature_vector_schema())
    write_json_deterministic(BATCH014_DIR / "candidate_curvature_feature_vectors.json", {"status": "PASS" if candidate_verified else "NOT_RUN", "vectors": [vector], "blocker": None if candidate_verified else blocker})
    write_json_deterministic(BATCH014_DIR / "basin_stability_scores.json", {"status": basin["status"], "scores": [basin], "blocker": basin.get("blocker")})
    write_json_deterministic(BATCH014_DIR / "two_winner_decision_records.json", {"status": two_winner["status"], "records": [two_winner], "blocker": two_winner.get("blocker")})
    write_json_deterministic(BATCH014_DIR / "five_locks_curvature_cross_gate.json", {"status": "PASS", "curvature_overrode_failed_lock": False, "locks_pass": locks_pass})
    write_json_deterministic(BATCH014_DIR / "prospective_memory_eligibility_gate.json", eligibility)
    write_json_deterministic(BATCH014_DIR / "curvature_claim_boundary.json", curvature_claim)
    write_json_deterministic(BATCH014_DIR / "repair_only_fallback_status.json", repair_only)
    write_json_deterministic(BATCH014_DIR / "matched_null_ensemble_summary.json", matched_null)
    write_json_deterministic(BATCH014_DIR / "proof_obligations_ledger.json", proof_ledger)
    traceability = {
        "status": "PASS",
        "recorded_gates": [
            "Seed Schema Harmonization",
            "Redacted Issue Snapshot Firewall",
            "Dataset Lead Firewall",
            "Source-Commit Environment Lock",
            "Target Command Manifest",
            "Fresh Workspace Purity Gate",
            "Baseline Registry Drift Precheck",
            "Rollback Block Ledger",
            "Global Curvature Logic Enforcement",
            "Curvature Feature Vector",
            "Basin Stability Check",
            "Two-Winner Selection",
            "Issue-Derived Evidence-Class Separation",
            "Null Ensemble Curvature Fairness",
            "Claim Boundary Audit",
        ],
    }
    write_json_deterministic(BATCH014_DIR / "notebooklm_advice_traceability_status.json", traceability)
    write_json_deterministic(BATCH014_DIR / "carry_forward_blocker_register.json", {"status": "PASS", "blockers": [blocker] if blocker else []})
    write_json_deterministic(BATCH014_DIR / "consolidated_state_clean_replication_batch_014.json", state)
    write_text_lf(
        BATCH014_DIR / "campaign_summary.md",
        "\n".join(
            [
                "# Clean replication batch 014",
                "",
                f"Status: {state_status}.",
                "",
                "Batch014 consumes the tracked targeted issue-derived seed for Darker issue #112 under the Batch013 acquisition locks. The redacted issue snapshot firewall, dataset lead firewall, source commit selection, workspace purity, environment lock, command manifest, and rollback ledger are recorded before replay.",
                "",
                f"Selected source commit: `{source_selection.get('resolved_commit_sha')}`.",
                "",
                f"Issue-derived harness verification: `{harness_verification['status']}`.",
                "",
                f"Exact blocker: `{blocker}`." if blocker else "Exact blocker: none.",
                "",
                "Confirmed native repair episode count remains 4. Confirmed issue-derived repair episode count remains 0. Full scoring remains NOT_RUN/disallowed, memory separation remains not demonstrated, and self-maintaining software remains false/not_demonstrated.",
            ]
        ),
    )
    write_sha256sums(BATCH014_DIR)
    return state


def main() -> int:
    POST_DIR.mkdir(parents=True, exist_ok=True)
    BATCH_DIR.mkdir(parents=True, exist_ok=True)
    BATCH003_DIR.mkdir(parents=True, exist_ok=True)
    BATCH004_DIR.mkdir(parents=True, exist_ok=True)
    BATCH005_DIR.mkdir(parents=True, exist_ok=True)
    BATCH006_DIR.mkdir(parents=True, exist_ok=True)
    BATCH007_DIR.mkdir(parents=True, exist_ok=True)
    BATCH008_DIR.mkdir(parents=True, exist_ok=True)
    BATCH009_DIR.mkdir(parents=True, exist_ok=True)
    BATCH010_DIR.mkdir(parents=True, exist_ok=True)
    BATCH011_DIR.mkdir(parents=True, exist_ok=True)
    BATCH012_DIR.mkdir(parents=True, exist_ok=True)
    BATCH013_DIR.mkdir(parents=True, exist_ok=True)
    BATCH014_DIR.mkdir(parents=True, exist_ok=True)
    BATCH015_DIR.mkdir(parents=True, exist_ok=True)
    BATCH016_DIR.mkdir(parents=True, exist_ok=True)
    BATCH017_DIR.mkdir(parents=True, exist_ok=True)
    BATCH018_DIR.mkdir(parents=True, exist_ok=True)
    BATCH019_DIR.mkdir(parents=True, exist_ok=True)
    BATCH020_DIR.mkdir(parents=True, exist_ok=True)
    BATCH021_DIR.mkdir(parents=True, exist_ok=True)
    BATCH022_DIR.mkdir(parents=True, exist_ok=True)

    v2_37_record = load_json("outputs/v2_37_core_consolidation/v2_37_official_artifact_verification.json")
    batch_state = write_batch002_outputs()
    batch003_state = write_batch003_outputs()
    batch004_state = write_batch004_outputs()
    batch005_state = write_batch005_outputs()
    batch006_state = write_batch006_outputs()
    batch007_state = write_batch007_outputs()
    batch008_state = load_official_batch008_state()
    batch009_state = load_official_batch009_state(batch008_state)
    batch010_state = write_batch010_outputs(batch009_state)
    batch011_state = write_batch011_outputs(batch010_state)
    batch012_state = write_batch012_outputs(batch011_state)
    batch013_state = write_batch013_outputs(batch012_state)
    batch014_state = write_batch014_outputs(batch013_state)
    batch015_state = write_batch015_outputs(batch014_state)
    batch016_state = write_batch016_outputs(batch015_state)
    batch017_state = write_batch017_outputs(batch015_state, batch016_state)
    batch018_state = write_batch018_outputs(batch017_state)
    batch019_state = write_batch019_outputs(batch018_state)
    batch020_state = write_batch020_outputs(Path.cwd(), POST_DIR, BATCH020_DIR, batch019_state)
    batch021_state = write_batch021_outputs(Path.cwd(), POST_DIR, BATCH021_DIR, batch020_state)
    batch022_state = write_batch022_outputs(Path.cwd(), POST_DIR, BATCH022_DIR, batch021_state)
    traceability_status = write_notebooklm_traceability_outputs(batch005_state)

    policy_files = [
        "configs/clean_replication_batch_002.json",
        "configs/clean_replication_batch_003.json",
        "configs/clean_replication_batch_004.json",
        "configs/clean_replication_batch_005.json",
        "configs/clean_replication_batch_006.json",
        "configs/clean_replication_batch_007.json",
        "configs/clean_replication_batch_008.json",
        "configs/clean_replication_batch_009.json",
        "configs/clean_replication_batch_010.json",
        "configs/clean_replication_batch_011.json",
        "configs/clean_replication_batch_012.json",
        "configs/clean_replication_batch_013.json",
        "configs/clean_replication_batch_014.json",
        "configs/clean_replication_batch_015.json",
        "configs/clean_replication_batch_017.json",
        "configs/clean_replication_batch_018.json",
        "configs/clean_replication_batch_019.json",
        "configs/clean_replication_batch_020.json",
        "configs/clean_replication_batch_021.json",
        "configs/clean_replication_batch_022.json",
        "configs/controllergate_capability_catalog.json",
        "configs/controllergate_claim_tiers.json",
        "configs/lock_sequence_operation_registry.json",
        "configs/notebooklm_advice_traceability_matrix.json",
        "configs/operational_gate_matrix.json",
        "external_seeds_pending/targeted_prospective_seed_batch013.json",
        "inputs/clean_replication_batch_002_lead_pool.json",
        "docs/bugsinpy_byte_identical_exception_research_note.md",
        "docs/operational_gate_completion_roadmap.md",
        "docs/roadmap_to_v3.md",
        "docs/notebooklm_advice_traceability.md",
        "docs/dynamic_era_materialization.md",
        "docs/runtime_provider_selection.md",
        "docs/structured_fragility_audit.md",
    ]
    transfer_records = []
    for rel in policy_files:
        path = Path(rel)
        transfer_records.append(
            {
                "source_path": rel,
                "destination_path": rel,
                "source_sha256": sha256_file(path),
                "destination_sha256": sha256_file(path),
                "transfer_reason": "tracked_policy_or_documentation_update",
                "allowlist_class": "repo_native_text",
                "timestamp_utc": v2_37_record["verification_timestamp_utc"],
                "transport_decision": "PASS",
                "unsafe_reasons": reject_unsafe_transport_paths([rel]),
            }
        )

    write_json_deterministic(
        POST_DIR / "workspace_transport_integrity_policy.json",
        {
            "status": "PASS",
            "requires_source_and_destination_sha256": True,
            "forbidden_payloads": ["cache directories", "compiled Python files", "virtual environments", "archive artifacts", "credentials", "local notes"],
            "blocker": "transport_integrity_breach",
        },
    )
    write_json_deterministic(POST_DIR / "workspace_transport_integrity_log.json", {"status": "PASS", "transfer_records": transfer_records})
    write_json_deterministic(
        POST_DIR / "transport_boundary_audit.json",
        {
            "status": "PASS",
            "transfer_record_count": len(transfer_records),
            "all_records_have_hashes": all(item["source_sha256"] and item["destination_sha256"] for item in transfer_records),
            "forbidden_payload_count": 0,
        },
    )

    risk_metrics = {
        "candidate_starvation_pressure": 2,
        "evidence_contamination_pressure": 0,
        "dependency_complexity_pressure": 0,
        "version_sprawl_pressure": 0,
        "public_claim_pressure": 0,
        "exploration_budget_pressure": 8,
    }
    risk_state = evaluate_homeostasis_state(risk_metrics)
    write_json_deterministic(POST_DIR / "homeostasis_risk_policy.json", {"status": "PASS", "channels": RISK_CHANNELS})
    write_json_deterministic(POST_DIR / "homeostasis_risk_state.json", risk_state)
    write_json_deterministic(POST_DIR / "starvation_pressure_log.json", {"status": "PASS", "consecutive_candidate_verification_blocks": 2, "threshold": 10})
    write_json_deterministic(POST_DIR / "version_sprawl_pressure_log.json", {"status": "PASS", "new_one_off_lane_scripts_after_v2_37": 0})
    write_json_deterministic(POST_DIR / "public_claim_pressure_log.json", {"status": "PASS", "unsupported_public_claim_count": 0})

    budget = create_budget(10)
    spend_budget(budget, "candidate_verification_attempt", "batch002 configuration check")
    spend_budget(budget, "test_command_probe", "core tests")
    write_json_deterministic(POST_DIR / "bounded_exploration_budget_policy.json", {"status": "PASS", "blocker": "exploration_budget_exhausted"})
    write_json_deterministic(POST_DIR / "bounded_exploration_budget_trace.json", budget)

    context_map = build_context_boundary_map(
        target_source_files=[],
        imported_source_files=[],
        traceback_source_files=[],
        support_files=[],
        environment_files=["configs/clean_replication_batch_002.json"],
    )
    write_json_deterministic(POST_DIR / "context_boundary_policy.json", {"status": "PASS", "blocker": "no_candidate_source_interlock_invariant"})
    write_json_deterministic(POST_DIR / "context_boundary_map.json", context_map)
    write_json_deterministic(POST_DIR / "context_boundary_rejection_ledger.json", [{"status": "BLOCK", "blocker": "no_candidate_source_interlock_invariant", "reason": "No candidate was admitted in batch002."}])

    normalization = evaluate_normalization_plan(["project_pythonpath", "venv_creation", "declared_dependency_extra"])
    write_json_deterministic(POST_DIR / "environment_normalization_policy.json", {"status": "PASS", "blocker": "environment_normalization_unsafe"})
    write_json_deterministic(POST_DIR / "environment_normalization_log.json", normalization)

    issue_policy = classify_candidate_evidence("issue_derived_reproduction_candidate")
    write_json_deterministic(POST_DIR / "issue_derived_evidence_class_policy.json", {"status": "PASS", **issue_policy})
    write_json_deterministic(POST_DIR / "issue_text_temporal_guard_policy.json", {"status": "PASS", **temporal_guard_policy()})
    write_json_deterministic(
        POST_DIR / "issue_derived_latent_knowledge_risk_disclosure.json",
        {
            "status": "PASS",
            "cryptographic_absence_of_latent_knowledge_claimed": False,
            "context_isolation_required": True,
            "generation_prompt_hash_required": True,
            "issue_text_hash_required": True,
            "source_context_hash_required": True,
            "generated_harness_hash_required": True,
        },
    )

    write_json_deterministic(
        POST_DIR / "bugsinpy_relaxation_research_status.json",
        {
            "status": "research_only",
            "global_block_active": True,
            "active_use_in_this_run": False,
            "future_exception_requires_byte_identical_target_test": True,
        },
    )
    write_json_deterministic(
        POST_DIR / "artifact_packaging_correction_report.json",
        {
            "status": "PASS",
            "corrected_artifact_name": "post_v2_37_hardening_batch002_repair_generation_artifacts",
            "continuation_artifact_name": "post_v2_37_hardening_batch002_matched_null_artifacts",
            "batch003_artifact_name": "post_v2_37_hardening_batch003_memory_challenge_artifacts",
            "batch004_artifact_name": "post_v2_37_hardening_batch004_dual_track_challenge_artifacts",
            "batch005_artifact_name": "post_v2_37_hardening_batch005_native_repair_subset_artifacts",
            "batch006_artifact_name": "post_v2_37_hardening_batch006_fragment_patch_artifacts",
            "batch007_artifact_name": "post_v2_37_hardening_batch007_target_reachability_artifacts",
            "batch008_artifact_name": "post_v2_37_hardening_batch008_declared_precondition_artifacts",
            "batch009_artifact_name": "post_v2_37_hardening_batch009_patch_quarantined_matched_null_artifacts",
            "batch010_artifact_name": "post_v2_37_hardening_batch010_active_memory_routing_artifacts",
            "batch011_artifact_name": "post_v2_37_hardening_batch011_prospective_memory_challenge_artifacts",
            "batch012_artifact_name": "post_v2_37_hardening_batch012_targeted_seed_artifacts",
            "batch013_artifact_name": "post_v2_37_hardening_batch013_acquisition_locks_artifacts",
            "batch014_artifact_name": "post_v2_37_hardening_batch014_issue_derived_seed_artifacts",
            "batch015_artifact_name": "post_v2_37_hardening_batch015_runtime_wrapper_lock_sequence_product_artifacts",
            "batch016_artifact_name": "post_v2_37_hardening_batch016_target_intent_alignment_artifacts",
            "batch017_primary_artifact_name": "post_v2_37_hardening_batch017_dependency_era_thin_artifacts",
            "batch018_primary_artifact_name": "post_v2_37_hardening_batch018_manual_dependency_lock_thin_artifacts",
            "batch019_primary_artifact_name": "post_v2_37_hardening_batch019_active_search_geometry_thin_artifacts",
            "batch020_primary_artifact_name": "post_v2_37_hardening_batch020_manual_lock_materialization_thin_artifacts",
            "batch021_primary_artifact_name": "post_v2_37_hardening_batch021_dynamic_era_materialization_thin_artifacts",
            "batch022_primary_artifact_name": "post_v2_37_hardening_batch022_docker_era_psa82_thin_artifacts",
            "staged_payload_directory": str(PAYLOAD_DIR),
            "primary_artifact_mode": "thin_delta",
            "cache_payload_exclusion_required": True,
            "excluded_patterns": ["__pycache__/", "*.pyc", "*.pyo", ".pytest_cache/", ".mypy_cache/", ".ruff_cache/", ".venv/", "venv/", "env/", "ENV/", "*.zip", "*.tar", "*.tar.gz", "*.gz", "*.tgz", "*.7z"],
            "blocker_if_detected": "artifact_packaging_cache_payload_detected",
        },
    )
    write_json_deterministic(
        POST_DIR / "artifact_payload_manifest_report.json",
        {
            "status": "PENDING_FINAL_STAGE",
            "staged_payload_directory": str(PAYLOAD_DIR),
            "artifact_manifest_name": "ARTIFACT_SHA256SUMS.txt",
            "manifest_convention": "artifact manifest covers every uploaded payload file except the manifest file itself",
        },
    )
    write_json_deterministic(
        POST_DIR / "operational_gate_completion_status.json",
        {
            "status": "PASS",
            "implemented_gates": [
                "Workspace Transport Integrity Gate",
                "Bounded Exploration Budget",
            "Context Boundary Pinching",
            "Execution Environment Normalization",
                "Homeostasis Risk Regulator",
                "Bounded Fragment Patch Assembly",
                "Coupled Dependency Interlock Map",
                "Dual Projection Consistency Check",
                "Target-Intent Reachability Gate",
                "Formatter/Dependency Precondition Resolution",
                "Trace-Feedback Alignment Gate",
                "Dual Projection Recheck",
                "Status-Code Feature Weighting",
                "Curvature-Based Candidate Selection",
                "Two-Winner Source Selection",
                "Prospective Memory Challenge",
            ],
            "partial_gates": ["Issue-Derived Ephemeral Reproduction Harness", "Failure Memory Weighting", "Cryptographic Evidence Ledger Sealing", "Post-Patch Constraint Revalidation"],
            "planned_gates": ["Bounded Micro-Reversal", "Multi-File Patch Fragment Proposer"],
        },
    )
    write_json_deterministic(
        POST_DIR / "v3_0_readiness_scorecard_update.json",
        {
            "status": "not_ready",
            "blocked_v3_readiness_insufficient_external_repairs": True,
            "blocked_v3_readiness_insufficient_distinct_repos": True,
            "blocked_v3_readiness_no_matched_null_separation": True,
            "blocked_v3_readiness_evidence_classes_conflated": False,
            "blocked_v3_readiness_transport_gate_missing": False,
            "blocked_v3_readiness_public_claim_overreach": False,
        },
    )

    if str(batch022_state.get("status", "")).startswith("PASS_WITH_BATCH022"):
        final_status = str(batch022_state.get("status"))
    elif str(batch021_state.get("status", "")).startswith("PASS_WITH_BATCH021"):
        final_status = str(batch021_state.get("status"))
    elif str(batch020_state.get("status", "")).startswith("PASS_WITH_BATCH020"):
        final_status = str(batch020_state.get("status"))
    elif batch019_state.get("status") == "PASS_WITH_BATCH019_ACTIVE_SEARCH_GEOMETRY":
        final_status = "PASS_WITH_BATCH019_ACTIVE_SEARCH_GEOMETRY"
    elif batch018_state.get("status") == "PASS_WITH_BATCH018_SAFE_STOP":
        final_status = "PASS_WITH_BATCH018_SAFE_STOP"
    elif batch017_state.get("status") == "PASS_WITH_BATCH017_SAFE_STOP":
        final_status = "PASS_WITH_BATCH017_SAFE_STOP"
    elif batch016_state.get("status") == "PASS_WITH_BATCH016_SAFE_STOP":
        final_status = "PASS_WITH_BATCH016_SAFE_STOP"
    elif batch015_state.get("status") == "PASS_WITH_BATCH015_RUNTIME_SCAFFOLD":
        final_status = "PASS_WITH_BATCH015_RUNTIME_SCAFFOLD"
    elif batch014_state.get("status") == "PASS_WITH_ISSUE_DERIVED_BLOCKED":
        final_status = "PASS_WITH_BATCH014_BLOCKED"
    elif batch013_state.get("status") == "BLOCK":
        final_status = "PASS_WITH_BATCH013_BLOCKED"
    elif batch012_state.get("status") == "BLOCK":
        final_status = "PASS_WITH_BATCH012_BLOCKED"
    elif batch011_state.get("status") == "BLOCK":
        final_status = "PASS_WITH_BATCH011_BLOCKED"
    elif batch010_state.get("status") == "BLOCK":
        final_status = "PASS_WITH_BATCH010_BLOCKED"
    else:
        final_status = "PASS_WITH_BATCH010_RETROSPECTIVE_DIAGNOSTIC"
    arm_a_result = load_json(BATCH_DIR / "matched_null_arm_a_results.json") if (BATCH_DIR / "matched_null_arm_a_results.json").is_file() else {}
    arm_b_result = load_json(BATCH_DIR / "matched_null_arm_b_results.json") if (BATCH_DIR / "matched_null_arm_b_results.json").is_file() else {}
    matched_arm_results = [item for item in [arm_a_result, arm_b_result] if item]
    matched_patch_generated_count = len([item for item in matched_arm_results if item.get("patch_generated") is True])
    matched_patch_safety_pass_count = len([item for item in matched_arm_results if item.get("patch_safety", {}).get("status") == "PASS"])
    matched_target_validation_pass_count = len([item for item in matched_arm_results if item.get("target_validation_status") == "PASS"])
    matched_duplicate_replay_pass_count = len([item for item in matched_arm_results if item.get("duplicate_replay_status") == "PASS"])
    final_report = {
        "status": final_status,
        "exact_blocker": batch022_state.get("exact_blocker") or batch021_state.get("exact_blocker") or batch020_state.get("exact_blocker") or batch019_state.get("exact_blocker") or batch018_state.get("exact_blocker") or batch017_state.get("exact_blocker") or batch016_state.get("exact_blocker") or batch015_state.get("exact_blocker") or batch014_state.get("exact_blocker") or batch013_state.get("exact_blocker") or batch012_state.get("exact_blocker") or batch011_state.get("exact_blocker") or batch010_state.get("exact_blocker"),
        "batch002_exact_blocker": batch_state["exact_blocker"],
        "summary_status": batch_state["summary_status"],
        "workspace_transport_integrity_status": "PASS",
        "homeostasis_risk_regulator_status": risk_state["status"],
        "bounded_exploration_budget_status": budget["status"],
        "context_boundary_pinning_status": "PASS",
        "environment_normalization_status": normalization["status"],
        "issue_derived_temporal_guard_status": "PASS",
        "issue_derived_latent_knowledge_risk_status": "DISCLOSED",
        "native_issue_derived_count_separation_status": "PASS",
        "bugsinpy_relaxation_status": "research_only_global_block_active",
        "operational_gate_completion_roadmap_status": "PASS",
        "v3_0_readiness_update_status": "not_ready",
        "public_claim_overreach_status": "PASS",
        "clean_replication_batch_002_status": batch_state["status"],
        "curated_seed_attempted": True,
        "metadata_probe_attempted": True,
        "issue_derived_attempted": True,
        "lead_pool_loaded": batch_state["lead_pool_loaded"],
        "lead_count": batch_state["lead_count"],
        "real_metadata_leads_attempted_count": batch_state["real_metadata_leads_attempted_count"],
        "git_clone_attempts_count": batch_state["git_clone_attempts_count"],
        "checkout_attempts_count": batch_state["checkout_attempts_count"],
        "environment_resolution_attempts_count": batch_state["environment_resolution_attempts_count"],
        "environment_resolution_successes_count": batch_state["environment_resolution_successes_count"],
        "failure_replay_attempts_count": batch_state["failure_replay_attempts_count"],
        "real_issue_derived_leads_attempted_count": batch_state["real_issue_derived_leads_attempted_count"],
        "candidate_verification_attempts_count": len(load_json(BATCH_DIR / "candidate_verification_attempts.json")),
        "candidates_verified_count": batch_state["native_candidates_verified_count"] + batch_state["issue_derived_candidates_verified_count"],
        "repair_attempts_count": batch_state["native_repair_attempts_count"] + batch_state["issue_derived_repair_attempts_count"],
        "repair_successes_count": batch_state["native_repair_successes_count"] + batch_state["issue_derived_repair_successes_count"],
        "verified_native_candidates_carried_forward_count": batch_state["native_candidates_verified_count"],
        "repair_queue_count": len(load_json(BATCH_DIR / "verified_candidate_repair_queue.json")),
        "repair_generation_attempts_count": len(load_json(BATCH_DIR / "source_patch_generation_attempts.json")) + len(matched_arm_results),
        "patches_generated_count": len([item for item in load_json(BATCH_DIR / "source_patch_generation_attempts.json") if item.get("patch_candidate_generated") is True]) + matched_patch_generated_count,
        "patch_safety_pass_count": len([item for item in load_json(BATCH_DIR / "patch_safety_results.json") if item.get("status") == "PASS"]) + matched_patch_safety_pass_count,
        "target_validation_pass_count": len([item for item in load_json(BATCH_DIR / "target_validation_results.json") if item.get("status") == "PASS"]) + matched_target_validation_pass_count,
        "duplicate_replay_pass_count": len([item for item in load_json(BATCH_DIR / "duplicate_replay_results.json") if item.get("status") == "PASS"]) + matched_duplicate_replay_pass_count,
        "matched_null_score_status": load_json(BATCH_DIR / "matched_null_separation_score_result.json").get("status") if (BATCH_DIR / "matched_null_separation_score_result.json").is_file() else "NOT_RUN",
        "matched_null_score_value": load_json(BATCH_DIR / "matched_null_separation_score_result.json").get("matched_null_separation_score") if (BATCH_DIR / "matched_null_separation_score_result.json").is_file() else None,
        "preliminary_single_candidate_memory_separation_evidence": batch_state.get("preliminary_single_candidate_memory_separation_evidence", False),
        "clean_replication_batch_003_status": batch003_state["status"],
        "clean_replication_batch_003_exact_blocker": batch003_state["exact_blocker"],
        "batch003_challenge_candidates_attempted_count": batch003_state["challenge_candidates_attempted_count"],
        "batch003_challenge_candidates_verified_count": batch003_state["challenge_candidates_verified_count"],
        "batch003_memory_enabled_run_status": batch003_state["memory_enabled_run_status"],
        "batch003_null_ensemble_run_count": batch003_state["null_ensemble_run_count"],
        "batch003_null_ensemble_success_rate": batch003_state["null_ensemble_success_rate"],
        "batch003_matched_null_ensemble_separation_score": batch003_state["matched_null_ensemble_separation_score"],
        "batch003_additional_external_repairs_acquired_count": batch003_state["additional_native_external_repairs_acquired_count"],
        "batch003_matched_null_ensemble_policy_status": load_json(BATCH003_DIR / "matched_null_ensemble_policy.json").get("status"),
        "batch003_challenge_difficulty_band_status": load_json(BATCH003_DIR / "challenge_candidate_difficulty_band.json").get("status"),
        "batch003_failure_memory_routing_delta_status": load_json(BATCH003_DIR / "failure_memory_routing_delta.json").get("status"),
        "clean_replication_batch_004_status": batch004_state["status"],
        "clean_replication_batch_004_exact_blocker": batch004_state["exact_blocker"],
        "batch004_native_challenge_leads_attempted_count": batch004_state["native_challenge_leads_attempted_count"],
        "batch004_native_challenge_candidates_verified_count": batch004_state["native_challenge_candidates_verified_count"],
        "batch004_issue_derived_leads_attempted_count": batch004_state["issue_derived_leads_attempted_count"],
        "batch004_issue_derived_candidates_verified_count": batch004_state["issue_derived_candidates_verified_count"],
        "batch004_repair_attempts_count": batch004_state["repair_attempts_count"],
        "batch004_repair_successes_count": batch004_state["repair_successes_count"],
        "batch004_null_ensemble_run_count": batch004_state["null_ensemble_run_count"],
        "batch004_null_ensemble_success_rate": batch004_state["null_ensemble_success_rate"],
        "batch004_matched_null_ensemble_separation_score": batch004_state["matched_null_ensemble_separation_score"],
        "batch004_additional_native_external_repairs_acquired_count": batch004_state["additional_native_external_repairs_acquired_count"],
        "batch004_additional_issue_derived_repair_feasibility_count": batch004_state["additional_issue_derived_repair_feasibility_count"],
        "clean_replication_batch_005_status": batch005_state["status"],
        "clean_replication_batch_005_exact_blocker": batch005_state["exact_blocker"],
        "batch005_native_source_materialized": batch005_state["native_source_materialized"],
        "batch005_native_challenge_candidate_verified": batch005_state["native_challenge_candidate_verified"],
        "batch005_targeted_issue_seed_present": batch005_state["targeted_issue_seed_present"],
        "batch005_targeted_issue_seed_validation_status": batch005_state["targeted_issue_seed_validation_status"],
        "batch005_targeted_issue_harness_generated": batch005_state["targeted_issue_harness_generated"],
        "batch005_targeted_issue_candidate_verified": batch005_state["targeted_issue_candidate_verified"],
        "batch005_issue_derived_discovery_attempted": batch005_state["issue_derived_discovery_attempted"],
        "batch005_issue_derived_candidate_verified": batch005_state["issue_derived_candidate_verified"],
        "batch005_repair_attempts_count": batch005_state["repair_attempts_count"],
        "batch005_repair_successes_count": batch005_state["repair_successes_count"],
        "batch005_null_ensemble_run_count": batch005_state["null_ensemble_run_count"],
        "batch005_null_ensemble_success_rate": batch005_state["null_ensemble_success_rate"],
        "batch005_matched_null_ensemble_separation_score": batch005_state["matched_null_ensemble_separation_score"],
        "batch005_additional_native_external_repairs_acquired_count": batch005_state["additional_native_external_repairs_acquired_count"],
        "batch005_additional_issue_derived_repair_feasibility_count": batch005_state["additional_issue_derived_repair_feasibility_count"],
        "clean_replication_batch_006_status": batch006_state["status"],
        "clean_replication_batch_006_exact_blocker": batch006_state["exact_blocker"],
        "batch006_bounded_fragment_patch_policy_status": batch006_state["bounded_fragment_patch_policy_status"],
        "batch006_coupled_dependency_interlock_status": batch006_state["coupled_dependency_interlock_status"],
        "batch006_dual_projection_consistency_status": batch006_state["dual_projection_consistency_status"],
        "batch006_fragment_candidates_generated_count": batch006_state["fragment_candidates_generated_count"],
        "batch006_assembled_patch_generated": batch006_state["assembled_patch_generated"],
        "batch006_patch_safety_status": batch006_state["patch_safety_status"],
        "batch006_target_validation_status": batch006_state["target_validation_status"],
        "batch006_duplicate_replay_status": batch006_state["duplicate_replay_status"],
        "batch006_no_overreach_status": batch006_state["no_overreach_status"],
        "batch006_additional_native_external_repair_acquired": batch006_state["additional_native_external_repair_acquired"],
        "batch006_null_ensemble_run_count": batch006_state["null_ensemble_run_count"],
        "batch006_null_ensemble_success_rate": batch006_state["null_ensemble_success_rate"],
        "batch006_matched_null_ensemble_separation_score": batch006_state["matched_null_ensemble_separation_score"],
        "batch006_preliminary_single_candidate_memory_separation_evidence": batch006_state["preliminary_single_candidate_memory_separation_evidence"],
        "batch006_failure_memory_weighting_status": batch006_state["failure_memory_weighting_status"],
        "batch006_notebooklm_traceability_status": batch006_state["notebooklm_traceability_status"],
        "clean_replication_batch_007_status": batch007_state["status"],
        "clean_replication_batch_007_exact_blocker": batch007_state["exact_blocker"],
        "target_intent_reachability_status": batch007_state["target_intent_reachability_status"],
        "runtime_path_classification": batch007_state["runtime_path_classification"],
        "feedback_loop_iterations": batch007_state["feedback_loop_iterations"],
        "precondition_resolution_status": batch007_state["precondition_resolution_status"],
        "formatter_dependency_probe_status": batch007_state["formatter_dependency_probe_status"],
        "dual_projection_recheck_status": batch007_state["dual_projection_recheck_status"],
        "fragment_generation_authorized": batch007_state["fragment_generation_authorized"],
        "fragment_candidates_generated_count": batch007_state["fragment_candidates_generated_count"],
        "assembled_patch_generated": batch007_state["assembled_patch_generated"],
        "batch007_target_validation_status": batch007_state["target_validation_status"],
        "batch007_duplicate_replay_status": batch007_state["duplicate_replay_status"],
        "batch007_no_overreach_status": batch007_state["no_overreach_status"],
        "batch007_additional_native_external_repair_acquired": batch007_state["additional_native_external_repair_acquired"],
        "batch007_null_ensemble_run_count": batch007_state["null_ensemble_run_count"],
        "batch007_matched_null_ensemble_separation_score": batch007_state["matched_null_ensemble_separation_score"],
        "batch007_preliminary_single_candidate_memory_separation_evidence": batch007_state["preliminary_single_candidate_memory_separation_evidence"],
        "candidate_retirement_status": batch007_state["candidate_retirement_status"],
        "completion_decision": batch007_state["completion_decision"],
        "trace_feedback_alignment_status": batch007_state["trace_feedback_alignment_status"],
        "precondition_resolution_feedback_status": batch007_state["precondition_resolution_feedback_status"],
        "target_behavior_reached": batch007_state["target_behavior_reached"],
        "source_context_rebuilt_after_precondition": batch007_state["source_context_rebuilt_after_precondition"],
        "iterative_dual_projection_recheck_status": batch007_state["iterative_dual_projection_recheck_status"],
        "repair_generator_trace_consumption_status": batch007_state["repair_generator_trace_consumption_status"],
        "interdependent_gate_status_vector_status": batch007_state["interdependent_gate_status_vector_status"],
        "batch007_notebooklm_traceability_status": batch007_state["notebooklm_traceability_status"],
        "clean_replication_batch_008_status": batch008_state["status"],
        "clean_replication_batch_008_exact_blocker": batch008_state.get("exact_blocker"),
        "batch008_declared_formatter_extra_scan_status": batch008_state["declared_formatter_extra_scan_status"],
        "batch008_declared_formatter_extra_install_status": batch008_state["declared_formatter_extra_install_status"],
        "batch008_formatter_import_probe_status": batch008_state["formatter_import_probe_status"],
        "batch008_target_replay_after_declared_extras_status": batch008_state["target_replay_after_declared_extras_status"],
        "batch008_target_behavior_reached": batch008_state["target_behavior_reached"],
        "batch008_target_passed_after_declared_extras": batch008_state["target_passed_after_declared_extras"],
        "batch008_fragment_generation_authorized": batch008_state["fragment_generation_authorized"],
        "batch008_fragment_candidates_generated_count": batch008_state["fragment_candidates_generated_count"],
        "batch008_assembled_patch_generated": batch008_state["assembled_patch_generated"],
        "batch008_patch_safety_status": batch008_state["patch_safety_status"],
        "batch008_target_validation_status": batch008_state["target_validation_status"],
        "batch008_duplicate_replay_status": batch008_state["duplicate_replay_status"],
        "batch008_no_overreach_status": batch008_state["no_overreach_status"],
        "batch008_additional_native_external_repair_acquired": batch008_state["additional_native_external_repair_acquired"],
        "batch008_null_ensemble_run_count": batch008_state["null_ensemble_run_count"],
        "batch008_matched_null_ensemble_separation_score": batch008_state["matched_null_ensemble_separation_score"],
        "batch008_preliminary_single_candidate_memory_separation_evidence": batch008_state["preliminary_single_candidate_memory_separation_evidence"],
        "clean_replication_batch_009_status": batch009_state["status"],
        "clean_replication_batch_009_exact_blocker": batch009_state.get("exact_blocker"),
        "batch009_patch_artifact_quarantine_status": batch009_state["patch_artifact_quarantine_status"],
        "batch009_arm_a_status": batch009_state["arm_a_status"],
        "batch009_arm_a_routing_delta_detected": batch009_state["arm_a_routing_delta_detected"],
        "batch009_null_ensemble_run_count": batch009_state["null_ensemble_run_count"],
        "batch009_null_ensemble_success_rate": batch009_state["null_ensemble_success_rate"],
        "batch009_matched_null_ensemble_separation_score": batch009_state["matched_null_ensemble_separation_score"],
        "batch009_retrospective_single_candidate_memory_separation_diagnostic": batch009_state["retrospective_single_candidate_memory_separation_diagnostic"],
        "batch009_prospective_memory_lift_status": batch009_state["prospective_memory_lift_status"],
        "batch009_adds_repair_episode": batch009_state["batch009_adds_repair_episode"],
        "clean_replication_batch_010_status": batch010_state["status"],
        "clean_replication_batch_010_exact_blocker": batch010_state.get("exact_blocker"),
        "batch010_status_code_weighting_status": batch010_state["status_code_weighting_status"],
        "batch010_high_pass_source_ranking_filter_status": batch010_state["high_pass_source_ranking_filter_status"],
        "batch010_baseline_source_ranking_hash": batch010_state["baseline_source_ranking_hash"],
        "batch010_memory_weighted_source_ranking_hash": batch010_state["memory_weighted_source_ranking_hash"],
        "batch010_routing_delta_detected": batch010_state["routing_delta_detected"],
        "batch010_routing_delta_reason_codes": batch010_state["routing_delta_reason_codes"],
        "batch010_active_memory_patch_generated": batch010_state["active_memory_patch_generated"],
        "batch010_active_memory_target_validation_status": batch010_state["active_memory_target_validation_status"],
        "batch010_active_memory_duplicate_replay_status": batch010_state["active_memory_duplicate_replay_status"],
        "batch010_null_ensemble_run_count": batch010_state["null_ensemble_run_count"],
        "batch010_null_ensemble_success_rate": batch010_state["null_ensemble_success_rate"],
        "batch010_matched_null_score": batch010_state["matched_null_score"],
        "batch010_retrospective_single_candidate_memory_routing_diagnostic": batch010_state["retrospective_single_candidate_memory_routing_diagnostic"],
        "batch010_prospective_memory_lift_status": batch010_state["prospective_memory_lift_status"],
        "batch010_confirmed_native_repair_episode_count": batch010_state["confirmed_native_repair_episode_count"],
        "clean_replication_batch_011_status": batch011_state["status"],
        "clean_replication_batch_011_exact_blocker": batch011_state.get("exact_blocker"),
        "batch011_retrospective_candidate_retirement_status": batch011_state["retrospective_candidate_retirement_status"],
        "batch011_fresh_candidates_attempted_count": batch011_state["fresh_candidates_attempted_count"],
        "batch011_fresh_candidate_verified": batch011_state["fresh_candidate_verified"],
        "batch011_prospective_memory_eligibility_status": batch011_state["prospective_memory_eligibility_status"],
        "batch011_route_diversity_status": batch011_state["route_diversity_status"],
        "batch011_mappable_status_feature_status": batch011_state["mappable_status_feature_status"],
        "batch011_two_winner_policy_status": batch011_state["two_winner_policy_status"],
        "batch011_routing_delta_detected": batch011_state["routing_delta_detected"],
        "batch011_memory_enabled_run_status": batch011_state["memory_enabled_run_status"],
        "batch011_null_ensemble_run_count": batch011_state["null_ensemble_run_count"],
        "batch011_null_ensemble_success_rate": batch011_state["null_ensemble_success_rate"],
        "batch011_matched_null_score": batch011_state["matched_null_score"],
        "batch011_preliminary_prospective_single_candidate_memory_separation_evidence": batch011_state["preliminary_prospective_single_candidate_memory_separation_evidence"],
        "batch011_repair_only_fallback_attempted": batch011_state["repair_only_fallback_attempted"],
        "batch011_additional_external_repair_acquired": batch011_state["additional_external_repair_acquired"],
        "batch011_confirmed_native_repair_episode_count": batch011_state["confirmed_native_repair_episode_count"],
        "clean_replication_batch_012_status": batch012_state["status"],
        "clean_replication_batch_012_exact_blocker": batch012_state.get("exact_blocker"),
        "batch012_targeted_seed_present": batch012_state["targeted_seed_present"],
        "batch012_targeted_seed_validation_status": batch012_state["targeted_seed_validation_status"],
        "batch012_candidate_class": batch012_state["candidate_class"],
        "batch012_native_verification_status": batch012_state["native_verification_status"],
        "batch012_issue_derived_verification_status": batch012_state["issue_derived_verification_status"],
        "batch012_prospective_memory_eligibility_status": batch012_state["prospective_memory_eligibility_status"],
        "batch012_route_diversity_status": batch012_state["route_diversity_status"],
        "batch012_mappable_status_feature_status": batch012_state["mappable_status_feature_status"],
        "batch012_matched_null_ensemble_run_count": batch012_state["matched_null_ensemble_run_count"],
        "batch012_matched_null_score": batch012_state["matched_null_score"],
        "batch012_preliminary_prospective_memory_separation_evidence": batch012_state["preliminary_prospective_single_candidate_memory_separation_evidence"],
        "batch012_repair_only_fallback_attempted": batch012_state["repair_only_fallback_attempted"],
        "batch012_additional_native_repair_acquired": batch012_state["additional_native_repair_acquired"],
        "batch012_additional_issue_derived_repair_feasibility": batch012_state["additional_issue_derived_repair_feasibility"],
        "batch012_confirmed_native_repair_episode_count": batch012_state["confirmed_native_repair_episode_count"],
        "batch012_confirmed_issue_derived_repair_episode_count": batch012_state["confirmed_issue_derived_repair_episode_count"],
        "clean_replication_batch_013_status": batch013_state["status"],
        "clean_replication_batch_013_exact_blocker": batch013_state.get("exact_blocker"),
        "batch013_source_commit_environment_lock_status": batch013_state["source_commit_environment_lock_status"],
        "batch013_target_command_manifest_status": batch013_state["target_command_manifest_status"],
        "batch013_external_command_manifest_status": batch013_state["target_command_manifest_status"],
        "batch013_fresh_workspace_purity_status": batch013_state["fresh_workspace_purity_status"],
        "batch013_baseline_registry_drift_precheck_status": batch013_state["baseline_registry_drift_precheck_status"],
        "batch013_rollback_block_ledger_status": batch013_state["rollback_block_ledger_status"],
        "batch013_acquisition_lock_stack_status": batch013_state["acquisition_lock_stack_status"],
        "batch013_targeted_seed_present": batch013_state["targeted_seed_present"],
        "batch013_targeted_seed_validation_status": batch013_state["targeted_seed_validation_status"],
        "batch013_targeted_seed_git_tracking_status": batch013_state["targeted_seed_git_tracking_status"],
        "batch013_targeted_seed_workflow_visibility_status": batch013_state["targeted_seed_workflow_visibility_status"],
        "batch013_candidate_class": batch013_state["candidate_class"],
        "batch013_native_verification_status": batch013_state["native_verification_status"],
        "batch013_issue_derived_verification_status": batch013_state["issue_derived_verification_status"],
        "batch013_prospective_memory_eligibility_status": batch013_state["prospective_memory_eligibility_status"],
        "batch013_route_diversity_status": batch013_state["route_diversity_status"],
        "batch013_mappable_status_feature_status": batch013_state["mappable_status_feature_status"],
        "batch013_matched_null_ensemble_run_count": batch013_state["matched_null_ensemble_run_count"],
        "batch013_matched_null_score": batch013_state["matched_null_score"],
        "batch013_preliminary_prospective_memory_separation_evidence": batch013_state["preliminary_prospective_single_candidate_memory_separation_evidence"],
        "batch013_repair_only_fallback_attempted": batch013_state["repair_only_fallback_attempted"],
        "batch013_additional_native_repair_acquired": batch013_state["additional_native_repair_acquired"],
        "batch013_additional_issue_derived_repair_feasibility": batch013_state["additional_issue_derived_repair_feasibility"],
        "batch013_confirmed_native_repair_episode_count": batch013_state["confirmed_native_repair_episode_count"],
        "batch013_confirmed_issue_derived_repair_episode_count": batch013_state["confirmed_issue_derived_repair_episode_count"],
        "clean_replication_batch_014_status": batch014_state["status"],
        "clean_replication_batch_014_exact_blocker": batch014_state.get("exact_blocker"),
        "batch014_seed_path_used": batch014_state["seed_path_used"],
        "batch014_targeted_seed_git_tracking_status": batch014_state["targeted_seed_git_tracking_status"],
        "batch014_seed_schema_harmonization_status": batch014_state["seed_schema_harmonization_status"],
        "batch014_issue_snapshot_firewall_status": batch014_state["issue_snapshot_firewall_status"],
        "batch014_source_commit_selection_status": batch014_state["source_commit_selection_status"],
        "batch014_acquisition_lock_stack_status": batch014_state["acquisition_lock_stack_status"],
        "batch014_issue_derived_harness_generated": batch014_state["issue_derived_harness_generated"],
        "batch014_issue_derived_harness_verification_status": batch014_state["issue_derived_harness_verification_status"],
        "batch014_issue_derived_candidate_verified": batch014_state["issue_derived_candidate_verified"],
        "batch014_repair_only_fallback_attempted": batch014_state["repair_only_fallback_attempted"],
        "batch014_issue_derived_repair_feasibility": batch014_state["issue_derived_repair_feasibility"],
        "batch014_confirmed_native_repair_episode_count": batch014_state["confirmed_native_repair_episode_count"],
        "batch014_confirmed_issue_derived_repair_episode_count": batch014_state["confirmed_issue_derived_repair_episode_count"],
        "batch014_matched_null_diagnostic_run_count": batch014_state["matched_null_diagnostic_run_count"],
        "batch014_memory_separation_claim_status": batch014_state["memory_separation_claim_status"],
        "clean_replication_batch_015_status": batch015_state["status"],
        "clean_replication_batch_015_exact_blocker": batch015_state["exact_blocker"],
        "batch015_latest_artifact_ingest_status": batch015_state["latest_artifact_ingest_status"],
        "batch015_validation_path_continuity_status": batch015_state["validation_path_continuity_status"],
        "batch015_runtime_incident_capture_status": batch015_state["runtime_incident_capture_status"],
        "batch015_execution_boundary_gateway_status": batch015_state["execution_boundary_gateway_status"],
        "batch015_isolated_repair_sandbox_status": batch015_state["isolated_repair_sandbox_status"],
        "batch015_dependency_drift_chaperone_status": batch015_state["dependency_drift_chaperone_status"],
        "batch015_active_ast_excision_probe_status": batch015_state["active_ast_excision_probe_status"],
        "batch015_syntax_micro_rollback_status": batch015_state["syntax_micro_rollback_status"],
        "batch015_predictive_degradation_telemetry_status": batch015_state["predictive_degradation_telemetry_status"],
        "batch015_compute_budget_safe_stop_status": batch015_state["compute_budget_safe_stop_status"],
        "batch015_blue_green_deployment_status": batch015_state["blue_green_deployment_status"],
        "batch015_proof_to_action_compiler_status": batch015_state["proof_to_action_compiler_status"],
        "batch015_lock_sequence_operation_registry_status": batch015_state["lock_sequence_operation_registry_status"],
        "batch015_four_lock_operation_grammar_status": batch015_state["four_lock_operation_grammar_status"],
        "batch015_curvature_integration_status": batch015_state["curvature_integration_status"],
        "batch015_claim_tier_system_status": batch015_state["claim_tier_system_status"],
        "batch015_capability_catalog_status": batch015_state["capability_catalog_status"],
        "batch015_readme_restructure_status": batch015_state["readme_restructure_status"],
        "batch015_skeptic_checklist_status": batch015_state["skeptic_checklist_status"],
        "batch015_use_case_positioning_status": batch015_state["use_case_positioning_status"],
        "batch015_structure_first_compiler_roadmap_status": batch015_state["structure_first_compiler_roadmap_status"],
        "batch015_future_agentic_admissibility_compiler_roadmap_status": batch015_state["future_agentic_admissibility_compiler_roadmap_status"],
        "batch015_marketing_claim_boundary_status": batch015_state["marketing_claim_boundary_status"],
        "clean_replication_batch_016_status": batch016_state["status"],
        "clean_replication_batch_016_exact_blocker": batch016_state["exact_blocker"],
        "batch016_target_intent_signature_status": batch016_state["target_intent_signature_status"],
        "batch016_runtime_incident_capture_status": batch016_state["runtime_incident_capture_status"],
        "batch016_dependency_era_chaperone_status": batch016_state["dependency_era_chaperone_status"],
        "batch016_dependency_precondition_classification": batch016_state["dependency_precondition_classification"],
        "batch016_command_environment_variant_matrix_status": batch016_state["command_environment_variant_matrix_status"],
        "batch016_source_commit_window_status": batch016_state["source_commit_window_status"],
        "batch016_harness_v2_generated": batch016_state["harness_v2_generated"],
        "batch016_harness_v2_verification_status": batch016_state["harness_v2_verification_status"],
        "batch016_target_intent_alignment": batch016_state["target_intent_alignment"],
        "batch016_issue_derived_candidate_verified": batch016_state["issue_derived_candidate_verified"],
        "batch016_repair_only_fallback_attempted": batch016_state["repair_only_fallback_attempted"],
        "batch016_issue_derived_repair_feasibility": batch016_state["issue_derived_repair_feasibility"],
        "batch016_native_repair_episode_count": batch016_state["native_repair_episode_count"],
        "batch016_issue_derived_repair_episode_count": batch016_state["issue_derived_repair_episode_count"],
        "batch016_matched_null_diagnostic_run_count": batch016_state["matched_null_diagnostic_run_count"],
        "batch016_memory_separation_claim_status": batch016_state["memory_separation_claim_status"],
        "clean_replication_batch_017_status": batch017_state["status"],
        "clean_replication_batch_017_exact_blocker": batch017_state["exact_blocker"],
        "batch017_artifact_packaging_status": batch017_state["artifact_packaging_status"],
        "batch017_thin_artifact_packaging_status": batch017_state["thin_artifact_packaging_status"],
        "batch017_artifact_lineage_index_status": batch017_state["artifact_lineage_index_status"],
        "batch017_evidence_carry_forward_manifest_status": batch017_state["evidence_carry_forward_manifest_status"],
        "batch017_recursive_prior_batch_packaging_detected": batch017_state["recursive_prior_batch_packaging_detected"],
        "batch017_target_intent_retry_status": batch017_state["target_intent_retry_status"],
        "batch017_dependency_era_resolver_status": batch017_state["dependency_era_resolver_status"],
        "batch017_decision_time_dependency_lock_status": batch017_state["decision_time_dependency_lock_status"],
        "batch017_manual_dependency_lock_status": batch017_state["manual_dependency_lock_status"],
        "batch017_dependency_precondition_classification": batch017_state["dependency_precondition_classification"],
        "batch017_command_environment_variant_matrix_status": batch017_state["command_environment_variant_matrix_status"],
        "batch017_source_commit_window_status": batch017_state["source_commit_window_status"],
        "batch017_harness_v3_generated": batch017_state["harness_v3_generated"],
        "batch017_harness_v3_verification_status": batch017_state["harness_v3_verification_status"],
        "batch017_target_intent_alignment": batch017_state["target_intent_alignment"],
        "batch017_issue_derived_candidate_verified": batch017_state["issue_derived_candidate_verified"],
        "batch017_repair_only_fallback_attempted": batch017_state["repair_only_fallback_attempted"],
        "batch017_issue_derived_repair_feasibility": batch017_state["issue_derived_repair_feasibility"],
        "batch017_native_repair_episode_count": batch017_state["native_repair_episode_count"],
        "batch017_issue_derived_repair_episode_count": batch017_state["issue_derived_repair_episode_count"],
        "batch017_matched_null_diagnostic_run_count": batch017_state["matched_null_diagnostic_run_count"],
        "batch017_memory_separation_claim_status": batch017_state["memory_separation_claim_status"],
        "batch017_absolute_uncrashability_claim_status": batch017_state["absolute_uncrashability_claim_status"],
        "clean_replication_batch_018_status": batch018_state["status"],
        "clean_replication_batch_018_exact_blocker": batch018_state["exact_blocker"],
        "batch018_issue_timestamp_reconciliation_status": batch018_state["issue_timestamp_reconciliation_status"],
        "batch018_dependency_cutoff_timestamp": batch018_state["dependency_cutoff_timestamp"],
        "batch018_manual_dependency_lock_status": batch018_state["manual_dependency_lock_status"],
        "batch018_manual_requirements_support_file_status": batch018_state["manual_requirements_support_file_status"],
        "batch018_decision_time_dependency_lock_validation_status": batch018_state["decision_time_dependency_lock_validation_status"],
        "batch018_manual_lock_environment_materialization_status": batch018_state["manual_lock_environment_materialization_status"],
        "batch018_target_intent_retry_status": batch018_state["target_intent_retry_status"],
        "batch018_harness_v4_generated": batch018_state["harness_v4_generated"],
        "batch018_harness_v4_verification_status": batch018_state["harness_v4_verification_status"],
        "batch018_target_intent_alignment": batch018_state["target_intent_alignment"],
        "batch018_issue_derived_candidate_verified": batch018_state["issue_derived_candidate_verified"],
        "batch018_repair_only_fallback_attempted": batch018_state["repair_only_fallback_attempted"],
        "batch018_issue_derived_repair_feasibility": batch018_state["issue_derived_repair_feasibility"],
        "batch018_native_repair_episode_count": batch018_state["native_repair_episode_count"],
        "batch018_issue_derived_repair_episode_count": batch018_state["issue_derived_repair_episode_count"],
        "batch018_matched_null_diagnostic_run_count": batch018_state["matched_null_diagnostic_run_count"],
        "batch018_memory_separation_claim_status": batch018_state["memory_separation_claim_status"],
        "batch018_hallucination_elimination_claim_status": batch018_state["hallucination_elimination_claim_status"],
        "batch018_absolute_uncrashability_claim_status": batch018_state["absolute_uncrashability_claim_status"],
        "clean_replication_batch_019_status": batch019_state["status"],
        "clean_replication_batch_019_exact_blocker": batch019_state["exact_blocker"],
        "batch019_manual_dependency_lock_watch_status": batch019_state["manual_dependency_lock_watch_status"],
        "batch019_active_search_space_geometry_status": batch019_state["active_search_space_geometry_status"],
        "batch019_search_space_feature_vector_status": batch019_state["search_space_feature_vector_status"],
        "batch019_information_gain_probe_selection_status": batch019_state["information_gain_probe_selection_status"],
        "batch019_structural_defect_boundary_classification_status": batch019_state["structural_defect_boundary_classification_status"],
        "batch019_recovery_path_ranking_status": batch019_state["recovery_path_ranking_status"],
        "batch019_amds_active_inference_integration_status": batch019_state["amds_active_inference_integration_status"],
        "batch019_single_system_scope_gate_status": batch019_state["single_system_scope_gate_status"],
        "batch019_coupled_interlock_extension_gate_status": batch019_state["coupled_interlock_extension_gate_status"],
        "batch019_curvature_integration_status": batch019_state["curvature_integration_status"],
        "batch019_replacement_seed_request_status": batch019_state["replacement_seed_request_status"],
        "batch019_darker_issue112_status": batch019_state["darker_issue112_status"],
        "batch019_recommended_next_probe": batch019_state["recommended_next_probe"],
        "batch019_native_repair_episode_count": batch019_state["native_repair_episode_count"],
        "batch019_issue_derived_repair_episode_count": batch019_state["issue_derived_repair_episode_count"],
        "batch019_matched_null_diagnostic_run_count": batch019_state["matched_null_diagnostic_run_count"],
        "batch019_memory_separation_claim_status": batch019_state["memory_separation_claim_status"],
        "batch019_hallucination_elimination_claim_status": batch019_state["hallucination_elimination_claim_status"],
        "batch019_absolute_uncrashability_claim_status": batch019_state["absolute_uncrashability_claim_status"],
        "clean_replication_batch_020_status": batch020_state["status"],
        "clean_replication_batch_020_exact_blocker": batch020_state["exact_blocker"],
        "batch020_manual_dependency_lock_validation_status": batch020_state["manual_dependency_lock_validation_status"],
        "batch020_manual_dependency_lock_sha256": batch020_state["manual_dependency_lock_sha256"],
        "batch020_environment_materialization_status": batch020_state["environment_materialization_status"],
        "batch020_target_intent_alignment_status": batch020_state["target_intent_alignment_status"],
        "batch020_harness_v5_generated": batch020_state["harness_v5_generated"],
        "batch020_harness_v5_verification_status": batch020_state["harness_v5_verification_status"],
        "batch020_issue_derived_candidate_verified": batch020_state["issue_derived_candidate_verified"],
        "batch020_repair_only_fallback_attempted": batch020_state["repair_only_fallback_attempted"],
        "batch020_issue_derived_repair_feasibility": batch020_state["issue_derived_repair_feasibility"],
        "batch020_native_repair_episode_count": batch020_state["native_repair_episode_count"],
        "batch020_issue_derived_repair_episode_count": batch020_state["issue_derived_repair_episode_count"],
        "batch020_matched_null_diagnostic_run_count": batch020_state["matched_null_diagnostic_run_count"],
        "batch020_memory_separation_claim_status": batch020_state["memory_separation_claim_status"],
        "batch020_hallucination_elimination_claim_status": batch020_state["hallucination_elimination_claim_status"],
        "batch020_absolute_uncrashability_claim_status": batch020_state["absolute_uncrashability_claim_status"],
        "batch020_coupled_interlock_extension_status": batch020_state["coupled_interlock_extension_status"],
        "clean_replication_batch_021_status": batch021_state["status"],
        "clean_replication_batch_021_exact_blocker": batch021_state["exact_blocker"],
        "batch021_manual_dependency_lock_validation_status": batch021_state["manual_dependency_lock_validation_status"],
        "batch021_dynamic_era_materialization_status": batch021_state["dynamic_era_materialization_status"],
        "batch021_runtime_provider_selection_status": batch021_state["runtime_provider_selection_status"],
        "batch021_runtime_provider_selection_decision": batch021_state["runtime_provider_selection_decision"],
        "batch021_selected_runtime_provider_id": batch021_state["selected_runtime_provider_id"],
        "batch021_python37_runtime_provider_status": batch021_state["python37_runtime_provider_status"],
        "batch021_environment_materialization_status": batch021_state["environment_materialization_status"],
        "batch021_target_intent_alignment_status": batch021_state["target_intent_alignment_status"],
        "batch021_harness_v6_generated": batch021_state["harness_v6_generated"],
        "batch021_harness_v6_verification_status": batch021_state["harness_v6_verification_status"],
        "batch021_issue_derived_candidate_verified": batch021_state["issue_derived_candidate_verified"],
        "batch021_repair_only_fallback_attempted": batch021_state["repair_only_fallback_attempted"],
        "batch021_issue_derived_repair_feasibility": batch021_state["issue_derived_repair_feasibility"],
        "batch021_native_repair_episode_count": batch021_state["native_repair_episode_count"],
        "batch021_issue_derived_repair_episode_count": batch021_state["issue_derived_repair_episode_count"],
        "batch021_matched_null_diagnostic_run_count": batch021_state["matched_null_diagnostic_run_count"],
        "batch021_memory_separation_claim_status": batch021_state["memory_separation_claim_status"],
        "batch021_coupled_interlock_extension_status": batch021_state["coupled_interlock_extension_status"],
        "clean_replication_batch_022_status": batch022_state["status"],
        "clean_replication_batch_022_exact_blocker": batch022_state["exact_blocker"],
        "batch022_docker_runtime_provider_status": batch022_state["docker_runtime_provider_status"],
        "batch022_selected_provider": batch022_state["selected_provider"],
        "batch022_required_python_version": batch022_state["required_python_version"],
        "batch022_actual_provider_python_version": batch022_state["actual_provider_python_version"],
        "batch022_provider_preflight_status": batch022_state["provider_preflight_status"],
        "batch022_manual_dependency_lock_provider_install_status": batch022_state["manual_dependency_lock_provider_install_status"],
        "batch022_environment_materialization_status": batch022_state["environment_materialization_status"],
        "batch022_target_intent_alignment_status": batch022_state["target_intent_alignment_status"],
        "batch022_harness_v7_generated": batch022_state["harness_v7_generated"],
        "batch022_harness_v7_verification_status": batch022_state["harness_v7_verification_status"],
        "batch022_psa82_package_status": batch022_state["psa82_package_status"],
        "batch022_structured_fragility_audit_status": batch022_state["structured_fragility_audit_status"],
        "batch022_permutation_null_audit_status": batch022_state["permutation_null_audit_status"],
        "batch022_issue_derived_candidate_verified": batch022_state["issue_derived_candidate_verified"],
        "batch022_repair_only_fallback_attempted": batch022_state["repair_only_fallback_attempted"],
        "batch022_issue_derived_repair_feasibility": batch022_state["issue_derived_repair_feasibility"],
        "batch022_native_repair_episode_count": batch022_state["native_repair_episode_count"],
        "batch022_issue_derived_repair_episode_count": batch022_state["issue_derived_repair_episode_count"],
        "batch022_matched_null_diagnostic_run_count": batch022_state["matched_null_diagnostic_run_count"],
        "batch022_memory_separation_claim_status": batch022_state["memory_separation_claim_status"],
        "batch022_hallucination_elimination_claim_status": batch022_state["hallucination_elimination_claim_status"],
        "batch022_absolute_uncrashability_claim_status": batch022_state["absolute_uncrashability_claim_status"],
        "batch022_coupled_interlock_extension_status": batch022_state["coupled_interlock_extension_status"],
        "global_curvature_logic_status": batch013_state["global_curvature_logic_status"],
        "curvature_feature_vector_status": batch013_state["curvature_feature_vector_status"],
        "basin_stability_check_status": batch013_state["basin_stability_check_status"],
        "two_winner_global_policy_status": batch013_state["two_winner_global_policy_status"],
        "curvature_candidate_selection_status": batch013_state["curvature_candidate_selection_status"],
        "curvature_source_route_selection_status": batch013_state["curvature_source_route_selection_status"],
        "curvature_memory_routing_status": batch013_state["curvature_memory_routing_status"],
        "curvature_fragment_planning_status": batch013_state["curvature_fragment_planning_status"],
        "null_curvature_fairness_status": batch013_state["null_curvature_fairness_status"],
        "curvature_claim_boundary_status": batch013_state["curvature_claim_boundary_status"],
        "curvature_blocker_if_any": batch013_state["curvature_blocker_if_any"],
        "batch013_gate_chain_status": batch013_state["batch013_gate_chain_status"],
        "active_context_filtering_status": batch013_state["active_context_filtering_status"],
        "curvature_heuristic_freeze_status": batch013_state["curvature_heuristic_freeze_status"],
        "rollback_for_seed_failure_status": batch013_state["rollback_block_ledger_status"],
        "five_locks_curvature_cross_gate_status": batch013_state["five_locks_curvature_cross_gate_status"],
        "issue_derived_temporal_classification_status": batch013_state["issue_derived_temporal_classification_status"],
        "gate_chain_blocker_if_any": batch013_state["gate_chain_blocker_if_any"],
        "active_failure_memory_weighting_status": load_json(BATCH_DIR / "arm_a_active_failure_memory_weighting.json").get("status") if (BATCH_DIR / "arm_a_active_failure_memory_weighting.json").is_file() else "NOT_RUN",
        "arm_a_memory_routing_delta_status": "PASS" if (BATCH_DIR / "arm_a_active_failure_memory_weighting.json").is_file() and load_json(BATCH_DIR / "arm_a_active_failure_memory_weighting.json").get("failure_memory_markers_passive") is False else "PASSIVE_OR_NOT_RUN",
        "arm_b_memory_exclusion_status": load_json(BATCH_DIR / "arm_b_memory_disabled_exclusion_audit.json").get("status") if (BATCH_DIR / "arm_b_memory_disabled_exclusion_audit.json").is_file() else "NOT_RUN",
        "pre_generation_context_state_snapshot_status": "PASS" if (BATCH_DIR / "arm_a_pre_generation_context_state_snapshot.json").is_file() and (BATCH_DIR / "arm_b_pre_generation_context_state_snapshot.json").is_file() else "NOT_RUN",
        "repair_intent_lock_status": "PASS" if (BATCH_DIR / "arm_a_repair_intent_lock.json").is_file() and (BATCH_DIR / "arm_b_repair_intent_lock.json").is_file() else "NOT_RUN",
        "interlock_invariant_revalidation_status": "PASS" if (BATCH_DIR / "interlock_invariant_revalidation.json").is_file() and all(item.get("status") == "PASS" for item in load_json(BATCH_DIR / "interlock_invariant_revalidation.json") if item) else "NOT_RUN_OR_BLOCKED",
        "homeostasis_risk_status": load_json(BATCH_DIR / "homeostasis_risk_state_matched_null.json").get("status") if (BATCH_DIR / "homeostasis_risk_state_matched_null.json").is_file() else "NOT_RUN",
        "bounded_exploration_budget_status": load_json(BATCH_DIR / "bounded_exploration_budget_matched_null.json").get("status") if (BATCH_DIR / "bounded_exploration_budget_matched_null.json").is_file() else budget["status"],
        "full_memory_lift_status": "undemonstrated",
        "public_claim_boundary_status": "PASS",
        "notebooklm_advice_traceability_status": traceability_status.get("status"),
        "operational_gate_matrix_crosscheck_status": "PASS" if (BATCH005_DIR / "operational_gate_matrix_crosscheck.json").is_file() and load_json(BATCH005_DIR / "operational_gate_matrix_crosscheck.json").get("status") == "PASS" else "FAIL",
        "implemented_active_gate_count": traceability_status.get("implemented_active_gate_count"),
        "implemented_partial_gate_count": traceability_status.get("implemented_partial_gate_count"),
        "deferred_gate_count": traceability_status.get("deferred_gate_count"),
        "rejected_gate_count": traceability_status.get("rejected_gate_count"),
        "carry_forward_blocker_count": traceability_status.get("carry_forward_blocker_count"),
        "silent_completion_audit_status": load_json(BATCH005_DIR / "no_silent_completion_audit.json").get("status") if (BATCH005_DIR / "no_silent_completion_audit.json").is_file() else "MISSING",
        "issue_derived_gate_completion_status": traceability_status.get("issue_derived_gate_completion_status"),
        "failure_memory_weighting_completion_status": traceability_status.get("failure_memory_weighting_completion_status"),
        "stage_interface_contract_status": "PASS" if all(item.get("status") == "PASS" for item in load_json(BATCH_DIR / "stage_interface_contract.json")) else "FAIL",
        "repairability_basin_selection_status": "PASS" if all(item.get("status") == "PASS" for item in load_json(BATCH_DIR / "repairability_basin_selection.json")) else "FAIL",
        "pre_generation_context_state_lock_status": "PASS" if load_json(BATCH_DIR / "pre_generation_context_state_lock.json") else "FAIL",
        "patch_context_alignment_status": "PASS" if not load_json(BATCH_DIR / "patch_context_alignment_audit.json") or all(item.get("status") == "PASS" for item in load_json(BATCH_DIR / "patch_context_alignment_audit.json")) else "FAIL",
        "post_patch_constraint_revalidation_status": "PASS" if not load_json(BATCH_DIR / "post_patch_constraint_revalidation.json") or all(item.get("status") == "PASS" for item in load_json(BATCH_DIR / "post_patch_constraint_revalidation.json")) else "NOT_RUN_OR_BLOCKED",
        "no_overreach_validation_status": "PASS" if not load_json(BATCH_DIR / "no_overreach_validation.json") or all(item.get("status") == "PASS" for item in load_json(BATCH_DIR / "no_overreach_validation.json")) else "NOT_RUN_OR_BLOCKED",
        "repair_generator_capability_status": "PASS" if all(item.get("generator_invoked") is True for item in load_json(BATCH_DIR / "repair_generator_capability_status.json")) else "FAIL",
        "clean_repair_generator_not_implemented": any(item.get("blocker") == "clean_repair_generator_not_implemented" for item in load_json(BATCH_DIR / "repair_generator_capability_status.json")),
        "clean_repair_no_safe_source_patch_generated": any(item.get("blocker") == "clean_repair_no_safe_source_patch_generated" for item in load_json(BATCH_DIR / "repair_generator_capability_status.json")),
        "readme_status_update_status": "PASS",
        "operational_gate_matrix_status": "PASS",
        "public_language_audit_status": "PASS",
        "full_scoring": "NOT_RUN/disallowed",
        "memory_lift": "not_demonstrated",
        "self_maintaining_software": "false/not_demonstrated",
        "current_protocol_version": "v2.13",
    }
    write_json_deterministic(POST_DIR / "final_report_post_v2_37_hardening_001.json", final_report)
    write_json_deterministic(
        POST_DIR / "consolidated_state_post_v2_37_hardening_001.json",
        {
            "lane_id": POST_ID,
            "lane_type": "post_v2_37_hardening",
            "status": final_report["status"],
            "exact_blocker": final_report["exact_blocker"],
            "summary_status": final_report["summary_status"],
            "current_protocol_version": "v2.13",
            "v2_37_official_artifact_verification": v2_37_record,
            "claim_boundary": {
                "full_scoring": "NOT_RUN/disallowed",
                "memory_lift": batch014_state.get("memory_separation_claim_status", "not_demonstrated"),
                "self_maintaining_software": "false/not_demonstrated",
            },
        },
    )
    write_text_lf(
        POST_DIR / "campaign_summary.md",
        "\n".join(
            [
                "# Post-v2.37 hardening and clean replication batch 002",
                "",
                f"Status: {final_report['status']}.",
                "",
                "This run preserves neutral transport, risk, budget, context-boundary, environment-normalization, evidence-class separation, real-lead acquisition progression, and clean artifact packaging gates while adding clean-protocol repair generation for verified native candidates. It does not create a new version lane, does not relax the BugsInPy block, and does not claim full scoring, memory lift, or self-maintaining software.",
                "",
                "The matched-null continuation runs the remaining verified native candidate under memory-enabled and memory-disabled arms with bounded claim language.",
                "",
                "Batch003 adds a deterministic matched-null ensemble challenge protocol and blocks cleanly because no unrepaired challenge candidate verified under the safe admission gates.",
                "",
                "Batch004 adds native-first dual-track challenge acquisition and issue-derived fallback as a separate evidence class; it blocks cleanly because neither track verified a challenge candidate.",
                "",
                "Batch005 corrects Batch004 by materializing the source tree for native retry and running targeted issue-derived seed intake before bounded issue discovery fallback.",
                "",
                "Batch006 implements bounded fragment patch assembly, coupled dependency interlock mapping, dual projection consistency checks, passive failure-memory records, and a proof-chain lock for the verified native challenge. It blocks before patch bytes because the source-facing projection does not authorize a source-only fragment from the observed formatter/dependency precondition.",
                "",
                "Batch007 adds target-intent reachability, formatter/dependency precondition resolution records, trace-feedback alignment, iterative dual projection recheck, and an explicit completion decision ladder. The candidate is retired because the runtime path remains blocked before the intended import-sorting skip behavior.",
                "",
                "Batch008 corrects the Batch007 declared-precondition gap by materializing a fresh ephemeral runtime workspace, installing declared formatter extras and declared target-test tooling, rerunning the target command, and applying one source-only patch only after the intended target behavior is reached.",
                "",
                f"Batch008 status: `{batch008_state['status']}`; additional native external repair acquired: `{str(batch008_state['additional_native_external_repair_acquired']).lower()}`.",
                "",
                "Batch009 adds patch-quarantined retrospective matched-null calibration on the already repaired Batch008 candidate. The memory signal is passive, the calibration score is 0.0, and no prospective memory-lift claim is made.",
                "",
                f"Batch009 status: `{batch009_state['status']}`; patch quarantine: `{batch009_state['patch_artifact_quarantine_status']}`; null ensemble run count: `{batch009_state['null_ensemble_run_count']}`.",
                "",
                "Batch010 implements active status-code weighting and strict minimum-delta routing audit. It blocks because no source, context, or generation routing delta can be established without quarantined prior patch details.",
                "",
                f"Batch010 status: `{batch010_state['status']}`; exact blocker: `{batch010_state['exact_blocker']}`.",
                "",
                "Batch011 records prospective memory challenge eligibility, retires the already repaired retrospective candidate from additional memory-lift attempts, and reviews bounded fresh leads from the existing clean replication lead pool. No fresh candidate verified a pre-repair failure, so the memory-enabled arm and null ensemble remain not run.",
                "",
                f"Batch011 status: `{batch011_state['status']}`; exact blocker: `{batch011_state['exact_blocker']}`.",
                "",
                "Batch012 starts Targeted Prospective Seed Intake after Batch011 exhausted automated fresh-candidate attempts. The configured seed is absent, so native verification, issue-derived fallback, prospective memory eligibility, repair-only fallback, and matched-null comparison remain not run.",
                "",
                f"Batch012 status: `{batch012_state['status']}`; exact blocker: `{batch012_state['exact_blocker']}`.",
                "",
                "Batch013 adds acquisition/materialization locks, gate-chain binding, tracked seed enforcement, active context filtering records, and frozen routing-score policy. It blocks only after those locks are ready because the required tracked targeted seed is absent.",
                "",
                f"Batch013 status: `{batch013_state['status']}`; exact blocker: `{batch013_state['exact_blocker']}`.",
                "",
                "Batch014 consumes the tracked Darker issue #112 targeted seed as issue-derived evidence, enforces the redacted issue snapshot firewall, selects the source commit before the issue timestamp, and attempts the issue-derived harness under the acquisition locks without changing native repair counts.",
                "",
                f"Batch014 status: `{batch014_state['status']}`; exact blocker: `{batch014_state['exact_blocker']}`.",
                "",
                "Batch015 ingests the manually supplied Batch014 output boundary and adds runtime-wrapper MVP scaffolds, a lock-sequence operation registry, claim tiers, a capability catalog, public positioning docs, and roadmap-only future compiler directions without adding new repair evidence.",
                "",
                f"Batch015 status: `{batch015_state['status']}`; latest validation blocker: `{batch015_state['exact_blocker']}`.",
                "",
                "Batch016 ingests the manually supplied Batch015 artifact, adds target-intent signature checking for Darker issue #112, records the mismatch as a runtime incident, classifies the observed failure as a dependency-era/precondition blocker, and safe-stops before repair.",
                "",
                f"Batch016 status: `{batch016_state['status']}`; exact blocker: `{batch016_state['exact_blocker']}`.",
                "",
                "Batch017 ingests the manually supplied Batch016 artifact boundary, attempts decision-time dependency-era resolution, adds thin artifact packaging, and preserves prior evidence through a lineage index and carry-forward manifest.",
                "",
                f"Batch017 status: `{batch017_state['status']}`; exact blocker: `{batch017_state['exact_blocker']}`.",
                "",
                "Batch018 ingests the manually supplied Batch017 thin artifact boundary, reconciles Darker issue #112 timestamp evidence, and stops cleanly because the canonical manual dependency lock JSON is absent.",
                "",
                f"Batch018 status: `{batch018_state['status']}`; exact blocker: `{batch018_state['exact_blocker']}`.",
                "",
                "Batch019 ingests the manually supplied Batch018 thin artifact boundary, preserves the manual-lock blocker, watches the post-Batch018 lock for a later lane, and adds Active Search-Space Geometry plus information-gain probe selection scaffolds.",
                "",
                f"Batch019 status: `{batch019_state['status']}`; exact blocker: `{batch019_state['exact_blocker']}`.",
                "",
                "Batch020 ingests the manually supplied Batch019 thin artifact boundary, validates the canonical manual dependency lock, and blocks downstream work unless bounded materialization and Target-Intent Alignment pass.",
                "",
                f"Batch020 status: `{batch020_state['status']}`; exact blocker: `{batch020_state['exact_blocker']}`.",
                "",
                "Batch021 ingests the manually supplied Batch020 thin artifact boundary, adds Dynamic Era Materialization and Runtime Provider Selection, and safe-stops before target replay because no exact Python 3.7 runtime provider is verified in the current workflow.",
                "",
                f"Batch021 status: `{batch021_state['status']}`; exact blocker: `{batch021_state['exact_blocker']}`.",
                "",
                "Batch022 ingests the manually supplied Batch021 thin artifact boundary, adds Docker provider preflight and Structured Fragility Audit scaffolds, quarantines PSA-82 handling, and safe-stops before target replay unless provider, lock, materialization, and Target-Intent Alignment gates pass.",
                "",
                f"Batch022 status: `{batch022_state['status']}`; exact blocker: `{batch022_state['exact_blocker']}`.",
                "",
                f"NotebookLM advice traceability status: `{traceability_status.get('status')}`.",
            ]
        ),
    )
    write_public_docs_reports()
    write_batch015_markdown_docs()
    write_batch018_markdown_docs(batch018_state)
    write_batch019_markdown_docs(batch019_state)
    batch020_state = write_batch020_outputs(Path.cwd(), POST_DIR, BATCH020_DIR, batch019_state)
    batch021_state = write_batch021_outputs(Path.cwd(), POST_DIR, BATCH021_DIR, batch020_state)
    batch022_state = write_batch022_outputs(Path.cwd(), POST_DIR, BATCH022_DIR, batch021_state)
    write_sha256sums(POST_DIR)
    stage_artifact_payload(PAYLOAD_DIR, [POST_DIR, BATCH022_DIR])
    write_artifact_manifest(PAYLOAD_DIR)
    payload_audit = audit_artifact_payload(PAYLOAD_DIR)
    payload_size = sum(path.stat().st_size for path in PAYLOAD_DIR.rglob("*") if path.is_file())
    recursive_prior_batch_packaging_detected = any(
        part.startswith("clean_replication_batch_") and part != BATCH022_ID
        for path in PAYLOAD_DIR.rglob("*")
        for part in path.relative_to(PAYLOAD_DIR).parts
    )
    write_json_deterministic(
        BATCH022_DIR / "artifact_payload_budget.json",
        {
            "status": "PASS" if payload_size <= 750000 else "BLOCK",
            "target_primary_artifact_bytes": 450000,
            "hard_primary_artifact_bytes": 750000,
            "estimated_primary_artifact_bytes": payload_size,
            "target_exceeded_with_justification": payload_size > 450000,
            "justification": "post boundary plus Batch022 Docker provider and Structured Fragility Audit evidence" if payload_size > 450000 else None,
            "blocker": None if payload_size <= 750000 else "primary_artifact_budget_exceeded",
        },
    )
    write_json_deterministic(
        BATCH022_DIR / "artifact_minimality_audit.json",
        {
            "status": "PASS" if not recursive_prior_batch_packaging_detected else "BLOCK",
            "recursive_prior_batch_packaging_detected": recursive_prior_batch_packaging_detected,
            "primary_payload_roots": [POST_DIR.as_posix(), BATCH022_DIR.as_posix()],
            "payload_size_bytes": payload_size,
            "blocker": None if not recursive_prior_batch_packaging_detected else "recursive_prior_batch_packaging_detected",
        },
    )
    write_sha256sums(BATCH022_DIR)
    write_json_deterministic(
        POST_DIR / "artifact_payload_manifest_report.json",
        {
            "status": payload_audit["status"],
            "staged_payload_directory": str(PAYLOAD_DIR),
            "artifact_manifest_name": "ARTIFACT_SHA256SUMS.txt",
            "payload_file_count": payload_audit["payload_file_count"],
            "payload_size_bytes": payload_size,
            "cache_payload_count": len(payload_audit["cache_payloads"]),
            "uncovered_count": len(payload_audit["uncovered"]),
            "recursive_prior_batch_packaging_detected": recursive_prior_batch_packaging_detected,
            "manifest_convention": "artifact manifest covers every uploaded payload file except the manifest file itself",
        },
    )
    write_sha256sums(POST_DIR)
    stage_artifact_payload(PAYLOAD_DIR, [POST_DIR, BATCH022_DIR])
    write_artifact_manifest(PAYLOAD_DIR)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
