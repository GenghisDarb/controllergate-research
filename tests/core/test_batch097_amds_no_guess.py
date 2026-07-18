import ast
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]

def test_builder_has_no_candidate_terminal_table():
    tree=ast.parse((ROOT/'scripts/run_batch097_amds_builder.py').read_text())
    forbidden={'truth_by_id','candidate_terminals','expected_terminals'}
    assert not any(isinstance(n,ast.Assign) and any(getattr(t,'id','') in forbidden for t in n.targets) for n in ast.walk(tree))

def test_truth_join_occurs_in_separate_script():
    text=(ROOT/'scripts/run_batch097_amds_builder.py').read_text().lower()
    assert 'batch084_historical_episode_registry' not in text
    assert 'truth_by' not in text
    assert 'truth_capsule' not in text

def test_incomplete_role_cohort_blocks_without_guessing_or_crashing():
    text=(ROOT/'scripts/run_batch097_amds_builder.py').read_text()
    assert "if missing_roles:" in text
    assert "fresh_role_specific_measurement_cohort_incomplete" in text
    assert "amds_episode_eligibility_v6.jsonl" in text
