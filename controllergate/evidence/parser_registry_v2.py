from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any, Callable, Mapping

from .contracts import CandidateExecutionContract
from .observations import TypedObservationParser


Parser = Callable[[int | None, str, str, list[Path], list[Path], Mapping[str, Any]], dict[str, Any]]
Verifier = Callable[[CandidateExecutionContract, Mapping[str, Any], list[Mapping[str, Any]], Mapping[str, Any]], dict[str, Any]]


def _base(return_code: int | None, stdout: str, stderr: str, structured: list[Path], products: list[Path], context: Mapping[str, Any]) -> dict[str, Any]:
    return {"process": {**TypedObservationParser.process(return_code, stdout, stderr), "executed_argv": list(context.get("executed_argv", ()))}}


def _pytest(return_code: int | None, stdout: str, stderr: str, structured: list[Path], products: list[Path], context: Mapping[str, Any]) -> dict[str, Any]:
    result = _base(return_code, stdout, stderr, structured, products, context)
    junit = next((path for path in structured if path.is_file() and path.suffix == ".xml"), None)
    if junit:
        result["structured_test"] = TypedObservationParser.junit(junit)
    result["warnings"] = TypedObservationParser.warnings(stdout, stderr)
    result["warning_configuration"] = [arg for arg in context.get("executed_argv", ()) if str(arg).startswith("-W")]
    return result


def _import_failure(return_code: int | None, stdout: str, stderr: str, structured: list[Path], products: list[Path], context: Mapping[str, Any]) -> dict[str, Any]:
    result = _pytest(return_code, stdout, stderr, structured, products, context)
    combined = stdout + "\n" + stderr
    result["missing_modules"] = sorted(set(re.findall(r"No module named ['\"]([^'\"]+)['\"]", combined)))
    origins = []
    for line in combined.splitlines():
        try:
            value = json.loads(line)
        except (ValueError, TypeError):
            continue
        if isinstance(value, dict) and "origin" in value:
            origins.append({"module": value.get("module"), "origin": value.get("origin")})
    result["import_origins"] = origins
    return result


def _toml(return_code: int | None, stdout: str, stderr: str, structured: list[Path], products: list[Path], context: Mapping[str, Any]) -> dict[str, Any]:
    result = _base(return_code, stdout, stderr, structured, products, context)
    product = next((path for path in products if path.name == "pyproject.toml" and path.is_file()), None)
    if product:
        result["product"] = TypedObservationParser.toml_product(product)
    result["path_derived_name"] = Path(str(context.get("target_cwd", "."))).name
    return result


def _openapi(return_code: int | None, stdout: str, stderr: str, structured: list[Path], products: list[Path], context: Mapping[str, Any]) -> dict[str, Any]:
    result = _base(return_code, stdout, stderr, structured, products, context)
    product = next((path for path in products if path.is_file()), None)
    if product:
        result["product"] = {**TypedObservationParser.openapi_product(product), "path": str(product), "lineage_operation_id": context.get("operation_id")}
    return result


PARSERS: dict[str, Parser] = {
    "darker-subprocess-trace-v3": _base,
    "structured-pytest-exact-node-v2": _pytest,
    "structured-pytest-datetime-v2": _pytest,
    "import-origin-and-structured-test-v2": _import_failure,
    "structured-pytest-warning-v2": _pytest,
    "openapi-structural-product-v2": _openapi,
    "toml-product-and-direct-normalization-v2": _toml,
}


def parse_registered(parser_id: str, return_code: int | None, stdout: str, stderr: str, structured: list[Path], products: list[Path], context: Mapping[str, Any]) -> dict[str, Any]:
    try:
        parser = PARSERS[parser_id]
    except KeyError as exc:
        raise ValueError(f"unregistered sealed parser_id: {parser_id}") from exc
    result = parser(return_code, stdout, stderr, structured, products, context)
    result["parser_id"] = parser_id
    result["parser_receipt"] = hashlib.sha256(json.dumps(result, sort_keys=True, default=str, separators=(",", ":")).encode()).hexdigest()
    return result


def _control_status(controls: list[Mapping[str, Any]]) -> bool:
    return bool(controls) and all(row.get("status") == "PASS" and row.get("operation_id") and row.get("semantic_verification_receipt") for row in controls)


def _expected_pytest_targets(contract: CandidateExecutionContract) -> list[str]:
    return [arg for arg in contract.target_argv if ".py" in arg and not str(arg).startswith("--")]


def _junit_matches(contract: CandidateExecutionContract, product: Mapping[str, Any]) -> tuple[bool, list[dict[str, Any]]]:
    cases = list(product.get("structured_test", {}).get("cases", ()))
    failures = [row for row in cases if row.get("outcome") in {"failure", "error"}]
    expected = _expected_pytest_targets(contract)
    matched = []
    for target in expected:
        path, _, node = target.partition("::")
        for row in failures:
            same_path = str(row.get("file", "")).replace("\\", "/").endswith(path.replace("\\", "/"))
            same_node = not node or row.get("name") == node or str(row.get("node_id", "")).endswith("::" + node)
            if same_path and same_node:
                matched.append(row)
    return bool(matched), matched


def _verify_darker(contract: CandidateExecutionContract, product: Mapping[str, Any], controls: list[Mapping[str, Any]], context: Mapping[str, Any]) -> dict[str, Any]:
    process = product.get("process", {})
    child = [row for row in process.get("command_records", ()) if "git" in str(row).lower()]
    ok = process.get("return_code") == 1 and bool(process.get("traceback_frames")) and bool(set(process.get("exception_types", ())).intersection({"CalledProcessError", "DarkerException"})) and bool(child)
    return {"verified": ok, "reasons": [] if ok else ["exact_subprocess_boundary_or_git_child_argv_missing"]}


def _verify_pytest(contract: CandidateExecutionContract, product: Mapping[str, Any], controls: list[Mapping[str, Any]], context: Mapping[str, Any]) -> dict[str, Any]:
    matched, rows = _junit_matches(contract, product)
    return {"verified": matched, "matched_exact_cases": rows, "reasons": [] if matched else ["exact_registered_test_failure_absent"]}


def _verify_audioread(contract: CandidateExecutionContract, product: Mapping[str, Any], controls: list[Mapping[str, Any]], context: Mapping[str, Any]) -> dict[str, Any]:
    process = product.get("process", {})
    missing = product.get("missing_modules", ())
    ok = "ModuleNotFoundError" in process.get("exception_types", ()) and "aifc" in missing
    return {"verified": ok, "missing_modules": list(missing), "reasons": [] if ok else ["structured_aifc_missing_module_not_observed"]}


def _verify_pytest_warning(contract: CandidateExecutionContract, product: Mapping[str, Any], controls: list[Mapping[str, Any]], context: Mapping[str, Any]) -> dict[str, Any]:
    expected_nodes = _expected_pytest_targets(contract)
    cases = product.get("structured_test", {}).get("cases", ())
    families = set(product.get("warnings", {}).get("families", ()))
    configured = "-Wdefault" in product.get("warning_configuration", ())
    paths = {str(row.get("file", "")).replace("\\", "/") for row in cases}
    nodes_ok = all(any(path.endswith(target.split("::", 1)[0]) for path in paths) for target in expected_nodes)
    ok = configured and nodes_ok and bool(families.intersection({"PytestUnraisableExceptionWarning", "PytestUnhandledThreadExceptionWarning"}))
    return {"verified": ok, "exact_nodes": expected_nodes, "warning_families": sorted(families), "reasons": [] if ok else ["exact_warning_node_configuration_or_record_missing"]}


def _verify_openapi(contract: CandidateExecutionContract, product: Mapping[str, Any], controls: list[Mapping[str, Any]], context: Mapping[str, Any]) -> dict[str, Any]:
    process = product.get("process", {})
    parsed = product.get("product", {})
    ok = process.get("return_code") == 0 and parsed.get("operation_count") == 0 and bool(parsed.get("lineage_operation_id"))
    return {"verified": ok, "reasons": [] if ok else ["cutoff_bound_empty_openapi_product_missing"]}


def _verify_poetry(contract: CandidateExecutionContract, product: Mapping[str, Any], controls: list[Mapping[str, Any]], context: Mapping[str, Any]) -> dict[str, Any]:
    process = product.get("process", {})
    parsed = product.get("product", {})
    expected = product.get("path_derived_name")
    ok = process.get("return_code") == 0 and bool(expected) and parsed.get("project_name") == expected
    return {"verified": ok, "expected_path_name": expected, "observed_name": parsed.get("project_name"), "reasons": [] if ok else ["exact_path_derived_name_defect_absent"]}


VERIFIERS: dict[str, Verifier] = {
    "controllergate.evidence.semantic_verifiers:darker-subprocess-trace-v3": _verify_darker,
    "controllergate.evidence.semantic_verifiers:structured-pytest-exact-node-v2": _verify_pytest,
    "controllergate.evidence.semantic_verifiers:structured-pytest-datetime-v2": _verify_pytest,
    "controllergate.evidence.semantic_verifiers:import-origin-and-structured-test-v2": _verify_audioread,
    "controllergate.evidence.semantic_verifiers:structured-pytest-warning-v2": _verify_pytest_warning,
    "controllergate.evidence.semantic_verifiers:openapi-structural-product-v2": _verify_openapi,
    "controllergate.evidence.semantic_verifiers:toml-product-and-direct-normalization-v2": _verify_poetry,
}


def verify_registered(verifier_id: str, contract: CandidateExecutionContract, product: Mapping[str, Any], controls: list[Mapping[str, Any]], context: Mapping[str, Any]) -> dict[str, Any]:
    try:
        verifier = VERIFIERS[verifier_id]
    except KeyError as exc:
        raise ValueError(f"unregistered sealed verifier_id: {verifier_id}") from exc
    semantic = verifier(contract, product, controls, context)
    controls_ok = _control_status(controls)
    verified = bool(semantic["verified"]) and controls_ok
    record = {
        "status": "PASS" if verified else "BLOCK",
        "typed_incident_materialized": verified,
        "reasons": [*semantic.get("reasons", ()), *([] if controls_ok else ["executed_control_verification_incomplete"])],
        "verifier_id": verifier_id,
        "semantic_result": semantic,
        "structured_product_parents": [hashlib.sha256(json.dumps(product, sort_keys=True, default=str).encode()).hexdigest()],
        "executed_control_count": len(controls),
        "authority_allowed": "frozen cohort eligibility",
        "authority_forbidden": ["causal ownership", "repair authority"],
    }
    record["verification_receipt"] = hashlib.sha256(json.dumps(record, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    return record
