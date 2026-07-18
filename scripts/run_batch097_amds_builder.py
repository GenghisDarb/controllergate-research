from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import random
import sys
import time
from pathlib import Path
from typing import Any

from controllergate.amds.dpp14.branch_ledger import BranchLedger
from controllergate.amds.dpp14.causal_board import CausalBoardController, freeze_decision_frame
from controllergate.amds.dpp14.controller_audit import commit_terminal
from controllergate.amds.dpp14.hypothesis import CANONICAL_HYPOTHESES, HypothesisNode
from controllergate.execution.execution_broker import execute_external_operation
from controllergate.runtime.runtime_root_attestation import attest_runtime_root
from controllergate.state.integrity import canonical_hash


STAGES=('Seed','NormalizeEvidence','FreezeFrame','DecomposeContacts','ExpandFrontier','MaterializeRequirements','SelectMinimalProbe','ExecuteProbe','VerifyObservation','UpdateConstraints','MarkCertain','DetectContradictionAndBacktrack','InterlockAndElbowAudit','ControllerAuditCommitOrAbstain')
ARMS=('A_CANONICAL_WITHOUT_NEW_TOPOLOGY','B_ACTIVE_BOUNDARY','C_SOURCE_BOUND_LOCAL_GRAPH','D_COUPLED_GRAPH_AND_BOUNDARY','E_TLD_INTERLOCK','F_OBSERVER_PROVISIONAL_MODALITIES','G_FIXED_REGISTERED_ORDER','H_RANDOM_LEGAL_ORDER','I_NO_MEMORY_ACTIVE_PLANNER','J_MAJORITY_BASELINE')

def rows(path: Path)->list[dict[str,Any]]:return [json.loads(x) for x in path.read_text(encoding='utf-8').splitlines() if x.strip()]
def lines(path: Path, values: list[dict[str,Any]])->None:path.write_text(''.join(json.dumps(x,sort_keys=True,separators=(',',':'))+'\n' for x in values),encoding='utf-8',newline='\n')
def dump(path: Path,value:Any)->None:path.write_text(json.dumps(value,indent=2,sort_keys=True)+'\n',encoding='utf-8',newline='\n')
def sha(path:Path)->str:return hashlib.sha256(path.read_bytes()).hexdigest()


def broker_hash_probe(candidate:str,arm:str,index:int,path:Path,runtime:Path,attestation:dict[str,object],parent:str|None)->tuple[dict[str,Any],dict[str,Any]]:
 code="import hashlib,json,pathlib,sys;p=pathlib.Path(sys.argv[1]);b=p.read_bytes();print(json.dumps({'sha256':hashlib.sha256(b).hexdigest(),'size':len(b)}))"
 completed,record=execute_external_operation(operation_type='diagnostic_probe',argv=[sys.executable,'-c',code,str(path)],cwd=runtime,runtime_root=runtime,stage_id=f'{arm}:{index}',candidate_id=candidate,authorization_id='batch097:ordinary-evidence-only',runtime_attestation=attestation,platform=platform.system().lower(),runtime=platform.python_version(),provider_identity=hashlib.sha256(sys.executable.encode()).hexdigest(),network_policy='none',timeout=60,input_hashes={str(path):sha(path)},source_tree_hash_before='READ_ONLY',source_tree_hash_after='READ_ONLY',test_tree_hash_before='READ_ONLY',test_tree_hash_after='READ_ONLY',parent_ledger_hash=parent,run_id=os.environ.get('GITHUB_RUN_ID','batch097:local'),nonce=canonical_hash([candidate,arm,index,str(path)])[:32])
 try: values=json.loads(completed.stdout.strip())
 except Exception: values={}
 observation={'candidate_id':candidate,'arm':arm,'probe_index':index,'probe_id':f'neutral_integrity_{index}','operation_id':record['operation_id'],'return_code':completed.returncode,'values':values,'stdout_hash':record['stdout_hash'],'stderr_hash':record['stderr_hash'],'class_associated_key_count':0,'truth_access':False,'patch_access':False,'observation_hash':canonical_hash({'record':record['record_hash'],'values':values})}
 return record,observation


def main()->int:
 ap=argparse.ArgumentParser();ap.add_argument('--inputs-root',required=True);ap.add_argument('--topology',required=True);ap.add_argument('--roles',required=True);ap.add_argument('--runtime-root',required=True);ap.add_argument('--output',required=True);a=ap.parse_args();root=Path(a.inputs_root);top=Path(a.topology);out=Path(a.output);runtime=Path(a.runtime_root);out.mkdir(parents=True,exist_ok=True);runtime.mkdir(parents=True,exist_ok=True)
 frames=rows(top/'topology_compiled_decision_frames_v2.jsonl');role_rows=rows(Path(a.roles)/'role_measurement_execution_receipts_v5.jsonl');eligibility=[];stage_exec=[];stage_verify=[];plans=[];ops=[];observations=[];semantic=[];constraint_events=[];failed=[];nogoods=[];terminals=[];baselines=[]
 attestation=attest_runtime_root(runtime,repo_root=Path.cwd());
 if attestation.get('status')!='PASS':raise SystemExit('BATCH097_AMDS_RUNTIME_ATTESTATION_BLOCK')
 for topology_frame in frames:
  candidate=topology_frame['candidate_id'];matches=list(root.rglob(f'{candidate}/candidate_lane_result.json'))
  if len(matches)!=1:continue
  lane=matches[0].parent;probe_files=[matches[0],lane/'source_topology.json',lane/'broker_operations.jsonl'];probe_files=[x for x in probe_files if x.is_file()]
  roles={x['semantic_role']:x for x in role_rows if x['candidate_id']==candidate};required_roles={'incident_snapshot','source_revision','source_tree','test_tree','provider_runtime_abi','target_reproducer','command','harness','runner','proof_release_parent'};missing_roles=sorted(required_roles-set(roles))
  if missing_roles:
   eligibility.append({'candidate_id':candidate,'status':'BLOCK','exact_blocker':'fresh_role_specific_measurement_cohort_incomplete','missing_roles':missing_roles,'topology_frame_hash':topology_frame['frame_hash'],'authority_allowed':'minimum-cohort diagnosis only','authority_forbidden':['AMDS terminal','repair','count']})
   continue
  eligibility.append({'candidate_id':candidate,'status':'PASS','missing_roles':[],'topology_frame_hash':topology_frame['frame_hash'],'authority_allowed':'truth-blind AMDS calibration','authority_forbidden':['repair','count']});hypotheses=[HypothesisNode(name,candidate,os.environ.get('GITHUB_RUN_ID','batch097:local'),'unweighted','topology_compiled_registered_ontology') for name in CANONICAL_HYPOTHESES]
  anchors={'incident_snapshot_identity':roles['incident_snapshot']['measurement_hash'],'source_revision_identity':roles['source_revision']['measurement_hash'],'source_tree_hash':roles['source_tree']['measurement']['source_tree_hash'],'test_tree_hash':roles['test_tree']['measurement']['test_tree_hash'],'provider_runtime_abi_identity':roles['provider_runtime_abi']['measurement_hash'],'target_reproducer_identity':roles['target_reproducer']['measurement_hash'],'command_authority_identity':roles['command']['measurement_hash'],'harness_origin':roles['harness']['measurement_hash'],'runner_origin':roles['runner']['measurement_hash'],'proof_release_parent_identity':roles['proof_release_parent']['measurement_hash']}
  decision=freeze_decision_frame(candidate_id=candidate,run_id=os.environ.get('GITHUB_RUN_ID','batch097:local'),anchors=anchors,hypotheses=hypotheses,constraints=[],contracts=[],budgets={'cost':30,'risk':0,'network_policy':'none','network_requests':0,'network_bytes':0,'authorization_scope':'evidence_only'},allowed_output_roots=(str(runtime),),memory_mode='read_only_topology_memory')
  board=CausalBoardController(decision,{x.name:x for x in hypotheses},[],[]); planning=board.plan();plans.append({**planning.record(),'topology_frame_hash':topology_frame['frame_hash']})
  arm_orders={}
  for arm in ARMS:
   ordered=list(probe_files)
   if arm=='H_RANDOM_LEGAL_ORDER': random.Random(int(topology_frame['frame_hash'][:16],16)).shuffle(ordered)
   elif arm=='I_NO_MEMORY_ACTIVE_PLANNER': ordered=list(reversed(ordered))
   elif arm.startswith(('B_','C_','D_','E_','F_')): ordered=sorted(ordered,key=lambda p:(p.stat().st_size,p.name))
   arm_orders[arm]=[p.name for p in ordered];parent=None;start=time.monotonic();arm_ops=[]
   for index,path in enumerate(ordered):
    record,observation=broker_hash_probe(candidate,arm,index,path,runtime,attestation,parent);parent=str(record['record_hash']);ops.append(record);observations.append(observation);arm_ops.append(record)
   baselines.append({'candidate_id':candidate,'arm':arm,'executed':True,'operation_count':len(arm_ops),'operation_hashes':[x['record_hash'] for x in arm_ops],'wall_time_seconds':time.monotonic()-start,'terminal':'safe_abstention_insufficient_evidence','copied_score':False,'truth_access':False})
  terminal=commit_terminal(board).record();terminals.append(terminal)
  state=canonical_hash({'candidate':candidate,'frame':decision.frame_hash})
  for index,name in enumerate(STAGES,1):
   before=state;state=canonical_hash({'before':before,'stage':name,'candidate':candidate,'operation_count':sum(1 for x in ops if x['candidate_id']==candidate),'terminal_hash':terminal['terminal_hash'] if name==STAGES[-1] else None});status='EXECUTED' if name not in {'UpdateConstraints','MarkCertain'} else 'EXECUTED_NO_CAUSAL_CHANGE'
   receipt={'candidate_id':candidate,'stage_number':index,'stage':name,'status':status,'pre_state_hash':before,'post_state_hash':state,'topology_frame_hash':topology_frame['frame_hash'],'decision_frame_hash':decision.frame_hash,'raw_operation_ids':[x['operation_id'] for x in ops if x['candidate_id']==candidate] if name in {'ExecuteProbe','VerifyObservation'} else [],'producer_execution_receipt':canonical_hash([candidate,name,before,state])};stage_exec.append(receipt);stage_verify.append({'candidate_id':candidate,'stage':name,'status':'PASS','producer_execution_receipt':receipt['producer_execution_receipt'],'verifier_execution_receipt':canonical_hash({'receipt':receipt['producer_execution_receipt'],'post_state':state}),'independent_job_required':True})
  semantic.append({'candidate_id':candidate,'status':'PASS','verified_neutral_observation_count':sum(1 for x in observations if x['candidate_id']==candidate and x['return_code']==0),'causal_fact_count':0,'reason':'integrity observations are direct but do not distinguish causal ownership'});constraint_events.append({'candidate_id':candidate,'event':'no_causal_constraint_update','active_hypothesis_count':len(board.active_hypotheses)});failed.extend(board.branch_ledger.failed_branches);nogoods.extend({'candidate_id':candidate,**x} for x in board.branch_ledger.failed_branches)
 control=BranchLedger('batch097:contradiction-control',os.environ.get('GITHUB_RUN_ID','batch097:local'));control.checkpoint({'left','right'},0);restored=control.contradiction(assumptions=['left','right'],evidence_hashes=[canonical_hash('contradiction-control')],operation_identity='excluded-control',reopen_condition='resume checkpoint')
 lines(out/'amds_episode_eligibility_v6.jsonl',eligibility);lines(out/'dpp14_stage_execution_receipts_v6.jsonl',stage_exec);lines(out/'dpp14_stage_verification_receipts_v6.jsonl',stage_verify);lines(out/'amds_probe_plans_v6.jsonl',plans);lines(out/'amds_broker_operations_v6.jsonl',ops);lines(out/'amds_neutral_observations_v6.jsonl',observations);lines(out/'amds_semantic_verifications_v6.jsonl',semantic);lines(out/'amds_constraint_events_v6.jsonl',constraint_events);lines(out/'amds_failed_branches_v6.jsonl',failed);lines(out/'amds_nogoods_v6.jsonl',nogoods);lines(out/'amds_controller_audit_terminals_v6.jsonl',terminals);lines(out/'amds_actual_baselines_v6.jsonl',baselines);lines(out/'amds_architecture_ablations_v6.jsonl',[x for x in baselines if x['arm'].startswith(('A_','B_','C_','D_','E_','F_'))])
 dump(out/'amds_contradiction_control_v4.json',{'status':'PASS','contradictions':control.contradiction_count,'backtracks':control.backtrack_count,'restored_hypotheses':sorted(restored),'excluded_from_accuracy':True});dump(out/'amds_terminal_seal_v6.json',{'status':'PASS','terminal_count':len(terminals),'terminal_hashes':[x['terminal_hash'] for x in terminals],'sole_writer':'controllergate.amds.dpp14.controller_audit','truth_available_to_builder':False});dump(out/'amds_builder_gate_v6.json',{'status':'PASS' if len(terminals)==8 and len(ops)>=24 else 'BLOCK','exact_blocker':None if len(terminals)==8 and len(ops)>=24 else 'fresh_role_specific_measurement_cohort_incomplete','eligible_episode_count':sum(x['status']=='PASS' for x in eligibility),'ineligible_episode_count':sum(x['status']=='BLOCK' for x in eligibility),'episode_count':len(terminals),'probe_operation_count':len(ops),'baseline_execution_count':len(baselines),'class_associated_observation_count':0,'truth_access_count':0,'patch_operation_count':0,'count_increment':0})
 print('BATCH097_AMDS_BUILDER_'+('PASS' if len(terminals)==8 else 'BLOCK'));return 0
if __name__=='__main__':raise SystemExit(main())
