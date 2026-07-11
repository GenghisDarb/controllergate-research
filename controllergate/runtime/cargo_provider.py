from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any

from .cargo_provider_strategies import generate_direct_vendor
from .cargo_provider_verifier import run_offline_cargo_metadata, verify_vendor_manifest


def resolve_cargo_provider(*, failed_cache_attempt: dict[str, Any], lock_path: Path, source_root: Path, manifest_relative: str, vendor_root: Path, cutoff: str, rust_image: str, phase_id: str, policy: dict[str, Any], ledger_path: Path, verified_vendor_capsule: dict[str, Any] | None = None) -> dict[str, Any]:
    strategies = [{"method": "cargo_fetch_cache", "status": failed_cache_attempt.get("status", "BLOCK"), "blocker": failed_cache_attempt.get("blocker"), "classification": failed_cache_attempt.get("classification")}]
    if failed_cache_attempt.get("status") == "PASS":
        lock_hash = hashlib.sha256(lock_path.read_bytes()).hexdigest()
        crates = failed_cache_attempt.get("crate_verification", [])
        closed = failed_cache_attempt.get("cargo_lock_sha256") == lock_hash and failed_cache_attempt.get("provider_file_count", 0) > 0 and bool(crates) and all(item.get("status") == "PASS" for item in crates)
        if not closed:
            strategies[0].update({"status": "BLOCK", "blocker": "cargo_fetch_cache_closure_incomplete"})
        else:
            return {"status": "PASS", "selected_method": "cargo_fetch_cache", "provider_hash": failed_cache_attempt.get("provider_manifest_hash"), "cargo_lock_sha256": lock_hash, "package_count": len(failed_cache_attempt.get("package_catalog", [])), "file_count": failed_cache_attempt.get("provider_file_count", 0), "provider_path": failed_cache_attempt.get("cache_path"), "offline_metadata_status": failed_cache_attempt.get("offline_metadata_status", "BUILDER_PREFLIGHT_REQUIRED"), "network_acquisition_status": "PASS", "reopen_conditions": [], "strategy_attempts": strategies}
    vendor = generate_direct_vendor(lock_path=lock_path, vendor_root=vendor_root, cutoff=cutoff, phase_id=phase_id, policy=policy, ledger_path=ledger_path)
    strategies.append({"method": "direct_lock_vendor", "status": vendor.get("status"), "blocker": vendor.get("blocker")})
    if vendor.get("status") != "PASS":
        if verified_vendor_capsule is not None:
            capsule = dict(verified_vendor_capsule)
            verification = verify_vendor_manifest(capsule)
            capsule_root = Path(capsule.get("vendor_root", ""))
            config_path = Path(capsule.get("config_path", ""))
            lock_matches = capsule.get("cargo_lock_sha256") == hashlib.sha256(lock_path.read_bytes()).hexdigest()
            metadata = run_offline_cargo_metadata(rust_image=rust_image, source_root=source_root, manifest_relative=manifest_relative, vendor_root=capsule_root, cargo_config=config_path) if verification["status"] == "PASS" and lock_matches else {"status": "BLOCK", "blocker": "cargo_vendor_capsule_identity_mismatch", "executed": False}
            passed = verification["status"] == metadata["status"] == "PASS" and lock_matches
            strategies.append({"method": "verified_vendor_capsule", "status": "PASS" if passed else "BLOCK", "blocker": None if passed else metadata.get("blocker")})
            if passed:
                return {"status": "PASS", "selected_method": "verified_vendor_capsule", "provider_hash": capsule.get("vendor_hash"), "cargo_lock_sha256": capsule.get("cargo_lock_sha256"), "package_count": verification.get("package_count", 0), "file_count": verification.get("file_count", 0), "provider_path": str(capsule_root), "cargo_config_path": str(config_path), "offline_metadata_status": "PASS", "network_acquisition_status": "NOT_RUN", "reopen_conditions": [], "strategy_attempts": strategies, "vendor": capsule, "verification": verification, "offline_metadata": metadata}
        return {"status": "BLOCK", "selected_method": "blocked", "blocker": vendor.get("blocker"), "strategy_attempts": strategies, "vendor": vendor, "reopen_conditions": ["regenerate exact Cargo.lock vendor provider"]}
    verification = verify_vendor_manifest(vendor)
    metadata = run_offline_cargo_metadata(rust_image=rust_image, source_root=source_root, manifest_relative=manifest_relative, vendor_root=vendor_root, cargo_config=Path(vendor["config_path"])) if verification["status"] == "PASS" else {"status": "BLOCK", "blocker": "cargo_vendor_verification_failed", "executed": False}
    passed = verification["status"] == metadata["status"] == "PASS"
    return {"status": "PASS" if passed else "BLOCK", "selected_method": "direct_lock_vendor" if passed else "blocked", "blocker": None if passed else metadata.get("blocker") or "cargo_vendor_verification_failed", "provider_hash": vendor.get("vendor_hash"), "cargo_lock_sha256": hashlib.sha256(lock_path.read_bytes()).hexdigest(), "package_count": verification.get("package_count", 0), "file_count": verification.get("file_count", 0), "provider_path": str(vendor_root), "cargo_config_path": vendor.get("config_path"), "offline_metadata_status": metadata.get("status"), "network_acquisition_status": vendor.get("status"), "reopen_conditions": [] if passed else ["actual cargo metadata --locked --offline must pass"], "strategy_attempts": strategies, "vendor": vendor, "verification": verification, "offline_metadata": metadata}
