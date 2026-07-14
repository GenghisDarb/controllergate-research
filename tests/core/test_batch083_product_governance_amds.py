from __future__ import annotations

import hashlib
import json
from pathlib import Path

from controllergate.amds.historical_challenge import execute_historical_challenge
from controllergate.engine import resume_run, run_manifest, verify_run
from controllergate.governance.capability_maturity import adjudicate_dimension
from controllergate.governance.raw_law_evidence import bind_law_proof, verify_law_proof


def fixture(tmp_path: Path) -> tuple[Path, dict[str, object]]:
    source=tmp_path/"fixture";source.mkdir();(source/"app.py").write_text("def f(v):\n    return v.strip()\n",encoding="utf-8");(source/"verify.py").write_text("from app import f\nraise SystemExit(0 if f(' A ')== 'a' else 1)\n",encoding="utf-8")
    manifest={"run_id":"test-run","candidate_id":"fixture","fixture_root":str(source),"runtime_root":str(tmp_path/"runtime"),"incident_command":["verify.py"],"allowed_source_paths":["app.py"],"patch_plan":{"path":"app.py","old":"return v.strip()","new":"return v.strip().lower()"},"stop_after":"failure_reproduction"}
    path=tmp_path/"manifest.json";path.write_text(json.dumps(manifest),encoding="utf-8");return path,manifest


def test_product_alpha_interrupt_resume_and_verify(tmp_path: Path) -> None:
    path,manifest=fixture(tmp_path);interrupted=run_manifest(path);assert interrupted["status"]=="INTERRUPTED_AT_CHECKPOINT"
    manifest.pop("stop_after");path.write_text(json.dumps(manifest),encoding="utf-8");resumed=resume_run(path,"test-run")
    assert resumed["status"]=="CONTROLLED_PRODUCT_ALPHA_CYCLE_PASS"
    assert verify_run(path,"test-run")["status"]=="PASS" and verify_run(path,"test-run")["idempotent"]


def test_product_alpha_safe_abstention_on_harness_edit(tmp_path: Path) -> None:
    path,manifest=fixture(tmp_path);manifest.pop("stop_after");manifest["run_id"]="unsafe";manifest["patch_plan"]={"path":"verify.py","old":"raise","new":"print"};path.write_text(json.dumps(manifest),encoding="utf-8")
    result=run_manifest(path);assert result["status"]=="SAFE_ABSTENTION" and result["blocker"]=="unsafe_repair_blocked"


def test_raw_law_proof_requires_physical_hash_bound_files(tmp_path: Path) -> None:
    raw=tmp_path/"raw.log";out=tmp_path/"out.json";raw.write_text("executed",encoding="utf-8");out.write_text("{}",encoding="utf-8")
    proof=bind_law_proof("CG-LAW-001","CONTROLLED_FIXTURE_EXERCISED_PASS",["run:1"],[raw],[out],{"status":"PASS"},"job")
    assert verify_law_proof(proof,tmp_path)["status"]=="PASS";raw.write_text("changed",encoding="utf-8");assert verify_law_proof(proof,tmp_path)["status"]=="BLOCK"


def test_maturity_cannot_increase_without_execution_evidence() -> None:
    row=adjudicate_dimension("canary deployment","LEVEL_3_HISTORICAL_REAL_REPLAY",[],[],[],"",[],"execute")
    assert row["level"]=="LEVEL_0_ABSENT"


def test_historical_amds_executes_four_arms_and_hides_truth(tmp_path: Path) -> None:
    episodes=[]
    for i in range(8):
        path=tmp_path/f"e{i}.txt";path.write_text("traceback source assert",encoding="utf-8");episodes.append({"candidate_id":f"c{i}","repository":f"repo{i}","decision_time_files":[path.name],"terminal_class":"candidate_source"})
    result=execute_historical_challenge(tmp_path,{"episodes":episodes})
    assert result["episode_count"]==8 and result["repository_count"]==8 and result["actual_probe_count"]==32
    assert all(arm["sealed_before_truth"] and arm["patch_authority"] is False for ep in result["episodes"] for arm in ep["arms"])
