# Candidate #2 Discovery Support Packet

v2.33 stopped because `inputs/external_candidate_seed_draft_v2_33.json` is absent.

Candidate #2 must provide a real external Python project bug with a native target test that physically exists in the buggy commit tree before any repair. Issue links, pull requests, labels, and search results are lead evidence only; the seed must prove the buggy commit, native test path, environment file, exact target command, and pre-repair failure from local verification.

The buggy commit SHA must be a full 40-character Git commit hash. Short SHAs, 64-character SHA256 values, placeholder hashes, branch names, tags, and `latest main` are invalid because they do not uniquely pin the decision-time source tree.

No fixed commit contents, later commit contents, gold patches, hidden labels, pull request patch contents, fixed diffs, generated tests, copied tests, or manual one-off reproducer files may be used. The target command must not depend on public internet access or remote services.

Brad or an external helper should return the completed seed fields only after manual verification, then place the reviewed JSON at `inputs/external_candidate_seed_draft_v2_33.json` or a future lane input path.
