from __future__ import annotations

import hashlib
import io
import tarfile
from pathlib import Path
from types import SimpleNamespace

import pytest

from controllergate.amds.probe_executors import PROBE_HANDLERS,PROBE_VERIFIERS,executor_contracts
from controllergate.amds.probe_registry import PROBE_TYPES
from controllergate.amds.runtime_adapter import run_amds_active_loop
from controllergate.amds.types import AmdsCell
from controllergate.amds.board import build_board
from controllergate.core.evidence import hash_record
from controllergate.runtime.batch068h7_pipeline import migrate_board_v3
from controllergate.runtime.historical_toolchain_provider import _acquire_locked_rust_dependencies,inspect_rust_image


def simple_board():
    board=build_board('candidate',[AmdsCell('BUILD-CELL-X','build','candidate',('a'*64,),reopen_conditions=('new evidence',))],[],[])
    branch={'branch_id':'BUILD-CELL-X','branch_state':'REMEDIATION_PENDING','goal_predicate':'wheel','reopen_conditions':['new evidence'],'evidence_hashes':['a'*64]};branch['state_hash']=hash_record(branch);board['branches']={'x':branch};board.pop('board_hash');board['board_hash']=hash_record(board);return board


def test_canonical_loop_closes_only_on_goal():
    probes=lambda board,history: [] if history else [{'probe_id':'p1','probe_type':'build_provider_probe','cell_id':'BUILD-CELL-X','branch_key':'x','targeted_hypotheses':['h'],'utility':1.0}]
    def factory(probe):return lambda:{'status':'PASS','operation_status':'PASS','mutation_count':0,'goal_evidence':{'wheel_produced':True,'wheel_identity_verified':True,'wheel_metadata_verified':True,'wheel_tags_compatible':True,'record_verified':True,'fresh_runtime_install_pass':True,'minimal_import_pass':True,'unresolved_required_providers':[]}}
    result=run_amds_active_loop(simple_board(),[],factory,registry_factory=probes)
    assert result['status']=='PASS';assert result['board']['branches']['x']['branch_state']=='CLOSED';assert result['posterior_updates'];assert len(result['registry_versions'])==2


def test_failed_operation_cannot_close_branch():
    probes=lambda board,history: [] if history else [{'probe_id':'p1','probe_type':'build_provider_probe','cell_id':'BUILD-CELL-X','branch_key':'x','targeted_hypotheses':['h'],'utility':1.0}]
    result=run_amds_active_loop(simple_board(),[],lambda probe:lambda:{'status':'BLOCK','operation_status':'PASS','mutation_count':0,'stderr':'missing provider','blocker':'missing_provider'},registry_factory=probes)
    assert result['board']['branches']['x']['branch_state']!='CLOSED';assert result['branches_closed']==0


def test_vacuous_completion_rejected():
    result=run_amds_active_loop(simple_board(),[],lambda probe:lambda:{},registry_factory=lambda board,history:[])
    assert result['status']=='BLOCK';assert result['vacuous_completion_rejected'] is True


def test_registry_regeneration_posterior_and_rerank():
    calls=[]
    def registry(board,history):calls.append(len(history));return [] if history else [{'probe_id':'p','probe_type':'build_provider_probe','cell_id':'BUILD-CELL-X','branch_key':'x','targeted_hypotheses':['h'],'utility':0.2}]
    result=run_amds_active_loop(simple_board(),[],lambda probe:lambda:{'status':'BLOCK','operation_status':'PASS','mutation_count':0,'stderr':'x'},registry_factory=registry)
    assert calls==[0,1];assert len(result['posterior_updates'])==1;assert result['rerank_events'][1]['derived_after_observation'] is True


def test_all_probe_contracts_are_real_and_not_applicable_is_valid():
    contracts=executor_contracts();assert set(contracts)==set(PROBE_TYPES);assert len({row['evidence_subsystem'] for row in contracts.values()})==13
    for name in PROBE_TYPES:
        observed=PROBE_HANDLERS[name]({'applicable':False,'applicability_reason':'fixture'});assert observed['observation']=='NOT_APPLICABLE';assert PROBE_VERIFIERS[name](observed)['status']=='PASS'


def test_issue_timestamp_adapter_obtains_comparison_evidence():
    observed=PROBE_HANDLERS['issue_timestamp_probe']({'issue_created_at':'2024-01-01T00:00:00Z','cutoff':'2024-07-03T00:00:00Z'});assert observed['status']=='PASS';assert observed['evidence']['decision_time_safe']


def test_command_adapter_runs_token_safety():
    observed=PROBE_HANDLERS['command_variant_probe']({'command':['python','-m','pytest'],'authority':'pyproject.toml','cwd':'.'});assert observed['status']=='PASS';assert observed['evidence']['safety']['status']=='PASS'


def test_native_test_adapter_hashes_real_file(tmp_path):
    (tmp_path/'tests').mkdir();test=tmp_path/'tests/test_x.py';test.write_text('def test_x(): pass\n')
    observed=PROBE_HANDLERS['native_test_presence_probe']({'source_root':str(tmp_path),'test_path':'tests/test_x.py'});assert observed['status']=='PASS';assert observed['evidence']['sha256']==hashlib.sha256(test.read_bytes()).hexdigest()


def test_runtime_incident_adapter_captures_redacted_evidence():
    observed=PROBE_HANDLERS['runtime_incident_probe']({'command':['python'],'cwd':'.','env':{'TOKEN':'secret'},'stack_trace':'Traceback Exception','timestamp':'2024-01-01T00:00:00+00:00'});assert observed['status']=='PASS';assert observed['evidence']['secrets_captured'] is False


def test_null_and_curvature_adapters_execute_real_subsystems():
    arm={'candidate_id':'c','repo_url':'u','commit_sha':'a','target_test_path':'t'}
    assert PROBE_HANDLERS['null_comparability_probe']({'arm_a':arm,'arm_b':arm})['status']=='PASS'
    candidate={'candidate_id':'c','patchable_source_file_count':1,'alternative_route_count':2};assert PROBE_HANDLERS['curvature_route_diversity_probe']({'candidate':candidate,'routes':[{'a':1},{'a':2}]})['status']=='PASS'


def test_full_board_v3_migration_preserves_92_cells():
    import json
    root=Path(__file__).resolve().parents[2];original=json.loads((root/'outputs/post_v2_37_hardening_batch068h5_amds_build_provider_recovery_fifth_repair/amds_active_board_nbclient_batch068h5.json').read_text())
    board=migrate_board_v3({'h5_board':original,'batch068h6_hash':'a'*64,'evidence_topology_hashes':['b'*64]});assert len(board['cells'])==92;assert {c['cell_id'] for c in board['cells']}=={c['cell_id'] for c in original['cells']}


def _completed(stdout='',stderr='',returncode=0):return SimpleNamespace(stdout=stdout,stderr=stderr,returncode=returncode)


def test_rust_image_probe_finds_absolute_cargo_and_login_difference(monkeypatch):
    calls={'inspect':0,'run':0}
    def fake(command,**kwargs):
        if command[1:3]==['image','inspect']:
            calls['inspect']+=1;return _completed('["PATH=/usr/local/cargo/bin:/usr/bin"]\n' if calls['inspect']==1 else 'null\n')
        calls['run']+=1
        out='PATH=/usr/local/cargo/bin:/usr/bin\n/usr/local/cargo/bin/cargo\ncargo 1.79.0\n' if calls['run']==1 else 'PATH=/usr/bin\n/usr/local/cargo/bin/cargo\n'
        return _completed(out)
    monkeypatch.setattr('controllergate.runtime.historical_toolchain_provider.subprocess.run',fake);result=inspect_rust_image('rust@sha256:x');assert result['cargo_binary_path']=='/usr/local/cargo/bin/cargo';assert result['login_shell_path_changed'] is True


def test_locked_cargo_acquisition_uses_absolute_binary_and_verifies_crate(tmp_path,monkeypatch):
    crate=b'crate-bytes';checksum=hashlib.sha256(crate).hexdigest();source=tmp_path/'src';source.mkdir();(source/'Cargo.toml').write_text('[package]\nname="x"\nversion="0.1.0"\n');(source/'Cargo.lock').write_text(f'version = 3\n[[package]]\nname = "dep"\nversion = "1.0.0"\nsource = "registry+https://github.com/rust-lang/crates.io-index"\nchecksum = "{checksum}"\n')
    archive=tmp_path/'source.tar.gz'
    with tarfile.open(archive,'w:gz') as tar:
        tar.add(source/'Cargo.toml',arcname='pkg/Cargo.toml');tar.add(source/'Cargo.lock',arcname='pkg/Cargo.lock')
    monkeypatch.setattr('controllergate.runtime.historical_toolchain_provider.inspect_rust_image',lambda image:{'status':'PASS','cargo_binary_path':'/usr/local/cargo/bin/cargo','classification':'cargo_binary_present_path_reset_by_login_shell'})
    commands=[]
    def fake(command,**kwargs):
        commands.append(command);mount=next(item for item in command if ':/cargo-cache:rw' in item);cache=Path(mount.split(':/cargo-cache:rw')[0]);target=cache/'registry/cache/index/dep-1.0.0.crate';target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(crate);return _completed('fetched')
    monkeypatch.setattr('controllergate.runtime.historical_toolchain_provider.subprocess.run',fake);result=_acquire_locked_rust_dependencies(tmp_path/'work',{'repo_digest':'rust@sha256:x'},archive);assert result['status']=='PASS';assert '/usr/local/cargo/bin/cargo fetch' in commands[0][-1];assert result['crate_verification'][0]['status']=='PASS'
