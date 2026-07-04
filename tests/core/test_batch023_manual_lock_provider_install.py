import json
from pathlib import Path


def test_batch023_manual_lock_install_requires_provider():
    base = Path("outputs/clean_replication_batch_023")
    revalidation = json.loads((base / "manual_dependency_lock_provider_revalidation.json").read_text(encoding="utf-8"))
    install = json.loads((base / "manual_dependency_lock_provider_install_status.json").read_text(encoding="utf-8"))
    assert revalidation["canonical_lock_only"] is True
    assert revalidation["actual_sha256"] == "108d961f89b603d3c6a7bcb374976992c3fadc80497bf967421cdea38aff248a"
    if install["status"] == "PASS":
        provider = json.loads((base / "python37_provider_preflight_results.json").read_text(encoding="utf-8"))
        assert provider["status"] == "PASS"
