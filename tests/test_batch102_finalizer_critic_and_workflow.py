from __future__ import annotations
import hashlib,json,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def rows(path):return [json.loads(x) for x in path.read_text(encoding="utf-8").splitlines() if x]
def test_blocked_finalizer_accounts_every_registered_cell(tmp_path:Path)->None:
 evidence=tmp_path/"evidence";empty=tmp_path/"empty";empty.mkdir()
 subprocess.run([sys.executable,str(ROOT/"scripts/finalize_batch102_public_evidence.py"),"--cell-artifacts-root",str(empty),"--output-root",str(evidence),"--workflow-run-id","test-run","--workflow-head","1"*40],cwd=ROOT,check=True)
 state=json.loads((evidence/"batch102_consolidated_state.json").read_text())
 assert state["registered_cell_count"]==70 and state["fresh_executed_cell_count"]==0
 assert len(rows(evidence/"batch102_registered_cell_ledger_v4.jsonl"))==70
 assert all(r["status"].startswith("BLOCKED") for r in rows(evidence/"batch102_registered_cell_ledger_v4.jsonl"))
 assert json.loads((evidence/"batch102_claim_boundary.json").read_text())["ordinary_patch_count"]==0
def test_independent_critic_executes_and_rejects_at_least_75(tmp_path:Path)->None:
 evidence=tmp_path/"evidence";evidence.mkdir();(evidence/"batch102_claim_boundary.json").write_text("{}\n");(evidence/"batch102_consolidated_state.json").write_text("{}\n")
 subprocess.run([sys.executable,str(ROOT/"scripts/run_batch102_independent_critic.py"),"--evidence-root",str(evidence),"--output-root",str(evidence),"--runtime-root",str(tmp_path/"runtime")],cwd=ROOT,check=True)
 result=json.loads((evidence/"batch102_independent_critic_summary.json").read_text());assert result["mutations_executed"]==77==result["mutations_rejected"]
def test_batch102_workflow_has_real_matrix_and_windows_slice()->None:
 text=(ROOT/".github/workflows/post_v2_37_hardening_batch102_fresh_exact_counterfactual_execution_ownership_closure.yml").read_text()
 for name in ("darker_py37_linux","pybugger_exact_linux","cloudpickle_py311_linux","cloudpickle_issue_py312_linux","freezegun_py312_linux","freezegun_py313b1_linux","audioread_py312_linux","audioread_py313b2_linux","pytest_py3133_linux","openbb_py311_linux","poetry_linux_secondary","poetry_windows_py31314"):
  assert name in text
 assert "runs-on: windows-latest" in text and "retention-days: 30" in text
 assert "run_batch102_candidate_slice.py" in text and "finalize_batch102_public_evidence.py" in text
 assert "--write-source-manifests" in text and '--manifest "$BATCH102_OUT/SHA256SUMS.txt"' in text

def test_stage_manifests_have_correct_scope_and_no_self_entry(tmp_path:Path)->None:
 source=tmp_path/"source";destination=tmp_path/"artifact";source.mkdir()
 (source/"evidence.json").write_text('{"status":"PASS"}\n',encoding="utf-8",newline="\n")
 subprocess.run([sys.executable,str(ROOT/"scripts/stage_batch102_artifact.py"),"--source",str(source),"--destination",str(destination),"--write-source-manifests"],cwd=ROOT,check=True)
 artifact=(destination/"ARTIFACT_SHA256SUMS.txt").read_text().splitlines()
 portable=(destination/"PORTABLE_ARTIFACT_SHA256SUMS.txt").read_text().splitlines()
 complete=(destination/"SHA256SUMS.txt").read_text().splitlines()
 assert artifact==portable and len(artifact)==1 and len(complete)==3
 assert all("ARTIFACT_SHA256SUMS.txt  ARTIFACT_SHA256SUMS.txt" not in row for row in complete)
 assert not any(row.endswith("  SHA256SUMS.txt") for row in complete)
 for row in complete:
  digest,rel=row.split("  ",1);assert hashlib.sha256((destination/rel).read_bytes()).hexdigest()==digest
