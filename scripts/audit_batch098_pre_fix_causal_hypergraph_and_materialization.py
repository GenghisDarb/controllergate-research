from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "outputs" / "post_v2_37_hardening_batch098_causal_hypergraph_real_materialization_topology_probe_closure"
SEALED = OUTPUT / "batch098_pre_fix_causal_hypergraph_and_materialization_expected_failure.json"
RESULT = "BATCH098_PRE_FIX_CAUSAL_HYPERGRAPH_AND_MATERIALIZATION_FAIL_EXPECTED"


FINDINGS = (
    ("B098-001", "scripts/run_batch097_installed_candidate_lane.py", "main", "runpy checkout execution", "installed CLI owns candidate orchestration"),
    ("B098-002", "scripts/run_batch095_candidate_lane.py", "main", "checkout config and reusable lane behavior", "sealed installed CandidateExecutionContract"),
    ("B098-003", "scripts/run_batch095_candidate_lane.py", "LaneBroker.run", "project installation may run from acquired source", "six-compartment materializer"),
    ("B098-004", "scripts/run_batch095_candidate_lane.py", "tree_hash", "all-files hashing conflates residue and tracked mutation", "Git tracked integrity verifier"),
    ("B098-005", "scripts/run_batch095_candidate_lane.py", "LaneBroker.run", "post-operation hashes copy before values", "measured post-operation identities"),
    ("B098-006", "outputs/post_v2_37_hardening_batch097_evidence_reconstitution_real_repository_genome_topology_amds", "materialization outputs", "no path-level tracked diff for blocked lanes", "path mutation and residue ledgers"),
    ("B098-007", "scripts/run_batch095_candidate_lane.py", "derive_product", "marker conjunction derives semantic booleans", "typed product parsers"),
    ("B098-008", "scripts/run_batch095_candidate_lane.py", "derive_product", "configured values copied into evidence", "observed-value-only parser"),
    ("B098-009", "scripts/run_batch095_candidate_lane.py", "derive_product", "OpenBB word-count product parsing", "structured source-validated parser"),
    ("B098-010", "configs/batch093_amds_frozen_cohort.json", "controls", "generic controls lack issue-specific contracts", "candidate-specific controls"),
    ("B098-011", "configs/batch093_amds_frozen_cohort.json", "darker contract", "obsolete return-code 123 contract", "exit-1 traceback contract"),
    ("B098-012", "configs/batch093_amds_frozen_cohort.json", "darker control", "exit 1 accepted without product contract", "control-specific verifier"),
    ("B098-013", "scripts/run_batch095_candidate_lane.py", "pytest observation", "text markers replace structured exact-node results", "JUnit/report-log parser"),
    ("B098-014", "scripts/run_batch095_candidate_lane.py", "OpenBB acquisition", "detached secondary commit lacks branch ancestry", "cutoff ancestry verifier"),
    ("B098-015", "scripts/run_batch095_candidate_lane.py", "OpenBB positive control", "inline control declared without execution", "brokered control operation"),
    ("B098-016", ".github/workflows/post_v2_37_hardening_batch097_evidence_reconstitution_real_repository_genome_topology_amds.yml", "TLD job", "raw TLD bundle absent in CI", "exact source-custody bridge"),
    ("B098-017", "scripts/run_batch097_topology_producers.py", "ToT-BULB", "nonempty values treated as verified", "dimension-specific producer/verifier receipts"),
    ("B098-018", "scripts/run_batch097_topology_producers.py", "local BROT", "graph hash used as verifier identity", "executed independent edge verifier"),
    ("B098-019", "scripts/run_batch097_topology_producers.py", "OpenBB process-product edge", "producer not-run", "eligible executed operation"),
    ("B098-020", "scripts/run_batch097_topology_producers.py", "coupled projection", "named rows lack two executed sides", "executed ProjectionPair"),
    ("B098-021", "controllergate/topology/evidence_compiler.py", "compile_decisive_board", "fixed ontology permits empty derivation", "source-bound causal-contact hypotheses"),
    ("B098-022", "controllergate/topology/evidence_compiler.py", "compile_decisive_board", "one generic terminal cell per candidate", "ownership uncertainty cells"),
    ("B098-023", "controllergate/topology/evidence_compiler.py", "probe compiler", "probe lacks executable contract and partitions", "MinimalProbeV1"),
    ("B098-024", "scripts/run_batch097_amds_builder.py", "builder", "topology-derived frame ignored", "installed AMDS consumes frozen frame"),
    ("B098-025", "scripts/run_batch097_amds_builder.py", "builder", "fixed hypotheses with empty constraints/contracts", "graph-derived inputs only"),
    ("B098-026", "scripts/run_batch097_amds_builder.py", "arms", "same evidence hashes reused by all arms", "component-specific execution ledgers"),
    ("B098-027", "scripts/run_batch097_amds_builder.py", "observations", "zero causal facts derived", "independent semantic fact verifier"),
    ("B098-028", "scripts/run_batch097_amds_builder.py", "DPP-14 stages", "declared rows replace executed transitions", "installed stage producers"),
    ("B098-029", "scripts/run_batch097_amds_builder.py", "contradiction", "injected control counted as backtracking", "observation-driven contradiction"),
    ("B098-030", "scripts/run_batch097_amds_builder.py", "stage verification", "producer also creates verifier rows", "isolated verifier execution"),
    ("B098-031", "scripts/batch097_standalone_critic.py", "mutation campaign", "summary mutation lacks copied raw tree", "complete raw-tree mutation"),
    ("B098-032", "scripts/join_batch097_truth_and_quality.py", "quality", "one episode and no causal facts", "eight-episode causal quality gate"),
    ("B098-033", "README.md", "public entry", "current scope lacks concise installed read-only path", "truthful v2.19 quick start"),
)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def line_range(path: Path, symbol: str) -> str:
    if not path.is_file():
        return "artifact-or-config-scope"
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    needle = symbol.split(".")[-1]
    for index, line in enumerate(lines, 1):
        if needle in line:
            return f"{index}-{min(index + 12, len(lines))}"
    return f"1-{min(20, len(lines))}"


def build() -> dict[str, object]:
    commit = __import__("subprocess").check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    findings = []
    for finding_id, relative, symbol, risk, correction in FINDINGS:
        path = ROOT / relative
        findings.append({
            "finding_id": finding_id,
            "commit": commit,
            "path": relative,
            "symbol": symbol,
            "line_range": line_range(path, symbol),
            "artifact_evidence": {"exists": path.exists(), "sha256": sha256(path) if path.is_file() else None},
            "risk": risk,
            "required_correction": correction,
            "red_to_green_test": f"tests/batch098/test_{finding_id.lower().replace('-', '_')}.py",
        })
    return {
        "status": RESULT,
        "execution_depth": "direct pre-implementation source and artifact inspection",
        "producer": "scripts/audit_batch098_pre_fix_causal_hypergraph_and_materialization.py",
        "authority_allowed": "expected-red correction plan",
        "authority_forbidden": ["scientific PASS", "repair authority", "release promotion"],
        "finding_count": len(findings),
        "findings": findings,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seal", action="store_true")
    args = parser.parse_args()
    if args.seal:
        value = build()
        SEALED.parent.mkdir(parents=True, exist_ok=True)
        SEALED.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    else:
        value = json.loads(SEALED.read_text(encoding="utf-8"))
        if value.get("status") != RESULT or value.get("finding_count") != 33:
            raise SystemExit("sealed Batch098 expected-red result is invalid")
    print(RESULT)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
