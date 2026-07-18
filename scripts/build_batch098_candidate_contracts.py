from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from controllergate.evidence.contracts import CandidateExecutionContract, seal_contracts


CONTROL_RECIPES = {
    "darker_issue_112_relative_git_dir": {
        "positive": [
            {"control_id": "darker-absolute-git-dir", "argv_mode": "target", "environment": {"GIT_DIR": "{ABS_GIT_DIR}"}, "product_schema": "process-trace-v1"},
            {"control_id": "darker-no-git-dir", "argv_mode": "target", "environment": {}, "product_schema": "process-trace-v1"},
        ],
        "negative": [{"control_id": "darker-invalid-absolute-git-dir", "argv_mode": "target", "environment": {"GIT_DIR": "{MISSING_GIT_DIR}"}, "product_schema": "process-trace-v1"}],
        "adversarial": [{"control_id": "darker-unrelated-exit-one", "operation": "python -c raise-SystemExit-1", "must_not_verify_incident": True}],
        "parser": "darker-subprocess-trace-v3",
    },
    "py_bugger_issue_65": {
        "positive": [{"control_id": "py-bugger-exact-node-collect", "argv_mode": "collect_exact_node", "product_schema": "junit-and-collection-v1"}],
        "negative": [{"control_id": "py-bugger-unrelated-node", "argv_mode": "source_derived_unrelated_node", "product_schema": "junit-v1"}],
        "adversarial": [{"control_id": "py-bugger-marker-collision", "synthetic_text_only": True, "must_not_verify_incident": True}],
        "parser": "structured-pytest-exact-node-v2",
    },
    "cloudpickle_507_py313_typevar_distutils": {
        "positive": [{"control_id": "cloudpickle-exact-node-collect", "argv_mode": "collect_exact_node", "product_schema": "junit-and-collection-v1"}],
        "negative": [{"control_id": "cloudpickle-direct-call-control", "argv_mode": "source_derived_direct_callable", "product_schema": "process-trace-v1"}],
        "adversarial": [{"control_id": "cloudpickle-wrong-node", "must_not_verify_incident": True}],
        "parser": "structured-pytest-exact-node-v2",
    },
    "freezegun_547_py313_datetimes_assertion": {
        "positive": [{"control_id": "freezegun-exact-file-collect", "argv_mode": "collect_registered_tests", "product_schema": "junit-and-collection-v1"}],
        "negative": [{"control_id": "freezegun-direct-datetime", "argv_mode": "direct_datetime_without_harness", "product_schema": "datetime-values-v1"}],
        "adversarial": [{"control_id": "freezegun-value-substitution", "must_not_verify_incident": True}],
        "parser": "structured-pytest-datetime-v2",
    },
    "audioread_144_py313_aifc_removed": {
        "positive": [{"control_id": "audioread-direct-aifc-import", "argv_mode": "direct_removed_module_import", "product_schema": "import-observation-v1"}],
        "negative": [{"control_id": "audioread-unrelated-stdlib-import", "argv_mode": "direct_unrelated_import", "product_schema": "import-observation-v1"}],
        "adversarial": [{"control_id": "audioread-fabricated-origin", "must_not_verify_incident": True}],
        "parser": "import-origin-and-structured-test-v2",
    },
    "pytest_13480_wdefault_unraisable_threadexception": {
        "positive": [{"control_id": "pytest-exact-warning-nodes", "argv_mode": "target", "product_schema": "junit-warning-v1"}],
        "negative": [{"control_id": "pytest-direct-unraisable-thread", "argv_mode": "direct_runtime_behavior", "product_schema": "warning-record-v1"}],
        "adversarial": [{"control_id": "pytest-broad-word-marker", "synthetic_text_only": True, "must_not_verify_incident": True}],
        "parser": "structured-pytest-warning-v2",
    },
    "incident_openbb_7585_modular_openapi_reproducer": {
        "positive": [{"control_id": "openbb-inline-one-operation", "argv_mode": "brokered_inline_service", "product_schema": "openapi-structural-v1"}],
        "negative": [
            {"control_id": "openbb-service-unavailable", "argv_mode": "service_unavailable", "product_schema": "process-trace-v1"},
            {"control_id": "openbb-corrupt-yaml", "argv_mode": "corrupt_yaml", "product_schema": "parse-error-v1"},
            {"control_id": "openbb-post-cutoff", "argv_mode": "post_cutoff_rejection", "product_schema": "source-lineage-v1"},
        ],
        "adversarial": [{"control_id": "openbb-fabricated-product", "must_not_verify_incident": True}],
        "parser": "openapi-structural-product-v2",
    },
    "incident_poetry_10974_init_duplicate_name": {
        "positive": [{"control_id": "poetry-explicit-name", "argv_mode": "explicit_name", "product_schema": "toml-product-v1"}],
        "negative": [{"control_id": "poetry-product-absent-before-run", "argv_mode": "precondition", "product_schema": "filesystem-state-v1"}],
        "adversarial": [{"control_id": "poetry-configured-name-injection", "must_not_verify_incident": True}],
        "parser": "toml-product-and-direct-normalization-v2",
    },
}


def build() -> list[CandidateExecutionContract]:
    providers = json.loads((ROOT / "configs" / "batch095_provider_recipe_registry.json").read_text(encoding="utf-8"))["episodes"]
    acquisition = {row["candidate_id"]: row for row in json.loads((ROOT / "configs" / "batch094_fresh_cohort_acquisition.json").read_text(encoding="utf-8"))["episodes"]}
    rows = []
    for provider in providers:
        candidate = provider["candidate_id"]
        acquired = acquisition[candidate]
        controls = CONTROL_RECIPES[candidate]
        target_argv = list(provider["target_argv"])
        if candidate == "darker_issue_112_relative_git_dir":
            target_argv = ["{venv_bin}/darker", "--check", "src"]
        secondary = None
        if provider.get("secondary_repository"):
            secondary = {
                "repository": provider["secondary_repository"],
                "cutoff": provider["secondary_cutoff"],
                "expected_commit": provider["expected_secondary_commit"],
                "required_history_ref": "origin/main",
                "ancestry_required": True,
            }
        lock_specs = []
        if provider.get("decision_time_lock_path"):
            lock_specs = json.loads((ROOT / provider["decision_time_lock_path"]).read_text(encoding="utf-8"))["install_specs"]
        install_tail = list(provider["install_argv"])[4:]
        external_specs = [value for value in install_tail if not value.startswith(".")]
        local_paths = [value for value in install_tail if value.startswith(".") and value not in {".", "./cli"}]
        build_source = "./cli" if "./cli" in install_tail else "."
        rows.append(CandidateExecutionContract.from_mapping({
            "candidate_id": candidate,
            "repository": provider["repository"],
            "source_commit": provider["source_commit"],
            "candidate_class": acquired["candidate_class"],
            "provider_python": provider["python_version"],
            "provider_install_specs": [*lock_specs, *external_specs],
            "project_build_source": build_source,
            "additional_project_install_paths": local_paths,
            "project_build_argv": ["{python}", "-m", "pip", "wheel", "{PROJECT_BUILD_SOURCE}", "--no-deps", "--wheel-dir", "{PRODUCT_DIR}"],
            "target_argv": target_argv,
            "target_paths": acquired.get("target_paths", []),
            "target_working_compartment": "CONSUMER_OR_TARGET_WORKSPACE" if provider["materializer"] in {"git_consumer_cli", "state_product_cli", "openapi_local_service"} else "EXECUTION_WORKSPACE",
            "target_environment": acquired.get("target_environment", {}),
            "parser_id": controls["parser"],
            "verifier_id": f"controllergate.evidence.semantic_verifiers:{controls['parser']}",
            "positive_controls": controls["positive"],
            "negative_controls": controls["negative"],
            "adversarial_controls": controls["adversarial"],
            "acquisition_network_policy": provider["network_acquisition_policy"],
            "execution_network_policy": "loopback_only" if candidate == "incident_openbb_7585_modular_openapi_reproducer" else "none",
            "environment_allowlist": provider["environment_allowlist"],
            "resource_budget": {"timeout_seconds": 1800, "network_requests": 256, "network_bytes": 2_000_000_000, "processes": 16},
            "source_path_classes": {"test": acquired.get("target_paths", []), "source": []},
            "secondary_source": secondary,
        }))
    return rows


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True)
    parser.add_argument("--custody", required=True)
    args = parser.parse_args()
    contracts = build()
    output = Path(args.output); output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("".join(json.dumps(row.record(), sort_keys=True, separators=(",", ":")) + "\n" for row in contracts), encoding="utf-8", newline="\n")
    custody = seal_contracts(contracts)
    custody.update({"producer": "scripts/build_batch098_candidate_contracts.py", "execution_depth": "decision-time-safe config reconciliation", "semantic_scope": "sealed candidate contract custody", "authority_allowed": "materialization inputs", "authority_forbidden": ["terminal truth", "repair authority"]})
    Path(args.custody).write_text(json.dumps(custody, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({"status": "PASS", "contract_count": len(contracts), "bundle_hash": custody["bundle_hash"]}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
