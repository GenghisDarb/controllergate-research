from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def write(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def test_critic_reconstructs_block_and_rejects_actual_evidence_mutations(tmp_path: Path) -> None:
    evidence = tmp_path / "evidence"
    candidates = tmp_path / "candidates"
    write(evidence / "batch094_artifact_manifest_verification.json", {"status": "PASS"})
    write(evidence / "historical_eight_episode_materialization_gate.json", {"status": "BLOCK", "historical_count_increment": 0})
    write(evidence / "role_measurement_quality_gate_v3.json", {"status": "NOT_RUN"})
    write(evidence / "amds_historical_quality_gate_v4.json", {"status": "NOT_RUN"})
    write(evidence / "external_human_authorization_gate_v2.json", {"status": "HUMAN_AUTHORIZATION_BLOCKED_EXACT", "approval_received": False})
    write(evidence / "batch095_blocker_dependency_graph.json", {"status": "PASS"})
    write(evidence / "reactome_product_dependency_audit.json", {"status": "PASS", "active_product_blocker": False})
    write(candidates / "one" / "candidate_lane_result.json", {"candidate_id": "one", "patch_operation_count": 0, "count_increment": 0})
    completed = subprocess.run(
        [sys.executable, str(ROOT / "scripts/batch095_standalone_critic.py"), "--evidence", str(evidence), "--candidate-inputs-root", str(candidates), "--runtime", str(tmp_path / "runtime")],
        cwd=ROOT, text=True, capture_output=True,
    )
    assert completed.returncode == 0, completed.stdout + completed.stderr
    decision = json.loads((evidence / "internal_release_evidence_decision_v4.json").read_text(encoding="utf-8"))
    mutation = json.loads((evidence / "resigned_actual_evidence_mutation_results_v2.json").read_text(encoding="utf-8"))
    findings = (evidence / "standalone_critic_findings_v4.jsonl").read_text(encoding="utf-8").splitlines()
    assert decision["release_decision"] == "PRODUCT_BETA_RC_BLOCKED_EXACT"
    assert mutation["executed"] >= 3
    assert mutation["executed"] == mutation["rejected"]
    assert findings
