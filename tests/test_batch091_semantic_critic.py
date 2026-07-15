import json
from pathlib import Path

from controllergate.evaluation.semantic_release_critic import MUTATIONS


def test_all_required_semantic_mutations_are_registered() -> None:
    assert [row[0] for row in MUTATIONS] == [f"M{value:02d}" for value in range(1, 23)]
    assert len({row[3] for row in MUTATIONS}) == 22


def test_standalone_critic_has_no_controllergate_import() -> None:
    critic = Path(__file__).resolve().parents[1] / "scripts/batch091_semantic_critic.py"
    source = critic.read_text(encoding="utf-8")
    assert "import controllergate" not in source
    assert "from controllergate" not in source
