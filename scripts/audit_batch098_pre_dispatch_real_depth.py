from __future__ import annotations

import hashlib
import json
import re
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
START = "b68b0a5c37d12daa21d2e0366179caf2771cd1ea"
OUT = ROOT / "outputs" / "post_v2_37_hardening_batch098_causal_hypergraph_real_materialization_topology_probe_closure"
WORKFLOW = ".github/workflows/post_v2_37_hardening_batch098_causal_hypergraph_real_materialization_topology_probe_closure.yml"
MATERIALIZER = "controllergate/evidence/materializer.py"
PIPELINE = "controllergate/topology/pipeline_v1.py"
PROBES = "controllergate/topology/probe_compiler_v1.py"
STAGES = "controllergate/amds/stage_runtime_v7.py"
DIAGNOSE = "controllergate/amds/batch098_diagnose.py"


def at_head(path: str) -> str:
    return subprocess.check_output(["git", "show", f"{START}:{path}"], cwd=ROOT, text=True, encoding="utf-8")


def line_range(text: str, token: str) -> list[int]:
    for number, line in enumerate(text.splitlines(), 1):
        if token in line:
            return [number, number]
    return [1, max(1, len(text.splitlines()))]


def finding(number: int, title: str, path: str, symbol: str, detected: bool, token: str, correction: str) -> dict[str, object]:
    text = at_head(path)
    return {
        "finding_id": f"BATCH098-PRE-DISPATCH-{number:02d}",
        "title": title,
        "detected": detected,
        "commit": START,
        "path": path,
        "symbol": symbol,
        "line_range": line_range(text, token),
        "raw_evidence_sha256": hashlib.sha256(text.encode()).hexdigest(),
        "risk": f"Shallow evidence could be misclassified as {title.lower()} closure.",
        "required_correction": correction,
        "red_to_green_test": f"tests/test_batch098_corrective_real_depth.py::test_finding_{number:02d}",
    }


def main() -> int:
    if subprocess.check_output(["git", "rev-parse", START], cwd=ROOT, text=True).strip() != START:
        raise SystemExit("BATCH098_STARTING_HEAD_UNRESOLVED")
    workflow = at_head(WORKFLOW)
    materializer = at_head(MATERIALIZER)
    pipeline = at_head(PIPELINE)
    probes = at_head(PROBES)
    stages = at_head(STAGES)
    diagnose = at_head(DIAGNOSE)
    job_count = len(re.findall(r"^  [a-zA-Z0-9_-]+:\s*$", workflow, re.MULTILINE)) - 1  # workflow_dispatch is not a job
    specs = [
        (1, "workflow independence", WORKFLOW, "jobs", job_count == 6, "jobs:", "Separate custody, production, verification, truth, baselines, critic, and adjudication jobs."),
        (2, "sealed truth isolation", WORKFLOW, "jobs", "sealed-truth" not in workflow, "jobs:", "Add a physically isolated sealed-truth custody job."),
        (3, "architecture arm execution", WORKFLOW, "jobs", "architecture-arm" not in workflow, "jobs:", "Execute independent architecture-arm jobs."),
        (4, "baseline execution", WORKFLOW, "jobs", "baseline" not in workflow, "jobs:", "Execute independent baseline jobs."),
        (5, "standalone critic isolation", WORKFLOW, "jobs", "standalone-critic" not in workflow, "jobs:", "Add a standard-library-only critic job."),
        (6, "complete copied raw-tree mutation", WORKFLOW, "jobs", "complete-raw-tree" not in workflow, "jobs:", "Run re-signed mutations over a complete copied evidence tree."),
        (7, "main artifact retention", WORKFLOW, "final", "retention-days: 30" not in workflow, "retention-days: 1", "Retain the final main artifact for at least 30 days."),
        (8, "executed adversarial controls", MATERIALIZER, "_candidate_controls", "synthetic_text_only" in materializer, "synthetic_text_only", "Require an operation or copied-evidence rejection receipt for every control."),
        (9, "OpenBB real controls", MATERIALIZER, "_candidate_controls", "brokered_inline_service" in materializer and "control_id':%r" in materializer, "brokered_inline_service", "Execute service and structural controls with raw products."),
        (10, "source-derived controls", MATERIALIZER, "_candidate_controls", "source-derived-control" in materializer, "source-derived-control", "Derive direct and unrelated calls from pinned candidate source."),
        (11, "OpenBB ancestry acquisition", MATERIALIZER, "materialize_candidate", "origin/main" not in materializer, "source_fetch", "Acquire bounded origin/main ancestry."),
        (12, "OpenBB cutoff verification", MATERIALIZER, "materialize_candidate", "merge-base --is-ancestor" not in materializer, "source_fetch", "Recompute and verify cutoff and ancestry."),
        (13, "OpenBB loopback service", MATERIALIZER, "materialize_candidate", "ThreadingHTTPServer" not in materializer, "incident_openbb", "Execute a broker-managed dynamic loopback service."),
        (14, "OpenBB port substitution", MATERIALIZER, "materialize_candidate", "port=" not in materializer.split("target_argv =", 1)[-1], "target_argv =", "Supply the acquired dynamic port to target expansion."),
        (15, "OpenBB structural product controls", MATERIALIZER, "_candidate_controls", "openapi_product" not in materializer.split("def _candidate_controls", 1)[-1], "def _candidate_controls", "Execute structural OpenAPI verification for each control."),
        (16, "fresh post-operation manifests", MATERIALIZER, "materialize_candidate", "source_after_manifest = full_manifest" in materializer, "source_after_manifest = full_manifest", "Freshly remeasure source, build, and execution after operations."),
        (17, "post-operation Git revalidation", MATERIALIZER, "materialize_candidate", "source_head_after" not in materializer, "source_identity_after", "Reverify HEAD, tree, tracked manifests, and clean diff after execution."),
        (18, "immutable broker chain", MATERIALIZER, "materialize_candidate", "target_record[\"record_hash\"] = None" in materializer, "target_record[\"record_hash\"] = None", "Emit a child integrity receipt instead of mutating a chained record."),
        (19, "local wheel network policy", MATERIALIZER, "materialize_candidate", '"project_wheel_build"' in materializer and "network=True" in materializer, "project_wheel_build", "Use network none for local wheel build/install."),
        (20, "additional local install network policy", MATERIALIZER, "materialize_candidate", '"provider_additional_local_install"' in materializer and "network=True" in materializer, "provider_additional_local_install", "Use network none for local project installs."),
        (21, "sealed parser verifier registry", MATERIALIZER, "_parse_products", "contract.candidate_id" in materializer.split("def _parse_products", 1)[-1].split("def _candidate_controls", 1)[0], "def _parse_products", "Dispatch only through sealed parser_id and verifier_id registries."),
        (22, "exact JUnit node verification", MATERIALIZER, "_verify_incident", 'verified = bool(failures)' in materializer, "verified = bool(failures)", "Bind exact collected node and structured outcome family."),
        (23, "Audioread structured module evidence", MATERIALIZER, "_verify_incident", '"aifc" in json.dumps(product)' in materializer, '"aifc" in json.dumps(product)', "Use the structured missing-module field and import origin."),
        (24, "Pytest exact warning evidence", MATERIALIZER, "_verify_incident", "bool(structured.get(\"cases\"))" in materializer, "structured_warning_incident_absent", "Bind exact nodes, warning configuration, and structured warnings."),
        (25, "Poetry exact path-derived defect", MATERIALIZER, "_verify_incident", '" " in parsed.get("project_name"' in materializer, "path_derived_space", "Compare parsed name to the exact path-derived expected name and explicit-name control."),
        (26, "raw boundary producer receipts", PIPELINE, "produce_topology", "raw_hash = identity([dimension, value" in pipeline, "raw_hash = identity", "Bind producers to exact raw operation objects."),
        (27, "independent boundary reconstruction", PIPELINE, "verify_topology", "recomputed = identity([row[\"dimension\"]" in pipeline, "recomputed = identity", "Reopen raw operations and reconstruct observed dimensions."),
        (28, "executed local graph receipts", PIPELINE, "produce_topology", "local-node-producer" in pipeline, "local-node-producer", "Execute source parsing/trace producers and independent reopen verifiers."),
        (29, "ownership-specific derivation", PIPELINE, "verify_topology", "source_parents = tuple" in pipeline, "source_parents = tuple", "Derive each ownership cell from role-specific evidence."),
        (30, "semantic process-product verification", PIPELINE, "verify_topology", "product-verifier:{identity" in pipeline, "product-verifier", "Execute a distinct semantic product verifier."),
        (31, "executed projection sides", PIPELINE, "produce_topology", "side_a_observation\": identity(control)" in pipeline, "side_a_observation", "Execute and independently verify both projection sides."),
        (32, "executed modality transformations", PIPELINE, "produce_topology", '"VERIFIED_TRUE" if raw_parents' in pipeline, "state_proposal", "Run distinct modality transformations and verifiers."),
        (33, "candidate-specific ownership operations", PROBES, "_probe_for", "argv = tuple(contract.get(\"target_argv\"" in probes, "argv = tuple", "Compile relation-specific operations instead of reusing target argv."),
        (34, "relation-specific probes", PROBES, "_probe_for", "source_cell_or_edge_or_region=source" in probes, "source_cell_or_edge_or_region", "Bind each probe to its actual edge, region, projection, or boundary operation."),
        (35, "semantic predicted partitions", PROBES, "_probe_for", '"contact_observed"' in probes, '"contact_observed"', "Bind partitions to candidate-specific verifier rules."),
        (36, "installed execute-probe command", PROBES, "MinimalProbeV1", "controllergate evidence execute-probe" in probes and "def execute_probe" not in probes, "controllergate evidence execute-probe", "Implement the installed brokered execute-probe command."),
        (37, "real DPP-14 mechanisms", STAGES, "execute_stage", "executed_stages" in stages and "CausalBoardController" not in stages, "def execute_stage", "Execute board, planner, broker, verifier, truth maintenance, and audit mechanisms."),
        (38, "isolated stage verification", STAGES, "run_dpp14", "verify_stage(index, before, state)" in stages, "verify_stage(index", "Use isolated verifier executables that reconstruct transitions."),
        (39, "diagnostic probe execution", DIAGNOSE, "diagnose_batch098", "execute_probe" not in diagnose, "def diagnose_batch098", "Execute topology-derived probes through the broker."),
        (40, "real arms and baselines", DIAGNOSE, "diagnose_batch098", "baseline" not in diagnose and "architecture" not in diagnose, "def diagnose_batch098", "Execute distinct arms and baselines."),
        (41, "truth-separated scoring", DIAGNOSE, "diagnose_batch098", "truth" not in diagnose, "def diagnose_batch098", "Join sealed truth only after terminal commitment."),
        (42, "stage-produced source ownership", DIAGNOSE, "diagnose_batch098", "source_ownership" not in diagnose, "def diagnose_batch098", "Run producer/verifier source-ownership stages."),
        (43, "shallow final packaging", WORKFLOW, "final", "standalone-critic" not in workflow and "complete-raw-tree" not in workflow, "final:", "Gate packaging on raw critic, mutations, truth join, and adjudication."),
    ]
    findings = [finding(*spec) for spec in specs]
    if not all(row["detected"] for row in findings):
        missing = [row["finding_id"] for row in findings if not row["detected"]]
        raise SystemExit("BATCH098_EXPECTED_RED_DETECTION_INCOMPLETE:" + ",".join(missing))
    result = {
        "status": "BATCH098_PRE_DISPATCH_REAL_DEPTH_FAIL_EXPECTED",
        "target_commit": START,
        "finding_count": len(findings),
        "findings": findings,
        "producer": "scripts.audit_batch098_pre_dispatch_real_depth",
        "execution_depth": "frozen-starting-commit source inspection",
        "authority_allowed": "corrective implementation requirements only",
        "authority_forbidden": ["scientific pass", "patch", "count mutation", "release promotion"],
    }
    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / "batch098_pre_dispatch_real_depth_expected_failure.json"
    path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    print(result["status"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
