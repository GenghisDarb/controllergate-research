# Candidate #2 Manual Validation Commands

```bash
git clone <repo_url>
cd <repo>
git checkout <40_char_buggy_commit_sha>
python -m venv .venv
.venv/bin/python -m pip install -U pip
.venv/bin/python -m pip install -e ".[test]"
.venv/bin/python -m pytest <target_test_node_or_file> -q
```

Projects may use declared development extras such as `".[dev]"` or `".[tests]"` only if those extras are declared in the buggy commit tree. If the project uses tox, nox, hatch, or another native tool, record the exact command and the environment file that declares it.
