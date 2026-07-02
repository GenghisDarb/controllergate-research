from pathlib import Path


def test_structure_first_compiler_roadmap_cannot_be_marked_implemented():
    path = Path("docs/structure_first_compiler_roadmap.md")
    if path.exists():
        text = path.read_text(encoding="utf-8").lower()
        assert "roadmap only" in text
        assert "implemented structural compiler" not in text
