from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--registry", default="configs/controllergate_regression_audit_registry.json")
    parser.add_argument("--result", default=None)
    args = parser.parse_args()
    registry_path = ROOT / args.registry
    registry = json.loads(registry_path.read_text(encoding="utf-8"))
    results = []
    failed_required = False
    for audit in sorted(registry["audits"], key=lambda item: item["dependency_order"]):
        path = ROOT / audit["script_path"]
        if not path.is_file():
            result = {"audit_id": audit["audit_id"], "status": "MISSING", "required": audit["required"], "returncode": None}
            failed_required = failed_required or audit["required"]
        else:
            command = [sys.executable, str(path), *audit.get("arguments", [])]
            completed = subprocess.run(command, cwd=ROOT, text=True, capture_output=True, check=False)
            passed = completed.returncode == audit["expected_exit_status"]
            result = {
                "audit_id": audit["audit_id"], "status": "PASS" if passed else "FAIL",
                "required": audit["required"], "returncode": completed.returncode,
                "expected_exit_status": audit["expected_exit_status"],
                "stdout_tail": completed.stdout[-1200:], "stderr_tail": completed.stderr[-1200:],
                "evidence_boundary_protected": audit["evidence_boundary_protected"],
            }
            failed_required = failed_required or (audit["required"] and not passed)
        results.append(result)
        print(f"{result['audit_id']}: {result['status']}")
        if failed_required:
            break
    report = {"status": "FAIL" if failed_required else "PASS", "registry": args.registry, "results": results}
    if args.result:
        from controllergate.core.evidence import write_json_deterministic
        write_json_deterministic(ROOT / args.result, report)
    return 1 if failed_required else 0


if __name__ == "__main__":
    raise SystemExit(main())
