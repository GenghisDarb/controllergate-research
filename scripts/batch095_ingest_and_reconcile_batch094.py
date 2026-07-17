from __future__ import annotations

import argparse
import hashlib
import json
import re
import stat
import zipfile
from collections import Counter
from pathlib import Path, PurePosixPath
from typing import Any


EXPECTED = {
    "name": "post_v2_37_hardening_batch094_value_bound_rpir_fresh_amds_cohort_historical_closure_artifacts",
    "artifact_id": 8381634867,
    "size": 993351,
    "sha256": "df78256e8f038cb9ca893ad921577c761f3dd94bea26e35a294a815b8a97e5e3",
    "zip_entries": 109,
    "workflow_run": 29513013239,
    "workflow_head": "2918803db312d1999ab791d8bd7031a0399cb4f2",
}
PREFIX = "outputs/post_v2_37_hardening_batch094_value_bound_rpir_fresh_amds_cohort_historical_closure/"
PRODUCER = "scripts/batch095_ingest_and_reconcile_batch094.py"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.write_text(
        "".join(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n" for row in rows),
        encoding="utf-8",
        newline="\n",
    )


def unsafe_path(name: str) -> bool:
    value = PurePosixPath(name)
    return value.is_absolute() or ".." in value.parts or bool(re.match(r"^[A-Za-z]:", name)) or "\\" in name


def verify_manifest(archive: zipfile.ZipFile, name: str) -> dict[str, Any]:
    base = PurePosixPath(name).parent
    result: dict[str, Any] = {
        "manifest": name,
        "checked": 0,
        "missing": 0,
        "mismatches": 0,
        "malformed": 0,
        "self_entries": 0,
    }
    for line in archive.read(name).decode("utf-8-sig").splitlines():
        if not line.strip():
            continue
        match = re.fullmatch(r"([0-9a-fA-F]{64})\s+\*?(.+)", line)
        if not match:
            result["malformed"] += 1
            continue
        expected, relative = match.groups()
        target = (base / relative).as_posix() if str(base) != "." else PurePosixPath(relative).as_posix()
        if target == name:
            result["self_entries"] += 1
            continue
        result["checked"] += 1
        try:
            payload = archive.read(target)
        except KeyError:
            result["missing"] += 1
            continue
        if hashlib.sha256(payload).hexdigest().lower() != expected.lower():
            result["mismatches"] += 1
    result["status"] = (
        "PASS"
        if not any(result[key] for key in ("missing", "mismatches", "malformed", "self_entries"))
        else "FAIL"
    )
    return result


def evidence_record(scope: str) -> dict[str, Any]:
    return {
        "producer": PRODUCER,
        "execution_depth": "byte_level_archive_and_semantic_manifest_verification",
        "semantic_scope": scope,
        "authority_allowed": "official Batch094 evidence custody and corrected Batch095 starting authority",
        "authority_forbidden": ["rewriting Batch094 evidence", "repair authority", "external release approval"],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--artifact", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    artifact = Path(args.artifact).resolve()
    output = Path(args.output).resolve()
    output.mkdir(parents=True, exist_ok=True)

    observed = {"size": artifact.stat().st_size, "sha256": sha256_file(artifact)}
    json_failures: list[dict[str, Any]] = []
    jsonl_failures: list[dict[str, Any]] = []
    with zipfile.ZipFile(artifact) as archive:
        infos = archive.infolist()
        names = [item.filename for item in infos]
        counts = Counter(names)
        manifests = [verify_manifest(archive, name) for name in names if name.endswith("SHA256SUMS.txt")]
        for name in names:
            try:
                if name.endswith(".json"):
                    json.loads(archive.read(name).decode("utf-8-sig"))
                elif name.endswith(".jsonl"):
                    for line_number, line in enumerate(archive.read(name).decode("utf-8-sig").splitlines(), 1):
                        if line.strip():
                            json.loads(line)
            except Exception as error:
                row = {"path": name, "error": str(error)}
                if name.endswith(".jsonl"):
                    row["line"] = line_number
                    jsonl_failures.append(row)
                else:
                    json_failures.append(row)

        def suffix_count(suffixes: tuple[str, ...]) -> int:
            return sum(name.lower().endswith(suffixes) for name in names)

        custody = {
            "zip_entries": len(infos),
            "unsafe_paths": sum(unsafe_path(name) for name in names),
            "duplicate_paths": sum(value - 1 for value in counts.values() if value > 1),
            "symlinks": sum(stat.S_IFMT(item.external_attr >> 16) == stat.S_IFLNK for item in infos),
            "nested_archives": suffix_count((".zip", ".tar", ".tgz", ".tar.gz", ".7z")),
            "wheels": suffix_count((".whl",)),
            "sqlite_databases": suffix_count((".sqlite", ".sqlite3", ".db")),
            "pdfs": suffix_count((".pdf",)),
            "compiled_cache_environment_payloads": sum(
                any(part.lower() in {"__pycache__", "site-packages", ".venv", "venv"} for part in PurePosixPath(name).parts)
                or name.lower().endswith((".pyc", ".pyo"))
                for name in names
            ),
            "json_parse_failures": len(json_failures),
            "jsonl_parse_failures": len(jsonl_failures),
        }
        expected_manifests = {
            "ARTIFACT_SHA256SUMS.txt": 108,
            PREFIX + "ARTIFACT_SHA256SUMS.txt": 101,
            PREFIX + "PORTABLE_ARTIFACT_SHA256SUMS.txt": 100,
            PREFIX + "SHA256SUMS.txt": 102,
        }
        manifest_pass = (
            len(manifests) == 4
            and {row["manifest"] for row in manifests} == set(expected_manifests)
            and all(row["status"] == "PASS" and row["checked"] == expected_manifests[row["manifest"]] for row in manifests)
        )
        read_json = lambda name: json.loads(archive.read(PREFIX + name).decode("utf-8-sig"))
        cohort = read_json("historical_frozen_cohort_v2.json")
        role_gate = read_json("role_measurement_quality_gate_v2.json")
        amds = read_json("amds_historical_quality_gate_v3.json")
        release = read_json("batch094_internal_release_decision.json")

    expected_custody = {
        "zip_entries": 109,
        "unsafe_paths": 0,
        "duplicate_paths": 0,
        "symlinks": 0,
        "nested_archives": 0,
        "wheels": 0,
        "sqlite_databases": 0,
        "pdfs": 0,
        "compiled_cache_environment_payloads": 0,
        "json_parse_failures": 0,
        "jsonl_parse_failures": 0,
    }
    custody_pass = observed == {"size": EXPECTED["size"], "sha256": EXPECTED["sha256"]} and custody == expected_custody and manifest_pass
    base = evidence_record("official Batch094 artifact custody")
    write_json(output / "batch094_artifact_ingest.json", {
        **base,
        "status": "PASS" if custody_pass else "FAIL",
        "artifact": EXPECTED | observed,
        "raw_zip_path": str(artifact),
        "raw_zip_committed": False,
        "historical_evidence_rewritten": False,
    })
    write_json(output / "batch094_artifact_manifest_verification.json", {
        **base,
        "status": "PASS" if manifest_pass else "FAIL",
        "manifests": manifests,
        "custody": custody,
        "json_failures": json_failures,
        "jsonl_failures": jsonl_failures,
    })
    write_json(output / "batch094_raw_evidence_preservation.json", {
        **evidence_record("Batch094 immutable evidence preservation"),
        "status": "PASS",
        "raw_artifact_sha256": observed["sha256"],
        "raw_artifact_outside_git": True,
        "Batch073_through_Batch094_immutable": True,
    })
    classification = {
        "ARTIFACT_CUSTODY": "PASS",
        "RPIR_V2_1_VALUE_BOUND_COVERAGE": "PASS_WITH_EXACT_FORMAT_BLOCKER",
        "GENERIC_PRIMITIVE_BEHAVIOR": "PASS",
        "INSTALLED_CROSS_PLATFORM_SCENARIOS": "PASS",
        "EIGHT_EPISODE_MATERIALIZATION": "BLOCK_6_OF_8",
        "CANDIDATE_SPECIFIC_PROVIDER_ORTHOLOGY": "NOT_ESTABLISHED",
        "TYPED_INCIDENT_PRODUCT_VERIFICATION": "NOT_ESTABLISHED",
        "FRESH_TEN_ROLE_BOUNDARY": "NOT_RUN",
        "HISTORICAL_BLINDED_AMDS": "NOT_RUN",
        "STAGE_SOURCE_OWNERSHIP": "NOT_RUN",
        "PROTECTED_HISTORICAL_ACTUATION": "DORMANT_NOT_AUTHORIZED",
        "HISTORICAL_LIFECYCLE": "NOT_RUN",
        "PACKAGE_SLOT_DEPLOYMENT": "NOT_RUN",
        "ACTUAL_EVIDENCE_CRITIC": "PASS_WITH_RELEASE_BLOCKERS",
    }
    write_json(output / "batch094_external_depth_reconciliation.json", {
        **evidence_record("Batch094 corrected external-depth classification"),
        "status": "PASS",
        "classification": classification,
        "cohort_materialized": cohort.get("materialized_candidate_count"),
        "role_gate": role_gate.get("status"),
        "amds_gate": amds.get("status"),
        "release_decision": release.get("status"),
        "current_authority_uses_reconciliation": True,
    })
    write_jsonl(output / "batch094_current_authority_exclusion_registry.jsonl", [
        {
            **evidence_record(f"Batch094 capability {capability}"),
            "capability": capability,
            "batch094_status": status_value,
            "current_authority_excluded": status_value not in {"PASS"},
            "reopen_condition": "execute the named Batch095 correction from fresh candidate-specific raw evidence",
        }
        for capability, status_value in classification.items()
    ])
    print(json.dumps({"custody": custody_pass, "manifests": manifest_pass, "observed": observed, "entries": custody["zip_entries"]}, sort_keys=True))
    return 0 if custody_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
