from pathlib import Path


def test_future_agentic_admissibility_compiler_roadmap_cannot_be_marked_implemented():
    path = Path("docs/future_agentic_admissibility_compiler_integration.md")
    if path.exists():
        text = path.read_text(encoding="utf-8").lower()
        assert "roadmap only" in text
        assert "integration implemented" not in text
