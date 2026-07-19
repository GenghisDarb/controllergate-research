from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PARENT = "228e72533ebb6d70dc3094b5a4dd9512eb38dbc3"
STATUS = "BATCH098_PRE_HYBRID_EXECUTION_FAIL_EXPECTED"


FINDINGS = (
    ("HYB-001", "scripts/run_batch098_with_local_tld_sources.ps1", "provider map", "local Windows executable routing cannot establish frozen Linux parity", "replace primary execution with public exact-Linux provider evidence", "test_hybrid_mode_does_not_materialize_locally"),
    ("HYB-002", "scripts/run_batch098_with_local_tld_sources.ps1", "provider series", "major/minor matching omits platform parity", "bind implementation, microrelease, OS, architecture, ABI, SOABI, runner, and command", "test_windows_series_is_false_parity"),
    ("HYB-003", "scripts/run_batch098_with_local_tld_sources.ps1", "CG_PYTHON provider map", "provider mapping does not require exact microrelease", "require exact frozen microrelease verification", "test_provider_microrelease_exact"),
    ("HYB-004", "scripts/run_batch098_with_local_tld_sources.ps1", "default python", "default python is assumed to satisfy the 3.13 provider role", "measure and verify the exact executable identity", "test_default_python_requires_independent_measurement"),
    ("HYB-005", ".github/workflows/post_v2_37_hardening_batch098_causal_hypergraph_real_materialization_topology_probe_closure.yml", "tld_source_artifact_custody", "TLD custody is permanently disabled", "split public TLD-independent evidence from private TLD continuation", "test_public_decision_workflow_has_no_tld_dependency"),
    ("HYB-006", ".github/workflows/post_v2_37_hardening_batch098_causal_hypergraph_real_materialization_topology_probe_closure.yml", "materialization.needs", "public materialization depends on the skipped TLD job", "remove TLD from public decision-time dependencies", "test_public_materialization_is_reachable"),
    ("HYB-007", ".github/workflows/post_v2_37_hardening_batch098_causal_hypergraph_real_materialization_topology_probe_closure.yml", "materialization matrix", "Poetry is assigned to Windows despite the frozen Linux receipt", "run all eight frozen candidates on ubuntu-22.04", "test_poetry_requires_linux"),
    ("HYB-008", ".github/workflows/post_v2_37_hardening_batch098_causal_hypergraph_real_materialization_topology_probe_closure.yml", "setup-python", "provider requests use a version series rather than exact microreleases", "freeze and verify 3.7.17, 3.11.15, and 3.13.14", "test_exact_setup_python_versions"),
    ("HYB-009", ".github/workflows/post_v2_37_hardening_batch098_causal_hypergraph_real_materialization_topology_probe_closure.yml", "artifact boundary", "no public decision-time artifact supports later private continuation", "seal a public truth-blind pre-TLD evidence artifact", "test_public_decision_artifact_contract"),
    ("HYB-010", "scripts/run_batch098_with_local_tld_sources.ps1", "parameters", "local runner cannot consume public decision and truth-blind artifacts", "add exact artifact-ID hybrid continuation inputs", "test_hybrid_artifact_inputs"),
    ("HYB-011", "scripts/run_batch098_with_local_tld_sources.ps1", "scientific runner", "local runner rematerializes candidates instead of consuming frozen public evidence", "forbid local candidate execution in hybrid mode", "test_hybrid_local_execution_counts_zero"),
    ("HYB-012", "controllergate/topology/pipeline_v1.py", "compile_candidate_frame", "public frame binds a TLD identity before private join", "introduce PreTLDDecisionFrameV1 with pending private join", "test_pre_tld_frame_excludes_tld_identity"),
    ("HYB-013", "configs", "opaque plan registry", "no public-safe opaque private-TLD plan format exists", "compile only legal opaque probe identifiers and aggregate identities", "test_opaque_plan_schema"),
    ("HYB-014", "scripts", "private-source leakage audit", "no audit proves opaque plans exclude private TLD content", "scan plans against the sealed private corpus and forbidden classes", "test_opaque_plan_private_source_leakage"),
    ("HYB-015", "scripts", "plan timing", "no two-phase proof establishes plan freeze before execution", "bind plan commit and creation receipt before all planned probe operations", "test_opaque_plan_predates_execution"),
)


def parent_text(path: str) -> str:
    return subprocess.check_output(["git", "show", f"{PARENT}:{path}"], cwd=ROOT, text=True, encoding="utf-8")


def line_range(path: str, symbol: str) -> str:
    lines = parent_text(path).splitlines()
    matches = [index + 1 for index, line in enumerate(lines) if symbol.casefold() in line.casefold()]
    if not matches:
        return "1-1"
    first = matches[0]
    return f"{first}-{min(len(lines), first + 8)}"


def build_report() -> dict:
    rows = []
    for finding_id, path, symbol, risk, correction, test in FINDINGS:
        rows.append(
            {
                "finding_id": finding_id,
                "commit": PARENT,
                "path": path,
                "symbol": symbol,
                "line_range": line_range(path, symbol),
                "raw_evidence_sha256": hashlib.sha256(parent_text(path).encode("utf-8")).hexdigest(),
                "risk": risk,
                "required_correction": correction,
                "red_to_green_test": test,
            }
        )
    report = {
        "status": STATUS,
        "parent_head": PARENT,
        "finding_count": len(rows),
        "findings": rows,
        "authority_allowed": "expected-red implementation guidance",
        "authority_forbidden": ["provider parity", "scientific closure", "repair", "count", "release"],
    }
    report["report_hash"] = hashlib.sha256(json.dumps(report, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output")
    parser.add_argument("--verify", action="store_true")
    args = parser.parse_args()
    report = build_report()
    if args.output:
        output = Path(args.output)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    if args.verify and report["status"] != STATUS:
        return 1
    print(json.dumps({"status": report["status"], "finding_count": report["finding_count"], "report_hash": report["report_hash"]}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
