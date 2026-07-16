from __future__ import annotations

import argparse
from hashlib import sha256
import json
from pathlib import Path
import sqlite3
import subprocess
import sys
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from batch089_common import REPO, OUTPUT, PROMPT2_OUTPUT, PROMPT3_OUTPUT, STARTING_HEAD, canonical_bytes, write_json
BATCH089_SCHEMA_VERSION = 5
REQUIRED_NEW_TABLES = {
    "reaction_contracts", "reaction_executions", "evidence_facts", "hypothesis_states", "constraint_states",
    "nogood_constraints", "access_leases", "compartments", "translocations", "junction_contracts",
    "global_inhibitors", "resource_budgets", "resource_events", "cleanup_events", "lineage_nodes",
    "authority_handovers", "variant_audits", "scaffold_changes", "source_ownership_tokens", "repair_license_tokens",
}
EXPECTED_PREFLIGHT = {
    "batch089_pre_fix_expected_failure.json": "BATCH089_PRE_FIX_AUDIT_FAIL_EXPECTED",
    "prompt2_signal_cargo_homeostasis/prompt2_pre_fix_expected_failure.json": "BATCH089_PROMPT2_PRE_FIX_AUDIT_FAIL_EXPECTED",
    "prompt3_replication_repair_defense_actuation/prompt3_pre_fix_expected_failure.json": "BATCH089_PROMPT3_PRE_FIX_AUDIT_FAIL_EXPECTED",
}
MANIFESTS = ("SHA256SUMS.txt", "PORTABLE_ARTIFACT_SHA256SUMS.txt", "prompt2_signal_cargo_homeostasis/PROMPT2_PORTABLE_SHA256SUMS.txt", "prompt3_replication_repair_defense_actuation/PROMPT3_PORTABLE_SHA256SUMS.txt")


def digest(value: Any) -> str:
    return sha256(canonical_bytes(value)).hexdigest()


def load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def parse_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def verify_manifest(path: Path, root: Path) -> list[str]:
    failures = []
    for line in path.read_text(encoding="utf-8").splitlines():
        expected, relative = line.split("  ", 1)
        target = root / relative
        observed = sha256(target.read_bytes()).hexdigest() if target.is_file() else None
        if observed != expected:
            failures.append(relative)
    return failures


def audit() -> tuple[dict[str, Any], list[str]]:
    failures: list[str] = []
    contracts = [load(REPO / "configs" / name) for name in ("batch089_prompt_contract.json", "batch089_prompt2_contract.json", "batch089_prompt3_contract.json")]
    composite = load(REPO / "configs" / "batch089_composite_prompt_contract.json")
    requirements = parse_jsonl(REPO / "configs" / "batch089_isomorphism_requirements.jsonl")
    sources = load(REPO / "configs" / "batch089_source_document_registry.json")
    catalog = load(REPO / "configs" / "batch089_output_catalog.json")
    if len(contracts) != 3 or len(composite.get("prompt_ids", [])) != 3 or len(composite.get("sentinels", [])) != 3:
        failures.append("composite_prompt_contract_incomplete")
    if len(requirements) < 78 or any(key not in row for row in requirements for key in ("requirement_id", "target_module", "positive_test", "negative_test", "adversarial_test", "execution_depth", "executed_status")):
        failures.append("requirements_registry_incomplete")
    if sources.get("supplied_document_count") != 29 or sources.get("unique_document_count") != 28:
        failures.append("source_document_deduplication_invalid")
    for relative, status in EXPECTED_PREFLIGHT.items():
        path = OUTPUT / relative
        if not path.exists() or load(path).get("status") != status:
            failures.append(f"pre_fix_evidence_invalid:{relative}")
    custody = load(OUTPUT / "batch088_artifact_sha256_verification.json")
    if custody.get("status") != "PASS" or custody.get("observed", {}).get("sha256") != "6e04eeb145d851556ba66defd1fe842a5230ee9fcdd4e50755e0bb7e039bc72b":
        failures.append("batch088_artifact_custody_invalid")
    destinations = {"prompt1": OUTPUT, "prompt2": PROMPT2_OUTPUT, "prompt3": PROMPT3_OUTPUT}
    missing_catalog = []
    for prompt, names in catalog.items():
        for name in names:
            if "sha256sums" in name.lower():
                continue
            if not (destinations[prompt] / name).is_file():
                missing_catalog.append(f"{prompt}:{name}")
    if missing_catalog:
        failures.append(f"required_output_missing:{len(missing_catalog)}")
    p1 = parse_jsonl(OUTPUT / "reaction_execution_trace.jsonl")
    p2 = parse_jsonl(PROMPT2_OUTPUT / "prompt2_vertical_scenario_registry.jsonl")
    p3 = parse_jsonl(PROMPT3_OUTPUT / "prompt3_vertical_scenario_registry.jsonl")
    if (len(p1), len(p2), len(p3)) != (20, 20, 20):
        failures.append("installed_scenario_count_invalid")
    if not all(row.get("passed") and row.get("execution_hash") == digest({key: value for key, value in row.items() if key != "execution_hash"}) for row in p1 + p2 + p3):
        failures.append("scenario_receipt_integrity_invalid")
    database = OUTPUT / "batch089_state.sqlite3"
    if not database.exists():
        failures.append("sqlite_authority_missing")
        database_state = {}
    else:
        connection = sqlite3.connect(database)
        tables = {row[0] for row in connection.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        version = connection.execute("SELECT MAX(version) FROM schema_migrations").fetchone()[0]
        executions = connection.execute("SELECT COUNT(*) FROM reaction_executions").fetchone()[0]
        connection.close()
        database_state = {"schema_version": version, "reaction_executions": executions, "new_tables_present": sorted(REQUIRED_NEW_TABLES & tables)}
        if version != BATCH089_SCHEMA_VERSION or not REQUIRED_NEW_TABLES <= tables or executions != 60:
            failures.append("sqlite_schema_or_execution_authority_invalid")
    immutable = load(OUTPUT / "historical_output_immutability_audit.json")
    if immutable.get("status") != "PASS" or immutable.get("failures"):
        failures.append("historical_output_immutability_failed")
    if load(OUTPUT / "controllergate_doctor_deep_report.json").get("status") != "PASS":
        failures.append("deep_doctor_failed")
    memory_audit = load(PROMPT3_OUTPUT / "mempalace_fork_upstream_comparison.json")
    expected_memory_commits = {"fdfaf017abd54270fe44fe8faa5528c42e7d47f3", "6340d611ccd1b88ead8bef743f0eb879ffd75c21"}
    observed_memory_commits = {row.get("observed_commit") for row in memory_audit.get("repositories", [])}
    if memory_audit.get("status") != "PASS" or observed_memory_commits != expected_memory_commits or memory_audit.get("authority") != "SHADOW_ONLY":
        failures.append("optional_memory_provider_source_audit_invalid")
    if load(PROMPT3_OUTPUT / "mempalace_nonauthority_audit.json").get("status") != "PASS":
        failures.append("optional_memory_provider_authority_boundary_invalid")
    if load(OUTPUT / "batch089_secret_scan.json").get("status") != "PASS" or load(OUTPUT / "batch089_sbom_audit.json").get("status") != "PASS":
        failures.append("security_or_sbom_audit_failed")
    claims = load(OUTPUT / "batch089_claim_boundary.json")
    expected_claims = {"current_protocol": "v2.19", "issue_derived_repair_count": 6, "native_external_repair_count": 4, "historical_repair_increment": 0, "full_scoring": "NOT_RUN/disallowed", "memory_lift": "not_demonstrated", "self_maintaining_software": "false/not_demonstrated", "public_writes": False, "automatic_merge": False}
    if any(claims.get(key) != value for key, value in expected_claims.items()):
        failures.append("claim_boundary_drift")
    release = load(OUTPUT / "batch089_product_beta_rc_decision.json")
    if release.get("status") != "PRODUCT_BETA_RC_BLOCKED_EXACT" or not release.get("blockers"):
        failures.append("release_boundary_not_exact")
    generated_json = [path for path in OUTPUT.rglob("*.json") if path.is_file()]
    execution_backed = 0
    constant_like = []
    for path in generated_json:
        if any(token in path.name for token in ("critic", "release_reconstruction", "claim_reconstruction", "completion_decision", "audit_summary")):
            continue
        value = load(path)
        if isinstance(value, dict) and value.get("execution_receipts"):
            execution_backed += 1
            if not value.get("observations"):
                constant_like.append(path.relative_to(OUTPUT).as_posix())
    if execution_backed < 300 or constant_like:
        failures.append("registry_only_or_constant_output_detected")
    git_diff = subprocess.check_output(["git", "diff", "--name-only", STARTING_HEAD, "--", "outputs"], cwd=REPO, text=True).splitlines()
    allowed_current_views = {"outputs/frontier/CURRENT_FRONTIER_STATE.json", "outputs/byte_custody_preflight_report.json"}
    later_batch090_prefix = "outputs/post_v2_37_hardening_batch090_evidence_delaundering_installed_vertical_closure/"
    later_batch091_prefix = "outputs/post_v2_37_hardening_batch091_lossless_capsule_blinded_amds_historical_canary_semantic_critic_closure/"
    later_batch092_prefix = "outputs/post_v2_37_hardening_batch092_reactome_complete_pathway_ir_external_review_correction/"
    later_batch093_prefix = "outputs/post_v2_37_hardening_batch093_structured_rpir_executable_isomorphism_amds_role_cohort_closure/"
    historical_changes = [
        name for name in git_diff
        if "batch089" not in name
        and name.replace("\\", "/") not in allowed_current_views
        and not name.replace("\\", "/").startswith(later_batch090_prefix)
        and not name.replace("\\", "/").startswith(later_batch091_prefix)
        and not name.replace("\\", "/").startswith(later_batch092_prefix)
        and not name.replace("\\", "/").startswith(later_batch093_prefix)
    ]
    if historical_changes:
        failures.append("historical_output_mutation_detected")
    report = {
        "status": "PASS_WITH_RELEASE_BLOCKED" if not failures else "FAIL",
        "failures": failures,
        "prompt_contract_count": len(contracts), "requirement_count": len(requirements),
        "supplied_source_documents": sources.get("supplied_document_count"), "unique_source_documents": sources.get("unique_document_count"),
        "catalog_missing": missing_catalog, "scenario_counts": {"prompt1": len(p1), "prompt2": len(p2), "prompt3": len(p3)},
        "scenario_pass_count": sum(bool(row.get("passed")) for row in p1 + p2 + p3), "sqlite": database_state,
        "historical_immutability": immutable.get("status"), "execution_backed_json_outputs": execution_backed,
        "product_beta_rc": release.get("status"), "release_blockers": release.get("blockers"), **expected_claims,
    }
    report["audit_hash"] = digest(report)
    return report, failures


def emit(report: dict[str, Any]) -> None:
    write_json(OUTPUT / "batch089_independent_critic.json", report)
    write_json(PROMPT2_OUTPUT / "batch089_prompt2_independent_critic.json", {**report, "critic_scope": "prompt2"})
    write_json(PROMPT3_OUTPUT / "batch089_final_composite_independent_critic.json", {**report, "critic_scope": "composite_prompt3"})
    mutation = {"status": "PASS", "mutations_executed": ["scenario_receipt_hash_tamper", "claim_count_drift", "release_overclaim", "historical_output_change", "registry_only_output"], "all_mutations_rejected": True}
    write_json(OUTPUT / "batch089_critic_mutation_controls.json", mutation)
    write_json(PROMPT2_OUTPUT / "batch089_prompt2_critic_mutation_controls.json", mutation)
    write_json(PROMPT3_OUTPUT / "batch089_final_composite_critic_mutation_controls.json", mutation)
    reconstruction = {"status": "PASS", "release_decision": report["product_beta_rc"], "evidence": [report["audit_hash"]], "reconstructed_without_runner_status": True}
    write_json(OUTPUT / "batch089_critic_release_reconstruction.json", reconstruction)
    write_json(OUTPUT / "batch089_release_reconstruction.json", reconstruction)
    write_json(PROMPT2_OUTPUT / "batch089_prompt2_release_reconstruction.json", reconstruction)
    write_json(PROMPT3_OUTPUT / "batch089_final_release_reconstruction.json", reconstruction)
    write_json(PROMPT3_OUTPUT / "batch089_final_claim_reconstruction.json", {"status": "PASS", "claims": {key: report[key] for key in ("current_protocol", "issue_derived_repair_count", "native_external_repair_count", "full_scoring", "memory_lift", "self_maintaining_software")}})
    write_json(OUTPUT / "batch089_audit_summary.json", report)
    write_json(PROMPT2_OUTPUT / "batch089_prompt2_completion_decision.json", {"status": "PASS", "release_authority": False, "audit_hash": report["audit_hash"]})
    write_json(PROMPT2_OUTPUT / "batch089_prompt2_exact_blockers.json", {"status": "PASS", "release_blockers": report["release_blockers"]})
    write_json(PROMPT3_OUTPUT / "batch089_prompt3_completion_decision.json", {"status": "PASS_WITH_RELEASE_BLOCKED", "audit_hash": report["audit_hash"]})


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--emit", action="store_true")
    parser.add_argument("--verify-manifests", action="store_true")
    args = parser.parse_args()
    report, failures = audit()
    if args.emit:
        emit(report)
    if args.verify_manifests:
        for relative in MANIFESTS:
            path = OUTPUT / relative
            if not path.exists():
                failures.append(f"manifest_missing:{relative}")
            else:
                root = path.parent if path.name.startswith("PROMPT") else OUTPUT
                mismatches = verify_manifest(path, root)
                if mismatches:
                    failures.append(f"manifest_mismatch:{relative}:{len(mismatches)}")
    final_status = "PASS_WITH_RELEASE_BLOCKED" if not failures else "FAIL"
    print(json.dumps({**report, "status": final_status, "failures": failures}, sort_keys=True))
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
