# Manual issue seed package template

Place a fresh unused seed package under `incoming_artifacts/manual_seed_intake/`. Keep it untracked.

Required package rules:

- Include the buggy commit, not the fixed commit.
- Include the failing command and stable failure signature.
- do not include patch diffs.
- do not include future fix PRs.
- do not include hidden labels.
- Do not include solution notes.
- Raw logs are allowed only when they are pre-repair failure logs.
- Source archives are allowed only when they are buggy source snapshots.
- The ZIP, if used, must live under `incoming_artifacts/manual_seed_intake/` and remain untracked.
