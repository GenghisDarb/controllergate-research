# BugsInPy byte-identical exception research note

This note is research-only. The current BugsInPy global block remains active for post-v2.37 hardening and clean replication batch 002.

A future exception could be considered only if all of these conditions are proven before repair:

- target test file exists in the selected source commit tree,
- target test file exists in the comparison commit tree,
- target test file SHA256 is byte-identical across both trees,
- no comparison-only target test content is used,
- no repair patch or benchmark answer content is used,
- harness origin is recorded,
- the candidate remains separate from strict native external candidates until a future milestone explicitly authorizes it.

This exception is not active in this run.
