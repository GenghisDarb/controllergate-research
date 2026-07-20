"""Freeze Batch102 v4 contracts without assigning candidate outcomes."""
from __future__ import annotations
import hashlib,json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]; CFG=ROOT/"configs"
def h(value): return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(",",":")).encode()).hexdigest()
def rows(path): return [json.loads(x) for x in path.read_text(encoding="utf-8").splitlines() if x.strip()]
def write(path,data): path.write_text("".join(json.dumps(x,sort_keys=True,separators=(",",":"))+"\n" for x in data),encoding="utf-8",newline="\n")

ADDITIONS={
 "batch100-py-bugger-65-accounting":[
  ("cli-normal-deterministic","diagnostic",["py-bugger","--target-file","${TARGET_FILE}","-n","10"]),
  ("cli-low-capacity","incident",["py-bugger","--target-file","${LOW_CAPACITY_TARGET}","-n","10"]),
  ("cli-zero-success","negative",["py-bugger","--target-file","${ZERO_SUCCESS_TARGET}","-n","10"]),
  ("attempt-filter-intervention","intervention",["python","${EXTERNAL_ACCOUNTING_HARNESS}","--mode","remove-failed"]),
  ("failed-attempt-injection","intervention",["python","${EXTERNAL_ACCOUNTING_HARNESS}","--mode","introduce-failed"]),
  ("successful-only-projection","control",["python","${EXTERNAL_ACCOUNTING_HARNESS}","--mode","successful-only"]),
  ("ledger-only-observation","negative",["python","${EXTERNAL_ACCOUNTING_HARNESS}","--mode","ledger-only"]),
 ],
 "batch100-cloudpickle-507-distutils":[
  ("python311-setuptools-absent","factorial",["python","-m","pytest","tests/cloudpickle_test.py","-q"]),
  ("python311-setuptools-present","factorial",["python","-m","pytest","tests/cloudpickle_test.py","-q"]),
  ("python312-setuptools-absent","factorial",["python","-m","pytest","tests/cloudpickle_test.py","-q"]),
  ("python312-setuptools-present","factorial",["python","-m","pytest","tests/cloudpickle_test.py","-q"]),
 ],
 "batch100-freezegun-547-three-nodes":[
  ("python312-plain-api","control",["python","${SEMANTIC_HARNESS}","--route","plain-api"]),
  ("python313b1-plain-api","factorial",["python","${SEMANTIC_HARNESS}","--route","plain-api"]),
  ("python312-unittest-decorator","control",["python","${SEMANTIC_HARNESS}","--route","unittest"]),
  ("python313b1-unittest-decorator","factorial",["python","${SEMANTIC_HARNESS}","--route","unittest"]),
  ("python312-type-equality","control",["python","${SEMANTIC_HARNESS}","--route","type-equality"]),
  ("python313b1-type-equality","factorial",["python","${SEMANTIC_HARNESS}","--route","type-equality"]),
 ],
 "batch100-audioread-144-aifc":[
  ("python312-rawread","factorial",["python","${AUDIOREAD_HARNESS}","--route","rawread"]),
  ("python312-unrelated-backend","factorial",["python","${AUDIOREAD_HARNESS}","--route","unrelated"]),
  ("python313b2-rawread","factorial",["python","${AUDIOREAD_HARNESS}","--route","rawread"]),
  ("python313b2-unrelated-backend","factorial",["python","${AUDIOREAD_HARNESS}","--route","unrelated"]),
  ("python313b2-compatibility-provider","exclusion",["python","${AUDIOREAD_HARNESS}","--route","rawread","--compatibility-provider"]),
 ],
 "batch100-pytest-13480-warning-mode":[
  ("threadexception-wdefault","factorial",["python","-m","pytest","testing/test_threadexception.py","-Wdefault","-q"]),
  ("threadexception-default","factorial",["python","-m","pytest","testing/test_threadexception.py","-q"]),
  ("unraisable-wdefault","factorial",["python","-m","pytest","testing/test_unraisableexception.py","-Wdefault","-q"]),
  ("unraisable-default","factorial",["python","-m","pytest","testing/test_unraisableexception.py","-q"]),
  ("warning-filter-wdefault","factorial",["python","-m","pytest","testing/test_warnings.py","-Wdefault","-q"]),
  ("warning-filter-default","factorial",["python","-m","pytest","testing/test_warnings.py","-q"]),
 ],
 "batch100-darker-112-git-dir":[
  ("direct-git-unset","exclusion",["git","diff","--name-only","HEAD","--","src"]),
  ("direct-git-invalid","negative",["git","diff","--name-only","HEAD","--","src"]),
 ],
 "batch100-cloudpickle-507-typevar":[
  ("python312b3-typevar","incident",["python","${TYPEVAR_HARNESS}"]),
  ("python312-final-typevar","exclusion",["python","${TYPEVAR_HARNESS}"]),
 ],
 "batch100-openbb-7585-topology":[
  ("modular-loopback-service","incident",["python","${OPENBB_HARNESS}","--mode","modular","--service","loopback"]),
  ("flattened-loopback-service","control",["python","${OPENBB_HARNESS}","--mode","flattened","--service","loopback"]),
  ("service-unavailable","negative",["python","${OPENBB_HARNESS}","--mode","modular","--service","unavailable"]),
  ("corrupt-yaml","negative",["python","${OPENBB_HARNESS}","--mode","corrupt"]),
  ("post-cutoff-source","negative",["python","${OPENBB_HARNESS}","--mode","post-cutoff"]),
 ],
}

SOURCE_COMMITS={
 "batch100-darker-112-git-dir":"bc751841439a02f5fd7277bbddb28190d4dcedd3",
 "batch100-pytest-13480-warning-mode":"80dfa2db8e6157bf706c2f2656ba0fd7bc13195a",
 "batch100-openbb-7585-topology":"1c74893140292944e71ff5cdd9536edf12f05483",
}
SECONDARY_SOURCE_COMMITS={"batch100-openbb-7585-topology":"901d6209e5738b0cbb42d48553c51fdc5f98bd7e"}

def main():
 old_programs=rows(CFG/"batch101_candidate_counterfactual_programs_v3.jsonl"); old_cells=rows(CFG/"batch101_counterfactual_cell_registry_v3.jsonl"); old_outcomes=rows(CFG/"batch101_outcome_semantic_registry_v3.jsonl"); old_proj=rows(CFG/"batch101_semantic_projection_registry_v1.jsonl")
 programs=[]
 for old in old_programs:
  row=dict(old); row["contract_version"]="batch102-counterfactual-v4"; row["execution_epoch_required"]="BATCH102_FRESH_OPERATION"; row["fresh_broker_receipt_required"]=True; row["necessity_sufficiency_required_for_ownership"]=True; row["alternative_exclusion_required_for_ownership"]=True; row["required_source_commit"]=SOURCE_COMMITS.get(row["program_id"]); row["required_secondary_source_commit"]=SECONDARY_SOURCE_COMMITS.get(row["program_id"]); row["old_program_hash"]=old.get("program_hash") or h(old); row.pop("program_hash",None); row["program_hash"]=h(row); programs.append(row)
 cells=[]; seen=set()
 for old in old_cells:
  row=dict(old); row["contract_version"]="batch102-cell-v4"; row["execution_epoch_required"]="BATCH102_FRESH_OPERATION"; row["fresh_broker_receipt_required"]=True; row["source_capsule_version"]="v2"; row["provider_capsule_version"]="v4"; row["required_source_commit"]=SOURCE_COMMITS.get(row["program_id"]); row["required_secondary_source_commit"]=SECONDARY_SOURCE_COMMITS.get(row["program_id"]); row["old_cell_hash"]=old.get("cell_hash") or h(old); row.pop("cell_hash",None); row["cell_hash"]=h(row); cells.append(row); seen.add(row["cell_id"])
 by_program={r["program_id"]:r for r in cells}
 for pid,specs in ADDITIONS.items():
  template=by_program[pid]
  for name,role,argv in specs:
   cid=f"cell:batch102-{pid.removeprefix('batch100-')}:{name}"
   if cid in seen: continue
   row={"cell_id":cid,"cell_name":name,"cell_role":role,"program_id":pid,"candidate_id":template["candidate_id"],"contract_version":"batch102-cell-v4","exact_argv":argv,"exact_cwd":"${RUNTIME_ROOT}/batch102/"+template["candidate_id"]+"/"+name,"exact_environment":{},"command_hash":h(argv),"environment_hash":h({}),"fixture_hash":h({"name":name,"program":pid}),"fresh_workspace_count":2,"replay_count":2,"execution_epoch_required":"BATCH102_FRESH_OPERATION","fresh_broker_receipt_required":True,"source_capsule_version":"v2","provider_capsule_version":"v4","required_source_commit":SOURCE_COMMITS.get(pid),"required_secondary_source_commit":SECONDARY_SOURCE_COMMITS.get(pid),"network_policy":"loopback_only" if "openbb" in pid else "none","truth_access":0,"private_tld_access":0,"patch_operations":0,"authority_allowed":"truth-blind fresh candidate observation","authority_forbidden":["causal ownership before intervention/exclusion","patch","repair count","release"]}; row["cell_hash"]=h(row); cells.append(row); seen.add(cid)
 outcomes=[]
 for old in old_outcomes:
  row=dict(old); row["registry_version"]="batch102-outcome-semantic-v4"; row["fresh_execution_required"]=True; row["necessity_sufficiency_required_for_ownership"]=True; row["registry_hash"]=h({k:v for k,v in row.items() if k!="registry_hash"}); outcomes.append(row)
 projections=[]
 for old in old_proj:
  row=dict(old); row["projection_id"]="controllergate-semantic-projection-v2"; row["execution_epoch_required"]="BATCH102_FRESH_OPERATION"; row["volatile_fields"]=["duration","timestamp","pid","absolute_workspace_path","installation_path","address"]; row["projection_hash"]=h(row); projections.append(row)
 supers=[]
 pairs=[("batch101_candidate_counterfactual_programs_v3.jsonl","batch102_candidate_counterfactual_programs_v4.jsonl",old_programs,programs),("batch101_counterfactual_cell_registry_v3.jsonl","batch102_counterfactual_cell_registry_v4.jsonl",old_cells,cells),("batch101_outcome_semantic_registry_v3.jsonl","batch102_outcome_semantic_registry_v4.jsonl",old_outcomes,outcomes),("batch101_semantic_projection_registry_v1.jsonl","batch102_semantic_projection_registry_v2.jsonl",old_proj,projections)]
 for oldn,newn,old,new in pairs:
  row={"old_contract":oldn,"old_hash":h(old),"new_contract":newn,"new_hash":h(new),"reason":"Require current-workflow brokered receipts, exact source/provider custody, and intervention/exclusion evidence.","Batch101_artifact_evidence":"Batch101 official ingest: zero fresh Batch101 candidate operations","scientific_meaning_changed":False,"execution_mechanics_changed":True,"approval_boundary":"non-authorizing contract freeze","authority_forbidden":["outcome assignment","patch","repair count","release"]}; row["supersession_receipt"]=h(row); supers.append(row)
 exclusions=[]
 for program in programs:
  row={"program_id":program["program_id"],"candidate_id":program["candidate_id"],"registry_version":"batch102-alternative-exclusion-v1","alternatives":["source","provider","environment_platform","runner","harness_fixture","service_transport","test_expectation","mixed_interaction"],"predeclared":True,"execution_required":True,"authority_allowed":"alternative-exclusion planning","authority_forbidden":["exclusion without candidate-specific execution","ownership","patch"]}; row["program_hash"]=h(row); exclusions.append(row)
 for name,data in [("batch102_candidate_counterfactual_programs_v4.jsonl",programs),("batch102_counterfactual_cell_registry_v4.jsonl",cells),("batch102_outcome_semantic_registry_v4.jsonl",outcomes),("batch102_semantic_projection_registry_v2.jsonl",projections),("batch102_contract_supersession_registry_v1.jsonl",supers),("batch102_alternative_exclusion_programs_v1.jsonl",exclusions)]: write(CFG/name,data)
 print(json.dumps({"status":"PASS","programs":len(programs),"registered_cells":len(cells),"outcomes":len(outcomes),"projections":len(projections),"supersessions":len(supers),"exclusion_programs":len(exclusions)},sort_keys=True))
 return 0
if __name__=="__main__": raise SystemExit(main())
