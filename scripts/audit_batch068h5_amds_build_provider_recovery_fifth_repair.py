from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))

from controllergate.amds.probe_registry import PROBE_TYPES,probe_contracts
from controllergate.amds.validators import validate_amds_implementation
from controllergate.protocols.v2_18_evidence_derived_topology_historical_provider import runtime_capabilities

OUT=ROOT/'outputs/post_v2_37_hardening_batch068h5_amds_build_provider_recovery_fifth_repair'
REQUIRED={"batch068h4_artifact_ingest.json","historical_complete_lock_v3.json","historical_lock_v2_to_v3_diff.json","exact_runtime_wheel_tag_inventory.json","build_cell_results_batch068h5.jsonl","build_failure_family_graph_batch068h5.json","system_build_provider_lock_batch068h5.json","built_wheel_manifest_batch068h5.json","amds_active_board_nbclient_batch068h5.json","amds_constraint_registry_batch068h5.jsonl","amds_probe_candidate_registry_batch068h5.jsonl","amds_probe_execution_trace_batch068h5.jsonl","amds_board_update_trace_batch068h5.jsonl","amds_branch_closure_trace_batch068h5.jsonl","amds_stop_decision_batch068h5.json","amds_run_result_batch068h5.json","amds_implementation_completion_decision.json","amds_runtime_integration_decision.json","amds_current_incident_demonstration.json","amds_prospective_effectiveness_boundary.json","runtime_dispatch_result_batch068h5.json","offline_capsule_decision_batch068h5.json","collection_duplicate_equivalence_batch068h5.json","prerepair_reproduction_decision_batch068h5.json","patch_authorization_decision_batch068h5.json","duplicate_clean_replay_decision_batch068h5.json","fifth_repair_count_gate_batch068h5.json","v2_19_promotion_decision_batch068h5.json","batch068h5_final_decision.json","batch068h5_handoff_plan.json","batch068h5_summary.md","SHA256SUMS.txt"}

def load(name:str):return json.loads((OUT/name).read_text(encoding='utf-8'))
def rows(name:str):return [json.loads(line) for line in (OUT/name).read_text(encoding='utf-8').splitlines() if line.strip()]

def main()->int:
    errors=[];missing=sorted(name for name in REQUIRED if not (OUT/name).is_file())
    if missing:errors.append('missing:'+','.join(missing))
    if errors:print('\n'.join(errors));return 1
    for line in (OUT/'SHA256SUMS.txt').read_text().splitlines():
        digest,rel=line.split(maxsplit=1);path=OUT/rel.strip().lstrip('*')
        if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest()!=digest:errors.append('manifest_mismatch:'+rel)
    ingest=load('batch068h4_artifact_ingest.json')
    if not(ingest.get('status')=='PASS' and ingest.get('observed_size_bytes')==429909 and ingest.get('observed_sha256')=='ae8b32b1273a3152528f94ed544d93ca7bfcf6013f2d92d6b631af3eab61e006' and ingest.get('file_count')==120 and ingest.get('outer_manifest',{}).get('checked')==119 and ingest.get('internal_manifest',{}).get('checked')==90):errors.append('Batch068h4 artifact identity invalid')
    diff=load('historical_lock_v2_to_v3_diff.json');lock=load('historical_complete_lock_v3.json');tags=load('exact_runtime_wheel_tag_inventory.json')
    if diff.get('prereleases_selected',0) and not all(r.get('version') for r in diff.get('prerelease_records',[])):errors.append('prerelease selection lacks justification')
    if lock.get('status')!='PASS' or lock.get('unresolved_metadata_nodes') or lock.get('unresolved_dependency_nodes') or lock.get('constraint_conflicts') or lock.get('post_cutoff_selected_artifact_count'):errors.append('historical lock-v3 incomplete')
    final=load('batch068h5_final_decision.json');dispatch=load('runtime_dispatch_result_batch068h5.json')
    if tags.get('status')!='PASS' and dispatch.get('blocker') not in {'exact_runtime_tag_capsule_unavailable','exact_runtime_tag_capsule_failed','system_toolchain_inventory_unavailable','system_toolchain_inventory_failed'}:errors.append('exact runtime sys_tags absent without matching terminal block')
    cells=rows('build_cell_results_batch068h5.jsonl')
    for cell in cells:
        command=' '.join(cell.get('command',[]))
        if command.count('.tar.gz')+command.count('.zip')>1:errors.append('multiple sdists in one build cell')
        if not cell.get('stdout_sha256') or not cell.get('stderr_sha256'):errors.append('build log custody missing')
        if cell.get('network_policy')!='none':errors.append('build network enabled')
    board=load('amds_active_board_nbclient_batch068h5.json');constraints=rows('amds_constraint_registry_batch068h5.jsonl');probes=rows('amds_probe_candidate_registry_batch068h5.jsonl');observations=rows('amds_probe_execution_trace_batch068h5.jsonl');updates=rows('amds_board_update_trace_batch068h5.jsonl')
    if board.get('cells') and any(not c.get('evidence_hashes') or not c.get('state_hash') for c in board['cells']):errors.append('AMDS cells not evidence-derived')
    if any(c.get('constraint_type') not in {'requires','excludes','implies','mutually_exclusive','exactly_one','at_least_one','at_most_one','provider_dependency','environment_dependency','source_ownership','provenance_boundary','interlock_boundary','authorization_boundary','rollback_boundary'} for c in constraints):errors.append('AMDS constraint type invalid')
    if any(p.get('expected_information_gain_nats') is None for p in probes):errors.append('AMDS information gain missing')
    if any(p.get('prior_classification')!='structural_uniform_uncalibrated_prior' for p in probes):errors.append('AMDS uncalibrated prior mislabeled')
    if len(updates)!=len(observations):errors.append('AMDS board not updated after each observation')
    if validate_amds_implementation().get('status')!='PASS' or set(probe_contracts())!=set(PROBE_TYPES):errors.append('AMDS implementation incomplete')
    capabilities=runtime_capabilities()
    required_bindings={'build_amds_board','validate_amds_board','propagate_amds_constraints','enumerate_amds_probes','rank_amds_probes','authorize_amds_probe','execute_amds_probe','ingest_amds_observation','update_amds_board','close_amds_branch','evaluate_amds_stop','run_amds_active_loop'}
    if not required_bindings.issubset(capabilities['bindings']) or capabilities['unbound_reusable_mechanisms']:errors.append('AMDS runtime bindings incomplete')
    collection=load('collection_duplicate_equivalence_batch068h5.json');prerepair=load('prerepair_reproduction_decision_batch068h5.json');patch=load('patch_authorization_decision_batch068h5.json');replay=load('duplicate_clean_replay_decision_batch068h5.json');count=load('fifth_repair_count_gate_batch068h5.json')
    if collection.get('status')=='PASS' and not(collection.get('run1')=='PASS' and collection.get('run2')=='PASS' and collection.get('node_count',0)>0 and collection.get('node_set_equivalence') and collection.get('source_mutations')==collection.get('test_mutations')==0):errors.append('duplicate collection invalid')
    if prerepair.get('status')=='PASS' and collection.get('status')!='PASS':errors.append('prerepair bypassed collection')
    if patch.get('status')=='PASS' and prerepair.get('status')!='PASS':errors.append('patch authorization bypassed prerepair')
    if count.get('increment') and replay.get('status')!='PASS':errors.append('count gate bypassed duplicate replay')
    if final.get('issue_derived_repair_count') not in {4,5} or final.get('native_external_repair_count')!=4:errors.append('repair count invalid')
    if final.get('issue_derived_repair_count')==5 and count.get('status')!='PASS':errors.append('fifth repair lacks count gate')
    if final.get('full_scoring')!='NOT_RUN/disallowed' or final.get('memory_lift')!='not_demonstrated' or final.get('self_maintaining_software')!='false/not_demonstrated' or final.get('live_connectors')!='inactive':errors.append('claim boundary violation')
    if load('amds_prospective_effectiveness_boundary.json').get('AMDS_PROSPECTIVE_EFFECTIVENESS')!='NOT_ESTABLISHED':errors.append('AMDS prospective effectiveness overclaim')
    if load('v2_19_promotion_decision_batch068h5.json').get('status')=='PASS' and collection.get('status')!='PASS':errors.append('v2.19 promoted without duplicate collection')
    if errors:print('\n'.join(errors));return 1
    print('Batch068h5 AMDS/build-provider/fifth-repair audit PASS');return 0

if __name__=='__main__':raise SystemExit(main())
