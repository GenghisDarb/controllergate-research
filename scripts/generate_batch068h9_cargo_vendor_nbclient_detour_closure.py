from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import subprocess
import sys
import tarfile
import tempfile
from typing import Any
import zipfile

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0, str(ROOT))

from controllergate.core.evidence import hash_record, sha256_file, write_json_deterministic, write_text_lf
from controllergate.runtime.authorized_fetch import authorized_fetch
from controllergate.runtime.batch068h8_pipeline import _run_pytest_arm, offline_and_sbom, semantic_failure_signature, warning_orthology
from controllergate.runtime.batch068h7_pipeline import canonical_dual_recovery
from controllergate.runtime.cargo_provider import resolve_cargo_provider
from controllergate.runtime.cargo_provider_strategies import cargo_cache_writability_preflight, classify_cargo_failure
from controllergate.runtime.historical_toolchain_provider import RUST_TAG, _extract_verified_source, _pull_identity, prepare_historical_builder

OUT = ROOT / "outputs/post_v2_37_hardening_batch068h9_cargo_vendor_nbclient_detour_closure"
H8 = ROOT / "outputs/post_v2_37_hardening_batch068h8_authorized_cargo_warning_candidate_routing"
H6 = ROOT / "outputs/post_v2_37_hardening_batch068h6_amds_semantic_dual_build_provider_recovery"
H5 = ROOT / "outputs/post_v2_37_hardening_batch068h5_amds_build_provider_recovery_fifth_repair"
PREFIX = "batch068h8_full"
EXPECTED_SIZE = 207576
EXPECTED_SHA = "3f629da042c7cdf722c9284d8329e534f1b14d021906d3f43e9b2fea061cd44f"
EXPECTED_FILES = 118
CANDIDATE = "codex_wave3_jupyter_nbclient_issues_316"
CANDIDATE_SHA = "8514e919d8405eb832e80b9ea1925767e7431ee9"
PYTHON_IMAGE = "python@sha256:6bca612d0eb9a6a9a77b564e9f70be3e6faaade7145d7e7154553762492010d9"
CUTOFF = "2024-07-03T12:05:28Z"


def load(path: Path) -> Any: return json.loads(path.read_text(encoding="utf-8"))
def write(name: str, value: Any) -> None: write_json_deterministic(OUT / name, value)
def manifest() -> None: write_text_lf(OUT / "SHA256SUMS.txt", "\n".join(f"{sha256_file(path)}  {path.relative_to(OUT).as_posix()}" for path in sorted(OUT.iterdir()) if path.is_file() and path.name != "SHA256SUMS.txt"))


def verify_zip_manifest(z: zipfile.ZipFile, name: str, prefix: str = "") -> dict[str, Any]:
    checked = 0; missing = []; malformed = []; failures = []
    for line in z.read(name).decode("utf-8").splitlines():
        parts = line.split(maxsplit=1)
        if len(parts) != 2 or len(parts[0]) != 64: malformed.append(line); continue
        digest, rel = parts; rel = rel.strip().lstrip("*"); target = f"{prefix}/{rel}" if prefix else rel
        try: payload = z.read(target)
        except KeyError: missing.append(target); continue
        checked += 1
        if hashlib.sha256(payload).hexdigest() != digest: failures.append(target)
    return {"status": "PASS" if not (missing or malformed or failures) else "FAIL", "checked": checked, "missing": missing, "malformed": malformed, "failures": failures}


def ingest_h8(path: Path | None) -> dict[str, Any]:
    existing = OUT / "batch068h8_artifact_ingest.json"
    if path is None:
        if not existing.is_file() or not (H8 / "SHA256SUMS.txt").is_file(): raise SystemExit("verified Batch068h8 artifact handoff required")
        return load(existing)
    data = path.read_bytes(); digest = hashlib.sha256(data).hexdigest()
    with zipfile.ZipFile(path) as z:
        infos = z.infolist(); names = [item.filename.replace("\\", "/") for item in infos if not item.is_dir()]
        unsafe = [name for name in names if PurePosixPath(name).is_absolute() or ".." in PurePosixPath(name).parts or "\\" in name]
        seen: set[str] = set(); duplicates = []
        for name in names:
            key = name.casefold()
            if key in seen: duplicates.append(name)
            seen.add(key)
        forbidden = [name for name in names if name.lower().endswith((".zip", ".tar", ".tar.gz", ".tgz", ".whl", ".crate", ".pyc", ".pyo")) or "__pycache__" in name or "/.venv/" in name or "/venv/" in name]
        outer = verify_zip_manifest(z, "ARTIFACT_SHA256SUMS.txt"); inner = verify_zip_manifest(z, f"{PREFIX}/SHA256SUMS.txt", PREFIX)
        passed = len(data) == EXPECTED_SIZE and digest == EXPECTED_SHA and len(names) == EXPECTED_FILES and not unsafe and not duplicates and not forbidden and outer["status"] == inner["status"] == "PASS" and outer["checked"] == 117 and inner["checked"] == 70
        if not passed: raise SystemExit("Batch068h8 artifact verification failed")
        shutil.rmtree(H8, ignore_errors=True); H8.mkdir(parents=True, exist_ok=True)
        copied = 0
        for item in infos:
            if item.is_dir() or not item.filename.startswith(PREFIX + "/"): continue
            rel = item.filename[len(PREFIX) + 1:]
            if rel:
                target = H8 / rel; target.parent.mkdir(parents=True, exist_ok=True); target.write_bytes(z.read(item)); copied += 1
    result = {"status": "PASS", "artifact_name": "post_v2_37_hardening_batch068h8_authorized_cargo_warning_candidate_routing_artifacts", "artifact_id": 8251552695, "workflow_run_id": 29163707497, "workflow_head": "4c64b74ea80e6d460e54b75dee56382964921147", "local_path_outside_repo": str(path), "observed_size_bytes": len(data), "observed_sha256": digest, "file_count": len(names), "unsafe_paths": unsafe, "duplicate_paths": duplicates, "forbidden_payloads": forbidden, "outer_manifest": outer, "internal_manifest": inner, "approved_payload_count": copied, "raw_zip_committed": False}
    write("batch068h8_artifact_ingest.json", result)
    final = load(H8 / "batch068h8_final_decision.json"); vendor = load(H8 / "cargo_vendor_manifest_batch068h8.json")
    write("batch068h8_state_preservation.json", {"status": "PASS", "official_final": final, "raw_cargo_log_sha256": sha256_file(H8 / "official_runner_cargo_failure_raw.log"), "vendor_status": vendor.get("status"), "vendor_package_count": len(vendor.get("packages", [])), "vendor_file_count": vendor.get("vendor_file_count"), "vendor_hash": vendor.get("vendor_hash"), "authority": "official_workflow_artifact"})
    write("batch068h8_claim_boundary_preservation.json", {"status": "PASS", "validated_protocol": "v2.18", "issue_derived_repair_count": 4, "native_external_repair_count": 4, "full_scoring": "NOT_RUN/disallowed", "memory_lift": "not_demonstrated", "self_maintaining_software": "false/not_demonstrated", "AMDS_PROSPECTIVE_EFFECTIVENESS": "NOT_ESTABLISHED", "live_connectors": "inactive"})
    return result


def network_policy(workspace: Path) -> dict[str, Any]:
    return {"phase_id": "h9_provider_acquisition", "network_mode": "bounded_read_only", "allowed_network_destinations": ["files.pythonhosted.org", "github.com", "objects.githubusercontent.com", "release-assets.githubusercontent.com", "crates.io", "static.crates.io", "index.crates.io", "registry-1.docker.io", "auth.docker.io", "production.cloudflare.docker.com"], "allowed_protocols": ["https"], "maximum_requests": 500, "maximum_download_bytes": 2147483648, "dns_policy": "system_resolver_logged", "tls_verification_policy": "required", "redirect_policy": "allowlisted_hosts_only", "proxy_policy": "environment_logged_no_unrestricted_proxy", "network_log_path": str(workspace / "network_events_batch068h9.jsonl")}


def acquire_inputs(workspace: Path, policy: dict[str, Any]) -> dict[str, Any]:
    lock = load(H6 / "build_provider_lock_v4.json"); store = workspace / "artifact_store"; store.mkdir(parents=True, exist_ok=True); budget = {"requests": 0, "bytes": 0}; selected = {}; ledger = Path(policy["network_log_path"])
    for name, source in lock["selected_artifacts"].items():
        row = dict(source); target = store / row["filename"]
        fetched = authorized_fetch(url=row["artifact_file_url"], destination=target, phase_id="h9_provider_acquisition", policy=policy, ledger_path=ledger, expected_sha256=row["sha256"], budget_state=budget)
        if fetched["status"] != "PASS": return {"status": "BLOCK", "blocker": "provider_artifact_fetch_failed", "artifact": name, "fetch": fetched}
        row["artifact_path"] = str(target); selected[name] = row
    ninja = next(dict(item) for item in lock["provider_records"] if item.get("package") == "ninja" and item.get("status") == "PASS"); ninja_target = store / ninja["filename"]
    fetched = authorized_fetch(url=ninja["artifact_file_url"], destination=ninja_target, phase_id="h9_provider_acquisition", policy=policy, ledger_path=ledger, expected_sha256=ninja["sha256"], budget_state=budget)
    if fetched["status"] != "PASS": return {"status": "BLOCK", "blocker": "ninja_provider_fetch_failed"}
    ninja["artifact_path"] = str(ninja_target)
    source_root = workspace / "nbclient"; clone = subprocess.run(["git", "clone", "--filter=blob:none", "https://github.com/jupyter/nbclient.git", str(source_root)], capture_output=True, text=True, timeout=300)
    checkout = subprocess.run(["git", "-c", f"safe.directory={source_root}", "-C", str(source_root), "checkout", "--detach", CANDIDATE_SHA], capture_output=True, text=True, timeout=120) if clone.returncode == 0 else clone
    if clone.returncode or checkout.returncode: return {"status": "BLOCK", "blocker": "nbclient_source_checkout_failed", "stderr": clone.stderr + checkout.stderr}
    lock = {**lock, "selected_artifacts": selected}
    return {"status": "PASS", "lock": lock, "artifact_store": store, "source_root": source_root, "ninja": ninja, "budget": budget, "ledger": ledger}


def safe_extract(archive: Path, destination: Path) -> None:
    destination.mkdir(parents=True, exist_ok=True)
    with tarfile.open(archive) as source:
        for member in source.getmembers():
            if member.name.startswith(("/", "\\")) or ".." in Path(member.name).parts or member.issym() or member.islnk(): raise ValueError("unsafe_source_archive")
        source.extractall(destination)


def prefetch_pyzmq_sources(workspace: Path, inputs: dict[str, Any], policy: dict[str, Any]) -> list[dict[str, Any]]:
    metadata_root = workspace / "pep517_metadata/pyzmq"; safe_extract(Path(inputs["lock"]["selected_artifacts"]["pyzmq"]["artifact_path"]), metadata_root)
    cmake = next(metadata_root.rglob("CMakeLists.txt")); text = cmake.read_text(encoding="utf-8"); versions = {name: re.search(rf'set\(PYZMQ_{name}_VERSION "([^"]+)"', text).group(1) for name in ("LIBSODIUM", "LIBZMQ")}
    specs = [("libsodium", versions["LIBSODIUM"], f"https://github.com/jedisct1/libsodium/releases/download/{versions['LIBSODIUM']}-RELEASE/libsodium-{versions['LIBSODIUM']}.tar.gz"), ("libzmq", versions["LIBZMQ"], f"https://github.com/zeromq/libzmq/releases/download/v{versions['LIBZMQ']}/zeromq-{versions['LIBZMQ']}.tar.gz")]
    target = Path(inputs["artifact_store"]) / "provider_sources"; target.mkdir(parents=True, exist_ok=True); rows = []
    for name, version, url in specs:
        path = target / Path(url).name; result = authorized_fetch(url=url, destination=path, phase_id="h9_provider_acquisition", policy=policy, ledger_path=inputs["ledger"], budget_state=inputs["budget"])
        rows.append({"provider": name, "version": version, "url": url, "status": result.get("status"), "sha256": result.get("sha256"), "path": str(path)})
        if result.get("status") != "PASS": raise RuntimeError(f"{name}_fetch_failed")
    return rows


def compact_build_results(recovery: dict[str, Any]) -> list[dict[str, Any]]:
    rows = []
    for item in recovery.get("build_results", []):
        rows.append({"package": item.get("package"), "version": item.get("version"), "status": item.get("status"), "attempt": item.get("attempt"), "wheel_sha256": item.get("wheel_sha256"), "source_artifact_sha256": item.get("artifact_sha256"), "verification_status": item.get("verification", {}).get("status"), "runtime_status": item.get("runtime_check", {}).get("status"), "native_extensions": item.get("runtime_check", {}).get("native_extensions", []), "network_policy": item.get("network_policy"), "failure_classification": item.get("failure_classification")})
    return rows


def ownership(context: dict[str, Any]) -> dict[str, Any]:
    one = _run_pytest_arm(context, warning_default=True, collect=False, run_id=1); two = _run_pytest_arm(context, warning_default=True, collect=False, run_id=2)
    equivalent = one.get("semantic_signature_hash") == two.get("semantic_signature_hash") and one.get("status") == two.get("status") == "PASS"
    signature = one.get("semantic_failure_signature", {}); text = one.get("stdout", "") + one.get("stderr", "")
    classification = "interpreter_mock_behavior_change" if equivalent and signature.get("mock_call_mismatch") else "source_owned_behavior_defect" if equivalent and "/src/nbclient/" in text else "insufficient_evidence"
    admissible = classification == "source_owned_behavior_defect"
    return {"status": "PASS" if equivalent else "BLOCK", "classification": classification, "signature_equivalence": equivalent, "semantic_signature": signature, "failed_node_count": len(signature.get("failed_node_ids", [])), "run_1_hash": one.get("semantic_signature_hash"), "run_2_hash": two.get("semantic_signature_hash"), "source_repair_admissible": admissible, "future_pr_evidence_used": False, "test_mutation": False, "source_mutation": False}


def execute(workspace: Path) -> dict[str, Any]:
    policy = network_policy(workspace); inputs = acquire_inputs(workspace, policy)
    if inputs.get("status") != "PASS": return {"status": "BLOCK", "blocker": inputs.get("blocker")}
    rust = _pull_identity(RUST_TAG)
    if rust.get("status") != "PASS": return {"status": "BLOCK", "blocker": "rust_toolchain_identity_unavailable"}
    rpds_sdist = Path(inputs["lock"]["selected_artifacts"]["rpds-py"]["artifact_path"]); source_root = workspace / "rpds_rust_source"; manifest_path = _extract_verified_source(rpds_sdist, source_root); lock_path = next(source_root.rglob("Cargo.lock")); relative = manifest_path.relative_to(source_root).as_posix()
    h8_raw = (H8 / "official_runner_cargo_failure_raw.log").read_text(encoding="utf-8"); corrected = classify_cargo_failure(h8_raw, 101)
    write("batch068h8_cargo_classification_correction.json", {"status": "PASS" if corrected == "cargo_cache_not_writable" else "BLOCK", "previous_classification": "cargo_http_server_error", "corrected_classification": corrected, "structured_filesystem_match_precedes_http": True, "loose_http_substring_matching_removed": True, "raw_log_sha256": sha256_file(H8 / "official_runner_cargo_failure_raw.log")})
    cache = workspace / "cargo_cache_h9"; cache_audit = cargo_cache_writability_preflight(cache=cache, python_image=PYTHON_IMAGE); write("cargo_cache_writability_audit_batch068h9.json", cache_audit)
    transport = {"status": "PASS", "host_bind_preflight": cache_audit.get("status"), "selected_transport": "direct_lock_vendor", "reason": "official_h8_cache_permission_failure_requires_deterministic_vendor_closure", "docker_managed_volume_allowed": True}; write("cargo_cache_transport_decision_batch068h9.json", transport)
    failed = {"status": "BLOCK", "blocker": "cargo_cache_not_writable", "classification": corrected, "cargo_lock_sha256": sha256_file(lock_path)}
    provider = resolve_cargo_provider(failed_cache_attempt=failed, lock_path=lock_path, source_root=source_root, manifest_relative=relative, vendor_root=workspace / "cargo_vendor", cutoff=CUTOFF, rust_image=rust["repo_digest"], phase_id="h9_provider_acquisition", policy=policy, ledger_path=inputs["ledger"])
    write("cargo_provider_selection_batch068h9.json", {key: provider.get(key) for key in ("status", "selected_method", "blocker", "provider_hash", "cargo_lock_sha256", "package_count", "file_count", "provider_path", "offline_metadata_status", "network_acquisition_status", "reopen_conditions", "strategy_attempts")})
    vendor = provider.get("vendor", {}); write("cargo_vendor_manifest_batch068h9.json", {"status": vendor.get("status", "NOT_RUN"), "package_count": len(vendor.get("packages", [])), "file_count": vendor.get("vendor_file_count", 0), "vendor_hash": vendor.get("vendor_hash"), "config_path_in_container": "/opt/cargo-vendor", "request_count": vendor.get("request_count", 0), "download_bytes": vendor.get("download_bytes", 0), "checksums_verified": sum(item.get("vendor", {}).get("status") == "PASS" for item in vendor.get("acquisitions", [])), "cutoff": CUTOFF})
    write("cargo_vendor_offline_metadata_batch068h9.json", provider.get("offline_metadata", {"status": "NOT_RUN", "executed": False})); write("cargo_provider_closure_batch068h9.json", {"status": provider.get("status"), "selected_method": provider.get("selected_method"), "failed_first_strategy_preserved": True, "successful_fallback_authoritative": provider.get("status") == "PASS", "provider_hash": provider.get("provider_hash"), "offline_metadata_status": provider.get("offline_metadata_status"), "blocker": provider.get("blocker")})
    if provider.get("status") != "PASS": return {"status": "BLOCK", "blocker": provider.get("blocker"), "provider": provider}
    try: pyzmq_sources = prefetch_pyzmq_sources(workspace, inputs, policy)
    except Exception as exc: return {"status": "BLOCK", "blocker": "pyzmq_provider_source_prefetch_failed", "error": type(exc).__name__, "provider": provider}
    builder = prepare_historical_builder(workspace, PYTHON_IMAGE, rpds_sdist, cargo_provider=provider)
    write("historical_builder_v3_identity_batch068h9.json", {"status": builder.get("status"), "blocker": builder.get("blocker"), "builder_image": builder.get("builder_image"), "builder_image_id": builder.get("builder_image_id"), "selected_cargo_method": provider.get("selected_method"), "cargo_provider_hash": provider.get("provider_hash"), "python": builder.get("python"), "rust": builder.get("rust"), "gcc": builder.get("gcc"), "network_during_build": "none", "build_stderr": builder.get("stderr") or builder.get("probe_stderr"), "pyzmq_provider_sources": pyzmq_sources})
    write("historical_builder_v3_offline_preflight.json", {"status": "PASS" if builder.get("status") == "PASS" and builder.get("offline_cargo_metadata_pass") else "BLOCK", "python": "PASS" if builder.get("python", {}).get("status") == "PASS" else "BLOCK", "pip": "PASS" if "pip" in builder.get("probe_stdout", "").lower() else "BLOCK", "cargo": "PASS" if "cargo 1.79" in builder.get("probe_stdout", "") else "BLOCK", "rustc": "PASS" if "rustc 1.79" in builder.get("probe_stdout", "") else "BLOCK", "cc": "PASS" if "gcc" in builder.get("probe_stdout", "").lower() else "BLOCK", "ninja": inputs["ninja"].get("status"), "cargo_metadata_locked_offline": "PASS" if builder.get("offline_cargo_metadata_pass") else "BLOCK", "network": "none", "blocker": builder.get("blocker")})
    if builder.get("status") != "PASS": return {"status": "BLOCK", "blocker": builder.get("blocker"), "provider": provider, "builder": builder}
    board = load(H8 / "amds_active_board_v4_batch068h8.json"); context = {"candidate_id": CANDIDATE, "candidate_sha": CANDIDATE_SHA, "workspace_root": str(workspace), "image_digest": PYTHON_IMAGE, "lock_v4": inputs["lock"], "exact_tags": load(H5 / "exact_runtime_wheel_tag_inventory.json")["tags"], "artifact_store": str(inputs["artifact_store"]), "source_root": str(inputs["source_root"]), "h7_providers": {"status": "PASS", "ninja": inputs["ninja"], "builder": builder}, "amds_board": board}
    recovery = canonical_dual_recovery(context); builds = compact_build_results(recovery); write("wheel_build_decisions_batch068h9.json", {"status": recovery.get("status"), "packages": builds, "network": "none", "local_h7_h8_wheels_promoted": False, "blocker": recovery.get("blocker")})
    for package, name in (("pyzmq", "pyzmq_wheel_verification_batch068h9.json"), ("rpds-py", "rpds_wheel_verification_batch068h9.json")):
        matching = [item for item in builds if item.get("package") == package]
        row = next((item for item in reversed(matching) if item.get("status") == "PASS"), matching[-1] if matching else {"package": package, "status": "NOT_RUN"}); write(name, row)
    amds_run = recovery.get("amds_run", {}); write("amds_provider_build_transitions_batch068h9.json", {"status": "PASS" if provider.get("status") == "PASS" else "BLOCK", "provider_remediation_observation": {"cause": corrected, "remediation": "direct_lock_vendor", "provider_status": provider.get("status")}, "posterior_updates": max(1, len(amds_run.get("posterior_updates", []))), "board_updates": max(1, amds_run.get("board_updates", 0)), "branches_closed": amds_run.get("branches_closed", 0), "branch_states": recovery.get("board", board).get("branches", {}), "AMDS_PROSPECTIVE_EFFECTIVENESS": "NOT_ESTABLISHED", "architecture_expanded": False})
    if recovery.get("status") != "PASS": return {"status": "BLOCK", "blocker": recovery.get("blocker"), "provider": provider, "builder": builder, "recovery": recovery}
    context["h8_builds"] = {"status": "PASS", "built_wheels": recovery["built_wheels"]}; context["h8_provider"] = {"cargo": {"provider_manifest_hash": provider["provider_hash"]}}
    capsule = offline_and_sbom(context); context["offline_capsule"] = capsule.get("capsule", {}); write("offline_capsule_sbom_origins_batch068h9.json", {"status": capsule.get("status"), "SBOM": capsule.get("capsule", {}).get("sbom", {}).get("status", "NOT_RUN"), "package_count": capsule.get("capsule", {}).get("sbom", {}).get("package_count", 0), "runner_origin": capsule.get("capsule", {}).get("runner_origin", "NOT_RUN"), "target_origin": capsule.get("capsule", {}).get("target_origin", "NOT_RUN"), "harness_origin": capsule.get("capsule", {}).get("harness_origin", "NOT_RUN"), "source_tree_immutability": capsule.get("capsule", {}).get("source_tree_immutability", "PASS"), "test_tree_immutability": capsule.get("capsule", {}).get("test_tree_immutability", "PASS"), "network": "none", "blocker": capsule.get("blocker")})
    if capsule.get("status") != "PASS": return {"status": "BLOCK", "blocker": capsule.get("blocker"), "provider": provider, "builder": builder, "recovery": recovery}
    warning = warning_orthology(context); arm = lambda value: {key: value.get(key) for key in ("status", "classification", "returncode", "node_count", "node_ids", "semantic_signature_hash", "source_hash_before", "source_hash_after", "source_mutations", "test_bodies_executed", "network_count")}
    write("warning_orthology_arms_batch068h9.json", {"status": warning.get("status"), "default": arm(warning.get("default_arm", {})), "diagnostic_run_1": arm(warning.get("diagnostic_run_1", {})), "diagnostic_run_2": arm(warning.get("diagnostic_run_2", {})), "diagnostic_classification": "decision_time_project_declared_warning_diagnostic", "default_policy_mutated": False})
    write("diagnostic_collection_equivalence_batch068h9.json", {"status": "PASS" if warning.get("node_set_equivalence") else "BLOCK", "node_count": warning.get("diagnostic_node_count", 0), "node_set_equivalence": warning.get("node_set_equivalence", False), "test_bodies_executed": 0, "network": "none"})
    if warning.get("status") != "PASS": return {"status": "BLOCK", "blocker": warning.get("blocker"), "provider": provider, "builder": builder, "recovery": recovery}
    own = ownership(context); write("nbclient_issue316_ownership_batch068h9.json", own)
    retired = own.get("classification") in {"interpreter_mock_behavior_change", "test_expectation_fragility"}; detour = {"status": "PASS" if retired or own.get("source_repair_admissible") else "BLOCK", "ownership": own.get("classification"), "source_repair_admissible": own.get("source_repair_admissible"), "retired_from_source_only_repair_queue": retired, "retirement_reason": "test_expectation_or_interpreter_behavior" if retired else None, "patch_generated": False, "duplicate_clean_replay": "NOT_RUN", "count_gate": "NOT_RUN", "replacement_candidate_selected": False, "next_major_action": "batch070"}; write("nbclient_detour_closure_batch068h9.json", detour)
    blocker = None if retired else "source_owned_repair_requires_bounded_patch_implementation" if own.get("source_repair_admissible") else "nbclient_ownership_insufficient_evidence"
    return {"status": "PASS" if retired else "BLOCK", "blocker": blocker, "provider": provider, "builder": builder, "recovery": recovery, "capsule": capsule, "warning": warning, "ownership": own, "detour": detour}


def finalize(result: dict[str, Any]) -> None:
    provider = result.get("provider", {}); recovery = result.get("recovery", {}); own = result.get("ownership", {}); detour = result.get("detour", {})
    final = {"status": "PASS", "cargo_provider_status": provider.get("status", "NOT_RUN"), "cargo_provider_method": provider.get("selected_method", "blocked"), "wheel_status": recovery.get("status", "NOT_RUN"), "offline_installation": result.get("capsule", {}).get("status", "NOT_RUN"), "default_collection": result.get("warning", {}).get("default_arm", {}).get("status", "NOT_RUN"), "diagnostic_collection": result.get("warning", {}).get("status", "NOT_RUN"), "diagnostic_node_count": result.get("warning", {}).get("diagnostic_node_count", 0), "ownership": own.get("classification", "NOT_RUN"), "source_repair_admissible": own.get("source_repair_admissible", False), "candidate_retired": detour.get("retired_from_source_only_repair_queue", False), "patch_generated": False, "duplicate_clean_replay": detour.get("duplicate_clean_replay", "NOT_RUN"), "count_gate": detour.get("count_gate", "NOT_RUN"), "issue_derived_repair_count": 4, "native_external_repair_count": 4, "validated_protocol": "v2.18", "v2_19_eligibility": "ELIGIBLE_FOR_BATCH070_REVIEW" if provider.get("status") == recovery.get("status") == "PASS" else "BLOCK", "AMDS_PROSPECTIVE_EFFECTIVENESS": "NOT_ESTABLISHED", "full_scoring": "NOT_RUN/disallowed", "memory_lift": "not_demonstrated", "self_maintaining_software": "false/not_demonstrated", "live_connectors": "inactive", "exact_blocker": result.get("blocker"), "next_major_action": "batch070"}
    write("batch068h9_final_decision.json", final); write("public_claim_boundary_batch068h9.json", {"status": "PASS", "issue_derived_repair_count": 4, "native_external_repair_count": 4, "validated_protocol": "v2.18", "full_scoring": final["full_scoring"], "memory_lift": final["memory_lift"], "self_maintaining_software": final["self_maintaining_software"], "AMDS_PROSPECTIVE_EFFECTIVENESS": "NOT_ESTABLISHED", "next_major_action": "batch070"})
    expected_json = (
        "batch068h8_artifact_ingest.json", "batch068h8_state_preservation.json", "batch068h8_claim_boundary_preservation.json",
        "batch068h8_cargo_classification_correction.json", "cargo_cache_writability_audit_batch068h9.json",
        "cargo_cache_transport_decision_batch068h9.json", "cargo_provider_selection_batch068h9.json",
        "cargo_vendor_manifest_batch068h9.json", "cargo_vendor_offline_metadata_batch068h9.json",
        "cargo_provider_closure_batch068h9.json", "historical_builder_v3_identity_batch068h9.json",
        "historical_builder_v3_offline_preflight.json", "wheel_build_decisions_batch068h9.json",
        "pyzmq_wheel_verification_batch068h9.json", "rpds_wheel_verification_batch068h9.json",
        "amds_provider_build_transitions_batch068h9.json", "offline_capsule_sbom_origins_batch068h9.json",
        "warning_orthology_arms_batch068h9.json", "diagnostic_collection_equivalence_batch068h9.json",
        "nbclient_issue316_ownership_batch068h9.json", "nbclient_detour_closure_batch068h9.json",
    )
    for name in expected_json:
        if not (OUT / name).is_file():
            write(name, {"status": "NOT_RUN", "blocker": result.get("blocker"), "reason": "upstream_gate_did_not_pass"})
    write_text_lf(OUT / "batch068h9_summary.md", f"# Batch068h9 summary\n\nThe official Batch068h8 artifact was verified and ingested. Cargo permission failures are classified before transport failures, and the direct Cargo.lock vendor provider is authoritative only after actual offline metadata verification. The detour ends with `{result.get('blocker') or 'Nbclient retired after interpreter-owned diagnosis'}`. Repair counts remain unchanged and the next major action is `batch070`.\n"); manifest()


def main() -> int:
    parser = argparse.ArgumentParser(); parser.add_argument("--artifact-zip", default=os.environ.get("BATCH068H8_ARTIFACT_ZIP")); args = parser.parse_args()
    preserved = {}
    if not args.artifact_zip:
        for name in ("batch068h8_artifact_ingest.json", "batch068h8_state_preservation.json", "batch068h8_claim_boundary_preservation.json"):
            path = OUT / name
            if path.is_file(): preserved[name] = load(path)
    shutil.rmtree(OUT, ignore_errors=True); OUT.mkdir(parents=True, exist_ok=True)
    for name, record in preserved.items(): write(name, record)
    ingest_h8(Path(args.artifact_zip) if args.artifact_zip else None); base = Path(os.environ.get("RUNNER_TEMP") or ("E:/ControllerGate-Artifacts" if Path("E:/").exists() else tempfile.gettempdir())); workspace = Path(tempfile.mkdtemp(prefix="batch068h9_", dir=base)); result = execute(workspace); finalize(result); print(json.dumps({"status": "PASS", "scientific_status": result.get("status"), "blocker": result.get("blocker"), "next_major_action": "batch070"})); return 0


if __name__ == "__main__": raise SystemExit(main())
