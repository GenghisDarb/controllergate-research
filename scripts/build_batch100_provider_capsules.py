#!/usr/bin/env python3
"""Compile exact or explicitly limited provider capsules for Batch100."""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from controllergate.evidence.provider_capsule_v2 import ProviderCapsuleV2, canonical_hash, verify_provider_capsule


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n" for row in rows), encoding="utf-8", newline="\n")


def write_json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, sort_keys=True, indent=2) + "\n", encoding="utf-8", newline="\n")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--registry", type=Path, default=Path("configs/batch100_incident_provider_registry_v2.jsonl"))
    parser.add_argument("--output-root", type=Path, required=True)
    args = parser.parse_args()
    providers = read_jsonl(args.registry)
    args.output_root.mkdir(parents=True, exist_ok=True)
    observed_version = platform.python_version()
    git_version = subprocess.run(["git", "--version"], capture_output=True, text=True, check=False).stdout.strip()
    variants = {
        "darker_issue_112_relative_git_dir": [("3.7", "linux", "incident-series")],
        "py_bugger_issue_65": [("3.11", "linux", "reported-cli-sensitivity")],
        "cloudpickle_507_py313_typevar_distutils": [("3.11", "linux", "supported-control"), ("3.12", "linux", "incident-no-setuptools"), ("3.12", "linux", "incident-with-setuptools")],
        "freezegun_547_py313_datetimes_assertion": [("3.12", "linux", "supported-control"), ("3.13.0b1", "linux", "exact-incident")],
        "audioread_144_py313_aifc_removed": [("3.12", "linux", "supported-control"), ("3.13.0b2", "linux", "exact-incident")],
        "pytest_13480_wdefault_unraisable_threadexception": [("3.13.3", "linux", "exact-incident")],
        "incident_openbb_7585_modular_openapi_reproducer": [("3.11", "debian-12", "incident")],
        "incident_poetry_10974_init_duplicate_name": [("3.13", "windows", "exact-platform"), ("3.13", "linux", "secondary-control")],
    }
    rows: list[dict] = []
    for provider in providers:
      for requested_micro, requested_os, variant in variants[provider["candidate_id"]]:
        exact = observed_version == requested_micro and platform.system().lower().startswith(requested_os.split("-")[0])
        micro_unresolved = requested_micro in {"3.13.0b1", "3.13.0b2"}
        parity = "EXACT" if exact else ("MICRO_UNRESOLVED" if micro_unresolved else "PLATFORM_UNAVAILABLE")
        observed = observed_version if exact else None
        row = ProviderCapsuleV2(
            capsule_id=f"provider:{provider['candidate_id']}:{variant}",
            candidate_id=provider["candidate_id"], implementation=sys.implementation.name,
            requested_version=requested_micro, observed_version=observed,
            version_parity=parity, os=requested_os, architecture="x86_64",
            abi=sys.implementation.cache_tag or "unknown", soabi=None,
            setup_python_identity=f"actions-setup-python-or-authenticated-image:{requested_micro}",
            dependency_lock_hash=canonical_hash([provider["candidate_id"], variant, "frozen-dependency-contract"]),
            dependency_graph_hash=canonical_hash([provider["candidate_id"], variant, "materialize-in-isolated-job"]),
            environment_hash=canonical_hash({"locale": "C.UTF-8", "timezone": "UTC"}),
            locale="C.UTF-8", timezone="UTC", git_version=git_version,
            runner_image=f"requested:{requested_os};local-compiler:{platform.platform()}",
            resource_budget={"timeout_seconds": 1800, "processes": 16, "network_requests": 0},
            acquisition_phase_network="bounded_read_only_acquisition",
            offline_execution_network="loopback_only" if "openbb" in provider["candidate_id"] else "none",
        ).record()
        rows.append(row)
    write_jsonl(args.output_root / "provider_capsule_registry_v2.jsonl", rows)
    blockers = [{"candidate_id": row["candidate_id"], "blockers": verify_provider_capsule(row)} for row in rows if verify_provider_capsule(row)]
    exact_count = sum(row["version_parity"] == "EXACT" for row in rows)
    audit = {
        "status": "PASS_WITH_LIMITED_PROVIDER_PARITY" if not blockers else "BLOCK",
        "capsule_count": len(rows), "candidate_coverage": len({row['candidate_id'] for row in rows}), "exact_provider_count": exact_count,
        "limited_provider_count": len(rows) - exact_count, "blockers": blockers,
        "producer": "scripts/build_batch100_provider_capsules.py",
        "execution_depth": "provider identity compilation; no candidate execution",
        "semantic_scope": "provider custody and parity",
        "authority_allowed": "limited-scope sensitivity planning",
        "authority_forbidden": ["exact parity for limited providers", "ownership", "patch", "release"],
    }
    write_json(args.output_root / "capsule_offline_execution_audit.json", {**audit, "offline_or_loopback_count": sum(row["offline_execution_network"] in {"none", "loopback_only"} for row in rows)})
    return 0 if not blockers else 2


if __name__ == "__main__":
    raise SystemExit(main())
