# Disallowed Candidate #2 Seed Patterns

- short commit SHA
- 64-character SHA256 values presented as commit SHA
- branch names
- tags
- latest main
- issue-only evidence
- PR-only evidence
- fixed-diff evidence
- generated reproducer
- manual one-off test file
- test depending on live network
- OS-specific failure not reproducible on ubuntu-latest
- benchmark framework materialization
- any candidate requiring BugsInPy
- any candidate that passes before patch
