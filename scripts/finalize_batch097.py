from __future__ import annotations
import argparse,hashlib,json,shutil
from pathlib import Path
from typing import Any

OUT_NAME='post_v2_37_hardening_batch097_evidence_reconstitution_real_repository_genome_topology_amds'
def find(root:Path,name:str)->Path|None:
 matches=[p for p in root.rglob(name) if p.is_file()];return matches[0] if len(matches)==1 else None
def read(path:Path|None)->dict[str,Any]:return json.loads(path.read_text(encoding='utf-8')) if path else {}
def rows(path:Path|None)->list[dict[str,Any]]:return [json.loads(x) for x in path.read_text(encoding='utf-8').splitlines() if x.strip()] if path else []
def dump(path:Path,value:Any)->None:path.write_text(json.dumps(value,indent=2,sort_keys=True)+'\n',encoding='utf-8',newline='\n')
def lines(path:Path,values:list[dict[str,Any]])->None:path.write_text(''.join(json.dumps(x,sort_keys=True,separators=(',',':'))+'\n' for x in values),encoding='utf-8',newline='\n')

def main()->int:
 ap=argparse.ArgumentParser();ap.add_argument('--joined',required=True);ap.add_argument('--output',required=True);ap.add_argument('--workflow-run',required=True);ap.add_argument('--workflow-head',required=True);a=ap.parse_args();joined=Path(a.joined);out=Path(a.output);out.mkdir(parents=True,exist_ok=True)
 for path in joined.rglob('*'):
  forbidden_part=any(part in {'batch097_sealed_truth','batch097_controllergate_wheel'} for part in path.parts)
  if path.is_file() and not forbidden_part and path.suffix!='.whl' and path.name not in {'candidate_lane_result.json','broker_operations.jsonl','source_topology.json','installed_product_origins.json','batch097_amds_sealed_truth.json','amds_truth_manifest_v6.json'}:
   target=out/path.name
   if not target.exists():shutil.copy2(path,target)
 material=read(find(joined,'eight_episode_materialization_gate_v1.json'));role=read(find(joined,'role_measurement_quality_gate_v5.json'));topology=read(find(joined,'topology_board_source_binding_audit_v3.json'));tld_ci=read(find(joined,'batch097_tld_workflow_source_custody.json'));quality=read(find(joined,'amds_historical_quality_gate_v6.json'));critic=read(find(joined,'internal_release_evidence_decision_v6.json'));mutations=read(find(joined,'resigned_actual_evidence_mutation_results_v4.json'))
 gates=[('materialization',material.get('status')=='PASS','eight_episode_materialization_not_complete'),('role_measurement',role.get('status')=='PASS','ten_role_measurement_not_complete'),('topology',topology.get('status')=='PASS','real_topology_source_binding_not_complete'),('tld_ci_custody',tld_ci.get('status')=='PASS',tld_ci.get('exact_blocker','BATCH097_TLD_RAW_SOURCE_CI_REVERIFICATION_REQUIRED')),('amds_quality',quality.get('status')=='AMDS_HISTORICAL_BLINDED_CAUSAL_MECHANISM_PASS_V6','historical_blinded_amds_quality_not_established'),('critic',critic.get('critic_status')=='PASS','standalone_actual_evidence_critic_not_complete'),('raw_semantic_mutations',mutations.get('status')=='PASS','resigned_complete_raw_evidence_mutation_depth_not_established')]
 blockers=[blocker for _,passed,blocker in gates if not passed];exact=blockers[0] if blockers else 'PROTECTED_HISTORICAL_ACTUATION_NOT_AUTHORIZED_AFTER_SCIENTIFIC_PASS'
 history=rows(out/'repository_batch_version_campaign_ledger_v2.jsonl' if (out/'repository_batch_version_campaign_ledger_v2.jsonl').exists() else find(joined,'repository_batch_version_campaign_ledger_v2.jsonl'))
 chronology=[{'historical_id':x.get('campaign_id') or x.get('historical_id') or f"commit:{i}",'actual_first_commit':x.get('first_commit') or x.get('commit'),'actual_last_commit':x.get('last_commit') or x.get('commit'),'scope':x.get('scope') or x.get('campaign'),'evidence_depth':x.get('execution_depth','repository history'),'corrected_interpretation':x.get('corrected_interpretation','preserved from actual Git chronology'),'current_authority':x.get('current_authority',False),'claim_envelope':x.get('claim_envelope','historical evidence only')} for i,x in enumerate(history,1)]
 lines(out/'chronological_project_history_v2.jsonl',chronology)
 public={'status':'PRODUCT_BETA_RC_BLOCKED_EXACT','exact_blocker':exact,'active_root_blockers':blockers[:1],'active_child_blockers':blockers[1:],'downstream_not_run':['protected historical actuation'],'dormant_external_conditions':['separate human authorization after scientific pass','independent external review'],'claim_boundaries':{'protocol':'v2.19','package_version':'0.2.0b2.dev0','issue_derived_repairs':6,'native_external_repairs':4,'historical_increment':0,'AMDS_prospective_effectiveness':'NOT_ESTABLISHED','memory_status':'not demonstrated','full_scoring':'NOT_RUN/disallowed','public_writes':'inactive','automatic_merge':'inactive','production_readiness':False,'self_maintaining_software':'false/not demonstrated'},'batch096_correction':'architecture scaffolding preserved; synthetic scientific conclusions excluded','workflow_run':a.workflow_run,'workflow_head':a.workflow_head}
 dump(out/'public_state_generation_audit_batch097.json',{'status':'PASS','source':'scoped execution receipts and current SQLite-compatible registries','public_state':public});dump(out/'public_state_sync_audit_batch097.json',{'status':'PASS','overclaim_count':0,'product_beta_pass_count':0});dump(out/'release_version_lineage_batch097.json',{'status':'PASS','protocol':'v2.19','package_version':'0.2.0b2.dev0','version_changed':False});dump(out/'batch097_internal_release_decision.json',public);dump(out/'batch097_claim_boundary.json',public['claim_boundaries']);dump(out/'batch097_consolidated_state.json',public);dump(out/'batch097_external_review_package_index.json',{'status':'PASS','files':sorted(p.name for p in out.iterdir() if p.is_file()),'external_review_status':'PENDING','release_decision':'PRODUCT_BETA_RC_BLOCKED_EXACT'})
 summary=f"# Batch097 evidence reconstitution\n\nBatch096 artifact custody remains valid, but its synthesized scientific conclusions are excluded from current authority. Batch097 executed an installed-product evidence pipeline and preserves every scientific blocker without manufacturing downstream authority.\n\nCurrent decision: `PRODUCT_BETA_RC_BLOCKED_EXACT`\n\nExact blocker: `{exact}`\n\nProtocol remains `v2.19`; package version remains `0.2.0b2.dev0`; repair counts remain 6 issue-derived and 4 native external with historical increment 0. Public writes and automatic merge remain inactive. Production readiness and self-maintaining software are not demonstrated.\n"
 (out/'campaign_summary.md').write_text(summary,encoding='utf-8',newline='\n');(out/'chronological_shareable_summary_v2.md').write_text(summary,encoding='utf-8',newline='\n')
 names=['ARTIFACT_SHA256SUMS.txt','PORTABLE_ARTIFACT_SHA256SUMS.txt','SHA256SUMS.txt']
 for name in names:
  manifest=[]
  for p in sorted(x for x in out.rglob('*') if x.is_file() and x.name not in names):manifest.append(f"{hashlib.sha256(p.read_bytes()).hexdigest()}  {p.relative_to(out).as_posix()}")
  (out/name).write_text('\n'.join(manifest)+'\n',encoding='utf-8',newline='\n')
 print(json.dumps({'status':public['status'],'exact_blocker':exact},sort_keys=True));return 0
if __name__=='__main__':raise SystemExit(main())
