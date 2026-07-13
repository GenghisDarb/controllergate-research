from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from controllergate.core.batch075_provider_harness_amds_memory_wave1a import BATCH, EXPECTED_SHA, EXPECTED_SIZE, REVIEW, REJECTED
from controllergate.core.evidence import hash_record

OUT = ROOT / "outputs" / BATCH


def load(name: str) -> dict:
    return json.loads((OUT / name).read_text(encoding="utf-8"))


def expect(errors: list[str], condition: bool, label: str) -> None:
    if not condition:
        errors.append(label)


def manifest_valid() -> tuple[bool, int]:
    path = OUT / "SHA256SUMS.txt"
    if not path.is_file():
        return False, 0
    checked = 0
    for line in path.read_text(encoding="utf-8").splitlines():
        parts = line.split(maxsplit=1)
        if len(parts) != 2:
            return False, checked
        digest, relative = parts
        target = OUT / relative.strip().lstrip("*")
        if not target.is_file() or hashlib.sha256(target.read_bytes()).hexdigest() != digest:
            return False, checked
        checked += 1
    return checked > 0, checked


def event_chain_valid(path: Path) -> bool:
    parent = "0" * 64
    if not path.is_file():
        return False
    for line in path.read_text(encoding="utf-8").splitlines():
        row = json.loads(line)
        supplied = row.pop("event_hash", None)
        if row.get("parent_event_hash") != parent or supplied != hash_record(row):
            return False
        parent = str(supplied)
    return parent != "0" * 64


def main() -> int:
    errors: list[str] = []
    required = {
        "batch074_artifact_ingest.json", "batch074_state_preservation.json", "batch074_claim_boundary_preservation.json",
        "batch074_static_handoff_preservation.json", "batch075_interrupted_worktree_reconciliation.json",
        "provider_harness_v2_policy.json", "provider_workspace_path_audit_batch075.json",
        "provider_strategy_registry_batch075.json", "provider_lock_version_trace_batch075.jsonl",
        "provider_harness_completion_decision.json", "batch075_manual_review_decisions.json",
        "batch075_candidate_frame.json", "batch075_candidate_frame_freeze.json",
        "batch075_candidate_evidence_firewall.json", "batch075_routing_memory_snapshot.json",
        "batch075_candidate_memory_views.jsonl", "batch075_memory_exclusion_audit.json",
        "cognicore_admission_decision.json", "hordeforge_admission_decision.json",
        "batch075_admitted_cohort_freeze.json", "batch075_diagnostic_arm_summary.json",
        "batch075_arm_state_custody.json", "batch075_fourteen_contact_evidence.json",
        "batch075_blinded_ground_truth.json", "batch075_wave1a_metrics.json",
        "batch075_event_chain_audit.json", "batch075_checkpoint_resume_audit.json",
        "batch075_resource_and_download_budget_audit.json", "batch075_authoritative_repair_decision.json",
        "batch075_completion_decisions.json", "batch075_final_decision.json", "batch075_capability_depth.json",
        "batch075_summary.md", "SHA256SUMS.txt",
    }
    missing = sorted(name for name in required if not (OUT / name).is_file())
    if missing:
        errors.append("missing:" + ",".join(missing))
        print("Batch075 provider harness and Wave 1A audit: FAIL")
        print("errors:", ", ".join(errors))
        return 1

    valid_manifest, manifest_count = manifest_valid()
    expect(errors, valid_manifest and manifest_count >= 60, "manifest")

    ingest = load("batch074_artifact_ingest.json")
    expect(errors, ingest.get("status") == "PASS", "batch074_ingest")
    expect(errors, ingest.get("observed_size_bytes") == EXPECTED_SIZE and ingest.get("observed_sha256") == EXPECTED_SHA, "batch074_identity")
    expect(errors, ingest.get("file_count") == 69, "batch074_file_count")
    expect(errors, ingest.get("outer_manifest", {}).get("checked") == 68, "batch074_outer_manifest")
    expect(errors, ingest.get("batch073_manifest", {}).get("checked") == 41, "batch073_manifest")
    expect(errors, ingest.get("batch074_manifest", {}).get("checked") == 16, "batch074_manifest")
    entry = ingest.get("entry_audit", {})
    expect(errors, all(entry.get(key) == 0 for key in ("unsafe_path_count", "duplicate_path_count", "pycache_payload_count", "pyc_payload_count", "nested_archive_or_cache_payload_count")), "batch074_path_custody")

    preserved = load("batch074_state_preservation.json")
    claims = load("batch074_claim_boundary_preservation.json")
    expect(errors, preserved.get("COUNT_5_HARDENING") == "PASS" and preserved.get("Batch073_cohort") == "EXECUTED_EMPTY_COHORT", "prior_state")
    expect(errors, claims.get("validated_protocol") == "v2.19" and claims.get("issue_derived_repair_count") == 5 and claims.get("native_external_repair_count") == 4, "prior_claims")

    review = load("batch075_manual_review_decisions.json")
    expected_ids = [item["candidate_id"] for item in REVIEW]
    expect(errors, review.get("recorded_before_execution") is True and review.get("candidate_order") == expected_ids, "manual_frame")
    expect(errors, review.get("rejected", {}).get("candidate_id") == REJECTED["candidate_id"] and review.get("rejected", {}).get("executed") is False, "obsidian_exclusion")
    firewall = load("batch075_candidate_evidence_firewall.json")
    expect(errors, firewall.get("status") == "PASS" and firewall.get("issue_comments_consumed") is False and firewall.get("future_commits_used") is False and firewall.get("pull_requests_used") is False, "evidence_firewall")
    frame = load("batch075_candidate_frame_freeze.json")
    expect(errors, frame.get("candidate_count") == 2 and frame.get("candidate_order") == expected_ids and frame.get("replacement_allowed") is False, "candidate_freeze")
    expect(errors, [item.get("candidate_sha") for item in frame.get("candidates", [])] == [item["candidate_sha"] for item in REVIEW], "candidate_shas")

    workspace = load("provider_workspace_path_audit_batch075.json")
    expect(errors, workspace.get("status") == "PASS" and len(workspace.get("records", [])) == 2, "workspace_audit")
    for record in workspace.get("records", []):
        expect(errors, bool(re.fullmatch(r"[0-9a-f]{12}", str(record.get("candidate_key")))) and record.get("effective_projected_maximum_path_length", 9999) <= record.get("path_limit", 0), "short_workspace_path")
        expect(errors, record.get("candidate_id") not in str(record.get("candidate_root", "")), "full_id_in_runtime_path")

    strategies = load("provider_strategy_registry_batch075.json")
    expect(errors, strategies.get("status") == "PASS" and len(strategies.get("records", [])) == 2, "provider_strategies")
    by_id = {item["candidate_id"]: item for item in strategies.get("records", [])}
    cog = by_id.get(expected_ids[0], {})
    horde = by_id.get(expected_ids[1], {})
    expect(errors, {"server", "dev"}.issubset(set(cog.get("selected_optional_extras", []))), "cognicore_extras")
    expect(errors, cog.get("writable_build_copy") is True and cog.get("immutable_source_preserved") is True, "cognicore_build_copy")
    expect(errors, horde.get("strategy") in {"source_on_pythonpath", "build_project_wheel"}, "hordeforge_strategy")
    if horde.get("strategy") == "build_project_wheel":
        expect(errors, bool(horde.get("build_backend") or horde.get("legacy_build_method")) and horde.get("writable_build_copy") is True, "hordeforge_build_authority")

    completion = load("provider_harness_completion_decision.json")
    expect(errors, completion.get("status") == "PASS" and completion.get("expected_hashes_before_execution") is True and completion.get("same_store_duplicate_environments") is True, "provider_completion")
    for slug in ("cognicore", "hordeforge"):
        lock = load(f"{slug}_provider_lock.json")
        expect(errors, lock.get("status") == "PASS" and lock.get("expected_hashes_recorded_before_execution") is True and lock.get("artifact_count", 0) > 0, f"{slug}_provider_lock")
        for artifact in lock.get("artifacts", []):
            expect(errors, bool(re.fullmatch(r"[0-9a-f]{64}", str(artifact.get("sha256")))), f"{slug}_artifact_hash")

    admissions = [load("cognicore_admission_decision.json"), load("hordeforge_admission_decision.json")]
    for slug, decision in zip(("cognicore", "hordeforge"), admissions):
        expect(errors, decision.get("status") == "ADMITTED_DUPLICATE_FAILURE" and decision.get("duplicate_collection") is True and decision.get("duplicate_failure") is True, f"{slug}_admission")
        collections = [load(f"{slug}_collection_run_1.json"), load(f"{slug}_collection_run_2.json")]
        failures = [load(f"{slug}_failure_run_1.json"), load(f"{slug}_failure_run_2.json")]
        expect(errors, all(item.get("returncode") == 0 and item.get("node_count", 0) > 0 for item in collections) and collections[0]["node_ids"] == collections[1]["node_ids"], f"{slug}_duplicate_collection")
        expect(errors, all(item.get("returncode") != 0 for item in failures) and failures[0]["semantic_failure_signature"] == failures[1]["semantic_failure_signature"], f"{slug}_duplicate_failure")

    cohort = load("batch075_admitted_cohort_freeze.json")
    expect(errors, cohort.get("status") == "EXECUTED_COHORT_READY" and cohort.get("candidates") == expected_ids and cohort.get("frozen_after_all_dispositions") is True, "cohort_freeze")
    diagnostics = load("batch075_diagnostic_arm_summary.json")
    expect(errors, diagnostics.get("status") == "PASS" and diagnostics.get("arm_executions") == 8 and diagnostics.get("probe_executions") == 24, "diagnostic_execution")
    all_arms = [arm for record in diagnostics.get("records", []) for arm in record.get("arm_outputs", {}).values()]
    expect(errors, len(all_arms) == 8 and len({item.get("authorization_store_path") for item in all_arms}) == 8 and len({item.get("checkpoint_path") for item in all_arms}) == 8 and len({item.get("posterior_store") for item in all_arms}) == 8, "arm_isolation")
    expect(errors, all(item.get("observation_sharing") is False and item.get("patch_authority") is False for item in all_arms), "arm_sharing_or_patch")
    expect(errors, all(item.get("canonical_run_amds_active_loop") is True for item in all_arms if item.get("strategy") == "AMDS_ACTIVE"), "canonical_amds")
    expect(errors, all(item.get("canonical_run_amds_active_loop") is False for item in all_arms if item.get("strategy") == "FIXED_LEGAL_ORDER"), "fixed_order")

    contacts = load("batch075_fourteen_contact_evidence.json")
    expect(errors, contacts.get("status") == "PASS" and len(contacts.get("records", [])) == 2, "fourteen_contacts")
    for record in contacts.get("records", []):
        expect(errors, len(record.get("contacts", [])) == 14 and all(item.get("boolean_only_hash") is False and re.fullmatch(r"[0-9a-f]{64}", str(item.get("evidence_record_hash"))) for item in record.get("contacts", [])), "contact_hashes")

    custody = load("batch075_arm_state_custody.json")
    expect(errors, custody.get("status") == "PASS" and len(custody.get("records", [])) == 10, "arm_state_custody")
    for record in custody.get("records", []):
        for item in record.get("files", []):
            target = OUT / item["path"]
            expect(errors, target.is_file() and hashlib.sha256(target.read_bytes()).hexdigest() == item["sha256"], "arm_state_hash")
            if item["kind"] == "event_ledger":
                expect(errors, event_chain_valid(target), "event_chain")

    ground = load("batch075_blinded_ground_truth.json")
    expect(errors, ground.get("status") == "PASS" and ground.get("arm_outputs_sealed_first") is True and ground.get("adjudicator_blinded") is True and len(ground.get("records", [])) == 2, "blinded_ground_truth")
    expect(errors, all(item.get("classification") == "insufficient_evidence" for item in ground.get("records", [])), "ground_truth_classification")
    metrics = load("batch075_wave1a_metrics.json")
    expect(errors, metrics.get("status") == "PASS" and metrics.get("candidate_count") == 2 and metrics.get("AMDS_PROSPECTIVE_EFFECTIVENESS") == "NOT_ESTABLISHED" and metrics.get("memory_lift") == "not_demonstrated", "metrics")
    repair = load("batch075_authoritative_repair_decision.json")
    expect(errors, repair.get("attempts") == 0 and repair.get("successes") == 0 and repair.get("memory_disabled_lane") is True, "repair_boundary")
    final = load("batch075_final_decision.json")
    expect(errors, final.get("validated_protocol") == "v2.19" and final.get("issue_derived_repair_count") == 5 and final.get("native_external_repair_count") == 4, "final_counts")
    expect(errors, final.get("AMDS_PROSPECTIVE_EFFECTIVENESS") == "NOT_ESTABLISHED" and final.get("memory_lift") == "not_demonstrated" and final.get("self_maintaining_software") == "false/not_demonstrated", "final_claim_boundary")

    source = (ROOT / "controllergate/intake/admission_executor.py").read_text(encoding="utf-8")
    expect(errors, "run_amds_active_loop" in source and "--network" not in source.split("def intake_duplicate_replay", 1)[1].split("def intake_amds_board", 1)[0].replace('"--network", "none"', ""), "runtime_source_guard")
    expect(errors, "git reset --hard" not in source and "git clean" not in source, "destructive_git")

    if errors:
        print("Batch075 provider harness and Wave 1A audit: FAIL")
        print("errors:", ", ".join(errors))
        return 1
    print(f"Batch075 provider harness and Wave 1A audit: PASS ({manifest_count} manifest entries)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
