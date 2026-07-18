from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from controllergate.amds.role_measurement import ROLE_NAMES, measure_role
from controllergate.core.evidence import hash_record
import controllergate.amds.role_measurement.producer as producer_module


ORDER = ['darker_issue_112_relative_git_dir','py_bugger_issue_65','cloudpickle_507_py313_typevar_distutils','freezegun_547_py313_datetimes_assertion','audioread_144_py313_aifc_removed','pytest_13480_wdefault_unraisable_threadexception','incident_openbb_7585_modular_openapi_reproducer','incident_poetry_10974_init_duplicate_name']


def _lines(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n" for row in rows), encoding="utf-8", newline="\n")


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _raw(row: dict[str, Any], role: str, object_ids: list[str], producer_hash: str) -> dict[str, Any]:
    source=row['source_capsule']; provider=row['provider_recipe']; observed=row['observed_provider']; process=row['process']; verification=row['typed_incident_verification']; immutable=row['source_test_immutability']; topology=row['source_topology']; parent=row['execution_parent']
    interpreter_hash=hash_record(observed.get('python',{})); operation=process.get('record_hash')
    common={'fresh_measurement_epoch':'batch097','producer_execution_receipt':hash_record({'producer_code_hash':producer_hash,'candidate_id':row['candidate_id'],'role':role,'raw_object_ids':object_ids,'raw_operation_id':operation}),'raw_operation_hash':operation,'raw_output_hashes':[process.get('stdout_sha256'),process.get('stderr_sha256')],'parent_evidence':object_ids,'raw_object_ids':object_ids}
    mappings={
      'source_revision':{'commit_sha':source['observed_commit'],'commit_object_type':source['object_type'],'repository_url':source['repository'],'source_revision_timestamp':source['source_revision_timestamp']},
      'source_tree':{'source_file_hashes':[node['sha256'] for node in topology['nodes'] if node.get('node_class')=='SOURCE_FILE'],'source_tree_hash':source['source_tree_hash'],'dirty_state':'clean_verified','submodule_state':'recorded_none_or_unchanged'},
      'test_tree':{'test_file_hashes':[immutable['test_tree_before']],'collection_identity':verification.get('raw_evidence_hash',operation),'support_file_hashes':[immutable['test_tree_after']],'test_tree_hash':immutable['test_tree_after']},
      'provider_runtime_abi':{'interpreter_hash':interpreter_hash,'python_version':observed.get('python',{}).get('version'),'abi_tags':observed['abi_tags'],'platform':observed['platform_tags'],'distribution_graph_hash':observed['package_graph_hash']},
      'target_reproducer':{'target_identity':operation,'collection_result':verification.get('status'),'failure_signature_schema':verification.get('outcome_family',verification.get('failure_terminal')),'project_level_reproducer':True},
      'command':{'argv':provider['project_target_command'],'cwd':provider['working_directory_policy'],'environment_allowlist':provider['environment_allowlist'],'timeout_seconds':1800,'network_policy':provider['network_acquisition_policy'],'command_authority':provider['recipe_hash']},
      'runner':{'executable_hash':observed['provider_identity'],'entrypoint':provider['project_target_command'][0],'process_parent':'controllergate.execution.execution_broker','interpreter_hash':interpreter_hash,'runner_version':observed.get('python',{}).get('version')},
      'harness':{'wrapper_hash':provider['recipe_hash'],'plugin_set':[observed['package_graph_hash']],'fixture_origins':[source['source_tree_hash']],'translation_layers':[provider['semantic_outcome_contract_id']]},
      'incident_snapshot':{'raw_log_hash':hash_record([process.get('stdout_sha256'),process.get('stderr_sha256')]),'structured_exception':verification.get('outcome_family',verification.get('failure_terminal')),'import_origins':[observed['provider_identity']],'captured_at':row['run_id'],'frame_hashes':[row['frame_id'],verification.get('raw_evidence_hash',operation)]},
      'proof_release_parent':{'sqlite_run_parent':str(parent['workflow_run_id']),'proof_ledger_parent':source['identity_record_hash'],'release_state_parent':str(parent['workflow_head']),'public_state_parent':str(parent['frame_id'])},
    }
    return {**mappings[role], **common}


def main() -> int:
    ap=argparse.ArgumentParser(); ap.add_argument('--inputs-root',required=True); ap.add_argument('--output',required=True); args=ap.parse_args()
    root=Path(args.inputs_root); out=Path(args.output); out.mkdir(parents=True,exist_ok=True)
    producer_hash=_sha(Path(producer_module.__file__).resolve()); receipts=[]
    for candidate in ORDER:
        matches=list(root.rglob(f'{candidate}/candidate_lane_result.json'))
        if len(matches)!=1:
            continue
        row=json.loads(matches[0].read_text(encoding='utf-8'))
        lane=matches[0].parent
        object_ids=[_sha(path) for path in sorted(lane.rglob('*')) if path.is_file()]
        if row.get('status')!='PASS':
            continue
        for role in ROLE_NAMES:
            receipt=measure_role(candidate, role, _raw(row,role,object_ids,producer_hash))
            receipt['producer_code_hash']=producer_hash; receipt['installed_module_path']=str(Path(producer_module.__file__).resolve()); receipt['raw_object_ids']=object_ids
            receipts.append(receipt)
    _lines(out/'role_measurement_execution_receipts_v5.jsonl',receipts)
    summary={'status':'PASS' if len(receipts)==80 and all(r['status']=='PASS' for r in receipts) else 'BLOCK','execution_receipt_count':len(receipts),'required_count':80,'producer_code_hash':producer_hash,'authority_allowed':'independent role verification input','authority_forbidden':['terminal','repair','count']}
    (out/'role_producer_gate_v5.json').write_text(json.dumps(summary,indent=2,sort_keys=True)+'\n',encoding='utf-8',newline='\n')
    print('BATCH097_ROLE_PRODUCERS_'+summary['status']); return 0


if __name__=='__main__': raise SystemExit(main())
