import ast
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]

def test_batch097_join_has_no_hardcoded_terminal_array():
 tree=ast.parse((ROOT/'scripts/join_batch097_materialization_evidence.py').read_text())
 assert not any(isinstance(n,ast.Assign) and any(getattr(t,'id','') in {'terminals','classes','baselines'} for t in n.targets) for n in ast.walk(tree))

def test_installed_lane_rejects_checkout_origin():
 text=(ROOT/'scripts/run_batch097_installed_candidate_lane.py').read_text()
 assert 'CHECKOUT_IMPORT_FORBIDDEN_EXACT' in text
