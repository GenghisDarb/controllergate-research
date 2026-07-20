"""Expected-red audit of Batch101's inherited-execution boundary."""

from __future__ import annotations
import hashlib, json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
OUTPUT=ROOT/"outputs/post_v2_37_hardening_batch102_fresh_exact_counterfactual_execution_necessity_sufficiency_ownership_closure/batch102_pre_fresh_execution_expected_failure.json"
BOUNDARY="78116fb7dc57b4d92d08a6f9ee15c96ea8adfef3"

IDS=[
"batch101_artifact_not_officially_ingested","batch101_finalizer_reprojects_batch100","batch101_reads_batch100_clean_replays","no_new_candidate_target_execution","workflow_has_no_candidate_runner","single_ubuntu_reconstruction_job","no_candidate_matrix_job","no_windows_poetry_execution","no_python37_darker_execution","no_python312_cloudpickle_execution","no_python313_beta_execution","no_openbb_lifecycle","no_fresh_broker_records","raw_records_name_batch100_source","source_blockers_hardcoded","provider_modes_hardcoded","source_versions_static","blocked_cells_not_retried","necessity_static_not_established","sufficiency_static_not_established","interaction_copied_from_pair","all_arms_receive_all_cells","all_arms_open_all_outcomes","architecture_arms_do_not_select","baselines_not_distinct_executions","architecture_gain_not_evaluable","execution_epoch_missing","workflow_run_per_cell_missing","workflow_job_per_cell_missing","broker_attestation_missing","source_provider_not_observed_fresh","source_tree_presence_not_proven","candidate_command_not_run_in_batch101","darker_exact_source_not_executed","pytest_exact_source_not_executed","openbb_commits_not_acquired","poetry_corrected_cwd_not_executed","audioread_dependency_plan_not_executed","cloudpickle_fourth_corner_not_executed","freezegun_exact_provider_not_retried","pybugger_necessity_sufficiency_not_executed","alternative_exclusion_not_executed","arm_plan_not_frozen_pre_outcome","arm_job_does_not_limit_envelopes","private_scoring_cannot_establish_gain"]

def main()->int:
 findings=[]
 for i,fid in enumerate(IDS,1):
  path="scripts/finalize_batch101_public_evidence.py" if i not in {1,5,6,7,8,9,10,11,12} else (".github/workflows/post_v2_37_hardening_batch101_exact_incident_salvage_ownership_closure.yml" if i!=1 else "outputs/post_v2_37_hardening_batch101_canonical_semantic_replay_exact_incident_salvage_ownership_closure")
  findings.append({"finding_number":i,"finding_id":fid,"commit":BOUNDARY,"path":path,"symbol":"Batch101 execution and reconstruction boundary","line_range":"1-EOF","observed_artifact_evidence":"The official Batch101 artifact records zero fresh Batch101 operations, 56 inherited Batch100 raw replays, and semantic projection only.","risk":"Inherited or static evidence could be misrepresented as fresh execution or causal closure.","required_correction":"Require current-workflow brokered execution, exact source/provider attestation, and independently verified causal/arm receipts.","red_to_green_test":f"test_batch102_{fid}"})
 if len(findings)!=45: raise RuntimeError("expected 45 findings")
 value={"status":"BATCH102_PRE_FRESH_EXECUTION_FAIL_EXPECTED","boundary_commit":BOUNDARY,"finding_count":len(findings),"findings":findings,"authority_allowed":"expected-red implementation planning","authority_forbidden":["fresh execution substitution","candidate patch","repair count","release promotion"]}; value["seal_sha256"]=hashlib.sha256(json.dumps(value,sort_keys=True,separators=(",",":")).encode()).hexdigest(); OUTPUT.parent.mkdir(parents=True,exist_ok=True); OUTPUT.write_text(json.dumps(value,indent=2,sort_keys=True)+"\n",encoding="utf-8",newline="\n"); print(json.dumps({"status":value["status"],"finding_count":45,"seal_sha256":value["seal_sha256"]},sort_keys=True)); return 0
if __name__=="__main__": raise SystemExit(main())
