from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from scripts.run_batch095_amds_builder import make_contracts


ROOT = Path(__file__).resolve().parents[1]


def write(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def test_probe_contracts_are_neutral_and_validate(tmp_path: Path) -> None:
    evidence = {"process": {"return_code": 1}}
    contracts = make_contracts("candidate", tmp_path, "a" * 64, evidence)
    assert len(contracts) == 3
    for contract in contracts:
        contract.validate()
        surface = json.dumps(contract.record()).lower()
        assert "expected_terminal" not in surface
        assert "truth_label" not in surface


def test_builder_stops_before_truth_when_roles_not_complete(tmp_path: Path) -> None:
    cohort = tmp_path / "cohort"
    write(cohort / "role_measurement_quality_gate_v3.json", {"status": "NOT_RUN"})
    output = tmp_path / "output"
    subprocess.run(
        [sys.executable, str(ROOT / "scripts/run_batch095_amds_builder.py"), "--cohort-output", str(cohort), "--candidate-inputs-root", str(tmp_path / "candidates"), "--runtime-root", str(tmp_path / "runtime"), "--output", str(output)],
        cwd=ROOT, check=True,
    )
    gate = json.loads((output / "amds_historical_quality_gate_v4.json").read_text(encoding="utf-8"))
    assert gate["status"] == "NOT_RUN"
    assert gate["active_blocker"] == "80_role_measurements_not_complete"
    assert not (output / "amds_controller_audit_terminals_v4.jsonl").exists()


def test_stage_authority_can_honestly_have_zero_source_proofs(tmp_path: Path) -> None:
    amds = tmp_path / "amds"
    amds.mkdir()
    (amds / "amds_controller_audit_terminals_v4.jsonl").write_text(
        json.dumps({"candidate_id": "candidate", "terminal": "provider_owned"}) + "\n", encoding="utf-8"
    )
    output = tmp_path / "output"
    subprocess.run(
        [sys.executable, str(ROOT / "scripts/run_batch095_stage_source_ownership.py"), "--amds-output", str(amds), "--candidate-inputs-root", str(tmp_path / "candidate-inputs"), "--output", str(output)],
        cwd=ROOT, check=True,
    )
    coverage = json.loads((output / "source_ownership_requirement_coverage_v3.json").read_text(encoding="utf-8"))
    assert coverage["status"] == "NOT_RUN_NO_SOURCE_TERMINAL"
    assert coverage["source_ownership_proof_count"] == 0
    assert not (output / "source_ownership_proof_chain_v4.jsonl").exists()


def test_truth_capsule_is_separate_from_builder_output(tmp_path: Path) -> None:
    runtime = tmp_path / "truth"
    manifest = tmp_path / "manifest.json"
    subprocess.run(
        [sys.executable, str(ROOT / "scripts/seal_batch095_amds_truth.py"), "--runtime", str(runtime), "--manifest-output", str(manifest)],
        cwd=ROOT, check=True,
    )
    value = json.loads(manifest.read_text(encoding="utf-8"))
    assert value["builder_access"] is False
    assert value["episode_count"] == 8
    assert Path(value["truth_capsule_path"]).parent == runtime
