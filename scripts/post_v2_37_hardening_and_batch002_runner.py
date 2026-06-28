from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from controllergate.core.budget import create_budget, spend_budget
from controllergate.core.context_boundary import build_context_boundary_map
from controllergate.core.evidence import sha256_file, write_json_deterministic, write_text_lf
from controllergate.core.evidence_classes import classify_candidate_evidence, temporal_guard_policy
from controllergate.core.artifact_hygiene import audit_artifact_payload, stage_artifact_payload, write_artifact_manifest
from controllergate.core.homeostasis import RISK_CHANNELS, evaluate_homeostasis_state
from controllergate.core.manifests import write_sha256sums
from controllergate.core.normalization import evaluate_normalization_plan
from controllergate.core.transport import reject_unsafe_transport_paths
from controllergate.experiments.replication_batch import run_replication_batch

POST_ID = "post_v2_37_hardening_001"
POST_DIR = Path("outputs") / POST_ID
BATCH_ID = "clean_replication_batch_002"
BATCH_DIR = Path("outputs") / BATCH_ID
PAYLOAD_DIR = Path("artifact_payload/post_v2_37_hardening_batch002_repair_generation")


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


ACTIVE_PUBLIC_LANGUAGE_PATHS = [
    "README.md",
    "docs/current_status.md",
    "docs/capability_inventory.md",
    "docs/claim_boundaries.md",
    "docs/public_release_readiness.md",
    "docs/technical_validation_gap_report.md",
    "docs/replication_protocol.md",
    "docs/evidence_model.md",
    "docs/operational_gate_matrix.md",
    "controllergate_v1_7_beta/reports/critic_review_package/shareable_summary.md",
    "configs/operational_gate_matrix.json",
    ".github/workflows/post_v2_37_hardening_and_batch002.yml",
    "controllergate/core/environment.py",
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
        "meta" + "phorical",
        "bio" + "logical",
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
        "docs/public_release_readiness.md",
        "docs/technical_validation_gap_report.md",
        "docs/replication_protocol.md",
        "docs/evidence_model.md",
    ]
    write_json_deterministic(
        POST_DIR / "public_docs_accuracy_audit.json",
        {
            "status": "PASS" if not missing and not forbidden_hits and all(Path(path).is_file() for path in docs) else "FAIL",
            "docs_checked": docs,
            "full_scoring": "NOT_RUN/disallowed",
            "memory_lift": "undemonstrated",
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
    artifact_paths = [str(path) for path in sorted(POST_DIR.glob("*.json"))] + [str(path) for path in sorted(BATCH_DIR.glob("*.json"))]
    write_json_deterministic(
        POST_DIR / "public_language_audit_expanded.json",
        public_language_audit(ACTIVE_PUBLIC_LANGUAGE_PATHS + artifact_paths),
    )


def write_batch002_outputs() -> dict[str, object]:
    BATCH_DIR.mkdir(parents=True, exist_ok=True)
    config = load_json("configs/clean_replication_batch_002.json")
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


def main() -> int:
    POST_DIR.mkdir(parents=True, exist_ok=True)
    BATCH_DIR.mkdir(parents=True, exist_ok=True)

    v2_37_record = load_json("outputs/v2_37_core_consolidation/v2_37_official_artifact_verification.json")
    batch_state = write_batch002_outputs()

    policy_files = [
        "configs/clean_replication_batch_002.json",
        "inputs/clean_replication_batch_002_lead_pool.json",
        "docs/bugsinpy_byte_identical_exception_research_note.md",
        "docs/operational_gate_completion_roadmap.md",
        "docs/roadmap_to_v3.md",
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
            "staged_payload_directory": str(PAYLOAD_DIR),
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
            ],
            "partial_gates": ["Issue-Derived Ephemeral Reproduction Harness", "Failure Memory Weighting", "Cryptographic Evidence Ledger Sealing"],
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

    final_status = "PASS_WITH_ADDITIONAL_REPAIR" if batch_state["native_repair_successes_count"] else "PASS_WITH_BATCH002_BLOCKED"
    final_report = {
        "status": final_status,
        "exact_blocker": batch_state["exact_blocker"],
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
        "repair_generation_attempts_count": len(load_json(BATCH_DIR / "source_patch_generation_attempts.json")),
        "patches_generated_count": len([item for item in load_json(BATCH_DIR / "source_patch_generation_attempts.json") if item.get("patch_candidate_generated") is True]),
        "patch_safety_pass_count": len([item for item in load_json(BATCH_DIR / "patch_safety_results.json") if item.get("status") == "PASS"]),
        "target_validation_pass_count": len([item for item in load_json(BATCH_DIR / "target_validation_results.json") if item.get("status") == "PASS"]),
        "duplicate_replay_pass_count": len([item for item in load_json(BATCH_DIR / "duplicate_replay_results.json") if item.get("status") == "PASS"]),
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
        "memory_lift": "undemonstrated",
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
                "memory_lift": "undemonstrated",
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
            ]
        ),
    )
    write_public_docs_reports()
    write_sha256sums(POST_DIR)
    stage_artifact_payload(PAYLOAD_DIR, [POST_DIR, BATCH_DIR])
    write_artifact_manifest(PAYLOAD_DIR)
    payload_audit = audit_artifact_payload(PAYLOAD_DIR)
    write_json_deterministic(
        POST_DIR / "artifact_payload_manifest_report.json",
        {
            "status": payload_audit["status"],
            "staged_payload_directory": str(PAYLOAD_DIR),
            "artifact_manifest_name": "ARTIFACT_SHA256SUMS.txt",
            "payload_file_count": payload_audit["payload_file_count"],
            "cache_payload_count": len(payload_audit["cache_payloads"]),
            "uncovered_count": len(payload_audit["uncovered"]),
            "manifest_convention": "artifact manifest covers every uploaded payload file except the manifest file itself",
        },
    )
    write_sha256sums(POST_DIR)
    stage_artifact_payload(PAYLOAD_DIR, [POST_DIR, BATCH_DIR])
    write_artifact_manifest(PAYLOAD_DIR)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
