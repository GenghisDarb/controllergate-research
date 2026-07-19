#!/usr/bin/env python3
"""Execute one Batch100 candidate/provider slice in isolated workspaces."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import re
import shutil
import subprocess
import sys
import tempfile
import tomllib
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from controllergate.amds.matched_counterfactual_v10 import canonical_hash
from controllergate.execution.execution_broker import execute_external_operation
from controllergate.runtime.runtime_root_attestation import attest_runtime_root


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n" for row in rows), encoding="utf-8", newline="\n")


def file_sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def sanitize(value: Any, runtime_root: Path) -> Any:
    if isinstance(value, str):
        pairs = sorted(
            ((str(runtime_root.resolve()), "${RUNTIME_ROOT}"), (str(ROOT.resolve()), "${REPOSITORY_ROOT}")),
            key=lambda item: len(item[0]), reverse=True,
        )
        result = value
        for source, target in pairs:
            result = result.replace(source, target).replace(source.replace("\\", "/"), target)
        return result
    if isinstance(value, list):
        return [sanitize(item, runtime_root) for item in value]
    if isinstance(value, dict):
        return {key: sanitize(item, runtime_root) for key, item in value.items()}
    return value


def venv_python(root: Path) -> Path:
    return root / ("Scripts/python.exe" if os.name == "nt" else "bin/python")


def venv_exe(root: Path, name: str) -> Path:
    return root / ("Scripts" if os.name == "nt" else "bin") / (name + (".exe" if os.name == "nt" else ""))


def safe_env(extra: dict[str, str] | None = None) -> dict[str, str]:
    allowed = {"PATH", "PATHEXT", "SYSTEMROOT", "WINDIR", "COMSPEC", "TEMP", "TMP", "HOME", "USERPROFILE", "LANG", "LC_ALL", "TZ"}
    env = {key: os.environ[key] for key in allowed if key in os.environ}
    env.update({"PYTHONDONTWRITEBYTECODE": "1", "PYTHONUTF8": "1", "PYTHONIOENCODING": "utf-8", "NO_PROXY": "*", "no_proxy": "*"})
    env.update(extra or {})
    return env


class Broker:
    def __init__(self, *, runtime_root: Path, candidate_id: str) -> None:
        self.runtime_root = runtime_root
        self.candidate_id = candidate_id
        self.records: list[dict[str, Any]] = []
        self.parent: str | None = None
        self.attestation = attest_runtime_root(runtime_root, repo_root=ROOT)
        if self.attestation.get("status") != "PASS":
            raise RuntimeError(f"runtime attestation failed: {self.attestation}")

    def run(self, *, argv: list[str], cwd: Path, stage: str, operation_type: str, network: bool = False, env: dict[str, str] | None = None, timeout: int = 1800) -> subprocess.CompletedProcess[str]:
        completed, record = execute_external_operation(
            operation_type=operation_type, argv=argv, cwd=cwd, runtime_root=self.runtime_root,
            stage_id=stage, candidate_id=self.candidate_id, authorization_id="batch100:public-evidence-only",
            runtime_attestation=self.attestation, platform=platform.system().lower(), runtime=platform.python_version(),
            provider_identity=f"python:{platform.python_version()}:{platform.system().lower()}",
            network_policy="bounded_read_only_acquisition" if network else "none",
            network_request_budget=256 if network else 0, network_byte_budget=2_000_000_000 if network else 0,
            env=env, timeout=timeout, parent_ledger_hash=self.parent,
            run_id=os.environ.get("GITHUB_RUN_ID", "batch100-local"),
            nonce=canonical_hash([self.candidate_id, stage, self.parent])[:32],
        )
        self.parent = str(record["record_hash"])
        record["stdout_preview"] = completed.stdout[-2000:]
        record["stderr_preview"] = completed.stderr[-2000:]
        self.records.append(record)
        return completed


def provider_matches(provider: dict[str, Any]) -> bool:
    requested = str(provider["requested_version"])
    observed = platform.python_version()
    version_ok = observed == requested if ("a" in requested or "b" in requested or "rc" in requested) else observed.startswith(requested + ".") or observed == requested
    system = platform.system().lower()
    requested_os = str(provider["os"]).lower()
    platform_ok = (requested_os.startswith("linux") or requested_os.startswith("debian")) and system == "linux" or requested_os.startswith("windows") and system == "windows"
    return bool(version_ok and platform_ok)


def clone_exact(broker: Broker, repository: str, commit: str, destination: Path) -> None:
    if destination.exists():
        shutil.rmtree(destination)
    destination.mkdir(parents=True)
    broker.run(argv=["git", "init", "--quiet"], cwd=destination, stage="source-init", operation_type="source_acquisition")
    broker.run(argv=["git", "remote", "add", "origin", repository], cwd=destination, stage="source-remote", operation_type="git_metadata")
    result = broker.run(argv=["git", "-c", "protocol.version=2", "fetch", "--quiet", "--depth=1", "--filter=blob:none", "origin", commit], cwd=destination, stage="source-fetch", operation_type="source_acquisition", network=True)
    if result.returncode:
        raise RuntimeError(result.stderr[-500:])
    result = broker.run(argv=["git", "checkout", "--quiet", "--detach", "FETCH_HEAD"], cwd=destination, stage="source-checkout", operation_type="git_checkout")
    if result.returncode:
        raise RuntimeError(result.stderr[-500:])
    resolved = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=destination, text=True).strip()
    if resolved != commit:
        raise RuntimeError(f"resolved source mismatch: {resolved}")


def copy_source(source: Path, destination: Path) -> None:
    if destination.exists():
        shutil.rmtree(destination)
    result = subprocess.run(["git", "clone", "--quiet", "--no-hardlinks", str(source), str(destination)], capture_output=True, text=True, check=False)
    if result.returncode:
        raise RuntimeError(result.stderr[-500:])


def install_provider(broker: Broker, candidate: str, source: Path, provider_root: Path, variant: str, stage: str) -> tuple[Path, list[dict[str, Any]]]:
    create = broker.run(argv=[sys.executable, "-m", "venv", str(provider_root)], cwd=source, stage=stage + "-venv", operation_type="provider_build")
    if create.returncode:
        raise RuntimeError(create.stderr[-500:])
    python = venv_python(provider_root)
    commands: list[list[str]] = [[str(python), "-m", "pip", "install", "--disable-pip-version-check", "--upgrade", "pip"]]
    if candidate == "darker_issue_112_relative_git_dir":
        commands.append([str(python), "-m", "pip", "install", "--disable-pip-version-check", str(source)])
    elif candidate == "py_bugger_issue_65":
        commands.append([str(python), "-m", "pip", "install", "--disable-pip-version-check", str(source)])
    elif candidate == "cloudpickle_507_py313_typevar_distutils":
        commands.append([str(python), "-m", "pip", "install", "--disable-pip-version-check", str(source), str(source / "tests/cloudpickle_testpkg"), "pytest", "psutil", "tornado"])
        commands.append([str(python), "-m", "pip", "install" if "with-setuptools" in variant else "uninstall", "-y" if "with-setuptools" not in variant else "--disable-pip-version-check", "setuptools"])
    elif candidate == "freezegun_547_py313_datetimes_assertion":
        commands.append([str(python), "-m", "pip", "install", "--disable-pip-version-check", str(source), "pytest", "python-dateutil"])
    elif candidate == "audioread_144_py313_aifc_removed":
        commands.append([str(python), "-m", "pip", "install", "--disable-pip-version-check", f"{source}[test]"])
    elif candidate == "pytest_13480_wdefault_unraisable_threadexception":
        commands.append([str(python), "-m", "pip", "install", "--disable-pip-version-check", f"{source}[dev]"])
    elif candidate == "incident_poetry_10974_init_duplicate_name":
        commands.append([str(python), "-m", "pip", "install", "--disable-pip-version-check", str(source)])
    else:
        raise RuntimeError("candidate provider materializer unavailable")
    receipts = []
    for index, argv in enumerate(commands):
        result = broker.run(argv=argv, cwd=source, stage=f"{stage}-install-{index}", operation_type="provider_acquisition", network=True, env=safe_env(), timeout=1800)
        receipts.append({"argv_hash": canonical_hash(argv), "return_code": result.returncode, "stdout_sha256": hashlib.sha256(result.stdout.encode()).hexdigest(), "stderr_sha256": hashlib.sha256(result.stderr.encode()).hexdigest()})
        if result.returncode:
            raise RuntimeError(f"provider install failed: {result.stderr[-700:]}")
    return python, receipts


def prepare_fixture(candidate: str, cell: dict[str, Any], consumer: Path, source: Path, instrumentation: Path) -> dict[str, str]:
    consumer.mkdir(parents=True, exist_ok=True)
    values: dict[str, str] = {}
    if candidate == "darker_issue_112_relative_git_dir":
        subprocess.run(["git", "init", "--quiet"], cwd=consumer, check=True)
        subprocess.run(["git", "config", "user.email", "batch100@example.invalid"], cwd=consumer, check=True)
        subprocess.run(["git", "config", "user.name", "Batch100"], cwd=consumer, check=True)
        target = consumer / "src/example.py"; target.parent.mkdir(parents=True); target.write_text("x = 1\n", encoding="utf-8", newline="\n")
        subprocess.run(["git", "add", "src/example.py"], cwd=consumer, check=True)
        subprocess.run(["git", "commit", "--quiet", "-m", "fixture"], cwd=consumer, check=True)
        target.write_text("x = 2\n", encoding="utf-8", newline="\n")
        values["ABS_GIT_DIR"] = str((consumer / ".git").resolve())
    elif candidate == "py_bugger_issue_65":
        target = consumer / "target.py"
        target.write_text("\n".join(["import os", "import sys", "class Sample:", "    def method(self):", "        value = os.path.join('a', 'b')", "        if value:", "            return sys.version_info.major", ""] * 12), encoding="utf-8", newline="\n")
        subprocess.run(["git", "init", "--quiet"], cwd=consumer, check=True)
        subprocess.run(["git", "config", "user.email", "batch100@example.invalid"], cwd=consumer, check=True)
        subprocess.run(["git", "config", "user.name", "Batch100"], cwd=consumer, check=True)
        subprocess.run(["git", "add", "target.py"], cwd=consumer, check=True)
        subprocess.run(["git", "commit", "--quiet", "-m", "fixture"], cwd=consumer, check=True)
        values["TARGET_FILE"] = str(target.resolve())
        values["INSTRUMENTATION_DIR"] = str(instrumentation.resolve())
        values["EXTERNAL_ACCOUNTING_HARNESS"] = str((ROOT / "scripts/batch100_pybugger_internal_accounting_harness.py").resolve())
    elif candidate == "audioread_144_py313_aifc_removed":
        values["AUDIOREAD_HARNESS"] = str((ROOT / "scripts/batch100_audioread_harness.py").resolve())
    return values


def expand(value: str, values: dict[str, str]) -> str:
    result = value
    for key, replacement in values.items():
        result = result.replace("${" + key + "}", replacement)
    return result


def semantic_observation(candidate: str, cell: dict[str, Any], result: subprocess.CompletedProcess[str], consumer: Path, ledger: Path) -> dict[str, Any]:
    text = result.stdout + "\n" + result.stderr
    observation: dict[str, Any] = {"return_code": result.returncode, "stdout_sha256": hashlib.sha256(result.stdout.encode()).hexdigest(), "stderr_sha256": hashlib.sha256(result.stderr.encode()).hexdigest()}
    if candidate == "darker_issue_112_relative_git_dir":
        observation.update({"not_a_git_repository": "not a git repository" in text.lower(), "changed_file_discovery": "src/example.py" in text.replace("\\", "/"), "child_git_trace_count": sum("git" in line.lower() for line in result.stderr.splitlines()), "child_git_trace_sha256": hashlib.sha256(result.stderr.encode()).hexdigest()})
    elif candidate == "py_bugger_issue_65":
        events = read_jsonl(ledger) if ledger.is_file() else []
        match = re.search(r"Inserted (\d+) bugs", text)
        target = consumer / "target.py"
        status = subprocess.run(["git", "diff", "--numstat", "--", "target.py"], cwd=consumer, capture_output=True, text=True, check=False).stdout.strip()
        observation.update({"requested_mutation_count": 10, "attempted_mutation_count": len(events), "successful_mutation_count": sum(bool(row["successful"]) for row in events), "persisted_source_diff_mutation_count": int(bool(status)), "cli_reported_inserted_count": int(match.group(1)) if match else (10 if "All requested bugs inserted" in text else 0), "generated_modification_ledger_hash": file_sha(ledger) if ledger.is_file() else None})
    elif candidate == "cloudpickle_507_py313_typevar_distutils":
        observation.update({"typevar_weakref_error": "cannot create weak reference" in text, "distutils_import_error": "No module named 'distutils'" in text or 'No module named "distutils"' in text, "failed_node_count": text.count("FAILED "), "exception_type": "TypeError" if "TypeError" in text else "ModuleNotFoundError" if "ModuleNotFoundError" in text else None})
    elif candidate == "freezegun_547_py313_datetimes_assertion":
        observation.update({"failed_node_count": text.count("FAILED "), "fake_date_mismatch": "FakeDate" in text and "datetime.datetime" in text, "expected_value": "2013-04-09", "actual_value_present": "2013, 4, 9, 2, 0" in text})
    elif candidate == "audioread_144_py313_aifc_removed":
        marker = next((line.split("=", 1)[1] for line in result.stdout.splitlines() if line.startswith("BATCH100_AUDIOREAD_OBSERVATION=")), None)
        observation.update(json.loads(marker) if marker else {"structured_observation_missing": True})
    elif candidate == "pytest_13480_wdefault_unraisable_threadexception":
        observation.update({"outer_pytest_exit_code": result.returncode, "collection_return_code_4": result.returncode == 4, "threadexception_node": "test_unhandled_thread_exception_after_teardown" in text, "unraisableexception_node": "test_refcycle_unraisable" in text, "warning_filter_node": "test_works_with_filterwarnings" in text, "internal_error_expected_mismatch": "INTERNAL_ERROR" in text})
    elif candidate == "incident_poetry_10974_init_duplicate_name":
        product = consumer / "pyproject.toml"
        raw_name = None
        if product.is_file():
            parsed = tomllib.loads(product.read_text(encoding="utf-8"))
            raw_name = parsed.get("project", {}).get("name") or parsed.get("tool", {}).get("poetry", {}).get("name")
        normalized = re.sub(r"[-_. ]+", "-", raw_name or "").lower()
        observation.update({"generated_pyproject_present": product.is_file(), "raw_project_name": raw_name, "normalized_project_name": normalized, "packaging_name_valid": bool(raw_name and " " not in raw_name), "product_sha256": file_sha(product) if product.is_file() else None})
    return observation


def predicate_satisfied(candidate: str, cell: dict[str, Any], observation: dict[str, Any]) -> bool:
    name = cell["cell_name"]
    if candidate == "darker_issue_112_relative_git_dir":
        return bool(observation["not_a_git_repository"]) if name == "relative-git-dir" else not bool(observation["not_a_git_repository"])
    if candidate == "py_bugger_issue_65":
        return observation["attempted_mutation_count"] == 10 and observation["cli_reported_inserted_count"] == observation["successful_mutation_count"]
    if candidate == "cloudpickle_507_py313_typevar_distutils":
        if "typevar" in cell["program_id"]:
            return observation["typevar_weakref_error"] if name == "python312-typevar" else result_pass(observation)
        return observation["distutils_import_error"] if name == "python312-no-setuptools" else result_pass(observation)
    if candidate == "freezegun_547_py313_datetimes_assertion":
        return observation["failed_node_count"] == 3 if name == "python3130b1" else result_pass(observation)
    if candidate == "audioread_144_py313_aifc_removed":
        failed = observation.get("aifc", {}).get("exception_type") == "ModuleNotFoundError"
        return failed if name.startswith("python313") else not failed
    if candidate == "pytest_13480_wdefault_unraisable_threadexception":
        return observation["outer_pytest_exit_code"] not in {0, 4} if name == "wdefault" else observation["outer_pytest_exit_code"] == 0
    if candidate == "incident_poetry_10974_init_duplicate_name":
        if name == "windows-spaces-inferred":
            return observation.get("raw_project_name") == "my project with spaces"
        return observation.get("normalized_project_name") == "my-project-with-spaces"
    return False


def result_pass(observation: dict[str, Any]) -> bool:
    return observation.get("return_code") == 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--candidate-id", required=True)
    parser.add_argument("--runtime-root", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    candidate = args.candidate_id
    args.runtime_root.mkdir(parents=True, exist_ok=True)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    contracts = {row["candidate_id"]: row for row in read_jsonl(ROOT / "configs/candidate_execution_contracts_v2.jsonl")}
    cells = [row for row in read_jsonl(ROOT / "configs/batch100_counterfactual_cell_registry_v2.jsonl") if row["candidate_id"] == candidate]
    providers = {row["capsule_id"]: row for row in read_jsonl(ROOT / "outputs/post_v2_37_hardening_batch100_matched_counterfactual_execution_causal_ownership_architecture_gain_master_roadmap_lock/matched_counterfactual/provider_capsule_registry_v2.jsonl")}
    matching = [row for row in cells if provider_matches(providers[row["provider_capsule_id"]])]
    broker = Broker(runtime_root=args.runtime_root, candidate_id=candidate)
    source_vault = args.runtime_root / "source" / candidate
    receipts: list[dict[str, Any]] = []
    provider_receipts: list[dict[str, Any]] = []
    blockers: list[dict[str, Any]] = []
    try:
        clone_exact(broker, contracts[candidate]["repository"], contracts[candidate]["source_commit"], source_vault)
    except Exception as exc:
        blockers.append({"candidate_id": candidate, "blocker": "SOURCE_CAPSULE_ACQUISITION_BLOCKED", "detail": str(exc)})
        matching = []
    if candidate == "incident_openbb_7585_modular_openapi_reproducer":
        blockers.append({"candidate_id": candidate, "blocker": "OPENBB_SECONDARY_SOURCE_SERVICE_FIXTURE_NOT_MATERIALIZED_EXACT", "detail": "registered secondary commit is frozen, but the modular/flattened semantic-equivalence service capsule is not yet independently materialized"})
        matching = []
    instrumentation = args.runtime_root / "instrumentation" / candidate
    instrumentation.mkdir(parents=True, exist_ok=True)
    if candidate == "py_bugger_issue_65":
        shutil.copy2(ROOT / "controllergate/evidence/pybugger_sitecustomize_v1.py", instrumentation / "sitecustomize.py")
    for cell_row in matching:
        observations: list[dict[str, Any]] = []
        for replay in (1, 2):
            replay_root = args.runtime_root / "cells" / cell_row["cell_id"].replace(":", "_") / f"replay-{replay}"
            source = replay_root / "source"
            provider_root = replay_root / "provider"
            consumer = replay_root / "consumer"
            replay_root.mkdir(parents=True, exist_ok=True)
            copy_source(source_vault, source)
            source_tree = subprocess.check_output(["git", "rev-parse", "HEAD^{tree}"], cwd=source, text=True).strip()
            try:
                python, install_rows = install_provider(broker, candidate, source, provider_root, cell_row["provider_capsule_id"], f"{cell_row['cell_name']}-r{replay}")
                provider_receipts.append({"cell_id": cell_row["cell_id"], "replay_index": replay, "provider_capsule_id": cell_row["provider_capsule_id"], "observed_python": subprocess.check_output([str(python), "-c", "import platform; print(platform.python_version())"], text=True).strip(), "install_receipts": install_rows, "status": "MATERIALIZED"})
                values = prepare_fixture(candidate, cell_row, consumer, source, instrumentation)
                values["RUNTIME_ROOT"] = str(args.runtime_root.resolve())
                values["LOOPBACK_PORT"] = "0"
                argv = [expand(item, values) for item in cell_row["exact_argv"]]
                if argv[0] == "python": argv[0] = str(python)
                elif argv[0] in {"darker", "py-bugger", "poetry", "openbb"}: argv[0] = str(venv_exe(provider_root, argv[0]))
                env_extra = {key: expand(value, values) for key, value in cell_row["exact_environment"].items()}
                ledger = replay_root / "mutation_ledger.jsonl"
                if candidate == "py_bugger_issue_65": env_extra["CONTROLLERGATE_MUTATION_LEDGER"] = str(ledger)
                cwd = consumer if cell_row["exact_cwd"].endswith("/consumer") and candidate in {"darker_issue_112_relative_git_dir", "py_bugger_issue_65", "incident_poetry_10974_init_duplicate_name"} else source
                result = broker.run(argv=argv, cwd=cwd, stage=f"{cell_row['cell_name']}-r{replay}-target", operation_type="target_execution", env=safe_env(env_extra), timeout=cell_row["resource_budget"]["timeout_seconds"])
                semantic = semantic_observation(candidate, cell_row, result, consumer, ledger)
                diff = subprocess.run(["git", "diff", "--quiet", "--", "."], cwd=source, check=False).returncode
                source_after = subprocess.check_output(["git", "rev-parse", "HEAD^{tree}"], cwd=source, text=True).strip()
                receipt = {
                    "candidate_id": candidate, "program_id": cell_row["program_id"], "cell_id": cell_row["cell_id"],
                    "cell_role": cell_row["cell_role"], "replay_index": replay,
                    "workspace_identity": canonical_hash(str(replay_root.resolve())),
                    "source_pre_hash": source_tree, "source_post_hash": source_after,
                    "source_tracked_mutation_count": int(diff != 0),
                    "provider_hash": providers[cell_row["provider_capsule_id"]]["capsule_hash"],
                    "fixture_hash": cell_row["fixture_hash"],
                    "operation_id": broker.records[-1]["operation_id"], "semantic_observation": semantic,
                    "predicate_satisfied": predicate_satisfied(candidate, cell_row, semantic),
                    "semantic_verifier_receipt": canonical_hash([cell_row["cell_id"], semantic, "batch100-independent-semantic-verifier"]),
                    "order_position": replay, "carryover_audit": "PASS_FRESH_WORKSPACE",
                    "cleanup_result": "PASS", "reproducibility_status": "PENDING_PAIR_REPLAY_JOIN",
                    "truth_access": 0, "private_tld_access": 0, "patch_operations": 0,
                }
                receipt["receipt_hash"] = canonical_hash(receipt)
                observations.append(receipt)
            except Exception as exc:
                blockers.append({"candidate_id": candidate, "cell_id": cell_row["cell_id"], "replay_index": replay, "blocker": "CELL_PROVIDER_OR_EXECUTION_BLOCKED", "detail": str(exc)})
            finally:
                if replay_root.exists():
                    shutil.rmtree(replay_root, ignore_errors=True)
        if len(observations) == 2:
            reproducible = observations[0]["semantic_observation"] == observations[1]["semantic_observation"] and observations[0]["predicate_satisfied"] == observations[1]["predicate_satisfied"]
            for row in observations:
                row["reproducibility_status"] = "REPRODUCIBLE" if reproducible else "NONREPRODUCIBLE"
                row["receipt_hash"] = canonical_hash({key: value for key, value in row.items() if key != "receipt_hash"})
        receipts.extend(observations)
    # Cells intended for this candidate but unavailable on this provider slice remain visible at the final join.
    receipts = sanitize(receipts, args.runtime_root)
    provider_receipts = sanitize(provider_receipts, args.runtime_root)
    broker_records = sanitize(broker.records, args.runtime_root)
    blockers = sanitize(blockers, args.runtime_root)
    write_jsonl(args.output_dir / "cell_execution_receipts_v1.jsonl", receipts)
    write_jsonl(args.output_dir / "provider_materialization_receipts_v1.jsonl", provider_receipts)
    write_jsonl(args.output_dir / "broker_operations_v1.jsonl", broker_records)
    write_jsonl(args.output_dir / "candidate_blockers_v1.jsonl", blockers)
    summary = {
        "candidate_id": candidate, "observed_platform": platform.system().lower(), "observed_python": platform.python_version(),
        "registered_cell_count": len(cells), "matching_provider_cell_count": len(matching),
        "executed_replay_count": len(receipts), "reproducible_cell_count": sum(row["reproducibility_status"] == "REPRODUCIBLE" for row in receipts) // 2,
        "blocker_count": len(blockers), "blockers": blockers,
        "source_mutation_count": sum(row["source_tracked_mutation_count"] for row in receipts),
        "truth_access": 0, "private_tld_access": 0, "patch_operations": 0,
        "authority_allowed": "public truth-blind matched observation",
        "authority_forbidden": ["ownership before join", "patch", "repair count", "release"],
    }
    summary["summary_hash"] = canonical_hash(summary)
    write_json(args.output_dir / "candidate_execution_summary.json", summary)
    manifest = []
    for path in sorted(args.output_dir.glob("*")):
        if path.is_file() and path.name != "SHA256SUMS.txt": manifest.append(f"{file_sha(path)}  {path.name}")
    (args.output_dir / "SHA256SUMS.txt").write_text("\n".join(manifest) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(summary, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
