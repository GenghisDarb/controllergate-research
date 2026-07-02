from pathlib import Path

from controllergate.core.dependency_era_resolution import manual_dependency_lock_presence


def test_missing_manual_dependency_lock_stops_with_request(tmp_path: Path):
    canonical = tmp_path / "external_seeds_pending" / "dependency_locks" / "darker_issue112_dependency_lock.json"
    result = manual_dependency_lock_presence(canonical, [])

    assert result["status"] == "BLOCK"
    assert result["canonical_json_present"] is False
    assert result["blocker"] == "manual_dependency_lock_absent"


def test_present_manual_dependency_lock_is_detected(tmp_path: Path):
    canonical = tmp_path / "external_seeds_pending" / "dependency_locks" / "darker_issue112_dependency_lock.json"
    canonical.parent.mkdir(parents=True)
    canonical.write_text("{}", encoding="utf-8")

    result = manual_dependency_lock_presence(canonical, [])

    assert result["status"] == "PASS"
    assert result["canonical_json_present"] is True
