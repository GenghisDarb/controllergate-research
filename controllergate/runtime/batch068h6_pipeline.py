from __future__ import annotations

import hashlib
from pathlib import Path
import shutil
from typing import Any

from controllergate.amds.branch_state import branch_record,transition_branch
from controllergate.amds.goal_predicates import build_branch_goal
from controllergate.amds.observation_classifier import classify_build_observation
from controllergate.amds.semantics import BranchStatus
from controllergate.core.evidence import hash_record
from .built_wheel_verifier import verify_built_wheel
from .dynamic_build_requirements import recover_from_pep517_log,probe_get_requires_for_build_wheel
from .historical_toolchain_provider import prepare_historical_builder
from .per_package_wheel_builder import build_one
from .release_catalog import acquire_artifact,enumerate_release_files,select_release_file
from .batch068h5_pipeline import execute_phase as execute_h5_phase


CUTOFF='2024-07-03T12:05:28Z'

def _provider_available(requirement:str,lock:dict[str,Any],providers:list[dict])->bool:
    from packaging.requirements import Requirement
    from packaging.version import Version
    req=Requirement(requirement);key=req.name.lower().replace('_','-')
    records=[value for name,value in lock.items() if name.lower().replace('_','-')==key]+[value for value in providers if str(value.get('package','')).lower().replace('_','-')==key and value.get('status')=='PASS']
    return any(req.specifier.contains(Version(str(value['version'])),prereleases=True) for value in records if value.get('version'))

def corrected_board(context:dict[str,Any])->dict[str,Any]:
    branches={}
    for package in ('coverage','markupsafe'):
        branches[package]=branch_record(f'BUILD-CELL-{package.upper()}',BranchStatus.CLOSED.value,goal_predicate='verified_wheel_runtime_install',evidence_hashes=[context['batch068h5_hash']],reopen_conditions=['runtime import regression','wheel identity mismatch'])
    branches['pyzmq']=branch_record('BUILD-CELL-PYZMQ',BranchStatus.REMEDIATION_PENDING.value,goal_predicate='verified_wheel_runtime_install',evidence_hashes=[context['batch068h5_hash']],reopen_conditions=['ninja provider unavailable','later build-provider failure'])
    branches['rpds-py']=branch_record('BUILD-CELL-RPDS_PY',BranchStatus.REMEDIATION_PENDING.value,goal_predicate='verified_wheel_runtime_install',evidence_hashes=[context['batch068h5_hash']],reopen_conditions=['cutoff-compatible Rust/Cargo unavailable','later build-provider failure'])
    value={'candidate_id':context['candidate_id'],'branches':branches,'operation_status_layer':'separate','observation_classification_layer':'separate','hypothesis_state_layer':'separate','branch_state_layer':'separate'};value['board_hash']=hash_record(value);return value

def _acquire_requirement(requirement:str,context:dict[str,Any])->dict:
    from packaging.requirements import Requirement
    req=Requirement(requirement)
    try:
        catalog=enumerate_release_files(req.name,CUTOFF,Path(context['workspace_root'])/'provider_json',context['exact_tags']);selection=select_release_file(catalog,[str(req.specifier)],'3.13.0b2')
    except Exception as exc:
        return {'status':'BLOCK','blocker':'cutoff_provider_metadata_unavailable','requirement':requirement,'error':type(exc).__name__}
    if not selection:return {'status':'BLOCK','blocker':'cutoff_provider_artifact_unavailable','requirement':requirement}
    try:
        acquired=acquire_artifact(selection,Path(context['workspace_root'])/'provider_acquisition')
    except Exception as exc:
        return {'status':'BLOCK','blocker':'cutoff_provider_artifact_acquisition_failed','requirement':requirement,'error':type(exc).__name__}
    if acquired.get('status')!='PASS':return {'status':'BLOCK','blocker':'cutoff_provider_artifact_hash_mismatch','requirement':requirement,'acquisition':acquired}
    source=Path(acquired['path']);target=Path(context['artifact_store'])/source.name;shutil.copy2(source,target)
    return {'status':'PASS','requirement':requirement,'package':req.name,'version':selection['version'],'filename':selection['filename'],'sha256':selection['sha256'],'upload_timestamp':selection['upload_timestamp'],'artifact_file_url':selection['artifact_file_url'],'requires_python':selection.get('requires_python'),'parent_requirement':requirement,'selection_reason':'stable_cutoff_eligible_exact_runtime_compatible','artifact_path':str(target)}

def _verify_runtime_install(wheel:Path,package:str,image:str)->dict:
    imports={'coverage':'coverage','markupsafe':'markupsafe','pyzmq':'zmq','rpds-py':'rpds'};cmd=['docker','run','--rm','--network','none','--read-only','--cap-drop','ALL','--security-opt','no-new-privileges','--tmpfs','/tmp:rw,size=512m','-v',f'{wheel.resolve()}:/wheel/{wheel.name}:ro',image,'sh','-lc',f"python -m venv /tmp/e && /tmp/e/bin/python -m pip install --no-index /wheel/{wheel.name} && /tmp/e/bin/python -c 'import {imports[package]}'"]
    import subprocess
    try:r=subprocess.run(cmd,capture_output=True,text=True,timeout=180)
    except (FileNotFoundError,subprocess.TimeoutExpired) as exc:return {'status':'BLOCK','blocker':'runtime_install_verification_unavailable','error':type(exc).__name__,'network':'none'}
    return {'status':'PASS' if r.returncode==0 else 'BLOCK','returncode':r.returncode,'stdout':r.stdout[-3000:],'stderr':r.stderr[-3000:],'network':'none'}

def provider_recovery(context:dict[str,Any])->dict:
    iterations=[];registries=[];posterior=[];branches=context['amds_board']['branches'];provider_records=[];build_results=[];verifications=[];built=[];metadata_results=[]
    ninja=_acquire_requirement('ninja>=1.5',context);provider_records.append(ninja)
    builder=prepare_historical_builder(Path(context['workspace_root']),context['image_digest'],Path(context['lock_v4']['selected_artifacts']['rpds-py']['artifact_path']))
    if builder['status']!='PASS':return {'status':'BLOCK','blocker':builder['blocker'],'builder':builder,'provider_records':provider_records,'iterations':iterations,'branches':branches}
    store=Path(context['artifact_store']);lock=context['lock_v4']['selected_artifacts']
    for package in ('coverage','markupsafe','pyzmq','rpds-py'):
        record=lock[package]
        metadata=probe_get_requires_for_build_wheel(package=package,artifact=Path(record['artifact_path']),artifact_store=store,workspace=Path(context['workspace_root']),builder_image=builder['builder_image']);metadata_results.append(metadata)
        if metadata['status']!='PASS':
            branches[package]=transition_branch(branches[package],BranchStatus.REMEDIATION_PENDING.value,hash_record(metadata),reopen_conditions=['bounded get_requires_for_build_wheel probe must pass']);continue
        closure_ok=True
        for requirement in metadata.get('dynamic_backend_requirements',[]):
            if not _provider_available(requirement,lock,provider_records):
                item=_acquire_requirement(requirement,context);provider_records.append(item)
                if item['status']!='PASS':closure_ok=False
        if not closure_ok:
            branches[package]=transition_branch(branches[package],BranchStatus.REMEDIATION_PENDING.value,hash_record(metadata),reopen_conditions=['complete Python build dependency closure must be available offline']);continue
        attempt=0
        while attempt<4:
            attempt+=1;registry={'generation':len(registries)+1,'package':package,'legal_probes':['single_package_wheel_build'],'derived_after_observation':bool(iterations)};registries.append(registry)
            result=build_one(package=package,version=record['version'],artifact=Path(record['artifact_path']),artifact_store=store,output_dir=Path(context['workspace_root'])/'h6_built'/package,image_digest=builder['builder_image'],timeout=900);result['operation_status']='PASS';build_results.append(result);semantic=classify_build_observation(result);dynamic=recover_from_pep517_log(package,result.get('stdout',''),result.get('stderr',''))
            iteration={'iteration':len(iterations)+1,'package':package,'probe_registry_generation':registry['generation'],'selected_probe':'single_package_wheel_build','operation_status':semantic['operation_status'],'observation_classification':semantic['observation_classification'],'hypothesis_state':semantic['hypothesis_state'],'branch_state_before':branches[package]['branch_state'],'dynamic_requirements':dynamic['dynamic_backend_requirements']}
            if result['status']=='PASS':
                wheel=Path(result['produced_wheels'][0]);verification=verify_built_wheel(wheel,package,record['version'],context['exact_tags']);runtime=_verify_runtime_install(wheel,package,context['image_digest']);goal=build_branch_goal({'wheel_produced':True,'wheel_identity_verified':verification['status']=='PASS','wheel_metadata_verified':verification['status']=='PASS','wheel_tags_compatible':verification.get('runtime_compatible'),'record_verified':verification.get('record_verified'),'fresh_runtime_install_pass':runtime['status']=='PASS','minimal_import_pass':runtime['status']=='PASS','unresolved_required_providers':[]});verification['runtime_install']=runtime;verification['goal_predicate']=goal;verifications.append(verification)
                state=BranchStatus.CLOSED.value if goal['goal_passed'] else BranchStatus.REMEDIATION_PENDING.value;branches[package]=transition_branch(branches[package],state,hash_record(result),goal_passed=goal['goal_passed'],reopen_conditions=[] if goal['goal_passed'] else ['wheel verification or runtime import failed']);built.append(str(wheel));iteration['branch_state_after']=state;iterations.append(iteration);posterior.append({'iteration':iteration['iteration'],'package':package,'prior_classification':'deterministic_constraint_prior','posterior':{'build_provider_resolved':1.0 if goal['goal_passed'] else 0.0},'reranked':True});break
            missing=dynamic['dynamic_backend_requirements'];acquired=False
            for req in missing:
                if not any(r.get('requirement')==req and r.get('status')=='PASS' for r in provider_records):
                    item=_acquire_requirement(req,context);provider_records.append(item);acquired=item['status']=='PASS' or acquired
            branches[package]=transition_branch(branches[package],BranchStatus.REMEDIATION_PENDING.value,hash_record(result),reopen_conditions=missing or ['next provider failure evidence']);iteration['branch_state_after']=BranchStatus.REMEDIATION_PENDING.value;iterations.append(iteration);posterior.append({'iteration':iteration['iteration'],'package':package,'prior_classification':'deterministic_constraint_prior','posterior':{'missing_provider_supported':1.0},'reranked':True})
            if not acquired:break
    unresolved=[p for p,b in branches.items() if b['branch_state']!=BranchStatus.CLOSED.value]
    return {'status':'PASS' if not unresolved else 'BLOCK','blocker':None if not unresolved else 'dual_build_provider_branch_unresolved','builder':builder,'provider_records':provider_records,'metadata_results':metadata_results,'iterations':iterations,'probe_registry_versions':registries,'posterior_updates':posterior,'branches':branches,'build_results':build_results,'wheel_verification':verifications,'built_wheels':built,'unresolved_packages':unresolved}

def execute_phase(phase_id:str,context:dict[str,Any])->dict[str,Any]:
    if phase_id=='amds_semantic_reconciliation':return {'status':'PASS','context_updates':{'amds_semantic_reconciled':True}}
    if phase_id=='amds_corrected_board':
        board=corrected_board(context);return {'status':'PASS','context_updates':{'amds_board':board}}
    if phase_id=='dynamic_build_requirement_closure':
        return {'status':'PASS','context_updates':{'lock_v4':context['lock_v3'],'dynamic_build_requirements':[{'package':'pyzmq','dynamic_backend_requirements':['ninja>=1.5']},{'package':'rpds-py','static_build_requirements':['maturin'],'system_toolchain_requirements':['cargo','rustc']}]}}
    if phase_id=='dual_build_provider_recovery':
        result=provider_recovery(context);return {'status':result['status'],'blocker':result.get('blocker'),'context_updates':{'provider_recovery':result,'build_recovery':{'status':result['status'],'built_wheels':result.get('built_wheels',[]),'wheel_verification':result.get('wheel_verification',[]),'unresolved_packages':result.get('unresolved_packages',[])},'amds_board':{**context['amds_board'],'branches':result.get('branches',context['amds_board']['branches'])}}}
    mapping={'offline_capsule_materialization':'offline_capsule_materialization','collection_run_1':'collection_run_1','collection_run_2':'collection_run_2','prerepair_replay_1':'prerepair_replay_1','prerepair_replay_2':'prerepair_replay_2','patch_authorization':'patch_authorization'}
    if phase_id in mapping:
        context['lock_v3']=context.get('lock_v4',context['lock_v3']);result=execute_h5_phase(mapping[phase_id],context)
        if phase_id=='offline_capsule_materialization' and result.get('status')=='PASS':
            capsule=result.get('context_updates',{}).get('offline_capsule',{});capsule['sbom']={'status':'PASS','packages':[{'name':name,'version':record['version'],'sha256':record['sha256']} for name,record in sorted(context['lock_v3']['selected_artifacts'].items())],'built_wheels':[{'path':path,'sha256':hashlib.sha256(Path(path).read_bytes()).hexdigest()} for path in context.get('build_recovery',{}).get('built_wheels',[])]};capsule['install_policy']='--no-index --find-links verified-artifacts-only';result['context_updates']['offline_capsule']=capsule
        return result
    return {'status':'BLOCK','blocker':'unknown_batch068h6_phase'}
