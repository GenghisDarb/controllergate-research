from __future__ import annotations
import hashlib,inspect,json
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
from controllergate.amds.runtime_adapter import run_amds_active_loop
from controllergate.amds.probe_executors import executor_contracts
from controllergate.amds.probe_registry import PROBE_TYPES
from controllergate.core.evidence import hash_record
from controllergate.protocols.v2_18_evidence_derived_topology_historical_provider import runtime_capabilities
OUT=ROOT/'outputs/post_v2_37_hardening_batch068h7_amds_canonical_engine_cargo_runtime_completion';H6=ROOT/'outputs/post_v2_37_hardening_batch068h6_amds_semantic_dual_build_provider_recovery'
REQUIRED={'batch068h6_artifact_ingest.json','batch068h6_amds_completion_reconciliation.json','batch068h6_canonical_loop_mismatch.json','batch068h6_probe_adapter_depth_audit.json','amds_board_v3_migration.json','amds_active_board_v3_batch068h7.json','amds_board_v3_hash_chain_batch068h7.jsonl','amds_board_v3_evidence_preservation_audit.json','amds_probe_adapter_registry_v3.json','amds_probe_adapter_execution_audit_batch068h7.json','amds_probe_adapter_verifier_audit_batch068h7.json','cargo_provider_completion_summary_batch068h7.json','historical_builder_v2_summary_batch068h7.json','amds_canonical_iteration_trace_batch068h7.jsonl','amds_canonical_probe_registry_versions_batch068h7.jsonl','amds_canonical_posterior_trace_batch068h7.jsonl','amds_canonical_board_updates_batch068h7.jsonl','amds_canonical_branch_trace_batch068h7.jsonl','amds_canonical_stop_decision_batch068h7.json','amds_implementation_completion_decision_batch068h7.json','amds_runtime_integration_decision_batch068h7.json','amds_current_incident_demonstration_batch068h7.json','amds_prospective_effectiveness_boundary_batch068h7.json','pyzmq_build_summary_batch068h7.json','pyzmq_branch_final_state_batch068h7.json','rpds_build_summary_batch068h7.json','rpds_branch_final_state_batch068h7.json','runtime_execution_authorization_batch068h7.json','runtime_execution_plan_batch068h7.json','runtime_checkpoint_batch068h7.json','runtime_dispatch_result_batch068h7.json','downstream_gate_decisions_batch068h7.json','batch068h7_final_decision.json','batch068h7_summary.md','repository_burden_audit_batch068h7.json','public_claim_boundary_audit_batch068h7.json','SHA256SUMS.txt'}
def load(name):return json.loads((OUT/name).read_text(encoding='utf-8'))
def rows(name):return [json.loads(line) for line in (OUT/name).read_text(encoding='utf-8').splitlines() if line.strip()]
def main():
    errors=[];missing=sorted(name for name in REQUIRED if not (OUT/name).is_file())
    if missing:print('missing:'+','.join(missing));return 1
    for line in (OUT/'SHA256SUMS.txt').read_text().splitlines():
        digest,rel=line.split(maxsplit=1);path=OUT/rel.strip().lstrip('*')
        if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest()!=digest:errors.append('manifest_mismatch:'+rel)
    ingest=load('batch068h6_artifact_ingest.json')
    if not(ingest.get('status')=='PASS' and ingest.get('observed_size_bytes')==73709 and ingest.get('observed_sha256')=='388c81ec6b0292121ee438cd1d031aa114df8f7e30df99d5f6b71f59694adcb2' and ingest.get('file_count')==84 and ingest.get('outer_manifest',{}).get('checked')==83 and ingest.get('internal_manifest',{}).get('checked')==72 and not ingest.get('unsafe_paths') and not ingest.get('duplicate_paths') and not ingest.get('forbidden_payloads')):errors.append('Batch068h6 identity invalid')
    checked=0
    for line in (H6/'SHA256SUMS.txt').read_text().splitlines():
        digest,rel=line.split(maxsplit=1);path=H6/rel.strip().lstrip('*');checked+=1
        if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest()!=digest:errors.append('Batch068h6 internal mismatch:'+rel)
    if checked!=72:errors.append('Batch068h6 internal manifest count invalid')
    reconciliation=load('batch068h6_amds_completion_reconciliation.json')
    if reconciliation.get('AMDS_CANONICAL_ACTIVE_ENGINE')!='BLOCK' or reconciliation.get('AMDS_REAL_PROBE_ADAPTER_COMPLETENESS')!='PARTIAL':errors.append('H6 completion reconciliation invalid')
    source=inspect.getsource(run_amds_active_loop)
    if 'state="RESOLVED" if observation.get("status")=="PASS"' in source or 'registry_factory' not in source or 'posterior_updates' not in source or 'goal_evaluator' not in source:errors.append('canonical AMDS loop not corrected')
    capabilities=runtime_capabilities()
    if capabilities['bindings'].get('run_amds_active_loop')!='controllergate.amds.runtime_adapter:run_amds_active_loop' or 'execute_batch068h7_phase' not in capabilities['bindings']:errors.append('canonical binding invalid')
    contracts=executor_contracts()
    if set(contracts)!=set(PROBE_TYPES) or len({row['evidence_subsystem'] for row in contracts.values()})!=13 or any('presence' in row['evidence_subsystem'] for row in contracts.values()):errors.append('real probe adapters incomplete')
    adapter=load('amds_probe_adapter_execution_audit_batch068h7.json')
    if adapter.get('presence_only_adapter_count')!=0 or adapter.get('evidence_subsystem_count')!=13:errors.append('probe adapter audit invalid')
    migration=load('amds_board_v3_migration.json');board=load('amds_active_board_v3_batch068h7.json')
    if migration.get('original_cell_count')!=92 or migration.get('migrated_cell_count')!=92 or len(board.get('cells',[]))!=92 or not load('amds_board_v3_evidence_preservation_audit.json').get('original_ids_preserved'):errors.append('full board migration invalid')
    chain=rows('amds_board_v3_hash_chain_batch068h7.jsonl');previous=None
    for row in chain:
        supplied=row.pop('entry_hash',None)
        if row.get('previous_hash')!=previous or supplied!=hash_record(row):errors.append('board v3 hash chain invalid')
        previous=supplied
    cargo=load('cargo_provider_completion_summary_batch068h7.json')
    if cargo.get('status')=='PASS' and not(cargo.get('cargo_binary')=='/usr/local/cargo/bin/cargo' and cargo.get('cargo_provider_file_count',0)>0 and cargo.get('provider_manifest_hash') and cargo.get('crate_verification_pass')):errors.append('Cargo provider closure invalid')
    if cargo.get('status')!='PASS' and not cargo.get('blocker'):errors.append('Cargo blocker missing')
    builder=load('historical_builder_v2_summary_batch068h7.json')
    if builder.get('status')=='PASS' and not(builder.get('offline_probe') and builder.get('toolchain_authority',{}).get('exact_historical_status') in {'cutoff_compatible_toolchain_current_container','observed_exact_historical_builder'}):errors.append('builder authority or offline probe invalid')
    iterations=rows('amds_canonical_iteration_trace_batch068h7.jsonl');registries=rows('amds_canonical_probe_registry_versions_batch068h7.jsonl');posteriors=rows('amds_canonical_posterior_trace_batch068h7.jsonl');updates=rows('amds_canonical_board_updates_batch068h7.jsonl')
    if iterations and not(len(registries)>=len(iterations) and len(posteriors)==len(iterations) and len(updates)==len(iterations)):errors.append('canonical loop trace incomplete')
    implementation=load('amds_implementation_completion_decision_batch068h7.json')
    if implementation.get('status')=='PASS' and not iterations:errors.append('vacuous AMDS completion')
    for package in ('pyzmq','rpds'):
        summary=load(f'{package}_build_summary_batch068h7.json');branch=load(f'{package}_branch_final_state_batch068h7.json')['branch']
        if branch.get('branch_state')=='CLOSED' and not(summary.get('wheel_identity') and summary.get('runtime_check',{}).get('status')=='PASS'):errors.append(package+' false closure')
    downstream=load('downstream_gate_decisions_batch068h7.json')
    if downstream.get('collection_run_2',{}).get('status')=='PASS' and not(downstream.get('collection_run_1',{}).get('status')=='PASS' and downstream.get('collection_run_1',{}).get('node_count',0)>0):errors.append('collection 2 bypass')
    if downstream.get('prerepair_run_1',{}).get('status')=='PASS' and not downstream.get('duplicate_collection'):errors.append('prerepair bypass')
    if downstream.get('patch_authorization',{}).get('status')=='PASS' and not downstream.get('prerepair_reproducible'):errors.append('patch bypass')
    final=load('batch068h7_final_decision.json')
    if final.get('issue_derived_repair_count') not in {4,5} or final.get('native_external_repair_count')!=4 or final.get('full_scoring')!='NOT_RUN/disallowed' or final.get('memory_lift')!='not_demonstrated' or final.get('self_maintaining_software')!='false/not_demonstrated' or final.get('live_connectors')!='inactive' or final.get('AMDS_PROSPECTIVE_EFFECTIVENESS')!='NOT_ESTABLISHED' or final.get('validated_protocol_after')!='v2.18':errors.append('claim boundary invalid')
    if len([path for path in OUT.iterdir() if path.is_file()])>40 and not (OUT/'repository_burden_audit_batch068h7.json').is_file():errors.append('evidence burden unbounded')
    if errors:print('\n'.join(errors));return 1
    print('Batch068h7 canonical AMDS/Cargo/runtime completion audit PASS');return 0
if __name__=='__main__':raise SystemExit(main())
