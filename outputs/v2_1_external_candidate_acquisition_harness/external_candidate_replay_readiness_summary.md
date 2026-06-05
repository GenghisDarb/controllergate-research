# v2.1 External Candidate Acquisition Harness Result

v2.1 implements candidate acquisition/preflight.

- Candidate descriptors evaluated: 5
- Ready candidates: 0
- Manual-review candidates: 0
- Rejected/blocked candidates: 5
- v2.2 handoff recommendation: `continue_candidate_acquisition`
- Candidate acquisition is not repair success.
- Ready candidates only authorize future v2.2 replay attempts.
- Blocked candidate acquisition is not negative capability evidence.
- External memory lift remains undemonstrated.
- Self-maintaining software remains undemonstrated.
- Full scoring remains disallowed.

## Ranked Pool

- `v2_1_candidate_005_requests`: score 95, status `not_ready`, classification `rejected_no_deterministic_failure`
- `v2_1_candidate_001_sampleproject`: score 94, status `not_ready`, classification `rejected_no_deterministic_failure`
- `v2_1_candidate_004_packaging`: score 94, status `not_ready`, classification `rejected_no_deterministic_failure`
- `v2_1_candidate_002_itsdangerous`: score 93, status `not_ready`, classification `rejected_no_deterministic_failure`
- `v2_1_candidate_003_markupsafe`: score 93, status `not_ready`, classification `rejected_no_deterministic_failure`

## Future Framework Note

A future reusable ControllerGate developer framework should separate replay engine, proof ledger, and adapters. A first practical shape would be `controllergate.toml` or YAML config, a generic shell adapter, a pytest adapter first, and later npm, cargo, go test, Flutter/Dart, and Java build adapters.
