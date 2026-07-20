from __future__ import annotations
import argparse,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0,str(ROOT))
from controllergate.evidence.provider_capsule_v4 import build_provider_capsule_v4,observed_provider_identity
def main()->int:
 p=argparse.ArgumentParser(); p.add_argument("--candidate-id",required=True); p.add_argument("--capsule-id",required=True); p.add_argument("--requested",type=Path,required=True); p.add_argument("--operation-id",required=True); p.add_argument("--runner-image",required=True); p.add_argument("--dependency-graph-hash",required=True); p.add_argument("--output",type=Path,required=True); p.add_argument("--unavailable",action="store_true"); a=p.parse_args(); requested=json.loads(a.requested.read_text(encoding="utf-8")); observed={} if a.unavailable else observed_provider_identity(); row=build_provider_capsule_v4(capsule_id=a.capsule_id,candidate_id=a.candidate_id,requested=requested,observed=observed,materialization_receipt={"operation_id":a.operation_id},runner_image=a.runner_image,dependency_graph_hash=a.dependency_graph_hash,wheel_hashes=[],available=not a.unavailable); a.output.parent.mkdir(parents=True,exist_ok=True); a.output.write_text(json.dumps(row,indent=2,sort_keys=True)+"\n",encoding="utf-8",newline="\n"); print(json.dumps({"status":"PASS","provider_capsule_hash":row["provider_capsule_hash"],"exactness":row["provider_exactness_status"]},sort_keys=True)); return 0
if __name__=="__main__": raise SystemExit(main())
