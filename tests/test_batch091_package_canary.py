from pathlib import Path

from controllergate.deployment.package_canary import _tree_hash
from controllergate.product.historical_lifecycle import _tree_hash as lifecycle_tree_hash


def test_tree_hash_changes_with_semantic_content(tmp_path: Path) -> None:
    target = tmp_path / "source.py"
    target.write_text("value = 1\n", encoding="utf-8")
    before = _tree_hash(tmp_path)
    target.write_text("value = 2\n", encoding="utf-8")
    assert _tree_hash(tmp_path) != before


def test_tree_hash_excludes_compiled_cache(tmp_path: Path) -> None:
    target = tmp_path / "source.py"
    target.write_text("value = 1\n", encoding="utf-8")
    before = _tree_hash(tmp_path)
    cache = tmp_path / "__pycache__"
    cache.mkdir()
    (cache / "source.pyc").write_bytes(b"not portable")
    assert _tree_hash(tmp_path) == before


def test_historical_tree_hash_supports_capsule_without_git_metadata(tmp_path: Path) -> None:
    (tmp_path / "package").mkdir()
    target = tmp_path / "package/module.py"
    target.write_text("value = 1\n", encoding="utf-8")
    before = lifecycle_tree_hash(tmp_path)
    target.write_text("value = 2\n", encoding="utf-8")
    assert lifecycle_tree_hash(tmp_path) != before
