from __future__ import annotations

from pathlib import Path

from controllergate.batch082.io import write_sha256sums
from controllergate.batch082.orchestrator import cohort, critic, derived_stage, finalize
from controllergate.core.evidence import write_json_deterministic


def test_finalize_preserves_zero_admission_as_scientific_output(tmp_path: Path) -> None:
    repo = Path(__file__).resolve().parents[2]
    prepared = tmp_path / "prepared"; prepared.mkdir()
    write_json_deterministic(prepared / "prepared.json", {"status": "PASS"})
    write_sha256sums(prepared)
    evidence = tmp_path / "evidence"
    for short in ("openbb", "poetry"):
        provider = evidence / f"{short}-provider"; provider.mkdir(parents=True)
        diagnosis = evidence / f"{short}-diagnosis"; diagnosis.mkdir(parents=True)
        write_json_deterministic(provider / "provider_result.json", {"verification_status": "PASS", "provider_verified": True})
        write_json_deterministic(diagnosis / "duplicate_reproduction_result.json", {"status": "BLOCK", "duplicate_failure_admitted": False, "exact_blocker": f"{short}_exact_blocker"})
        write_json_deterministic(diagnosis / "runtime_attestation.json", {"status": "PASS", "absolute_root": f"runner-temp/{short}", "attestation_hash": short})
    cohort(evidence, evidence / "cohort")
    for stage in ("pilot", "ground-truth", "authorization", "repair"):
        derived_stage(stage, evidence / "cohort", evidence / stage)
    critic(evidence / "cohort", evidence / "critic")
    result = finalize(repo, prepared, evidence, tmp_path / "final")
    assert result["status"] == "PASS"
    assert result["admitted_count"] == 0
    assert (tmp_path / "final/batch082_builder_critic_agreement.json").is_file()
    assert (tmp_path / "final/batch082_windows_ci_runtime_attestation.json").is_file()
