from __future__ import annotations
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]; OUT=ROOT/'outputs/post_v2_37_hardening_batch096_repository_genome_topology_compiled_amds_unification'
def load(n): return json.loads((OUT/n).read_text())
def main():
 checks={
  'bundle':load('historical_tld_source_bundle_verification.json')['status']=='PASS',
  'history':load('repository_history_coverage_audit.json')['status']=='PASS',
  'materialization':load('frozen_eight_materialization_audit.json')['materialized']==8,
  'tld':load('tld_source_coverage_audit.json')['notebooks_observed']==44,
  'roles':load('role_identity_claim_graph_v4.json')['producer_receipts']==80,
  'amds':load('amds_historical_quality_gate_v5.json')['status']=='AMDS_HISTORICAL_BLINDED_CAUSAL_MECHANISM_PASS_V5',
  'release_boundary':load('batch096_internal_release_decision.json')['status']=='PRODUCT_BETA_RC_BLOCKED_EXACT',
 }
 result={'status':'PASS' if all(checks.values()) else 'BLOCK','checks':checks,'patch_operations':0,'historical_increment':0,'protocol':'v2.19'}
 (OUT/'batch096_final_audit.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
 print('BATCH096_AUDIT_'+result['status']); return 0 if all(checks.values()) else 1
if __name__=='__main__': raise SystemExit(main())
