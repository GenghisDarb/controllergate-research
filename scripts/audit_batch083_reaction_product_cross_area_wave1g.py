from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
REQUIRED=["batch082_ingest_preservation.json","batch082_claim_preservation.json","batch082_count_preservation.json","batch082_main_artifact_manifest_reverification.json","batch083_batch082_artifact_byte_binding.jsonl","batch083_batch082_artifact_verification_summary.json","batch083_reaction_contracts.jsonl","batch083_reaction_ledger.jsonl","batch083_output_token_registry.jsonl","batch083_failed_reaction_registry.jsonl","batch083_translocation_ledger.jsonl","batch083_cycle_guard_decisions.jsonl","batch083_reference_anchors.json","batch083_contact_registry.json","batch083_repair_regulator_gate.json","batch083_contact_coherence_matrix.json","batch083_openbb_provider_v4_result.json","batch083_poetry_provider_v4_result.json","batch083_provider_dependency_graphs.jsonl","batch083_provider_state_ledger.jsonl","batch083_provider_install_results.jsonl","batch083_provider_function_probes.jsonl","batch083_provider_capsule_registry.jsonl","batch083_openapi_rooted_reference_closure.json","batch083_network_compartment_execution.json","batch083_openbb_duplicate_reproduction.json","batch083_poetry_duplicate_reproduction.json","batch083_candidate_failure_signatures.jsonl","batch083_admitted_cohort_freeze.json","batch083_ast_contact_domain_results.json","batch083_prospective_diagnostic_comparison.json","batch083_matched_nulls.json","batch083_blinded_ground_truth.json","batch083_conditional_repair_authorization.json","batch083_conditional_repair_results.json","batch083_duplicate_replay_proof_count_canary.json","batch083_historical_amds_blind_challenge.json","batch083_routing_memory_counterfactual.json","batch083_historical_canary_health_rollback.json","batch083_offline_connector_canary.json","batch083_public_readonly_connector_pilot.json","batch083_product_alpha_cycle.json","batch083_independent_critic.json","batch083_capability_maturity_before.json","batch083_capability_maturity_after.json","batch083_capability_maturity_delta.json","batch083_cross_area_advancement_contract.json","batch083_cross_area_advancement_results.json","batch083_zero_gain_prevention_audit.json","batch083_final_claim_boundary.json","batch083_final_state.json","SHA256SUMS.txt"]


def read(p:Path):return json.loads(p.read_text(encoding="utf-8"))
def main()->int:
 p=argparse.ArgumentParser();p.add_argument("--out",required=True);a=p.parse_args();o=Path(a.out);errors=[f"missing:{name}" for name in REQUIRED if not (o/name).is_file()]
 contract=read(ROOT/"configs/batch083_prompt_contract.json")
 if contract.get("prompt_id")!="CG-BATCH083-INTEGRATED-REACTION-PRODUCT-ADVANCEMENT-2026-07-14-V1" or contract.get("prompt_sentinel")!="BEGIN_BATCH083_INTEGRATED_CONTINUATION":errors.append("prompt_identity")
 if not errors:
  final=read(o/"batch083_final_state.json");claim=read(o/"batch083_final_claim_boundary.json");zero=read(o/"batch083_zero_gain_prevention_audit.json");critic=read(o/"batch083_independent_critic.json");matrix=read(o/"batch083_contact_coherence_matrix.json");amds=read(o/"batch083_historical_amds_blind_challenge.json");canary=read(o/"batch083_historical_canary_health_rollback.json");product=read(o/"batch083_product_alpha_cycle.json");offline=read(o/"batch083_offline_connector_canary.json")
  if final.get("batch082_rerun") or not final.get("canonical_engine_invoked"):errors.append("stale_or_noncanonical")
  if matrix.get("pair_count")!=196:errors.append("contact_matrix")
  if amds.get("episode_count",0)<8 or amds.get("arms_per_episode")!=4:errors.append("amds_depth")
  if canary.get("rollback_drills",0)<2 or canary.get("health_windows",0)<2:errors.append("deployment_depth")
  if product.get("resume",{}).get("status")!="CONTROLLED_PRODUCT_ALPHA_CYCLE_PASS":errors.append("product_cycle")
  if offline.get("write_authority") is not False:errors.append("connector_write")
  providers=[read(o/f"batch083_{name}_provider_v4_result.json") for name in ("openbb","poetry")]
  if any(row.get("provider_execution_ready") and (row["dependency_graph"].get("missing_runtime_dependencies") or len(row.get("offline_installs",[]))!=2) for row in providers):errors.append("false_provider_ready")
  reproductions=[read(o/f"batch083_{name}_duplicate_reproduction.json") for name in ("openbb","poetry")]
  if any(row.get("duplicate_failure_admitted") and not (row.get("status")=="CANDIDATE_FAILURE_REPRODUCED" and len(row.get("replays",[]))==2 and all(replay.get("incident_reproduced") for replay in row["replays"])) for row in reproductions):errors.append("false_candidate_admission")
  nulls=read(o/"batch083_matched_nulls.json")
  if nulls.get("eligible") and (nulls.get("null_count")!=38 or nulls.get("actual_probe_count",0)<=0):errors.append("matched_null_depth")
  repair=read(o/"batch083_conditional_repair_results.json")
  if repair.get("repair_attempt_count",0)>2 or repair.get("memory_patch_content_used") is not False:errors.append("repair_boundary")
  if critic.get("status")!="PASS":errors.append("critic")
  if zero.get("status")!="PASS":errors.append("zero_gain")
  if claim.get("current_protocol")!="v2.19" or claim.get("full_scoring")!="NOT_RUN/disallowed" or claim.get("self_maintaining_software")!="false/not demonstrated":errors.append("claim_boundary")
  sums={line.split(maxsplit=1)[1].lstrip(" *"):line.split(maxsplit=1)[0] for line in (o/"SHA256SUMS.txt").read_text(encoding="utf-8").splitlines() if line.strip()}
  if any(name not in sums for name in REQUIRED if name!="SHA256SUMS.txt"):errors.append("required_manifest_coverage")
  for rel,digest in sums.items():
   path=o/rel
   if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest()!=digest:errors.append(f"manifest:{rel}")
 result={"status":"PASS" if not errors else "FAIL","errors":errors,"required_file_count":len(REQUIRED)};print(json.dumps(result,sort_keys=True));return 0 if not errors else 1
if __name__=="__main__":raise SystemExit(main())
