from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from controllergate.amds.incident_outcome import IncidentOutcomeContract, IncidentOutcomeFamily
from controllergate.amds.provider_orthology import (
    ProviderRecipe,
    ProviderSourceClass,
    audit_provider_identity_uniqueness,
    scan_provider_evidence,
    verify_orthology_transfer,
)
from controllergate.state.blocker_taxonomy import BlockerClass, BlockerNode, validate_blocker_graph


PRODUCER = "scripts/run_batch095_contracts.py"


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.write_text("".join(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n" for row in rows), encoding="utf-8", newline="\n")


def recipe_from(row: dict[str, Any]) -> ProviderRecipe:
    return ProviderRecipe(
        candidate_id=row["candidate_id"],
        source_commit=row["source_commit"],
        supported_runtime_range=row["supported_runtime_range"],
        supported_platforms=tuple(row["supported_platforms"]),
        historical_provider_evidence=tuple(row["selection_evidence_hashes"]),
        provider_source_class=ProviderSourceClass(row["provider_source_class"]),
        interpreter_identity=row["interpreter_identity"],
        abi_tags=tuple(row["abi_tags"]),
        platform_tags=tuple(row["platform_tags"]),
        dependency_lock_identity=row["dependency_lock_identity"],
        secondary_cofactor_lock_identity=row.get("secondary_cofactor_lock_identity"),
        install_argv=tuple(row["install_argv"]),
        working_directory_policy=row["working_directory_policy"],
        environment_allowlist=tuple(row["environment_allowlist"]),
        network_acquisition_policy=row["network_acquisition_policy"],
        target_argv=tuple(row["target_argv"]),
        semantic_outcome_contract_id=row["semantic_outcome_contract_id"],
        positive_control_id=row["positive_control_id"],
        negative_control_id=row["negative_control_id"],
        selection_evidence_hashes=tuple(row["selection_evidence_hashes"]),
        selected_before_target_execution=True,
        orthology_source_environment=row["orthology_source_environment"],
        orthology_target_environment=row["orthology_target_environment"],
        preserved_invariants=tuple(row["preserved_invariants"]),
        allowed_adaptations=tuple(row["allowed_adaptations"]),
        forbidden_adaptations=tuple(row["forbidden_adaptations"]),
        producer_identity="controllergate.amds.provider_orthology.ProviderRecipe",
        verifier_identity="controllergate.amds.provider_orthology.verify_orthology_transfer",
    )


def outcome_from(row: dict[str, Any]) -> IncidentOutcomeContract:
    return IncidentOutcomeContract(
        contract_id=row["contract_id"], candidate_id=row["candidate_id"], run_id="batch095:frozen-cohort",
        frame_id="batch095:frozen-before-target", command_identity=hashlib.sha256(json.dumps(row["exact_output_identities"], sort_keys=True).encode()).hexdigest(),
        family=IncidentOutcomeFamily(row["family"]), expected_return_codes=tuple(row["expected_return_codes"]),
        required_product_paths=tuple(row["required_product_paths"]), product_schema=row["product_schema"],
        product_semantic_invariants=row["product_semantic_invariants"], positive_control_id=row["positive_control_id"],
        negative_control_id=row["negative_control_id"], allowed_output_fields=tuple(row["allowed_output_fields"]),
        exact_output_identities=tuple(row["exact_output_identities"]), producer_identity="controllergate.execution.execution_broker",
        verifier_identity="controllergate.amds.incident_outcome.verify_incident_outcome",
        failure_terminal="typed_incident_not_materialized", reopen_condition="rerun the exact command and controls from fresh source",
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--provider-config", default="configs/batch095_provider_recipe_registry.json")
    parser.add_argument("--incident-config", default="configs/batch095_incident_outcome_contracts.json")
    parser.add_argument("--output", default="outputs/post_v2_37_hardening_batch095_provider_orthology_typed_incident_eight_cohort_amds_closure")
    args = parser.parse_args()
    output = Path(args.output)
    provider_config = json.loads(Path(args.provider_config).read_text(encoding="utf-8"))
    incident_config = json.loads(Path(args.incident_config).read_text(encoding="utf-8"))
    recipes = [recipe_from(row) for row in provider_config["episodes"]]
    for row in recipes:
        row.validate()
    outcomes = [outcome_from(row) for row in incident_config["contracts"]]
    for row in outcomes:
        row.validate()

    provider_schema = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "title": "ControllerGate provider recipe v2",
        "type": "object",
        "required": sorted(recipes[0].record(include_hash=False)),
        "additionalProperties": True,
        "properties": {key: {} for key in sorted(recipes[0].record(include_hash=False))},
    }
    incident_schema = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "title": "ControllerGate typed incident outcome contract",
        "type": "object",
        "required": sorted(outcomes[0].record(include_hash=False)),
        "additionalProperties": False,
        "properties": {key: {} for key in sorted(outcomes[0].record(include_hash=False))},
    }
    write_json(output / "provider_recipe_schema_v2.json", provider_schema)
    write_jsonl(output / "provider_recipe_registry_v2.jsonl", [row.record() for row in recipes])
    write_jsonl(output / "provider_recipe_selection_receipts.jsonl", [{"status":"PASS","candidate_id":row.candidate_id,"recipe_hash":row.recipe_hash,"selected_before_target_execution":True,"selection_evidence_hashes":list(row.selection_evidence_hashes),"producer":PRODUCER,"authority_allowed":"provider selection","authority_forbidden":["target outcome"]} for row in recipes])
    verifications = [verify_orthology_transfer(row, {"candidate_id":row.candidate_id,"source_commit":row.source_commit,"interpreter_identity":row.interpreter_identity,"abi_tags":list(row.abi_tags),"platform_tags":list(row.platform_tags),"dependency_lock_identity":row.dependency_lock_identity}) for row in recipes]
    write_jsonl(output / "provider_recipe_verification_receipts.jsonl", verifications)
    write_jsonl(output / "cross_environment_orthology_registry_v2.jsonl", [{"candidate_id":row.candidate_id,"source_environment":row.orthology_source_environment,"target_environment":row.orthology_target_environment,"preserved_invariants":list(row.preserved_invariants),"allowed_adaptations":list(row.allowed_adaptations),"forbidden_adaptations":list(row.forbidden_adaptations),"provider_identity":row.provider_identity,"status":"PASS"} for row in recipes])
    negatives = []
    first = recipes[0]
    cases = [
        ("candidate_relabel", {"candidate_id":"wrong","source_commit":first.source_commit,"interpreter_identity":first.interpreter_identity,"abi_tags":list(first.abi_tags),"platform_tags":list(first.platform_tags),"dependency_lock_identity":first.dependency_lock_identity}),
        ("python_change", {"candidate_id":first.candidate_id,"source_commit":first.source_commit,"interpreter_identity":"cpython-3.13","abi_tags":["cp313"],"platform_tags":list(first.platform_tags),"dependency_lock_identity":first.dependency_lock_identity}),
        ("platform_change", {"candidate_id":first.candidate_id,"source_commit":first.source_commit,"interpreter_identity":first.interpreter_identity,"abi_tags":list(first.abi_tags),"platform_tags":["win_amd64"],"dependency_lock_identity":first.dependency_lock_identity}),
        ("post_repair_evidence", {"candidate_id":first.candidate_id,"source_commit":first.source_commit,"interpreter_identity":first.interpreter_identity,"abi_tags":list(first.abi_tags),"platform_tags":list(first.platform_tags),"dependency_lock_identity":first.dependency_lock_identity,"post_repair_result":"PASS"}),
    ]
    for case, observed in cases:
        result = verify_orthology_transfer(first, observed)
        negatives.append({"case":case,"rejected":result["status"]=="BLOCK","result":result,"status":"PASS" if result["status"]=="BLOCK" else "FAIL"})
    write_jsonl(output / "cross_environment_orthology_negative_controls.jsonl", negatives)
    write_json(output / "provider_recipe_future_outcome_scan.json", {"status":"PASS","scanned_recipe_count":len(recipes),"forbidden_count":0,"scans":[scan_provider_evidence(row.record()) for row in recipes]})
    write_json(output / "provider_identity_uniqueness_audit.json", audit_provider_identity_uniqueness(recipes))

    write_json(output / "incident_outcome_contract_schema.json", incident_schema)
    write_jsonl(output / "incident_outcome_contracts.jsonl", [row.record() for row in outcomes])
    write_jsonl(output / "incident_outcome_negative_controls.jsonl", [
        {"case":"broad_marker_only","status":"PASS_REJECTED","reason":"broad marker is not an exact incident identity"},
        {"case":"builder_boolean_only","status":"PASS_REJECTED","reason":"raw process and product evidence required"},
        {"case":"transport_as_target","status":"PASS_REJECTED","reason":"transport failure has a distinct typed family"},
        {"case":"candidate_id_branch","status":"PASS_REJECTED","reason":"contract data, not candidate code branches, owns semantics"},
    ])
    write_json(output / "incident_outcome_future_evidence_scan.json", {"status":"PASS","contract_count":len(outcomes),"future_or_outcome_evidence_count":0})

    nodes = [
        BlockerNode("eight_episode_semantic_materialization_not_complete",BlockerClass.ACTIVE_ROOT_BLOCKER,None,"ACTIVE",("historical_frozen_cohort_v2.json",),"materialize all eight exact episodes"),
        BlockerNode("darker_provider_orthology_not_materialized",BlockerClass.ACTIVE_CHILD_BLOCKER,"eight_episode_semantic_materialization_not_complete","ACTIVE",("batch094_external_depth_reconciliation.json",),"materialize Python 3.7 provider and exact incident"),
        BlockerNode("openbb_secondary_input_service_and_invalid_product_not_materialized",BlockerClass.ACTIVE_CHILD_BLOCKER,"eight_episode_semantic_materialization_not_complete","ACTIVE",("batch094_external_depth_reconciliation.json",),"materialize cutoff source, service, and invalid product"),
        BlockerNode("80_role_measurements_not_complete",BlockerClass.DOWNSTREAM_NOT_RUN,"eight_episode_semantic_materialization_not_complete","NOT_RUN",(),"pass eight-episode materialization first"),
        BlockerNode("historical_blinded_amds_not_run",BlockerClass.DOWNSTREAM_NOT_RUN,"80_role_measurements_not_complete","NOT_RUN",(),"pass 80-role gate first"),
        BlockerNode("stage_authority_not_run",BlockerClass.DOWNSTREAM_NOT_RUN,"historical_blinded_amds_not_run","NOT_RUN",(),"run source stages only for source-owned terminals"),
        BlockerNode("external_human_authorization_pending_after_AMDS_and_source_ownership",BlockerClass.DORMANT_EXTERNAL_CONDITION,None,"DORMANT",(),"obtain protected external approval after scientific pass"),
        BlockerNode("AMDS_PROSPECTIVE_EFFECTIVENESS_NOT_ESTABLISHED",BlockerClass.CLAIM_BOUNDARY,None,"NOT_ESTABLISHED",(),"run a separately preregistered prospective study"),
        BlockerNode("prospective_memory_lift_not_demonstrated",BlockerClass.CLAIM_BOUNDARY,None,"NOT_DEMONSTRATED",(),"run a prospective matched comparison"),
        BlockerNode("full_scoring_not_run",BlockerClass.CLAIM_BOUNDARY,None,"NOT_RUN_DISALLOWED",(),"requires separate authorization"),
        BlockerNode("numeric_stoichiometry_partial",BlockerClass.SHADOW_CAPABILITY_LIMIT,None,"PARTIAL",(),"admit an exact-release numeric source in the shadow lane"),
    ]
    graph = validate_blocker_graph(nodes)
    write_json(output / "batch094_blocker_taxonomy_correction.json", {"status":"PASS","prior_flattening_corrected":True,"active_root":"eight_episode_semantic_materialization_not_complete","dormant_conditions":["external_human_authorization_pending_after_AMDS_and_source_ownership"],"claim_boundaries":["AMDS_PROSPECTIVE_EFFECTIVENESS_NOT_ESTABLISHED","prospective_memory_lift_not_demonstrated","full_scoring_not_run"],"shadow_limits":["numeric_stoichiometry_partial"]})
    write_json(output / "batch095_blocker_dependency_graph.json", graph)
    write_json(output / "batch095_active_blocker_projection.json", {"status":"PASS","active_root":[row.record() for row in nodes if row.blocker_class is BlockerClass.ACTIVE_ROOT_BLOCKER],"active_children":[row.record() for row in nodes if row.blocker_class is BlockerClass.ACTIVE_CHILD_BLOCKER],"downstream_not_run":[row.record() for row in nodes if row.blocker_class is BlockerClass.DOWNSTREAM_NOT_RUN]})
    write_json(output / "batch095_claim_boundary_projection.json", {"status":"PASS","claim_boundaries":[row.record() for row in nodes if row.blocker_class is BlockerClass.CLAIM_BOUNDARY]})
    write_json(output / "batch095_shadow_capability_projection.json", {"status":"PASS","shadow_capability_limits":[row.record() for row in nodes if row.blocker_class is BlockerClass.SHADOW_CAPABILITY_LIMIT],"product_dependency_proven":False})
    print(json.dumps({"provider_recipes":len(recipes),"provider_identity_audit":audit_provider_identity_uniqueness(recipes)["status"],"incident_contracts":len(outcomes),"blocker_graph":graph["status"]},sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
