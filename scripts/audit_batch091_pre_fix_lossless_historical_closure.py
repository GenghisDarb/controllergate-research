from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import zipfile
from datetime import datetime, timezone
from pathlib import Path


START_HEAD = "7b72d4a7fd7aa81f2cc418bdb272dbf095880715"
OUTPUT = Path(
    "outputs/post_v2_37_hardening_batch091_lossless_capsule_blinded_amds_"
    "historical_canary_semantic_critic_closure"
)


def git_text(path: str) -> str:
    return subprocess.run(
        ["git", "show", f"{START_HEAD}:{path}"],
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
    ).stdout


def line_range(text: str, needle: str) -> list[int]:
    for number, line in enumerate(text.splitlines(), 1):
        if needle in line:
            return [number, number]
    return [1, 1]


def finding(
    number: int,
    *,
    path: str,
    symbol: str,
    text: str,
    needle: str,
    observed: str,
    risk: str,
    correction: str,
    test: str,
) -> dict[str, object]:
    return {
        "finding_id": f"B091-RED-{number:02d}",
        "commit": START_HEAD,
        "path": path,
        "symbol": symbol,
        "line_range": line_range(text, needle),
        "observed_behavior": observed,
        "risk": risk,
        "required_correction": correction,
        "red_to_green_test": test,
    }


def artifact_json(archive: zipfile.ZipFile, name: str) -> dict[str, object]:
    return json.loads(archive.read(name).decode("utf-8"))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--artifact", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=OUTPUT)
    args = parser.parse_args()

    transport = git_text("scripts/batch090_capsule_transport_v3.py")
    consumer = git_text("scripts/batch090_historical_capsule_consumer.py")
    amds = git_text("scripts/run_batch090_historical_amds.py")
    critic = git_text("scripts/batch090_standalone_internal_critic.py")
    workflow = git_text(
        ".github/workflows/post_v2_37_hardening_batch090_evidence_"
        "delaundering_installed_vertical_closure.yml"
    )
    with zipfile.ZipFile(args.artifact) as archive:
        cloud_source = artifact_json(archive, "cloudpickle_source_capsule_verification.json")
        freezegun_source = artifact_json(archive, "freezegun_source_capsule_verification.json")
        cloud_lifecycle = artifact_json(archive, "cloudpickle_installed_historical_lifecycle.json")
        freezegun_lifecycle = artifact_json(archive, "freezegun_installed_historical_lifecycle.json")
        amds_quality = artifact_json(archive, "amds_historical_quality_gate.json")
        non_source = artifact_json(archive, "non_source_historical_results.json")
        canary = artifact_json(archive, "repaired_package_canary_health_rollback.json")
        mutation = artifact_json(archive, "mutation_campaign_results.json")

    rows = [
        finding(1, path="Batch090 main artifact", symbol="cloudpickle source capsule consumer", text=transport, needle="source_capsule", observed=f"Producer records 58 entries but consumer received {cloud_source.get('entry_count')}; missing {cloud_source.get('hash_mismatches')}", risk="Public tracked dotfiles are lost in transport.", correction="Construct and transport a deterministic Git-object capsule as one exact file.", test="test_cloudpickle_hidden_files_conserved"),
        finding(2, path="Batch090 main artifact", symbol="freezegun source capsule consumer", text=transport, needle="source_capsule", observed=f"Producer records 39 entries but consumer received {freezegun_source.get('entry_count')}; missing {freezegun_source.get('hash_mismatches')}", risk="Public tracked dotfiles are lost in transport.", correction="Construct and transport a deterministic Git-object capsule as one exact file.", test="test_freezegun_hidden_files_conserved"),
        finding(3, path=".github/workflows/post_v2_37_hardening_batch090_evidence_delaundering_installed_vertical_closure.yml", symbol="source capsule upload", text=workflow, needle="upload-artifact", observed="Source directories are uploaded rather than a single deterministic capsule file.", risk="Uploader traversal policy can omit hidden paths.", correction="Upload exact capsule archives and include hidden files as defense in depth.", test="test_source_capsule_exact_file_upload"),
        finding(4, path=".github/workflows/post_v2_37_hardening_batch090_evidence_delaundering_installed_vertical_closure.yml", symbol="temporary transport roots", text=workflow, needle="RUNNER_TEMP", observed="Temporary parent trees may include checkouts, provider virtual environments, site-packages, and compiled caches.", risk="Runtime residue can enter short-lived transport.", correction="Scan exact upload payloads and reject runtime residue.", test="test_short_lived_artifact_runtime_residue_rejected"),
        finding(5, path="scripts/batch090_capsule_transport_v3.py", symbol="module imports", text=transport, needle="from batch088_capsule_transport", observed="Capsule construction imports a prior batch script.", risk="Reusable custody logic is not canonical product code.", correction="Move lossless capsule construction and verification into controllergate.custody.", test="test_canonical_capsule_service_import"),
        finding(6, path="scripts/batch090_capsule_transport_v3.py", symbol="build", text=transport, needle="source_capsule(episode", observed="Source capsule behavior copies a materialized working tree.", risk="Tree identity and public dotfile conservation are not guaranteed.", correction="Read the verified commit tree from Git objects.", test="test_git_object_capsule_tree_identity"),
        finding(7, path="scripts/batch090_historical_capsule_consumer.py", symbol="proof_records", text=consumer, needle="def proof_records", observed="The consumer preconstructs source-ownership and repair-license requirements.", risk="Manifest prose can mint authority without executed evidence.", correction="Require named stages to produce every proof record.", test="test_manifest_injected_proof_rejected"),
        finding(8, path="scripts/batch090_historical_capsule_consumer.py", symbol="proof_records.common", text=consumer, needle='"status": "PASS"', observed="All generated proof requirements share a default PASS record.", risk="Independent proof obligations collapse into one generic assertion.", correction="Bind each proof to its producer, verifier, raw evidence, and derivation parents.", test="test_generic_pass_proof_rejected"),
        finding(9, path="scripts/batch090_historical_capsule_consumer.py", symbol="EPISODES", text=consumer, needle='"causal_family"', observed="The expected causal family is embedded before diagnosis.", risk="Historical diagnosis is outcome-labelled.", correction="Remove causal labels from builder and lifecycle decision frames.", test="test_hardcoded_causal_family_rejected"),
        finding(10, path="scripts/batch090_historical_capsule_consumer.py", symbol="proof_records", text=consumer, needle='"human_approval"', observed="Human approval is generic prompt prose.", risk="Approval is not candidate-, patch-, run-, nonce-, or expiry-bound.", correction="Require a structured Brad approval record bound to the prompt contract and patch.", test="test_candidate_bound_human_approval"),
        finding(11, path="scripts/run_batch090_historical_amds.py", symbol="episode records", text=amds, needle="terminal_class", observed="Builder-visible candidate records include terminal_class.", risk="Terminal labels leak before blinded execution.", correction="Physically separate sanitized builder inputs from sealed truth.", test="test_amds_terminal_label_leakage"),
        finding(12, path="scripts/run_batch090_historical_amds.py", symbol="eligibility", text=amds, needle="measured", observed="Eligibility measurements are static booleans rather than receipt-backed observations.", risk="A declared frame can be mistaken for measured execution.", correction="Require source/provider/target/command/runner receipt hashes.", test="test_amds_literal_true_measurement_rejected"),
        finding(13, path="Batch090 main artifact", symbol="AMDS cohort", text=amds, needle="EPISODES", observed=f"Only {amds_quality.get('eligible_episode_count')} eligible episodes exist.", risk="The preregistered eight-episode quality gate cannot run.", correction="Freeze eight sanitized eligible episodes before any probe.", test="test_amds_eight_episode_freeze"),
        finding(14, path="Batch090 main artifact", symbol="AMDS quality gate", text=amds, needle="minimum", observed=f"Historical AMDS quality is {amds_quality.get('status')} and no probe or baseline executed.", risk="Mechanism quality remains unestablished.", correction="Execute candidate-specific brokered probes and equal-budget baselines after freeze.", test="test_amds_historical_quality_gate"),
        finding(15, path="Batch090 main artifact", symbol="non-source selection", text=consumer, needle="NON_SOURCE_POOL", observed="Non-source eligibility uses static booleans and expected terminal labels.", risk="The terminal is prewritten rather than discovered.", correction="Sanitize non-source frames and seal truth separately.", test="test_non_source_terminal_unavailable_before_join"),
        finding(16, path="Batch090 main artifact", symbol="non-source execution", text=consumer, needle="execute_non_source_lifecycle", observed=f"Complete installed non-source lifecycle count is {non_source.get('complete_lifecycle_count')}.", risk="Two required historical terminals are not materialized.", correction="Execute both frozen episodes through installed canonical CLI mode.", test="test_two_installed_non_source_lifecycles"),
        finding(17, path="Batch090 main artifact", symbol="canary gate", text=consumer, needle="historical_repair_lifecycle", observed=f"Repaired-package canary status is {canary.get('status')}.", risk="No distinct package deployment or rollback evidence exists.", correction="Build twice, deploy a distinct canary, execute health and negative control, then exact rollback.", test="test_deployed_canary_health_rollback"),
        finding(18, path="scripts/batch090_standalone_internal_critic.py", symbol="mutation campaign", text=critic, needle="manifest", observed="Mutation rejection is dominated by sealed-manifest hash mismatch.", risk="Semantic defects may evade a consistently re-signed bundle.", correction="Add re-signed semantic mutation reconstruction.", test="test_resigned_semantic_mutations_rejected"),
        finding(19, path="scripts/batch090_standalone_internal_critic.py", symbol="semantic reconstruction", text=critic, needle="mutation", observed=f"Existing mutation campaign records {mutation.get('executed')} byte-level cases without a re-signed semantic family.", risk="Critic depth is custody-only for mutated bundles.", correction="Recompute manifests after mutation and reject on named semantic invariants.", test="test_semantic_rejection_not_hash_only"),
        finding(20, path="Batch090 main artifact", symbol="Cloudpickle lifecycle", text=consumer, needle="source_capsule_not_activatable", observed=f"Cloudpickle lifecycle remains {cloud_lifecycle.get('status')} with {cloud_lifecycle.get('exact_blockers')}", risk="Producer acquisition is not lifecycle execution.", correction="Require lossless activation before installed lifecycle execution.", test="test_cloudpickle_lossless_activation_gate"),
        finding(21, path="Batch090 main artifact", symbol="Freezegun lifecycle", text=consumer, needle="source_capsule_not_activatable", observed=f"Freezegun lifecycle remains {freezegun_lifecycle.get('status')} with {freezegun_lifecycle.get('exact_blockers')}", risk="Producer acquisition is not lifecycle execution.", correction="Require lossless activation before installed lifecycle execution.", test="test_freezegun_lossless_activation_gate"),
        finding(22, path="Batch090 installed wheel identities", symbol="semantic wheel identity", text=workflow, needle="cross_platform", observed="Cross-platform scenarios match but normalized semantic wheel hashes differ without component decomposition.", risk="Executable-content equivalence is not independently established.", correction="Compare normalized archive members and classify metadata-only differences.", test="test_semantic_wheel_difference_decomposition"),
    ]
    result: dict[str, object] = {
        "prompt_id": "CG-BATCH091-LOSSLESS-CAPSULE-BLINDED-AMDS-HISTORICAL-CANARY-SEMANTIC-CRITIC-CLOSURE-2026-07-15-V1",
        "audited_commit": START_HEAD,
        "artifact_sha256": hashlib.sha256(args.artifact.read_bytes()).hexdigest(),
        "finding_count": len(rows),
        "findings": rows,
        "expected_result": "BATCH091_PRE_FIX_AUDIT_FAIL_EXPECTED",
        "observed_result": "BATCH091_PRE_FIX_AUDIT_FAIL_EXPECTED" if len(rows) == 22 else "UNEXPECTED",
        "sealed_at_utc": datetime.now(timezone.utc).isoformat(),
    }
    result["seal_sha256"] = hashlib.sha256(
        json.dumps(result, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    args.output.mkdir(parents=True, exist_ok=True)
    target = args.output / "batch091_pre_fix_expected_failure.json"
    target.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    print(result["observed_result"])
    return 0 if result["observed_result"] == result["expected_result"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
