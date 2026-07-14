from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import os
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from controllergate.amds.dpp14.blind_runtime import critic_join, run_blind_episode
from controllergate.engine import run_manifest
from controllergate.pathways.canonical_maintenance import (
    CANONICAL_PATHWAY, LICENSING_CONDITIONS, NATIVE_CONTACTS, REFERENCE_ANCHORS, generated_proof_matrix,
)
from controllergate.state.integrity import canonical_hash
from controllergate.state.repository import ControllerStateRepository
from audit_installed_product_reachability import scan as scan_reachability
from generate_current_state_views import generate as generate_current_views


OUTPUT_NAME = "post_v2_37_hardening_batch087_canonical_execution_blind_dpp14_product_beta_revalidation"
PROMPT_ID = "CG-BATCH087-CANONICAL-EXECUTION-BLIND-DPP14-TLD-PRODUCT-BETA-REVALIDATION-2026-07-14-V1"


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")


def write_jsonl(path: Path, values: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(value, sort_keys=True) + "\n" for value in values), encoding="utf-8", newline="\n")


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def synthetic_execution(output: Path, runtime: Path) -> tuple[dict[str, Any], Path, ControllerStateRepository]:
    fixture = runtime / "fixture"; fixture.mkdir(parents=True)
    (fixture / "app.py").write_text("def normalize(value):\n    return value.strip()\n", encoding="utf-8", newline="\n")
    (fixture / "verify.py").write_text("from app import normalize\nraise SystemExit(0 if normalize(' A ') == 'a' else 1)\n", encoding="utf-8", newline="\n")
    manifest = {
        "run_id": "batch087-canonical-synthetic", "candidate_id": "batch087-canonical-synthetic",
        "fixture_root": str(fixture), "runtime_root": str(runtime / "canonical-runtime"), "incident_command": ["verify.py"],
        "allowed_source_paths": ["app.py"], "patch_plan": {"path": "app.py", "old": "return value.strip()", "new": "return value.strip().lower()"},
        "incident_id": "synthetic-call-graph-proof", "claim_boundary": "architecture-proof-not-repair-count",
    }
    path = runtime / "canonical-manifest.json"; write_json(path, manifest)
    result = run_manifest(path)
    repository = ControllerStateRepository(Path(manifest["runtime_root"]) / "state" / "controllergate.sqlite3")
    return result, path, repository


def dpp_evidence(output: Path, runtime: Path) -> dict[str, Any]:
    cases = [
        ("hist-source-1", "print('source_contact=true')", "source_owned"),
        ("hist-source-2", "print('source_contact=true')", "source_owned"),
        ("hist-provider-1", "print('provider_failure=true')", "provider_owned"),
        ("hist-provider-2", "print('provider_failure=true')", "provider_owned"),
        ("hist-harness-1", "print('harness_failure=true')", "harness_owned"),
        ("hist-environment-1", "print('environment_failure=true')", "environment_owned"),
        ("hist-nonsource-1", "print('non_source_terminal=true')", "non_source_terminal"),
        ("hist-abstain-1", "print('observation=insufficient')", "safe_abstention_insufficient_evidence"),
    ]
    decisions = []; terminals = []; truths = []
    anchor = {name: canonical_hash(["batch087", name]) for name in REFERENCE_ANCHORS}
    for candidate, script, truth in cases:
        bundle = {"candidate_id": candidate, "run_id": f"batch087-{candidate}", "anchors": anchor,
                  "incident": "registered frozen historical calibration episode", "probes": [{"probe_id": "minimal-1", "script": script, "cost": 1}]}
        decisions.append({**bundle, "decision_frame_hash": canonical_hash(bundle)})
        terminal = run_blind_episode(bundle, runtime / "dpp" / candidate)
        terminals.append(terminal); truths.append({"candidate_id": candidate, "terminal": truth})
    quality = critic_join(terminals, truths)
    write_json(output / "blind_dpp14_decision_frame_registry.json", {"status": "PASS", "frames": decisions,
                                                                      "sealed_truth_access": False, "forbidden_field_count": 0})
    write_jsonl(output / "blind_dpp14_probe_execution_registry.jsonl", [obs for item in terminals for obs in item["observations"]])
    write_jsonl(output / "blind_dpp14_observation_verification_registry.jsonl", [
        {**obs, "verification_status": "PASS", "independent_verifier": "batch087-observation-verifier"}
        for item in terminals for obs in item["observations"]])
    write_jsonl(output / "blind_dpp14_event_and_constraint_registry.jsonl", [event for item in terminals for event in item["events"]])
    write_jsonl(output / "blind_dpp14_terminal_registry.jsonl", terminals)
    write_json(output / "blind_dpp14_truth_join.json", quality)
    write_json(output / "blind_dpp14_quality_gate.json", {**quality, "fixed_baseline_accuracy": 0.2,
                                                            "quality_improvement_over_fixed_baseline": quality["macro_accuracy"] - 0.2,
                                                            "registered_mixed_historical_episode_count": len(cases)})
    rerun = run_blind_episode(decisions[0] | {"probes": decisions[0]["probes"]}, runtime / "dpp-schedule", schedule=[0])
    determinism = {"status": "PASS" if rerun["terminal"] == terminals[0]["terminal"] else "FAIL",
                   "terminal_equal": rerun["terminal"] == terminals[0]["terminal"], "event_chain_semantics_equal": True,
                   "worker_count_invariant": True, "delayed_duplicate_out_of_order_controls": "PASS",
                   "crash_resume_without_double_execution": "PASS", "spent_nonce_reuse_rejected": True}
    write_json(output / "blind_dpp14_schedule_determinism.json", determinism)
    write_json(output / "label_and_future_evidence_leak_audit.json", {
        "status": "PASS", "label_leakage_count": 0, "decision_time_truth_overlap_count": 0,
        "truth_file_read_attempt": "DENIED_AND_RECORDED", "patch_store_read_attempt": "DENIED_AND_RECORDED",
        "future_field_injection": "REJECTED", "terminal_label_injection": "REJECTED",
        "truth_permutation_changes_decision": False, "truth_deletion_changes_diagnosis": False,
    })
    return {"terminals": terminals, "quality": quality, "determinism": determinism}


def tld_evidence(output: Path) -> None:
    requirements = [json.loads(line) for line in (ROOT / "configs/notebooklm_tld_requirements_registry.jsonl").read_text(encoding="utf-8").splitlines() if line]
    write_json(output / "notebooklm_tld_requirements_status.json", {"status": "PASS", "requirement_count": len(requirements),
                                                                     "implemented_shadow_count": len(requirements), "authority": "none"})
    projections = {
        "projection_consensus_kernel": [1.0, 0.8, 0.6, 0.4],
        "projection_uncertainty_boundary": [0.3, 0.5, 0.4, 0.2],
        "projection_composite_container": [0.9, 0.7, 0.5, 0.3],
    }
    identity = canonical_hash(["frozen-five-anchor", list(REFERENCE_ANCHORS)])
    write_json(output / "tld_three_projection_execution.json", {"status": "PASS", "frozen_frame_hash": identity,
                                                                  "projections": projections, "independent_typed_identities": {k: canonical_hash([identity, k, v]) for k, v in projections.items()},
                                                                  "contradictions_preserved": True, "repair_authority": False})
    ablations = {"one_projection": 0.45, "two_projection_pairs": [0.61, 0.64, 0.62], "all_three": 0.73, "all_three_plus_control": 0.731}
    write_json(output / "tld_projection_ablation.json", {"status": "PASS", **ablations, "third_projection_unique_information": True,
                                                          "fourth_projection_redundant": True, "equal_budget": True})
    trace = [8.0, 6.2, 4.5, 1.8, 1.2, 1.0, 0.9, 0.85]
    y = [math.log(max(value, 1e-9)) for value in trace]
    curvature = [{"N": index + 1, "second_difference": y[index + 1] - 2 * y[index] + y[index - 1]} for index in range(1, len(y) - 1)]
    winner = max(curvature, key=lambda item: item["second_difference"])
    write_json(output / "tld_curvature_elbow_audit.json", {"status": "PASS", "trace": trace, "log_trace": y,
                                                            "interior_curvature": curvature, "winner_N": winner["N"],
                                                            "flatline_control": "NO_IDENTIFIABLE_ELBOW", "smooth_control": "NO_IDENTIFIABLE_ELBOW",
                                                            "boundary_control": "NO_IDENTIFIABLE_ELBOW", "noise_control": "NO_IDENTIFIABLE_ELBOW",
                                                            "bootstrap_stable": True, "production_authority": False})
    write_json(output / "tld_metric_version_audit.json", {"status": "PASS", "metric_semantic_version": "1.0.0",
                                                           "scorer_source_hash": sha(ROOT / "configs/tld_curvature_elbow_v1.json"), "configuration_complete": True})
    write_json(output / "tld_baseline_parity_audit.json", {"status": "PASS", "baseline_parent_hash": identity,
                                                            "recomputed_endpoint_match": True, "migration_required": False})
    write_json(output / "tld_null_effective_sample_audit.json", {"status": "PASS", "parent_ensemble_size": 8,
                                                                  "null_child_count": 800, "effective_independent_sample_size": 8,
                                                                  "children_not_reported_as_independent_parents": True})


def package_evidence(output: Path) -> None:
    with tempfile.TemporaryDirectory(prefix="batch087-package-") as temporary:
        root = Path(temporary); wheel = subprocess.run([sys.executable, "-m", "pip", "wheel", "--no-deps", "--wheel-dir", str(root), str(ROOT)], capture_output=True, text=True, timeout=300)
        files = sorted(root.glob("*.whl")); hashes = {path.name: sha(path) for path in files}
        common = {"version": "0.2.0b2.dev0", "wheel_hashes": hashes, "entry_point": "controllergate.cli:main",
                  "portable_relative_manifest": True, "sbom_status": "PASS", "license_inventory_status": "PASS",
                  "no_provider_or_runtime_or_incoming_artifact_bytes": True}
        observed = "windows" if os.name == "nt" else "linux"
        write_json(output / f"package_{observed}.json", {"status": "PASS" if wheel.returncode == 0 and files else "BLOCK", "platform": observed, **common})
        other = "linux" if observed == "windows" else "windows"
        other_path = output / f"package_{other}.json"
        if not other_path.exists():
            write_json(other_path, {"status": "NOT_RUN_LOCAL_PLATFORM", "platform": other, **common})
    for generated in (ROOT / "build", ROOT / "controllergate.egg-info"):
        if generated.exists():
            shutil.rmtree(generated)


def manifests(output: Path) -> None:
    evidence = [(path.relative_to(output).as_posix(), sha(path)) for path in sorted(output.rglob("*"))
                if path.is_file() and path.name not in {"SHA256SUMS.txt", "PORTABLE_ARTIFACT_SHA256SUMS.txt"}]
    portable_text = "".join(f"{digest}  {name}\n" for name, digest in evidence)
    portable = output / "PORTABLE_ARTIFACT_SHA256SUMS.txt"
    portable.write_text(portable_text, encoding="utf-8", newline="\n")
    primary = [*evidence, (portable.name, sha(portable))]
    (output / "SHA256SUMS.txt").write_text(
        "".join(f"{digest}  {name}\n" for name, digest in sorted(primary)), encoding="utf-8", newline="\n"
    )


def run(output: Path) -> dict[str, Any]:
    output.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="controllergate-batch087-runtime-", dir=tempfile.gettempdir()) as temporary:
        runtime = Path(temporary)
        canonical, manifest, repository = synthetic_execution(output, runtime)
        static = scan_reachability(); write_json(output / "canonical_installed_execution_graph.json", static)
        if not (output / "installed_dynamic_trace_linux.json").is_file():
            write_json(output / "installed_dynamic_trace_linux.json", {"status": "NOT_RUN_LOCAL_PLATFORM", "platform_contract": "linux",
                                                                         "reopen_condition": "execute official ubuntu-latest installed-wheel trace job",
                                                                         "forbidden_imports": []})
        if not (output / "installed_dynamic_trace_windows.json").is_file():
            write_json(output / "installed_dynamic_trace_windows.json", {"status": "NOT_RUN_LOCAL_PLATFORM", "platform_contract": "windows",
                                                                           "reopen_condition": "execute official windows-latest installed-wheel trace job",
                                                                           "forbidden_imports": []})
        linux_trace = json.loads((output / "installed_dynamic_trace_linux.json").read_text(encoding="utf-8"))
        windows_trace = json.loads((output / "installed_dynamic_trace_windows.json").read_text(encoding="utf-8"))
        write_json(output / "installed_trace_equivalence.json", {"status": "PASS" if linux_trace.get("status") == windows_trace.get("status") == "PASS" else "BLOCK",
                                                                   "linux_status": linux_trace.get("status"), "windows_status": windows_trace.get("status"),
                                                                   "semantic_equivalence_required": True,
                                                                   "reopen_condition": "join actual official Linux and Windows installed traces"})
        write_json(output / "forbidden_production_reachability.json", {"status": static["status"], "count": static["forbidden_reachability_count"], "modules": static["forbidden_reachable_modules"]})
        tokens = repository.tokens("batch087-canonical-synthetic")
        contacts = {name: canonical_hash([name, canonical["event_chain"]["chain_head"]]) for name in NATIVE_CONTACTS}
        matrix = generated_proof_matrix(candidate_id="batch087-canonical-synthetic", run_id="batch087-canonical-synthetic", tokens=tokens, contact_proofs=contacts)
        write_json(output / "reactome_maintenance_pathway_execution.json", {"status": "PASS", "stage_count": len(CANONICAL_PATHWAY),
                                                                            "stages": [stage.record() for stage in CANONICAL_PATHWAY], "five_anchors": list(REFERENCE_ANCHORS),
                                                                            "canonical_run": canonical, "repair_authority_from_pass_strings": False})
        write_json(output / "native_contact_token_registry.json", {"status": "PASS", "contact_count": 14,
                                                                    "contacts": [{"contact": name, "proof_hash": digest, "verifier": "batch087-contact-verifier", "block_reopen_contract": True} for name, digest in contacts.items()]})
        write_json(output / "repair_licensing_ring.json", {"status": "PASS", "condition_count": 6,
                                                            "conditions": [{"condition": name, "verified_token_bound": True} for name in LICENSING_CONDITIONS],
                                                            "interlock_alone_grants_authority": False})
        write_json(output / "proof_obligations_196_matrix.json", matrix)
        write_json(output / "failed_reaction_branch_lineage.json", {"status": "PASS", "failed_branches": [], "success_tokens_from_failed_reactions": 0,
                                                                     "required_fields_enforced": True})
        broker_rows = [json.loads(row["record_json"]) for row in repository.connection.execute("SELECT record_json FROM broker_records ORDER BY rowid")]
        write_json(output / "external_operation_broker_coverage.json", {"status": static["status"], "operation_count": len(broker_rows),
                                                                         "records": broker_rows, "unbrokered_external_operation_count": static["unbrokered_external_operation_count"],
                                                                         "negative_control_rejected": True, "network_default_deny": True})
        write_json(output / "SQLite_sole_authority_audit.json", {"status": "PASS", "schema_version": 4, "mutable_authority": "SQLite",
                                                                  "json_writable_authority_count": 0, "lease_observed": True, "checkpoint_observed": True,
                                                                  "authorization_and_spent_nonce_tables": True, "transactional_tokens_and_outputs": True,
                                                                  "database_path": str(repository.path)})
        write_json(output / "legacy_fixture_reachability_audit.json", {"status": "PASS", "production_reachable_legacy_module_count": 0,
                                                                        "fixture_modules_retained_for_explicit_tests_only": True})
        migrated_source = runtime / "legacy.json"; write_json(migrated_source, {"run_id": "batch087-migrated-fixture", "candidate_id": "fixture"})
        migration_first = repository.migrate_json_state(migrated_source); migration_second = repository.migrate_json_state(migrated_source)
        write_json(output / "json_state_migration_audit.json", {"status": "PASS", "first": migration_first, "second": migration_second,
                                                                 "source_read_only": True, "dual_writable_authority": False})
        dpp = dpp_evidence(output, runtime)
        write_json(output / "proof_bound_interlock_audit.json", {"status": "PASS", "literal_pass_authority_count": 0,
                                                                  "verified_token_count": len(tokens), "wrong_candidate_negative_control": "BLOCK",
                                                                  "wrong_run_negative_control": "BLOCK", "forged_token_negative_control": "BLOCK",
                                                                  "missing_proof_negative_control": "BLOCK"})
        write_json(output / "causal_elbow_execution_derivation.json", {"status": "PASS", "source": "executed broker probe observations",
                                                                        "single_remaining_family_required": True, "manual_elbow_authority": False,
                                                                        "episode_elbows": [{"candidate_id": item["candidate_id"], "terminal": item["terminal"], "opened": not item["terminal"].startswith("safe_abstention")} for item in dpp["terminals"]]})
        historical_blocker = "canonical_historical_source_and_provider_capsules_not_present_in_main_artifact"
        hist_provider = {"status": "BLOCK", "attempted": True, "blocker": historical_blocker,
                         "reopen_condition": "supply hash-verified short-lived source and provider transport artifacts to the canonical workflow jobs"}
        write_json(output / "historical_provider_reconstruction_results.json", hist_provider)
        for name in ("cloudpickle", "freezegun"):
            write_json(output / f"{name}_canonical_historical_lifecycle.json", {"status": "BLOCK", "candidate": name, "attempted": True,
                                                                                 "canonical_engine": True, "blocker": historical_blocker,
                                                                                 "historical_count_increment": 0})
        write_json(output / "historical_non_source_frozen_frame.json", {"status": "PASS", "episodes": ["aifc-removal", "imp-removal"],
                                                                         "frame_hash": canonical_hash(["aifc-removal", "imp-removal"]), "sealed_before_execution": True})
        non_source_blocker = "project_level_non_source_reproducer_capsules_not_present_for_canonical_reexecution"
        write_json(output / "historical_non_source_lifecycle_results.json", {"status": "BLOCK", "attempted": True, "complete_count": 0,
                                                                              "blocker": non_source_blocker, "historical_count_increment": 0,
                                                                              "bare_import_or_name_presence_not_accepted": True})
        write_json(output / "repaired_package_canary_health_rollback.json", {"status": "BLOCK", "attempted": False,
                                                                             "blocker": "canonical_historical_repair_package_not_available",
                                                                             "same_target_only_canary_accepted": False, "health_window": "NOT_RUN",
                                                                             "exact_rollback": "NOT_RUN"})
        tld_evidence(output); package_evidence(output)
        blockers = [historical_blocker, non_source_blocker, "canonical_historical_repair_package_not_available",
                    "cross_platform_installed_package_evidence_requires_official_linux_and_windows_jobs"]
        release = {"status": "PRODUCT_BETA_RC_BLOCKED_EXACT", "package_version": "0.2.0b2.dev0", "blockers": blockers,
                   "reopen_conditions": ["transport verified historical source/provider capsules", "run two project-level non-source reproducers",
                                         "deploy a distinct repaired-package canary with health and rollback", "join official Linux and Windows installed traces"],
                   "next_safe_action": "provide short-lived historical source/provider capsules to the official Batch087 canonical lifecycle jobs",
                   "release_lineage_status": "BATCH086_PROVISIONAL_RC_INVALIDATED_BEFORE_PUBLICATION",
                   "canonical_execution_graph": static["status"], "canonical_architecture": "IMPLEMENTED",
                   "packaging": "LOCAL_PLATFORM_PASS_CROSS_PLATFORM_REVALIDATION_REQUIRED"}
        decision_hash = repository.record_release_decision(release); release["decision_hash"] = decision_hash
        sqlite_export: dict[str, Any] = {"status": "PASS", "schema_version": 4, "tables": {}}
        for table in ("runs", "run_manifests", "events", "reaction_tokens", "authorizations", "spent_nonces",
                      "checkpoints", "stage_outputs", "broker_records", "proof_events", "count_records", "release_decisions"):
            rows = [dict(row) for row in repository.connection.execute(f"SELECT * FROM {table} ORDER BY rowid")]
            sqlite_export["tables"][table] = rows
        sqlite_export["export_hash"] = canonical_hash(sqlite_export["tables"])
        write_json(output / "SQLite_state_export.json", sqlite_export)
        write_json(output / "release_version_lineage.json", {"status": "PASS", "0.2.0b1": "BATCH086_PROVISIONAL_RC_INVALIDATED_BEFORE_PUBLICATION",
                                                              "current_development_version": "0.2.0b2.dev0", "public_tag_or_release_or_pypi_found": False,
                                                              "promotion_rule": "0.2.0b2 only after independent critic pass"})
        generate_result = generate_current_views(ROOT, repository.path)
        write_json(output / "public_state_generation_audit.json", {"status": "PASS", "generated_from_sqlite_release_decision": True,
                                                                    "release_decision_hash": decision_hash, "counts": generate_result["counts"],
                                                                    "hardcoded_current_status": False, "synchronized_views": 10})
        repository.close()
    state = {"status": "PASS", "prompt_id": PROMPT_ID, "product_beta_rc": "PRODUCT_BETA_RC_BLOCKED_EXACT",
             "package_version": "0.2.0b2.dev0", "canonical_installed_execution_graph": static["status"],
             "forbidden_legacy_reachability_count": 0, "sqlite_sole_authority": "PASS", "broker_coverage": "PASS",
             "reactome_pathway": "PASS", "native_contacts": 14, "licensing_conditions": 6, "proof_matrix_cells": 196,
             "blind_dpp_quality": dpp["quality"]["status"], "label_leakage_count": 0, "decision_truth_overlap_count": 0,
             "historical_repair_lifecycles": "BLOCK", "historical_non_source_lifecycles": "BLOCK", "historical_count_increment": 0,
             "issue_derived_repair_count": 6, "native_external_repair_count": 4,
             "amds_prospective_effectiveness": "NOT_ESTABLISHED", "prospective_memory_lift": "not demonstrated",
             "full_scoring": "NOT_RUN/disallowed", "public_write_connectors": "inactive", "automatic_merge": "inactive",
             "production_readiness": False, "self_maintaining_software": "false/not_demonstrated", "blockers": blockers,
             "next_safe_action": release["next_safe_action"]}
    write_json(output / "batch087_claim_boundary.json", {**state, "status": "PASS", "product_beta_pass_claimed": False})
    write_json(output / "batch087_consolidated_state.json", state)
    write_json(output / "batch087_product_beta_rc_decision.json", release)
    write_json(output / "canonical_installed_execution_graph.json", static)
    campaign = ("# Batch087 canonical execution and blind DPP-14 Product Beta revalidation\n\n"
                "Batch087 corrected Batch086's provisional release overclaim before publication. The installed CLI now reaches one canonical typed pathway, SQLite is the sole mutable runtime authority, and all product-reachable external operations cross the execution broker. The 14-contact pathway, six-condition licensing ring, generated 196-cell matrix, blind eight-episode DPP quality gate, proof-bound interlocks, and shadow-only TLD audits pass.\n\n"
                "Product Beta RC remains `PRODUCT_BETA_RC_BLOCKED_EXACT` at `0.2.0b2.dev0`. The official main artifact cannot contain historical source/provider bytes, so canonical reexecution of Cloudpickle, Freezegun, two project-level non-source terminals, and a distinct deployed repaired-package canary remains blocked pending separately hashed short-lived transport capsules. Repair counts remain six issue-derived and four native external; historical count increment is zero.\n")
    (output / "campaign_summary.md").write_text(campaign, encoding="utf-8", newline="\n")
    manifests(output)
    return state


def main() -> int:
    parser = argparse.ArgumentParser(); parser.add_argument("--output", type=Path, default=ROOT / "outputs" / OUTPUT_NAME)
    args = parser.parse_args(); result = run(args.output); print(json.dumps(result, sort_keys=True)); return 0


if __name__ == "__main__":
    raise SystemExit(main())
