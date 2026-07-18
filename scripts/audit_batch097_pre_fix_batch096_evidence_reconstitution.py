from __future__ import annotations
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'outputs/post_v2_37_hardening_batch097_evidence_reconstitution_real_repository_genome_topology_amds'

DEFECTS=[
('checkout_import','scripts/run_batch096_materialization_and_topology.py','sys.path.insert','checkout imported instead of installed product'),
('fabricated_materialization','scripts/run_batch096_materialization_and_topology.py','mats.append','eight PASS rows without candidate execution'),
('unmeasured_immutability','scripts/run_batch096_materialization_and_topology.py','integrity.append','immutability declared without tree measurements'),
('configured_incident','scripts/run_batch096_materialization_and_topology.py','incident=','incident inferred from IDs and contracts'),
('fabricated_cleanup','scripts/run_batch096_materialization_and_topology.py','cleanup.append','cleanup declared without workspaces'),
('synthetic_roles','scripts/run_batch096_materialization_and_topology.py','roles=','role identities are label hashes'),
('synthetic_contact','scripts/run_batch096_materialization_and_topology.py','contacts=','source contact is a constant-label hash'),
('placeholder_tld','scripts/run_batch096_materialization_and_topology.py','ThreeProjectionResult','TLD projections are placeholders'),
('tld_fallback','scripts/run_batch096_materialization_and_topology.py','preserved=','source parsing falls back to old output'),
('fabricated_promotion','scripts/run_batch096_materialization_and_topology.py','buf.promote','promotion uses fabricated audit hash'),
('prewritten_modalities','scripts/run_batch096_materialization_and_topology.py','obs=','modality support is prewritten'),
('hardcoded_terminals','scripts/run_batch096_amds_and_release.py','classes=','terminal classes precede observations'),
('synthetic_role_receipts','scripts/run_batch096_amds_and_release.py','raw=h','receipts do not resolve to raw evidence'),
('nonexecuting_probes','scripts/run_batch096_amds_and_release.py','probes.append','probes have no executable operation'),
('declared_dpp14','scripts/run_batch096_amds_and_release.py','for stage in range','DPP stages are declared PASS'),
('declared_truth_maintenance','scripts/run_batch096_amds_and_release.py','constraints.append','contradictions/backtracks are declarations'),
('hardcoded_metrics','scripts/run_batch096_amds_and_release.py','baselines=','accuracy and costs are hardcoded'),
('proof_loop','scripts/run_batch096_amds_and_release.py','for req in requirements','proofs are manufactured by requirement loop'),
('declared_mutations','scripts/run_batch096_amds_and_release.py','mutations=','critic mutations are not executed'),
('lexical_genome','scripts/run_batch096_repository_genome.py','discover_identifiers','complete Git history is not traversed'),
('default_migrated','scripts/run_batch096_repository_genome.py','dispositions =','repository presence defaults to MIGRATED'),
('hardcoded_capabilities','scripts/run_batch096_repository_genome.py','capabilities =','capability set and decommission result are declarations'),
('helper_overclaim','controllergate/governance/repository_genome.py','discover_identifiers','lexical index is called repository genome'),
('caller_supplied_board','controllergate/amds/topology_compiler.py','compile_topology_frame','decisive content is externally supplied'),
('compiler_unreachable','controllergate/amds/topology_compiler.py','compile_topology_frame','canonical engine does not invoke compiler'),
('shallow_local_graph','controllergate/topology/canonical_v2.py','build_local_graph','graph has caller supplied contacts only'),
('adjacent_coupling','controllergate/topology/canonical_v2.py','couple_graphs','adjacent candidates are coupled by simple equality'),
('observer_contract_thin','controllergate/topology/canonical_v2.py','ObserverStateContractV1','required authority and transition fields absent'),
('buffer_not_durable','controllergate/topology/canonical_v2.py','ProvisionalEvidenceBufferV1','no durable lineage/checkpoint/resume/nonce state'),
('modality_name_check','controllergate/topology/canonical_v2.py','verify_modalities','string inequality substitutes for execution'),
('single_job_workflow','.github/workflows/post_v2_37_hardening_batch096_repository_genome_topology_compiled_amds_unification.yml','evidence-only','one checkout job regenerates all evidence'),
('count_only_audit','scripts/audit_batch096_repository_genome_topology_compiled_amds.py','checks=','audit trusts declarations and counts'),
('no_real_decommission','git diff 7c56ee..c870cb','no deletions','claimed decommission had no removal'),
('public_boundary_stale','README.md and docs/current_status.md','Batch096 evidence-only closure','public text repeats invalid closure'),
]

def main():
 OUT.mkdir(parents=True,exist_ok=True)
 rows=[]
 for i,(code,path,symbol,risk) in enumerate(DEFECTS,1):
  rows.append({'finding_id':f'B097-RED-{i:02d}','code':code,'commit':'c870cb448cda496407b0840468e63c5c6d2c7c82','path':path,'symbol':symbol,'line_range':'resolved_from_frozen_commit','artifact_evidence':'Batch096 artifact 8399956632 plus independent depth review','risk':risk,'required_correction':f'remove {code} from current authority and replace with executed evidence','red_to_green_test':f'test_batch097_{code}'})
 result={'status':'BATCH097_PRE_FIX_BATCH096_SCIENTIFIC_CLOSURE_FAIL_EXPECTED','finding_count':len(rows),'findings':rows,'authority_allowed':'expected-red correction baseline','authority_forbidden':['scientific closure','repair','count','release']}
 (OUT/'batch097_pre_fix_batch096_evidence_reconstitution_expected_failure.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
 print(result['status']); return 0
if __name__=='__main__': raise SystemExit(main())
