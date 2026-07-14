# Troubleshooting

- `BLOCK` or exit 3 means a prerequisite is absent; repair the named evidence boundary.
- `SAFE_ABSTENTION` or exit 2 is valid only when it matches the manifest's expected terminal contract.
- `CANARY_REJECTED` or exit 5 requires rollback or operator review.
- Integrity failure or exit 4 requires stopping and verifying state/proof hashes.
- A worker-lease conflict means another live or unexpired worker owns the run.
- Historical provider expiration is not permission to reconstruct unverified bytes or claim a replay.
