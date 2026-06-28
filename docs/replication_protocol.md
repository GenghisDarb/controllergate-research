# Clean replication protocol

The clean replication protocol is the maintained path for future external repair replication.

It supports:

- `batch_id`
- `candidate_source_mode`
- `max_candidates_to_verify`
- `max_repairs_to_attempt`
- `max_successful_repairs_target`
- `provenance_level`
- `evidence_class`
- `matched_null_required`
- `full_scoring: false`

Candidate sources may be curated seeds, bounded metadata probes, or issue-derived harnesses. Native tests are preferred and issue-derived evidence remains a separate class.

The protocol must not use fixed, later, gold, or PR patch content as repair evidence. Full scoring remains disabled.
