from __future__ import annotations

from pathlib import Path
from typing import Any

from .evidence import hash_record, sha256_file


ALLOWED_OUTPUT_KEYS = {
    "dependency_recovery",
    "environment_hash",
    "harness_verification",
    "installed_package_freeze",
    "installed_package_hashes",
    "provider_preflight",
    "sanitized_logs",
    "source_checkout_audit",
    "source_commit_verification",
    "target_intent_retry",
    "workspace_purity_report",
}

FORBIDDEN_OUTPUT_KEYS = {
    "credentials",
    "full_external_checkout",
    "secrets",
    "unbounded_logs",
    "unredacted_issue_text",
    "venv",
}


def build_provider_output_bundle(results: dict[str, Any]) -> dict[str, Any]:
    allowed_results = {key: value for key, value in results.items() if key in ALLOWED_OUTPUT_KEYS}
    bundle = {
        "status": "PASS",
        "allowed_keys": sorted(ALLOWED_OUTPUT_KEYS),
        "present_keys": sorted(allowed_results),
        "forbidden_keys_present": sorted(set(results) & FORBIDDEN_OUTPUT_KEYS),
        "contains_full_external_checkout": False,
        "contains_credentials": False,
        "contains_secrets": False,
        "contains_unbounded_logs": False,
        "results": allowed_results,
    }
    return {**bundle, "bundle_sha256": hash_record(bundle)}


def validate_provider_output_bundle(bundle: dict[str, Any]) -> dict[str, Any]:
    forbidden_present = bundle.get("forbidden_keys_present", [])
    unsafe_flags = [
        bundle.get("contains_full_external_checkout") is True,
        bundle.get("contains_credentials") is True,
        bundle.get("contains_secrets") is True,
        bundle.get("contains_unbounded_logs") is True,
    ]
    status = "PASS" if not forbidden_present and not any(unsafe_flags) else "BLOCK"
    return {
        "status": status,
        "forbidden_keys_present": forbidden_present,
        "contains_full_external_checkout": bundle.get("contains_full_external_checkout"),
        "contains_credentials": bundle.get("contains_credentials"),
        "contains_secrets": bundle.get("contains_secrets"),
        "contains_unbounded_logs": bundle.get("contains_unbounded_logs"),
        "blocker": None if status == "PASS" else "provider_output_bundle_invalid",
    }


def output_file_manifest(output_dir: str | Path) -> list[dict[str, Any]]:
    root = Path(output_dir)
    records = []
    if not root.is_dir():
        return records
    for path in sorted(root.rglob("*")):
        if path.is_file():
            records.append(
                {
                    "path": path.relative_to(root).as_posix(),
                    "sha256": sha256_file(path),
                    "size_bytes": path.stat().st_size,
                }
            )
    return records
