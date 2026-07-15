from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "outputs/post_v2_37_hardening_batch090_evidence_delaundering_installed_vertical_closure"
BASE_REQUIRED = {
    "batch089_main_artifact_ingest.json", "batch089_short_lived_artifact_ingest.json",
    "batch089_evidence_depth_reconciliation.json", "execution_receipt_registry.jsonl",
    "mechanism_outcome_registry.jsonl", "test_assertion_registry.jsonl", "claim_binding_registry.jsonl",
    "evidence_scope_audit.json", "canonical_stage_registry.json", "stage_executor_verifier_matrix.json",
    "source_ownership_proof_resolution.json", "repair_license_proof_resolution.json",
    "sqlite_operational_population_audit.json", "sqlite_state_export.json",
    "installed_wheel_identity_windows.json", "installed_cli_vertical_trace_windows.jsonl",
    "amds_historical_frozen_frame.json", "amds_episode_eligibility.json", "amds_historical_quality_gate.json",
    "historical_capsule_transport_registry.json", "historical_count_nonincrement_audit.json",
    "non_source_episode_eligibility.json", "non_source_frozen_frame.json", "non_source_historical_results.json",
    "repaired_distribution_build.json", "repaired_package_canary_health_rollback.json",
    "public_state_evidence_depth_correction.json", "batch090_internal_release_decision.json",
    "batch090_claim_boundary.json", "batch090_consolidated_state.json", "campaign_summary.md",
}
CI_REQUIRED = {
    "installed_wheel_identity_linux.json", "installed_cli_vertical_trace_linux.jsonl",
    "cross_platform_vertical_equivalence.json", "repository_import_leakage_audit.json",
    "internal_critic_input_manifest.json", "internal_critic_reconstruction.json",
    "internal_critic_findings.jsonl", "mutation_campaign_registry.jsonl",
    "mutation_campaign_results.json", "internal_release_evidence_decision.json",
    "SHA256SUMS.txt", "PORTABLE_ARTIFACT_SHA256SUMS.txt", "ARTIFACT_SHA256SUMS.txt",
}


def load(name: str) -> dict[str, object]:
    return json.loads((OUTPUT / name).read_text(encoding="utf-8"))


def verify_manifest(name: str) -> list[str]:
    failures = []
    for line in (OUTPUT / name).read_text(encoding="utf-8").splitlines():
        expected, relative = line.split("  ", 1)
        path = OUTPUT / relative.removeprefix("./")
        if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != expected:
            failures.append(relative)
    return failures


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--allow-ci-pending", action="store_true")
    args = parser.parse_args()
    required = set(BASE_REQUIRED) | (set() if args.allow_ci_pending else CI_REQUIRED)
    missing = sorted(name for name in required if not (OUTPUT / name).is_file())
    failures = []
    if not missing:
        correction = load("public_state_evidence_depth_correction.json")
        decision = load("batch090_internal_release_decision.json")
        claim = load("batch090_claim_boundary.json")
        failures.extend([] if correction.get("batch089_mechanism_fixture_count") == 60 and correction.get("batch089_installed_product_vertical_lifecycle_count") == 0 else ["batch089_evidence_depth_correction_invalid"])
        failures.extend([] if decision.get("package_version") == "0.2.0b2.dev0" and decision.get("issue_derived_repair_count") == 6 and decision.get("native_external_repair_count") == 4 and decision.get("historical_repair_increment") == 0 else ["locked_public_state_changed"])
        failures.extend([] if decision.get("status") in {"PRODUCT_BETA_RC_BLOCKED_EXACT", "PRODUCT_BETA_RC_EXTERNAL_REVIEW_PENDING"} else ["product_beta_decision_invalid"])
        failures.extend([] if claim.get("production_readiness") is False and claim.get("self_maintaining_software") == "false/not demonstrated" and claim.get("full_scoring") == "NOT_RUN/disallowed" else ["claim_boundary_overreach"])
        failures.extend([] if load("amds_historical_quality_gate.json").get("prospective_effectiveness") == "NOT_ESTABLISHED" else ["amds_prospective_overclaim"])
        if not args.allow_ci_pending:
            for name in ("SHA256SUMS.txt", "PORTABLE_ARTIFACT_SHA256SUMS.txt", "ARTIFACT_SHA256SUMS.txt"):
                failures.extend(f"{name}:{item}" for item in verify_manifest(name))
            critic = load("internal_release_evidence_decision.json")
            failures.extend([] if critic.get("mutation_cases_executed") == 20 and critic.get("mutation_cases_rejected") == 20 else ["mutation_campaign_not_executed"])
            source = (ROOT / "scripts/batch090_standalone_internal_critic.py").read_text(encoding="utf-8")
            failures.extend([] if "controllergate" not in "\n".join(line for line in source.splitlines() if line.startswith(("import ", "from "))) else ["standalone_critic_import_violation"])
    result = {"status": "PASS" if not missing and not failures else "FAIL", "missing": missing, "failures": failures, "ci_pending_allowed": args.allow_ci_pending}
    print(json.dumps(result, sort_keys=True))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
