from __future__ import annotations

import hashlib
import io
import json
import zipfile
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Iterable, Mapping


TRUTH_STATUSES = {
    "VERIFIED", "VERIFIED_WITH_LIMITED_SCOPE", "UNRESOLVED",
    "CONTRADICTED", "NOT_SCOREABLE",
}
SCOREABILITY = {"SCOREABLE_CAUSAL", "SCOREABLE_ABSTENTION", "NOT_SCOREABLE"}
CAUSAL_CLASSES = {
    "SOURCE_OWNED_BEHAVIOR_DEFECT", "PROVIDER_OWNED",
    "ENVIRONMENT_PLATFORM_OWNED", "RUNNER_OWNED", "HARNESS_FIXTURE_OWNED",
    "SERVICE_TRANSPORT_OWNED", "TEST_EXPECTATION_FRAGILITY", "MIXED_FAILURE",
    "ABSTENTION_REQUIRED", "UNRESOLVED_TRUTH",
}
ACCEPTED_SOURCE_CLASSES = {
    "UPSTREAM_ISSUE_SNAPSHOT", "UPSTREAM_ISSUE_COMMENT", "MERGED_FIX_PR",
    "ACCEPTED_FIX_COMMIT", "REGRESSION_TEST", "RELEASE_NOTE",
    "MAINTAINER_CONFIRMATION", "BEFORE_AFTER_REPRODUCER",
    "PROVIDER_OR_PLATFORM_DOCUMENTATION", "TEST_ORACLE_DOCUMENTATION",
    "SOURCE_HISTORY_DIFF", "MANUAL_EXPERT_ADJUDICATION",
}


def canonical_bytes(value: object) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n").encode("utf-8")


def canonical_hash(value: object) -> str:
    return hashlib.sha256(canonical_bytes(value)).hexdigest()


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


@dataclass(frozen=True)
class CandidateTruthRecordV2:
    truth_record_id: str
    candidate_id: str
    repository: str
    issue_or_incident_id: str
    frozen_buggy_commit: str
    candidate_contract_hash: str
    truth_status: str
    scoreability: str
    causal_class: str
    abstention_expected: bool
    accepted_fix_identity: str | None
    accepted_fix_commit: str | None
    accepted_fix_pr: str | None
    accepted_release: str | None
    primary_truth_sources: tuple[str, ...]
    supporting_truth_sources: tuple[str, ...]
    truth_source_hashes: tuple[str, ...]
    executed_before_after_differential: bool
    regression_test_identity: str | None
    direct_causal_contact: bool
    alternative_exclusions: tuple[str, ...]
    mixed_failure_members: tuple[str, ...]
    truth_scope: str
    ambiguities: tuple[str, ...]
    adjudication_required: bool
    producer: str
    independent_verifier: str
    producer_receipt: str
    verifier_receipt: str
    terminal_commitment_hash: str
    truth_created_after_terminal: bool
    authority_allowed: str
    authority_forbidden: tuple[str, ...]
    reopen_condition: str

    def validate(self) -> None:
        if self.truth_status not in TRUTH_STATUSES:
            raise ValueError(f"invalid truth_status: {self.truth_status}")
        if self.scoreability not in SCOREABILITY:
            raise ValueError(f"invalid scoreability: {self.scoreability}")
        if self.causal_class not in CAUSAL_CLASSES:
            raise ValueError(f"invalid causal_class: {self.causal_class}")
        if len(self.frozen_buggy_commit) != 40 or any(c not in "0123456789abcdef" for c in self.frozen_buggy_commit.lower()):
            raise ValueError(f"invalid frozen commit for {self.candidate_id}")
        if len(self.candidate_contract_hash) != 64 or len(self.terminal_commitment_hash) != 64:
            raise ValueError(f"invalid binding hash for {self.candidate_id}")
        if not self.truth_created_after_terminal:
            raise ValueError(f"truth predates terminal for {self.candidate_id}")
        if self.scoreability == "SCOREABLE_CAUSAL":
            required = (
                self.causal_class not in {"ABSTENTION_REQUIRED", "UNRESOLVED_TRUTH"},
                bool(self.primary_truth_sources), bool(self.truth_source_hashes),
                self.direct_causal_contact, bool(self.alternative_exclusions),
                self.truth_status in {"VERIFIED", "VERIFIED_WITH_LIMITED_SCOPE"},
            )
            if not all(required):
                raise ValueError(f"scoreable causal truth lacks direct support: {self.candidate_id}")
        if self.scoreability == "SCOREABLE_ABSTENTION" and self.causal_class != "ABSTENTION_REQUIRED":
            raise ValueError("scoreable abstention requires ABSTENTION_REQUIRED")
        if self.causal_class == "UNRESOLVED_TRUTH" and self.scoreability != "NOT_SCOREABLE":
            raise ValueError("unresolved truth cannot be scored")

    def record(self) -> dict[str, Any]:
        self.validate()
        return asdict(self)


def make_truth_record(
    *, adjudication: Mapping[str, Any], contract: Mapping[str, Any],
    commitment: Mapping[str, Any], source_rows: Iterable[Mapping[str, Any]],
    created_at_utc: str,
) -> CandidateTruthRecordV2:
    candidate_id = str(contract["candidate_id"])
    source_rows = list(source_rows)
    source_ids = tuple(sorted(str(row["source_id"]) for row in source_rows))
    source_hashes = tuple(sorted(str(row["content_sha256"]) for row in source_rows))
    payload = {
        "candidate_id": candidate_id,
        "contract_hash": contract["contract_hash"],
        "terminal_commitment_hash": commitment["terminal_commitment_hash"],
        "adjudication": adjudication,
        "source_hashes": source_hashes,
        "created_at_utc": created_at_utc,
    }
    producer_receipt = f"truth-producer:{canonical_hash(payload)}"
    verifier_payload = {
        "producer_receipt": producer_receipt,
        "contract_binding": contract["contract_hash"],
        "terminal_timing_only": commitment["terminal_commitment_hash"],
        "source_hashes": source_hashes,
        "ruleset": "candidate-truth-v2-independent-verifier",
    }
    verifier_receipt = f"truth-verifier:{canonical_hash(verifier_payload)}"
    truth_record_id = f"truth-v2:{canonical_hash([candidate_id, producer_receipt, verifier_receipt])}"
    record = CandidateTruthRecordV2(
        truth_record_id=truth_record_id,
        candidate_id=candidate_id,
        repository=str(contract["repository"]),
        issue_or_incident_id=str(adjudication["issue_or_incident_id"]),
        frozen_buggy_commit=str(contract["source_commit"]),
        candidate_contract_hash=str(contract["contract_hash"]),
        truth_status=str(adjudication["truth_status"]),
        scoreability=str(adjudication["scoreability"]),
        causal_class=str(adjudication["causal_class"]),
        abstention_expected=bool(adjudication.get("abstention_expected", False)),
        accepted_fix_identity=adjudication.get("accepted_fix_identity"),
        accepted_fix_commit=adjudication.get("accepted_fix_commit"),
        accepted_fix_pr=adjudication.get("accepted_fix_pr"),
        accepted_release=adjudication.get("accepted_release"),
        primary_truth_sources=tuple(adjudication.get("primary_truth_sources", source_ids[:1])),
        supporting_truth_sources=tuple(adjudication.get("supporting_truth_sources", source_ids[1:])),
        truth_source_hashes=source_hashes,
        executed_before_after_differential=bool(adjudication.get("executed_before_after_differential", False)),
        regression_test_identity=adjudication.get("regression_test_identity"),
        direct_causal_contact=bool(adjudication.get("direct_causal_contact", False)),
        alternative_exclusions=tuple(adjudication.get("alternative_exclusions", ())),
        mixed_failure_members=tuple(adjudication.get("mixed_failure_members", ())),
        truth_scope=str(adjudication["truth_scope"]),
        ambiguities=tuple(adjudication.get("ambiguities", ())),
        adjudication_required=bool(adjudication.get("adjudication_required", False)),
        producer="controllergate.evidence.private_truth_v2.make_truth_record",
        independent_verifier="scripts.verify_batch098_private_sealed_truth",
        producer_receipt=producer_receipt,
        verifier_receipt=verifier_receipt,
        terminal_commitment_hash=str(commitment["terminal_commitment_hash"]),
        truth_created_after_terminal=created_at_utc > str(commitment["terminal_commitment_timestamp"]),
        authority_allowed="historical non-counting calibration truth only",
        authority_forbidden=("repair", "repair count", "release", "public write", "automatic merge"),
        reopen_condition=str(adjudication["reopen_condition"]),
    )
    record.validate()
    return record


def build_deterministic_bundle(path: Path, members: Mapping[str, bytes]) -> dict[str, Any]:
    normalized = {name.replace("\\", "/"): data for name, data in members.items()}
    if any(name.startswith("/") or ".." in Path(name).parts for name in normalized):
        raise ValueError("unsafe truth bundle member")
    manifest_rows = [
        {"path": name, "size": len(data), "sha256": sha256_bytes(data)}
        for name, data in sorted(normalized.items())
    ]
    manifest = b"".join(canonical_bytes(row) for row in manifest_rows)
    complete = dict(normalized)
    complete["PORTABLE_SHA256SUMS.jsonl"] = manifest
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for name, data in sorted(complete.items()):
            info = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.create_system = 3
            info.external_attr = 0o100644 << 16
            archive.writestr(info, data)
    payload = buffer.getvalue()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(payload)
    return {
        "path_basename": path.name,
        "size": len(payload),
        "sha256": sha256_bytes(payload),
        "members": len(complete),
        "manifest_entries": len(manifest_rows),
    }


def verify_deterministic_bundle(path: Path) -> dict[str, Any]:
    raw = path.read_bytes()
    failures: list[str] = []
    with zipfile.ZipFile(io.BytesIO(raw)) as archive:
        names = archive.namelist()
        if names != sorted(names) or len(names) != len(set(names)):
            failures.append("member_order_or_uniqueness")
        if any(name.startswith("/") or ".." in Path(name).parts for name in names):
            failures.append("unsafe_member")
        if any(info.date_time != (1980, 1, 1, 0, 0, 0) for info in archive.infolist()):
            failures.append("non_fixed_timestamp")
        rows = [json.loads(line) for line in archive.read("PORTABLE_SHA256SUMS.jsonl").splitlines() if line]
        for row in rows:
            if row["path"] == "PORTABLE_SHA256SUMS.jsonl":
                failures.append("self_manifest_entry")
                continue
            data = archive.read(row["path"])
            if len(data) != row["size"] or sha256_bytes(data) != row["sha256"]:
                failures.append(f"manifest:{row['path']}")
        records = [json.loads(line) for line in archive.read("candidate_truth_records_v2.jsonl").splitlines() if line]
        for row in records:
            CandidateTruthRecordV2(**{key: tuple(value) if key in {
                "primary_truth_sources", "supporting_truth_sources", "truth_source_hashes",
                "alternative_exclusions", "mixed_failure_members", "ambiguities", "authority_forbidden",
            } else value for key, value in row.items()}).validate()
    return {
        "status": "PASS" if not failures else "BLOCK",
        "bundle_sha256": sha256_bytes(raw),
        "bundle_size": len(raw),
        "member_count": len(names),
        "truth_record_count": len(records),
        "failures": failures,
    }
