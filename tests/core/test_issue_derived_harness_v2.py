from pathlib import Path


FORBIDDEN_SECTIONS = ["analysis and suggested fix", "normalize environment", "rip it out"]


def test_harness_v2_cannot_use_solution_sections():
    context = Path("outputs/clean_replication_batch_016/issue_derived_harness_v2_context_manifest.json")
    if context.exists():
        text = context.read_text(encoding="utf-8").lower()
        assert not [section for section in FORBIDDEN_SECTIONS if section in text]
