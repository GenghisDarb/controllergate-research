from __future__ import annotations
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def main()->int:
 source=json.loads((ROOT/"configs/controllergate_seed_product_readiness_registry.json").read_text(encoding="utf-8"))["records"]
 rows=[]
 for index,item in enumerate(source[:24],1):
  row={"cohort_id":f"batch102-preliminary-{index:03d}","candidate_id":item["candidate_id"],"repository":item.get("repo_url"),"issue":item.get("issue_url_or_source_url") or None,"cutoff":None,"source_provider_availability":"BLOCKED" if item.get("missing_environment") or item.get("missing_provider_capsule") else "PRELIMINARY","proposed_causal_family":"UNASSIGNED_BEFORE_DIAGNOSIS","selection_reason":"existing public seed-readiness record selected in frozen registered order","selection_blindness_evidence":{"future_fix_inspected":False,"gold_patch_inspected":False,"outcome_inspected":False,"source_registry_record_hash":hashlib.sha256(json.dumps(item,sort_keys=True,separators=(",",":")).encode()).hexdigest()},"status":"PRELIMINARY_NOT_DIAGNOSED","authority_allowed":"future cohort planning","authority_forbidden":["diagnosis","truth","patch","repair count","release"]};rows.append(row)
 path=ROOT/"configs/batch102_preliminary_historical_cohort_registry_v1.jsonl";path.write_text("".join(json.dumps(x,sort_keys=True,separators=(",",":"))+"\n" for x in rows),encoding="utf-8",newline="\n");print(json.dumps({"status":"IN_PROGRESS","record_count":len(rows)},sort_keys=True));return 0
if __name__=="__main__":raise SystemExit(main())
