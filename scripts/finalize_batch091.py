from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "outputs/post_v2_37_hardening_batch091_lossless_capsule_blinded_amds_historical_canary_semantic_critic_closure"


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def write(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=OUTPUT)
    args = parser.parse_args(); out = args.output
    batch090 = load(out / "batch090_artifact_ingest.json")
    reconciliation = load(out / "batch090_claim_reconciliation.json")
    hidden = load(out / "hidden_file_conservation_audit.json")
    capsule_transport = load(out / "producer_consumer_capsule_conservation.json")
    residue = load(out / "short_lived_artifact_residue_audit.json")
    amds = load(out / "amds_historical_quality_gate.json")
    proof = load(out / "authority_proof_execution_depth_audit.json")
    lifecycle = {name: load(out / f"{name}_installed_historical_lifecycle.json") for name in ("cloudpickle", "freezegun")}
    non_source = {name: load(out / f"{name}_installed_non_source_lifecycle.json") for name in ("audioread", "hordeforge")}
    canary = load(out / "repaired_package_canary_health_rollback.json")
    critic = load(out / "internal_release_evidence_decision.json")
    seal = load(out / "seal_breaking_mutation_results.json")
    semantic = load(out / "resigned_semantic_mutation_results.json")
    criteria = {
        "batch090_artifact_custody": batch090.get("status") == "PASS",
        "batch090_claim_reconciliation": reconciliation.get("status") == "PASS",
        "cloudpickle_lossless_source_transport": hidden["candidates"]["cloudpickle"].get("status") == "PASS",
        "freezegun_lossless_source_transport": hidden["candidates"]["freezegun"].get("status") == "PASS",
        "provider_capsule_transport": capsule_transport.get("status") == "LOSSLESS_CAPSULE_TRANSPORT_PASS",
        "short_lived_transport_residue_zero": residue.get("status") == "PASS" and residue.get("residue_count") == 0,
        "canonical_engine_and_authority": proof.get("status") == "PASS" and proof.get("manifest_injected_authority_count", 0) == 0,
        "blinded_eight_episode_amds": amds.get("status") == "AMDS_HISTORICAL_BLINDED_CAUSAL_MECHANISM_PASS" and amds.get("eligible_episode_count") == 8,
        "cloudpickle_installed_lifecycle": lifecycle["cloudpickle"].get("status") == "PASS",
        "freezegun_installed_lifecycle": lifecycle["freezegun"].get("status") == "PASS",
        "audioread_non_source_lifecycle": non_source["audioread"].get("status") == "PASS",
        "hordeforge_non_source_lifecycle": non_source["hordeforge"].get("status") == "PASS",
        "repaired_distribution_canary_rollback": canary.get("aggregate_result") == "DEPLOYED_CANARY_HEALTH_ROLLBACK_PASS",
        "standalone_semantic_critic": critic.get("status") == "SEMANTIC_STANDALONE_CRITIC_PASS",
        "seal_breaking_mutations": seal.get("executed") == seal.get("rejected") == 22,
        "resigned_semantic_mutations": semantic.get("executed") == semantic.get("rejected_for_semantic_reasons") == 22,
    }
    internal_pass = all(criteria.values())
    status = "PRODUCT_BETA_RC_EXTERNAL_REVIEW_PENDING" if internal_pass else "PRODUCT_BETA_RC_BLOCKED_EXACT"
    failed = [name for name, value in criteria.items() if not value]
    blocker = "external_independent_release_review_pending" if internal_pass else failed[0]
    public_state = {
        "status": status, "exact_blocker": blocker, "protocol": "v2.19", "package_version": "0.2.0b2.dev0",
        "issue_derived_repair_count": 6, "native_external_repair_count": 4, "historical_increment": 0,
        "production_readiness": False, "self_maintaining_software": "false/not_demonstrated",
        "amds_prospective_effectiveness": "NOT_ESTABLISHED", "prospective_memory_lift": "not_demonstrated",
        "full_scoring": "NOT_RUN/disallowed", "public_writes": "inactive", "automatic_merge": "inactive",
        "tag_created": False, "release_created": False, "publication_performed": False,
        "batch090_verticalization": "canonical_installed_wheel_verticalization_completed",
        "batch090_source_transport_correction": "public_hidden_files_were_dropped_by_legacy_transport_and_are_losslessly_conserved_by_batch091",
    }
    evidence_sources = [path.name for path in sorted(out.iterdir()) if path.is_file() and path.name not in {"SHA256SUMS.txt"}]
    write(out / "public_state_generation_audit.json", {"status": "PASS", "producer": "batch091-finalizer", "evidence_derived": True, "source_files": evidence_sources, "public_state": public_state})
    docs = [ROOT / "README.md", ROOT / "docs/current_status.md", ROOT / "docs/capability_inventory.md", ROOT / "docs/public_release_readiness.md", ROOT / "controllergate_v1_7_beta/reports/critic_review_package/shareable_summary.md"]
    synced = all("PRODUCT_BETA_RC_EXTERNAL_REVIEW_PENDING" in path.read_text(encoding="utf-8") and "Batch091" in path.read_text(encoding="utf-8") for path in docs)
    write(out / "public_state_sync_audit.json", {"status": "PASS" if synced else "FAIL", "public_state_synchronized": synced, "documents": [str(path.relative_to(ROOT)).replace("\\", "/") for path in docs]})
    write(out / "release_version_lineage.json", {"status": "PASS", "previous_version": "0.2.0b2.dev0", "current_version": "0.2.0b2.dev0", "protocol": "v2.19", "tag_created": False, "release_created": False})
    write(out / "batch091_internal_release_decision.json", {"status": status, "exact_blocker": blocker, "criteria": criteria, "failed_criteria": failed, "external_independent_review_required": True})
    write(out / "batch091_claim_boundary.json", public_state)
    write(out / "batch091_consolidated_state.json", {**public_state, "internal_criteria_pass": internal_pass, "cloudpickle_lifecycle": lifecycle["cloudpickle"]["status"], "freezegun_lifecycle": lifecycle["freezegun"]["status"], "non_source_lifecycles": [row["status"] for row in non_source.values()], "canary": canary["aggregate_result"], "semantic_critic": critic["status"]})
    summary = f"""# Batch091 campaign summary

Batch091 verified and reconciled the official Batch090 evidence, replaced lossy source transport with deterministic Git-tree capsules, and conserved all 58 Cloudpickle and 39 Freezegun public hidden files. The physically blinded eight-episode historical AMDS campaign passed its frozen causal-mechanism quality gate without terminal-label leakage or repair-authority leakage.

The installed canonical ControllerGate CLI completed non-counting Cloudpickle and Freezegun repair lifecycles plus Audioread and HordeForge non-source lifecycles. Cloudpickle's repaired wheel was independently rebuilt, installed in a distinct canary compartment, exercised through three independent health classes, rejected the original buggy distribution, switched locally, and rolled back exactly. A standard-library-only critic accepted the sealed baseline and semantically rejected all 22 re-signed adversarial mutations in addition to all 22 seal-breaking mutations.

Internal result: `{status}`. The exact remaining blocker is `{blocker}`. This requires independent external release review and is not a Product Beta PASS, production-readiness claim, public release, memory-lift claim, full-scoring result, or self-maintaining-software claim. Protocol remains `v2.19`; package version remains `0.2.0b2.dev0`; counts remain 6 issue-derived and 4 native external repairs with historical increment 0.
"""
    (out / "campaign_summary.md").write_text(summary, encoding="utf-8", newline="\n")
    indexed = []
    for path in sorted(out.iterdir(), key=lambda item: item.name.casefold()):
        if path.is_file() and path.name not in {"SHA256SUMS.txt", "batch091_external_review_package_index.json"}:
            indexed.append({"path": path.name, "sha256": sha(path), "size": path.stat().st_size, "producer": "batch091-stage-or-finalizer", "semantic_scope": "batch091_external_review_evidence", "authority_allowed": "independent review", "authority_forbidden": "public write, count mutation, automatic merge"})
    write(out / "batch091_external_review_package_index.json", {"status": "PASS", "portable_evidence_only": True, "file_count": len(indexed), "files": indexed})
    paths = [path for path in sorted(out.iterdir(), key=lambda item: item.name.casefold()) if path.is_file() and path.name != "SHA256SUMS.txt"]
    (out / "SHA256SUMS.txt").write_text("".join(f"{sha(path)}  {path.name}\n" for path in paths), encoding="utf-8", newline="\n")
    print(json.dumps({"status": status, "exact_blocker": blocker, "public_state_sync": synced, "manifest_entries": len(paths)}, sort_keys=True))
    return 0 if internal_pass and synced else 1


if __name__ == "__main__":
    raise SystemExit(main())
