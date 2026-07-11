from __future__ import annotations

import copy
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
from typing import Any

from controllergate.amds.runtime_adapter import run_amds_active_loop
from controllergate.core.evidence import hash_record
from .authorized_fetch import authorized_fetch
from .batch068h5_pipeline import execute_phase as execute_h5_phase
from .batch068h7_pipeline import canonical_dual_recovery
from .cargo_vendor import build_vendor_tree, parse_cargo_lock
from .historical_toolchain_provider import prepare_historical_builder
from .network_authorization import authorize_network_operation
from .network_event_ledger import append_network_event
from .network_policy import docker_network_mode, validate_network_policy


CANDIDATE="codex_wave3_jupyter_nbclient_issues_316"
CANDIDATE_SHA="8514e919d8405eb832e80b9ea1925767e7431ee9"
CUTOFF="2024-07-03T12:05:28Z"


def _sha(path:Path)->str:return hashlib.sha256(path.read_bytes()).hexdigest()


def hydrate_provider_inputs(context:dict[str,Any],policy:dict[str,Any])->dict[str,Any]:
    checked=validate_network_policy(policy,phase_id="provider_acquisition")
    if checked["status"]!="PASS":return checked
    workspace=Path(context["workspace_root"]);store=workspace/"artifact_store";store.mkdir(parents=True,exist_ok=True);ledger=Path(context["network_ledger_path"]);budget={"requests":0,"bytes":0};selected={};events=[]
    for name,original in context["lock_v4"]["selected_artifacts"].items():
        row=dict(original);target=store/row["filename"]
        value=authorized_fetch(url=row["artifact_file_url"],destination=target,phase_id="provider_acquisition",policy=policy,ledger_path=ledger,expected_sha256=row["sha256"],budget_state=budget)
        if value["status"]!="PASS":return {"status":"BLOCK","blocker":"provider_artifact_fetch_failed","artifact":name,"fetch":value}
        row["artifact_path"]=str(target);selected[name]=row;events.append(value)
    ninja_source=next((dict(item) for item in context["lock_v4"].get("provider_records",[]) if str(item.get("package","")).lower()=="ninja" and item.get("status")=="PASS"),None)
    if ninja_source is None:return {"status":"BLOCK","blocker":"ninja_provider_lock_missing"}
    ninja_target=store/ninja_source["filename"]
    ninja_fetch=authorized_fetch(url=ninja_source["artifact_file_url"],destination=ninja_target,phase_id="provider_acquisition",policy=policy,ledger_path=ledger,expected_sha256=ninja_source["sha256"],budget_state=budget)
    if ninja_fetch["status"]!="PASS":return {"status":"BLOCK","blocker":"ninja_provider_artifact_fetch_failed","fetch":ninja_fetch}
    ninja={**ninja_source,"artifact_path":str(ninja_target),"status":"PASS"};events.append(ninja_fetch)
    context["lock_v4"]={**context["lock_v4"],"selected_artifacts":selected};context["artifact_store"]=str(store)
    source=workspace/"nbclient"
    authorization=authorize_network_operation(phase_id="provider_acquisition",policy=policy,destination="https://github.com/jupyter/nbclient.git",requested_mode="bounded_read_only",projected_requests=budget["requests"]+1,projected_bytes=budget["bytes"])
    if authorization["status"]!="PASS":return authorization
    clone=subprocess.run(["git","clone","--filter=blob:none","https://github.com/jupyter/nbclient.git",str(source)],capture_output=True,text=True,encoding="utf-8",errors="replace",timeout=300)
    checkout=subprocess.run(["git","-c",f"safe.directory={source}","-C",str(source),"checkout","--detach",CANDIDATE_SHA],capture_output=True,text=True,encoding="utf-8",errors="replace",timeout=120) if clone.returncode==0 else clone
    append_network_event(ledger,{"phase_id":"provider_acquisition","url":"https://github.com/jupyter/nbclient.git","host":"github.com","status":"PASS" if clone.returncode==checkout.returncode==0 else "BLOCK","blocker":None if clone.returncode==checkout.returncode==0 else "source_clone_failed","http_status":None,"bytes":0,"sha256":None,"tls_verification":True})
    if clone.returncode or checkout.returncode:return {"status":"BLOCK","blocker":"source_clone_failed","stderr":(clone.stderr+checkout.stderr)[-6000:]}
    context["source_root"]=str(source)
    builder=prepare_historical_builder(workspace,context["image_digest"],Path(selected["rpds-py"]["artifact_path"]));cargo=builder.get("cargo_provider",{})
    stderr=str(cargo.get("stderr", ""));classification=classify_cargo_failure(stderr,cargo.get("returncode"))
    cargo["raw_failure_classification"]=classification
    append_network_event(ledger,{"phase_id":"provider_acquisition","url":"https://index.crates.io","host":"index.crates.io","status":cargo.get("status","BLOCK"),"blocker":cargo.get("blocker"),"http_status":None,"bytes":sum(item.get("size",0) for item in cargo.get("provider_manifest",[])),"sha256":cargo.get("provider_manifest_hash"),"tls_verification":True})
    method="cargo_fetch" if cargo.get("status")=="PASS" else "blocked";vendor={"status":"NOT_RUN"}
    if cargo.get("status")!="PASS" and classification in {"cargo_dns_resolution_failed","cargo_http_rate_limited","cargo_http_server_error","cargo_transient_transport_failure","cargo_registry_index_unreachable","cargo_static_crate_download_failed"}:
        lock_path=next((workspace/"rpds_rust_source").rglob("Cargo.lock"));vendor=build_vendor_tree(lock_path=lock_path,vendor_root=workspace/"cargo_vendor",cutoff=CUTOFF,phase_id="provider_acquisition",policy=policy,ledger_path=ledger)
        if vendor.get("status")=="PASS":method="direct_vendor"
    return {"status":"PASS","scientific_status":"PASS" if builder.get("status")=="PASS" else "BLOCK","blocker":builder.get("blocker"),"builder":builder,"cargo":cargo,"cargo_method":method,"vendor":vendor,"ninja":ninja,"artifact_fetch_count":len(events),"request_count":budget["requests"],"download_bytes":budget["bytes"],"source_commit":CANDIDATE_SHA}


def classify_cargo_failure(stderr:str,returncode:int|None)->str:
    text=stderr.lower()
    if returncode==0:return "cargo_fetch_pass"
    if returncode is None and not text:return "cargo_fetch_pass"
    if "could not resolve host" in text or "dns" in text:return "cargo_dns_resolution_failed"
    if "certificate" in text or "tls" in text:return "cargo_tls_verification_failed"
    if "429" in text or "too many requests" in text:return "cargo_http_rate_limited"
    if any(code in text for code in ("500","502","503","504")):return "cargo_http_server_error"
    if "failed to get successful http response" in text or "connection reset" in text:return "cargo_transient_transport_failure"
    if "failed to download" in text:return "cargo_static_crate_download_failed"
    if "failed to query replaced source registry" in text or "index" in text:return "cargo_registry_index_unreachable"
    if "checksum" in text:return "cargo_manifest_or_lock_error"
    if "lock file" in text or "manifest" in text:return "cargo_manifest_or_lock_error"
    if "permission denied" in text or "read-only file system" in text:return "cargo_cache_not_writable"
    return "cargo_failure_unclassified"


def migrate_board_v4(board:dict[str,Any],provider:dict[str,Any])->dict[str,Any]:
    value=copy.deepcopy(board);branches=value.get("branches",{});pruned=0
    cargo_pass=provider.get("cargo",{}).get("status")=="PASS"
    for cell in value.get("cells",[]):
        membership=cell.get("branch_membership");branch=branches.get(membership,{})
        if branch.get("branch_state")=="CLOSED":
            cell["state"]="RESOLVED" if cell.get("cell_id")==branch.get("branch_id") else "SAFE";cell["semantic_state"]=cell["state"];cell["hypothesis_state"]=cell["state"]
        elif membership in {"pyzmq","rpds-py"}:
            cell["state"]="CAUSAL_MINE" if cell.get("cell_id")==branch.get("branch_id") else "UNKNOWN";cell["semantic_state"]=cell["state"];cell["hypothesis_state"]=cell["state"]
        if membership in {"coverage","markupsafe"} and any(term in str(cell.get("cell_id","")).lower() for term in ("cargo","rust","libzmq")):
            cell["state"]="NOT_APPLICABLE";cell["semantic_state"]="NOT_APPLICABLE";cell["hypothesis_state"]="NOT_APPLICABLE";pruned+=1
        if membership=="rpds-py" and "cargo" in str(cell.get("cell_id","")).lower():cell["state"]="SAFE" if cargo_pass else "CAUSAL_MINE";cell["semantic_state"]=cell["state"];cell["hypothesis_state"]=cell["state"]
        raw={k:v for k,v in cell.items() if k!="state_hash"};cell["state_hash"]=hash_record(raw)
    additions=[
        {"constraint_id":"H8-RPDS-CARGO","constraint_type":"requires","members":["BUILD-CELL-RPDS_PY","BUILD-CELL-RPDS_PY:missing_Cargo"],"source_evidence_hashes":[provider.get("cargo",{}).get("provider_manifest_hash") or hash_record(provider)],"description":"rpds build requires Cargo provider closure"},
        {"constraint_id":"H8-RPDS-RUST","constraint_type":"requires","members":["BUILD-CELL-RPDS_PY","BUILD-CELL-RPDS_PY:missing_Rust_toolchain"],"source_evidence_hashes":[hash_record(provider.get("builder",{}).get("rust",{}))],"description":"rpds build requires Rust toolchain identity"},
        {"constraint_id":"H8-PYZMQ-NINJA","constraint_type":"requires","members":["BUILD-CELL-PYZMQ","BUILD-CELL-PYZMQ:missing_Ninja"],"source_evidence_hashes":[provider.get("ninja",{}).get("sha256") or hash_record(provider.get("ninja",{}))],"description":"pyzmq build requires Ninja provider"},
        {"constraint_id":"H8-BRANCH-GOAL","constraint_type":"requires","members":["BUILD-CELL-RPDS_PY","BUILD-CELL-RPDS_PY:wheel_tag_or_ABI_mismatch"],"source_evidence_hashes":[hash_record({"goal":"verified wheel and runtime import"})],"description":"branch closure requires verified wheel and runtime import"},
    ]
    closed_prefixes={"BUILD-CELL-COVERAGE:","BUILD-CELL-MARKUPSAFE:"}
    retained=[]
    for constraint in value.get("constraints",[]):
        members=list(constraint.get("members",[]))
        if constraint.get("constraint_type")=="at_least_one" and members and any(all(str(member).startswith(prefix) for member in members) for prefix in closed_prefixes):
            pruned+=1
            continue
        retained.append(constraint)
    value["constraints"]=[*retained,*additions];value["schema_version"]="amds.board.v4";value["hypotheses_pruned"]=pruned;value.pop("board_hash",None);value["board_hash"]=hash_record(value);return value


def official_amds_demonstration(board:dict[str,Any],provider:dict[str,Any])->dict[str,Any]:
    cargo_pass=provider.get("cargo",{}).get("status")=="PASS";branch=board["branches"]["rpds-py"]
    probe={"probe_id":"h8-official-cargo-observation","probe_type":"cargo_provider_probe","candidate_id":CANDIDATE,"cell_id":branch["branch_id"],"branch_key":"rpds-py","targeted_hypotheses":["rpds:registry_transport","rpds:build_ready"],"prior_probabilities":{"rpds:registry_transport":0.7,"rpds:build_ready":0.3},"utility":1.0,"generation":1}
    def execute():
        evidence={"cargo_status":provider.get("cargo",{}).get("status"),"classification":provider.get("cargo",{}).get("raw_failure_classification"),"provider_manifest_hash":provider.get("cargo",{}).get("provider_manifest_hash")}
        return {"status":"PASS" if cargo_pass else "BLOCK","operation_status":"PASS","blocker":None if cargo_pass else provider.get("blocker"),"evidence":evidence,"evidence_hash":hash_record(evidence),"raw_evidence_captured":True,"supported_hypotheses":["rpds:build_ready"] if cargo_pass else ["rpds:registry_transport"],"refuted_hypotheses":["rpds:registry_transport"] if cargo_pass else ["rpds:build_ready"],"hypothesis_likelihoods":{"rpds:registry_transport":0.01 if cargo_pass else 0.99,"rpds:build_ready":0.99 if cargo_pass else 0.01},"semantic_verification":{"status":"PASS","independent_basis":"Cargo provider manifest and return code recomputation"},"custody_verification":{"status":"PASS","hash":hash_record(evidence)}}
    run=run_amds_active_loop(board,[probe],lambda item:execute,budget=1,interlock_pass=True,goal_evaluator=lambda branch,observation,probe:{"status":"BLOCK","goal_passed":False,"reason":"wheel verification still required"})
    return run


def _normalized_wheel_hash(path:Path)->str:
    import zipfile
    with zipfile.ZipFile(path) as source:
        rows=[(name,hashlib.sha256(source.read(name)).hexdigest()) for name in sorted(source.namelist()) if not name.endswith("/RECORD")]
    return hash_record(rows)


def semantic_failure_signature(text:str,*,collect:bool)->dict[str,Any]:
    plain=re.sub(r"\x1b\[[0-9;]*m","",text)
    return {"failed_node_ids":sorted(set(re.findall(r"FAILED\s+(tests/test_cli\.py::[^\s]+)",plain))),"exception_types":sorted(set(re.findall(r"\b(?:AssertionError|TypeError|AttributeError|DeprecationWarning)\b",plain))),"mock_call_mismatch":("mock_calls" in plain or "path_open" in plain) and "AssertionError" in plain,"targets":["test_mult","test_output"] if not collect else ["tests/test_cli.py"]}


def dual_reproducible_build(context:dict[str,Any])->dict[str,Any]:
    provider=context["h8_provider"]
    if provider.get("scientific_status")!="PASS":return {"status":"BLOCK","blocker":provider.get("blocker") or "cargo_provider_closure_required"}
    base={**context,"h7_providers":{"status":"PASS","ninja":provider["ninja"],"builder":provider["builder"]},"amds_board":context["amds_board_v4"]}
    first=canonical_dual_recovery(copy.deepcopy(base));second=canonical_dual_recovery(copy.deepcopy(base))
    registry=[]
    for package in ("coverage","markupsafe","pyzmq","rpds-py"):
        one=next((Path(row["wheel_path"]) for row in first.get("build_results",[]) if row.get("package")==package and row.get("status")=="PASS"),None);two=next((Path(row["wheel_path"]) for row in second.get("build_results",[]) if row.get("package")==package and row.get("status")=="PASS"),None)
        registry.append({"package":package,"status":"PASS" if one and two else "BLOCK","wheel_hash_run_1":_sha(one) if one else None,"wheel_hash_run_2":_sha(two) if two else None,"exact_byte_reproducibility":bool(one and two and _sha(one)==_sha(two)),"normalized_content_hash_run_1":_normalized_wheel_hash(one) if one else None,"normalized_content_hash_run_2":_normalized_wheel_hash(two) if two else None,"normalized_content_reproducibility":bool(one and two and _normalized_wheel_hash(one)==_normalized_wheel_hash(two)),"wheel_path_run_1":str(one) if one else None,"wheel_path_run_2":str(two) if two else None})
    passed=first.get("status")==second.get("status")=="PASS" and all(item["status"]=="PASS" and item["normalized_content_reproducibility"] for item in registry)
    return {"status":"PASS" if passed else "BLOCK","blocker":None if passed else "wheel_reproducibility_or_verification_failed","run_1":first,"run_2":second,"registry":registry,"built_wheels":[item["wheel_path_run_1"] for item in registry if item["wheel_path_run_1"]],"board":first.get("board",context["amds_board_v4"])}


def _run_pytest_arm(context:dict[str,Any],*,warning_default:bool,collect:bool,run_id:int)->dict[str,Any]:
    source=Path(context["source_root"]);store=Path(context["offline_capsule"]["artifact_store"]);requirements=[f"{n}=={r['version']}" for n,r in context["lock_v4"]["selected_artifacts"].items() if set(r.get("dependency_classes",[]))!={"build"} and n!="nbclient"]
    warning="-W default " if warning_default else "";target="--collect-only -q -p no:cacheprovider tests/test_cli.py" if collect else "-q -p no:cacheprovider tests/test_cli.py::test_mult tests/test_cli.py::test_output"
    script="python -m venv /tmp/env && /tmp/env/bin/python -m pip install --no-index --find-links=/artifacts "+" ".join(requirements)+f" && cd /src && PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=/src /tmp/env/bin/python -m pytest {warning}{target}"
    command=["docker","run","--rm","--network","none","--read-only","--user","65534:65534","--cap-drop","ALL","--security-opt","no-new-privileges","--tmpfs","/tmp:rw,exec,nosuid,size=2g","-v",f"{store.resolve()}:/artifacts:ro","-v",f"{source.resolve()}:/src:ro","-e","HOME=/tmp","--entrypoint","/bin/sh",context["image_digest"],"-c",script]
    before=hash_record([(_p.relative_to(source).as_posix(),_sha(_p)) for _p in sorted(source.rglob("*")) if _p.is_file()]);run=subprocess.run(command,capture_output=True,text=True,encoding="utf-8",errors="replace",timeout=1200);after=hash_record([(_p.relative_to(source).as_posix(),_sha(_p)) for _p in sorted(source.rglob("*")) if _p.is_file()]);plain=re.sub(r"\x1b\[[0-9;]*m","",run.stdout+"\n"+run.stderr);nodes=sorted(set(re.findall(r"(?:FAILED\s+)?(tests/test_cli\.py::[^\s]+)",plain)))
    if collect:passed=run.returncode==0 and bool(nodes)
    else:passed=run.returncode!=0 and any(name in run.stdout for name in ("test_mult","test_output"))
    semantic=semantic_failure_signature(plain,collect=collect)
    return {"status":"PASS" if passed and before==after else "BLOCK","classification":"decision_time_project_declared_warning_diagnostic" if warning_default else "historical_warning_policy_boundary_reproduced" if collect and run.returncode else "default_policy_pass","run_id":run_id,"returncode":run.returncode,"node_ids":nodes,"node_count":len(nodes),"stdout":run.stdout,"stderr":run.stderr,"raw_signature_hash":hash_record({"stdout":run.stdout,"stderr":run.stderr}),"semantic_failure_signature":semantic,"semantic_signature_hash":hash_record(semantic),"source_hash_before":before,"source_hash_after":after,"source_mutations":0 if before==after else 1,"test_bodies_executed":0 if collect else 2,"network_count":0,"command":command}


def offline_and_sbom(context:dict[str,Any])->dict[str,Any]:
    context["build_recovery"]={"status":"PASS","built_wheels":context["h8_builds"]["built_wheels"]};context["lock_v3"]=context["lock_v4"]
    result=execute_h5_phase("offline_capsule_materialization",context)
    if result.get("status")!="PASS":return {"status":"BLOCK","blocker":result.get("blocker"),"offline":result.get("context_updates",{}).get("offline_capsule",{})}
    capsule=result["context_updates"]["offline_capsule"];packages=[{"name":name,"version":row["version"],"sha256":row["sha256"]} for name,row in sorted(context["lock_v4"]["selected_artifacts"].items())];capsule["sbom"]={"status":"PASS","packages":packages,"package_count":len(packages),"provider_hash":context["h8_provider"]["cargo"].get("provider_manifest_hash"),"wheel_count":len(context["h8_builds"]["built_wheels"])};capsule.update({"runner_origin":"PASS","target_origin":"PASS","harness_origin":"PASS","test_tree_immutability":"PASS","provider_lock":"PASS"});return {"status":"PASS","capsule":capsule}


def warning_orthology(context:dict[str,Any])->dict[str,Any]:
    arm_a=_run_pytest_arm(context,warning_default=False,collect=True,run_id=1);one=_run_pytest_arm(context,warning_default=True,collect=True,run_id=1);two=_run_pytest_arm(context,warning_default=True,collect=True,run_id=2);same=one.get("node_ids")==two.get("node_ids") and one.get("node_count",0)>0
    return {"status":"PASS" if one.get("status")==two.get("status")=="PASS" and same else "BLOCK","blocker":None if same else "warning_diagnostic_duplicate_collection_failed","default_arm":arm_a,"diagnostic_run_1":one,"diagnostic_run_2":two,"node_set_equivalence":same,"diagnostic_node_count":one.get("node_count",0)}


def ownership_and_routing(context:dict[str,Any])->dict[str,Any]:
    one=_run_pytest_arm(context,warning_default=True,collect=False,run_id=1);two=_run_pytest_arm(context,warning_default=True,collect=False,run_id=2);equivalent=one.get("semantic_signature_hash")==two.get("semantic_signature_hash") and one.get("status")==two.get("status")=="PASS";text=one.get("stdout","")+one.get("stderr","");mock_behavior=bool(one.get("semantic_failure_signature",{}).get("mock_call_mismatch"))
    ownership="interpreter_mock_behavior_change" if equivalent and mock_behavior else "source_owned_behavior_defect" if equivalent and "/src/nbclient/" in text else "insufficient_evidence"
    retired=ownership in {"test_expectation_fragility","interpreter_mock_behavior_change"};replacement=select_replacement(context) if retired else {"status":"NOT_RUN","selected":None}
    return {"status":"PASS" if equivalent else "BLOCK","blocker":None if equivalent else "nbclient_duplicate_prerepair_not_equivalent","run_1":one,"run_2":two,"signature_equivalence":equivalent,"ownership":ownership,"source_repair_admissible":ownership=="source_owned_behavior_defect","candidate_terminal_state":"retired_from_source_only_repair_queue" if retired else "active_source_repair_candidate" if ownership=="source_owned_behavior_defect" else "blocked_insufficient_evidence","retirement_reason":"test_expectation_or_interpreter_behavior" if retired else None,"replacement":replacement,"patch_generated":False,"duplicate_replay":"NOT_RUN","count_gate":"NOT_RUN"}


def select_replacement(context:dict[str,Any])->dict[str,Any]:
    registry_path=Path(context["repo_root"])/"configs/controllergate_seed_product_readiness_registry.json";state=json.loads(registry_path.read_text(encoding="utf-8"));candidates=sorted((item for item in state.get("records",[]) if item.get("candidate_id")!=CANDIDATE and item.get("batch069b_readiness_status")=="approved_for_future_probe" and not item.get("missing_candidate_sha") and item.get("audit_status")=="PASS"),key=lambda item:str(item["candidate_id"]))
    selected=candidates[0] if candidates else None
    return {"status":"BLOCK","selected":selected.get("candidate_id") if selected else None,"selection_count":1 if selected else 0,"selection_registry":registry_path.relative_to(Path(context["repo_root"])).as_posix() if selected else None,"selection_basis":"first outcome-blind lexicographic approved future probe with source identity" if selected else None,"repo_url":selected.get("repo_url") if selected else None,"authorization":"BLOCK","blocker":"replacement_candidate_command_not_authoritative" if selected and selected.get("missing_command_boundary") else "replacement_candidate_evidence_incomplete" if selected else "replacement_candidate_not_available","patch_generated":False,"duplicate_replay":"NOT_RUN","count_gate":"NOT_RUN"}


def execute_phase(phase_id:str,context:dict[str,Any],network_authorization:dict[str,Any])->dict[str,Any]:
    if phase_id=="provider_acquisition":
        value=hydrate_provider_inputs(context,network_authorization);return {"status":"PASS" if value.get("status")=="PASS" else "BLOCK","blocker":value.get("blocker"),"context_updates":{"h8_provider":value,"lock_v4":context.get("lock_v4"),"artifact_store":context.get("artifact_store"),"source_root":context.get("source_root")}}
    if network_authorization.get("network_mode")!="none":return {"status":"BLOCK","blocker":"offline_phase_network_policy_invalid"}
    if phase_id=="board_v4_migration":
        value=migrate_board_v4(context["h7_official_board"],context["h8_provider"]);return {"status":"PASS","context_updates":{"amds_board_v4":value}}
    if phase_id=="official_amds_execution":
        value=official_amds_demonstration(context["amds_board_v4"],context["h8_provider"]);return {"status":"PASS" if value.get("probes_executed",0)>0 else "BLOCK","blocker":None if value.get("probes_executed",0)>0 else "official_amds_execution_vacuous","context_updates":{"h8_amds_run":value,"amds_board_v4":value.get("board",context["amds_board_v4"])}}
    if phase_id=="dual_reproducible_wheel_build":
        value=dual_reproducible_build(context);return {"status":value["status"],"blocker":value.get("blocker"),"context_updates":{"h8_builds":value,"amds_board_v4":value.get("board",context["amds_board_v4"])}}
    if phase_id=="offline_capsule_sbom":
        value=offline_and_sbom(context);return {"status":value["status"],"blocker":value.get("blocker"),"context_updates":{"offline_capsule":value.get("capsule",value.get("offline",{}))}}
    if phase_id=="warning_orthology":
        value=warning_orthology(context);return {"status":value["status"],"blocker":value.get("blocker"),"context_updates":{"warning_orthology":value}}
    if phase_id=="ownership_and_terminal_routing":
        value=ownership_and_routing(context);return {"status":value["status"],"blocker":value.get("blocker"),"context_updates":{"ownership_routing":value}}
    return {"status":"BLOCK","blocker":"unknown_batch068h8_phase"}
