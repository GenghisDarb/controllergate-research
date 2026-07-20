import ast
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_reactome_mysql_importer_parses_with_declared_python311_minimum():
    source = (ROOT / "controllergate/reactome_ir/mysql_dump.py").read_text(encoding="utf-8")
    ast.parse(source, filename="controllergate/reactome_ir/mysql_dump.py", feature_version=(3, 11))
