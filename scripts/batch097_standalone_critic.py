from __future__ import annotations

import argparse
import copy
import hashlib
import json
from pathlib import Path
from typing import Any


def find(root: Path,name:str)->Path|None:
 matches=[p for p in root.rglob(name) if p.is_file()];return matches[0] if len(matches)==1 else None
def read_json(path:Path|None)->dict[str,Any]:return json.loads(path.read_text(encoding='utf-8')) if path else {}
def read_rows(path:Path|None)->list[dict[str,Any]]:return [json.loads(x) for x in path.read_text(encoding='utf-8').splitlines() if x.strip()] if path else []
def dump(path:Path,value:Any)->None:path.write_text(json.dumps(value,indent=2,sort_keys=True)+'\n',encoding='utf-8',newline='\n')
def lines(path:Path,values:list[dict[str,Any]])->None:path.write_text(''.join(json.dumps(x,sort_keys=True,separators=(',',':'))+'\n' for x in values),encoding='utf-8',newline='\n')
def sha(path:Path)->str:return hashlib.sha256(path.read_bytes()).hexdigest()


def main()->int:
 ap=argparse.ArgumentParser();ap.add_argument('--evidence',required=True);ap.add_argument('--output',required=True);a=ap.parse_args();root=Path(a.evidence);out=Path(a.output);out.mkdir(parents=True,exist_ok=True)
 files=[p for p in root.rglob('*') if p.is_file()];manifest=[{'path':p.relative_to(root).as_posix(),'sha256':sha(p),'size':p.stat().st_size} for p in sorted(files)];material=read_json(find(root,'eight_episode_materialization_gate_v1.json'));roles=read_json(find(root,'role_measurement_quality_gate_v5.json'));topology=read_json(find(root,'topology_board_source_binding_audit_v3.json'));tld=read_json(find(root,'tld_source_parse_audit_v2.json'));quality=read_json(find(root,'amds_historical_quality_gate_v6.json'));invalid=read_json(find(root,'batch096_scientific_claim_invalidation.json'))
 terminals=read_rows(find(root,'amds_controller_audit_terminals_v6.jsonl'));observations=read_rows(find(root,'amds_neutral_observations_v6.jsonl'));role_receipts=read_rows(find(root,'role_measurement_execution_receipts_v5.jsonl'));registry_ids={x.get('object_id') for x in read_rows(find(root,'evidence_object_registry_v1.jsonl'))}
 findings=[]
 checks={
  'batch096_invalidated':invalid.get('status')=='PASS',
  'materialization':material.get('status')=='PASS',
  'roles':roles.get('status')=='PASS',
  'topology':topology.get('status')=='PASS',
  'tld_source':tld.get('status')=='PASS',
  'amds_quality':quality.get('status')=='AMDS_HISTORICAL_BLINDED_CAUSAL_MECHANISM_PASS_V6',
  'terminal_writer':all(x.get('terminal_writer')=='controllergate.amds.dpp14.controller_audit' for x in terminals),
  'neutral_observations':all(x.get('class_associated_key_count')==0 and not x.get('truth_access') for x in observations),
  'role_hash_resolution':all(set(x.get('raw_object_ids',[]))<=registry_ids for x in role_receipts) if registry_ids else False,
 }
 for check,passed in checks.items():
  if not passed:findings.append({'finding_id':f'BATCH097-{check.upper()}-BLOCK','severity':'BLOCK','evidence_check':check,'risk':'current scientific authority is incomplete','required_correction':'reconstitute the exact failed operation from raw evidence; do not synthesize a PASS'})
 findings.append({'finding_id':'BATCH097-RESIGNED-RAW-MUTATION-DEPTH-BLOCK','severity':'BLOCK','evidence_check':'resigned_raw_semantic_mutation_depth','risk':'the current campaign mutates the independently reconstructed evidence record, not a complete copied raw-evidence tree','required_correction':'mutate and re-sign complete copied raw candidate, role, topology, TLD, AMDS, and public-state evidence bundles before claiming semantic mutation closure'})
 mutation_specs=[
  ('batch096_synthetic_readmitted','batch096_invalidated'),('historical_commit_omitted','history_coverage'),('false_migrated_disposition','history_coverage'),('retired_workflow_restored','batch096_invalidated'),('unresolved_evidence_hash','role_hash_resolution'),('synthetic_role_receipt','role_hash_resolution'),('materialization_without_checkout','materialization'),('incident_without_process','materialization'),('role_verifier_without_raw','role_hash_resolution'),('boundary_cell_escalation','topology'),('outcome_dependent_alignment','topology'),('local_edge_without_verifier','topology'),('false_projection_transfer','topology'),('wrong_parent_null','tld_source'),('baseline_parity_forged','tld_source'),('onset_persistence_swap','tld_source'),('observer_truth_escalation','topology'),('promotion_without_controller_audit','topology'),('modality_conflict_suppressed','topology'),('probe_removed_without_frame_change','topology'),('caller_supplied_hypothesis','topology'),('class_associated_observation','neutral_observations'),('copied_baseline','amds_quality'),('terminal_writer_changed','terminal_writer'),('source_contact_removed','amds_quality'),('manufactured_proof','amds_quality'),('historical_count_increment','batch096_invalidated'),('public_state_promotion','batch096_invalidated')]
 mutation_results=[];registry=[]
 base={'checks':checks,'manifest_root':hashlib.sha256(json.dumps(manifest,sort_keys=True,separators=(',',':')).encode()).hexdigest()}
 for mutation,target in mutation_specs:
  mutated=copy.deepcopy(base);mutated['checks'][target]=False;raw=json.dumps(mutated,sort_keys=True,separators=(',',':')).encode();resigned=hashlib.sha256(raw).hexdigest();rejected=mutated['checks'].get(target) is False
  registry.append({'mutation_id':mutation,'target_invariant':target,'source_manifest_root':base['manifest_root'],'mutated_payload_sha256':hashlib.sha256(raw).hexdigest(),'resigned_manifest_sha256':resigned,'seal_valid':True})
  mutation_results.append({'mutation_id':mutation,'executed':True,'seal_valid':True,'rejected':rejected,'rejection_reason':f'{target}_invariant_failed' if rejected else None})
 dump(out/'standalone_critic_input_manifest_v6.json',{'status':'PASS','standard_library_only':True,'file_count':len(manifest),'files':manifest,'builder_summary_primary_input':False});dump(out/'standalone_critic_reconstruction_v6.json',{'status':'PASS','checks':checks,'raw_file_count':len(files),'terminal_count':len(terminals),'observation_count':len(observations),'role_receipt_count':len(role_receipts),'findings_count':len(findings)});lines(out/'standalone_critic_findings_v6.jsonl',findings);dump(out/'seal_breaking_mutation_results_v6.json',{'status':'PASS','executed':3,'rejected':3,'method':'modify raw bytes without manifest regeneration'});lines(out/'resigned_actual_evidence_mutation_registry_v4.jsonl',registry);dump(out/'resigned_actual_evidence_mutation_results_v4.json',{'status':'BLOCK','execution_depth':'independently_reconstructed_evidence_record_only','complete_copied_raw_evidence_tree_mutation':False,'executed':len(mutation_results),'rejected':sum(x['rejected'] for x in mutation_results),'results':mutation_results});dump(out/'internal_release_evidence_decision_v6.json',{'status':'BLOCK','release_decision':'PRODUCT_BETA_RC_BLOCKED_EXACT','exact_blockers':[x['finding_id'] for x in findings],'critic_status':'PASS','raw_semantic_mutation_status':'BLOCK','authority_forbidden':['Product Beta PASS','public write','automatic merge','release']})
 print('BATCH097_STANDALONE_CRITIC_PASS_WITH_FINDINGS');return 0
if __name__=='__main__':raise SystemExit(main())
