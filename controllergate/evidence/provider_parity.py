from __future__ import annotations

import fnmatch
import hashlib
import json
from pathlib import Path
from typing import Any, Iterable, Mapping


EXACT_BLOCKER = "BATCH098_FROZEN_PROVIDER_PARITY_BLOCKED_EXACT"


def canonical_hash(value: object) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")).hexdigest()


def load_provider_contracts(path: str | Path) -> list[dict[str, Any]]:
    rows = [json.loads(line) for line in Path(path).read_text(encoding="utf-8").splitlines() if line.strip()]
    identifiers = [str(row["candidate_id"]) for row in rows]
    if len(rows) != 8 or len(identifiers) != len(set(identifiers)):
        raise ValueError("frozen provider contract cohort must contain eight unique candidates")
    for row in rows:
        supplied = row.get("contract_hash")
        unsigned = {key: value for key, value in row.items() if key != "contract_hash"}
        if supplied != canonical_hash(unsigned):
            raise ValueError(f"frozen provider contract hash mismatch: {row['candidate_id']}")
    return rows


def contract_for_candidate(contracts: Iterable[Mapping[str, Any]], candidate_id: str) -> Mapping[str, Any]:
    matches = [row for row in contracts if row.get("candidate_id") == candidate_id]
    if len(matches) != 1:
        raise ValueError(f"provider contract cardinality invalid: {candidate_id}")
    return matches[0]


def verify_provider_observation(contract: Mapping[str, Any], observation: Mapping[str, Any]) -> dict[str, Any]:
    checks = {
        "implementation": str(observation.get("implementation", "")).casefold() == str(contract["provider_implementation"]).casefold(),
        "exact_version": observation.get("python_version") == contract["provider_exact_version"],
        "cache_tag": observation.get("cache_tag") == contract["provider_cache_tag"],
        "soabi": fnmatch.fnmatch(str(observation.get("soabi", "")), str(contract["provider_soabi_pattern"])),
        "platform_tag": observation.get("platform_tag") == contract["provider_platform_tag"],
        "os_family": str(observation.get("os_family", "")).casefold() == str(contract["provider_os_family"]).casefold(),
        "architecture": str(observation.get("architecture", "")).casefold() == str(contract["provider_architecture"]).casefold(),
        "abi_tag": observation.get("abi_tag") == contract["provider_abi_tag"],
        "runner_image": observation.get("runner_image") == contract["runner_image"],
        "runner_image_version": observation.get("runner_image_version") == contract["runner_image_version"],
        "libc_identity": bool(observation.get("libc_identity")),
        "kernel_identity": bool(observation.get("kernel_identity")),
        "source_commit": observation.get("source_commit") == contract["source_commit"],
        "dependency_graph": observation.get("dependency_graph_hash") == contract["dependency_graph_hash"],
        "runner": observation.get("runner_identity") == contract["runner_identity"],
        "harness": observation.get("harness_identity") == contract["harness_identity"],
        "command": observation.get("command_identity") == contract["command_identity"],
    }
    failures = sorted(key for key, passed in checks.items() if not passed)
    result = {
        "candidate_id": contract["candidate_id"],
        "status": "PASS_EXACT_FROZEN_LINUX_PARITY" if not failures else "BLOCK",
        "exact_blocker": None if not failures else EXACT_BLOCKER,
        "checks": checks,
        "failures": failures,
        "provider_parity_parent_receipt": contract["provider_parity_parent_receipt"],
        "ordinary_patch_authority": False,
        "protected_actuation": False,
        "authority_allowed": "public decision-time provider evidence",
        "authority_forbidden": ["truth", "repair", "source ownership", "count", "release"],
    }
    result["verification_receipt"] = canonical_hash(result)
    return result


def public_provider_negative_controls(contract: Mapping[str, Any]) -> list[dict[str, Any]]:
    base = {
        "implementation": contract["provider_implementation"],
        "python_version": contract["provider_exact_version"],
        "cache_tag": contract["provider_cache_tag"],
        "soabi": contract["provider_soabi_pattern"].replace("*", "x86_64"),
        "platform_tag": contract["provider_platform_tag"],
        "os_family": contract["provider_os_family"],
        "architecture": contract["provider_architecture"],
        "abi_tag": contract["provider_abi_tag"],
        "runner_image": contract["runner_image"],
        "runner_image_version": contract["runner_image_version"],
        "libc_identity": "glibc-test",
        "kernel_identity": "linux-test",
        "source_commit": contract["source_commit"],
        "dependency_graph_hash": contract["dependency_graph_hash"],
        "runner_identity": contract["runner_identity"],
        "harness_identity": contract["harness_identity"],
        "command_identity": contract["command_identity"],
    }
    controls = []
    mutations = {
        "windows_series_only": {"os_family": "windows", "platform_tag": "win-amd64", "runner_image": "windows-2025"},
        "wrong_microrelease": {"python_version": {"3.7.17": "3.7.9", "3.11.15": "3.11.9", "3.13.14": "3.13.0"}[str(contract["provider_exact_version"])]},
    }
    for control_id, mutation in mutations.items():
        observed = {**base, **mutation}
        verified = verify_provider_observation(contract, observed)
        controls.append({"control_id": control_id, "status": "PASS" if verified["status"] == "BLOCK" else "FAIL", "rejected_failures": verified["failures"]})
    return controls
