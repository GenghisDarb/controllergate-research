# v2.8 BugsInPy Real-Bug Limited Replay Execution

Gate status: opened by three clean target-matched BugsInPy candidates.

Executed candidate shells:

- `youtube-dl:1`
- `black:8`
- `black:4`

Aggregate result: `blocked_bugsinpy_real_bug_replay_runtime_failure`.

The v2.8 candidate gate opened, but no episode is scoreable yet because the
available artifacts contain target replay logs and not validated no-memory or
memory-enabled post-repair BugsInPy execution logs. This is blocked execution
evidence, not negative memory-lift evidence.

Full scoring remains disallowed. Memory lift is not demonstrated.
Self-maintaining software remains undemonstrated.
