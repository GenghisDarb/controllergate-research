import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]; OUT=ROOT/'outputs/post_v2_37_hardening_batch096_repository_genome_topology_compiled_amds_unification'
def rows(n): return [json.loads(x) for x in (OUT/n).read_text().splitlines() if x]
def test_ten_role_boundary():
 assert len(rows('role_measurement_execution_receipts_v4.jsonl'))==80
 assert len(rows('role_measurement_verification_receipts_v4.jsonl'))==80
def test_only_controller_audit_writes_terminal():
 assert {x['writer'] for x in rows('controller_audit_terminals_v5.jsonl')}=={'ControllerAudit'}
def test_actual_baselines_not_copied():
 data=rows('amds_actual_baselines_v5.jsonl'); assert len(data)>=10 and all(x['executed'] for x in data)
def test_ordinary_run_never_patches_or_counts():
 state=json.loads((OUT/'batch096_consolidated_state.json').read_text()); assert state['historical_increment']==0 and state['status']=='PRODUCT_BETA_RC_BLOCKED_EXACT'
def test_semantic_mutations_rejected():
 value=json.loads((OUT/'resigned_actual_evidence_mutation_results_v3.json').read_text()); assert value['executed']==value['rejected']==31
