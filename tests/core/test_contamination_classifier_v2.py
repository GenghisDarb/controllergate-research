from controllergate.intake.contamination_classifier_v2 import classify_contamination_v2


def test_pluggy_style_solution_is_hard_reject():
    text = "# Intended Solution\nIn src/hooks.py line 42 replace x with y.\n```python\ny = 1\n```"
    assert classify_contamination_v2(text)["classification"] == "HARD_REJECT_SOLUTION_CONTAMINATION"


def test_reproducer_alone_is_clean():
    assert classify_contamination_v2("```python\nraise RuntimeError('x')\n```")["classification"] == "CLEAN"


def test_traceback_alone_is_clean():
    assert classify_contamination_v2('Traceback (most recent call last):\n File "x.py", line 1')["classification"] == "CLEAN"


def test_fix_pr_rejected():
    assert classify_contamination_v2("Fixed by PR #123")["hard_reject"]
