from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def run(*args: object) -> None:
    subprocess.run(
        [sys.executable, *map(str, args)],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )


def jsonl(path: Path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def test_truth_blind_empty_outcome_pipeline_is_conservative(tmp_path: Path):
    cells = tmp_path / "cells"
    cells.mkdir()
    outcomes = tmp_path / "outcomes"
    run(
        "scripts/seal_batch103_candidate_outcomes.py",
        "--cell-artifacts-root",
        cells,
        "--output-root",
        outcomes,
        "--workflow-run-id",
        "103",
        "--workflow-head",
        "a" * 40,
    )
    seal = json.loads((outcomes / "batch103_outcome_envelope_seal_receipt_v1.json").read_text())
    assert seal["status"] == "PASS_NO_FRESH_OUTCOMES_AVAILABLE"
    assert len(jsonl(outcomes / "batch103_registered_cell_ledger_v1.jsonl")) == 70

    arms = tmp_path / "arms"
    for arm in "ABCDEFGHIJ":
        run(
            "scripts/run_batch103_planner_arm.py",
            "--arm",
            arm,
            "--outcome-root",
            outcomes,
            "--output-root",
            arms / arm,
        )
    assert jsonl(arms / "J/reactome_planner_selection_history_v1.jsonl") == []
    assert all(
        row["status"] == "SELECTED_OUTCOME_UNAVAILABLE"
        for row in jsonl(arms / "A/reactome_planner_outcome_vault_access_v1.jsonl")
    )

    gain = tmp_path / "gain"
    causal = tmp_path / "causal"
    terminal = tmp_path / "terminal"
    ownership = tmp_path / "ownership"
    run(
        "scripts/compile_batch103_public_evidence.py",
        "--phase",
        "gain",
        "--arm-artifacts-root",
        arms,
        "--output-root",
        gain,
    )
    run(
        "scripts/compile_batch103_public_evidence.py",
        "--phase",
        "causal",
        "--outcome-root",
        outcomes,
        "--output-root",
        causal,
    )
    run(
        "scripts/compile_batch103_public_evidence.py",
        "--phase",
        "terminal",
        "--arm-artifacts-root",
        arms,
        "--causal-root",
        causal,
        "--output-root",
        terminal,
    )
    run(
        "scripts/compile_batch103_public_evidence.py",
        "--phase",
        "ownership",
        "--causal-root",
        causal,
        "--terminal-root",
        terminal,
        "--output-root",
        ownership,
    )
    gate = json.loads((gain / "reactome_planner_gain_gate_v1.json").read_text())
    assert gate["R4"] == gate["R5"] == "NOT_ESTABLISHED"
    assert gate["R6"] == "NOT_RUN"
    assert len(jsonl(gain / "reactome_planner_execution_receipts_v1.jsonl")) == 90
    assert len(jsonl(terminal / "batch103_controller_audit_terminal_records_v1.jsonl")) == 90
    assert json.loads((ownership / "batch103_source_ownership_proof_registry_v1.json").read_text())["proof_count"] == 0

    evidence = tmp_path / "evidence"
    evidence.mkdir()
    for source in (gain, causal, terminal, ownership):
        for path in source.iterdir():
            shutil.copy2(path, evidence / path.name)
    critic = tmp_path / "critic"
    run(
        "scripts/run_batch103_independent_critic.py",
        "--evidence-root",
        evidence,
        "--output-root",
        critic,
        "--runtime-root",
        tmp_path / "critic-runtime",
    )
    summary = json.loads((critic / "batch103_independent_critic_summary_v1.json").read_text())
    assert summary["mutations_executed"] >= 100
    assert summary["mutations_rejected"] == summary["mutations_executed"]

    static = tmp_path / "static"
    (static / "batch102_official_ingest/ingest_receipts").mkdir(parents=True)
    required_static = {
        "batch102_official_ingest/ingest_receipts/batch102_official_ingest_receipt.json": "{}\n",
        "batch103_pre_isomorphism_reactome_closure_expected_failure.json": "{}\n",
        "canonical_isomorphism_errata_lock_v3.json": "{}\n",
        "reactome_completion_status_v1.json": "{}\n",
        "reactome_planner_arm_contracts_v1.jsonl": "{}\n",
    }
    for name, content in required_static.items():
        path = static / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
    overlays = tmp_path / "overlays"
    for source in (outcomes, gain, causal, terminal, ownership, critic):
        target = overlays / source.name
        shutil.copytree(source, target)
    (overlays / "critic-input").mkdir()
    (overlays / "critic-input/batch103_independent_critic_input_audit_v1.json").write_text("{}\n")
    staged = tmp_path / "staged"
    run(
        "scripts/stage_batch103_artifact.py",
        "--static-source",
        static,
        "--overlays-root",
        overlays,
        "--destination",
        staged,
    )
    run("scripts/verify_batch103_staged_artifact.py", "--root", staged)
    assert (staged / "ARTIFACT_SHA256SUMS.txt").is_file()


def test_gain_compiler_rejects_missing_arm_isolation(tmp_path: Path):
    result = subprocess.run(
        [
            sys.executable,
            "scripts/compile_batch103_public_evidence.py",
            "--phase",
            "gain",
            "--arm-artifacts-root",
            str(tmp_path),
            "--output-root",
            str(tmp_path / "out"),
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    assert result.returncode != 0
    assert "all 90 isolated" in result.stderr


def test_workflow_exposes_all_34_required_groups_and_fresh_matrix():
    text = (ROOT / ".github/workflows/post_v2_37_hardening_batch103_reactome_isomorphism_causal_planning_gain.yml").read_text()
    for group in range(1, 35):
        assert f"{group:02d} " in text
    assert "BATCH103_FRESH_OPERATION" not in text  # produced by the runner, not injected by YAML
    assert "scripts/run_batch103_candidate_slice.py" in text
    assert "pattern: batch103-cell-*" in text
    assert "scripts/run_batch103_planner_arm.py" in text
    assert "retention-days: 30" in text
    assert "raw private truth" not in text.casefold()
