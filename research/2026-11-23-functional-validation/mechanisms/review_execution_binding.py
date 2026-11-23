"""Focused peer re-review of the discovered argv/cwd binding defects.

No provider operations or broad regression suite. Only local source-shaped
records are constructed and mutated; all output stays in this review folder.
"""
from __future__ import annotations
from datetime import datetime, timezone
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parent
STUDY = ROOT.parent
INTEGRATION = STUDY / "integration"


def main():
    path = INTEGRATION / "run_integration_checks.py"
    spec = importlib.util.spec_from_file_location("peer_current_integration", path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    assert spec.loader
    spec.loader.exec_module(module)
    cell = module.chosen("batch100-darker-112-git-dir", "incident")
    base = module.fixture_receipt(cell, {"not_a_git_repository": True, "return_code": 1})
    checks = [{"name": "valid_source_shaped_baseline", "expected": "ACCEPT",
               "errors": module.verify_fresh_semantics(base, cell, module.REGISTRY)}]

    def check(name, row, expected_error, mutation):
        module.rehash(row)
        errors = module.verify_fresh_semantics(row, cell, module.REGISTRY)
        checks.append({"name": name, "expected": "REJECT", "expected_error": expected_error,
                       "errors": errors, "mutation": mutation})

    for label, key, value, expected in (
        ("unrelated_actual_command", "observed_argv", ["unrelated-command"], "observed_argv_not_declared_materialization"),
        ("unrelated_actual_directory", "observed_cwd", "/unrelated-directory", "observed_cwd_not_declared_materialization"),
    ):
        for mirror in (False, True):
            row = copy.deepcopy(base)
            row["raw_execution_binding"][key] = value
            if mirror:
                row["bound_broker_observation"]["argv" if key == "observed_argv" else "working_directory"] = value
            check(label + ("_broker_mirrored" if mirror else ""), row, expected,
                  {"field": key, "new_value": value, "broker_mirrored": mirror})
    for name, key, value in (
        ("boolean_replaced_by_integer", "predicate_result", 1),
        ("outer_status_forgery", "semantic_status", "UNRESOLVED"),
    ):
        row = copy.deepcopy(base)
        row[key] = value
        check(name, row, "outer_semantic_fields_disagree", {"field": key, "new_value": value})
    row = copy.deepcopy(base)
    argv = list(row["raw_execution_binding"]["observed_argv"])
    position = next(i for i, value in enumerate(argv) if i and value.startswith("-"))
    old = argv[position]
    argv[position] += "/"
    row["raw_execution_binding"]["observed_argv"] = argv
    row["bound_broker_observation"]["argv"] = argv
    check("literal_option_trailing_slash", row, "observed_argv_not_declared_materialization",
          {"position": position, "before": old, "after": argv[position], "broker_mirrored": True})
    row = copy.deepcopy(base)
    argv = list(row["raw_execution_binding"]["observed_argv"])
    old = argv[0]
    assert base["platform"] == "linux" and "/bin/" in old
    argv[0] = old.replace("/bin/", "/bin\\")
    row["raw_execution_binding"]["observed_argv"] = argv
    row["bound_broker_observation"]["argv"] = argv
    check("linux_backslash_changes_executable_path", row, "observed_argv_not_declared_materialization",
          {"position": 0, "before": old, "after": argv[0], "broker_mirrored": True})

    for check_row in checks:
        check_row["pass"] = not check_row["errors"] if check_row["expected"] == "ACCEPT" else check_row["expected_error"] in check_row["errors"]
    inspected = [
        path,
        INTEGRATION / "checkout/controllergate/evidence/execution_contract_binding_candidate.py",
        INTEGRATION / "checkout/controllergate/evidence/registry_bound_semantic_seam_candidate.py",
        INTEGRATION / "checkout/scripts/run_batch102_candidate_slice.py",
    ]
    receipt = {"schema": "focused_execution_binding_peer_review.v1", "reviewer": "/root/bridge_review",
               "executed_utc": datetime.now(timezone.utc).isoformat(),
               "status": "PASS_WITH_LOCAL_SCOPE" if all(row["pass"] for row in checks) else "FAIL",
               "checks": checks, "check_count": len(checks),
               "source_sha256": {str(p.relative_to(STUDY)): hashlib.sha256(p.read_bytes()).hexdigest() for p in inspected},
               "scope": "Source-shaped synthetic receipt, actual shared raw-record constructor and semantic verifier. Confirms rejection of the discovered binding/normalization mutations; no remote provider or full-suite execution.",
               "preserved_initial_receipts": ["peer_execution_binding_review_initial.json", "peer_execution_binding_review_v4.json"],
               "limits": ["A self-generated hash is not an authenticated external observation.",
                          "No causal sensitivity, source ownership, biological benefit or production readiness follows from this peer check."]}
    (ROOT / "peer_execution_binding_review_final.json").write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"status": receipt["status"], "check_count": len(checks),
                      "accepted_baseline": checks[0]["pass"], "rejected_mutations": sum(r["pass"] for r in checks[1:])}, indent=2))
    return 0 if all(row["pass"] for row in checks) else 1


if __name__ == "__main__":
    raise SystemExit(main())
