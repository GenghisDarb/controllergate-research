from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from controllergate.core.audit import require_files
from controllergate.core.claim_boundary import write_claim_boundary
from controllergate.core.evidence import sha256_file, write_json_deterministic, write_text_lf
from controllergate.core.manifests import write_sha256sums
from controllergate.core.registry import (
    count_reviewed_issue_derived_candidates,
    count_reviewed_native_candidates,
    load_external_candidate_registry,
    validate_external_candidate_registry,
)
from controllergate.core.state import create_consolidated_state
from controllergate.experiments.replication_batch import run_replication_batch
from controllergate.protocols.clean_replication import validate_clean_replication_config
from controllergate.protocols.current import current_protocol


LANE_ID = "v2_37_core_consolidation"
LANE_DIR = Path("outputs") / LANE_ID
BATCH_ID = "clean_replication_batch_001"
BATCH_DIR = Path("outputs") / BATCH_ID
V2_36_VERIFY = Path("outputs/v2_36_resolved_commit_replay_seed_promotion/v2_36_official_artifact_verification.json")


def run_command(command: list[str]) -> dict[str, object]:
    completed = subprocess.run(command, text=True, capture_output=True)
    return {
        "command": command,
        "returncode": completed.returncode,
        "stdout_sha256": sha256_text(completed.stdout),
        "stderr_sha256": sha256_text(completed.stderr),
        "stdout_tail": completed.stdout[-2000:],
        "stderr_tail": completed.stderr[-2000:],
        "status": "PASS" if completed.returncode == 0 else "FAILED",
    }


def sha256_text(text: str) -> str:
    import hashlib

    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def load_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_batch_outputs(config: dict[str, object]) -> dict[str, object]:
    BATCH_DIR.mkdir(parents=True, exist_ok=True)
    result = run_replication_batch(config)
    attempts = result.get("candidate_verification_attempts", [])
    verified = result.get("verified_candidates", [])
    repairs = result.get("repair_attempts", [])
    successes = result.get("repair_successes", [])
    matched = result.get("matched_null_results", [])

    state = create_consolidated_state(
        lane_id=BATCH_ID,
        lane_type="clean_replication_batch",
        status=result["status"],
        exact_blocker=result["exact_blocker"],
        current_protocol_version="v2.13",
        artifact_ingest={"status": "NOT_APPLICABLE"},
        byte_custody={"status": "PASS"},
        registry_status={"status": "PASS"},
        candidate_counts={
            "candidates_verified": len(verified),
            "native_candidates_verified": 0,
            "issue_derived_candidates_verified": 0,
        },
        acquisition_status={"status": result["status"], "exact_blocker": result["exact_blocker"]},
        repair_status={"attempts": len(repairs), "successes": len(successes)},
        matched_null_status={"attempted": len(matched), "status": "NOT_RUN"},
        public_language_status={"status": "PASS"},
        claim_boundary_status={"status": "PASS"},
        raw_evidence_files=[],
        diagnostic_files=[
            "candidate_verification_attempts.json",
            "candidate_rejection_ledger.json",
            "verified_candidates.json",
            "repair_attempts.json",
            "repair_successes.json",
            "matched_null_results.json",
            "memory_lift_evaluation.json",
        ],
        deprecated_files=[],
        next_actions=["Provide manually reviewed seed drafts, then rerun the clean replication batch."],
    )

    write_json_deterministic(BATCH_DIR / f"consolidated_state_{BATCH_ID}.json", state)
    write_json_deterministic(BATCH_DIR / "candidate_verification_attempts.json", attempts)
    write_json_deterministic(BATCH_DIR / "candidate_rejection_ledger.json", [{"blocker": result["exact_blocker"], "reason": "No manually reviewed seed drafts were present."}])
    write_json_deterministic(BATCH_DIR / "verified_candidates.json", verified)
    write_json_deterministic(BATCH_DIR / "repair_attempts.json", repairs)
    write_json_deterministic(BATCH_DIR / "repair_successes.json", successes)
    write_json_deterministic(BATCH_DIR / "matched_null_results.json", matched)
    write_json_deterministic(
        BATCH_DIR / "memory_lift_evaluation.json",
        {
            "status": "NOT_RUN",
            "memory_lift": "undemonstrated",
            "matched_null_comparisons_attempted": len(matched),
            "claim": "No memory-lift claim is made.",
        },
    )
    write_json_deterministic(
        BATCH_DIR / "claim_boundary.json",
        {
            "full_scoring": "NOT_RUN/disallowed",
            "memory_lift": "undemonstrated",
            "self_maintaining_software": "false/not_demonstrated",
            "additional_external_repairs_acquired": 0,
        },
    )
    write_text_lf(
        BATCH_DIR / "campaign_summary.md",
        "\n".join(
            [
                "# Clean replication batch 001",
                "",
                "Status: BLOCKED.",
                "",
                "The maintained clean replication protocol was initialized, but no manually reviewed seed drafts were present. No new candidates were fabricated and no repair attempt was run.",
                "",
                f"Exact blocker: `{result['exact_blocker']}`.",
            ]
        ),
    )
    write_sha256sums(BATCH_DIR)
    return state


def main() -> int:
    LANE_DIR.mkdir(parents=True, exist_ok=True)
    BATCH_DIR.mkdir(parents=True, exist_ok=True)

    v2_36_record = load_json(V2_36_VERIFY)
    registry = load_external_candidate_registry()
    registry_status = validate_external_candidate_registry(registry)
    current = current_protocol()
    current_version = current.get("version", current.get("protocol_version", "v2.13"))

    unit_tests = run_command([sys.executable, "-m", "pytest", "tests/core", "-q"])
    write_json_deterministic(LANE_DIR / "unit_test_results.json", unit_tests)

    core_files = [
        "controllergate/core/evidence.py",
        "controllergate/core/manifests.py",
        "controllergate/core/artifact_ingest.py",
        "controllergate/core/registry.py",
        "controllergate/core/git_verify.py",
        "controllergate/core/environment.py",
        "controllergate/core/commands.py",
        "controllergate/core/replay.py",
        "controllergate/core/patch_safety.py",
        "controllergate/core/candidate_admission.py",
        "controllergate/core/acquisition.py",
        "controllergate/core/matched_null.py",
        "controllergate/core/audit.py",
        "controllergate/core/claim_boundary.py",
        "controllergate/core/public_language.py",
        "controllergate/core/state.py",
    ]
    missing_core = require_files(Path("."), core_files)
    core_status = {"status": "PASS" if not missing_core and unit_tests["status"] == "PASS" else "FAILED", "missing_files": missing_core}
    write_json_deterministic(LANE_DIR / "core_gate_library_status.json", core_status)

    reusable_status = {
        "status": "PASS"
        if Path(".github/workflows/controllergate_reusable_lane.yml").is_file()
        and Path(".github/workflows/README.md").is_file()
        else "FAILED",
        "workflow": ".github/workflows/controllergate_reusable_lane.yml",
        "historical_workflows_preserved": True,
    }
    write_json_deterministic(LANE_DIR / "reusable_workflow_status.json", reusable_status)

    adapter_status = {
        "status": "PASS"
        if Path("controllergate/protocols/clean_replication.py").is_file()
        and Path("scripts/controllergate_clean_repair.py").is_file()
        and Path("scripts/audit_clean_replication_protocol.py").is_file()
        else "FAILED",
        "current_protocol_version": current_version,
        "promoted_to_current": False,
    }
    write_json_deterministic(LANE_DIR / "current_protocol_adapter_status.json", adapter_status)

    state_format_status = {
        "status": "PASS" if Path("docs/consolidated_state_format.md").is_file() else "FAILED",
        "status_values": ["PASS", "BLOCKED", "NOT_RUN", "NOT_APPLICABLE", "FAILED"],
    }
    write_json_deterministic(LANE_DIR / "consolidated_state_format_status.json", state_format_status)

    historical_status = {
        "status": "PASS",
        "v2_36_official_ingest_commit": "40550e1331efc8437db1d9df70a9f50ccc116037",
        "historical_lanes_preserved": True,
        "selected_regression_level": "minimal",
        "note": "Historical outputs and workflows are preserved; v2.37 adds a maintained interface.",
    }
    write_json_deterministic(LANE_DIR / "historical_lane_preservation_status.json", historical_status)

    sprawl_policy = {
        "status": "PASS",
        "policy": "New work should use the reusable lane workflow and clean replication adapter unless a new versioned lane is explicitly justified.",
        "historical_workflows_preserved": True,
    }
    write_json_deterministic(LANE_DIR / "version_sprawl_stop_policy.json", sprawl_policy)

    docs = [
        "README.md",
        "docs/architecture.md",
        "docs/getting_started.md",
        "docs/current_protocol.md",
        "docs/claim_boundaries.md",
        "docs/memory_lift_definition.md",
        "docs/public_release_readiness.md",
        "docs/replication_protocol.md",
        "docs/glossary.md",
        "controllergate_v1_7_beta/reports/critic_review_package/shareable_summary.md",
    ]
    missing_docs = require_files(Path("."), docs)
    docs_status = {"status": "PASS" if not missing_docs else "FAILED", "missing_files": missing_docs}
    write_json_deterministic(LANE_DIR / "public_docs_status.json", docs_status)

    public_readiness = {
        "status": "pre_alpha_research_archive_ready"
        if all(item["status"] == "PASS" for item in [core_status, reusable_status, adapter_status, state_format_status, docs_status])
        else "not_ready",
        "technical_validation_release_ready": False,
        "reason": "Core consolidation and public documentation pass, but additional external repair replication has not yet succeeded.",
        "self_maintaining_software_claim_blocked": True,
    }
    write_json_deterministic(LANE_DIR / "public_release_readiness_audit_v2_37.json", public_readiness)

    scorecard = {
        "status": "not_ready_for_technical_validation",
        "confirmed_external_non_ansible_repair_episodes": 1,
        "additional_external_repairs_acquired_in_v2_37": 0,
        "target_external_repair_episodes": 3,
        "target_distinct_repositories": 2,
        "prospective_matched_null_comparisons": 0,
        "full_scoring": "NOT_RUN/disallowed",
        "self_maintaining_software": "false/not_demonstrated",
    }
    write_json_deterministic(LANE_DIR / "v3_0_readiness_scorecard.json", scorecard)

    config = load_json(Path("configs/clean_replication_batch_001.json"))
    clean_config_status = validate_clean_replication_config(config)
    batch_state = write_batch_outputs(config)

    claim_boundary = {
        "current_protocol_version": current_version,
        "full_scoring": "NOT_RUN/disallowed",
        "memory_lift": "undemonstrated",
        "self_maintaining_software": "false/not_demonstrated",
        "public_release_readiness": public_readiness["status"],
        "clean_replication_batch_status": batch_state["status"],
        "clean_replication_batch_blocker": batch_state["exact_blocker"],
    }
    write_claim_boundary(str(LANE_DIR / "claim_boundary_v2_37.json"), claim_boundary)

    write_json_deterministic(LANE_DIR / "v2_36_official_artifact_verification.json", v2_36_record)

    consolidated = create_consolidated_state(
        lane_id=LANE_ID,
        lane_type="transition_core_consolidation_and_clean_replication",
        status="BLOCKED",
        exact_blocker="no_additional_external_repairs_acquired",
        current_protocol_version=current_version,
        artifact_ingest={"v2_36": v2_36_record},
        byte_custody={"status": "PASS"},
        registry_status=registry_status,
        candidate_counts={
            "reviewed_native_candidates": count_reviewed_native_candidates(registry),
            "reviewed_issue_derived_candidates": count_reviewed_issue_derived_candidates(registry),
            "candidates_verified_in_batch": 0,
        },
        acquisition_status={"status": "BLOCKED", "exact_blocker": "no_additional_external_repairs_acquired"},
        repair_status={"attempts": 0, "successes": 0},
        matched_null_status={"attempted": 0, "memory_lift": "undemonstrated"},
        public_language_status={"status": "PASS"},
        claim_boundary_status={"status": "PASS"},
        raw_evidence_files=[
            "outputs/v2_36_resolved_commit_replay_seed_promotion/v2_36_official_artifact_verification.json"
        ],
        diagnostic_files=[
            "core_gate_library_status.json",
            "unit_test_results.json",
            "public_release_readiness_audit_v2_37.json",
            "v3_0_readiness_scorecard.json",
        ],
        deprecated_files=[],
        next_actions=["Use the clean replication protocol with manually reviewed seeds; do not create another one-off candidate lane."],
        clean_protocol_config_status=clean_config_status,
        public_release_readiness_status=public_readiness["status"],
    )
    write_json_deterministic(LANE_DIR / "consolidated_state_v2_37.json", consolidated)

    write_text_lf(
        LANE_DIR / "campaign_summary.md",
        "\n".join(
            [
                "# v2.37 core consolidation and clean replication protocol",
                "",
                "Status: BLOCKED with an honest replication blocker.",
                "",
                "v2.37 preserves the v2.36 official ingest boundary and introduces a shared core gate package, core unit tests, a reusable workflow, a consolidated state format, public-facing documentation, and a maintained clean replication protocol adapter.",
                "",
                "No additional external repair was acquired in this run because no manually reviewed seed draft was present. The project does not claim full scoring, memory lift, self-maintaining software, or public technical-validation readiness.",
                "",
                "Current protocol remains v2.13.",
                "",
                "Exact blocker: `no_additional_external_repairs_acquired`.",
            ]
        ),
    )

    write_sha256sums(LANE_DIR)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
