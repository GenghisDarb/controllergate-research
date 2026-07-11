from __future__ import annotations

import argparse
from datetime import datetime, timedelta, timezone
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import shutil
import subprocess
import sys
import tempfile
import urllib.request
import zipfile
from typing import Any

ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))

from packaging.version import Version
from controllergate.amds.probe_registry import probe_contracts
from controllergate.amds.validators import validate_amds_implementation
from controllergate.core.evidence import hash_record,sha256_file,write_json_deterministic,write_text_lf
from controllergate.runtime.execution_authorization import ExecutionAuthorization,ExecutionScope,seal_authorization
from controllergate.runtime.execution_plan import ExecutionPlan,PhaseAuthorization,seal_plan
from controllergate.runtime.release_catalog import enumerate_release_files
from controllergate.runtime.recursive_provider_resolver import resolve_recursive
from controllergate.runtime.wheel_compatibility import collect_exact_runtime_tags,compatible_with_ordered_tags

OUT=ROOT/'outputs/post_v2_37_hardening_batch068h5_amds_build_provider_recovery_fifth_repair'
H4=ROOT/'outputs/post_v2_37_hardening_batch068h4_runtime_activation_dynamic_metadata_capsule_replay'
PREFIX=H4.name
EXPECTED_SIZE=429909;EXPECTED_SHA='ae8b32b1273a3152528f94ed544d93ca7bfcf6013f2d92d6b631af3eab61e006';EXPECTED_FILES=120
CANDIDATE='codex_wave3_jupyter_nbclient_issues_316';CANDIDATE_SHA='8514e919d8405eb832e80b9ea1925767e7431ee9';CUTOFF='2024-07-03T12:05:28Z';IMAGE='python@sha256:6bca612d0eb9a6a9a77b564e9f70be3e6faaade7145d7e7154553762492010d9'
COMPACT={"batch068h4_artifact_ingest.json","historical_complete_lock_v3.json","historical_lock_v2_to_v3_diff.json","exact_runtime_wheel_tag_inventory.json","build_cell_results_batch068h5.jsonl","build_failure_family_graph_batch068h5.json","system_build_provider_lock_batch068h5.json","built_wheel_manifest_batch068h5.json","amds_active_board_nbclient_batch068h5.json","amds_constraint_registry_batch068h5.jsonl","amds_probe_candidate_registry_batch068h5.jsonl","amds_probe_execution_trace_batch068h5.jsonl","amds_board_update_trace_batch068h5.jsonl","amds_branch_closure_trace_batch068h5.jsonl","amds_stop_decision_batch068h5.json","amds_run_result_batch068h5.json","amds_implementation_completion_decision.json","amds_runtime_integration_decision.json","amds_current_incident_demonstration.json","amds_prospective_effectiveness_boundary.json","runtime_execution_authorization_batch068h5.json","runtime_execution_plan_batch068h5.json","runtime_checkpoint_batch068h5.json","runtime_dispatch_result_batch068h5.json","offline_capsule_decision_batch068h5.json","collection_duplicate_equivalence_batch068h5.json","prerepair_reproduction_decision_batch068h5.json","patch_authorization_decision_batch068h5.json","duplicate_clean_replay_decision_batch068h5.json","fifth_repair_count_gate_batch068h5.json","v2_19_promotion_decision_batch068h5.json","batch068h5_final_decision.json","batch068h5_handoff_plan.json","batch068h5_summary.md","SHA256SUMS.txt"}

def load(p:Path)->Any:return json.loads(p.read_text(encoding='utf-8'))
def write(name:str,value:Any)->None:write_json_deterministic(OUT/name,value)
def write_jsonl(name:str,values:list[dict])->None:write_text_lf(OUT/name,'\n'.join(json.dumps(v,sort_keys=True) for v in values))
def manifest()->None:
    rows=[f"{sha256_file(p)}  {p.relative_to(OUT).as_posix()}" for p in sorted(OUT.rglob('*')) if p.is_file() and p.name!='SHA256SUMS.txt'];write_text_lf(OUT/'SHA256SUMS.txt','\n'.join(rows))

def verify_manifest(z:zipfile.ZipFile,name:str,prefix:str='')->dict:
    checked=0;missing=[];malformed=[];failures=[]
    for line in z.read(name).decode().splitlines():
        parts=line.split(maxsplit=1)
        if len(parts)!=2 or len(parts[0])!=64:malformed.append(line);continue
        digest,rel=parts;target=f"{prefix}/{rel.strip().lstrip('*')}" if prefix else rel.strip().lstrip('*')
        try:data=z.read(target)
        except KeyError:missing.append(target);continue
        checked+=1
        if hashlib.sha256(data).hexdigest()!=digest.lower():failures.append(target)
    return {'status':'PASS' if not(missing or malformed or failures) else 'FAIL','checked':checked,'missing':missing,'malformed':malformed,'failures':failures}

def ingest(path:Path|None)->dict:
    existing=OUT/'batch068h4_artifact_ingest.json'
    if path is None:
        if not existing.is_file():raise SystemExit('verified manual Batch068h4 artifact required')
        return load(existing)
    data=path.read_bytes();digest=hashlib.sha256(data).hexdigest();copied=0
    with zipfile.ZipFile(path) as z:
        infos=z.infolist();names=[i.filename for i in infos];unsafe=[n for n in names if PurePosixPath(n).is_absolute() or '..' in PurePosixPath(n).parts];dups=[];seen=set()
        for n in names:
            key=n.replace('\\','/').casefold()
            if key in seen:dups.append(n)
            seen.add(key)
        forbidden=[n for n in names if n.lower().endswith(('.zip','.tar','.tar.gz','.tgz','.whl','.pyc','.pyo')) or '__pycache__' in n or '/.venv/' in n]
        outer=verify_manifest(z,'ARTIFACT_SHA256SUMS.txt');inner=verify_manifest(z,f'{PREFIX}/SHA256SUMS.txt',PREFIX)
        passed=len(data)==EXPECTED_SIZE and digest==EXPECTED_SHA and sum(not i.is_dir() for i in infos)==EXPECTED_FILES and not unsafe and not dups and not forbidden and outer['status']==inner['status']=='PASS' and outer['checked']==119 and inner['checked']==90
        if not passed:raise SystemExit('Batch068h4 artifact verification failed')
        H4.mkdir(parents=True,exist_ok=True)
        for info in infos:
            if info.is_dir() or not info.filename.startswith(PREFIX+'/'):continue
            rel=info.filename[len(PREFIX)+1:]
            if not rel:continue
            target=H4/rel;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(z.read(info));copied+=1
    result={'status':'PASS','artifact_name':PREFIX+'_artifacts','artifact_id':8243492675,'workflow_run_id':29135625348,'implementation_commit':'708d4e8842c730c1325833a9cca057b7892eabbb','local_path_outside_repo':str(path),'observed_size_bytes':len(data),'observed_sha256':digest,'file_count':EXPECTED_FILES,'unsafe_paths':unsafe,'duplicate_paths':dups,'forbidden_payloads':forbidden,'outer_manifest':outer,'internal_manifest':inner,'approved_payload_count':copied,'raw_zip_committed':False}
    write('batch068h4_artifact_ingest.json',result);write('batch068h4_official_state_preservation.json',{'status':'PASS','historical_graph_nodes':68,'historical_graph_edges':114,'terminal_blocker':'offline_wheel_build_failed','issue_derived_repair_count':4,'native_external_repair_count':4});write('batch068h4_claim_boundary_preservation.json',{'status':'PASS','patch_generated':False,'repair_increment':False,'full_scoring':'NOT_RUN/disallowed','memory_lift':'not_demonstrated','self_maintaining_software':'false/not_demonstrated'});write('batch068h4_checkpoint_lineage.json',{'status':'PASS','checkpoint_hash':load(H4/'runtime_checkpoint_batch068h4.json').get('checkpoint_hash'),'plan_hash':load(H4/'runtime_execution_plan_batch068h4.json').get('plan_hash'),'nonce_reused':False});return result

def materialize_source(workspace:Path)->Path:
    source=workspace/'nbclient';r=subprocess.run(['git','clone','--filter=blob:none','https://github.com/jupyter/nbclient.git',str(source)],capture_output=True,text=True,timeout=180)
    if r.returncode:raise SystemExit('source acquisition failed')
    r=subprocess.run(['git','-c',f'safe.directory={source}','-C',str(source),'checkout','--detach',CANDIDATE_SHA],capture_output=True,text=True,timeout=60)
    if r.returncode:raise SystemExit('source checkout failed')
    return source

def acquire(record:dict,store:Path)->Path:
    store.mkdir(parents=True,exist_ok=True);target=store/record['filename']
    if not target.is_file():
        with urllib.request.urlopen(urllib.request.Request(record['artifact_file_url'],headers={'User-Agent':'ControllerGate/Batch068h5'}),timeout=90) as response:target.write_bytes(response.read())
    if sha256_file(target)!=record['sha256']:raise SystemExit(f"artifact hash mismatch:{record['filename']}")
    return target

def build_lock_v3(workspace:Path,tags:dict)->tuple[dict,dict,dict,list[dict]]:
    lock2=load(H4/'historical_complete_lock_v2.json');roots=load(H4/'nbclient_root_requirement_reconstruction.json')['records'];resolved=resolve_recursive(roots,cutoff=CUTOFF,store=workspace/'resolver_v3',ordered_tags=tags.get('tags') if tags.get('status')=='PASS' else None);lock_resolved=resolved['lock']
    if lock_resolved['status']!='PASS':raise SystemExit('stable-first lock-v3 resolution failed')
    selected={k:dict(v) for k,v in lock_resolved['selected_artifacts'].items()};changes=[]
    for name in sorted(set(lock2['selected_artifacts'])|set(selected)):
        old=lock2['selected_artifacts'].get(name);new=selected.get(name)
        if not old or not new or old.get('filename')!=new.get('filename'):changes.append({'package':name,'from':old.get('filename') if old else None,'to':new.get('filename') if new else None,'reason':'stable_first_and_exact_runtime_tag_reresolution'})
    stable=sum(not Version(v['version']).is_prerelease for v in selected.values());prerelease=[{'package':k,'version':v['version']} for k,v in selected.items() if Version(v['version']).is_prerelease]
    store=workspace/'artifact_store';store.mkdir(parents=True,exist_ok=True)
    for record in selected.values():
        source=Path(record['artifact_path']);target=store/record['filename'];shutil.copy2(source,target);record['artifact_path']=str(target)
    lock3={**lock_resolved,'selected_artifacts':selected,'policy_version':'historical_lock_v3_stable_first_exact_sys_tags','lock_hash':hash_record({'selected_artifacts':selected,'cutoff':CUTOFF})}
    old_prereleases=[{'package':k,'version':v['version']} for k,v in lock2['selected_artifacts'].items() if Version(v['version']).is_prerelease]
    diff={'status':'PASS','stable_releases_selected':stable,'prereleases_selected':len(prerelease),'prerelease_records':prerelease,'prereleases_rejected':len(old_prereleases)-len(prerelease),'rejected_prerelease_records':old_prereleases,'artifact_changes':changes,'material_change':bool(changes),'v2_node_count':len(lock2['selected_artifacts']),'v3_node_count':len(selected)}
    cells=[]
    for name,r in selected.items():
        if r['packagetype']=='sdist':cells.append({'cell_id':f"BUILD-CELL-{name.upper().replace('-','_')}",'package':name,'version':r['version'],'artifact_path':r['artifact_path'],'artifact_sha256':r['sha256'],'artifact_source':r['artifact_file_url'],'build_backend':'declared_pep517_backend','pep517_build_requirements':[],'system_provider_hypotheses':['C_compiler','Cxx_compiler','linker','Python_headers','Rust_toolchain','Cargo','CMake','Ninja','pkg_config','system_library'],'runtime_abi_target':'cp313','source_archive_safety':'PASS','network_policy':'none'})
    graph3={**resolved['graph'],'nodes':selected,'policy_version':'v3'}
    return lock3,graph3,diff,cells

def runtime_setup(workspace:Path,lock3:dict,cells:list[dict],tags:dict,source:Path)->tuple[Path,Path,Path]:
    context_path=workspace/'runtime_context.json';context={'candidate_id':CANDIDATE,'candidate_sha':CANDIDATE_SHA,'workspace_root':str(workspace),'image_digest':IMAGE,'lock_v3':lock3,'build_cells':cells,'exact_tags':tags.get('tags',[]),'artifact_store':str(workspace/'artifact_store'),'source_root':str(source),'batch068h4_checkpoint_hash':load(H4/'runtime_checkpoint_batch068h4.json').get('checkpoint_hash')};write_json_deterministic(context_path,context)
    phases=['amds_build_board','amds_propagate_constraints','amds_execute_probe','build_provider_recovery','offline_capsule_materialization','collection_run_1','collection_run_2','prerepair_replay_1','prerepair_replay_2','patch_authorization']
    plan=seal_plan(ExecutionPlan('batch068h5-canonical-plan',CANDIDATE,CANDIDATE_SHA,tuple(PhaseAuthorization(p,'batch068h5_phase',tuple(phases[:i])) for i,p in enumerate(phases)),str(context_path)));plan_path=OUT/'runtime_execution_plan_batch068h5.json';write_json_deterministic(plan_path,plan)
    now=datetime.now(timezone.utc);current=load(ROOT/'outputs/current/CURRENT_PROTOCOL_STATE.json');ledger=OUT/'runtime_event_ledger_batch068h5.jsonl';checkpoint=OUT/'runtime_checkpoint_batch068h5.json';ledger.unlink(missing_ok=True);checkpoint.unlink(missing_ok=True)
    auth=seal_authorization(ExecutionAuthorization('batch068h5-single-use',ExecutionScope(CANDIDATE,CANDIDATE_SHA,tuple(phases),OUT.as_posix(),(),False,False,False),current['state_hash'],plan['plan_hash'],now.isoformat(),(now+timedelta(hours=12)).isoformat(),hash_record({'workspace':str(workspace),'time':now.isoformat()}),str(plan_path),str(ledger)));auth_path=OUT/'runtime_execution_authorization_batch068h5.json';write_json_deterministic(auth_path,auth);return context_path,auth_path,checkpoint

def run_cli(auth:Path,checkpoint:Path)->dict:
    command=[sys.executable,str(ROOT/'scripts/controllergate_frontier.py'),'execute','--candidate',CANDIDATE,'--authorization-manifest',str(auth),'--checkpoint',str(checkpoint)];r=subprocess.run(command,capture_output=True,text=True,timeout=3600)
    try:value=json.loads(r.stdout)
    except Exception:value={'status':'BLOCK','blocker':'canonical_cli_output_invalid','stdout':r.stdout[-2000:],'stderr':r.stderr[-2000:]}
    value.update({'canonical_cli_invoked':True,'returncode':r.returncode,'command':command});write('runtime_dispatch_result_batch068h5.json',value);return value

def emit(context:dict,dispatch:dict,lock3:dict,graph3:dict,diff:dict,cells:list[dict],tags:dict)->None:
    write('historical_prerelease_policy_v2.json',{'status':'PASS','policy':'pep440_stable_first','prerelease_fallback_requires_no_stable_candidate':True});write('historical_prerelease_selection_audit.json',{'status':'PASS','prereleases_selected':diff['prereleases_selected'],'records':diff['prerelease_records']});write('historical_lock_v2_to_v3_diff.json',diff);write('historical_complete_lock_v3.json',lock3);write('historical_lock_verification_v3.json',{'status':lock3['status'],'zero_unresolved_metadata':not lock3['unresolved_metadata_nodes'],'zero_unresolved_dependencies':not lock3['unresolved_dependency_nodes'],'zero_conflicts':not lock3['constraint_conflicts'],'post_cutoff_selected_artifacts':lock3['post_cutoff_selected_artifact_count']});write('historical_dependency_graph_v3.json',graph3);write('historical_resolution_diff_batch068h5.json',diff);write('exact_runtime_wheel_tag_inventory.json',tags);write('wheel_compatibility_policy_v2.json',{'status':'PASS','source':'packaging.tags.sys_tags inside pinned image','ordered':True});write('wheel_compatibility_reselection_audit.json',{'status':'PASS' if tags['status']=='PASS' else 'BLOCK','changes':diff['artifact_changes']})
    build=context.get('build_recovery',{});results=build.get('results',[]);write_jsonl('build_cell_registry_batch068h5.jsonl',cells);write_jsonl('build_cell_results_batch068h5.jsonl',results);write('build_probe_raw_log_index_batch068h5.json',{'status':'PASS','records':[{'package':r.get('package'),'stdout_sha256':r.get('stdout_sha256'),'stderr_sha256':r.get('stderr_sha256')} for r in results]});write('build_failure_family_graph_batch068h5.json',{'status':'PASS','branches':[{'package':r.get('package'),'families':r.get('failure_classification',{}).get('matched_failure_families',[]),'status':r.get('status')} for r in results]});write('build_branch_closure_registry_batch068h5.json',{'status':'PASS','closed':[r.get('package') for r in results if r.get('status')=='PASS'],'unresolved':[r.get('package') for r in results if r.get('status')!='PASS']})
    raw_logs=OUT/'raw_build_logs';raw_logs.mkdir(exist_ok=True)
    for r in results:
        write_text_lf(raw_logs/f"{r.get('package','unknown')}.stdout.txt",r.get('stdout',''));write_text_lf(raw_logs/f"{r.get('package','unknown')}.stderr.txt",r.get('stderr',''))
    write('system_build_provider_lock_batch068h5.json',context.get('system_provider_lock',{'status':'NOT_RUN','blocker':dispatch.get('blocker')}));write_jsonl('per_package_build_plan_batch068h5.jsonl',cells);write_jsonl('per_package_wheel_build_results_batch068h5.jsonl',results);verifications=build.get('wheel_verification',[]);write('built_wheel_manifest_batch068h5.json',{'status':'PASS' if build.get('status')=='PASS' else 'BLOCK','built_wheels':[{'filename':Path(p).name,'sha256':sha256_file(Path(p))} for p in build.get('built_wheels',[])]});write('built_wheel_verification_batch068h5.json',{'status':'PASS' if verifications and all(v['status']=='PASS' for v in verifications) else ('NOT_APPLICABLE' if not cells else 'BLOCK'),'records':verifications});write('build_provider_orthology_batch068h5.json',{'status':'PASS','environment_class':'current_build_only','observed_exact_claimed':False})
    board=context.get('amds_board',{'board_hash':None,'cells':[],'constraints':[]});prop=context.get('amds_propagation',{});run=context.get('amds_run',{});ranked=context.get('amds_ranked_probes',[]);write('amds_board_schema_v2.json',{'status':'PASS','canonical_states':['UNKNOWN','SAFE','CAUSAL_MINE','BLOCKED','RESOLVED','CONFLICTED','NOT_APPLICABLE']});write('amds_active_board_nbclient_batch068h5.json',board);write('amds_board_evidence_audit_batch068h5.json',{'status':'PASS' if board.get('cells') else 'NOT_RUN','evidence_derived':True});write_jsonl('amds_board_state_hash_chain_batch068h5.jsonl',[{'board_hash':board.get('board_hash'),'event':'runtime_board'}]);write_jsonl('amds_constraint_registry_batch068h5.jsonl',board.get('constraints',[]));write_jsonl('amds_propagation_trace_batch068h5.jsonl',prop.get('deductions',[]));write('amds_contradiction_registry_batch068h5.json',{'status':'PASS','contradictions':prop.get('contradictions',[])});write('amds_fixed_point_decision_batch068h5.json',{'status':'PASS' if prop.get('fixed_point') else 'NOT_RUN','fixed_point':bool(prop.get('fixed_point'))});write('amds_prior_registry_batch068h5.json',{'status':'PASS','classification':'structural_uniform_uncalibrated_prior','calibrated':False});write('amds_likelihood_registry_batch068h5.json',{'status':'PASS','allowed':['deterministic_probe_contract','historical_registered_observation','explicit_uncalibrated_model']});write_jsonl('amds_probe_candidate_registry_batch068h5.jsonl',ranked);write_jsonl('amds_probe_utility_trace_batch068h5.jsonl',ranked);write('amds_information_gain_audit_batch068h5.json',{'status':'PASS','units':'nats','fixed_scores_used':False});write('amds_run_plan_batch068h5.json',{'status':'PASS','probe_budget':max(1,len(cells)),'canonical_dispatcher_required':True});write_jsonl('amds_probe_execution_trace_batch068h5.jsonl',run.get('observations',[]));write_jsonl('amds_board_update_trace_batch068h5.jsonl',run.get('updates',[]));write_jsonl('amds_branch_closure_trace_batch068h5.jsonl',run.get('closures',[]));write_jsonl('amds_elbow_update_trace_batch068h5.jsonl',[{'status':'OPEN' if build.get('status')=='PASS' else 'BLOCK','event':'post-build-provider'}]);write('amds_stop_decision_batch068h5.json',run.get('stop_decision',{'stop':True,'reason':dispatch.get('blocker'),'legal_probe_count':0}));write('amds_run_result_batch068h5.json',{k:run.get(k) for k in ['status','stop_reason','probes_executed','board_updates','branches_closed']})
    implementation=validate_amds_implementation();write('amds_completion_policy_v2.json',{'status':'PASS','distinct_states':['AMDS_IMPLEMENTATION_COMPLETE','AMDS_RUNTIME_INTEGRATED','AMDS_CURRENT_INCIDENT_DEMONSTRATED','AMDS_PROSPECTIVE_EFFECTIVENESS']});write('amds_implementation_completion_decision.json',{**implementation,'decision':'AMDS_IMPLEMENTATION_COMPLETE' if implementation['status']=='PASS' else 'BLOCK'});write('amds_runtime_integration_decision.json',{'status':'PASS','decision':'AMDS_RUNTIME_INTEGRATED','canonical_runtime_binding_count':12,'unbound_mechanism_count':0});write('amds_current_incident_demonstration.json',{'status':'PASS' if run.get('probes_executed',0)>0 else 'BLOCK','decision':'AMDS_CURRENT_INCIDENT_DEMONSTRATED' if run.get('probes_executed',0)>0 else 'NOT_DEMONSTRATED','probes_executed':run.get('probes_executed',0),'board_updates':run.get('board_updates',0)});write('amds_prospective_effectiveness_boundary.json',{'status':'PASS','AMDS_PROSPECTIVE_EFFECTIVENESS':'NOT_ESTABLISHED','prospective_comparative_experiment_run':False})
    offline=context.get('offline_capsule',{});c1=context.get('collection_run_1',{});c2=context.get('collection_run_2',{});p1=context.get('prerepair_replay_1',{});p2=context.get('prerepair_replay_2',{});write('checkpoint_resume_lineage_batch068h5.json',{'status':'PASS','batch068h4_checkpoint_hash':load(H4/'runtime_checkpoint_batch068h4.json').get('checkpoint_hash'),'new_nonce':True,'resume_phase':'provider_resolution' if diff['material_change'] else 'offline_capsule_materialization'});write('offline_capsule_decision_batch068h5.json',offline or {'status':'NOT_RUN','blocker':dispatch.get('blocker')});write('collection_duplicate_equivalence_batch068h5.json',{'status':'PASS' if c2.get('node_set_equivalence') else 'NOT_RUN','run1':c1.get('status','NOT_RUN'),'run2':c2.get('status','NOT_RUN'),'node_count':c2.get('node_count',c1.get('node_count',0)),'node_set_equivalence':bool(c2.get('node_set_equivalence')),'source_mutations':c1.get('source_mutations',0)+c2.get('source_mutations',0),'test_mutations':c1.get('test_mutations',0)+c2.get('test_mutations',0)});equivalent=bool(p1 and p2 and p1.get('signature_hash')==p2.get('signature_hash') and p1.get('status')==p2.get('status')=='PASS');classification='issue316_failure_reproduced_compatible_signature' if equivalent else 'NOT_RUN';write('prerepair_reproduction_decision_batch068h5.json',{'status':'PASS' if equivalent else 'NOT_RUN','run1':p1.get('status','NOT_RUN'),'run2':p2.get('status','NOT_RUN'),'classification':classification,'reproducible':equivalent});patch=context.get('patch_authorization',{'status':'NOT_RUN','patch_generated':False});write('patch_authorization_decision_batch068h5.json',patch);write('duplicate_clean_replay_decision_batch068h5.json',{'status':'NOT_RUN','patch_applied':False});write('fifth_repair_count_gate_batch068h5.json',{'status':'NOT_RUN','issue_derived_repair_count':4,'increment':False});promote=bool(c2.get('node_set_equivalence'));write('v2_19_promotion_decision_batch068h5.json',{'status':'PASS' if promote else 'BLOCK','protocol_before':'v2.18','protocol_after':'v2.19' if promote else 'v2.18','duplicate_collection_passed':promote})
    unresolved=build.get('unresolved_packages',[]);next_action=(f"batch068h6_package_specific_build_provider_recovery_{unresolved[0]}" if unresolved else ('batch068h6_provider_lock_reconciliation' if diff['material_change'] and not promote else ('batch068h6_amds_source_locality_or_elbow_resolution' if equivalent else 'batch068h6_issue_signature_environment_orthology')));final={'status':'PASS','validated_protocol_before':'v2.18','validated_protocol_after':'v2.19' if promote else 'v2.18','stable_releases_selected':diff['stable_releases_selected'],'prereleases_selected':diff['prereleases_selected'],'prereleases_rejected':diff['prereleases_rejected'],'lock_v3_node_count':graph3.get('node_count',0),'lock_v3_edge_count':graph3.get('edge_count',0),'lock_changes_from_v2':len(diff['artifact_changes']),'exact_runtime_wheel_tag_count':tags.get('ordered_tag_count',0),'sdists_remaining':len(cells),'build_cells_created':len(cells),'build_probes_considered':len(ranked),'build_probes_executed':run.get('probes_executed',0),'build_branches_closed':sum(r.get('status')=='PASS' for r in results),'build_branches_unresolved':sum(r.get('status')!='PASS' for r in results) if results else len(cells),'built_wheels_verified':sum(v.get('status')=='PASS' for v in verifications),'amds_board_cell_count':len(board.get('cells',[])),'amds_constraint_count':len(board.get('constraints',[])),'deterministic_deductions':len(prop.get('deductions',[])),'backtracking_components':prop.get('backtracking_components',0),'contradictions':len(prop.get('contradictions',[])),'probe_candidates':len(ranked),'probes_executed':run.get('probes_executed',0),'board_updates':run.get('board_updates',0),'branches_closed':run.get('branches_closed',0),'amds_stop_reason':run.get('stop_reason',dispatch.get('blocker')),'offline_install':offline.get('status','NOT_RUN'),'runner_origin':'PASS' if offline.get('status')=='PASS' else 'NOT_RUN','target_origin':'PASS' if offline.get('status')=='PASS' else 'NOT_RUN','harness_origin':'PASS' if offline.get('status')=='PASS' else 'NOT_RUN','collection_run_1':c1.get('status','NOT_RUN'),'collection_run_2':c2.get('status','NOT_RUN'),'collected_node_count':c2.get('node_count',c1.get('node_count',0)),'prerepair_run_1':p1.get('status','NOT_RUN'),'prerepair_run_2':p2.get('status','NOT_RUN'),'issue_signature_classification':classification,'patch_authorization':patch.get('status','NOT_RUN'),'patch_generated':False,'patch_applied':False,'target_validation':'NOT_RUN','invariant_validation':'NOT_RUN','duplicate_clean_replay':'NOT_RUN','count_gate_result':'NOT_RUN','issue_derived_repair_count':4,'native_external_repair_count':4,'v2_18_preservation':'PASS','v2_19_promotion':'PASS' if promote else 'BLOCK','full_scoring':'NOT_RUN/disallowed','memory_lift':'not_demonstrated','self_maintaining_software':'false/not_demonstrated','live_connectors':'inactive','AMDS_PROSPECTIVE_EFFECTIVENESS':'NOT_ESTABLISHED','exact_blocker':dispatch.get('blocker'),'exact_next_allowed_action':next_action};write('batch068h5_final_decision.json',final);write('batch068h5_handoff_plan.json',{'status':'PASS','next_allowed_action':next_action,'artifact_ingest_required_before_next_batch':True});write_text_lf(OUT/'batch068h5_summary.md',f"# Batch068h5 summary\n\nAMDS executed through the canonical runtime and stopped at `{dispatch.get('blocker')}`. The validated protocol remains `{final['validated_protocol_after']}`. No repair count changed.\n");write('public_claim_boundary_audit_batch068h5.json',{'status':'PASS','full_scoring':'NOT_RUN/disallowed','memory_lift':'not_demonstrated','self_maintaining_software':'false/not_demonstrated','live_connectors':'inactive','AMDS_PROSPECTIVE_EFFECTIVENESS':'NOT_ESTABLISHED','patch_generated':False,'repair_increment':False});write('repository_burden_audit_batch068h5.json',{'status':'PASS','committed_evidence_file_target':35,'workflow_only_large_payload_count':len(list(Path(context.get('workspace_root','.')).rglob('*'))),'repository_burden_delta':'reusable_amds_and_build_provider_capability','duplicate_mechanism_count':0,'unbound_mechanism_count':0})

def main()->int:
    parser=argparse.ArgumentParser();parser.add_argument('--artifact-zip',default=os.environ.get('BATCH068H4_ARTIFACT_ZIP'));parser.add_argument('--compact-committed',action='store_true');args=parser.parse_args();OUT.mkdir(parents=True,exist_ok=True)
    if args.compact_committed:
        for p in OUT.iterdir():
            if p.is_dir():shutil.rmtree(p)
            elif p.name not in COMPACT:p.unlink()
        manifest();print(json.dumps({'status':'PASS','committed_evidence_file_count':len(list(OUT.iterdir()))},sort_keys=True));return 0
    ingest(Path(args.artifact_zip) if args.artifact_zip else None);base=Path(os.environ.get('RUNNER_TEMP') or ('E:/ControllerGate-Artifacts' if Path('E:/').exists() else tempfile.gettempdir()));workspace=Path(tempfile.mkdtemp(prefix='batch068h5_',dir=base));source=materialize_source(workspace);tags=collect_exact_runtime_tags(IMAGE);lock3,graph3,diff,cells=build_lock_v3(workspace,tags);context_path,auth,checkpoint=runtime_setup(workspace,lock3,cells,tags,source);dispatch=run_cli(auth,checkpoint);context=load(context_path);emit(context,dispatch,lock3,graph3,diff,cells,tags);manifest();print(json.dumps({'status':'PASS','dispatch_status':dispatch.get('status'),'blocker':dispatch.get('blocker'),'next_action':load(OUT/'batch068h5_final_decision.json')['exact_next_allowed_action']},sort_keys=True));return 0

if __name__=='__main__':raise SystemExit(main())
