from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_ordinary_run_keeps_authorization_dormant_and_stoichiometry_shadow_only(tmp_path: Path) -> None:
    output = tmp_path / "output"
    subprocess.run(
        [sys.executable, str(ROOT / "scripts/generate_batch095_boundaries_and_shadow.py"), "--output", str(output)],
        cwd=ROOT, check=True,
    )
    authorization = json.loads((output / "external_human_authorization_gate_v2.json").read_text(encoding="utf-8"))
    dependency = json.loads((output / "reactome_product_dependency_audit.json").read_text(encoding="utf-8"))
    shadow = json.loads((output / "reactome_stoichiometry_shadow_decision.json").read_text(encoding="utf-8"))
    assert authorization["status"] == "HUMAN_AUTHORIZATION_BLOCKED_EXACT"
    assert authorization["blocker_class"] == "DORMANT_EXTERNAL_CONDITION"
    assert dependency["active_product_blocker"] is False
    assert shadow["production_authority"] is False
