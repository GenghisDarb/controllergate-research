from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
import zipfile
from pathlib import Path


CANDIDATES = [
    "darker_issue_112_relative_git_dir",
    "py_bugger_issue_65",
    "cloudpickle_507_py313_typevar_distutils",
    "freezegun_547_py313_datetimes_assertion",
    "audioread_144_py313_aifc_removed",
    "pytest_13480_wdefault_unraisable_threadexception",
    "incident_openbb_7585_modular_openapi_reproducer",
    "incident_poetry_10974_init_duplicate_name",
]
PROVIDER_SERIES = {
    "darker_issue_112_relative_git_dir": "3.7",
    "py_bugger_issue_65": "3.11",
    "incident_openbb_7585_modular_openapi_reproducer": "3.11",
    "incident_poetry_10974_init_duplicate_name": "3.11",
}
FIXED_TIME = (1980, 1, 1, 0, 0, 0)


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")


def stage(receipts: Path, name: str, role: str, command: list[str], input_path: Path | None = None, output_path: Path | None = None) -> None:
    wrapper = Path(__file__).with_name("run_batch098_local_stage.py")
    wrapped = [sys.executable, str(wrapper), "--stage", name, "--role", role, "--receipts", str(receipts)]
    if input_path is not None:
        wrapped.extend(["--input", str(input_path)])
    if output_path is not None:
        wrapped.extend(["--output", str(output_path)])
    wrapped.extend(["--", *command])
    completed = subprocess.run(wrapped, check=False)
    if completed.returncode != 0:
        raise RuntimeError(f"local stage blocked: {name}")


def package(evidence: Path, artifact: Path) -> dict:
    files = [path for path in evidence.rglob("*") if path.is_file() and "sealed-truth" not in path.parts]
    manifest_rows = []
    for path in sorted(files):
        rel = path.relative_to(evidence).as_posix()
        manifest_rows.append((rel, hashlib.sha256(path.read_bytes()).hexdigest()))
    manifest = "".join(f"{digest}  {rel}\n" for rel, digest in manifest_rows).encode("utf-8")
    artifact.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(artifact, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for path in sorted(files):
            rel = path.relative_to(evidence).as_posix()
            info = zipfile.ZipInfo(rel, FIXED_TIME); info.create_system = 3; info.external_attr = (0o100644 << 16); info.compress_type = zipfile.ZIP_DEFLATED
            archive.writestr(info, path.read_bytes(), compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)
        info = zipfile.ZipInfo("ARTIFACT_SHA256SUMS.txt", FIXED_TIME); info.create_system = 3; info.external_attr = (0o100644 << 16); info.compress_type = zipfile.ZIP_DEFLATED
        archive.writestr(info, manifest, compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)
    raw = artifact.read_bytes()
    return {"artifact_name": artifact.name, "artifact_size": len(raw), "artifact_sha256": hashlib.sha256(raw).hexdigest(), "manifest_entry_count": len(manifest_rows), "execution_surface": "LOCAL_PROTECTED_SOURCE_RUN"}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--controllergate", required=True)
    parser.add_argument("--workflow-stage", required=True)
    parser.add_argument("--provider-map", required=True)
    parser.add_argument("--contracts", required=True)
    parser.add_argument("--bundle", required=True)
    parser.add_argument("--requirements", required=True)
    parser.add_argument("--runtime-root", required=True)
    parser.add_argument("--forbidden-repo-root", required=True)
    parser.add_argument("--artifact", required=True)
    parser.add_argument("--artifact-report", required=True)
    args = parser.parse_args()
    root = Path(args.runtime_root); evidence = root / "evidence"; evidence.mkdir(parents=True, exist_ok=True)
    receipts = evidence / "local_stage_process_receipts.jsonl"
    providers = json.loads(Path(args.provider_map).read_text(encoding="utf-8"))
    cli = str(Path(args.controllergate))
    py = sys.executable
    workflow_stage = str(Path(args.workflow_stage))
    try:
        candidates_root = evidence / "candidate-artifacts"
        for candidate in CANDIDATES:
            series = PROVIDER_SERIES.get(candidate, "3.13")
            output = candidates_root / candidate
            stage(receipts, f"materialization-{candidate}", "producer", [cli, "evidence", "materialize-candidate", "--contracts", args.contracts, "--candidate", candidate, "--runtime-root", str(root / "candidate-runtime" / candidate), "--output", str(output), "--provider-python", providers[series], "--forbidden-repo-root", args.forbidden_repo_root, "--run-id", f"batch098-local-{candidate}"], output_path=output)
        cohort = evidence / "cohort"
        stage(receipts, "cohort-join", "custody", [py, workflow_stage, "normalize-candidates", "--source", str(candidates_root), "--output", str(cohort)], candidates_root, cohort)
        incidents = evidence / "incidents"
        stage(receipts, "incident-verification", "verifier", [py, workflow_stage, "incident-verify", "--source", str(cohort), "--output", str(incidents)], cohort, incidents)
        roles_produced = evidence / "roles-produced"; roles_verified = evidence / "roles-verified"
        stage(receipts, "role-production", "producer", [py, workflow_stage, "role-produce", "--source", str(cohort), "--output", str(roles_produced)], cohort, roles_produced)
        stage(receipts, "role-verification", "verifier", [py, workflow_stage, "role-verify", "--source", str(roles_produced), "--output", str(roles_verified)], roles_produced, roles_verified)
        frames = evidence / "frames"
        for candidate in CANDIDATES:
            candidate_evidence = cohort / candidate
            for family in ("bulb", "brot"):
                produced = evidence / f"{family}-produced" / candidate
                verified = evidence / f"{family}-verified" / candidate
                stage(receipts, f"{family}-production-{candidate}", "producer", [cli, "topology", "produce", "--candidate-evidence", str(candidate_evidence), "--contracts", args.contracts, "--output", str(produced)], candidate_evidence, produced)
                stage(receipts, f"{family}-verification-{candidate}", "verifier", [cli, "topology", "verify", "--candidate-evidence", str(candidate_evidence), "--producer-evidence", str(produced), "--output", str(verified)], produced, verified)
            frame = frames / candidate
            stage(receipts, f"frame-compilation-{candidate}", "producer", [cli, "topology", "compile-board", "--candidate-evidence", str(candidate_evidence), "--verified-topology", str(evidence / "brot-verified" / candidate), "--contracts", args.contracts, "--output", str(frame)], candidate_evidence, frame)
        stage(receipts, "frame-verification", "verifier", [py, workflow_stage, "frame-verify", "--source", str(frames), "--output", str(evidence / "frame-verification")], frames, evidence / "frame-verification")
        stage(receipts, "tld-shadow-processing", "producer", [py, str(Path(__file__).with_name("parse_batch098_tld_direct_bundle.py")), "--bundle", args.bundle, "--requirements", args.requirements, "--output", str(evidence / "tld-shadow")], Path(args.bundle), evidence / "tld-shadow")
        stage(receipts, "truth-custody", "custody", [py, workflow_stage, "truth-custody", "--output", str(evidence / "sealed-truth")], output_path=evidence / "sealed-truth")
        terminals = evidence / "terminals"
        for candidate in CANDIDATES:
            frame_file = frames / candidate / "topology_compiled_decision_frame_v3.json"
            stage(receipts, f"dpp14-{candidate}", "producer", [py, workflow_stage, "dpp-candidate", "--frame", str(frame_file), "--output", str(terminals / candidate)], frame_file, terminals / candidate)
        stage(receipts, "terminal-seal", "verifier", [py, workflow_stage, "seal-tree", "--source", str(terminals), "--output", str(evidence / "terminal-seal")], terminals, evidence / "terminal-seal")
        reference_frame = frames / CANDIDATES[0] / "topology_compiled_decision_frame_v3.json"
        experiments = evidence / "experiments"
        for experiment_id in "ABCDEFGHIJ":
            group = "arms" if experiment_id <= "F" else "baselines"
            stage(receipts, f"experiment-{experiment_id}", "producer", [py, workflow_stage, "experiment", "--frame", str(reference_frame), "--experiment-id", experiment_id, "--output", str(experiments / group / experiment_id)], reference_frame, experiments / group / experiment_id)
        stage(receipts, "truth-join", "verifier", [py, workflow_stage, "truth-join", "--source", str(experiments), "--truth", str(evidence / "sealed-truth"), "--output", str(evidence / "quality")], experiments, evidence / "quality")
        ownership = evidence / "source-ownership"
        for candidate in CANDIDATES:
            produced = ownership / "produced" / candidate; verified = ownership / "verified" / candidate
            stage(receipts, f"source-ownership-production-{candidate}", "producer", [py, workflow_stage, "source-ownership-produce", "--source", str(cohort / candidate / "candidate_lane_result_v2.json"), "--terminal", str(terminals / candidate / "terminal.json"), "--topology", str(evidence / "brot-verified" / candidate), "--output", str(produced)], terminals / candidate, produced)
            stage(receipts, f"source-ownership-verification-{candidate}", "verifier", [py, workflow_stage, "source-ownership-verify", "--source", str(produced), "--output", str(verified)], produced, verified)
        raw_seal = evidence / "raw-seal"
        stage(receipts, "complete-raw-tree-seal", "custody", [py, workflow_stage, "seal-tree", "--source", str(evidence), "--output", str(raw_seal)], evidence, raw_seal)
        stage(receipts, "standalone-critic", "critic", [py, str(Path(__file__).with_name("batch098_standalone_critic_v7.py")), "--raw-evidence", str(evidence), "--output", str(evidence / "critic")], evidence, evidence / "critic")
        stage(receipts, "seal-breaking-mutations", "critic", [py, str(Path(__file__).with_name("batch098_seal_breaking_mutations.py")), "--raw-evidence", str(evidence), "--output", str(evidence / "seal-mutations")], evidence, evidence / "seal-mutations")
        stage(receipts, "resigned-raw-tree-mutations", "critic", [py, str(Path(__file__).with_name("batch098_complete_raw_tree_mutations.py")), "--raw-evidence", str(evidence), "--output", str(evidence / "resigned-mutations")], evidence, evidence / "resigned-mutations")
        result = package(evidence, Path(args.artifact)); write_json(Path(args.artifact_report), {**result, "status": "PASS_LOCAL_ARTIFACT", "github_scientific_workflow": "NOT_RUN_PRIVATE_SOURCE_MODE"})
    except RuntimeError as exc:
        write_json(Path(args.artifact_report), {"status": "BLOCK", "execution_surface": "LOCAL_PROTECTED_SOURCE_RUN", "exact_blocker": str(exc), "github_scientific_workflow": "NOT_RUN_PRIVATE_SOURCE_MODE"})
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
