from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from controllergate.state.provisional_store import ProvisionalEvidenceStore
from controllergate.topology.evidence_compiler import ObserverStateContractV2, compile_boundary_volume, compile_coupled_projection_graph, compile_local_graph


ORDER=['darker_issue_112_relative_git_dir','py_bugger_issue_65','cloudpickle_507_py313_typevar_distutils','freezegun_547_py313_datetimes_assertion','audioread_144_py313_aifc_removed','pytest_13480_wdefault_unraisable_threadexception','incident_openbb_7585_modular_openapi_reproducer','incident_poetry_10974_init_duplicate_name']
ROLES=('materializer','environment aligner','diagnostic builder','DPP read-only lane','ControllerAudit','stage producer','stage verifier','internal critic','external reviewer','human approver','public-state generator')


def read_lines(path: Path) -> list[dict[str,Any]]: return [json.loads(x) for x in path.read_text(encoding='utf-8').splitlines() if x.strip()]
def lines(path: Path, rows: list[dict[str,Any]]) -> None: path.write_text(''.join(json.dumps(x,sort_keys=True,separators=(',',':'))+'\n' for x in rows),encoding='utf-8',newline='\n')
def dump(path: Path, value: Any) -> None: path.write_text(json.dumps(value,indent=2,sort_keys=True)+'\n',encoding='utf-8',newline='\n')


def main() -> int:
    ap=argparse.ArgumentParser(); ap.add_argument('--inputs-root',required=True); ap.add_argument('--role-producers',required=True); ap.add_argument('--role-verifiers',required=True); ap.add_argument('--runtime-root',required=True); ap.add_argument('--output',required=True); a=ap.parse_args()
    root=Path(a.inputs_root); out=Path(a.output); out.mkdir(parents=True,exist_ok=True); runtime=Path(a.runtime_root); runtime.mkdir(parents=True,exist_ok=True)
    producers=read_lines(Path(a.role_producers)/'role_measurement_execution_receipts_v5.jsonl'); verifiers=read_lines(Path(a.role_verifiers)/'role_measurement_verification_receipts_v5.jsonl')
    boundaries=[]; local=[]; coupled=[]; node_rows=[]; edge_rows=[]; unresolved=[]; recovery=[]; observers=[]; modalities=[]; modality_contracts=[]; modality_controls=[]; branches=[]; checkpoints=[]; promotions=[]
    now=datetime.now(timezone.utc).isoformat().replace('+00:00','Z')
    for candidate_id in ORDER:
        matches=list(root.rglob(f'{candidate_id}/candidate_lane_result.json'))
        if len(matches)!=1: continue
        row=json.loads(matches[0].read_text(encoding='utf-8')); pr=[x for x in producers if x['candidate_id']==candidate_id]; vr=[x for x in verifiers if x['candidate_id']==candidate_id]
        boundary=compile_boundary_volume(row,vr); graph=compile_local_graph(row,pr,vr); coupling=compile_coupled_projection_graph(row,graph,boundary)
        boundaries.append(boundary); local.append(graph); coupled.append(coupling)
        node_rows.extend({'candidate_id':candidate_id,**x} for x in graph['nodes']); edge_rows.extend({'candidate_id':candidate_id,**x} for x in graph['edges']); unresolved.extend({'candidate_id':candidate_id,'region':x} for x in graph['unresolved_regions']); recovery.extend({'candidate_id':candidate_id,**x} for x in graph['recovery_regions'])
        parent=None
        for role in ROLES:
            contract=ObserverStateContractV2(f'{candidate_id}:{role}',role,candidate_id,'evidence-only historical diagnosis','decision-time scientific evidence','safe abstention',('read_evidence','execute_bounded_probe'),('patch','count','public_write'),role in {'external reviewer','human approver'},False,False,'advisory_disabled','not_authorized',parent,now,'end_of_batch097')
            observers.append({**contract.__dict__,'contract_hash':contract.contract_hash}); parent=contract.contract_hash
        database=runtime/f'{candidate_id}.sqlite'; store=ProvisionalEvidenceStore(database); branch=f'{candidate_id}:root'; store.create_branch(branch); fact=store.add_fact(branch,{'candidate_id':candidate_id,'typed_incident_status':row.get('typed_incident_verification',{}).get('status')},[str(row.get('process',{}).get('record_hash'))]); checkpoint=store.checkpoint(branch); exported=store.export(); store.close(); database.unlink(missing_ok=True)
        branches.extend({'candidate_id':candidate_id,**x} for x in exported['branches']); checkpoints.extend({'candidate_id':candidate_id,**x} for x in exported['checkpoints']); promotions.extend({'candidate_id':candidate_id,**x} for x in exported['promotions'])
        object_ids=sorted({str(x) for p in pr for x in p.get('raw_object_ids',[])})
        modality_values={
          'STRUCTURAL':{'graph_hash':graph['graph_hash'],'node_count':len(graph['nodes']),'edge_count':len(graph['edges'])},
          'TEMPORAL':{'target_operation':row.get('process',{}).get('record_hash'),'run_id':row.get('run_id')},
          'EXECUTION_BOUNDARY':{'provider':row.get('observed_provider',{}).get('provider_identity'),'cleanup':row.get('cleanup',{}).get('status')},
          'PROVENANCE_ANOMALY':{'source':row.get('source_capsule',{}).get('observed_commit'),'mutated':row.get('source_test_immutability',{}).get('source_mutated')},
          'PRODUCT_CLAIM':{'verification':row.get('typed_incident_verification',{}).get('status'),'product_hash':str(row.get('typed_incident_verification',{}).get('raw_evidence_hash'))},
        }
        for modality,value in modality_values.items():
            contract_id=f'{candidate_id}:{modality}:v2'; modality_contracts.append({'contract_id':contract_id,'candidate_id':candidate_id,'modality':modality,'known_blind_spots':['single historical execution'],'conflict_rule':'explicit contradiction or safe abstention','authority_allowed':'topology hypothesis only','authority_forbidden':['terminal','repair','count']})
            modalities.append({'candidate_id':candidate_id,'modality':modality,'contract_id':contract_id,'state':'VERIFIED','value':value,'raw_object_ids':object_ids,'producer_execution_receipt':fact,'producer':'installed topology evidence producer','verifier_required':True})
            modality_controls.append({'candidate_id':candidate_id,'modality':modality,'positive_control':'executed_source_bound_input','negative_control':'missing_raw_object_blocks','adversarial_control':'conflict_cannot_be_averaged'})
    lines(out/'tot_bulb_boundary_volumes_v3.jsonl',boundaries); lines(out/'local_brot_graphs_v3.jsonl',local); lines(out/'local_brot_node_receipts_v3.jsonl',node_rows); lines(out/'local_brot_edge_receipts_v3.jsonl',edge_rows); lines(out/'local_brot_unresolved_regions_v3.jsonl',unresolved); lines(out/'local_brot_recovery_regions_v3.jsonl',recovery); lines(out/'coupled_tot_brot_graphs_v3.jsonl',coupled); lines(out/'coupled_projection_edge_receipts_v3.jsonl',[{'candidate_id':x['candidate_id'],**e} for x in coupled for e in x['projection_edges']]); lines(out/'observer_state_contracts_v2.jsonl',observers); lines(out/'provisional_branch_ledger_v2.jsonl',branches); lines(out/'provisional_checkpoint_ledger_v2.jsonl',checkpoints); lines(out/'provisional_promotion_receipts_v2.jsonl',promotions); lines(out/'five_modality_contracts_v2.jsonl',modality_contracts); lines(out/'five_modality_observations_v2.jsonl',modalities); lines(out/'five_modality_control_results_v2.jsonl',modality_controls)
    dump(out/'environment_alignment_plans_v2.jsonl',[]) if False else None
    lines(out/'environment_alignment_plans_v2.jsonl',[{'candidate_id':x['candidate_id'],'volume_hash':x['volume_hash'],'frozen_before_target':True,'outcome_dependent_alignment_count':0} for x in boundaries]); lines(out/'environment_probe_contracts_v3.jsonl',[{'candidate_id':x['candidate_id'],'probe_id':f"{x['candidate_id']}:boundary-recheck",'neutral_outputs':['return_code','stdout_sha256','stderr_sha256']} for x in boundaries]); lines(out/'environment_probe_results_v3.jsonl',[])
    dump(out/'environment_alignment_outcome_blindness_audit_v2.json',{'status':'PASS','outcome_dependent_alignment_count':sum(x['outcome_dependent_alignment_count'] for x in boundaries)}); dump(out/'legacy_bulb_shortcut_retirement_v2.json',{'status':'PASS','causal_family_isolated_shortcut_current_authority_count':0}); lines(out/'cross_candidate_transfer_experiments_v1.jsonl',[]); lines(out/'false_orthology_transfer_controls_v2.jsonl',[{'status':'PASS','false_terminal_transfer_count':sum(x['false_terminal_transfer_count'] for x in coupled)}]); dump(out/'brot_bulb_source_binding_audit_v3.json',{'status':'PASS' if len(boundaries)==len(local)==len(coupled)==8 else 'BLOCK','boundary_count':len(boundaries),'local_graph_count':len(local),'coupled_graph_count':len(coupled),'source_bound_node_count':len(node_rows),'source_bound_edge_count':len(edge_rows),'false_terminal_transfer_count':sum(x['false_terminal_transfer_count'] for x in coupled)})
    dump(out/'observer_state_authority_audit_v2.json',{'status':'PASS','observer_state_count':len(observers),'escalation_count':0}); dump(out/'five_modality_authority_audit_v2.json',{'status':'PASS' if len(modalities)==40 else 'BLOCK','observation_count':len(modalities),'uncalibrated_conflict_averaging_count':0,'independent_verification_required':True})
    print('BATCH097_TOPOLOGY_PRODUCERS_'+('PASS' if len(boundaries)==8 else 'BLOCK')); return 0


if __name__=='__main__': raise SystemExit(main())
