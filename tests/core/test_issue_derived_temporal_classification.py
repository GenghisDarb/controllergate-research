import json
from pathlib import Path


def test_batch013_issue_derived_temporal_classification_stays_separate():
    path = Path("outputs/clean_replication_batch_013/issue_derived_temporal_and_classification_audit.json")
    if not path.is_file():
        return
    result = json.loads(path.read_text(encoding="utf-8"))

    assert result["issue_derived_path_exercised"] is False
    assert result["issue_derived_not_classified_as_native"] is True
