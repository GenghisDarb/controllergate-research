# Consolidated state format

Future ControllerGate lanes should publish one primary state file named `consolidated_state_<lane>.json`.

Required fields:

- `lane_id`
- `lane_type`
- `status`
- `exact_blocker`
- `current_protocol_version`
- `artifact_ingest`
- `byte_custody`
- `registry_status`
- `candidate_counts`
- `acquisition_status`
- `repair_status`
- `matched_null_status`
- `public_language_status`
- `claim_boundary_status`
- `raw_evidence_files`
- `diagnostic_files`
- `deprecated_files`
- `next_actions`

Status values are distinct and must not be collapsed:

- `PASS`
- `BLOCKED`
- `NOT_RUN`
- `NOT_APPLICABLE`
- `FAILED`

Artifact minimization target:

1. one consolidated state file,
2. one campaign summary,
3. one `SHA256SUMS.txt`,
4. raw logs or hashes needed for replay,
5. diagnostic files only when they materially explain a decision.

Historical outputs remain preserved.
