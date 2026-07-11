from __future__ import annotations

import hashlib
import json
from pathlib import Path
import shutil
import subprocess
from typing import Any

from controllergate.amds.board import build_board
from controllergate.amds.constraints import AmdsConstraint
from controllergate.amds.hypotheses import hypotheses_for_build_cell
from controllergate.amds.priors import structural_uniform_prior
from controllergate.amds.probe_planner import rank_probes
from controllergate.amds.runtime_adapter import run_amds_active_loop
from controllergate.amds.types import AmdsCell, AmdsEdge, CellState, ProbeCandidate
from controllergate.amds.propagation import propagate_constraints
from controllergate.core.evidence import hash_record
from .built_wheel_verifier import verify_built_wheel
from .per_package_wheel_builder import build_one
from .system_provider_lock import build_system_provider_lock
from .system_toolchain_inventory import inventory


BUILD_HYPOTHESES=("missing_python_build_requirement","missing_C_compiler","missing_Cxx_compiler","missing_linker","missing_Python_headers","missing_Rust_toolchain","missing_Cargo","missing_CMake","missing_Ninja","missing_pkg_config","missing_system_library","missing_libzmq","vendored_dependency_failure","build_backend_import_failure","unsupported_Python_3_13_beta","wheel_tag_or_ABI_mismatch","read_only_filesystem_violation","writable_path_missing","resource_limit","timeout","source_archive_problem","package_version_incompatibility")


def _tree_hash(root: Path) -> str:
    digest=hashlib.sha256()
    for path in sorted(p for p in root.rglob('*') if p.is_file() and '.git' not in p.parts):digest.update(path.relative_to(root).as_posix().encode());digest.update(hashlib.sha256(path.read_bytes()).digest())
    return digest.hexdigest()


def construct_amds_board(context: dict[str,Any]) -> dict[str,Any]:
    cells=[];edges=[];constraints=[]
    for cell in context["build_cells"]:
        cid=cell["cell_id"]; hypotheses=hypotheses_for_build_cell(cid,list(BUILD_HYPOTHESES))
        cells.append(AmdsCell(cid,"build_provider",context["candidate_id"],(cell["artifact_sha256"],),CellState.UNKNOWN.value,associated_hypotheses=tuple(h.hypothesis_id for h in hypotheses),allowed_probes=("runtime_incident_probe",),forbidden_actions=("source_patch","test_mutation"),reopen_conditions=("new build-provider evidence",)))
        hypothesis_cells=[]
        for h in hypotheses:
            hid=h.hypothesis_id; hypothesis_cells.append(hid); cells.append(AmdsCell(hid,"failure_hypothesis",context["candidate_id"],(cell["artifact_sha256"],),CellState.UNKNOWN.value,associated_hypotheses=(hid,),allowed_probes=("runtime_incident_probe",),forbidden_actions=("source_patch",))); edges.append(AmdsEdge(f"edge:{cid}:{hid}",cid,hid,"provider_dependency"))
        constraints.append(AmdsConstraint(f"constraint:{cid}:at-least-one","at_least_one",tuple(hypothesis_cells),(cell["artifact_sha256"],)))
    return build_board(context["candidate_id"],cells,edges,constraints)


def _amds_probes(context: dict[str,Any]) -> tuple[list[dict],list[dict]]:
    board=context["amds_board"]; hypotheses=[c["cell_id"] for c in board["cells"] if c["cell_type"]=="failure_hypothesis"]; prior=structural_uniform_prior(hypotheses)
    probes=[]; likelihoods={}
    for cell in context["build_cells"]:
        pid=f"probe:{cell['cell_id']}:system-and-build"; targeted=[h for h in hypotheses if h.startswith(cell["cell_id"]+':')]
        probe=ProbeCandidate(pid,"runtime_incident_probe",context["candidate_id"],tuple(targeted),execution_cost=1.0,metadata={"cell_id":cell["cell_id"]});probes.append(probe)
        posterior={h:(1/len(targeted) if h in targeted else 0.0) for h in hypotheses}; likelihoods[pid]={"positive":{"probability":0.5,"posterior":posterior},"negative":{"probability":0.5,"posterior":prior["probabilities"]}}
    return rank_probes(probes,prior["probabilities"],likelihoods),[{"probe_id":p.probe_id,"cell_id":p.metadata["cell_id"],"probe_type":p.probe_type} for p in probes]


def _build_all(context: dict[str,Any]) -> dict[str,Any]:
    results=[]; verified=[]; built_root=Path(context["workspace_root"])/"built_wheels"
    for cell in context["build_cells"]:
        out=built_root/cell["package"]; result=build_one(package=cell["package"],version=cell["version"],artifact=Path(cell["artifact_path"]),artifact_store=Path(context["artifact_store"]),output_dir=out,image_digest=context["image_digest"]);results.append(result)
        for wheel in result.get("produced_wheels",[]): verified.append(verify_built_wheel(Path(wheel),cell["package"],cell["version"],context["exact_tags"]))
    unresolved=[r for r in results if r["status"]!="PASS"]+[r for r in verified if r["status"]!="PASS"]
    return {"status":"PASS" if not unresolved else "BLOCK","blocker":None if not unresolved else "build_provider_branch_unresolved","results":results,"wheel_verification":verified,"built_wheels":[w for r in results for w in r.get("produced_wheels",[])],"unresolved_packages":sorted({r.get("package") for r in unresolved if r.get("package")})}


def _offline(context: dict[str,Any]) -> dict[str,Any]:
    store=Path(context["artifact_store"]); built=[Path(p) for p in context["build_recovery"]["built_wheels"]]; source=Path(context["source_root"])
    install_store=Path(context["workspace_root"])/"execution_artifacts";install_store.mkdir(exist_ok=True)
    built_packages={p.parent.name for p in built}
    for path in store.iterdir():
        if path.is_file() and not (path.name.endswith(('.tar.gz','.zip'))):shutil.copy2(path,install_store/path.name)
    for path in built:shutil.copy2(path,install_store/path.name)
    requirements=[f"{name}=={record['version']}" for name,record in context["lock_v3"]["selected_artifacts"].items() if set(record.get('dependency_classes',[]))!={'build'} and name!='nbclient']
    script="python -m venv /tmp/env && /tmp/env/bin/python -m pip install --no-index --find-links=/artifacts " + " ".join(requirements) + " && cd /src && PYTHONPATH=/src /tmp/env/bin/python -c \"import nbclient,pytest,json; print(json.dumps({'nbclient':nbclient.__file__,'pytest':pytest.__file__}))\""
    command=["docker","run","--rm","--network","none","--read-only","--user","65534:65534","--cap-drop","ALL","--security-opt","no-new-privileges","--pids-limit","256","--memory","3g","--cpus","2","--tmpfs","/tmp:rw,exec,nosuid,size=2g","-v",f"{install_store.resolve()}:/artifacts:ro","-v",f"{source.resolve()}:/src:ro","-e","HOME=/tmp","--entrypoint","/bin/sh",context["image_digest"],"-c",script]
    before=_tree_hash(source);r=subprocess.run(command,capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=900);after=_tree_hash(source)
    return {"status":"PASS" if r.returncode==0 and before==after else "BLOCK","blocker":None if r.returncode==0 and before==after else "offline_install_or_origin_verification_failed","returncode":r.returncode,"stdout":r.stdout[-8000:],"stderr":r.stderr[-8000:],"command":command,"artifact_store":str(install_store),"source_tree_hash":before,"source_mutations":0 if before==after else 1,"network_count":0}


def _run_pytest(context: dict[str,Any], collect: bool, run_id: int) -> dict[str,Any]:
    source=Path(context["source_root"]);store=Path(context["offline_capsule"]["artifact_store"]);requirements=[f"{n}=={r['version']}" for n,r in context["lock_v3"]["selected_artifacts"].items() if set(r.get('dependency_classes',[]))!={'build'} and n!='nbclient']
    target="--collect-only -q -p no:cacheprovider tests/test_cli.py" if collect else "-q -p no:cacheprovider tests/test_cli.py"
    script="python -m venv /tmp/env && /tmp/env/bin/python -m pip install --no-index --find-links=/artifacts " + " ".join(requirements) + f" && cd /src && PYTHONPATH=/src /tmp/env/bin/python -m pytest {target}"
    command=["docker","run","--rm","--network","none","--read-only","--user","65534:65534","--cap-drop","ALL","--security-opt","no-new-privileges","--pids-limit","256","--memory","3g","--cpus","2","--tmpfs","/tmp:rw,exec,nosuid,size=2g","-v",f"{store.resolve()}:/artifacts:ro","-v",f"{source.resolve()}:/src:ro","-e","HOME=/tmp","--entrypoint","/bin/sh",context["image_digest"],"-c",script]
    before=_tree_hash(source);r=subprocess.run(command,capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=1200);after=_tree_hash(source);nodes=sorted({line.strip() for line in r.stdout.splitlines() if '::' in line and not line.startswith(('<','='))})
    signature=hashlib.sha256((r.stdout+r.stderr).encode()).hexdigest();ok=(r.returncode==0 and bool(nodes)) if collect else (r.returncode!=0)
    return {"status":"PASS" if ok and before==after else "BLOCK","blocker":None if ok and before==after else ("historical_warning_policy_boundary_reproduced" if collect else "target_passes_no_issue_reproduction"),"run_id":run_id,"returncode":r.returncode,"node_ids":nodes,"node_count":len(nodes),"signature_hash":signature,"stdout":r.stdout[-16000:],"stderr":r.stderr[-16000:],"source_mutations":0 if before==after else 1,"test_mutations":0,"network_count":0,"test_bodies_executed":0 if collect else None}


def execute_phase(phase_id: str, context: dict[str,Any]) -> dict[str,Any]:
    if phase_id=="amds_build_board":
        board=construct_amds_board(context);return {"status":"PASS","context_updates":{"amds_board":board}}
    if phase_id=="amds_propagate_constraints":
        value=propagate_constraints(context["amds_board"]);return {"status":value["status"],"blocker":None if value["status"]=="PASS" else "amds_constraint_contradiction","context_updates":{"amds_propagation":value}}
    if phase_id=="amds_execute_probe":
        ranked,probes=_amds_probes(context);inv=inventory(context["image_digest"]);lock=build_system_provider_lock(inv,context["build_cells"])
        def factory(probe):return lambda:{"status":"PASS" if inv["status"]=="PASS" else "BLOCK","blocker":inv.get("blocker"),"evidence_hash":hash_record(inv),"classifications":tuple(k for k,v in inv.get("tools",{}).items() if v),"mutation_count":0}
        result=run_amds_active_loop(context["amds_board"],probes,factory,budget=max(1,len(probes)),interlock_pass=True)
        status="PASS" if inv["status"]=="PASS" else "BLOCK";return {"status":status,"blocker":None if status=="PASS" else inv.get("blocker"),"context_updates":{"amds_ranked_probes":ranked,"amds_run":result,"system_inventory":inv,"system_provider_lock":lock}}
    if phase_id=="build_provider_recovery":
        result=_build_all(context);return {"status":result["status"],"blocker":result.get("blocker"),"context_updates":{"build_recovery":result}}
    if phase_id=="offline_capsule_materialization":
        result=_offline(context);return {"status":result["status"],"blocker":result.get("blocker"),"context_updates":{"offline_capsule":result}}
    if phase_id=="collection_run_1":
        result=_run_pytest(context,True,1);return {"status":result["status"],"blocker":result.get("blocker"),"context_updates":{"collection_run_1":result}}
    if phase_id=="collection_run_2":
        if context.get("collection_run_1",{}).get("status")!="PASS":return {"status":"BLOCK","blocker":"collection_run_2_requires_nonzero_run_1"}
        result=_run_pytest(context,True,2);same=result.get("node_ids")==context["collection_run_1"].get("node_ids");result.update({"status":"PASS" if result["status"]=="PASS" and same else "BLOCK","node_set_equivalence":same,"blocker":None if result["status"]=="PASS" and same else "collection_node_set_mismatch"});return {"status":result["status"],"blocker":result.get("blocker"),"context_updates":{"collection_run_2":result}}
    if phase_id in {"prerepair_replay_1","prerepair_replay_2"}:
        if context.get("collection_run_2",{}).get("status")!="PASS":return {"status":"BLOCK","blocker":"prerepair_requires_duplicate_collection"}
        run_id=1 if phase_id.endswith('_1') else 2;result=_run_pytest(context,False,run_id);return {"status":result["status"],"blocker":result.get("blocker"),"context_updates":{phase_id:result}}
    if phase_id=="patch_authorization":
        r1=context.get("prerepair_replay_1",{});r2=context.get("prerepair_replay_2",{});equivalent=r1.get("signature_hash")==r2.get("signature_hash") and r1.get("status")==r2.get("status")=="PASS"
        return {"status":"BLOCK","blocker":"bounded_repair_adapter_requires_source_locality_and_activation_license","context_updates":{"patch_authorization":{"status":"BLOCK","single_use":True,"duplicate_prerepair_reproduction":equivalent,"patch_generated":False}}}
    return {"status":"BLOCK","blocker":"unknown_batch068h5_phase"}
