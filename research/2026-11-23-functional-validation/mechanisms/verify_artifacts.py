"""Bounded artifact consistency verification, not a scientific-validity test."""
from __future__ import annotations
import csv
import hashlib
import json
from pathlib import Path
from run_benchmark import verify_freeze

ROOT = Path(__file__).resolve().parent


def main():
    sha = verify_freeze()
    result = json.loads((ROOT / "results.json").read_text())
    witness = json.loads((ROOT / "legacy_witnesses.json").read_text())
    with (ROOT / "source_oracle_truth_table.csv").open(newline="") as stream:
        rows = list(csv.DictReader(stream))
    enabled = sum(row["oracle_status"] == "PASS" for row in rows)
    tests = json.loads((ROOT / "test_receipt.json").read_text())
    checks = {
        "frozen_inputs_unchanged": True,
        "result_freeze_binding": result["frozen_design_sha256"] == sha,
        "legacy_witness_freeze_binding": witness["frozen_design_sha256"] == sha,
        "truth_row_count": len(rows) == result["one_step_cases_per_arm"],
        "truth_id_sequence": [int(r["case_id"]) for r in rows] == list(range(1, len(rows) + 1)),
        "oracle_enabled_totals": all(r["oracle_enabled"] == enabled for r in result["one_step_totals"].values()),
        "arm_case_totals": all(r["cases"] == len(rows) for r in result["one_step_totals"].values()),
        "per_event_totals": all(sum(v[name]["cases"] for v in result["by_event"].values()) == len(rows) for name in result["one_step_totals"]),
        "batch_totals": all(r["cases"] == len(result["batch_rows"]) for r in result["batch_summary"].values()),
        "observed_unit_test_receipt": tests["exit_code"] == 0 and tests["tests_run"] == 16 and tests["failures"] == tests["errors"] == 0,
        "original_resource_guard_negative_control": witness["archived_numeric_underflow_negative_control"]["status"] == "BLOCK",
    }
    payloads = ["FROZEN_DESIGN.json", "results.json", "legacy_witnesses.json", "source_oracle_truth_table.csv", "test_receipt.json"]
    report = {"schema": "functional_translation_artifact_verification.v1",
              "status": "PASS" if all(checks.values()) else "FAIL", "checks": checks,
              "payload_sha256": {p: hashlib.sha256((ROOT / p).read_bytes()).hexdigest() for p in payloads},
              "scope": "Checks the original pre-outcome input freeze and structural artifact consistency. Independent source-direct outcome recomputation is recorded separately by the parent reviewer; this manifest does not authenticate its own anchor or prove biology."}
    (ROOT / "verification.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"status": report["status"], "checks": len(checks), "truth_rows": len(rows)}))
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
