from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import tempfile
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "examples" / "local_manifest_demo"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def authorize(manifest: dict[str, Any], patch: dict[str, Any]) -> dict[str, Any]:
    allowed = set(manifest["allowed_source_paths"])
    forbidden = tuple(manifest["forbidden_path_prefixes"])
    paths = [change["path"].replace("\\", "/") for change in patch["changes"]]
    blocked = [path for path in paths if path.startswith(forbidden) or path not in allowed]
    return {
        "patch_id": patch["patch_id"],
        "paths": paths,
        "status": "BLOCK" if blocked else "PASS",
        "blocked_paths": blocked,
        "source_only": not blocked,
    }


def apply_patch(workspace: Path, patch: dict[str, Any]) -> list[dict[str, str]]:
    applied: list[dict[str, str]] = []
    for change in patch["changes"]:
        path = workspace / change["path"]
        before = path.read_text(encoding="utf-8")
        if before.count(change["replace"]) != 1:
            raise RuntimeError(f"expected exactly one replacement in {change['path']}")
        path.write_text(before.replace(change["replace"], change["with"]), encoding="utf-8", newline="\n")
        applied.append({"path": change["path"], "sha256": sha256(path)})
    return applied


def validate(workspace: Path, manifest: dict[str, Any]) -> dict[str, Any]:
    module_path = workspace / "demo_app.py"
    spec = importlib.util.spec_from_file_location("controllergate_local_demo_app", module_path)
    if spec is None or spec.loader is None:
        raise RuntimeError("unable to load demo module")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    contract = manifest["required_validation"]
    observed = getattr(module, contract["function"])(contract["input"])
    return {
        "status": "PASS" if observed == contract["expected"] else "FAIL",
        "expected": contract["expected"],
        "observed": observed,
    }


def run_demo() -> dict[str, Any]:
    manifest = load_json(FIXTURE / "manifest.json")
    unsafe = load_json(FIXTURE / "unsafe_patch.json")
    bounded = load_json(FIXTURE / "bounded_patch.json")
    with tempfile.TemporaryDirectory(prefix="controllergate_local_demo_") as temporary:
        workspace = Path(temporary) / "workspace"
        shutil.copytree(FIXTURE, workspace)
        source = workspace / "demo_app.py"
        original = source.read_bytes()
        original_sha = hashlib.sha256(original).hexdigest()
        unsafe_decision = authorize(manifest, unsafe)
        bounded_decision = authorize(manifest, bounded)
        if unsafe_decision["status"] != "BLOCK" or bounded_decision["status"] != "PASS":
            raise RuntimeError("demo authorization contract failed")
        applied = apply_patch(workspace, bounded)
        validation = validate(workspace, manifest)
        source.write_bytes(original)
        rollback_sha = sha256(source)
        proof = {
            "schema_version": "controllergate.local_manifest_demo.proof.v1",
            "status": "PASS" if validation["status"] == "PASS" and rollback_sha == original_sha else "FAIL",
            "credentials_required": False,
            "external_network_used": False,
            "unsafe_patch": unsafe_decision,
            "bounded_patch": bounded_decision,
            "applied_changes": applied,
            "validation": validation,
            "rollback": {
                "status": "PASS" if rollback_sha == original_sha else "FAIL",
                "original_sha256": original_sha,
                "restored_sha256": rollback_sha,
            },
        }
        canonical = json.dumps(proof, sort_keys=True, separators=(",", ":")).encode("utf-8")
        proof["proof_sha256"] = hashlib.sha256(canonical).hexdigest()
        return proof


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the credential-free ControllerGate local manifest demo")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    proof = run_demo()
    rendered = json.dumps(proof, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8", newline="\n")
    print(rendered, end="")
    return 0 if proof["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
