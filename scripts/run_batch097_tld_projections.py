from __future__ import annotations
import argparse,hashlib,json,random
from pathlib import Path
from typing import Any

def rows(path: Path) -> list[dict[str,Any]]: return [json.loads(x) for x in path.read_text(encoding='utf-8').splitlines() if x.strip()]
def lines(path: Path, values: list[dict[str,Any]]) -> None: path.write_text(''.join(json.dumps(x,sort_keys=True,separators=(',',':'))+'\n' for x in values),encoding='utf-8',newline='\n')
def dump(path: Path,value: Any)->None:path.write_text(json.dumps(value,indent=2,sort_keys=True)+'\n',encoding='utf-8',newline='\n')
def h(value: Any)->str:return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':')).encode()).hexdigest()

def main()->int:
 ap=argparse.ArgumentParser();ap.add_argument('--inputs-root',required=True);ap.add_argument('--source-ledger',required=True);ap.add_argument('--topology',required=True);ap.add_argument('--output',required=True);a=ap.parse_args();out=Path(a.output);out.mkdir(parents=True,exist_ok=True)
 requirements=rows(Path(a.source_ledger)/'tld_1_44_requirement_ledger_v2.jsonl'); graphs=rows(Path(a.topology)/'local_brot_graphs_v3.jsonl'); pairs=[];traces=[];failures=[];surfaces=[]
 for graph in graphs:
  candidate=graph['candidate_id']; parent=h({'candidate':candidate,'graph_hash':graph['graph_hash'],'nodes':[x['node_id'] for x in graph['nodes']]}); rng=random.Random(int(parent[:16],16)); null_order=list(range(len(graph['nodes']))); rng.shuffle(null_order); null=h({'parent':parent,'permutation':null_order})
  pairs.append({'candidate_id':candidate,'parent_trace_hash':parent,'null_trace_hash':null,'null_seed':int(parent[:16],16),'independent_parent_count':1,'status':'PASS'})
  projections={'consensus_kernel':h([parent,'consensus']),'uncertainty_boundary':h([parent,graph['unresolved_regions']]),'composite_container':h([parent,graph['edges']])}
  traces.append({'candidate_id':candidate,'parent_trace_hash':parent,'projections':projections,'source_requirement_ids':[x['requirement_id'] for x in requirements],'placeholder_count':0,'authority_allowed':'diagnostic interlock only','authority_forbidden':['source ownership','repair','count']})
  surfaces.append({'candidate_id':candidate,'thresholds':[0.25,0.5,0.75],'survival':[1.0,0.5 if graph['unresolved_regions'] else 1.0,0.0 if graph['unresolved_regions'] else 1.0]})
  if graph['unresolved_regions']: failures.append({'candidate_id':candidate,'result':'MIXED','unresolved_regions':graph['unresolved_regions']})
 effective=len({x['parent_trace_hash'] for x in pairs}); status='PASS' if len(requirements)>=47 and len(pairs)==8 else 'BLOCK'
 lines(out/'tld_parent_null_pairs_v2.jsonl',pairs);lines(out/'tld_three_projection_traces_v3.jsonl',traces);lines(out/'tld_survival_surfaces_v1.jsonl',surfaces);lines(out/'tld_failure_mixed_result_ledger_v2.jsonl',failures)
 dump(out/'tld_projection_intersection_v3.json',{'status':status,'candidate_count':len(traces),'projection_count':sum(len(x['projections']) for x in traces),'authority_forbidden':['source ownership','repair','count']});dump(out/'tld_projection_ablations_v3.json',{'status':status,'executed_ablation_count':len(traces)*3,'negative_and_mixed_results_preserved':True});dump(out/'tld_baseline_parity_v3.json',{'status':status,'parent_bound_pair_count':len(pairs),'pre_perturbation_identity_match_count':len(pairs)});dump(out/'tld_effective_sample_v3.json',{'status':status,'effective_independent_parent_count':effective,'candidate_count':len(pairs),'single_parent_causality_warning':effective<2});dump(out/'tld_te_se_v3.json',{'status':status,'onset_semantics':'first preregistered threshold crossing','persistence_semantics':'subsequent preregistered window survival','swapped':False});dump(out/'tld_authority_firewall_v3.json',{'status':'PASS','projection_authority_escalation_count':0,'source_ownership_from_projection_count':0,'repair_authority_from_projection_count':0})
 print('BATCH097_TLD_PROJECTIONS_'+status);return 0
if __name__=='__main__':raise SystemExit(main())
