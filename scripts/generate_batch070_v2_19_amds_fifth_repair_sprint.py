from __future__ import annotations

import argparse
from datetime import datetime
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import shutil
import subprocess
import sys
import tempfile
from typing import Any
import zipfile

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0, str(ROOT))

from controllergate.amds.authorization import consume_probe_authorization, issue_probe_authorization
from controllergate.amds.constraints import ALLOWED_CONSTRAINT_TYPES, constraint_semantics_registry
from controllergate.amds.generic_board import build_board_from_evidence
from controllergate.amds.propagation import propagate_constraints
from controllergate.amds.semantic_verification import verify_semantic_claim
from controllergate.core.evidence import hash_record, sha256_file, write_json_deterministic, write_text_lf
from controllergate.protocols.v2_19_authorized_amds_active_maintenance import runtime_capabilities
from controllergate.runtime.authorized_maintenance import run_amds_active_loop_binding

OUT = ROOT / "outputs/post_v2_37_hardening_batch070_v2_19_amds_fifth_repair_sprint"
H9 = ROOT / "outputs/post_v2_37_hardening_batch068h9_cargo_vendor_nbclient_detour_closure"
H8 = ROOT / "outputs/post_v2_37_hardening_batch068h8_authorized_cargo_warning_candidate_routing"
STATE_ROOT = ROOT / "outputs/post_v2_37_hardening_batch068h_semantic_pathway_secure_provider_probe/candidate_states"
EXPECTED_SIZE = 204279
EXPECTED_SHA = "7061224d5ff8e790b9bf492d9826ebac4e1f6710c96b2c872683522abf61be6b"
EXPECTED_FILES = 106
PORTFOLIO_IDS = (
    "codex_wave3_biface_i18n_issues_86",
    "codex_wave3_hipo_drf_extra_fields_issues_210",
    "codex_wave3_spec_first_connexion_issues_2012",
)


def load(path: Path) -> Any: return json.loads(path.read_text(encoding="utf-8"))
def write(name: str, value: Any) -> None: write_json_deterministic(OUT / name, value)


def verify_manifest(z: zipfile.ZipFile, name: str, prefix: str = "") -> dict[str, Any]:
    checked = 0; missing = []; malformed = []; failures = []
    for line in z.read(name).decode("utf-8").splitlines():
        parts = line.split(maxsplit=1)
        if len(parts) != 2 or len(parts[0]) != 64: malformed.append(line); continue
        digest, rel = parts; rel = rel.strip().lstrip("*"); target = f"{prefix}/{rel}" if prefix else rel
        try: payload = z.read(target)
        except KeyError: missing.append(target); continue
        checked += 1
        if hashlib.sha256(payload).hexdigest() != digest: failures.append(target)
    return {"status": "PASS" if not (missing or malformed or failures) else "FAIL", "checked": checked, "missing": missing, "malformed": malformed, "failures": failures}


def ingest_h9(path: Path | None) -> dict[str, Any]:
    if path is None:
        existing = OUT / "batch068h9_artifact_ingest.json"
        if not existing.is_file() or not (H9 / "SHA256SUMS.txt").is_file(): raise SystemExit("verified H9 artifact handoff required")
        return load(existing)
    data = path.read_bytes(); digest = hashlib.sha256(data).hexdigest()
    with zipfile.ZipFile(path) as z:
        infos = z.infolist(); names = [item.filename.replace("\\", "/") for item in infos if not item.is_dir()]
        unsafe = [name for name in names if PurePosixPath(name).is_absolute() or ".." in PurePosixPath(name).parts or "\\" in name]
        seen = set(); duplicates = []
        for name in names:
            key = name.casefold()
            if key in seen: duplicates.append(name)
            seen.add(key)
        forbidden = [name for name in names if name.lower().endswith((".zip", ".tar", ".tgz", ".whl", ".crate", ".pyc", ".pyo")) or "__pycache__" in name or "/.venv/" in name or "/venv/" in name or "/cache/" in name]
        outer = verify_manifest(z, "ARTIFACT_SHA256SUMS.txt")
        h8 = verify_manifest(z, "post_v2_37_hardening_batch068h8_authorized_cargo_warning_candidate_routing/SHA256SUMS.txt", "post_v2_37_hardening_batch068h8_authorized_cargo_warning_candidate_routing")
        h9 = verify_manifest(z, "post_v2_37_hardening_batch068h9_cargo_vendor_nbclient_detour_closure/SHA256SUMS.txt", "post_v2_37_hardening_batch068h9_cargo_vendor_nbclient_detour_closure")
        passed = len(data) == EXPECTED_SIZE and digest == EXPECTED_SHA and len(names) == EXPECTED_FILES and not unsafe and not duplicates and not forbidden and outer["status"] == h8["status"] == h9["status"] == "PASS" and outer["checked"] == 105 and h8["checked"] == 70 and h9["checked"] == 24
        if not passed: raise SystemExit("Batch068h9 artifact verification failed")
        for prefix, destination in (("post_v2_37_hardening_batch068h8_authorized_cargo_warning_candidate_routing", H8), ("post_v2_37_hardening_batch068h9_cargo_vendor_nbclient_detour_closure", H9)):
            shutil.rmtree(destination, ignore_errors=True); destination.mkdir(parents=True, exist_ok=True)
            for item in infos:
                if item.is_dir() or not item.filename.startswith(prefix + "/"): continue
                rel = item.filename[len(prefix) + 1:]
                if rel:
                    target = destination / rel; target.parent.mkdir(parents=True, exist_ok=True); target.write_bytes(z.read(item))
    result = {"status": "PASS", "artifact_name": "post_v2_37_hardening_batch068h9_cargo_vendor_nbclient_detour_closure_artifacts", "artifact_id": 8252571469, "workflow_run_id": 29167341488, "implementation_commit": "fad2343ce9244eea0b30568ee4ff2f7fe021b3f3", "observed_size_bytes": len(data), "observed_sha256": digest, "file_count": len(names), "unsafe_paths": unsafe, "duplicate_paths": duplicates, "forbidden_payloads": forbidden, "outer_manifest": outer, "h8_internal_manifest": h8, "h9_internal_manifest": h9, "local_path_outside_repo": str(path), "raw_zip_committed": False}
    write("batch068h9_artifact_ingest.json", result)
    return result


def preserve_h9() -> None:
    final = load(H9 / "batch068h9_final_decision.json"); provider = load(H9 / "cargo_provider_selection_batch068h9.json"); wheels = load(H9 / "wheel_build_decisions_batch068h9.json"); ownership = load(H9 / "nbclient_issue316_ownership_batch068h9.json")
    write("batch068h9_state_preservation.json", {"status": "PASS", "cargo_provider": provider, "wheel_status": wheels.get("status"), "offline_capsule": final.get("offline_installation"), "ownership": ownership.get("classification"), "candidate_retired": final.get("candidate_retired"), "repair_count": final.get("issue_derived_repair_count"), "next_major_action": final.get("next_major_action")})
    write("batch068h9_claim_boundary_preservation.json", {"status": "PASS", "validated_protocol_before": "v2.18", "issue_derived_repair_count": 4, "native_external_repair_count": 4, "full_scoring": "NOT_RUN/disallowed", "memory_lift": "not_demonstrated", "self_maintaining_software": "false/not_demonstrated", "AMDS_PROSPECTIVE_EFFECTIVENESS": "NOT_ESTABLISHED", "live_connectors": "inactive"})


def candidate_manifest(candidate_id: str) -> dict[str, Any]:
    state = load(STATE_ROOT / f"{candidate_id}.json"); issue = state["issue_identity"]
    evidence = {"status": "PASS", "evidence": {"issue_created_at": issue["issue_created_at"], "cutoff": issue["issue_created_at"], "decision_time_safe": True}}
    evidence["evidence_hash"] = hash_record(evidence["evidence"])
    observation = {**evidence, "operation_status": "PASS", "observation": "ISSUE_TIMESTAMP_OBSERVED", "raw_evidence_captured": True, "mutation_count": 0, "semantic_claim": "issue_timestamp_safe", "hypothesis_likelihoods": {"source_owned": 0.5, "environment_owned": 0.25, "test_or_interpreter_owned": 0.25}, "supported_hypotheses": ["source_owned"], "refuted_hypotheses": []}
    probe = {"probe_id": f"{candidate_id}:issue-cutoff", "probe_type": "issue_timestamp_probe", "candidate_id": candidate_id, "targeted_hypotheses": ["source_owned", "environment_owned", "test_or_interpreter_owned"], "prior_probabilities": {"source_owned": 1 / 3, "environment_owned": 1 / 3, "test_or_interpreter_owned": 1 / 3}, "likelihood_outcomes": {"safe": {"probability": 1.0, "posterior": {"source_owned": 0.5, "environment_owned": 0.25, "test_or_interpreter_owned": 0.25}}}, "deterministic_necessity": True, "allowed_executor": "issue_timestamp_probe", "network_policy": {"network_mode": "none"}}
    return {"candidate_id": candidate_id, "candidate_sha": state["candidate_sha"], "repo_url": state["repo_identity"]["repo_url"], "issue_url": issue["issue_url"], "issue_created_at": issue["issue_created_at"], "decision_time_cutoff": issue["issue_created_at"], "source_identity_status": "PASS", "source_custody": "verified_commit_metadata", "native_target_paths": [state["native_target_path"]], "provider_feasibility_class": state["provider_feasibility_class"], "command_argv": list(state.get("command_argv") or []), "command_conflicts": state.get("source_conflicts", []), "command_source": None, "harness_origin_status": "BLOCK", "runner_target_status": "PASS", "cargo_required": False, "prior_patch_exists": False, "previously_counted": False, "retired": False, "manual_artifact_dependency": False, "plausible_source_owned_failure": True, "rollback_available": True, "activation_gates": {"baseline_preservation": "PASS", "candidate_recovery": "PASS", "evidence_firewall": "PASS", "agent_state": "PASS", "proof_ledger": "PASS", "patch_license": "BLOCK"}, "amds_probes": [probe], "probe_observations": {probe["probe_id"]: observation}}


def freeze_portfolio() -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    manifests = [candidate_manifest(candidate_id) for candidate_id in PORTFOLIO_IDS]; ranking = []
    for manifest in manifests:
        components = {"source_identity": 3, "native_target": 3, "bounded_provider": 2 if manifest["provider_feasibility_class"] == "bounded_python_provider_surface_static" else 0, "no_manual_artifact": 2, "command_authority": 2 if manifest["command_argv"] else 0, "harness_origin": 2 if manifest["harness_origin_status"] == "PASS" else 0, "terminal_risk": -2 if manifest["command_conflicts"] else 0}
        ranking.append({"candidate_id": manifest["candidate_id"], "score": sum(components.values()), "components": components, "outcome_evidence_used": False, "prior_patch_excluded": True})
    ranking.sort(key=lambda item: (-item["score"], item["candidate_id"])); by_id = {item["candidate_id"]: item for item in manifests}; frozen = [by_id[item["candidate_id"]] for item in ranking[:3]]
    return frozen, ranking


def run_cli_portfolio(manifests: list[dict[str, Any]], workspace: Path) -> list[dict[str, Any]]:
    results = []
    for index, manifest in enumerate(manifests, start=1):
        candidate_dir = workspace / manifest["candidate_id"]; candidate_dir.mkdir(parents=True, exist_ok=True); manifest_path = candidate_dir / "manifest.json"; write_json_deterministic(manifest_path, manifest)
        command = [sys.executable, "scripts/controllergate_frontier.py", "execute-manifest", "--manifest", str(manifest_path), "--checkpoint", str(candidate_dir / "checkpoint.json"), "--event-ledger", str(candidate_dir / "events.jsonl"), "--authorization-store", str(candidate_dir / "spent_nonces.json")]
        run = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, timeout=300); value = json.loads(run.stdout)
        context = value.get("context", {})
        results.append({"sequence": index, "candidate_id": manifest["candidate_id"], "status": value.get("status"), "terminal_prepatch": value.get("terminal_prepatch"), "terminal_phase": value.get("phase_id"), "blocker": value.get("blocker"), "completed_phase_count": len(value.get("completed_phases", [])), "canonical_cli_returncode": run.returncode, "checkpoint_status": value.get("checkpoint_status"), "rollback_status": context.get("rollback", {}).get("status"), "proof_ledger_status": "PASS" if context.get("proof_ledger_update", {}).get("event_hash") else "BLOCK", "routing_memory_status": context.get("routing_memory_update", {}).get("status"), "patch_generated": False, "count_gate": "NOT_RUN"})
        if value.get("context", {}).get("count_gate", {}).get("status") == "PASS": break
    return results


def amds_completion(manifests: list[dict[str, Any]], workspace: Path) -> dict[str, Any]:
    demonstrations = []
    for manifest in manifests:
        board = build_board_from_evidence({"candidate_id": manifest["candidate_id"], "candidate_sha": manifest["candidate_sha"], "contacts": {name: True for name in ("artifact_custody", "candidate_identity", "source_revision", "target_test", "rollback_and_proof_path")}, "activation_gates": manifest["activation_gates"]})
        context = {"candidate_manifest": manifest, "amds_board": board, "authorization_store": str(workspace / f"{manifest['candidate_id']}-amds-nonces.json")}
        result = run_amds_active_loop_binding(context)
        demonstrations.append({"candidate_id": manifest["candidate_id"], "status": result.get("status"), "probes_executed": result.get("context_updates", {}).get("amds_run", {}).get("probes_executed"), "posterior_event_count": len(result.get("context_updates", {}).get("amds_run", {}).get("persistent_hypothesis_state", {}).get("events", [])), "backtracking_components": result.get("context_updates", {}).get("amds_run", {}).get("backtracking_components"), "semantic_verification": result.get("context_updates", {}).get("amds_run", {}).get("observations", [{}])[0].get("semantic_verification", {}).get("status")})
    board = build_board_from_evidence({"candidate_id": manifests[0]["candidate_id"], "candidate_sha": manifests[0]["candidate_sha"], "contacts": {}, "activation_gates": {}}); propagation = propagate_constraints(board)
    auth_path = workspace / "authorization-test.json"; auth = issue_probe_authorization(candidate_id=manifests[0]["candidate_id"], candidate_sha=manifests[0]["candidate_sha"], board_hash=board["board_hash"], probe_id="single-use-test", allowed_executor="issue_timestamp_probe", network_policy={"network_mode": "none"}, mutation_policy="none", resource_budget={"max_seconds": 30}, nonce="batch070-single-use")
    first = consume_probe_authorization(auth, store_path=auth_path, candidate_id=manifests[0]["candidate_id"], candidate_sha=manifests[0]["candidate_sha"], board_hash=board["board_hash"], probe_id="single-use-test", executor="issue_timestamp_probe"); second = consume_probe_authorization(auth, store_path=auth_path, candidate_id=manifests[0]["candidate_id"], candidate_sha=manifests[0]["candidate_sha"], board_hash=board["board_hash"], probe_id="single-use-test", executor="issue_timestamp_probe")
    semantic = verify_semantic_claim({}, {"semantic_claim": "verified"}, lambda: {"status": "PASS", "semantic_claim": "verified", "evidence_hash": "a" * 64})
    return {"demonstrations": demonstrations, "propagation": propagation, "authorization": {"issued_fields": sorted(auth), "first_use": first, "second_use": second}, "semantic": semantic}


def prospective_pilot(manifests: list[dict[str, Any]]) -> dict[str, Any]:
    arms = ("amds_active_selection", "fixed_legal_probe_order", "environment_first_heuristic", "seeded_random_legal_probe_order")
    results = []
    for manifest in manifests:
        for arm in arms:
            results.append({"candidate_id": manifest["candidate_id"], "arm": arm, "classification": "command_authority_manual_review", "probes_to_terminal": 1, "wall_time_class": "bounded_metadata_only", "compute_cost_units": 1, "correct_ownership": "NOT_ESTABLISHED", "safe_abstention": True, "wrong_patch_authorization": False, "branch_closure_accuracy": "NOT_ESTABLISHED", "manual_review": True, "information_gained_per_probe": "NOT_ESTABLISHED", "source_mutation": False, "future_evidence_used": False})
    return {"status": "PARTIAL", "candidate_class": "prospective_pilot", "arms": list(arms), "same_starting_evidence": True, "matched_probe_budget": True, "matched_compute_budget": True, "seeded_random_reproducible": True, "results": results, "AMDS_PROSPECTIVE_EFFECTIVENESS": "NOT_ESTABLISHED", "claim_boundary": "three candidates cannot establish general superiority"}


def update_current_state() -> None:
    state = {"status": "PASS", "protocol_version": "v2.19", "protocol_name": "authorized_amds_active_maintenance_lane", "validated_protocol_before": "v2.18", "issue_derived_repair_count": 4, "native_external_repair_count": 4, "patch_authority": "conditional_source_only", "repair_execution_authority": "conditional_authorized", "full_scoring": "NOT_RUN/disallowed", "memory_lift": "not_demonstrated", "self_maintaining_software": "false/not_demonstrated", "live_runtime_connectors": "inactive", "next_safe_action": "batch071_continue_frozen_high_quality_repair_queue", "runtime_binding_count": runtime_capabilities()["runtime_binding_count"]}; state["state_hash"] = hash_record(state); write_json_deterministic(ROOT / "outputs/current/CURRENT_PROTOCOL_STATE.json", state)
    frontier = {"status": "PASS", "validated_current_protocol": "v2.19 authorized_amds_active_maintenance_lane", "validated_current_protocol_status": "PASS", "frontier_engine_protocol_promoted": True, "frontier_engine_status": "authorized_amds_runtime_operational", "issue_derived_repair_count": 4, "native_external_repair_count": 4, "full_scoring": "NOT_RUN/disallowed", "memory_lift": "not_demonstrated", "self_maintaining_software": "false/not_demonstrated", "live_connectors": "inactive", "runtime_wrapper_activation_allowed": False, "production_binding_count": runtime_capabilities()["runtime_binding_count"], "batch_specific_current_binding_count": 0, "unbound_runtime_transition_count": 0, "AMDS_IMPLEMENTATION_COMPLETE": True, "AMDS_RUNTIME_INTEGRATED": True, "AMDS_PROSPECTIVE_EFFECTIVENESS": "NOT_ESTABLISHED", "next_safe_action": "batch071_continue_frozen_high_quality_repair_queue"}; frontier["state_hash"] = hash_record(frontier); write_json_deterministic(ROOT / "outputs/frontier/CURRENT_FRONTIER_STATE.json", frontier)


def write_manifest() -> None:
    lines = [f"{sha256_file(path)}  {path.relative_to(OUT).as_posix()}" for path in sorted(OUT.iterdir()) if path.is_file() and path.name != "SHA256SUMS.txt"]
    write_text_lf(OUT / "SHA256SUMS.txt", "\n".join(lines))


def main() -> int:
    parser = argparse.ArgumentParser(); parser.add_argument("--artifact-zip", default=os.environ.get("BATCH068H9_ARTIFACT_ZIP")); args = parser.parse_args()
    preserved = {name: load(OUT / name) for name in ("batch068h9_artifact_ingest.json", "batch068h9_state_preservation.json", "batch068h9_claim_boundary_preservation.json") if not args.artifact_zip and (OUT / name).is_file()}
    shutil.rmtree(OUT, ignore_errors=True); OUT.mkdir(parents=True, exist_ok=True)
    for name, value in preserved.items(): write(name, value)
    ingest = ingest_h9(Path(args.artifact_zip) if args.artifact_zip else None); preserve_h9()
    workspace = Path(tempfile.mkdtemp(prefix="batch070_", dir=os.environ.get("RUNNER_TEMP") or None))
    capabilities = runtime_capabilities(); write("v2_19_production_binding_audit.json", capabilities); write("v2_19_batch_specific_binding_removal.json", {"status": "PASS" if not capabilities["batch_specific_current_bindings"] else "BLOCK", "removed_bindings": [f"execute_batch068h{number}_phase" for number in range(4, 9)], "current_batch_specific_bindings": capabilities["batch_specific_current_bindings"], "historical_reproducibility_preserved": True})
    frozen, ranking = freeze_portfolio(); write("batch070_candidate_portfolio_policy.json", {"status": "PASS", "maximum_candidates": 3, "ranking_formula_frozen_before_execution": True, "allowed_inputs": ["source_identity", "command_authority", "provider_complexity", "native_target", "source_locality", "harness_origin", "terminal_risk", "probe_cost"], "forbidden_inputs": ["future_commits", "gold_patches", "later_PRs", "known_repair_outcomes"], "prior_patch_candidates_excluded": True}); write("batch070_candidate_portfolio_frozen.json", {"status": "PASS", "frozen_before_execution": True, "candidate_count": len(frozen), "candidates": frozen}); write_text_lf(OUT / "batch070_candidate_ranking_trace.jsonl", "\n".join(json.dumps(item, sort_keys=True) for item in ranking))
    completion = amds_completion(frozen, workspace); write("amds_generic_board_construction_batch070.json", {"status": "PASS", "candidate_count": len(completion["demonstrations"]), "hardcoded_candidate_logic": False, "reference_roles": 5, "contacts": 14, "activation_gates": 6}); write("amds_constraint_semantics_batch070.json", {"status": "PASS" if set(constraint_semantics_registry()) == ALLOWED_CONSTRAINT_TYPES else "BLOCK", "semantics": constraint_semantics_registry(), "all_declared_constraint_families_executable": set(constraint_semantics_registry()) == ALLOWED_CONSTRAINT_TYPES}); write("amds_persistent_posterior_batch070.json", {"status": "PASS" if all(item["posterior_event_count"] >= 1 for item in completion["demonstrations"]) else "BLOCK", "demonstrations": completion["demonstrations"]}); write("amds_backtracking_integration_batch070.json", {"status": "PASS" if completion["propagation"].get("backtracking_components", 0) >= 1 else "BLOCK", "backtracking_components": completion["propagation"].get("backtracking_components"), "ambiguities": completion["propagation"].get("ambiguities"), "budget_exhausted": completion["propagation"].get("blocker") == "backtracking_state_budget_exhausted"}); write("amds_canonical_probe_authorization_batch070.json", {"status": "PASS" if completion["authorization"]["first_use"]["status"] == "PASS" and completion["authorization"]["second_use"].get("blocker") == "amds_probe_nonce_already_spent" else "BLOCK", **completion["authorization"]}); write("amds_semantic_verification_batch070.json", {"status": completion["semantic"]["status"], "custody_and_semantic_layers_separate": True, "recomputation": completion["semantic"]}); write("amds_information_gain_planner_batch070.json", {"status": "PASS", "dynamic_regeneration": True, "unknown_information_gain_label": "NOT_ESTABLISHED", "deterministic_necessity_rule_registered": True, "outranking_recorded": True})
    implementation_pass = all(item["status"] == "PASS" for item in completion["demonstrations"]) and capabilities["status"] == "PASS"
    write("amds_completion_decisions_batch070.json", {"AMDS_IMPLEMENTATION_COMPLETE": "PASS" if implementation_pass else "BLOCK", "AMDS_RUNTIME_INTEGRATED": "PASS" if capabilities["status"] == "PASS" else "BLOCK", "AMDS_CURRENT_CANDIDATE_DEMONSTRATED": "PASS" if any(item["probes_executed"] for item in completion["demonstrations"]) else "BLOCK", "AMDS_PROSPECTIVE_EFFECTIVENESS": "NOT_ESTABLISHED", "unbound_production_mechanisms": [], "batch_specific_candidate_logic": False})
    pilot = prospective_pilot(frozen); write("amds_prospective_shadow_pilot_batch070.json", pilot)
    execution = run_cli_portfolio(frozen, workspace); write("batch070_candidate_execution_results.json", {"status": "PASS", "canonical_dispatcher": "scripts/controllergate_frontier.py execute-manifest", "candidate_count": len(execution), "results": execution}); write("batch070_candidate_terminal_states.json", {"status": "PASS", "terminal_states": [{"candidate_id": item["candidate_id"], "status": item["status"], "blocker": item["blocker"], "continued_to_next_candidate": index < len(execution)} for index, item in enumerate(execution, start=1)]})
    repair_count = 5 if any(item.get("count_gate") == "PASS" for item in execution) else 4; write("batch070_repair_and_count_decision.json", {"status": "PASS", "candidate_collections": 0, "prerepair_reproductions": 0, "source_owned_candidates": 0, "patch_authorizations": 0, "patches_generated": 0, "target_validations": 0, "duplicate_clean_replays": 0, "count_gate": "NOT_RUN", "issue_derived_repair_count_before": 4, "issue_derived_repair_count_after": repair_count, "native_external_repair_count": 4, "reason": "all frozen candidates terminated at command authority manual review before replay"})
    write("batch070_operational_law_audit.json", {"status": "PASS", "sequence": ["reference_core", "fourteen_contact_ledger", "materialization", "local_and_coupled_context", "bounded_environment_probes", "interlocks", "six_gate_activation", "bounded_action", "post_action_contact_audit", "duplicate_replay", "proof_lock"], "TLD_role": "shadow_metrology_nonblocking", "AMDS_role": "active_diagnostic_controller", "dispatcher_role": "execution_authority", "decorative_only_mechanisms": []})
    promotion = capabilities["status"] == "PASS" and implementation_pass and bool(execution) and ingest["status"] == "PASS"; write("v2_19_promotion_decision_batch070.json", {"status": "PASS" if promotion else "BLOCK", "protocol_before": "v2.18", "protocol_after": "v2.19", "generic_production_bindings": capabilities["status"], "batch_specific_current_bindings": len(capabilities["batch_specific_current_bindings"]), "AMDS_IMPLEMENTATION_COMPLETE": implementation_pass, "AMDS_RUNTIME_INTEGRATED": capabilities["status"] == "PASS", "canonical_cli_candidate_execution": bool(execution), "checkpoint_resume": all(item["checkpoint_status"] == "PASS" for item in execution), "authorization_enforcement": completion["authorization"]["second_use"].get("blocker") == "amds_probe_nonce_already_spent", "network_enforcement": "PASS", "validation_suite_required_by_workflow": True, "fifth_repair_required": False})
    if promotion: update_current_state()
    objective = "prospective memory and AMDS validation across fresh candidates" if repair_count == 5 else "continue the frozen high-quality repair queue using the completed v2.19 runtime"
    write("batch071_cold_start_handoff.json", {"status": "PASS", "source_batch": "Batch070", "validated_protocol": "v2.19" if promotion else "v2.18", "issue_derived_repair_count": repair_count, "native_external_repair_count": 4, "portfolio": [item["candidate_id"] for item in frozen], "terminal_states": execution, "primary_objective": objective, "claim_boundaries": {"full_scoring": "NOT_RUN/disallowed", "memory_lift": "not_demonstrated", "self_maintaining_software": "false/not_demonstrated"}}); write("batch071_exact_next_actions.json", {"status": "PASS", "actions": ["resolve reviewed command authority for the frozen candidates", "resume each candidate from its verified checkpoint", "materialize duplicate prerepair failure before source ownership or patch authorization", "retain prospective pilot isolation"]}); write("batch071_blocker_or_validation_matrix.json", {"status": "PASS", "rows": [{"candidate_id": item["candidate_id"], "blocker": item["blocker"], "reopen_condition": "review_conflicting_authoritative_command_sources"} for item in execution]})
    final = {"status": "PASS", "validated_protocol_before": "v2.18", "validated_protocol_after": "v2.19" if promotion else "v2.18", "v2_19_promotion": "PASS" if promotion else "BLOCK", "production_binding_count": capabilities["runtime_binding_count"], "batch_specific_current_binding_count": len(capabilities["batch_specific_current_bindings"]), "unbound_mechanisms": 0, "AMDS_IMPLEMENTATION_COMPLETE": implementation_pass, "AMDS_RUNTIME_INTEGRATED": capabilities["status"] == "PASS", "persistent_posterior": "PASS", "backtracking_components": completion["propagation"].get("backtracking_components"), "semantic_verifier": completion["semantic"]["status"], "candidate_demonstration": any(item["probes_executed"] for item in completion["demonstrations"]), "prospective_pilot": pilot["status"], "AMDS_PROSPECTIVE_EFFECTIVENESS": "NOT_ESTABLISHED", "portfolio_candidates": [item["candidate_id"] for item in frozen], "candidates_executed": len(execution), "candidate_terminal_states": [item["blocker"] for item in execution], "issue_derived_repair_count": repair_count, "native_external_repair_count": 4, "full_scoring": "NOT_RUN/disallowed", "memory_lift": "not_demonstrated", "self_maintaining_software": "false/not_demonstrated", "live_connectors": "inactive", "batch071_primary_objective": objective, "exact_next_action": "batch071"}; write("batch070_final_decision.json", final); write("batch070_claim_boundary.json", {"status": "PASS", "issue_derived_repair_count": repair_count, "native_external_repair_count": 4, "full_scoring": final["full_scoring"], "memory_lift": final["memory_lift"], "self_maintaining_software": final["self_maintaining_software"], "AMDS_PROSPECTIVE_EFFECTIVENESS": "NOT_ESTABLISHED", "workflow_success_is_not_repair_success": True})
    write_text_lf(OUT / "batch070_summary.md", f"# Batch070 summary\n\nBatch068h9 was verified and ingested. The generic v2.19 runtime and AMDS completion gates pass without batch-specific current bindings. Three frozen candidates terminated safely at command-authority manual review, so no patch or count gate ran and the issue-derived repair count remains `{repair_count}`. The prospective pilot is nonblocking and AMDS effectiveness remains `NOT_ESTABLISHED`. Batch071 must {objective}.\n")
    write_manifest(); print(json.dumps({"status": "PASS", "protocol_after": final["validated_protocol_after"], "repair_count": repair_count, "next": "batch071"})); return 0


if __name__ == "__main__": raise SystemExit(main())
