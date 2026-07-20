"""Append Batch102 ingest, execution-origin correction, and fresh-work goals."""

from __future__ import annotations
import hashlib, json
from datetime import datetime, timezone
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
LEDGER=ROOT/"configs/controllergate_master_completion_ledger_v2.json"
OUT=ROOT/"outputs/post_v2_37_hardening_batch102_fresh_exact_counterfactual_execution_necessity_sufficiency_ownership_closure"
INGEST_COMMIT="db30b10cc1a4419ea6995b1a5c94568bf6f849f6"

def sha(path: Path)->str: return hashlib.sha256(path.read_bytes()).hexdigest()

def main()->int:
    ledger=json.loads(LEDGER.read_text(encoding="utf-8")); by_id={row["goal_id"]:row for row in ledger["goals"]}
    rels=[(OUT/x).relative_to(ROOT).as_posix() for x in ["batch101_execution_origin_correction_receipt.json","batch101_official_ingest/artifact_identity/batch101_official_outer_artifact_custody.json","batch101_official_ingest/custody/batch101_official_manifest_verification.json","batch101_official_ingest/reconciliation/batch101_official_semantic_reconciliation.json","batch101_official_ingest/reconciliation/batch101_official_execution_origin_reconciliation.json","batch101_official_ingest/ingest_receipts/batch101_official_ingest_receipt.json"]]
    hashes={p:sha(ROOT/p) for p in rels}; stamp=datetime.now(timezone.utc).isoformat()
    specs={
      "CG-GOAL-022-OFFICIAL-BATCH101-INGEST":("Official Batch101 artifact ingest","COMPLETE",[],["CG-GOAL-021-OFFICIAL-BATCH100-INGEST"]),
      "CG-GOAL-023-FRESH-CANDIDATE-EXECUTION-ATTESTATION":("Fresh candidate execution attestation","IN_PROGRESS",["fresh_Batch102_candidate_operations_not_yet_executed","current_workflow_broker_receipts_required"],["CG-GOAL-022-OFFICIAL-BATCH101-INGEST"]),
      "CG-GOAL-024-NECESSITY-SUFFICIENCY-ALTERNATIVE-EXCLUSION":("Necessity, sufficiency, and alternative exclusion","IN_PROGRESS",["necessity_not_executed","sufficiency_not_executed","remaining_alternatives_not_excluded"],["CG-GOAL-023-FRESH-CANDIDATE-EXECUTION-ATTESTATION"]),
      "CG-GOAL-025-REAL-ARCHITECTURE-ARM-EVALUATION":("Real architecture arm evaluation","IN_PROGRESS",["independently_selected_arm_evidence_not_yet_executed","architecture_gain_not_established"],["CG-GOAL-024-NECESSITY-SUFFICIENCY-ALTERNATIVE-EXCLUSION"]),
    }
    for gid,(title,status,blockers,prereq) in specs.items():
      if gid not in by_id:
        row={"goal_id":gid,"title":title,"status":status,"prerequisites":prereq,"required_evidence":["executed evidence bound to current workflow epoch"],"current_evidence":rels,"evidence_hashes":hashes,"completion_batch":None,"completion_commit":None,"active_blockers":blockers,"reopen_conditions":["independently verified custody, execution-origin, or semantic defect"],"authority_allowed":["evidence acquisition and non-authorizing evaluation"],"authority_forbidden":["candidate patch","repair count mutation","release promotion"],"last_updated_timestamp":stamp,"last_updated_commit":INGEST_COMMIT}
        if status=="COMPLETE": row.update({"completion_batch":"Batch102","completion_commit":INGEST_COMMIT})
        ledger["goals"].append(row); by_id[gid]=row
      else:
        by_id[gid].setdefault("completion_batch", None)
        by_id[gid].setdefault("completion_commit", None)
    existing={row.get("transition_id") for row in ledger.get("supersession_receipts",[])}
    for gid in [f"CG-GOAL-{n:03d}-" for n in range(6,11)]:
      goal=next(row for row in ledger["goals"] if row["goal_id"].startswith(gid)); tid=f"batch102:{goal['goal_id']}:execution-origin-correction"
      blockers=["Batch101_did_not_perform_fresh_candidate_execution","fresh_exact_candidate_operations_remain_required"]
      if goal["goal_id"].endswith("ARCHITECTURE-GAIN"): blockers.append("architecture_gain_not_evaluated_from_independently_selected_arm_evidence")
      goal["active_blockers"]=sorted(set(goal.get("active_blockers",[])+blockers)); goal["last_updated_timestamp"]=stamp; goal["last_updated_commit"]=INGEST_COMMIT
      if tid not in existing:
        ledger.setdefault("supersession_receipts",[]).append({"transition_id":tid,"goal_id":goal["goal_id"],"previous_status":goal["status"],"new_status":goal["status"],"transition_reason":"Batch101 advanced semantic contracts and replay interpretation but did not perform fresh candidate execution; current-workflow exact operations remain required.","evidence_paths":rels,"evidence_sha256s":hashes,"transition_commit":INGEST_COMMIT,"active_blockers":goal["active_blockers"],"reopen_conditions":goal["reopen_conditions"],"authority_allowed":["execution-origin correction and fresh evidence acquisition"],"authority_forbidden":["historical rewrite","fresh execution substitution","repair","count mutation","release promotion"]})
    ledger["goal_count"]=len(ledger["goals"]); ledger.setdefault("batch_output_links",{})["Batch102"]=OUT.relative_to(ROOT).as_posix(); ledger["last_updated_batch"]="Batch102"; ledger["last_updated_commit"]=INGEST_COMMIT; ledger["last_updated_timestamp"]=stamp
    LEDGER.write_text(json.dumps(ledger,indent=2,sort_keys=True)+"\n",encoding="utf-8",newline="\n")
    print(json.dumps({"status":"PASS","goal_count":len(ledger["goals"]),"transition_count":len(ledger.get("supersession_receipts",[])),"ledger_sha256":sha(LEDGER)},sort_keys=True)); return 0
if __name__=="__main__": raise SystemExit(main())
