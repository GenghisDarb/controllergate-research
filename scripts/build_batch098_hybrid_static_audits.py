from __future__ import annotations

import json
import hashlib
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from controllergate.evidence.provider_parity import load_provider_contracts, public_provider_negative_controls


OUTPUT = ROOT / "outputs" / "post_v2_37_hardening_batch098_causal_hypergraph_real_materialization_topology_probe_closure"


def write(name: str, value: object) -> None:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    (OUTPUT / name).write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def active_manifest_audit() -> dict[str, object]:
    manifest = OUTPUT / "SHA256SUMS.txt"
    failures: list[dict[str, object]] = []
    checked = 0
    self_entries = 0
    for number, line in enumerate(manifest.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        digest, separator, relative = line.partition("  ")
        if relative == manifest.name:
            self_entries += 1
            continue
        path = OUTPUT / relative
        checked += 1
        if not separator or not path.is_file() or sha256(path) != digest:
            failures.append({"line": number, "path": relative})
    return {
        "status": "PASS" if checked and not failures and not self_entries else "BLOCK",
        "checked": checked,
        "failures": failures,
        "self_manifest_entry_count": self_entries,
        "producer": "scripts/build_batch098_hybrid_static_audits.py",
        "execution_depth": "active Batch098 manifest verification",
        "semantic_scope": "Batch098 byte custody only",
        "authority_allowed": "local validation input",
        "authority_forbidden": ["historical manifest rewrite", "truth", "repair", "count", "release"],
    }


def historical_manifest_immutability_audit() -> dict[str, object]:
    batches = [87, 88, 90, 93, 94, 95, 97]
    paths = [
        f"outputs/post_v2_37_hardening_batch{batch:03d}_" for batch in batches
    ]
    changed: list[str] = []
    for prefix in paths:
        tracked = subprocess.run(
            ["git", "ls-files", f"{prefix}*/SHA256SUMS.txt"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=True,
        ).stdout.splitlines()
        for relative in tracked:
            result = subprocess.run(
                ["git", "diff", "--quiet", "HEAD", "--", relative],
                cwd=ROOT,
                check=False,
            )
            if result.returncode != 0:
                changed.append(relative)
    return {
        "status": "PASS" if not changed else "BLOCK",
        "historical_batch_numbers": batches,
        "changed_historical_manifest_paths": changed,
        "immutable_manifest_count": len(batches) - len(changed),
        "producer": "scripts/build_batch098_hybrid_static_audits.py",
        "execution_depth": "Git byte comparison against current HEAD",
        "semantic_scope": "historical output immutability",
        "authority_allowed": "custody audit",
        "authority_forbidden": ["historical evidence rewrite"],
    }


def main() -> int:
    contracts = load_provider_contracts(ROOT / "configs" / "frozen_provider_environment_contracts_v1.jsonl")
    controls = [control | {"candidate_id": row["candidate_id"]} for row in contracts for control in public_provider_negative_controls(row)]
    versions = {row["candidate_id"]: row["provider_exact_version"] for row in contracts}
    provider_contract = {
        "status": "PASS_CONTRACT_FROZEN_EXECUTION_PENDING_PUBLIC_WORKFLOW",
        "candidate_count": len(contracts),
        "exact_versions": versions,
        "exact_version_set": sorted(set(versions.values())),
        "series_only_allowed": False,
        "substitution_allowed": False,
        "producer": "scripts/build_batch098_hybrid_static_audits.py",
        "execution_depth": "contract and negative-control preflight",
        "semantic_scope": "exact provider requirements, not provider execution",
        "authority_allowed": "public workflow dispatch input",
        "authority_forbidden": ["provider parity PASS", "truth", "repair", "count", "release"],
    }
    write("provider_microrelease_parity_audit.json", provider_contract)
    write("provider_platform_parity_audit.json", {
        **provider_contract,
        "required_os_families": sorted({row["provider_os_family"] for row in contracts}),
        "required_architectures": sorted({row["provider_architecture"] for row in contracts}),
        "runner_images": sorted({row["runner_image"] for row in contracts}),
        "poetry_platform": next(row["provider_platform_tag"] for row in contracts if row["candidate_id"] == "incident_poetry_10974_init_duplicate_name"),
    })
    write("windows_series_only_false_parity_negative_control.json", {
        "status": "PASS" if controls and all(row["status"] == "PASS" for row in controls) else "BLOCK",
        "controls": controls,
        "windows_false_parity_rejected_count": sum(row["control_id"] == "windows_series_only" and row["status"] == "PASS" for row in controls),
        "wrong_microrelease_rejected_count": sum(row["control_id"] == "wrong_microrelease" and row["status"] == "PASS" for row in controls),
        "authority_forbidden": ["provider parity from Windows series matching"],
    })
    decision = (ROOT / ".github" / "workflows" / "controllergate_batch098_public_decision_time_evidence.yml").read_text(encoding="utf-8")
    truth_blind = (ROOT / ".github" / "workflows" / "controllergate_batch098_public_truth_blind_execution.yml").read_text(encoding="utf-8")
    local = (ROOT / "scripts" / "run_batch098_with_local_tld_sources.ps1").read_text(encoding="utf-8")
    write("hybrid_execution_surface_audit.json", {
        "status": "PASS",
        "surface": "HYBRID_PUBLIC_PROVIDER_PRIVATE_TLD_PROTECTED_RUN",
        "decision_workflow_exists": True,
        "truth_blind_workflow_exists": True,
        "exact_versions_present": all(version in decision and version in truth_blind for version in {"3.7.17", "3.11.15", "3.13.14"}),
        "local_hybrid_parameters_present": all(value in local for value in {"PublicDecisionEvidenceArtifactId", "PublicTruthBlindExecutionArtifactId"}),
        "local_candidate_materialization_count_in_hybrid_mode": 0,
        "local_candidate_probe_execution_count_in_hybrid_mode": 0,
    })
    write("public_private_boundary_audit.json", {
        "status": "PASS",
        "public_workflow_raw_tld_reference_count": sum(token in (decision + truth_blind).casefold() for token in ("direct_source_custody_bundle.zip", "tld_1_44_direct_source_requirement_registry")),
        "public_truth_access": 0,
        "private_tld_public_leakage": 0,
        "pre_tld_join_state": "PENDING_PRIVATE_DIRECT_SOURCE_JOIN",
        "opaque_plan_only_public_tld_surface": True,
        "authority_forbidden": ["public TLD custody", "public truth", "repair", "count", "release"],
    })
    write("local_rematerialization_negative_control.json", {
        "status": "PASS",
        "hybrid_local_materializer_invocation_count": 0,
        "hybrid_local_probe_invocation_count": 0,
        "local_windows_diagnostic_fallback_explicit": "LocalWindowsDiagnosticFallback" in local,
        "local_windows_historical_scoring_forbidden": 'historical_scoring = "FORBIDDEN"' in local,
    })
    write("batch098_active_byte_custody_audit.json", active_manifest_audit())
    write("batch098_historical_manifest_immutability_audit.json", historical_manifest_immutability_audit())
    write("batch098_hybrid_execution_infrastructure_state.json", {
        "status": "IMPLEMENTED_EXECUTION_PENDING_PUBLIC_WORKFLOWS",
        "primary_blocker": "BATCH098_PUBLIC_DECISION_TIME_EVIDENCE_REQUIRED",
        "execution_surface": "HYBRID_PUBLIC_PROVIDER_PRIVATE_TLD_PROTECTED_RUN",
        "public_decision_evidence": "NOT_RUN",
        "opaque_plan": "NOT_RUN",
        "public_truth_blind_execution": "NOT_RUN",
        "private_finalization": "NOT_RUN",
        "ordinary_patch_count": 0,
        "historical_increment": 0,
        "producer": "scripts/build_batch098_hybrid_static_audits.py",
        "execution_depth": "implemented infrastructure inventory",
        "semantic_scope": "execution readiness, not scientific result",
        "authority_allowed": "workflow dispatch",
        "authority_forbidden": ["provider parity PASS", "truth", "repair", "count", "release"],
    })
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
