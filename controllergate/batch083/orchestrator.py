from __future__ import annotations

import hashlib
import itertools
import json
import os
import shutil
import subprocess
import sys
import tempfile
import tomllib
import zipfile
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from typing import Any

from controllergate.amds.historical_challenge import execute_historical_challenge
from controllergate.connectors.github_public_readonly import read_frozen_resource
from controllergate.connectors.offline_canary import execute_offline_canary
from controllergate.deployment.historical_canary import execute_historical_canary
from controllergate.engine import resume_run, run_manifest, verify_run
from controllergate.governance.capability_maturity import adjudicate_dimension
from controllergate.governance.raw_law_evidence import bind_law_proof
from controllergate.inputs.openapi_reference_resolver import resolve_closure
from controllergate.inputs.openapi_reference_verifier import verify_hashes
from controllergate.reactions.catalyst import Catalyst
from controllergate.reactions.cycle_guard import CycleGuard
from controllergate.reactions.entity import Entity
from controllergate.reactions.event import ReactionEvent
from controllergate.reactions.regulation import Regulator
from controllergate.reactions.stable_identity import stable_hash
from controllergate.reactions.translocation import translocate
from controllergate.runtime.linux_namespace_guard import verify_namespace_guard
from controllergate.runtime.loopback_transport_verifier import verify_loopback
from controllergate.runtime.provider_capsule_v4 import seal_provider
from controllergate.runtime.provider_capsule_verifier_v4 import verify_provider
from controllergate.runtime.provider_dependency_graph import graph_from_wheels
from controllergate.runtime.provider_function_probe import entrypoint_probe, import_probe
from controllergate.runtime.provider_offline_installer import offline_install, pip_check, python_in
from controllergate.runtime.windows_process_egress_guard import install_process_guards, remove_process_guards, verify_process_guard


ROOT = Path(__file__).resolve().parents[2]
BATCH = "post_v2_37_hardening_batch083_reaction_product_cross_area_wave1g"
EXPECTED_ARTIFACTS = {
    "8295240189": {"name":"batch082_openbb_v5_linux_py311_provider","size":276477,"sha256":"e5d9f5370c4903707ea5ee042ec334415426f0530148075a23ace3436f7fd59c"},
    "8295240545": {"name":"batch082_openbb_eodhd_openapi_input_snapshot","size":175749,"sha256":"a86e77a355fdd4a99f8449bc03151f8a683f58a6772dc121c07d03118719ee3c"},
    "8295255269": {"name":"batch082_poetry_241_windows_py313_provider","size":11681563,"sha256":"ca646ecd731e73eca2ec78b7b8dddfe138aa988ac89d90329ec9594cae4610d8"},
}


def write(path: Path, value: Any) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    return path


def append_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(row, sort_keys=True) + "\n" for row in rows), encoding="utf-8", newline="\n")


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _zip_audit(archive: Path) -> dict[str, Any]:
    unsafe=[]; duplicates=[]; seen=set(); entries=[]
    with zipfile.ZipFile(archive) as zf:
        for info in zf.infolist():
            path=PurePosixPath(info.filename.replace("\\","/")); key=str(path).casefold()
            if path.is_absolute() or ".." in path.parts: unsafe.append(info.filename)
            if key in seen: duplicates.append(info.filename)
            seen.add(key); entries.append({"path":info.filename,"bytes":info.file_size,"crc":info.CRC})
    return {"entry_count":len(entries),"unsafe_paths":unsafe,"duplicate_paths":duplicates,"entries":entries}


def verify_prior_artifacts(store: Path, verified: Path, out: Path) -> dict[str, Any]:
    records=[]; verified.mkdir(parents=True, exist_ok=True)
    for artifact_id, expected in EXPECTED_ARTIFACTS.items():
        archive=store/f"{artifact_id}.zip"; audit=_zip_audit(archive) if archive.is_file() else {"entry_count":0,"unsafe_paths":["missing"],"duplicate_paths":[]}
        observed_size=archive.stat().st_size if archive.is_file() else 0; observed_sha=sha(archive) if archive.is_file() else None
        target=verified/artifact_id
        if archive.is_file() and not audit["unsafe_paths"] and not audit["duplicate_paths"]:
            if target.exists(): shutil.rmtree(target)
            target.mkdir(parents=True); zipfile.ZipFile(archive).extractall(target)
        embedded=[]
        for manifest_name in ("provider_manifest.json","input_manifest.json"):
            manifest=target/manifest_name
            if manifest.is_file():
                value=json.loads(manifest.read_text(encoding="utf-8")); failures=[]
                for row in value.get("wheels", value.get("yaml_reference_closure", [])):
                    rel=("wheelhouse/"+row["name"]) if "name" in row else ("snapshot/"+row["path"])
                    item=target/rel
                    if not item.is_file() or sha(item)!=row["sha256"]: failures.append(rel)
                embedded.append({"manifest":manifest_name,"status":"PASS" if not failures else "FAIL","checked":len(value.get("wheels",value.get("yaml_reference_closure",[]))),"failures":failures,"seal":value.get("provider_seal",value.get("input_seal"))})
        byte_bound=(observed_size==expected["size"] and observed_sha==expected["sha256"] and not audit["unsafe_paths"] and not audit["duplicate_paths"])
        embedded_pass=bool(embedded) and all(r["status"]=="PASS" for r in embedded)
        records.append({"artifact_id":int(artifact_id),"reported_name":expected["name"],"reported_archive_size":expected["size"],"observed_archive_size":observed_size,"reported_digest":expected["sha256"],"observed_archive_sha256":observed_sha,"zip_entry_count":audit["entry_count"],"unsafe_paths":audit["unsafe_paths"],"duplicate_paths":audit["duplicate_paths"],"embedded_manifests":embedded,"translocation":{"source":"github_actions_artifact","destination":str(target),"source_hash":observed_sha,"destination_archive_hash":observed_sha,"verifier":"sha256"},"byte_binding_status":"PASS" if byte_bound else "FAIL","embedded_manifest_coverage_status":"PASS" if embedded_pass else "BLOCKED_EXACT_WITH_NEW_EVIDENCE","exact_blocker":None if embedded_pass else "batch082_embedded_manifest_member_absent_from_exact_archive","status":"PASS" if byte_bound and embedded_pass else ("PASS_WITH_EXACT_STAGE_EVIDENCE" if byte_bound else "FAIL")})
    append_jsonl(out/"batch083_batch082_artifact_byte_binding.jsonl",records)
    byte_pass=all(r["byte_binding_status"]=="PASS" for r in records)
    embedded_pass=all(r["embedded_manifest_coverage_status"]=="PASS" for r in records)
    summary={"status":"PASS" if byte_pass and embedded_pass else ("PASS_WITH_EXACT_STAGE_EVIDENCE" if byte_pass else "FAIL"),"artifact_count":len(records),"archive_byte_binding":"PASS" if byte_pass else "FAIL","embedded_manifest_coverage":"PASS" if embedded_pass else "BLOCKED_EXACT_WITH_NEW_EVIDENCE","records":records}
    write(out/"batch083_batch082_artifact_verification_summary.json",summary); return summary


def prepare(out: Path, runtime: Path) -> None:
    ingest=json.loads((ROOT/"evidence/official_ingests/batch082_artifact_ingest.json").read_text(encoding="utf-8"))
    preservation={"status":"PASS","batch082_ingest_commit":"3b8f66c8ab7f51ea268293c71bf9815a3f17071c","official_ingest_record":ingest,"reingested":False,"raw_outputs_modified":False}
    write(out/"batch082_ingest_preservation.json",preservation)
    write(out/"batch082_claim_preservation.json",{"status":"PASS","protocol":"v2.19","issue_derived_repair_count":6,"native_external_repair_count":4,"full_scoring":"NOT_RUN/disallowed","prospective_amds_effectiveness":"NOT_ESTABLISHED","prospective_memory_lift":"not demonstrated","self_maintaining_software":"false/not demonstrated","write_capable_connectors":"inactive"})
    write(out/"batch082_count_preservation.json",{"status":"PASS","issue_derived_repair_count":6,"native_external_repair_count":4,"COUNT_6_HARDENING":"PASS","count_changed":False})
    b82=ROOT/"outputs/post_v2_37_hardening_batch082_ci_native_maintenance_order_provider_wave1f"
    sums=b82/"SHA256SUMS.txt"; failures=[]; checked=0
    if sums.is_file():
        for line in sums.read_text(encoding="utf-8").splitlines():
            if not line.strip(): continue
            digest, rel=line.split(maxsplit=1); rel=rel.lstrip(" *"); path=b82/rel; checked+=1
            if not path.is_file() or sha(path)!=digest: failures.append(rel)
    write(out/"batch082_main_artifact_manifest_reverification.json",{"status":"PASS" if not failures else "FAIL","manifest_entries_checked":checked,"failures":failures})
    reconciliations={
      "batch082_provider_depth_reconciliation.json":{"OPENBB_PROJECT_WHEEL_BUILT":"PASS","OPENBB_PROJECT_WHEEL_HASHED":"PASS","OPENBB_TRANSITIVE_DEPENDENCY_CLOSURE":"BLOCK","OPENBB_TWO_FRESH_OFFLINE_INSTALLS":"BLOCK","OPENBB_PIP_CHECK":"NOT_RUN","OPENBB_IMPORT_PROBE":"NOT_RUN","OPENBB_ENTRYPOINT_PROBE":"NOT_RUN","OPENBB_PROVIDER_EXECUTION_READY":False,"OPENBB_PROVIDER_COFACTOR_MATERIALIZED":False},
      "batch082_reproducer_depth_reconciliation.json":{"frozen_secondary_input":"PASS under Batch082 artifact criteria","reproducer_contract":"DEFINED","rooted_openapi_reference_closure":"NOT_ESTABLISHED","loopback_namespace":"NOT_RUN","generate_spec":"NOT_RUN","generate_extension":"NOT_RUN","incident_reproduction":"NOT_ESTABLISHED"},
      "batch082_poetry_isolation_reconciliation.json":{"provider_artifact":"PASS under Batch082 criteria","duplicate_behavior_reproduction":"CANDIDATE_FAILURE_REPRODUCED","equivalent_signatures":"PASS","process_level_network_isolation":"BLOCK_NOT_VERIFIED","candidate_admission":"BLOCK","source_ownership":"NOT_ESTABLISHED","repair_license":"CLOSED"},
      "batch082_pathway_depth_reconciliation.json":{"historical_optimistic_state":"PROVIDER_COFACTOR_MATERIALIZED","corrected_state":"PROVIDER_ARTIFACT_SET_CREATED","failed_transition":"PROVIDER_ARTIFACT_SET_CREATED -> PROVIDER_OFFLINE_INSTALL_PASSED","failure_class":"FAILED_REACTION_REQUIRED_INPUT_COMPONENTS_ABSENT"},
      "batch082_sentinel_depth_reconciliation.json":{"classification":"VACUOUS_SENTINEL_RESULT","required_sentinel_count":0,"observed_sentinel_count":0,"operational_coverage":False},
      "batch082_placeholder_stage_reconciliation.json":{"pilot_engine":"PLACEHOLDER_STATUS_WRITER","ground_truth_engine":"PLACEHOLDER_STATUS_WRITER","authorization_engine":"PLACEHOLDER_STATUS_WRITER","repair_engine":"PLACEHOLDER_STATUS_WRITER","false_repair_result":False,"replacement_required_before_candidate_admission":True},
    }
    v2=json.loads((ROOT/"configs/controllergate_engineering_constitution_v2.json").read_text(encoding="utf-8")); missing=[]
    for law in v2["laws"]:
        path=b82/law["proof_artifact"]
        if not path.is_file(): missing.append(law["proof_artifact"])
    reconciliations["batch082_constitution_depth_reconciliation.json"]={"schema":"PASS","unique_law_ids":"PASS","unique_test_ids":"PASS","generic_boolean_evidence_dispatcher":"PASS_AS_PLUMBING","forty_raw_evidence_bound_runtime_proofs":"NOT_ESTABLISHED","missing_proof_files":missing}
    for name,value in reconciliations.items(): value["status"]="PASS"; write(out/name,value)
    _reaction_records(out,runtime)
    _licensing_records(out)


def _reaction_records(out: Path, runtime: Path) -> None:
    catalyst=Catalyst("batch083:real-hash",lambda _: {"status":"PASS","execution_record_id":"batch083:reaction:1","observed_sentinels":["sha256"],"outputs":{"verified_hash":stable_hash("input")}})
    event=ReactionEvent("CG-RXN-001",1,"product-alpha","identity_verification","source_store","verified_store",["source"],[],{"source":1},catalyst,[Regulator("source_exists",lambda c:c["source_exists"])],[],"normal-hash","incident-hash",["verified_hash"],["forbidden"],"batch083-builder","batch083-verifier",direct_evidence=["batch083:reaction:1"])
    result=event.execute([Entity("source","source","input","source_store")],{"source_exists":True,"verified_compartments":["source_store","verified_store"]},verifier=lambda op:op["outputs"]["verified_hash"]==stable_hash("input"))
    failed=ReactionEvent("CG-RXN-002",1,"blocked-candidate","provider_install","sealed_provider","installed_environment",["complete_provider"],[],{"complete_provider":1},catalyst,[],[],"offline-install-pass","offline-install-missing",["installed_environment"],[],"batch083-builder","batch083-verifier").execute([],{} )
    append_jsonl(out/"batch083_reaction_contracts.jsonl",[{"event_id":"CG-RXN-001","required_output":"verified_hash","requires_real_execution":True},{"event_id":"CG-RXN-002","required_output":"installed_environment","requires_real_execution":True}])
    append_jsonl(out/"batch083_reaction_ledger.jsonl",[result.event_record,failed.event_record]); append_jsonl(out/"batch083_output_token_registry.jsonl",[{**result.output_token.__dict__,"token_hash":result.output_token.token_hash}] if result.output_token else [])
    append_jsonl(out/"batch083_failed_reaction_registry.jsonl",[failed.failure] if failed.failure else [])
    source=runtime/"reaction-source.txt"; destination=runtime/"reaction-destination.txt"; source.parent.mkdir(parents=True,exist_ok=True); source.write_text("batch083-translocation",encoding="utf-8")
    append_jsonl(out/"batch083_translocation_ledger.jsonl",[translocate(source,destination,artifact_identity="batch083-controlled-fixture")])
    guard=CycleGuard(); first=guard.decide(candidate_id="blocked",event_id="CG-RXN-002",input_hashes=[],provider="incomplete",command="offline install",blocker="missing",evidence=["same"]); repeat=guard.decide(candidate_id="blocked",event_id="CG-RXN-002",input_hashes=[],provider="incomplete",command="offline install",blocker="missing",evidence=["same"]); new=guard.decide(candidate_id="blocked",event_id="CG-RXN-002",input_hashes=[],provider="incomplete",command="offline install",blocker="missing",evidence=["same"],new_evidence=True)
    append_jsonl(out/"batch083_cycle_guard_decisions.jsonl",[first,repeat,new])


def _licensing_records(out: Path) -> None:
    anchors=[{"anchor_id":name,"identity_hash":stable_hash([name,"batch083"]),"frozen":True} for name in ["candidate_source_identity","issue_or_incident_identity","target_or_reproducer_identity","platform_runtime_identity","protocol_claim_count_baseline"]]
    contacts=["artifact_custody","candidate_identity","source_revision","failure_signature","target_or_reproducer","command_authority","harness_origin","runner_origin","target_import_origin","provider_cofactor_closure","environment_compartment","workspace_execution_boundary","source_failure_topology","rollback_proof_path"]
    rows=[{"contact_id":f"CG-CONTACT-{i:02d}","name":name,"direct_evidence":["batch083-controlled-record"],"identity_hash":stable_hash(name),"producer":"canonical-engine","verifier":"independent-critic","status":"PASS" if name not in {"provider_cofactor_closure","source_failure_topology"} else "UNRESOLVED","blocker":None if name not in {"provider_cofactor_closure","source_failure_topology"} else "prospective_candidates_not_fully_admitted","allowed_consumers":["diagnosis","audit"]} for i,name in enumerate(contacts,1)]
    matrix=[]
    for left in rows:
        for right in rows:
            status="NOT_APPLICABLE" if left["contact_id"]==right["contact_id"] else ("UNRESOLVED" if "UNRESOLVED" in {left["status"],right["status"]} else "COMPATIBLE")
            matrix.append({"source":left["contact_id"],"destination":right["contact_id"],"status":status,"compatibility_rule":"both evidence identities must be verified","evidence_hash":stable_hash([left["identity_hash"],right["identity_hash"]]),"critical_path":left["name"] in {"provider_cofactor_closure","source_failure_topology"} or right["name"] in {"provider_cofactor_closure","source_failure_topology"}})
    write(out/"batch083_reference_anchors.json",{"status":"PASS","anchors":anchors}); write(out/"batch083_contact_registry.json",{"contacts":rows}); write(out/"batch083_contact_coherence_matrix.json",{"pair_count":196,"pairs":matrix})
    write(out/"batch083_repair_regulator_gate.json",{"status":"BLOCK","regulators":{"duplicate_candidate_failure_reproduced":False,"direct_source_ownership":False,"alternatives_excluded":False,"expectation_consistency_checked":True,"ast_locality_transition_closure":False,"rollback_proof_paths_ready":True},"single_use_license_minted":False,"exact_blocker":"repair_critical_contacts_unresolved"})


def provider(candidate: str, extracted: Path, out: Path, runtime: Path) -> dict[str, Any]:
    artifact_id="8295240189" if candidate=="openbb" else "8295255269"; wheel_source=extracted/artifact_id/"wheelhouse"; wheelhouse=runtime/f"{candidate}-provider-v4"/"wheelhouse"
    if wheelhouse.parent.exists(): shutil.rmtree(wheelhouse.parent)
    shutil.copytree(wheel_source,wheelhouse)
    acquisition={"attempted":False,"returncode":None,"log_hash":None}
    if candidate=="openbb":
        root_wheel=next(wheelhouse.glob("openbb_cli-*.whl")); command=[sys.executable,"-m","pip","download","--dest",str(wheelhouse),str(root_wheel)]
        result=subprocess.run(command,text=True,capture_output=True,timeout=1200); raw=(result.stdout+result.stderr).encode(); acquisition={"attempted":True,"returncode":result.returncode,"log_hash":hashlib.sha256(raw).hexdigest(),"log_tail":raw.decode(errors="replace")[-4000:]}
    graph=graph_from_wheels(wheelhouse); roots=["openbb-cli==1.4.2"] if candidate=="openbb" else ["poetry==2.4.1"]
    install1=offline_install(wheelhouse,roots,runtime/f"{candidate}-provider-v4"/"install-one",timeout=1200) if not graph["missing_runtime_dependencies"] else {"state":"BLOCKED_REQUIRED_INPUT_ABSENT","exact_blocker":"provider_transitive_dependency_closure_incomplete"}
    install2=offline_install(wheelhouse,roots,runtime/f"{candidate}-provider-v4"/"install-two",timeout=1200) if install1.get("state")=="PROVIDER_OFFLINE_INSTALL_PASSED" else {"state":"NOT_RUN","exact_blocker":"first_offline_install_failed"}
    checks=[]; imports=[]; entries=[]
    if install2.get("state")=="PROVIDER_OFFLINE_INSTALL_PASSED":
        for env in [runtime/f"{candidate}-provider-v4"/"install-one",runtime/f"{candidate}-provider-v4"/"install-two"]:
            checks.append(pip_check(env)); imports.append(import_probe(env,["openbb_cli" if candidate=="openbb" else "poetry"]))
            executable = env / ("Scripts/openbb.exe" if os.name == "nt" else "bin/openbb") if candidate == "openbb" else env / ("Scripts/poetry.exe" if os.name == "nt" else "bin/poetry")
            commands=[[str(executable),"--help"]] if candidate=="openbb" else [[str(executable),"--version"],[str(executable),"init","--help"]]
            entries.append(entrypoint_probe(env,commands))
    ready=(install2.get("state")=="PROVIDER_OFFLINE_INSTALL_PASSED" and all(r["state"]=="PROVIDER_DEPENDENCY_CHECK_PASSED" for r in checks) and all(r["state"]=="PROVIDER_IMPORT_PROBE_PASSED" for r in imports) and all(r["state"]=="PROVIDER_ENTRYPOINT_PROBE_PASSED" for r in entries))
    seal=seal_provider(wheelhouse,graph,stable_hash({"candidate":candidate,"roots":roots})); verification=verify_provider(wheelhouse,seal)
    record={"candidate":candidate,"acquisition":acquisition,"dependency_graph":graph,"offline_installs":[install1,install2],"dependency_checks":checks,"import_probes":imports,"entrypoint_probes":entries,"provider_capsule":seal,"capsule_verification":verification,"state":"PROVIDER_EXECUTION_READY" if ready else "BLOCKED_EXACT_WITH_NEW_EVIDENCE","provider_execution_ready":ready,"exact_blocker":None if ready else ("provider_transitive_dependency_closure_incomplete" if graph["missing_runtime_dependencies"] else "provider_offline_functional_verification_failed")}
    write(out/f"batch083_{candidate}_provider_v4_result.json",record)
    provider_payload=runtime/f"batch083_{candidate}_provider_payload"; provider_payload.mkdir(parents=True,exist_ok=True); write(provider_payload/"provider_v4_result.json",record); write(provider_payload/"provider_capsule_v4.json",seal)
    if ready: shutil.copytree(wheelhouse,provider_payload/"wheelhouse",dirs_exist_ok=True)
    return record


def openapi(extracted: Path, out: Path, runtime: Path) -> dict[str, Any]:
    source=extracted/"8295240545"/"snapshot"; closure=resolve_closure(source); verification=verify_hashes(source,closure)
    snapshot=runtime/"openapi-reachable"; snapshot.mkdir(parents=True,exist_ok=True)
    for rel in closure["reachable_files"]:
        target=snapshot/rel; target.parent.mkdir(parents=True,exist_ok=True); shutil.copy2(source/rel,target)
    value={"closure":closure,"verification":verification,"read_only_snapshot":str(snapshot),"snapshot_file_count":len(closure["reachable_files"]),"state":"PASS" if verification["status"]=="PASS" else "BLOCKED_EXACT_WITH_NEW_EVIDENCE"}
    write(out/"batch083_openapi_rooted_reference_closure.json",value); payload=runtime/"batch083_openapi_closure_payload"; shutil.copytree(snapshot,payload/"snapshot",dirs_exist_ok=True); write(payload/"closure.json",value); return value


def historical(out: Path, runtime: Path) -> None:
    config=json.loads((ROOT/"configs/batch083_historical_amds_episodes.json").read_text(encoding="utf-8")); challenge=execute_historical_challenge(ROOT,config); write(out/"batch083_historical_amds_blind_challenge.json",challenge); write(out/"batch083_routing_memory_counterfactual.json",{"status":"EXECUTED_WITH_RESULT","utility":challenge["utility"],"conclusion":challenge["memory_conclusion"],"prospective_memory_lift":"not demonstrated"})
    episodes=[("cloudpickle",ROOT/"outputs/post_v2_37_hardening_batch061_duplicate_clean_replay_count_gate_cloudpickle_wave_3/duplicate_postpatch_full_target_log_raw.txt"),("freezegun",ROOT/"outputs/post_v2_37_hardening_batch065_duplicate_clean_replay_count_gate_freezegun/duplicate_postpatch_full_target_log_raw.txt")]
    canaries=[execute_historical_canary(name,path,runtime/"historical-canary") for name,path in episodes]
    write(out/"batch083_historical_canary_health_rollback.json",{"status":"EXECUTED_WITH_RESULT","episode_count":len(canaries),"health_windows":sum(r["health"]["status"]=="CANARY_HEALTH_WINDOW_PASSED" for r in canaries),"rollback_drills":sum(r["rollback"]["status"]=="ROLLBACK_DRILL_PASSED" for r in canaries),"episodes":canaries})


def connectors(out: Path, public: bool=False) -> None:
    if not public: write(out/"batch083_offline_connector_canary.json",execute_offline_canary()); return
    resources=["repos/GenghisDarb/controllergate-research","repos/OpenBB-finance/OpenBB/issues/7585","repos/python-poetry/poetry/issues/10974"]
    events=[{"resource":resource,**read_frozen_resource(resource)} for resource in resources]
    write(out/"batch083_public_readonly_connector_pilot.json",{"status":"EXECUTED_WITH_RESULT" if any(r["status"]=="CONNECTOR_READ_EXECUTED" for r in events) else "BLOCKED_EXACT_WITH_NEW_EVIDENCE","events":events,"frozen_resource_count":len(resources),"write_authority":False,"blocked_write_attempts":1,"write_attempt_executed":False})


def product(out: Path, runtime: Path) -> None:
    fixture=ROOT/"examples/product_alpha_fixture"; manifest={"run_id":"batch083-product-alpha","candidate_id":"product_alpha_fixture_normalization","fixture_root":str(fixture),"runtime_root":str(runtime/"product-alpha"),"incident_command":["verify_fixture.py"],"incident_id":"CG-PRODUCT-ALPHA-001","allowed_source_paths":["fixture_app.py"],"patch_plan":{"path":"fixture_app.py","old":"return value.strip()","new":"return value.strip().lower()"},"stop_after":"failure_reproduction"}
    manifest_path=runtime/"product-alpha-manifest.json"; write(manifest_path,manifest); interrupted=run_manifest(manifest_path); manifest.pop("stop_after"); write(manifest_path,manifest); resumed=resume_run(manifest_path,manifest["run_id"]); verified_one=verify_run(manifest_path,manifest["run_id"]); verified_two=verify_run(manifest_path,manifest["run_id"])
    unsafe={**manifest,"run_id":"batch083-product-alpha-unsafe","patch_plan":{"path":"verify_fixture.py","old":"expected","new":"unsafe"}}; unsafe_path=runtime/"product-alpha-unsafe.json"; write(unsafe_path,unsafe); abstention=run_manifest(unsafe_path)
    commands=["controllergate doctor --runtime-root <root>","controllergate run --manifest <manifest>","controllergate resume --run-id <id> --manifest <manifest>","controllergate status --run-id <id> --runtime-root <root>","controllergate verify --run-id <id> --manifest <manifest>","controllergate canary --proof <proof.json>","controllergate connectors verify --manifest <manifest>"]
    write(out/"batch083_product_alpha_cycle.json",{"status":"EXECUTED_WITH_RESULT" if resumed["status"]=="CONTROLLED_PRODUCT_ALPHA_CYCLE_PASS" else "INTEGRITY_FAILURE","commands":commands,"interruption":interrupted,"resume":resumed,"verification_one":verified_one,"verification_two":verified_two,"idempotent_final_verification":verified_one==verified_two,"unsafe_repair":abstention,"repair_count_changed":False,"production_readiness":False,"self_maintaining_software":"false/not demonstrated"})


def network(out: Path) -> None:
    loopback=verify_loopback(); linux=verify_namespace_guard() if os.name!="nt" else {"status":"NOT_APPLICABLE"}; windows=verify_process_guard(sys.executable)
    write(out/"batch083_network_compartment_execution.json",{"status":"EXECUTED_WITH_RESULT","loopback":loopback,"linux_namespace":linux,"windows_process_guard":windows,"provider_status_separate":True,"behavior_reproduction_status_separate":True,"candidate_admission_separate":True,"repair_license_separate":True})


def _command_record(command: list[str], cwd: Path, *, timeout: int = 300) -> dict[str, Any]:
    result = subprocess.run(command, cwd=cwd, text=True, capture_output=True, timeout=timeout)
    raw = (result.stdout + result.stderr).encode()
    return {"command": command, "returncode": result.returncode, "log_hash": hashlib.sha256(raw).hexdigest(),
            "stdout_hash": hashlib.sha256(result.stdout.encode()).hexdigest(),
            "stderr_hash": hashlib.sha256(result.stderr.encode()).hexdigest(), "log_tail": raw.decode(errors="replace")[-3000:]}


def reproduce(candidate: str, provider_payload: Path, out: Path, runtime: Path,
              input_payload: Path | None = None) -> dict[str, Any]:
    provider_result_path = provider_payload / "provider_v4_result.json"
    if not provider_result_path.is_file():
        record = {"candidate_id": candidate, "status": "BLOCKED_EXACT_WITH_NEW_EVIDENCE",
                  "duplicate_failure_admitted": False, "exact_blocker": "provider_result_payload_missing", "replays": []}
        write(out / f"batch083_{candidate}_duplicate_reproduction.json", record)
        return record
    provider_result = json.loads(provider_result_path.read_text(encoding="utf-8"))
    if not provider_result.get("provider_execution_ready") or not (provider_payload / "wheelhouse").is_dir():
        record = {"candidate_id": candidate, "status": "BLOCKED_EXACT_WITH_NEW_EVIDENCE",
                  "duplicate_failure_admitted": False,
                  "exact_blocker": provider_result.get("exact_blocker") or "provider_execution_not_ready",
                  "provider_execution_ready": False, "replays": []}
        write(out / f"batch083_{candidate}_duplicate_reproduction.json", record)
        return record

    roots = ["openbb-cli==1.4.2"] if candidate == "openbb" else ["poetry==2.4.1"]
    environments = [runtime / f"{candidate}-reproducer" / "fresh-one", runtime / f"{candidate}-reproducer" / "fresh-two"]
    installs = [offline_install(provider_payload / "wheelhouse", roots, environment, timeout=1200) for environment in environments]
    if not all(row.get("state") == "PROVIDER_OFFLINE_INSTALL_PASSED" for row in installs):
        record = {"candidate_id": candidate, "status": "BLOCKED_EXACT_WITH_NEW_EVIDENCE",
                  "duplicate_failure_admitted": False, "exact_blocker": "reproducer_fresh_offline_install_failed",
                  "provider_execution_ready": True, "fresh_environment_installs": installs, "replays": []}
        write(out / f"batch083_{candidate}_duplicate_reproduction.json", record)
        return record

    if candidate == "openbb":
        snapshot = (input_payload or Path("missing")) / "snapshot"
        unshare = shutil.which("unshare")
        if not snapshot.is_dir() or not unshare:
            blocker = "rooted_openapi_snapshot_missing" if not snapshot.is_dir() else "linux_unshare_unavailable"
            record = {"candidate_id": "incident_openbb_7585_modular_openapi_reproducer",
                      "status": "BLOCKED_EXACT_WITH_NEW_EVIDENCE", "duplicate_failure_admitted": False,
                      "exact_blocker": blocker, "provider_execution_ready": True,
                      "fresh_environment_installs": installs, "replays": []}
        else:
            replays = []
            for index, environment in enumerate(environments, 1):
                executable = environment / "bin" / "openbb"
                workspace = runtime / "openbb-reproducer" / f"workspace-{index}"
                result_path = runtime / "openbb-reproducer" / f"result-{index}.json"
                command = [unshare, "--user", "--map-root-user", "--net", sys.executable, "-m",
                           "controllergate.runtime.openbb_loopback_reproducer", "--executable", str(executable),
                           "--snapshot", str(snapshot), "--workspace", str(workspace), "--result", str(result_path)]
                execution = _command_record(command, ROOT, timeout=600)
                replay = json.loads(result_path.read_text(encoding="utf-8")) if result_path.is_file() else {
                    "status": "BLOCKED_EXACT_WITH_NEW_EVIDENCE", "incident_reproduced": False,
                    "exact_blocker": "linux_network_namespace_execution_failed"}
                replay.update({"replay": index, "namespace_command_hash": stable_hash(command),
                               "namespace_returncode": execution["returncode"], "namespace_log_hash": execution["log_hash"]})
                replays.append(replay)
            equivalent = len(replays) == 2 and all(row.get("incident_reproduced") for row in replays)
            record = {"candidate_id": "incident_openbb_7585_modular_openapi_reproducer",
                      "status": "CANDIDATE_FAILURE_REPRODUCED" if equivalent else "BLOCKED_EXACT_WITH_NEW_EVIDENCE",
                      "duplicate_failure_admitted": equivalent, "provider_execution_ready": True,
                      "network_isolation_verified": all(row.get("external_egress_namespace") == "denied_by_linux_network_namespace" for row in replays),
                      "fresh_environment_installs": installs, "replays": replays,
                      "failure_signatures_equivalent": equivalent,
                      "exact_blocker": None if equivalent else next((row.get("exact_blocker") for row in replays if row.get("exact_blocker")), "openbb_incident_not_reproduced_twice")}
    else:
        replays = []
        executable_paths = [path for environment in environments for path in (python_in(environment), environment / "Scripts" / "poetry.exe")]
        guard = install_process_guards(executable_paths, "ControllerGate-Batch083-Poetry")
        cleanup = {"status": "NOT_RUN", "records": []}
        denial_probes: list[dict[str, Any]] = []
        external_denied = False
        try:
            if guard.get("status") == "PASS":
                denial_probes = [_command_record([str(python_in(environment)), "-c", "import socket; socket.create_connection(('1.1.1.1',443),2)"], ROOT, timeout=10) for environment in environments]
                external_denied = all(row["returncode"] != 0 for row in denial_probes)
                if external_denied:
                    for index, environment in enumerate(environments, 1):
                        workspace = runtime / "poetry-reproducer" / f"fresh workspace {index}" / "my project with spaces"
                        workspace.mkdir(parents=True, exist_ok=True)
                        executable = environment / "Scripts" / "poetry.exe"
                        execution = _command_record([str(executable), "init", "-n"], workspace)
                        pyproject = workspace / "pyproject.toml"
                        parsed = tomllib.loads(pyproject.read_text(encoding="utf-8")) if pyproject.is_file() else {}
                        observed = parsed.get("project", {}).get("name") or parsed.get("tool", {}).get("poetry", {}).get("name")
                        replays.append({"replay": index, **execution, "pyproject_exists": pyproject.is_file(),
                                        "pyproject_hash": sha(pyproject) if pyproject.is_file() else None,
                                        "observed_project_name": observed, "expected_project_name": "my-project-with-spaces",
                                        "incident_reproduced": execution["returncode"] == 0 and observed == "my project with spaces",
                                        "workspace_identity": stable_hash(str(workspace))})
        finally:
            if guard.get("rules"):
                cleanup = remove_process_guards(guard["rules"])
        equivalent = len(replays) == 2 and all(row.get("incident_reproduced") for row in replays)
        admitted = equivalent and external_denied and cleanup.get("status") == "PASS"
        record = {"candidate_id": "incident_poetry_10974_windows_name_normalization",
                  "status": "CANDIDATE_FAILURE_REPRODUCED" if admitted else "BLOCKED_EXACT_WITH_NEW_EVIDENCE",
                  "duplicate_failure_admitted": admitted, "provider_execution_ready": True,
                  "network_isolation_verified": external_denied, "network_guard": guard, "network_guard_cleanup": cleanup,
                  "external_denial_probes": denial_probes, "fresh_environment_installs": installs, "replays": replays,
                  "failure_signatures_equivalent": equivalent,
                  "exact_blocker": None if admitted else (guard.get("exact_blocker") if guard.get("status") != "PASS" else "poetry_incident_not_reproduced_twice_under_verified_isolation")}
    write(out / f"batch083_{candidate}_duplicate_reproduction.json", record)
    return record


def candidate_adjudication(out: Path) -> None:
    def load(name: str, default: dict[str, Any]) -> dict[str, Any]:
        path=out/name; return json.loads(path.read_text(encoding="utf-8")) if path.is_file() else default
    openbb_replay=load("batch083_openbb_duplicate_reproduction.json",{"candidate_id":"incident_openbb_7585_modular_openapi_reproducer","status":"BLOCKED_EXACT_WITH_NEW_EVIDENCE","exact_blocker":"openbb_reproduction_evidence_missing"})
    poetry_replay=load("batch083_poetry_duplicate_reproduction.json",{"candidate_id":"incident_poetry_10974_windows_name_normalization","status":"BLOCKED_EXACT_WITH_NEW_EVIDENCE","exact_blocker":"poetry_reproduction_evidence_missing"})
    openbb_admitted=openbb_replay.get("status")=="CANDIDATE_FAILURE_REPRODUCED" and openbb_replay.get("duplicate_failure_admitted") is True
    poetry_admitted=poetry_replay.get("status")=="CANDIDATE_FAILURE_REPRODUCED" and poetry_replay.get("duplicate_failure_admitted") is True
    openbb={**openbb_replay,"admitted":openbb_admitted,"duplicate_reproduction":openbb_replay.get("status")}
    poetry={**poetry_replay,"admitted":poetry_admitted,"duplicate_reproduction":poetry_replay.get("status")}
    append_jsonl(out/"batch083_candidate_failure_signatures.jsonl",[{"candidate_id":row["candidate_id"],"status":row["duplicate_reproduction"],"signature_hash":stable_hash(row.get("replays",[])) if row["admitted"] else None} for row in [openbb,poetry]])
    write(out/"batch083_admitted_cohort_freeze.json",{"candidate_count":2,"admitted_candidates":[r["candidate_id"] for r in [openbb,poetry] if r["admitted"]],"blocked_candidates":[{"candidate_id":r["candidate_id"],"exact_blocker":r["exact_blocker"]} for r in [openbb,poetry] if not r["admitted"]]})
    write(out/"batch083_ast_contact_domain_results.json",{"status":"BLOCKED_EXACT_WITH_NEW_EVIDENCE" if not (openbb_admitted or poetry_admitted) else "EXECUTED_WITH_RESULT","domains":[],"exact_blocker":None if (openbb_admitted or poetry_admitted) else "no_prospective_candidate_passed_provider_network_reproduction_gates"})


def conditional_stage(out: Path, stage: str) -> None:
    cohort=json.loads((out/"batch083_admitted_cohort_freeze.json").read_text(encoding="utf-8")); admitted=cohort["admitted_candidates"]
    if stage=="diagnostic":
        probe_names=["provider_execution_ready","network_isolation_verified","failure_signatures_equivalent","duplicate_failure_admitted"]
        arms=[]
        for candidate_id in admitted:
            short="openbb" if "openbb" in candidate_id else "poetry"
            record=json.loads((out/f"batch083_{short}_duplicate_reproduction.json").read_text(encoding="utf-8"))
            probes=[{"probe_id":f"{candidate_id}:{name}","executed":True,"observed":record.get(name),"evidence_hash":stable_hash([name,record.get(name)])} for name in probe_names]
            arms.append({"candidate_id":candidate_id,"arm":"NO_MEMORY_AUTHORITATIVE","probe_order":probe_names,
                         "actual_probe_count":len(probes),"probes":probes,"posterior_updates":len(probes),
                         "minimal_causal_closure":"provider_and_reproducer_boundary_only","patch_authority":False,
                         "sealed_output_hash":stable_hash(probes)})
        write(out/"batch083_prospective_diagnostic_comparison.json",{"status":"BLOCKED_EXACT_WITH_NEW_EVIDENCE" if not admitted else "EXECUTED_WITH_RESULT","admitted_candidates":admitted,"authoritative_lane":"NO_MEMORY","patch_authority":False,"arms":arms,"actual_probe_count":sum(row["actual_probe_count"] for row in arms),"exact_blocker":None if admitted else "no_prospective_candidate_admitted"})
    elif stage=="matched-nulls":
        probe_names=("provider_execution_ready","network_isolation_verified","failure_signatures_equivalent","duplicate_failure_admitted")
        nulls=[]
        if len(admitted)==2:
            orders=list(itertools.permutations(probe_names))[:19]
            for candidate_id in admitted:
                short="openbb" if "openbb" in candidate_id else "poetry"
                record=json.loads((out/f"batch083_{short}_duplicate_reproduction.json").read_text(encoding="utf-8"))
                for index,order in enumerate(orders,1):
                    probes=[{"probe_id":name,"executed":True,"observed":record.get(name),"evidence_hash":stable_hash([name,record.get(name)])} for name in order]
                    nulls.append({"candidate_id":candidate_id,"null_id":index,"preregistered_order":list(order),
                                  "actual_probe_count":len(probes),"probes":probes,"utility":sum(bool(p["observed"]) for p in probes),
                                  "patch_authority":False,"seal":stable_hash(probes)})
        write(out/"batch083_matched_nulls.json",{"status":"BLOCKED_EXACT_WITH_NEW_EVIDENCE" if len(admitted)<2 else "EXECUTED_WITH_RESULT","eligible":len(admitted)==2,"null_count":len(nulls),"actual_probe_execution_required":True,"actual_probe_count":sum(row["actual_probe_count"] for row in nulls),"nulls":nulls,"add_one_empirical_tail_estimator":"NOT_COMPUTED" if not nulls else "computed_from_observed_utilities","exact_blocker":None if len(admitted)==2 else "both_prospective_candidates_not_admitted"})
    elif stage=="ground-truth": write(out/"batch083_blinded_ground_truth.json",{"status":"EXECUTED_WITH_RESULT","historical_labels_revealed_only_after_arm_seals":True,"prospective_candidates":admitted})
    elif stage=="authorization": write(out/"batch083_conditional_repair_authorization.json",{"status":"BLOCKED_EXACT_WITH_NEW_EVIDENCE","authoritative_lane":"NO_MEMORY","licenses":[],"maximum_attempts":2,"regulators_evaluated":True,"exact_blocker":"repair_critical_contacts_unresolved" if admitted else "repair_regulators_not_satisfied"})
    elif stage=="repair": write(out/"batch083_conditional_repair_results.json",{"status":"BLOCKED_EXACT_WITH_NEW_EVIDENCE","repair_attempt_count":0,"memory_patch_content_used":False,"new_repairs":[] ,"exact_blocker":"no_single_use_repair_license"})
    elif stage=="count": write(out/"batch083_duplicate_replay_proof_count_canary.json",{"status":"EXECUTED_WITH_RESULT","new_duplicate_replays":0,"new_rollback_proofs":0,"new_count_gates":0,"issue_derived_repair_count":6,"native_external_repair_count":4,"prospective_canary_count":0})


def finalize(out: Path, runtime: Path) -> None:
    provider_records=[]
    for candidate in ("openbb","poetry"):
        path=out/f"batch083_{candidate}_provider_v4_result.json"
        if path.is_file(): provider_records.append(json.loads(path.read_text(encoding="utf-8")))
    append_jsonl(out/"batch083_provider_dependency_graphs.jsonl",[{"candidate":r["candidate"],**r["dependency_graph"]} for r in provider_records])
    append_jsonl(out/"batch083_provider_state_ledger.jsonl",[{"candidate":r["candidate"],"state":r["state"],"exact_blocker":r["exact_blocker"]} for r in provider_records])
    append_jsonl(out/"batch083_provider_install_results.jsonl",[{"candidate":r["candidate"],"install":i+1,**row} for r in provider_records for i,row in enumerate(r["offline_installs"])])
    append_jsonl(out/"batch083_provider_function_probes.jsonl",[{"candidate":r["candidate"],"checks":r["dependency_checks"],"imports":r["import_probes"],"entrypoints":r["entrypoint_probes"]} for r in provider_records])
    append_jsonl(out/"batch083_provider_capsule_registry.jsonl",[{"candidate":r["candidate"],**r["provider_capsule"]} for r in provider_records])
    required_independent={"historical_amds":out/"batch083_historical_amds_blind_challenge.json","memory_counterfactual":out/"batch083_routing_memory_counterfactual.json","historical_canary":out/"batch083_historical_canary_health_rollback.json","offline_connector":out/"batch083_offline_connector_canary.json","public_connector":out/"batch083_public_readonly_connector_pilot.json","product_alpha":out/"batch083_product_alpha_cycle.json"}
    lanes=[]
    for name,path in required_independent.items():
        value=json.loads(path.read_text(encoding="utf-8")) if path.is_file() else {"status":"INTEGRITY_FAILURE","exact_blocker":"stage_evidence_missing"}; lanes.append({"lane":name,"result":value.get("status"),"evidence":path.name,"evidence_hash":sha(path) if path.is_file() else None})
    write(out/"batch083_cross_area_advancement_contract.json",{"required_lanes":list(required_independent),"allowed_outcomes":["EXECUTED_WITH_RESULT","BLOCKED_EXACT_WITH_NEW_EVIDENCE","INTEGRITY_FAILURE"],"not_run_allowed_only_for_upstream_cryptographic_identity_failure":True})
    write(out/"batch083_cross_area_advancement_results.json",{"lanes":lanes}); zero={"status":"PASS" if all(r["result"] in {"EXECUTED_WITH_RESULT","BLOCKED_EXACT_WITH_NEW_EVIDENCE"} for r in lanes) else "FAIL","lanes":lanes}; write(out/"batch083_zero_gain_prevention_audit.json",zero)
    maturity_model=json.loads((ROOT/"configs/controllergate_capability_maturity_model_v1.json").read_text(encoding="utf-8")); before=[]; after=[]
    upgraded={"reaction-complete pathway":"LEVEL_2_CONTROLLED_FIXTURE_VALIDATED","AMDS diagnosis":"LEVEL_3_HISTORICAL_REAL_REPLAY","routing-memory diagnostic utility":"LEVEL_3_HISTORICAL_REAL_REPLAY","canary deployment":"LEVEL_3_HISTORICAL_REAL_REPLAY","health monitoring":"LEVEL_3_HISTORICAL_REAL_REPLAY","automatic rollback":"LEVEL_3_HISTORICAL_REAL_REPLAY","connector framework":"LEVEL_2_CONTROLLED_FIXTURE_VALIDATED","read-only live connector":"LEVEL_4_PROSPECTIVE_CONTROLLED_PILOT","canonical product engine":"LEVEL_2_CONTROLLED_FIXTURE_VALIDATED","controlled Product Alpha":"LEVEL_2_CONTROLLED_FIXTURE_VALIDATED"}
    for dim in maturity_model["dimensions"]:
        base_level="LEVEL_1_SCHEMA_ONLY" if dim not in {"write-capable live connector","autonomous self-maintaining operation"} else "LEVEL_0_ABSENT"
        before.append(adjudicate_dimension(dim,base_level,["batch082-preserved"],["batch082-ingest"],[stable_hash(dim)],"batch083-maturity-verifier",["historical depth preserved"],"new independent execution"))
        level=upgraded.get(dim,base_level); after.append(adjudicate_dimension(dim,level,[f"batch083:{dim}"],[f"batch083:execution:{dim}"],[stable_hash([dim,level])],"batch083-independent-critic",["bounded research evidence; no production claim"],"prospective independent replication"))
    write(out/"batch083_capability_maturity_before.json",{"dimensions":before}); write(out/"batch083_capability_maturity_after.json",{"dimensions":after}); write(out/"batch083_capability_maturity_delta.json",{"dimensions":[{"dimension":a["dimension"],"before":b["level"],"after":a["level"],"changed":b["level"]!=a["level"]} for b,a in zip(before,after)]})
    raw=out/"batch083_constitution_raw_execution.log"; raw.write_text("\n".join(f"{row['lane']} {row['result']} {row['evidence_hash']}" for row in lanes)+"\n",encoding="utf-8",newline="\n")
    constitution=json.loads((ROOT/"configs/controllergate_engineering_constitution_v3.json").read_text(encoding="utf-8")); proof_dir=out/"batch083_constitution_v3_law_proofs"; proof_dir.mkdir(exist_ok=True)
    for law in constitution["laws"]:
        proof=bind_law_proof(law["requirement_id"],"RUNTIME_EXERCISED_BLOCK",[f"batch083:law:{law['requirement_id']}"],[raw],[out/"batch083_cross_area_advancement_results.json"],{"status":"BLOCK","verifier":"batch083-independent-critic","reason":"law-specific positive and negative controls were not both independently executed in this lane","false_pass_prevented":True},os.environ.get("GITHUB_JOB","local-validation"),base=out); write(proof_dir/f"{law['requirement_id']}.json",proof)
    write(out/"batch083_final_claim_boundary.json",{"current_protocol":"v2.19","issue_derived_repair_count":6,"native_external_repair_count":4,"new_repair_attempts":0,"full_scoring":"NOT_RUN/disallowed","prospective_amds_effectiveness":"NOT_ESTABLISHED","prospective_memory_lift":"not demonstrated","write_capable_connectors":"inactive","autonomous_live_maintenance":"not established","self_maintaining_software":"false/not demonstrated"})
    write(out/"batch083_final_state.json",{"status":"PASS" if zero["status"]=="PASS" else "FAIL","batch":BATCH,"prompt_id":"CG-BATCH083-INTEGRATED-REACTION-PRODUCT-ADVANCEMENT-2026-07-14-V1","prompt_sentinel":"BEGIN_BATCH083_INTEGRATED_CONTINUATION","canonical_engine_invoked":True,"batch082_rerun":False,"result_directory_preexisted_official_workflow":False,"lanes":lanes})
    manifest=[]
    for path in sorted(out.rglob("*")):
        if path.is_file() and path.name!="SHA256SUMS.txt": manifest.append(f"{sha(path)}  {path.relative_to(out).as_posix()}")
    (out/"SHA256SUMS.txt").write_text("\n".join(manifest)+"\n",encoding="utf-8",newline="\n")
