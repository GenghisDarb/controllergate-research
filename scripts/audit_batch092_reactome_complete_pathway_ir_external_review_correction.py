from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


OUTPUT_NAME = "post_v2_37_hardening_batch092_reactome_complete_pathway_ir_external_review_correction"
MANIFESTS = ("ARTIFACT_SHA256SUMS.txt", "PORTABLE_ARTIFACT_SHA256SUMS.txt", "SHA256SUMS.txt")


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def rows(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require(condition: bool, message: str, failures: list[str]) -> None:
    if not condition:
        failures.append(message)


def main() -> int:
    parser = argparse.ArgumentParser(); parser.add_argument("--output", default=f"outputs/{OUTPUT_NAME}"); parser.add_argument("--require-cross-platform", action="store_true"); args = parser.parse_args()
    output = Path(args.output); failures: list[str] = []
    ingest = read_json(output / "batch091_artifact_ingest.json")
    manifest_audit = read_json(output / "batch091_artifact_manifest_verification.json")
    expected_red = read_json(output / "batch092_pre_fix_external_review_expected_failure.json")
    source = read_json(output / "reactome_source_coverage.json")
    stable = read_json(output / "rpir_stable_identity_audit.json")
    translation = read_json(output / "reactome_translation_coverage.json")
    primitive = read_json(output / "reactome_generic_primitive_execution_coverage.json")
    chapter = read_json(output / "reactome_chapter_coverage_audit.json")
    cross = read_json(output / "reactome_cross_platform_equivalence.json")
    amds = read_json(output / "amds_quality_gate.json")
    baselines = read_json(output / "amds_executed_baselines.json")
    proof = read_json(output / "proof_producer_verifier_independence.json")
    canary = read_json(output / "canary_and_rollback_decision.json")
    critic = read_json(output / "internal_release_evidence_decision.json")
    semantic_mutations = read_json(output / "resigned_raw_semantic_mutation_results.json")
    decision = read_json(output / "batch092_internal_release_decision.json")
    claims = read_json(output / "batch092_claim_boundary.json")

    require(ingest["status"] == "PASS", "Batch091 artifact custody failed", failures)
    require(ingest["observed_sha256"] == "306cc60bc1be7c89f7579c9b8a9c4b0f217ba15ef4f5f54d9b416aa6171560c5", "Batch091 artifact identity mismatch", failures)
    require(manifest_audit["status"] == "PASS_WITH_RECONCILED_OUTER_SELF_MANIFEST_DEFECT", "Batch091 outer self-manifest defect not reconciled", failures)
    require(expected_red["status"] == "BATCH092_PRE_FIX_EXTERNAL_REVIEW_FAIL_EXPECTED" and expected_red["finding_count"] == 24, "expected-red external review missing", failures)
    require(source["status"] == "PASS" and source["unique_chapter_count"] == 29 and source["duplicate_chapter_count"] == 0, "Reactome document coverage failed", failures)
    require(source["observed_pathway_count"] == 2916 and source["observed_reaction_count"] == 16814 and source["silent_omission_count"] == 0, "Reactome source counts failed", failures)
    require(stable["status"] == "PASS" and stable["source_occurrence_count"] == 19730, "RPIR stable identity/reuse audit failed", failures)
    require(translation["status"] == "PASS" and translation["translation_candidate_count"] == 16814 and translation["automatic_rejection_count"] == 0, "translation coverage failed", failures)
    require(translation["rejection_without_ablation_count"] == 0, "translation rejection without ablation", failures)
    require(primitive["status"] == "PASS" and primitive["executed_count"] == primitive["expected_count"], "generic primitive execution incomplete", failures)
    require(chapter["status"] == "PASS" and chapter["chapter_count"] == 29, "chapter scenario registry incomplete", failures)
    windows = rows(output / "installed_reactome_scenarios_windows.jsonl") if (output / "installed_reactome_scenarios_windows.jsonl").is_file() else []
    require(len(windows) == 29 and all(row.get("installed_site_packages_origin") is True for row in windows), "Windows installed CLI scenario evidence failed", failures)
    if args.require_cross_platform:
        linux = rows(output / "installed_reactome_scenarios_linux.jsonl") if (output / "installed_reactome_scenarios_linux.jsonl").is_file() else []
        require(len(linux) == 29 and all(row.get("installed_site_packages_origin") is True for row in linux), "Linux installed CLI scenario evidence failed", failures)
        require(cross["status"] == "PASS", "cross-platform equivalence failed", failures)
    else:
        require(cross["status"] in {"PASS", "PENDING_OTHER_PLATFORM"}, "cross-platform status invalid", failures)
    require(amds["status"] == "BLOCK" and amds["eligible_cohort_count"] == 0, "ineligible AMDS cohort was not blocked", failures)
    require(amds["post_repair_or_future_receipt_count"] == 0 and baselines["copied_result_count"] == 0, "AMDS future receipt or copied baseline contamination", failures)
    require(proof["executed_stage_receipt_count"] == 0 and proof["independently_verified_stage_receipt_count"] == 0, "downstream proofs ran after AMDS block", failures)
    require(canary["real_historical_repaired_slot_switch"] == "NOT_RUN" and canary["real_historical_exact_rollback"] == "NOT_RUN", "historical slot actuation ran after AMDS block", failures)
    require(critic["status"] == "PRODUCT_BETA_RC_BLOCKED_EXACT" and critic["finding_count"] > 0, "standalone critic overclaimed or emitted no findings", failures)
    require(semantic_mutations["status"] == "PASS" and semantic_mutations["executed"] == semantic_mutations["rejected"], "semantic mutation campaign failed", failures)
    require(decision["status"] == "PRODUCT_BETA_RC_BLOCKED_EXACT", "Batch092 release decision overclaimed", failures)
    require(claims["protocol"] == "v2.19" and claims["package_version"] == "0.2.0b2.dev0", "protocol or package version changed", failures)
    require(claims["issue_derived_repair_count"] == 6 and claims["native_external_repair_count"] == 4 and claims["historical_increment"] == 0, "repair counts changed", failures)
    require(claims["full_scoring"] == "NOT_RUN/disallowed" and claims["production_readiness"] is False and claims["self_maintaining_software"] == "false/not demonstrated", "claim boundary overclaimed", failures)

    for manifest_name in MANIFESTS:
        lines = [line for line in (output / manifest_name).read_text(encoding="utf-8").splitlines() if line]
        names = [line.split("  ", 1)[1] for line in lines]
        require(manifest_name not in names, f"{manifest_name} contains an invalid self entry", failures)
        for line in lines:
            expected, name = line.split("  ", 1)
            require((output / name).is_file() and sha(output / name) == expected, f"manifest mismatch: {manifest_name}:{name}", failures)
    forbidden_suffixes = {".zip", ".pdf", ".whl", ".pyc", ".tar", ".tgz", ".sqlite", ".sqlite3"}
    require(not [path for path in output.rglob("*") if path.is_file() and path.suffix.lower() in forbidden_suffixes], "forbidden raw/runtime payload in main output", failures)
    require(not any("incoming_artifacts" in str(path) for path in output.rglob("*")), "incoming artifact path included", failures)
    result = {
        "status": "PASS" if not failures else "FAIL", "producer": "scripts/audit_batch092_reactome_complete_pathway_ir_external_review_correction.py",
        "execution_depth": "complete Batch092 output, authority, manifest, and claim-boundary audit", "semantic_scope": "Batch092 internal evidence",
        "authority_allowed": "internal audit", "authority_forbidden": "external release approval", "require_cross_platform": args.require_cross_platform,
        "failure_count": len(failures), "failures": failures,
    }
    print(json.dumps(result, sort_keys=True))
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
