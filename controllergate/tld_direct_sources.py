from __future__ import annotations

import hashlib
import json
import mimetypes
import os
import re
import stat
import unicodedata
import zipfile
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from xml.etree import ElementTree


FIXED_ZIP_TIME = (1980, 1, 1, 0, 0, 0)
TEXT_SUFFIXES = {".txt", ".md", ".json", ".jsonl", ".py", ".ipynb", ".csv", ".yml", ".yaml"}
AUTHORITY_FORBIDDEN = [
    "AMDS cell mutation",
    "VerifiedCausalFact minting",
    "source ownership",
    "repair authorization",
    "repair count mutation",
    "terminal mutation",
    "release promotion",
]


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canonical_json_bytes(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode("utf-8") + b"\n"


def normalized_relative_path(value: str) -> str:
    value = unicodedata.normalize("NFC", value.replace("\\", "/"))
    path = PurePosixPath(value)
    if path.is_absolute() or not path.parts or any(part in {"", ".", ".."} for part in path.parts):
        raise ValueError(f"unsafe source path: {value}")
    if re.match(r"^[A-Za-z]:", value):
        raise ValueError(f"absolute drive path is forbidden: {value}")
    return path.as_posix()


def normalize_text(text: str) -> str:
    return text.replace("\r\n", "\n").replace("\r", "\n")


def decode_text(data: bytes) -> str:
    for encoding in ("utf-8-sig", "utf-16"):
        try:
            return normalize_text(data.decode(encoding))
        except UnicodeDecodeError:
            pass
    raise ValueError("text is not valid UTF-8 or UTF-16")


def extract_docx_text(data: bytes) -> str:
    from io import BytesIO

    with zipfile.ZipFile(BytesIO(data)) as archive:
        names = set(archive.namelist())
        if "word/document.xml" not in names:
            raise ValueError("DOCX lacks word/document.xml")
        root = ElementTree.fromstring(archive.read("word/document.xml"))
    paragraphs: list[str] = []
    for paragraph in root.iter("{http://schemas.openxmlformats.org/wordprocessingml/2006/main}p"):
        pieces = [node.text or "" for node in paragraph.iter("{http://schemas.openxmlformats.org/wordprocessingml/2006/main}t")]
        paragraphs.append("".join(pieces))
    return normalize_text("\n".join(paragraphs))


def media_type(path: str) -> str:
    suffix = Path(path).suffix.lower()
    if suffix == ".docx":
        return "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    if suffix == ".zip":
        return "application/zip"
    return mimetypes.guess_type(path)[0] or "application/octet-stream"


def classify_source(path: str, text: str | None) -> tuple[str, list[str]]:
    key = f"{path}\n{text[:4000] if text else ''}".casefold()
    secondary: list[str] = []
    if "formal lexicon" in key:
        return "FORMAL_LEXICON", secondary
    if "errata" in key or "mislabeling" in key or "notation history" in key:
        return "ERRATA_MAP", secondary
    if "technical standards" in key or "input protocol" in key:
        if "input protocol" in key:
            secondary.append("INPUT_PROTOCOL")
        return "TECHNICAL_STANDARD", secondary
    if "source_manifest" in key or "nonomission_ledger" in key:
        return "NOTEBOOK_REGISTRY", secondary
    if "detailed breakdown of notebooks" in key or "notebook_" in key or "notebook " in key:
        return "DETAILED_NOTEBOOK_BREAKDOWN", secondary
    if "development chats" in key:
        return "HISTORICAL_COMMENTARY", secondary
    if "reassessment" in key:
        return "SECONDARY_INTERPRETATION", secondary
    if "glossary" in key:
        return "GLOSSARY", secondary
    if path.casefold().endswith(".ipynb"):
        return "RAW_NOTEBOOK_SOURCE", secondary
    return "UNKNOWN", secondary


NOTEBOOK_PATTERN = re.compile(r"(?i)\bnotebook(?:[_\s\-]|\s+no\.?\s*)+(\d{1,2})\b")


def notebook_evidence(text: str | None) -> list[dict]:
    if not text:
        return []
    rows: list[dict] = []
    seen: set[int] = set()
    for match in NOTEBOOK_PATTERN.finditer(text):
        number = int(match.group(1))
        if not 1 <= number <= 44 or number in seen:
            continue
        seen.add(number)
        left = max(0, match.start() - 96)
        right = min(len(text), match.end() + 96)
        evidence = text[left:right]
        rows.append(
            {
                "notebook_number": number,
                "offset": match.start(),
                "match_sha256": sha256_bytes(evidence.encode("utf-8")),
                "evidence_kind": "content_notebook_identifier",
            }
        )
    return rows


@dataclass(frozen=True)
class SourceRecord:
    source_id: str
    original_name: str
    normalized_path: str
    size: int
    sha256: str
    media_type: str
    source_role: str
    secondary_roles: tuple[str, ...]
    extraction_method: str
    content_extraction_status: str
    normalized_text: str | None
    raw_bytes: bytes
    container_path: str | None
    notebook_evidence: tuple[dict, ...]

    def public_dict(self) -> dict:
        numbers = sorted({row["notebook_number"] for row in self.notebook_evidence})
        return {
            "source_id": self.source_id,
            "original_name": self.original_name,
            "normalized_path": self.normalized_path,
            "size": self.size,
            "sha256": self.sha256,
            "media_type": self.media_type,
            "source_role": self.source_role,
            "secondary_roles": list(self.secondary_roles),
            "notebook_numbers_detected": numbers,
            "coverage_range": [min(numbers), max(numbers)] if numbers else None,
            "lexicon_or_errata_role": self.source_role if self.source_role in {"FORMAL_LEXICON", "ERRATA_MAP"} else None,
            "content_extraction_status": self.content_extraction_status,
            "extraction_method": self.extraction_method,
            "container_path": self.container_path,
            "normalized_text_sha256": sha256_bytes(self.normalized_text.encode("utf-8")) if self.normalized_text is not None else None,
            "authority_allowed": ["shadow provenance", "shadow requirement extraction", "diagnostic design"],
            "authority_forbidden": AUTHORITY_FORBIDDEN,
        }


def _text_for(path: str, data: bytes) -> tuple[str | None, str]:
    suffix = Path(path).suffix.lower()
    if suffix in TEXT_SUFFIXES:
        return decode_text(data), "TEXT_DECODED"
    if suffix == ".docx":
        return extract_docx_text(data), "DOCX_XML_EXTRACTED"
    return None, "NOT_TEXT"


def _record(path: str, data: bytes, method: str, container: str | None = None) -> SourceRecord:
    text, status = _text_for(path, data)
    role, secondary = classify_source(path, text)
    digest = sha256_bytes(data)
    return SourceRecord(
        source_id=f"tld-source-{digest[:20]}",
        original_name=PurePosixPath(path).name,
        normalized_path=normalized_relative_path(path),
        size=len(data),
        sha256=digest,
        media_type=media_type(path),
        source_role=role,
        secondary_roles=tuple(secondary),
        extraction_method=method,
        content_extraction_status=status,
        normalized_text=text,
        raw_bytes=data,
        container_path=container,
        notebook_evidence=tuple(notebook_evidence(text)),
    )


def enumerate_sources(source_root: Path) -> list[SourceRecord]:
    source_root = source_root.resolve()
    if not source_root.is_dir():
        raise ValueError("source root is missing")
    paths: list[Path] = []
    for path in sorted(source_root.rglob("*"), key=lambda value: value.relative_to(source_root).as_posix().casefold()):
        if path.is_symlink():
            raise ValueError(f"symlink is forbidden: {path.relative_to(source_root)}")
        mode = path.stat().st_mode
        if path.is_dir():
            continue
        if not stat.S_ISREG(mode):
            raise ValueError(f"non-regular source is forbidden: {path.relative_to(source_root)}")
        paths.append(path)
    if not paths:
        raise ValueError("no direct source files supplied")

    root_names: set[str] = set()
    records: list[SourceRecord] = []
    for path in paths:
        relative = normalized_relative_path(path.relative_to(source_root).as_posix())
        folded = relative.casefold()
        if folded in root_names:
            raise ValueError(f"case-fold or normalized path collision: {relative}")
        root_names.add(folded)
        data = path.read_bytes()
        root_record = _record(relative, data, "direct-file")
        records.append(root_record)
        if path.suffix.casefold() != ".zip":
            continue
        from io import BytesIO

        with zipfile.ZipFile(BytesIO(data)) as archive:
            member_names: set[str] = set()
            for info in sorted(archive.infolist(), key=lambda value: unicodedata.normalize("NFC", value.filename).casefold()):
                if info.is_dir():
                    continue
                if info.flag_bits & 0x1:
                    raise ValueError(f"password-protected archive member: {relative}!{info.filename}")
                member = normalized_relative_path(info.filename)
                folded_member = member.casefold()
                if folded_member in member_names:
                    raise ValueError(f"archive member collision: {relative}!{member}")
                member_names.add(folded_member)
                unix_mode = (info.external_attr >> 16) & 0xFFFF
                if unix_mode and stat.S_ISLNK(unix_mode):
                    raise ValueError(f"archive symlink is forbidden: {relative}!{member}")
                member_data = archive.read(info)
                records.append(_record(f"{relative}!{member}", member_data, "zip-member", relative))
    return sorted(records, key=lambda row: (row.normalized_path.casefold(), row.normalized_path))


def enrich_duplicates(records: list[SourceRecord]) -> list[dict]:
    by_raw: dict[str, list[str]] = {}
    by_text: dict[str, list[str]] = {}
    for record in records:
        by_raw.setdefault(record.sha256, []).append(record.normalized_path)
        if record.normalized_text is not None:
            by_text.setdefault(sha256_bytes(record.normalized_text.encode("utf-8")), []).append(record.normalized_path)
    raw_groups = {key: value for key, value in by_raw.items() if len(value) > 1}
    text_groups = {key: value for key, value in by_text.items() if len(value) > 1}
    result: list[dict] = []
    for record in records:
        value = record.public_dict()
        value["duplicate_group"] = f"exact-{record.sha256[:16]}" if record.sha256 in raw_groups else None
        text_hash = value["normalized_text_sha256"]
        value["semantic_duplicate_group"] = f"text-{text_hash[:16]}" if text_hash in text_groups and record.sha256 not in raw_groups else None
        value["overlap_group"] = None
        value["conflict_group"] = None
        result.append(value)
    return result


def bundle_member_name(record: SourceRecord, normalized: bool) -> str:
    path = record.normalized_path.replace("!", "/__archive_members__/")
    if normalized:
        return f"normalized_text/{path}.txt"
    return f"original_sources/{path}"


def write_deterministic_zip(path: Path, members: dict[str, bytes]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9, strict_timestamps=True) as archive:
        for name in sorted(members):
            info = zipfile.ZipInfo(name, FIXED_ZIP_TIME)
            info.create_system = 3
            info.external_attr = (0o100644 & 0xFFFF) << 16
            info.compress_type = zipfile.ZIP_DEFLATED
            archive.writestr(info, members[name], compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)


def build_bundle(source_root: Path, output_bundle: Path, output_manifest: Path, output_report: Path) -> dict:
    records = enumerate_sources(source_root)
    public_records = enrich_duplicates(records)
    root_records = [record for record in records if record.extraction_method == "direct-file"]
    coverage = sorted({row["notebook_number"] for record in records for row in record.notebook_evidence})
    missing = sorted(set(range(1, 45)) - set(coverage))
    input_identity_rows = [{"path": row.normalized_path, "sha256": row.sha256, "size": row.size} for row in root_records]
    input_aggregate_identity = sha256_bytes(canonical_json_bytes(input_identity_rows))
    canonical_manifest = {
        "format": "controllergate-tld-direct-source-custody-v1",
        "authority_allowed": ["shadow provenance", "shadow requirement extraction", "diagnostic design"],
        "authority_forbidden": AUTHORITY_FORBIDDEN,
        "input_file_count": len(root_records),
        "expanded_source_count": len(records),
        "input_aggregate_identity": input_aggregate_identity,
        "notebook_coverage": coverage,
        "missing_notebooks": missing,
        "sources": public_records,
    }
    members: dict[str, bytes] = {"canonical_manifest.json": canonical_json_bytes(canonical_manifest)}
    for record in records:
        members[bundle_member_name(record, False)] = record.raw_bytes
        if record.normalized_text is not None:
            members[bundle_member_name(record, True)] = record.normalized_text.encode("utf-8")
    write_deterministic_zip(output_bundle, members)
    output_manifest.parent.mkdir(parents=True, exist_ok=True)
    output_manifest.write_bytes(canonical_json_bytes(canonical_manifest))
    bundle_bytes = output_bundle.read_bytes()
    report = {
        "status": "PASS_44_OF_44" if not missing else "BATCH098_TLD_DIRECT_SOURCE_COVERAGE_BLOCKED_EXACT",
        "bundle_filename": output_bundle.name,
        "bundle_sha256": sha256_bytes(bundle_bytes),
        "bundle_size": len(bundle_bytes),
        "member_count": len(members),
        "uncompressed_bytes": sum(len(value) for value in members.values()),
        "input_file_count": len(root_records),
        "expanded_source_count": len(records),
        "input_aggregate_identity": input_aggregate_identity,
        "notebook_coverage": coverage,
        "missing_notebooks": missing,
        "normalized_extraction_count": sum(record.normalized_text is not None for record in records),
        "extraction_failure_count": 0,
        "machine_specific_path_count": 0,
    }
    output_report.parent.mkdir(parents=True, exist_ok=True)
    output_report.write_bytes(canonical_json_bytes(report))
    return report


def read_bundle_manifest(bundle: Path) -> dict:
    with zipfile.ZipFile(bundle) as archive:
        return json.loads(archive.read("canonical_manifest.json"))
