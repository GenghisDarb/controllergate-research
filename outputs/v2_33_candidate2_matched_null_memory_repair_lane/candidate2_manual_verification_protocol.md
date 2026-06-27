# Candidate #2 Manual Verification Protocol

Brad or external helpers should return only:

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
- manual verification notes with exact commands run

Do not return placeholders. Do not include patch contents or fixed/later/gold evidence. If the seed is not verified, say `not verified`.
