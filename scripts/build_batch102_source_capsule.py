from __future__ import annotations

import argparse, json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0, str(ROOT))
from controllergate.evidence.source_capsule_v2 import build_source_capsule_v2


def main() -> int:
    p=argparse.ArgumentParser(); p.add_argument("--candidate-id",required=True); p.add_argument("--repository",required=True); p.add_argument("--repo",type=Path,required=True); p.add_argument("--commit",required=True); p.add_argument("--issue-cutoff",required=True); p.add_argument("--test-prefix",action="append",default=[]); p.add_argument("--operation-id",required=True); p.add_argument("--broker-record-hash",required=True); p.add_argument("--output",type=Path,required=True); p.add_argument("--tag")
    a=p.parse_args(); row=build_source_capsule_v2(candidate_id=a.candidate_id,repository=a.repository,exact_source_commit=a.commit,repo=a.repo,test_prefixes=a.test_prefix,issue_cutoff=a.issue_cutoff,acquisition_broker_receipt={"operation_id":a.operation_id,"record_hash":a.broker_record_hash},network_budget={"mode":"bounded_read_only","operations":1},tag=a.tag)
    a.output.parent.mkdir(parents=True,exist_ok=True); a.output.write_text(json.dumps(row,indent=2,sort_keys=True)+"\n",encoding="utf-8",newline="\n"); print(json.dumps({"status":"PASS","source_capsule_hash":row["source_capsule_hash"]},sort_keys=True)); return 0
if __name__=="__main__": raise SystemExit(main())
