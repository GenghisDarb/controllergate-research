from pathlib import Path

from controllergate.core.batch020_manual_lock import validate_manual_dependency_lock


def test_canonical_json_lock_is_required_and_validated():
    record, validation = validate_manual_dependency_lock(Path.cwd())
    assert record is not None
    assert validation["status"] == "PASS"
    assert validation["git_tracked"] is True
    assert validation["workflow_visible"] is True
    assert validation["current_sha256"] == "108d961f89b603d3c6a7bcb374976992c3fadc80497bf967421cdea38aff248a"


def test_txt_requirements_cannot_bypass_json_lock():
    audit = Path("outputs/clean_replication_batch_020/manual_requirements_support_file_audit.json")
    if audit.exists():
        import json

        data = json.loads(audit.read_text(encoding="utf-8"))
        assert data["canonical_json_authoritative"] is True
        assert data["txt_requirements_authoritative"] is False
