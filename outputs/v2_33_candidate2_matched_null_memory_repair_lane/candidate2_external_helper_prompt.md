Find one real external Python seed candidate for ControllerGate candidate #2.

Hard requirements:

- Public GitHub repo, not BugsInPy.
- Not Ansible.
- Not py_bugger_issue_65.
- Exact full 40-character buggy commit SHA.
- Native target test file physically present in that buggy commit tree.
- Exact test command that fails at that buggy commit on Ubuntu/Linux.
- No generated/manual reproducer file.
- No external internet dependency during the test command.
- No fixed commit content, fixed diff, gold patch, later commit content, PR patch content, or future-state test.
- Environment file path physically present in the buggy tree, such as pyproject.toml, tox.ini, pytest.ini, setup.cfg, setup.py, or requirements file.
- Prefer small pure-Python bugs with focused failing tests.
- Avoid OS-specific failures unless reproducible on ubuntu-latest.

Return only:

- candidate_id
- repo_url
- buggy_commit_sha
- issue_or_pr_url used only as lead evidence
- test_command
- target_test_file_paths
- support_file_paths if needed
- environment_lock_source
- expected failure type or short failure description
- why the test is native to the buggy tree
- manual verification notes, including exact commands to run

Do not provide placeholders. If not verified, say not verified.
