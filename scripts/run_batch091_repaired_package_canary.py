from __future__ import annotations

import argparse
import hashlib
import json
import sys
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from controllergate.deployment.package_canary import execute_repaired_package_canary


OUTPUT = ROOT / "outputs/post_v2_37_hardening_batch091_lossless_capsule_blinded_amds_historical_canary_semantic_critic_closure"


def write(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")


def sha_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--runtime", type=Path, required=True)
    parser.add_argument("--capsule-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=OUTPUT)
    args = parser.parse_args()
    lifecycle = json.loads((args.output / "cloudpickle_installed_historical_lifecycle.json").read_text(encoding="utf-8"))
    if lifecycle.get("status") != "PASS":
        write(args.output / "repaired_package_canary_health_rollback.json", {"status": "BLOCK", "exact_blocker": "cloudpickle_canonical_historical_lifecycle"})
        return 1
    result = execute_repaired_package_canary(
        runtime_root=args.runtime,
        source_capsule=args.capsule_root / "cloudpickle-source.zip",
        provider_capsule=args.capsule_root / "cloudpickle-provider.zip",
        patch_path=ROOT / "outputs/post_v2_37_hardening_batch060d_cloudpickle_class_dict_patch_gate_with_amds_health_review/cloudpickle_class_dict_source_only_patch_candidate.diff",
        patch_sha256="a06b5343f41a49daaa9d6902513966c6796e44124640ba29fcf80ede99d06e63",
        source_commit="a76f0812ccdbbd1397f36d536dc4d57b6d0557d6",
        historical_target=["tests/cloudpickle_test.py::test_extract_class_dict", "-q", "--tb=no"],
        lifecycle_record=lifecycle,
    )
    if result.get("status") != "PASS":
        write(args.output / "repaired_package_canary_health_rollback.json", result)
        print(json.dumps(result, sort_keys=True))
        return 1
    repaired_wheel = Path(result["builds"]["repaired_first"]["wheel"])
    with zipfile.ZipFile(repaired_wheel) as package:
        content = [{"path": item.filename, "size": item.file_size, "sha256": sha_bytes(package.read(item.filename))}
                   for item in package.infolist() if not item.is_dir()]
        licenses = [row for row in content if "license" in row["path"].casefold() or row["path"].casefold().endswith("metadata")]
    build = {
        "status": "PASS", "producer": "controllergate.deployment.package_canary", "source_commit": result["source_commit"],
        "patch_sha256": result["patch_sha256"], "source_tree_hash": result["repaired_source_tree_hash"],
        "test_tree_hash": result["test_tree_hash"], "provider_identity": result["activations"]["repair_provider"]["distribution_graph_sha256"],
        "build_backend": "setuptools.build_meta", "build_frontend": "pip wheel", "network": "none",
        "wheel_sha256": result["builds"]["repaired_first"]["wheel_sha256"],
        "semantic_wheel_hash": sha_bytes(json.dumps(content, sort_keys=True, separators=(",", ":")).encode()),
        "sdist": {"status": "NOT_SUPPORTED_BY_FROZEN_OFFLINE_FRONTEND", "sha256": None},
        "sbom": {"format": "compact-file-SBOM", "component": "cloudpickle", "content_count": len(content)},
        "license_inventory": licenses, "content_manifest": content,
    }
    write(args.output / "repaired_distribution_build.json", build)
    write(args.output / "repaired_distribution_reproducibility.json", {"status": "PASS" if result["reproducible"] else "FAIL", "independent_builds": 2, "byte_identical": result["reproducible"], "bounded_nondeterminism": result["bounded_nondeterminism"]})
    write(args.output / "repaired_distribution_identity.json", {"status": "PASS", "source_commit": result["source_commit"], "patch_sha256": result["patch_sha256"], "wheel_sha256": build["wheel_sha256"], "semantic_wheel_hash": build["semantic_wheel_hash"], "source_tree_hash": result["repaired_source_tree_hash"]})
    write(args.output / "canary_compartment_identity.json", {"status": "PASS", "distinct_compartment_count": 4, "compartments": result["compartments"], "diagnosis_provider_reused": False})
    write(args.output / "canary_target_execution.json", {"status": "PASS" if result["target"]["return_code"] == 0 else "FAIL", **result["target"]})
    write(args.output / "canary_distinct_consumer_execution.json", {"status": "PASS" if result["distinct_consumer"]["return_code"] == 0 else "FAIL", **result["distinct_consumer"]})
    (args.output / "canary_health_events.jsonl").write_text("".join(json.dumps(row, sort_keys=True) + "\n" for row in result["health_events"]), encoding="utf-8", newline="\n")
    write(args.output / "canary_negative_control.json", {"status": "PASS" if result["negative_control_rejected"] else "FAIL", "original_buggy_distribution_rejected": result["negative_control_rejected"], "execution": result["negative_control"]})
    write(args.output / "canary_package_switch.json", result["package_switch"])
    write(args.output / "canary_exact_rollback.json", result["rollback"])
    (args.output / "canary_cleanup_receipts.jsonl").write_text("".join(json.dumps(row, sort_keys=True) + "\n" for row in result["cleanup"]), encoding="utf-8", newline="\n")
    write(args.output / "repaired_package_canary_health_rollback.json", result)
    print(json.dumps({"status": result["status"], "aggregate_result": result["aggregate_result"]}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
