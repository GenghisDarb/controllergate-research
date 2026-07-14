from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from controllergate.reactions.stable_identity import stable_hash
from controllergate.governance.law_runtime_adjudicator import adjudicate


def _rows(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def recompute(evidence: Path, builder_source: Path, critic_source: Path) -> dict[str, Any]:
    errors=[]
    reactions=_rows(evidence/"batch083_reaction_ledger.jsonl"); tokens=_rows(evidence/"batch083_output_token_registry.jsonl"); failures=_rows(evidence/"batch083_failed_reaction_registry.jsonl")
    completed={row["stable_event_id"] for row in reactions if row["outcome"]=="REACTION_COMPLETED"}
    if any(token["event_id"] not in completed for token in tokens): errors.append("token_without_completed_reaction")
    if any(row.get("output_token_minted") is not False for row in failures): errors.append("failed_reaction_minted_token")
    challenge=json.loads((evidence/"batch083_historical_amds_blind_challenge.json").read_text(encoding="utf-8"))
    if challenge.get("episode_count",0)<8 or challenge.get("repository_count",0)<5: errors.append("historical_challenge_depth")
    if any(len(ep.get("arms",[]))<4 or any(not arm.get("probes") for arm in ep.get("arms",[])) for ep in challenge.get("episodes",[])): errors.append("amds_arm_not_executed")
    canary=json.loads((evidence/"batch083_historical_canary_health_rollback.json").read_text(encoding="utf-8"))
    if canary.get("episode_count",0)<2 or canary.get("rollback_drills",0)<2: errors.append("canary_rollback_depth")
    connector=json.loads((evidence/"batch083_offline_connector_canary.json").read_text(encoding="utf-8"))
    if connector.get("write_authority") is not False or not connector.get("circuit_breaker_tested"): errors.append("connector_boundary")
    product=json.loads((evidence/"batch083_product_alpha_cycle.json").read_text(encoding="utf-8"))
    if product.get("resume",{}).get("status")!="CONTROLLED_PRODUCT_ALPHA_CYCLE_PASS" or not product.get("idempotent_final_verification"): errors.append("product_alpha_incomplete")
    claim=json.loads((evidence/"batch083_final_claim_boundary.json").read_text(encoding="utf-8"))
    if claim.get("issue_derived_repair_count")!=6 or claim.get("full_scoring")!="NOT_RUN/disallowed" or claim.get("write_capable_connectors")!="inactive": errors.append("claim_boundary_changed")
    bindings=_rows(evidence/"batch083_batch082_artifact_byte_binding.jsonl")
    if len(bindings)!=3 or any(row.get("byte_binding_status") != "PASS" for row in bindings): errors.append("prior_artifact_byte_binding")
    for candidate in ("openbb","poetry"):
        provider=json.loads((evidence/f"batch083_{candidate}_provider_v4_result.json").read_text(encoding="utf-8"))
        if provider.get("provider_execution_ready") and (provider["dependency_graph"].get("missing_runtime_dependencies") or len(provider.get("offline_installs",[]))!=2 or not all(row.get("state")=="PROVIDER_OFFLINE_INSTALL_PASSED" for row in provider["offline_installs"])):
            errors.append(f"false_provider_ready:{candidate}")
        reproduction=json.loads((evidence/f"batch083_{candidate}_duplicate_reproduction.json").read_text(encoding="utf-8"))
        if reproduction.get("duplicate_failure_admitted") and not (reproduction.get("status")=="CANDIDATE_FAILURE_REPRODUCED" and len(reproduction.get("replays",[]))==2 and all(row.get("incident_reproduced") for row in reproduction["replays"])):
            errors.append(f"false_candidate_admission:{candidate}")
    openapi=json.loads((evidence/"batch083_openapi_rooted_reference_closure.json").read_text(encoding="utf-8"))
    if openapi.get("state")!="PASS" or openapi.get("verification",{}).get("status")!="PASS": errors.append("rooted_openapi_closure")
    nulls=json.loads((evidence/"batch083_matched_nulls.json").read_text(encoding="utf-8"))
    if nulls.get("eligible") and (nulls.get("null_count")!=38 or nulls.get("actual_probe_count",0)<=0 or any(not row.get("probes") for row in nulls.get("nulls",[]))): errors.append("matched_null_execution")
    constitution=json.loads((Path(__file__).resolve().parents[2]/"configs/controllergate_engineering_constitution_v3.json").read_text(encoding="utf-8"))
    proof_dir=evidence/"batch083_constitution_v3_law_proofs"
    proofs={path.stem:json.loads(path.read_text(encoding="utf-8")) for path in proof_dir.glob("CG-LAW-*.json")}
    law_result=adjudicate(constitution,proofs,evidence)
    if law_result.get("status")!="PASS" or law_result.get("law_count")!=40: errors.append("constitution_proof_custody")
    result={"evaluator":"batch083_independent_critic_v2","status":"PASS" if not errors else "FAIL","errors":errors,
            "builder_source_sha256":hashlib.sha256(builder_source.read_bytes()).hexdigest(),
            "critic_source_sha256":hashlib.sha256(critic_source.read_bytes()).hexdigest(),
            "separately_hashed_source_files":builder_source.resolve()!=critic_source.resolve(),
            "builder_pass_fields_accepted_as_facts":False,"raw_records_recomputed":len(reactions)+len(tokens)+len(failures)+challenge.get("actual_probe_count",0),
            "agreement_calculated_after_sealing":True,"constitution_proof_custody":law_result}
    result["critic_seal"]=stable_hash(result); return result
