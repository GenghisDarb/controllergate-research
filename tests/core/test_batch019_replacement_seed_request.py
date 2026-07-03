def test_replacement_seed_request_contains_evidence_and_forbidden_evidence_checklists():
    template = {
        "evidence_checklist": ["public repository", "issue timestamp", "environment lock source present"],
        "forbidden_evidence_checklist": ["fixed commit", "later commit", "gold patch", "PR patch", "future tests"],
    }

    assert "public repository" in template["evidence_checklist"]
    assert "fixed commit" in template["forbidden_evidence_checklist"]
    assert "future tests" in template["forbidden_evidence_checklist"]
