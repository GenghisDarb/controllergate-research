from __future__ import annotations

import json
import os
import stat
import subprocess
import sys
import zipfile
from pathlib import Path

import pytest

from controllergate.tld_direct_sources import FIXED_ZIP_TIME, build_bundle, enumerate_sources


REPO = Path(__file__).resolve().parents[1]


def complete_sources(root: Path) -> Path:
    root.mkdir(parents=True, exist_ok=True)
    notebooks = "Detailed Breakdown of Notebooks 1-44\n" + "\n".join(f"Notebook {index} — synthetic evidence" for index in range(1, 45))
    notebooks += "\nparent and null baseline; locked contract; perturbation families; no new thresholds\n"
    (root / "Detailed Breakdown of Notebooks 1-44.txt").write_text(notebooks, encoding="utf-8")
    (root / "Formal Lexicon.txt").write_text("Formal Lexicon\nTₑ onset; Sₑ persistence and survival depth\n", encoding="utf-8")
    (root / "Mislabeling Errata Map.txt").write_text("Errata Map\nlegacy value → current value\n", encoding="utf-8")
    (root / "Technical Standards and Input Protocol.txt").write_text("Technical Standards and Input Protocol\nsource manifest SHA256 registry\n", encoding="utf-8")
    (root / "SOURCE_MANIFEST.json").write_text('{"source_registry":"synthetic"}\n', encoding="utf-8")
    return root


def build(root: Path, destination: Path) -> dict:
    return build_bundle(root, destination / "bundle.zip", destination / "manifest.json", destination / "report.json")


def minimal_docx(path: Path) -> None:
    xml = b'<?xml version="1.0" encoding="UTF-8"?><w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:body><w:p><w:r><w:t>Notebook 44 synthetic DOCX</w:t></w:r></w:p></w:body></w:document>'
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr("word/document.xml", xml)


def run_script(name: str, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run([sys.executable, str(REPO / "scripts" / name), *args], text=True, capture_output=True, check=False)


def test_complete_1_44_coverage_and_authority_firewall(tmp_path: Path) -> None:
    source = complete_sources(tmp_path / "sources")
    report = build(source, tmp_path / "out")
    assert report["status"] == "PASS_44_OF_44"
    assert report["notebook_coverage"] == list(range(1, 45))
    manifest = json.loads((tmp_path / "out" / "manifest.json").read_text(encoding="utf-8"))
    assert "AMDS cell mutation" in manifest["authority_forbidden"]


def test_mixed_file_formats_and_docx_extraction(tmp_path: Path) -> None:
    source = complete_sources(tmp_path / "sources")
    minimal_docx(source / "standard.docx")
    records = enumerate_sources(source)
    docx = next(row for row in records if row.normalized_path.endswith("standard.docx"))
    assert docx.content_extraction_status == "DOCX_XML_EXTRACTED"
    assert "Notebook 44" in (docx.normalized_text or "")


def test_deterministic_zip_and_independent_rebuild(tmp_path: Path) -> None:
    source = complete_sources(tmp_path / "sources")
    first = build(source, tmp_path / "a")
    second = build(source, tmp_path / "b")
    assert (tmp_path / "a" / "bundle.zip").read_bytes() == (tmp_path / "b" / "bundle.zip").read_bytes()
    assert first["bundle_sha256"] == second["bundle_sha256"]
    with zipfile.ZipFile(tmp_path / "a" / "bundle.zip") as archive:
        assert all(info.date_time == FIXED_ZIP_TIME for info in archive.infolist())


def test_exact_duplicate_handling(tmp_path: Path) -> None:
    source = complete_sources(tmp_path / "sources")
    data = (source / "Formal Lexicon.txt").read_bytes()
    (source / "Formal Lexicon copy.txt").write_bytes(data)
    records = enumerate_sources(source)
    assert sum(row.sha256 == records[-1].sha256 for row in records) >= 1
    build(source, tmp_path / "out")


def test_errata_resolved_conflict_and_unresolved_conflict_block(tmp_path: Path) -> None:
    source = complete_sources(tmp_path / "sources")
    output = tmp_path / "audit"
    passed = run_script("audit_batch098_tld_direct_source_inventory.py", "--source-root", str(source), "--output-dir", str(output))
    assert passed.returncode == 0
    rows = [json.loads(line) for line in (output / "tld_direct_source_conflicts_v1.jsonl").read_text(encoding="utf-8").splitlines()]
    assert any(row["classification"] == "ERRATA_RESOLVED_CONFLICT" for row in rows)
    (source / "conflict.txt").write_text("UNRESOLVED_CONFLICT: synthetic disagreement\n", encoding="utf-8")
    blocked = run_script("audit_batch098_tld_direct_source_inventory.py", "--source-root", str(source), "--output-dir", str(output))
    assert blocked.returncode == 1
    assert json.loads((output / "tld_direct_source_coverage_v1.json").read_text(encoding="utf-8"))["exact_blocker"] == "BATCH098_TLD_DIRECT_SOURCE_CONFLICT_BLOCKED_EXACT"


def test_missing_notebook_blocks(tmp_path: Path) -> None:
    source = complete_sources(tmp_path / "sources")
    path = source / "Detailed Breakdown of Notebooks 1-44.txt"
    path.write_text(path.read_text(encoding="utf-8").replace("Notebook 26 — synthetic evidence", "missing entry"), encoding="utf-8")
    report = build(source, tmp_path / "out")
    assert report["status"] == "BATCH098_TLD_DIRECT_SOURCE_COVERAGE_BLOCKED_EXACT"
    assert 26 in report["missing_notebooks"]


@pytest.mark.parametrize("members", [[("same.txt", b"a"), ("same.txt", b"b")], [("A.txt", b"a"), ("a.txt", b"b")], [("../escape.txt", b"x")]])
def test_archive_path_and_collision_controls(tmp_path: Path, members: list[tuple[str, bytes]]) -> None:
    source = complete_sources(tmp_path / "sources")
    with zipfile.ZipFile(source / "unsafe.zip", "w") as archive:
        for name, data in members:
            archive.writestr(name, data)
    with pytest.raises(ValueError):
        enumerate_sources(source)


def test_archive_symlink_rejected(tmp_path: Path) -> None:
    source = complete_sources(tmp_path / "sources")
    with zipfile.ZipFile(source / "unsafe.zip", "w") as archive:
        info = zipfile.ZipInfo("link.txt")
        info.create_system = 3
        info.external_attr = (stat.S_IFLNK | 0o777) << 16
        archive.writestr(info, b"target")
    with pytest.raises(ValueError):
        enumerate_sources(source)


@pytest.mark.parametrize("name,data", [("unreadable.txt", b"\x80"), ("broken.docx", b"not-a-docx")])
def test_unreadable_and_extraction_failure_block(tmp_path: Path, name: str, data: bytes) -> None:
    source = complete_sources(tmp_path / "sources")
    (source / name).write_bytes(data)
    with pytest.raises((ValueError, zipfile.BadZipFile)):
        enumerate_sources(source)


def test_filename_claim_does_not_establish_notebook_26(tmp_path: Path) -> None:
    source = tmp_path / "sources"; source.mkdir()
    (source / "Notebook 26.txt").write_text("No notebook identifier appears in this content.", encoding="utf-8")
    records = enumerate_sources(source)
    assert records[0].notebook_evidence == ()


def test_modified_source_changes_frozen_input_identity(tmp_path: Path) -> None:
    source = complete_sources(tmp_path / "sources")
    first = build(source, tmp_path / "a")
    (source / "Formal Lexicon.txt").write_text("Formal Lexicon\nchanged\n", encoding="utf-8")
    second = build(source, tmp_path / "b")
    assert first["input_aggregate_identity"] != second["input_aggregate_identity"]


def test_no_machine_specific_path_leakage(tmp_path: Path) -> None:
    source = complete_sources(tmp_path / "private-user-name" / "sources")
    build(source, tmp_path / "out")
    manifest = (tmp_path / "out" / "manifest.json").read_text(encoding="utf-8")
    assert str(tmp_path) not in manifest
    assert "private-user-name" not in manifest


def test_compiled_requirements_have_source_citations_and_no_raw_passages(tmp_path: Path) -> None:
    source = complete_sources(tmp_path / "sources")
    registry = tmp_path / "registry.jsonl"; report = tmp_path / "report.json"; special = tmp_path / "special"
    result = run_script("compile_batch098_tld_requirements_from_sources.py", "--source-root", str(source), "--output-registry", str(registry), "--output-report", str(report), "--special-output-dir", str(special))
    assert result.returncode == 0
    rows = [json.loads(line) for line in registry.read_text(encoding="utf-8").splitlines()]
    assert rows and all(row["source_file_sha256"] and row["source_evidence_sha256"] for row in rows)
    assert json.loads(report.read_text(encoding="utf-8"))["raw_private_passage_count"] == 0


def test_notebook26_does_not_gain_hardcoded_three_probe_threshold(tmp_path: Path) -> None:
    source = complete_sources(tmp_path / "sources")
    registry = tmp_path / "registry.jsonl"; special = tmp_path / "special"
    run_script("compile_batch098_tld_requirements_from_sources.py", "--source-root", str(source), "--output-registry", str(registry), "--output-report", str(tmp_path / "report.json"), "--special-output-dir", str(special))
    result = json.loads((special / "tld_notebook26_direct_source_resolution_v2.json").read_text(encoding="utf-8"))
    assert result["three_probe_threshold_supported"] is False
    assert "spiral collapse after three probes" in result["unsupported_prior_interpretations"]


def separation_receipts(path: Path, one_process: bool = False, truth_access: bool = False) -> None:
    rows = []
    for index in range(24):
        rows.append({"stage": f"stage-{index}", "role": "producer" if index % 2 == 0 else "verifier", "process_id": 1 if one_process else index + 100, "child_return_code": 0, "input_handoff_hash": "a" * 64, "output_handoff_hash": "b" * 64, "shared_mutable_memory": False, "truth_preterminal_access": truth_access and index == 1})
    path.write_text("".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8")


def test_private_source_local_process_separation_positive_and_negative(tmp_path: Path) -> None:
    wheel = tmp_path / "controllergate.whl"; wheel.write_bytes(b"synthetic wheel")
    receipts = tmp_path / "receipts.jsonl"; separation_receipts(receipts)
    output = tmp_path / "audit.json"
    passed = run_script("audit_batch098_local_process_separation.py", "--receipts", str(receipts), "--wheel", str(wheel), "--installed-origin", "outside_repository_site_packages/controllergate", "--output", str(output))
    assert passed.returncode == 0
    assert json.loads(output.read_text(encoding="utf-8"))["status"] == "PASS"
    separation_receipts(receipts, one_process=True)
    assert run_script("audit_batch098_local_process_separation.py", "--receipts", str(receipts), "--wheel", str(wheel), "--installed-origin", "outside_repository_site_packages/controllergate", "--output", str(output)).returncode == 1
    separation_receipts(receipts, truth_access=True)
    assert run_script("audit_batch098_local_process_separation.py", "--receipts", str(receipts), "--wheel", str(wheel), "--installed-origin", "outside_repository_site_packages/controllergate", "--output", str(output)).returncode == 1


def test_local_helper_uses_private_mode_without_url_bridge() -> None:
    text = (REPO / "scripts" / "run_batch098_with_local_tld_sources.ps1").read_text(encoding="utf-8")
    assert "LOCAL_PROTECTED_SOURCE_RUN" not in text or "batch098_local_protected" in text
    assert "CONTROLLERGATE_TLD_BUNDLE_URL" not in text
    assert "run_batch098_local_stage.py" in text


def test_public_example_contains_no_private_source_passage() -> None:
    root = REPO / "examples" / "tld_direct_source_ingestion"
    combined = "\n".join(path.read_text(encoding="utf-8") for path in root.rglob("*") if path.is_file()).casefold()
    assert "ordered omega vector" not in combined
    assert "spiral collapse after three probes" not in combined
