from __future__ import annotations
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'outputs/post_v2_37_hardening_batch097_evidence_reconstitution_real_repository_genome_topology_amds'
def load(name:str):return json.loads((OUT/name).read_text(encoding='utf-8'))
def main()->int:
 required=('batch096_scientific_claim_invalidation.json','repository_history_coverage_audit_v2.json','batch097_tld_source_bundle_custody.json','tld_source_parse_audit_v2.json','batch097_internal_release_decision.json','batch097_claim_boundary.json','batch097_consolidated_state.json','campaign_summary.md','SHA256SUMS.txt')
 missing=[x for x in required if not (OUT/x).is_file()]
 if missing:raise SystemExit('BATCH097_REQUIRED_OUTPUT_MISSING:'+','.join(missing))
 assert load('batch096_scientific_claim_invalidation.json')['status']=='PASS';assert load('batch097_tld_source_bundle_custody.json')['status']=='PASS';assert load('tld_source_parse_audit_v2.json')['notebook_count']==44
 state=load('batch097_consolidated_state.json');claims=load('batch097_claim_boundary.json');assert state['status']=='PRODUCT_BETA_RC_BLOCKED_EXACT';assert claims=={'AMDS_prospective_effectiveness':'NOT_ESTABLISHED','automatic_merge':'inactive','full_scoring':'NOT_RUN/disallowed','historical_increment':0,'issue_derived_repairs':6,'memory_status':'not demonstrated','native_external_repairs':4,'package_version':'0.2.0b2.dev0','production_readiness':False,'protocol':'v2.19','public_writes':'inactive','self_maintaining_software':'false/not demonstrated'}
 print('BATCH097_EVIDENCE_RECONSTITUTION_AUDIT_PASS');return 0
if __name__=='__main__':raise SystemExit(main())
