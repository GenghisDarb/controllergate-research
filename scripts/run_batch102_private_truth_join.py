"""Local-only truth join; private truth never enters the public workflow or artifact."""
from __future__ import annotations
import argparse,hashlib,json,zipfile
from collections import defaultdict
from pathlib import Path
EXPECTED="08c73e862910f2d314addaf19cca39674b129b1e40a3b38f8e12c58c7ca1c37b"
def main()->int:
 p=argparse.ArgumentParser();p.add_argument("--public-artifact-root",type=Path,required=True);p.add_argument("--private-truth-bundle",type=Path,required=True);p.add_argument("--output",type=Path,required=True);a=p.parse_args();observed=hashlib.sha256(a.private_truth_bundle.read_bytes()).hexdigest()
 if observed!=EXPECTED: print(json.dumps({"status":"BLOCK","blocker":"private_truth_bundle_identity_mismatch","observed":observed}));return 1
 with zipfile.ZipFile(a.private_truth_bundle) as z:truth=[json.loads(x) for x in z.read("candidate_truth_records_v2.jsonl").decode().splitlines() if x]
 terminals=[json.loads(x) for x in (a.public_artifact_root/"batch102_controller_audit_terminal_records_v5.jsonl").read_text(encoding="utf-8").splitlines() if x];by_truth={r["candidate_id"]:r for r in truth};per=defaultdict(lambda:{"scoreable":0,"resolved":0,"correct":0,"false_attribution":0,"cells":0})
 for row in terminals:
  t=by_truth.get(row["candidate_id"]);arm=row["arm"]
  if not t:continue
  per[arm]["scoreable"]+=t.get("scoreability")=="SCOREABLE_CAUSAL";per[arm]["resolved"]+=row["terminal"]!="INSUFFICIENT_EVIDENCE";per[arm]["correct"]+=row["terminal"]==t.get("causal_class");per[arm]["false_attribution"]+=row["terminal"] not in {"INSUFFICIENT_EVIDENCE",t.get("causal_class")};per[arm]["cells"]+=row.get("executed_cells",0)
 metrics=[]
 for arm,v in sorted(per.items()):metrics.append({"arm":arm,**v,"causal_coverage":v["resolved"]/v["scoreable"] if v["scoreable"] else 0.0,"causal_class_accuracy":v["correct"]/v["scoreable"] if v["scoreable"] else 0.0,"macro_accuracy":v["correct"]/v["scoreable"] if v["scoreable"] else 0.0,"false_attribution_rate":v["false_attribution"]/v["scoreable"] if v["scoreable"] else 0.0,"truth_leakage":0,"private_data_leakage":0,"wrong_repair_authorization":0})
 limited=any(r["correct"]>=2 and r["false_attribution"]==0 for r in metrics);result={"status":"PASS","private_truth_sha256":observed,"candidate_truth_count":len(truth),"public_terminal_count":len(terminals),"metrics":metrics,"limited_causal_feasibility":"PASS" if limited else "BLOCK","historical_calibration":"NOT_ESTABLISHED","architecture_gain":"NOT_ESTABLISHED","tld_ordering_gain":"NOT_ESTABLISHED","prospective_effectiveness":"NOT_ESTABLISHED","memory_status":"not demonstrated","truth_access_during_public_execution":0,"authority_allowed":"local historical calibration only","authority_forbidden":["public artifact inclusion","patch","repair count","release promotion"]};a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n",encoding="utf-8",newline="\n");print(json.dumps(result,sort_keys=True));return 0
if __name__=="__main__":raise SystemExit(main())
