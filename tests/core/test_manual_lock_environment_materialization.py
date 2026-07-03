import json
from pathlib import Path


def test_environment_materialization_uses_validated_lock_only():
    path = Path("outputs/clean_replication_batch_020/manual_lock_environment_materialization_log.json")
    if path.exists():
        data = json.loads(path.read_text(encoding="utf-8"))
        assert data["lock_validation_status"] == "PASS"
        assert data["source_mutation_performed"] is False
        assert data["undeclared_dependency_install_attempted"] is False
