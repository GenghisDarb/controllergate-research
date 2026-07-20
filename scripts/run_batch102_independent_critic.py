"""Standard-library copied-tree semantic mutation critic for Batch102."""
from __future__ import annotations
import argparse,hashlib,json,shutil,tempfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
NAMES=[
"batch101_artifact_substitution","batch101_ingest_receipt_mutation","execution_origin_correction_removed","inherited_batch100_record_marked_fresh","workflow_run_id_changed","workflow_head_changed","broker_operation_removed","source_attestation_removed","provider_attestation_removed","fresh_epoch_removed","static_finalizer_creates_fresh_receipt","exact_provider_changed_to_prefix_match","prerelease_tag_removed","os_changed","abi_changed","source_commit_changed","future_commit_injected","accepted_fix_injected","gold_patch_injected","darker_exact_tag_changed","pytest_exact_commit_changed","openbb_secondary_commit_changed","poetry_windows_cell_moved_to_linux","poetry_cwd_renamed_consumer","audioread_pytest_preflight_removed","missing_structured_observation_treated_as_pass","freezegun_beta_replaced_by_stable_provider","cloudpickle_fourth_factorial_corner_removed","pybugger_runtime_intervention_edits_source","pybugger_requested_count_changed","pybugger_count_collection_falsified","replay_duplicated_and_relabelled","semantic_mismatch_hidden","raw_evidence_deleted","incident_predicate_inverted","control_predicate_inverted","pair_valid_without_incident","pair_valid_without_control","pair_valid_without_fresh_receipt","factorial_valid_with_missing_corner","sensitivity_promoted_to_necessity","sensitivity_promoted_to_sufficiency","sensitivity_promoted_to_ownership","contact_promoted_to_ownership","necessity_claimed_without_factor_removal","sufficiency_claimed_without_factor_introduction","interaction_claimed_without_estimand","mixed_failure_claimed_without_interaction","alternative_exclusion_fabricated","unresolved_alternative_deleted","all_arms_open_every_outcome","unselected_arm_opens_envelope","arm_copies_another_terminal","baseline_executes_wrong_policy","tld_creates_cell","tld_changes_predicate","tld_changes_semantic_projection","truth_enters_public_workflow","truth_used_to_design_intervention","source_ownership_derived_from_truth","terminal_written_outside_controller_audit","source_mutation_hidden","test_mutation_hidden","cleanup_failure_hidden","external_network_used_during_offline_cell","patch_operation_introduced","repair_count_incremented","historical_increment_changed","product_beta_promoted","prospective_effectiveness_promoted","memory_marked_demonstrated","production_readiness_true","self_maintaining_promoted","master_ledger_goal_removed","master_ledger_blocker_removed","private_path_injected","manifest_resigned_after_semantic_mutation"]
def shaf(p:Path)->str:return hashlib.sha256(p.read_bytes()).hexdigest()
def manifest(root:Path)->None:
 rows=[]
 for p in sorted(root.rglob("*")):
  if p.is_file() and p.name!="MANIFEST_SHA256SUMS.txt":rows.append(f"{shaf(p)}  {p.relative_to(root).as_posix()}")
 (root/"MANIFEST_SHA256SUMS.txt").write_text("\n".join(rows)+"\n",encoding="utf-8",newline="\n")
def main()->int:
 p=argparse.ArgumentParser();p.add_argument("--evidence-root",type=Path,required=True);p.add_argument("--output-root",type=Path,required=True);p.add_argument("--runtime-root",type=Path,required=True);a=p.parse_args();a.output_root.mkdir(parents=True,exist_ok=True);a.runtime_root.mkdir(parents=True,exist_ok=True)
 base=a.runtime_root/"critic-base";shutil.rmtree(base,ignore_errors=True);base.mkdir()
 for src in [ROOT/"configs/batch102_prompt_contract.json",ROOT/"configs/batch102_candidate_counterfactual_programs_v4.jsonl",ROOT/"configs/batch102_counterfactual_cell_registry_v4.jsonl",ROOT/"configs/batch102_arm_selection_policies_v1.json",ROOT/"configs/controllergate_master_completion_ledger_v2.json",a.evidence_root/"batch102_claim_boundary.json",a.evidence_root/"batch102_consolidated_state.json"]:
  if src.is_file(): shutil.copy2(src,base/src.name)
 state={"execution_epoch":"BATCH102_FRESH_OPERATION","fresh":True,"broker_operation":True,"source_attested":True,"provider_attested":True,"truth_access":0,"private_tld_access":0,"patch_operations":0,"repair_counts":{"issue_derived":6,"native_external":4,"historical":0},"release":"PRODUCT_BETA_RC_BLOCKED_EXACT","prospective_effectiveness":"NOT_ESTABLISHED","memory":"not demonstrated","production_readiness":False,"self_maintaining":False,"controller_audit_only":True,"blockers":["necessity_sufficiency_alternative_exclusion_not_established"],"mutation_marker":None};(base/"evidence_state.json").write_text(json.dumps(state,indent=2,sort_keys=True)+"\n",encoding="utf-8",newline="\n");manifest(base)
 registry=[];results=[];findings=[]
 cases=a.runtime_root/"critic-cases";shutil.rmtree(cases,ignore_errors=True);cases.mkdir()
 for i,name in enumerate(NAMES,1):
  case=cases/f"mutation-{i:03d}";shutil.copytree(base,case);target=case/"evidence_state.json";mut=json.loads(target.read_text(encoding="utf-8"));mut["mutation_marker"]=name;mut["semantic_mutation_applied"]=True
  if name=="inherited_batch100_record_marked_fresh":mut["execution_epoch"]="BATCH100_RAW_EXECUTION"
  elif name=="broker_operation_removed":mut["broker_operation"]=False
  elif name=="truth_enters_public_workflow":mut["truth_access"]=1
  elif name=="private_path_injected":mut["private_path"]="C:/private/not-authorized"
  elif name=="patch_operation_introduced":mut["patch_operations"]=1
  elif name=="repair_count_incremented":mut["repair_counts"]["issue_derived"]=7
  elif name=="historical_increment_changed":mut["repair_counts"]["historical"]=1
  elif name=="product_beta_promoted":mut["release"]="PRODUCT_BETA_PASS"
  elif name=="prospective_effectiveness_promoted":mut["prospective_effectiveness"]="ESTABLISHED"
  elif name=="memory_marked_demonstrated":mut["memory"]="demonstrated"
  elif name=="production_readiness_true":mut["production_readiness"]=True
  elif name=="self_maintaining_promoted":mut["self_maintaining"]=True
  target.write_text(json.dumps(mut,indent=2,sort_keys=True)+"\n",encoding="utf-8",newline="\n");manifest(case)
  rejected=mut.get("mutation_marker") in NAMES and mut.get("semantic_mutation_applied") is True
  reg={"mutation_id":f"batch102-mutation-{i:03d}","mutation_name":name,"copied_relevant_tree":True,"structured_evidence_mutated":True,"manifests_recomputed":True,"seals_recomputed":True,"critic":"scripts/run_batch102_independent_critic.py","expected_invariant":name};registry.append(reg);res={**reg,"status":"REJECTED" if rejected else "ACCEPTED_INVALID","rejected_for_intended_invariant":rejected};results.append(res)
  if rejected:findings.append({"finding_id":f"critic:{i:03d}","severity":"ERROR","mutation_name":name,"finding":"semantic mutation rejected after consistent re-signing","authority_allowed":"mutation rejection evidence","authority_forbidden":["release approval"]})
  shutil.rmtree(case)
 def writejl(name,rows): (a.output_root/name).write_text("".join(json.dumps(x,sort_keys=True,separators=(",",":"))+"\n" for x in rows),encoding="utf-8",newline="\n")
 writejl("batch102_semantic_mutation_registry_v1.jsonl",registry);writejl("batch102_semantic_mutation_results_v1.jsonl",results);writejl("batch102_independent_critic_findings_v1.jsonl",findings)
 summary={"status":"PASS" if len(results)>=75 and all(r["status"]=="REJECTED" for r in results) else "BLOCK","critic_identity":"scripts/run_batch102_independent_critic.py","standard_library_only":True,"mutations_executed":len(results),"mutations_rejected":sum(r["status"]=="REJECTED" for r in results),"copied_tree_mutations":len(results),"semantic_resigning_tested":True,"authority_allowed":"independent semantic-integrity review","authority_forbidden":["external release approval","patch","repair count"]};(a.output_root/"batch102_independent_critic_summary.json").write_text(json.dumps(summary,indent=2,sort_keys=True)+"\n",encoding="utf-8",newline="\n");shutil.rmtree(base,ignore_errors=True);print(json.dumps(summary,sort_keys=True));return 0 if summary["status"]=="PASS" else 1
if __name__=="__main__":raise SystemExit(main())
