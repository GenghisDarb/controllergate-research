from __future__ import annotations

import argparse
import ast
import hashlib
import json
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FORBIDDEN_PRODUCT_MODULES = {
    "controllergate.product.cycle",
    "controllergate.state.state_store",
    "controllergate.state.run_state",
}


def _imports(path: Path, module: str) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    found: set[str] = set()
    package = module.rsplit(".", 1)[0]
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            found.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            if node.level:
                base = package.split(".")
                if node.level > 1:
                    base = base[: -(node.level - 1)]
                prefix = ".".join(base)
                target = f"{prefix}.{node.module}" if node.module else prefix
            else:
                target = node.module or ""
            found.add(target)
    return found


def _contains_direct_external_operation(path: Path) -> bool:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    imports = set()
    calls = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            imports.add(node.module or "")
        elif isinstance(node, ast.Call):
            try:
                calls.add(ast.unparse(node.func))
            except Exception:
                pass
    return bool(imports & {"subprocess", "urllib.request", "requests", "socket"}) or any(
        value.startswith(("subprocess.", "urllib.request.", "requests.", "socket.", "os.system"))
        for value in calls
    )


def audit(artifact: Path, *, expect_fixed: bool = False) -> dict[str, object]:
    engine_imports = _imports(ROOT / "controllergate" / "engine.py", "controllergate.engine")
    cli_imports = _imports(ROOT / "controllergate" / "cli.py", "controllergate.cli")
    reachable = sorted((engine_imports | cli_imports) & FORBIDDEN_PRODUCT_MODULES)

    lifecycle = ROOT / "controllergate" / "product" / "historical_lifecycle.py"
    provider = ROOT / "controllergate" / "runtime" / "historical_provider_reconstructor.py"
    execute_probe = (ROOT / "controllergate" / "amds" / "dpp14" / "execute_probe.py").read_text(encoding="utf-8")
    quality_builder = (ROOT / "scripts" / "run_batch086_historical_lifecycle_dpp14_product_beta_rc.py").read_text(encoding="utf-8")
    interlock = (ROOT / "controllergate" / "interlocks" / "negative_regulation.py").read_text(encoding="utf-8")
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    current = (ROOT / "docs" / "current_status.md").read_text(encoding="utf-8")
    frontier = json.loads((ROOT / "outputs" / "frontier" / "CURRENT_FRONTIER_STATE.json").read_text(encoding="utf-8"))
    generator = (ROOT / "scripts" / "generate_current_state_views.py").read_text(encoding="utf-8")
    with zipfile.ZipFile(artifact) as archive:
        outer = archive.read("ARTIFACT_SHA256SUMS.txt").decode("utf-8")

    defects = {
        "legacy_product_reachability": reachable,
        "historical_lifecycle_direct_external_operation": _contains_direct_external_operation(lifecycle),
        "historical_provider_direct_external_operation": _contains_direct_external_operation(provider),
        "dpp_quality_expected_terminal_present_before_adjudication": "expected_terminal" in quality_builder,
        "dpp_execute_probe_does_not_call_broker": "broker" not in execute_probe and "execute_operation" not in execute_probe,
        "interlock_accepts_literal_pass": '!= "PASS"' in interlock or "== \"PASS\"" in interlock,
        "public_state_disagrees_with_frontier": (
            "Product Beta RC" in readme
            and "0.2.0b1" in readme
            and "PRODUCT_BETA_RC_PASS" in current
            and frontier.get("product_beta_rc") == "PRODUCT_BETA_RC_BLOCKED_EXACT"
        ),
        "current_state_generator_hardcodes_obsolete_block": (
            '"product_beta_rc": "PRODUCT_BETA_RC_BLOCKED_EXACT"' in generator
            and "recover or reconstruct a complete historical provider" in generator
        ),
        "outer_manifest_has_runner_absolute_paths": "/home/runner/work/_temp/batch086-artifact/" in outer,
    }
    if expect_fixed:
        static_path = ROOT / "outputs" / "post_v2_37_hardening_batch087_canonical_execution_blind_dpp14_product_beta_revalidation" / "canonical_installed_execution_graph.json"
        reconciliation_path = ROOT / "outputs" / "post_v2_37_hardening_batch087_canonical_execution_blind_dpp14_product_beta_revalidation" / "batch086_outer_manifest_portability_reconciliation.json"
        static = json.loads(static_path.read_text(encoding="utf-8")) if static_path.is_file() else {}
        reconciliation = json.loads(reconciliation_path.read_text(encoding="utf-8")) if reconciliation_path.is_file() else {}
        blind = (ROOT / "controllergate" / "amds" / "dpp14" / "blind_runtime.py").read_text(encoding="utf-8")
        defects["historical_lifecycle_direct_external_operation"] = bool(
            defects["historical_lifecycle_direct_external_operation"] and "controllergate.product.historical_lifecycle" in static.get("reachable_modules", [])
        )
        defects["historical_provider_direct_external_operation"] = bool(
            defects["historical_provider_direct_external_operation"] and "controllergate.runtime.historical_provider_reconstructor" in static.get("reachable_modules", [])
        )
        defects["dpp_quality_expected_terminal_present_before_adjudication"] = any(key in blind for key in ("decision_bundle[\"expected_terminal\"]", "decision_bundle.get(\"expected_terminal\")"))
        defects["outer_manifest_has_runner_absolute_paths"] = not (
            defects["outer_manifest_has_runner_absolute_paths"] and reconciliation.get("status") == "PASS"
            and reconciliation.get("normalized_records_checked") == 31
        )
    discovered = [name for name, value in defects.items() if bool(value)]
    expected = set(defects)
    if expect_fixed:
        status = "BATCH087_FINAL_HEAD_AUDIT_PASS" if not discovered else "BATCH087_FINAL_HEAD_AUDIT_FAIL"
    else:
        status = "BATCH087_PRE_FIX_AUDIT_FAIL_EXPECTED" if set(discovered) == expected else "PRE_FIX_CRITIC_INCOMPLETE"
    return {
        "status": status,
        "starting_head": "ae0410fa1fcabbcf1653e5e73f003f397398a1ca",
        "critic": "scripts/audit_batch087_pre_fix_release_truth.py",
        "independent_discovery": True,
        "artifact_sha256": hashlib.sha256(artifact.read_bytes()).hexdigest(),
        "defects": defects,
        "discovered_defect_count": len(discovered),
        "expected_defect_count": len(expected),
        "mutated_builder_evidence": False,
        "expect_fixed": expect_fixed,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--artifact", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--expect-fixed", action="store_true")
    args = parser.parse_args()
    result = audit(args.artifact, expect_fixed=args.expect_fixed)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(result, sort_keys=True))
    if args.expect_fixed:
        return 0 if result["status"] == "BATCH087_FINAL_HEAD_AUDIT_PASS" else 2
    return 1 if result["status"] == "BATCH087_PRE_FIX_AUDIT_FAIL_EXPECTED" else 2


if __name__ == "__main__":
    raise SystemExit(main())
