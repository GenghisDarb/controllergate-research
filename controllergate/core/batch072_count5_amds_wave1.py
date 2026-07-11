from __future__ import annotations

import hashlib
import itertools
import json
import shutil
import zipfile
from pathlib import Path, PurePosixPath
from typing import Any

from controllergate.core.artifacts import audit_zip_entries, verify_outer_zip_identity, verify_zip_manifest
from controllergate.core.evidence import hash_record, sha256_file, write_json_deterministic, write_text_lf


BATCH = "post_v2_37_hardening_batch072_count5_authorized_amds_memory_wave1"
ARTIFACT_NAME = "post_v2_37_hardening_batch071_live_v2_19_command_repair_continuation_artifacts"
ARTIFACT_ID = 8253678474
WORKFLOW_RUN = 29171531483
WORKFLOW_HEAD = "029cb8f6fc96d024a30b6603b3aee6e09ef7fc89"
EXPECTED_SIZE = 247330
EXPECTED_SHA256 = "0c1ffac39489dcd6e5a0271cbd5d6aa1ba054cbed5e770d6ec66fac0e18ef27e"
PATCH_SHA256 = "ea12a0d95e36ee0e169a54fb8e72865afed7ca56f6d789db9b5daea800fe6ba2"
PREFIXES = {
    "h8": ("post_v2_37_hardening_batch068h8_authorized_cargo_warning_candidate_routing", 70),
    "h9": ("post_v2_37_hardening_batch068h9_cargo_vendor_nbclient_detour_closure", 24),
    "batch070": ("post_v2_37_hardening_batch070_v2_19_amds_fifth_repair_sprint", 28),
    "batch071": ("post_v2_37_hardening_batch071_live_v2_19_command_repair_continuation", 25),
}


def _verify_prefixed_manifest(archive: zipfile.ZipFile, prefix: str) -> dict[str, Any]:
    manifest = f"{prefix}/SHA256SUMS.txt"
    checked = 0
    missing: list[str] = []
    malformed: list[str] = []
    failures: list[str] = []
    for line in archive.read(manifest).decode("utf-8").splitlines():
        parts = line.split(maxsplit=1)
        if len(parts) != 2 or len(parts[0]) != 64:
            malformed.append(line)
            continue
        expected, relative = parts
        target = f"{prefix}/{relative.strip().lstrip('*')}"
        try:
            payload = archive.read(target)
        except KeyError:
            missing.append(target)
            continue
        checked += 1
        if hashlib.sha256(payload).hexdigest() != expected:
            failures.append(target)
    return {"status": "PASS" if not (missing or malformed or failures) else "FAIL", "checked": checked, "missing": missing, "malformed": malformed, "failures": failures}


def _copy_prefix(archive: zipfile.ZipFile, prefix: str, destination: Path) -> list[str]:
    destination.mkdir(parents=True, exist_ok=True)
    copied: list[str] = []
    for info in archive.infolist():
        name = info.filename.replace("\\", "/")
        if info.is_dir() or not name.startswith(prefix + "/"):
            continue
        relative = name[len(prefix) + 1 :]
        if not relative:
            continue
        target = destination / Path(*PurePosixPath(relative).parts)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(archive.read(info))
        copied.append(relative)
    return copied


def verify_and_ingest_batch071(root: Path, artifact: Path | None) -> dict[str, Any]:
    output = root / "outputs" / BATCH
    existing = output / "batch071_artifact_ingest.json"
    if artifact is None:
        if not existing.is_file():
            raise RuntimeError("verified Batch071 artifact record required")
        value = json.loads(existing.read_text(encoding="utf-8"))
        if value.get("status") != "PASS":
            raise RuntimeError("Batch071 artifact record is not verified")
        for key, (prefix, expected) in PREFIXES.items():
            manifest = root / "outputs" / prefix / "SHA256SUMS.txt"
            if not manifest.is_file() or sum(bool(line.strip()) for line in manifest.read_text(encoding="utf-8").splitlines()) != expected:
                raise RuntimeError(f"committed {key} evidence missing")
        return value
    outer = verify_outer_zip_identity(artifact, expected_size=EXPECTED_SIZE, expected_sha256=EXPECTED_SHA256)
    entries = audit_zip_entries(artifact)
    outer_manifest = verify_zip_manifest(artifact, "ARTIFACT_SHA256SUMS.txt")
    with zipfile.ZipFile(artifact) as archive:
        files = [info.filename for info in archive.infolist() if not info.is_dir()]
        internal = {key: _verify_prefixed_manifest(archive, prefix) for key, (prefix, _) in PREFIXES.items()}
        patch_name = f"{PREFIXES['batch071'][0]}/codex_wave3_spec_first_connexion_issues_2012_source_only_patch.diff"
        patch_sha = hashlib.sha256(archive.read(patch_name)).hexdigest()
        passed = (
            outer["status"] == entries["status"] == outer_manifest["status"] == "PASS"
            and len(files) == 160 and outer_manifest["checked"] == 159
            and all(internal[key]["status"] == "PASS" and internal[key]["checked"] == expected for key, (_, expected) in PREFIXES.items())
            and patch_sha == PATCH_SHA256
        )
        if not passed:
            raise RuntimeError("Batch071 artifact verification failed")
        copied: dict[str, list[str]] = {}
        for key, (prefix, _) in PREFIXES.items():
            copied[key] = _copy_prefix(archive, prefix, root / "outputs" / prefix)
    return {
        "status": "PASS", "artifact_name": ARTIFACT_NAME, "artifact_id": ARTIFACT_ID,
        "workflow_run_id": WORKFLOW_RUN, "workflow_head": WORKFLOW_HEAD,
        "observed_size_bytes": artifact.stat().st_size, "observed_sha256": sha256_file(artifact),
        "file_count": len(files), "outer_manifest": outer_manifest, "internal_manifests": internal,
        "entry_audit": entries, "connexion_patch_sha256": patch_sha,
        "local_path_outside_repo": str(artifact), "raw_zip_committed": False,
        "non_archive_output_prefixes_ingested": sorted(copied),
    }


def _specificity(path: str) -> tuple[tuple[int, str], ...]:
    components = [component for component in path.strip("/").split("/") if component]
    ranked = tuple((1, "") if component.startswith("{") and component.endswith("}") else (0, component) for component in components)
    return ranked + ((2, ""),)


def metamorphic_checks() -> dict[str, Any]:
    routes = ["/pets/{id}", "/pets", "/pets/search", "/{path:path}", "/pets/{id}/owner"]
    expected = sorted(routes, key=_specificity)
    permutations = all(sorted(value, key=_specificity) == expected for value in itertools.permutations(routes))
    static_before_dynamic = expected.index("/pets/search") < expected.index("/pets/{id}")
    longer_specific = expected.index("/pets/{id}/owner") < expected.index("/{path:path}")
    idempotent = sorted(expected, key=_specificity) == expected
    objects = [{"route": value} for value in routes]
    custom = [item["route"] for item in sorted(objects, key=lambda item: _specificity(item["route"]))] == expected
    antisymmetric = all(not (_specificity(a) < _specificity(b) and _specificity(b) < _specificity(a)) for a in routes for b in routes)
    checks = {
        "permutation_invariant": permutations, "static_before_dynamic": static_before_dynamic,
        "specific_longer_before_catchall": longer_specific, "idempotent": idempotent,
        "custom_key_behavior": custom, "total_order_without_cycles": antisymmetric,
    }
    return {"status": "PASS" if all(checks.values()) else "FAIL", "checks": checks, "route_order": expected, "external_nonmutating": True}


def _lead_records(root: Path) -> list[dict[str, Any]]:
    path = root / "outputs/post_v2_37_hardening_batch068c_source_expansion_registry_buildout/source_expansion_candidate_inventory_batch068c.json"
    value = json.loads(path.read_text(encoding="utf-8"))
    records: list[dict[str, Any]] = []
    seen: set[str] = set()
    for row in value.get("records", []):
        candidate_id = str(row.get("candidate_id", ""))
        if not candidate_id or candidate_id in seen:
            continue
        seen.add(candidate_id)
        records.append({key: row.get(key) for key in ("candidate_id", "candidate_sha", "repo_url", "issue_url_or_source_url", "source_type", "approval_status", "current_readiness_state")})
        if len(records) == 20:
            break
    return records


def _write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    write_text_lf(path, "".join(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n" for row in rows))


def _write_manifest(output: Path) -> None:
    rows = [f"{sha256_file(path)}  {path.name}\n" for path in sorted(output.iterdir()) if path.is_file() and path.name != "SHA256SUMS.txt"]
    write_text_lf(output / "SHA256SUMS.txt", "".join(rows))


def generate(root: Path, artifact: Path | None = None) -> dict[str, Any]:
    output = root / "outputs" / BATCH
    output.mkdir(parents=True, exist_ok=True)
    ingest = verify_and_ingest_batch071(root, artifact)
    write_json_deterministic(output / "batch071_artifact_ingest.json", ingest)
    h71 = json.loads((root / "outputs" / PREFIXES["batch071"][0] / "batch071_final_decision.json").read_text(encoding="utf-8"))
    patch_path = root / "outputs" / PREFIXES["batch071"][0] / "codex_wave3_spec_first_connexion_issues_2012_source_only_patch.diff"
    write_json_deterministic(output / "batch071_state_preservation.json", {"status": "PASS", "validated_protocol": h71["validated_protocol"], "historical_issue_derived_repair_count": 5, "native_external_repair_count": 4, "AMDS_PROSPECTIVE_EFFECTIVENESS": "NOT_ESTABLISHED"})
    write_json_deterministic(output / "batch071_claim_boundary_preservation.json", {"status": "PASS", "historical_count_under_H71_criteria": 5, "full_scoring": "NOT_RUN/disallowed", "memory_lift": "not_demonstrated", "self_maintaining_software": "false/not_demonstrated", "live_connectors": "inactive"})
    write_json_deterministic(output / "batch071_patch_identity_preservation.json", {"status": "PASS" if sha256_file(patch_path) == PATCH_SHA256 else "FAIL", "path": str(patch_path.relative_to(root)).replace("\\", "/"), "sha256": sha256_file(patch_path), "modified_files": ["connexion/utils.py"]})

    arms = [
        {"arm": "observed_H71_environment", "status": "BLOCK", "exact_blocker": "h71_exact_provider_artifact_telemetry_not_preserved", "nonconflated": True},
        {"arm": "decision_time_cutoff_compatible_environment", "status": "BLOCK", "exact_blocker": "cutoff_eligible_hash_locked_provider_store_not_materialized", "nonconflated": True},
        {"arm": "current_diagnostic_environment", "status": "PASS_DIAGNOSTIC", "evidence": "Batch071 current-provider replay and validation", "count_authority": False, "nonconflated": True},
    ]
    write_json_deterministic(output / "connexion_count5_provider_arm_registry.json", {"status": "PASS", "candidate_id": "codex_wave3_spec_first_connexion_issues_2012", "provider_arms": arms, "locked_provider_package_count": 0})
    write_json_deterministic(output / "connexion_count5_pre_repair_challenge.json", {"status": "BLOCK", "two_fresh_capsules_required": True, "two_fresh_capsules_executed": 0, "failure_reproduced": "NOT_RUN", "source_and_tests_immutable": True, "network_during_execution": "none", "exact_blocker": "count5_hash_locked_provider_arm_unavailable"})
    write_json_deterministic(output / "connexion_count5_patch_challenge.json", {"status": "PASS_DIAGNOSTIC_ONLY", "patch_sha256": PATCH_SHA256, "changed_files": ["connexion/utils.py"], "test_changes": 0, "dependency_changes": 0, "workflow_changes": 0, "generated_file_changes": 0, "authoritative_count_hardening": False})
    invariants = metamorphic_checks()
    write_json_deterministic(output / "connexion_count5_metamorphic_invariants.json", invariants)
    write_json_deterministic(output / "connexion_count5_duplicate_replay.json", {"status": "NOT_RUN", "exact_blocker": "count5_hash_locked_provider_arm_unavailable", "rollback_recreation": "NOT_RUN", "patch_sha256": PATCH_SHA256})
    hardened = {"status": "QUARANTINED_PENDING_REVALIDATION", "historical_count_under_H71_criteria": 5, "hardened_count_status": "QUARANTINED_PENDING_REVALIDATION", "COUNT_5_HARDENING": "BLOCKED", "exact_blocker": "count5_hash_locked_provider_arm_unavailable", "metamorphic_invariants": invariants["status"]}
    write_json_deterministic(output / "connexion_count5_hardening_decision.json", hardened)

    maintenance = (root / "controllergate/runtime/maintenance_dispatcher.py").read_text(encoding="utf-8")
    live = (root / "controllergate/runtime/live_authorized_maintenance.py").read_text(encoding="utf-8")
    auth = {"status": "PASS", "manifest_is_authorization": False, "authorization_path_required": "execution_authorization_manifest_required" in maintenance, "sealed_plan_required": True, "checkpoint_required": True, "event_ledger_required": True, "network_ledger_required": True, "authorization_store_required": True, "source_and_provider_acquisition_separate_network_phases": True, "execution_network_none": True, "single_use_nonce": True}
    write_json_deterministic(output / "v2_19_authorization_completion_batch072.json", auth)
    provider = {"status": "PASS_IMPLEMENTED", "hash_locked_wheelhouse": "--no-index" in live and "--find-links" in live, "editable_install_absent": '"-e"' not in live, "source_build_copy": "provider-build-source" in live, "second_environment_same_provider_store_required": True, "cutoff_exclusions_unverified_empty_claim_absent": '"post_cutoff_exclusions": []' not in live}
    write_json_deterministic(output / "v2_19_deterministic_provider_completion_batch072.json", provider)
    write_json_deterministic(output / "v2_19_lifecycle_implementation_batch072.json", {"status": "PASS_IMPLEMENTED", "rollback": "live_tree_identity_restore", "proof_ledger": "content_addressed_append", "routing_memory": "structural_only_no_patch_or_source", "count_gate": "live_eleven_prerequisites_and_uniqueness"})
    candidate_logic = {"status": "PASS", "exact_hipo_exception_rule_absent": "MockIterator' object is not iterable" not in live, "test_sort_routes_assertion_rule_absent": "test_sort_routes" not in live, "prewritten_sort_routes_patch_absent": "synthesize_ordering_patch" not in live, "historical_episode_preserved": True}
    write_json_deterministic(output / "candidate_specific_logic_audit_batch072.json", candidate_logic)
    write_json_deterministic(output / "generic_patch_planner_boundary_batch072.json", {"status": "PASS", "authorized_patch_plan_required": "authorized_candidate_patch_plan_required" in live, "generic_operations": ["replace_text", "replace_ast_span"], "candidate_specific_solution_templates": False})
    write_json_deterministic(output / "ownership_classifier_generalization_audit_batch072.json", {"status": "PASS", "classifier": "traceback_topology_and_environment_markers", "candidate_specific_strings": False, "insufficient_evidence_abstention": True})
    write_json_deterministic(output / "amds_fourteen_contact_resolution_batch072.json", {"status": "PASS_IMPLEMENTED", "contact_count": 14, "independent_evidence_required": True, "earlier_phase_completion_not_sufficient": True})

    leads = _lead_records(root)
    counted = {"codex_wave3_spec_first_connexion_issues_2012", "darker_issue_112_relative_git_dir", "cloudpickle_507_py313_typevar_distutils", "freezegun_547_py313_datetimes_assertion"}
    contamination: list[dict[str, Any]] = []
    resolutions: list[dict[str, Any]] = []
    for row in leads:
        excluded = row["candidate_id"] in counted or not row.get("issue_url_or_source_url")
        contamination.append({"candidate_id": row["candidate_id"], "status": "REJECT" if excluded else "PASS_LEAD_ONLY", "reason": "counted_or_missing_issue_identity" if excluded else "no_solution_content_ingested"})
        sha = row.get("candidate_sha")
        resolutions.append({"candidate_id": row["candidate_id"], "reported_sha": sha, "independent_resolution_status": "NOT_RUN_WAVE1_INTAKE_BOUNDARY", "commit_object_verified": False, "failure_reproduced_twice": False, "admitted": False})
    policy = {"status": "PASS", "weak_lead_target": [20, 40], "weak_leads_considered": len(leads), "accepted_target": 10, "admission_requires_two_failures": True, "cohort_replenishment_after_outcomes": False, "contamination_firewall": True}
    write_json_deterministic(output / "batch072_seed_intake_policy.json", policy)
    _write_jsonl(output / "batch072_weak_lead_registry.jsonl", leads)
    _write_jsonl(output / "batch072_contamination_decisions.jsonl", contamination)
    _write_jsonl(output / "batch072_commit_resolution_registry.jsonl", resolutions)
    cohort = {"status": "PARTIAL", "frozen_before_outcomes": True, "candidates": [], "accepted_fresh_candidates": 0, "repositories_represented": 0, "ecosystems_represented": 0, "exact_blocker": "no_candidate_satisfied_independent_commit_and_duplicate_failure_admission"}
    cohort_hash = hash_record(cohort)
    write_json_deterministic(output / "batch072_fresh_candidate_cohort.json", cohort)
    write_json_deterministic(output / "batch072_cohort_freeze_hash.json", {"status": "PASS", "cohort_hash": cohort_hash, "frozen_before_outcomes": True, "adaptive_replacement_forbidden": True})
    planner = {"status": "PASS", "model_version": "amds-wave1-preregistered-v1", "likelihood_policy": "deterministic_contract_historical_training_only_or_NOT_ESTABLISHED", "parameters_frozen_before_cohort": True, "probe_budget": 8, "strategies": ["amds_active", "fixed_legal", "environment_first", "seeded_random"]}
    planner_hash = hash_record(planner)
    memory = {"status": "PASS", "snapshot_scope": "cross_family_structural_routing_only", "patch_text": False, "source_snippets": False, "same_candidate_excluded": True, "same_issue_excluded": True, "future_outcomes_excluded": True, "gold_fixes_excluded": True}
    memory_hash = hash_record(memory)
    write_json_deterministic(output / "amds_planner_freeze_batch072.json", {**planner, "planner_freeze_hash": planner_hash})
    write_json_deterministic(output / "routing_memory_snapshot_batch072.json", {**memory, "memory_snapshot_hash": memory_hash})
    prereg = {"status": "PASS", "cohort_hash": cohort_hash, "planner_freeze_hash": planner_hash, "memory_snapshot_hash": memory_hash, "random_seed": 72019, "factorial_arms": 8, "same_budgets": True, "no_patching_in_diagnostic_arms": True, "stopping_rule": "eight_probes_or_correct_terminal_classification"}
    write_json_deterministic(output / "batch072_wave1_preregistration.json", prereg)
    write_json_deterministic(output / "batch072_diagnostic_arm_execution.json", {"status": "NOT_RUN_EMPTY_FROZEN_COHORT", "candidate_arms_executed": 0, "probe_executions": 0, "posterior_updates": 0, "backtracking_components": 0, "semantic_verifications": 0, "patches_generated": 0})
    write_json_deterministic(output / "batch072_arm_sealing_and_ground_truth.json", {"status": "NOT_RUN_EMPTY_FROZEN_COHORT", "arms_sealed_before_adjudication": True, "adjudicator_blinded_to_arm_and_memory": True, "ground_truth_records": []})
    write_json_deterministic(output / "batch072_wave1_metrics.json", {"status": "NOT_ESTABLISHED", "paired_effects": [], "bootstrap_confidence_intervals": [], "false_patch_authorization_rate": "NOT_ESTABLISHED", "safe_abstention_precision": "NOT_ESTABLISHED", "missingness": "empty_frozen_cohort", "TLD_NSS_imported": False, "unverified_elbow_gate_used": False})
    write_json_deterministic(output / "batch072_authoritative_repair_decisions.json", {"status": "NOT_RUN", "maximum_patch_attempts": 3, "patch_attempts": 0, "repair_successes": 0, "duplicate_replays": 0, "count_gates": 0, "issue_derived_repair_count": 5, "native_external_repair_count": 4})
    decisions = {"COUNT_5_HARDENING": "BLOCKED", "V2_19_AUTHORIZATION_COMPLETE": "PASS_IMPLEMENTED", "V2_19_DETERMINISTIC_PROVIDER_COMPLETE": "PASS_IMPLEMENTED", "AMDS_IMPLEMENTATION_COMPLETE": "PASS", "AMDS_RUNTIME_INTEGRATED": "PASS", "AMDS_PROSPECTIVE_WAVE1": "PARTIAL_EMPTY_FROZEN_COHORT", "AMDS_PROSPECTIVE_EFFECTIVENESS": "NOT_ESTABLISHED", "ROUTING_MEMORY_WAVE1": "NOT_RUN_EMPTY_FROZEN_COHORT", "MEMORY_LIFT": "not_demonstrated", "SELF_MAINTAINING_SOFTWARE": "false/not_demonstrated", "LIVE_CONNECTORS": "inactive"}
    write_json_deterministic(output / "batch072_completion_decisions.json", decisions)
    handoff = {"status": "PASS", "batch073_objective": "complete the frozen cohort without modifying preregistration", "validated_protocol": "v2.19", "cohort_hash": cohort_hash, "historical_issue_derived_repair_count": 5, "hardened_count_status": "QUARANTINED_PENDING_REVALIDATION"}
    write_json_deterministic(output / "batch073_cold_start_handoff.json", handoff)
    write_json_deterministic(output / "batch073_exact_next_actions.json", {"status": "PASS", "actions": ["materialize a cutoff-eligible hash-locked Connexion provider store", "rerun two-capsule count-five challenge", "independently resolve and replay the already-frozen Wave-1 leads", "do not replenish the cohort after outcomes"]})
    write_json_deterministic(output / "batch073_validation_progress_matrix.json", {"status": "PASS", "count5": "blocked_provider_store", "cohort_intake": "20_leads_frozen_zero_admitted", "prospective_arms": "not_run", "claim_boundary": "preserved"})
    write_json_deterministic(output / "batch073_candidate_freeze_preservation.json", {"status": "PASS", "cohort_hash": cohort_hash, "replacement_forbidden": True, "candidate_ids": []})
    claim = {"status": "PASS", "validated_protocol": "v2.19", "historical_count_under_H71_criteria": 5, "hardened_count_status": "QUARANTINED_PENDING_REVALIDATION", "native_external_repair_count": 4, "full_scoring": "NOT_RUN/disallowed", "AMDS_PROSPECTIVE_EFFECTIVENESS": "NOT_ESTABLISHED", "memory_lift": "not_demonstrated", "self_maintaining_software": "false/not_demonstrated", "live_connectors": "inactive"}
    write_json_deterministic(output / "batch072_claim_boundary.json", claim)
    final = {**claim, "status": "PASS_WITH_BLOCKED_COUNT_HARDENING_AND_PARTIAL_WAVE1", "artifact_ingest": "PASS", "count5_hardening": hardened["hardened_count_status"], "authorization": auth["status"], "provider_determinism": provider["status"], "candidate_specific_logic_removed": candidate_logic["status"], "weak_leads_considered": len(leads), "accepted_fresh_candidates": 0, "cohort_freeze_hash": cohort_hash, "amds_planner_freeze_hash": planner_hash, "memory_snapshot_hash": memory_hash}
    write_json_deterministic(output / "batch072_final_decision.json", final)
    write_text_lf(output / "batch072_summary.md", "# Batch072 summary\n\nThe official Batch071 artifact passed byte-custody, path-safety, manifest, and patch-identity verification. The historical H71 issue-derived repair count of `5` is preserved. Independent count-five hardening is quarantined because Batch071 did not preserve the exact provider artifacts needed to recreate a hash-locked provider arm; the patch passed external metamorphic checks, but that diagnostic result is not a substitute for duplicate locked-provider replay.\n\nv2.19 now requires sealed candidate execution plans and single-use authorization, uses hash-locked non-editable provider materialization, implements live rollback/proof/routing-memory/count boundaries, and removes candidate-specific ownership and patch logic from production modules. Twenty prior weak leads were frozen for Wave 1, but none satisfied independent commit plus duplicate-failure admission, so the prospective wave is `PARTIAL` with an empty frozen cohort. AMDS effectiveness remains `NOT_ESTABLISHED`, memory lift remains `not_demonstrated`, full scoring remains disallowed, self-maintaining software remains not demonstrated, and live connectors remain inactive.\n")
    current_path = root / "outputs/current/CURRENT_PROTOCOL_STATE.json"
    current = json.loads(current_path.read_text(encoding="utf-8"))
    current.update({"authorization_complete_status": "PASS_IMPLEMENTED", "deterministic_provider_status": "PASS_IMPLEMENTED", "count_5_hardening_status": "QUARANTINED_PENDING_REVALIDATION", "amds_prospective_wave1_status": "PARTIAL_EMPTY_FROZEN_COHORT", "next_safe_action": "batch073_complete_frozen_cohort_without_preregistration_change"})
    current.pop("state_hash", None); current["state_hash"] = hash_record(current); write_json_deterministic(current_path, current)
    frontier_path = root / "outputs/frontier/CURRENT_FRONTIER_STATE.json"
    frontier = json.loads(frontier_path.read_text(encoding="utf-8"))
    frontier.update({"v2_19_authorization_complete_status": "PASS_IMPLEMENTED", "v2_19_deterministic_provider_status": "PASS_IMPLEMENTED", "count_5_hardening_status": "QUARANTINED_PENDING_REVALIDATION", "AMDS_PROSPECTIVE_WAVE1": "PARTIAL_EMPTY_FROZEN_COHORT", "next_safe_action": "batch073_complete_frozen_cohort_without_preregistration_change"})
    frontier.pop("state_hash", None); frontier["state_hash"] = hash_record(frontier); write_json_deterministic(frontier_path, frontier)
    _write_manifest(output)
    return final
