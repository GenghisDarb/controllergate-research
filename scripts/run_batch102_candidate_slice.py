"""Run one real Batch102 candidate/provider slice and attest any fresh operations."""
from __future__ import annotations
import argparse,hashlib,json,os,platform,re,shutil,subprocess,sys
from pathlib import Path
from typing import Any

ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0,str(ROOT))
from controllergate.evidence.fresh_execution_attestation_v1 import Batch102FreshExecutionReceiptV1,canonical_hash,verify_fresh_execution_receipt
from controllergate.evidence.batch103_fresh_execution_attestation_v1 import Batch103FreshExecutionReceiptV1,verify_batch103_fresh_execution_receipt
from controllergate.evidence.provider_capsule_v4 import build_provider_capsule_v4,observed_provider_identity,verify_provider_capsule_v4
from controllergate.evidence.source_capsule_v2 import build_source_capsule_v2,verify_source_capsule_v2

def readj(path:Path): return [json.loads(x) for x in path.read_text(encoding="utf-8").splitlines() if x.strip()]
def writej(path:Path,value:Any): path.parent.mkdir(parents=True,exist_ok=True); path.write_text(json.dumps(value,indent=2,sort_keys=True)+"\n",encoding="utf-8",newline="\n")
def writejl(path:Path,values:list[dict]): path.parent.mkdir(parents=True,exist_ok=True); path.write_text("".join(json.dumps(x,sort_keys=True,separators=(",",":"))+"\n" for x in values),encoding="utf-8",newline="\n")
def sha(value:bytes): return hashlib.sha256(value).hexdigest()
def version_identity(value:str, os_name:str)->dict[str,Any]:
 m=re.fullmatch(r"(\d+)\.(\d+)\.(\d+)(?:(a|b|rc)(\d+))?",value)
 if not m: raise ValueError("requested Python must be exact")
 levels={"a":"alpha","b":"beta","rc":"candidate"}; pre=None if m.group(4) is None else {"level":levels[m.group(4)],"serial":int(m.group(5))}
 observed=observed_provider_identity()
 return {"implementation":"CPython","version_tuple":[int(m.group(1)),int(m.group(2)),int(m.group(3))],"prerelease":pre,"os":os_name,"architecture":observed["architecture"],"ABI":observed["ABI"],"SOABI":observed["SOABI"]}

def identity_for_executable(executable:str)->dict[str,Any]:
 if Path(executable).resolve()==Path(sys.executable).resolve(): return observed_provider_identity()
 code="""import json,platform,sys,sysconfig\ni=sys.version_info\np=None if i.releaselevel=='final' else {'level':i.releaselevel,'serial':i.serial}\nprint(json.dumps({'implementation':platform.python_implementation(),'version':platform.python_version(),'version_tuple':[i.major,i.minor,i.micro],'prerelease':p,'os':platform.system().lower(),'architecture':platform.machine().lower(),'ABI':str(sysconfig.get_config_var('SOABI') or 'unknown'),'SOABI':str(sysconfig.get_config_var('SOABI') or 'unknown')}))"""
 run=subprocess.run([executable,"-c",code],capture_output=True,text=True,encoding="utf-8",errors="replace",check=False)
 if run.returncode: raise RuntimeError(f"provider identity failed: {run.stderr}")
 return json.loads(run.stdout)

def main()->int:
 p=argparse.ArgumentParser(); p.add_argument("--candidate-id",required=True); p.add_argument("--slice-id",required=True); p.add_argument("--requested-python",required=True); p.add_argument("--runtime-root",type=Path,required=True); p.add_argument("--output-dir",type=Path,required=True); p.add_argument("--source-commit"); p.add_argument("--requested-os"); p.add_argument("--provider-python",default=sys.executable); p.add_argument("--campaign-label",choices=["batch102","batch103"],default="batch102"); a=p.parse_args()
 a.runtime_root.mkdir(parents=True,exist_ok=True); a.output_dir.mkdir(parents=True,exist_ok=True)
 contracts={r["candidate_id"]:r for r in readj(ROOT/"configs/candidate_execution_contracts_v2.jsonl")}; contract=contracts[a.candidate_id]
 programs=[r for r in readj(ROOT/"configs/batch102_candidate_counterfactual_programs_v4.jsonl") if r["candidate_id"]==a.candidate_id]
 required=next((r.get("required_source_commit") for r in programs if r.get("required_source_commit")),None)
 source_commit=a.source_commit or required or contract["source_commit"]
 label=a.campaign_label; is_batch103=label=="batch103"; epoch="BATCH103_FRESH_OPERATION" if is_batch103 else "BATCH102_FRESH_OPERATION"; prefix="batch103" if is_batch103 else "batch102"
 old_out=a.output_dir/"raw_candidate_execution"; cmd=[sys.executable,str(ROOT/"scripts/run_batch100_candidate_program.py"),"--candidate-id",a.candidate_id,"--runtime-root",str(a.runtime_root),"--output-dir",str(old_out),"--provider-python",a.provider_python,"--source-commit",source_commit,"--batch102-exact-fixtures","--authorization-id",f"{label}:fresh-public-evidence-only","--execution-label",label]
 run=subprocess.run(cmd,cwd=ROOT,capture_output=True,text=True,encoding="utf-8",errors="replace",check=False)
 writej(a.output_dir/"slice_runner_invocation.json",{"argv_hash":canonical_hash(cmd),"return_code":run.returncode,"stdout_sha256":sha(run.stdout.encode()),"stderr_sha256":sha(run.stderr.encode()),"execution_depth":"current workflow candidate runner","authority_allowed":"candidate evidence acquisition","authority_forbidden":["patch","repair count","release"]})
 broker=readj(old_out/"broker_operations_v1.jsonl") if (old_out/"broker_operations_v1.jsonl").is_file() else []
 raw_receipts=readj(old_out/"cell_execution_receipts_v1.jsonl") if (old_out/"cell_execution_receipts_v1.jsonl").is_file() else []
 blockers=readj(old_out/"candidate_blockers_v1.jsonl") if (old_out/"candidate_blockers_v1.jsonl").is_file() else []
 source_root=a.runtime_root/"source"/a.candidate_id; source_capsule=None
 acquisition=next((r for r in broker if r.get("operation_type")=="source_acquisition"),None)
 if source_root.is_dir() and acquisition:
  try: source_capsule=build_source_capsule_v2(candidate_id=a.candidate_id,repository=contract["repository"],exact_source_commit=source_commit,repo=source_root,test_prefixes=["tests","test","testing"],issue_cutoff="decision-time-source-contract",acquisition_broker_receipt={"operation_id":acquisition["operation_id"],"record_hash":acquisition["record_hash"]},network_budget={"mode":"bounded_read_only","operations":sum(r.get("operation_type")=="source_acquisition" for r in broker)})
  except Exception as exc: blockers.append({"candidate_id":a.candidate_id,"blocker":f"{prefix.upper()}_SOURCE_CAPSULE_V2_BLOCKED","detail":str(exc)})
 requested=version_identity(a.requested_python,a.requested_os or platform.system().lower()); observed=identity_for_executable(a.provider_python); materialization=next((r for r in broker if r.get("operation_type") in {"provider_build","provider_acquisition"}),None)
 provider_capsule=build_provider_capsule_v4(capsule_id=f"provider:{prefix}:{a.slice_id}",candidate_id=a.candidate_id,requested=requested,observed=observed,materialization_receipt={"operation_id":materialization["operation_id"] if materialization else f"unavailable:{a.slice_id}"},runner_image=os.environ.get("ImageOS",platform.system().lower()),dependency_graph_hash=canonical_hash([r.get("stage_id") for r in broker if r.get("operation_type") in {"provider_build","provider_acquisition"}]),wheel_hashes=[],available=materialization is not None)
 provider_blockers=verify_provider_capsule_v4(provider_capsule); source_blockers=verify_source_capsule_v2(source_capsule) if source_capsule else ["source_capsule_not_materialized"]
 broker_by={r.get("operation_id"):r for r in broker}; cells={r["cell_id"]:r for r in readj(ROOT/"configs/batch102_counterfactual_cell_registry_v4.jsonl")}; pred_hash=sha((ROOT/"configs/batch102_outcome_semantic_registry_v4.jsonl").read_bytes()); fresh=[]
 for rr in raw_receipts:
  op=broker_by.get(rr.get("operation_id")); cell=cells.get(rr["cell_id"])
  if not op or not cell or not source_capsule or provider_blockers or source_blockers or int(rr.get("source_tracked_mutation_count", 1)) != 0: continue
  receipt_type=Batch103FreshExecutionReceiptV1 if is_batch103 else Batch102FreshExecutionReceiptV1
  semantic=rr.get("semantic_observation",{}); out=receipt_type(execution_receipt_id=f"{prefix}:{a.slice_id}:{rr['cell_id']}:{rr['replay_index']}",execution_epoch=epoch,workflow_run_id=os.environ.get("GITHUB_RUN_ID",f"{prefix}-local"),workflow_job_id=os.environ.get("GITHUB_JOB",a.slice_id),workflow_job_attempt=os.environ.get("GITHUB_RUN_ATTEMPT","1"),workflow_head=os.environ.get("GITHUB_SHA",subprocess.check_output(["git","rev-parse","HEAD"],cwd=ROOT,text=True).strip()),candidate_id=a.candidate_id,program_id=rr["program_id"],cell_id=rr["cell_id"],replay_index=int(rr["replay_index"]),broker_operation_id=op["operation_id"],broker_record_hash=op["record_hash"],source_capsule_hash=source_capsule["source_capsule_hash"],source_commit=source_commit,source_tree_hash_before=rr["source_pre_hash"],source_tree_hash_after=rr["source_post_hash"],provider_capsule_hash=provider_capsule["provider_capsule_hash"],provider_observed_identity=observed,provider_exactness_status=provider_capsule["provider_exactness_status"],platform=platform.system().lower(),architecture=platform.machine().lower(),ABI=observed["ABI"],SOABI=observed["SOABI"],exact_argv_hash=cell["command_hash"],cwd_hash=canonical_hash(cell["exact_cwd"]),environment_hash=cell["environment_hash"],fixture_hash=cell["fixture_hash"],raw_stdout_object={"sha256":semantic.get("stdout_sha256",op.get("stdout_hash"))},raw_stderr_object={"sha256":semantic.get("stderr_sha256",op.get("stderr_hash"))},raw_return_code=int(semantic.get("return_code",op.get("return_code",-1))),semantic_projection_id="controllergate-semantic-projection-v2",semantic_fingerprint=canonical_hash(semantic),predicate_registry_hash=pred_hash,predicate_result=bool(rr.get("predicate_satisfied")),network_policy=str(op.get("network_policy","none")),truth_access_count=0,private_tld_access_count=0,patch_operation_count=0,cleanup_status=rr.get("cleanup_result","BLOCK"),producer="canonical_external_operation_broker",independent_verifier=f"{prefix}_fresh_receipt_independent_verifier",producer_receipt={"operation_id":op["operation_id"],"record_hash":op["record_hash"]},verifier_receipt={"source_capsule":"PASS","provider_capsule":"PASS","semantic_receipt":rr.get("semantic_verifier_receipt")}).record(); fresh.append(out)
 current_run=os.environ.get("GITHUB_RUN_ID",f"{prefix}-local"); current_head=os.environ.get("GITHUB_SHA",subprocess.check_output(["git","rev-parse","HEAD"],cwd=ROOT,text=True).strip()); verifier=verify_batch103_fresh_execution_receipt if is_batch103 else verify_fresh_execution_receipt; verification=[{"id":r["execution_receipt_id"],"blockers":verifier(r,current_workflow_run_id=current_run,current_workflow_head=current_head)} for r in fresh]
 registered=[r for r in cells.values() if r["candidate_id"]==a.candidate_id]; executed_ids={r["cell_id"] for r in fresh}; account=[]
 for cell in registered:
  if cell["cell_id"] in executed_ids: status="EXECUTED_VERIFIED" if all(r["predicate_result"] for r in fresh if r["cell_id"]==cell["cell_id"]) else "EXECUTED_PREDICATE_FALSE"
  elif provider_capsule["provider_exactness_status"]=="UNAVAILABLE_PROVIDER": status="BLOCKED_EXACT_PROVIDER_UNAVAILABLE"
  elif source_capsule is None: status="BLOCKED_SOURCE_UNAVAILABLE"
  else: status="BLOCKED_INCIDENT_PREFLIGHT"
  account.append({"cell_id":cell["cell_id"],"candidate_id":a.candidate_id,"slice_id":a.slice_id,"status":status,"fresh_receipt_ids":[r["execution_receipt_id"] for r in fresh if r["cell_id"]==cell["cell_id"]],"authority_allowed":"cell accounting","authority_forbidden":["static execution substitution","patch","repair count"]})
 writejl(a.output_dir/f"{prefix}_fresh_execution_receipts_v1.jsonl",fresh); writejl(a.output_dir/f"{prefix}_broker_operations_v1.jsonl",broker); writejl(a.output_dir/f"{prefix}_cell_accounting_v1.jsonl",account); writejl(a.output_dir/f"{prefix}_candidate_blockers_v1.jsonl",blockers); writej(a.output_dir/f"{prefix}_source_capsule_v2.json",source_capsule or {"status":"BLOCK","blockers":source_blockers}); writej(a.output_dir/f"{prefix}_provider_capsule_v4.json",provider_capsule); writej(a.output_dir/f"{prefix}_fresh_execution_verification.json",{"status":"PASS" if all(not r["blockers"] for r in verification) else "BLOCK","receipts":verification}); writej(a.output_dir/f"{prefix}_slice_summary.json",{"slice_id":a.slice_id,"candidate_id":a.candidate_id,"requested_python":a.requested_python,"source_commit":source_commit,"provider_exactness_status":provider_capsule["provider_exactness_status"],"execution_epoch":epoch,"fresh_replay_count":len(fresh),"fresh_executed_cell_count":len(executed_ids),"registered_cell_count":len(registered),"blocked_cell_count":sum(r["status"].startswith("BLOCKED") for r in account),"source_capsule_status":"PASS" if not source_blockers else "BLOCK","provider_capsule_status":"PASS" if not provider_blockers else "BLOCK","ordinary_patch_count":0,"truth_access":0,"private_tld_access":0,"authority_allowed":"truth-blind candidate execution evidence","authority_forbidden":["ownership before join","patch","repair count","release"]})
 shutil.rmtree(source_root,ignore_errors=True)
 writej(a.output_dir/f"{prefix}_cleanup_receipt.json",{"status":"PASS" if not source_root.exists() else "BLOCK","source_workspace_removed":not source_root.exists(),"runtime_root_ephemeral":True,"authority_allowed":"workspace cleanup evidence","authority_forbidden":["execution success substitution"]})
 print(json.dumps({"status":"PASS_WITH_SCIENTIFIC_BLOCKERS" if blockers or not fresh else "PASS","slice":a.slice_id,"fresh_receipts":len(fresh),"blockers":len(blockers)},sort_keys=True)); return 0
if __name__=="__main__": raise SystemExit(main())
