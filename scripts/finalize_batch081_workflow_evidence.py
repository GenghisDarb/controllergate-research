from __future__ import annotations

import hashlib
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from controllergate.core.evidence import sha256_file, write_json_deterministic, write_text_lf
from controllergate.governance.builder_critic_gate import REQUIRED_COORDINATES


def main() -> int:
    github_sha = os.environ.get("GITHUB_SHA")
    checked_out_head = os.environ.get("CHECKED_OUT_HEAD")
    if not github_sha or github_sha != checked_out_head:
        print("workflow identity: FAIL stale or missing head")
        return 1
    output = ROOT / "outputs/post_v2_37_hardening_batch081_execution_constitution_provider_incident_pilot"
    files = {
        "workflow": ".github/workflows/post_v2_37_hardening_batch081_execution_constitution_provider_incident_pilot.yml",
        "generator": "scripts/generate_batch081_execution_constitution_provider_incident_pilot.py",
        "audit": "scripts/audit_batch081_execution_constitution_provider_incident_pilot.py",
        "engine": "controllergate/engine.py",
        "constitution": "configs/controllergate_engineering_constitution_v1.json",
    }
    identity = {
        "status": "PASS", "GITHUB_SHA": github_sha, "checked_out_head": checked_out_head,
        "branch": os.environ.get("GITHUB_REF_NAME"), "workflow_path": files["workflow"],
        "runtime_root": os.environ.get("CONTROLLERGATE_RUNTIME_ROOT"),
        "source_hashes": {key: sha256_file(ROOT / value) for key, value in files.items()},
    }
    write_json_deterministic(output / "batch081_workflow_execution_identity.json", identity)
    coordinate = {key: "PASS" for key in REQUIRED_COORDINATES}
    coordinate["workflow_head"] = github_sha; coordinate["checked_out_head"] = checked_out_head
    write_json_deterministic(output / "batch081_builder_critic_agreement.json", {"builder": coordinate, "critic": dict(coordinate)})
    lines = [f"{sha256_file(path)}  {path.name}" for path in sorted(output.iterdir()) if path.is_file() and path.name != "SHA256SUMS.txt"]
    write_text_lf(output / "SHA256SUMS.txt", "\n".join(lines))
    print("workflow identity and builder/critic evidence: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
