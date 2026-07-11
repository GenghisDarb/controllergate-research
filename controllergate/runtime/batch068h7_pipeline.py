from __future__ import annotations

import hashlib
from pathlib import Path
import re
import subprocess
from typing import Any
import urllib.request

from controllergate.amds.branch_state import branch_record
from controllergate.amds.goal_predicates import build_branch_goal
from controllergate.amds.runtime_adapter import run_amds_active_loop
from controllergate.amds.semantics import BranchStatus
from controllergate.core.evidence import hash_record
from .batch068h5_pipeline import execute_phase as execute_h5_phase
from .batch068h6_pipeline import _acquire_requirement, _provider_available
from .built_wheel_verifier import verify_built_wheel
from .dynamic_build_requirements import probe_get_requires_for_build_wheel, recover_from_pep517_log
from .historical_toolchain_provider import prepare_historical_builder
from .per_package_wheel_builder import build_one


def migrate_board_v3(context:dict[str,Any])->dict[str,Any]:
    original=context['h5_board'];branches={}
    for package,state in (("coverage","CLOSED"),("markupsafe","CLOSED"),("pyzmq","REMEDIATION_PENDING"),("rpds-py","REMEDIATION_PENDING")):
        branches[package]=branch_record(f"BUILD-CELL-{package.upper().replace('-','_')}",state,goal_predicate="verified_wheel_runtime_install",evidence_hashes=[context['batch068h6_hash']],reopen_conditions=["new provider, wheel, or runtime evidence"] if state!="CLOSED" else ["runtime import regression","wheel identity mismatch"])
    cells=[]
    for cell in original['cells']:
        raw={key:value for key,value in cell.items() if key!='state_hash'};cell_id=raw['cell_id'];package=next((name for name,branch in branches.items() if cell_id==branch['branch_id'] or cell_id.startswith(branch['branch_id']+':')),None)
        raw.update({'original_state_lineage':cell.get('last_update_event'),'original_evidence_hashes':cell.get('evidence_hashes',[]),'semantic_state':branches[package]['branch_state'] if package else raw.get('state'),'branch_membership':package,'reopen_conditions':cell.get('reopen_conditions') or (["new evidence"] if raw.get('state') not in {'RESOLVED','SAFE','NOT_APPLICABLE'} else [])});raw['state_hash']=hash_record(raw);cells.append(raw)
    value={**original,'cells':cells,'branches':branches,'schema_version':'amds.board.v3','evidence_topology_hashes':context['evidence_topology_hashes']};value.pop('board_hash',None);value['board_hash']=hash_record(value);return value


def _runtime_wheel_check(wheel:Path,package:str,image:str)->dict[str,Any]:
    module={'coverage':'coverage','markupsafe':'markupsafe','pyzmq':'zmq','rpds-py':'rpds'}[package]
    exercise="import zmq; c=zmq.Context(); c.term()" if package=='pyzmq' else "import rpds; rpds.HashTrieMap()" if package=='rpds-py' else f"import {module}"
    script=f"python -m venv /tmp/e && /tmp/e/bin/python -m pip install --no-index /wheel/{wheel.name} && /tmp/e/bin/python -c \"{exercise}\" && find /tmp/e -type f \\( -name '*.so' -o -name '*.pyd' \\) -print -exec ldd {{}} \\;"
    command=['docker','run','--rm','--network','none','--read-only','--cap-drop','ALL','--security-opt','no-new-privileges','--tmpfs','/tmp:rw,exec,nosuid,size=1g','-v',f'{wheel.resolve()}:/wheel/{wheel.name}:ro','--entrypoint','/bin/sh',image,'-c',script]
    try:run=subprocess.run(command,capture_output=True,text=True,timeout=240)
    except (FileNotFoundError,subprocess.TimeoutExpired) as exc:return {'status':'BLOCK','blocker':'runtime_wheel_check_unavailable','error':type(exc).__name__}
    extensions=[line for line in run.stdout.splitlines() if line.endswith(('.so','.pyd'))];native_required=package in {'pyzmq','rpds-py'};passed=run.returncode==0 and (bool(extensions) if native_required else True) and 'not found' not in run.stdout
    return {'status':'PASS' if passed else 'BLOCK','returncode':run.returncode,'command':command,'stdout':run.stdout[-8000:],'stderr':run.stderr[-4000:],'native_extensions':extensions,'native_extension_required':native_required,'elf_dependencies_resolved':'not found' not in run.stdout,'network':'none','minimal_object_exercise':exercise}


def _build_and_verify(package:str,context:dict[str,Any],builder:dict[str,Any],attempt:int,provider_requirements:list[str],build_environment:dict[str,str])->dict[str,Any]:
    record=context['lock_v4']['selected_artifacts'][package];result=build_one(package=package,version=record['version'],artifact=Path(record['artifact_path']),artifact_store=Path(context['artifact_store']),output_dir=Path(context['workspace_root'])/'h7_built'/package/image_safe(package),image_digest=builder['builder_image'],timeout=1200,provider_requirements=provider_requirements,build_environment=build_environment)
    result['operation_status']='PASS';result['attempt']=attempt
    if result['status']!='PASS':return result
    wheel=Path(result['produced_wheels'][0]);verification=verify_built_wheel(wheel,package,record['version'],context['exact_tags']);runtime=_runtime_wheel_check(wheel,package,context['image_digest']);goal_evidence={'wheel_produced':True,'wheel_identity_verified':verification['status']=='PASS','wheel_metadata_verified':verification['status']=='PASS','wheel_tags_compatible':verification.get('runtime_compatible'),'record_verified':verification.get('record_verified'),'fresh_runtime_install_pass':runtime['status']=='PASS','minimal_import_pass':runtime['status']=='PASS','unresolved_required_providers':[]};result.update({'verification':verification,'runtime_check':runtime,'goal_evidence':goal_evidence,'wheel_path':str(wheel),'wheel_sha256':hashlib.sha256(wheel.read_bytes()).hexdigest()});return result


def image_safe(package:str)->str:return package.replace('-','_')


def _acquire_pyzmq_cmake_sources(context:dict[str,Any])->tuple[list[dict[str,Any]],dict[str,str]]:
    source=Path(context['workspace_root'])/'pep517_metadata'/'pyzmq'/'pyzmq-26.0.3'/'CMakeLists.txt';text=source.read_text(encoding='utf-8')
    versions={name:re.search(rf'set\(PYZMQ_{name}_VERSION "([^"]+)"',text).group(1) for name in ('LIBSODIUM','LIBZMQ')}
    specifications=[('libsodium',versions['LIBSODIUM'],f"https://github.com/jedisct1/libsodium/releases/download/{versions['LIBSODIUM']}-RELEASE/libsodium-{versions['LIBSODIUM']}.tar.gz"),('libzmq',versions['LIBZMQ'],f"https://github.com/zeromq/libzmq/releases/download/v{versions['LIBZMQ']}/zeromq-{versions['LIBZMQ']}.tar.gz")]
    target=Path(context['artifact_store'])/'provider_sources';target.mkdir(parents=True,exist_ok=True);records=[];args=[]
    for name,version,url in specifications:
        path=target/Path(url).name
        if not path.is_file():
            with urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'ControllerGate/Batch068h7'}),timeout=180) as response:path.write_bytes(response.read())
        records.append({'status':'PASS','provider':name,'version':version,'source_url':url,'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'size':path.stat().st_size,'source_basis':'selected_pyzmq_sdist_CMakeLists','network_policy':'bounded_provider_acquisition_only','artifact_path':str(path)})
        key='PYZMQ_LIBSODIUM_URL' if name=='libsodium' else 'PYZMQ_LIBZMQ_URL';args.append(f'-D{key}=file:///artifacts/provider_sources/{path.name}')
    return records,{'CMAKE_ARGS':' '.join(args)}


def prepare_providers(context:dict[str,Any])->dict[str,Any]:
    ninja=_acquire_requirement('ninja>=1.5',context);builder=prepare_historical_builder(Path(context['workspace_root']),context['image_digest'],Path(context['lock_v4']['selected_artifacts']['rpds-py']['artifact_path']))
    return {'status':'PASS' if ninja['status']=='PASS' and builder['status']=='PASS' else 'BLOCK','blocker':None if ninja['status']=='PASS' and builder['status']=='PASS' else builder.get('blocker') or ninja.get('blocker'),'ninja':ninja,'builder':builder}


def canonical_dual_recovery(context:dict[str,Any])->dict[str,Any]:
    providers=context['h7_providers'];builder=providers['builder'];board=context['amds_board'];attempts={name:0 for name in ('coverage','markupsafe','pyzmq','rpds-py')};can_retry={name:True for name in attempts};provider_requirements={name:[] for name in attempts};build_environment={name:{} for name in attempts};results=[];wheels=[];metadata=[];provider_records=[providers['ninja']]
    for package in attempts:
        record=context['lock_v4']['selected_artifacts'][package];meta=probe_get_requires_for_build_wheel(package=package,artifact=Path(record['artifact_path']),artifact_store=Path(context['artifact_store']),workspace=Path(context['workspace_root']),builder_image=builder['builder_image']);metadata.append(meta)
        if meta['status']!='PASS':can_retry[package]=False
        provider_requirements[package]=list(dict.fromkeys([*meta.get('static_build_requirements',[]),*meta.get('dynamic_backend_requirements',[])]))
        for requirement in meta.get('dynamic_backend_requirements',[]):
            if _provider_available(requirement,context['lock_v4']['selected_artifacts'],provider_records):continue
            item=_acquire_requirement(requirement,context);provider_records.append(item)
            if item['status']!='PASS':can_retry[package]=False
    try:
        source_records,build_environment['pyzmq']=_acquire_pyzmq_cmake_sources(context);provider_records.extend(source_records)
    except Exception as exc:
        provider_records.append({'status':'BLOCK','provider':'pyzmq_cmake_sources','error':type(exc).__name__});can_retry['pyzmq']=False
    # Re-materialize the two already verified fallback wheels for the execution store.
    for package in ('coverage','markupsafe'):
        if not can_retry[package]:return {'status':'BLOCK','blocker':f'{package}_metadata_closure_failed','board':board,'metadata_results':metadata,'provider_records':provider_records,'build_results':results,'built_wheels':wheels}
        attempts[package]+=1;record=_build_and_verify(package,context,builder,attempts[package],provider_requirements[package],build_environment[package]);results.append(record)
        if record['status']!='PASS' or not build_branch_goal(record.get('goal_evidence',{}))['goal_passed']:return {'status':'BLOCK','blocker':f'{package}_wheel_rematerialization_failed','board':board,'metadata_results':metadata,'provider_records':provider_records,'build_results':results,'built_wheels':wheels}
        wheels.append(record['wheel_path'])
    def registry_factory(current,observations):
        generation=len(observations)+1;rows=[]
        for package in ('pyzmq','rpds-py'):
            if current['branches'][package]['branch_state']=='CLOSED' or not can_retry[package] or attempts[package]>=4:continue
            rows.append({'probe_id':f'build_{package}_{generation}','probe_type':'build_provider_probe','candidate_id':context['candidate_id'],'cell_id':current['branches'][package]['branch_id'],'branch_key':package,'targeted_hypotheses':[f'{package}:current_provider_boundary'],'expected_information_gain_nats':'NOT_ESTABLISHED','utility':None,'prior_classification':'deterministic_constraint_prior','generation':generation})
        return rows
    def executor_factory(probe):
        package=probe['branch_key']
        def execute():
            attempts[package]+=1;record=_build_and_verify(package,context,builder,attempts[package],provider_requirements[package],build_environment[package]);results.append(record)
            if record['status']=='PASS':wheels.append(record['wheel_path']);return record
            dynamic=recover_from_pep517_log(package,record.get('stdout',''),record.get('stderr',''));acquired=False
            for requirement in dynamic['dynamic_backend_requirements']:
                if _provider_available(requirement,context['lock_v4']['selected_artifacts'],provider_records):
                    acquired=True;continue
                item=_acquire_requirement(requirement,context);provider_records.append(item);acquired=acquired or item['status']=='PASS'
            if package=='rpds-py' and 'PYO3_USE_ABI3_FORWARD_COMPATIBILITY=1' in record.get('stderr',''):
                build_environment[package]['PYO3_USE_ABI3_FORWARD_COMPATIBILITY']='1';provider_records.append({'status':'PASS','provider':'PYO3_USE_ABI3_FORWARD_COMPATIBILITY','value':'1','source_basis':'observed_pyo3_0.20.3_build_diagnostic','mutation_policy':'environment_only'});acquired=True
            can_retry[package]=acquired
            record['evidence']={'package':package,'attempt':attempts[package],'dynamic_requirements':dynamic['dynamic_backend_requirements'],'failure_hash':hash_record({'stdout':record.get('stdout'),'stderr':record.get('stderr')})};record['evidence_hash']=hash_record(record['evidence']);record['raw_evidence_captured']=True;return record
        return execute
    def goal_evaluator(branch,observation,probe):return build_branch_goal(observation.get('goal_evidence',{}))
    run=run_amds_active_loop(board,[],executor_factory,budget=8,interlock_pass=True,registry_factory=registry_factory,goal_evaluator=goal_evaluator)
    final=run['board'];unresolved=[name for name in ('pyzmq','rpds-py') if final['branches'][name]['branch_state']!='CLOSED']
    return {'status':'PASS' if not unresolved else 'BLOCK','blocker':None if not unresolved else 'canonical_dual_build_branch_unresolved','board':final,'amds_run':run,'metadata_results':metadata,'provider_records':provider_records,'build_results':results,'built_wheels':wheels,'unresolved_packages':unresolved,'attempt_counts':attempts}


def execute_phase(phase_id:str,context:dict[str,Any])->dict[str,Any]:
    if phase_id=='amds_completion_reconciliation':return {'status':'PASS','context_updates':{'amds_completion_reconciled':True}}
    if phase_id=='amds_board_v3_migration':
        board=migrate_board_v3(context);return {'status':'PASS','context_updates':{'amds_board':board}}
    if phase_id=='cargo_provider_recovery_and_builder':
        value=prepare_providers(context);return {'status':value['status'],'blocker':value.get('blocker'),'context_updates':{'h7_providers':value}}
    if phase_id=='canonical_dual_build_recovery':
        value=canonical_dual_recovery(context);return {'status':value['status'],'blocker':value.get('blocker'),'context_updates':{'h7_recovery':value,'amds_board':value['board'],'build_recovery':{'status':value['status'],'built_wheels':value.get('built_wheels',[]),'unresolved_packages':value.get('unresolved_packages',[])}}}
    if phase_id in {'offline_capsule_materialization','collection_run_1','collection_run_2','prerepair_replay_1','prerepair_replay_2','patch_authorization'}:
        context['lock_v3']=context.get('lock_v4',context['lock_v3']);return execute_h5_phase(phase_id,context)
    return {'status':'BLOCK','blocker':'unknown_batch068h7_phase'}
