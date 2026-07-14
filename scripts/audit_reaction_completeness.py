from __future__ import annotations

import argparse,json
from pathlib import Path


def rows(path:Path):return [json.loads(x) for x in path.read_text(encoding="utf-8").splitlines() if x]
def main()->int:
 p=argparse.ArgumentParser();p.add_argument("--out",required=True);a=p.parse_args();o=Path(a.out);events=rows(o/"batch083_reaction_ledger.jsonl");tokens=rows(o/"batch083_output_token_registry.jsonl");failures=rows(o/"batch083_failed_reaction_registry.jsonl");complete={r["stable_event_id"] for r in events if r["outcome"]=="REACTION_COMPLETED"};errors=[]
 if any(t["event_id"] not in complete for t in tokens):errors.append("unlicensed_token")
 if any(r["outcome"]=="REACTION_COMPLETED" and not all(r.get("compartment_verification",{}).values()) for r in events):errors.append("unverified_compartment")
 if any(f.get("output_token_minted") is not False for f in failures):errors.append("failed_minted")
 if not complete or not failures:errors.append("controls_missing")
 print(json.dumps({"status":"PASS" if not errors else "FAIL","events":len(events),"tokens":len(tokens),"failures":len(failures),"errors":errors},sort_keys=True));return 0 if not errors else 1
if __name__=="__main__":raise SystemExit(main())
