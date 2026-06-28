from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from controllergate.core.audit import require_files
from controllergate.core.manifests import verify_manifest
from controllergate.core.state import distinguish_status


LANE_DIR = Path("outputs/v2_37_core_consolidation")
BATCH_DIR = Path("outputs/clean_replication_batch_001")


REQUIRED_LANE_FILES = [
    "consolidated_state_v2_37.json",
    "campaign_summary.md",
    "v2_36_official_artifact_verification.json",
    "core_gate_library_status.json",
    "unit_test_results.json",
    "reusable_workflow_status.json",
    "current_protocol_adapter_status.json",
    "consolidated_state_format_status.json",
    "historical_lane_preservation_status.json",
    "version_sprawl_stop_policy.json",
    "public_docs_status.json",
    "public_release_readiness_audit_v2_37.json",
    "v3_0_readiness_scorecard.json",
    "claim_boundary_v2_37.json",
    "SHA256SUMS.txt",
]

REQUIRED_BATCH_FILES = [
    "consolidated_state_clean_replication_batch_001.json",
    "campaign_summary.md",
    "candidate_verification_attempts.json",
    "candidate_rejection_ledger.json",
    "verified_candidates.json",
    "repair_attempts.json",
    "repair_successes.json",
    "matched_null_results.json",
    "memory_lift_evaluation.json",
    "claim_boundary.json",
    "SHA256SUMS.txt",
]


def read_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def blocked_terms() -> list[str]:
    return [
        "bio" + "logical",
        "chromo" + "somal",
        "TO" + "RUS",
        "TL" + "D",
        "A" + "GI",
        "observer" + "-state",
        "recursion" + "-constant",
        "meta" + "phorical",
    ]


def fail(message: str) -> int:
    print(f"FAIL: {message}")
    return 1


def command_passes(command: list[str]) -> bool:
    completed = subprocess.run(command, text=True, capture_output=True)
    if completed.returncode != 0:
        print(completed.stdout)
        print(completed.stderr)
    return completed.returncode == 0


def audit_public_files() -> list[str]:
    files = [
        Path("README.md"),
        Path("docs/architecture.md"),
        Path("docs/getting_started.md"),
        Path("docs/current_protocol.md"),
        Path("docs/claim_boundaries.md"),
        Path("docs/memory_lift_definition.md"),
        Path("docs/public_release_readiness.md"),
        Path("docs/replication_protocol.md"),
        Path("docs/glossary.md"),
        Path("controllergate_v1_7_beta/reports/critic_review_package/shareable_summary.md"),
        Path(".github/workflows/README.md"),
        Path(".github/workflows/controllergate_reusable_lane.yml"),
        Path(".github/workflows/v2_37_core_consolidation_and_clean_replication.yml"),
    ]
    terms = blocked_terms()
    hits: list[str] = []
    for path in files:
        if not path.is_file():
            hits.append(f"missing:{path.as_posix()}")
            continue
        text = path.read_text(encoding="utf-8")
        for term in terms:
            if term in text:
                hits.append(f"{path.as_posix()}:{term}")
    return hits


def main() -> int:
    missing_lane = require_files(LANE_DIR, REQUIRED_LANE_FILES)
    missing_batch = require_files(BATCH_DIR, REQUIRED_BATCH_FILES)
    if missing_lane or missing_batch:
        return fail(f"missing outputs lane={missing_lane} batch={missing_batch}")

    if verify_manifest(LANE_DIR)["status"] != "PASS":
        return fail("v2.37 manifest mismatch")
    if verify_manifest(BATCH_DIR)["status"] != "PASS":
        return fail("clean batch manifest mismatch")

    v2_36 = read_json(LANE_DIR / "v2_36_official_artifact_verification.json")
    if v2_36.get("status") != "PASS" or v2_36.get("zip_sha256") != "b15ed6f7646824dfcb6973711c4906f23d91d41d773efa759f7f02ae72609972":
        return fail("v2.36 official ingest record invalid")

    core_status = read_json(LANE_DIR / "core_gate_library_status.json")
    tests = read_json(LANE_DIR / "unit_test_results.json")
    if core_status.get("status") != "PASS" or tests.get("status") != "PASS":
        return fail("core gate library or unit tests failed")
    if not command_passes([sys.executable, "-m", "pytest", "tests/core", "-q"]):
        return fail("core unit tests fail on audit replay")

    required_repo_files = [
        "controllergate/protocols/clean_replication.py",
        "scripts/controllergate_clean_repair.py",
        "scripts/audit_clean_replication_protocol.py",
        ".github/workflows/controllergate_reusable_lane.yml",
        ".github/workflows/README.md",
        "docs/consolidated_state_format.md",
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
    missing_repo = require_files(Path("."), required_repo_files)
    if missing_repo:
        return fail(f"missing repo files: {missing_repo}")

    if not command_passes([sys.executable, "scripts/audit_clean_replication_protocol.py"]):
        return fail("clean protocol adapter audit failed")
    if not command_passes([sys.executable, "scripts/validate_external_candidate_registry.py"]):
        return fail("external candidate registry audit failed")

    state = read_json(LANE_DIR / "consolidated_state_v2_37.json")
    required_state = [
        "lane_id",
        "lane_type",
        "status",
        "exact_blocker",
        "current_protocol_version",
        "artifact_ingest",
        "byte_custody",
        "registry_status",
        "candidate_counts",
        "acquisition_status",
        "repair_status",
        "matched_null_status",
        "public_language_status",
        "claim_boundary_status",
        "raw_evidence_files",
        "diagnostic_files",
        "deprecated_files",
        "next_actions",
    ]
    missing_state = [field for field in required_state if field not in state]
    if missing_state:
        return fail(f"consolidated state missing fields: {missing_state}")
    for value in ["PASS", "BLOCKED", "NOT_RUN", "NOT_APPLICABLE", "FAILED"]:
        if not distinguish_status(value):
            return fail(f"status value not distinguished: {value}")

    claim = read_json(LANE_DIR / "claim_boundary_v2_37.json")
    if claim.get("current_protocol_version") != "v2.13":
        return fail("current protocol changed")
    if claim.get("full_scoring") != "NOT_RUN/disallowed":
        return fail("full scoring boundary changed")
    if claim.get("memory_lift") != "undemonstrated":
        return fail("memory lift overclaim")
    if claim.get("self_maintaining_software") != "false/not_demonstrated":
        return fail("self-maintaining software overclaim")

    batch = read_json(BATCH_DIR / "consolidated_state_clean_replication_batch_001.json")
    if batch.get("status") != "BLOCKED" or batch.get("exact_blocker") != "no_additional_external_repairs_acquired":
        return fail("clean replication batch blocker is not honest")

    readiness = read_json(LANE_DIR / "public_release_readiness_audit_v2_37.json")
    if readiness.get("status") not in {"not_ready", "pre_alpha_research_archive_ready", "technical_validation_release_ready"}:
        return fail("public readiness status invalid")
    if readiness.get("status") == "technical_validation_release_ready":
        return fail("technical validation readiness is not justified")

    public_hits = audit_public_files()
    if public_hits:
        return fail(f"public language audit failed: {public_hits}")

    print("v2.37 core consolidation and clean replication audit PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
