from __future__ import annotations
import argparse,datetime,hashlib,json
from pathlib import Path
def main()->int:
 p=argparse.ArgumentParser(); p.add_argument("--candidate-id",required=True); p.add_argument("--repository",required=True); p.add_argument("--issue-url",required=True); p.add_argument("--source-commit",required=True); p.add_argument("--output",type=Path,required=True); a=p.parse_args(); row={"candidate_id":a.candidate_id,"repository":a.repository,"issue_url":a.issue_url,"source_commit":a.source_commit,"frozen_at":datetime.datetime.now(datetime.timezone.utc).isoformat(),"diagnosis_performed":False,"future_fix_access":False,"patch_access":False,"authority_allowed":"prospective identity freeze","authority_forbidden":["diagnosis","patch","repair count","release"]}; row["freeze_hash"]=hashlib.sha256(json.dumps(row,sort_keys=True,separators=(",",":")).encode()).hexdigest(); a.output.parent.mkdir(parents=True,exist_ok=True); a.output.write_text(json.dumps(row,indent=2,sort_keys=True)+"\n",encoding="utf-8",newline="\n"); return 0
if __name__=="__main__": raise SystemExit(main())
