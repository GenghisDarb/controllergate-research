# v2.15 chromosomal maintenance gate order

Status: `PASS_WITH_ACTIVATION_DENIED`.

v2.15 preserves the verified v2.14 artifact and implements the requested maintenance order as machine-checkable gates. No broad sweep, full scoring, current-protocol promotion, or v2.16 work was performed.

- v2.14 artifact ingestion: `PASS`.
- Gate order implemented: `PASS`.
- Patch generation: `blocked before licensing`.
- PySnooper:1: `activation_denied_after_dependency_or_cofactor_mismatch`.
- PySnooper:2: `activation_denied_after_fixture_materialization_incomplete`.
- Final scoreable count: `5`.
- Final positive-memory count: `2`.
- Non-Ansible positive-memory count: `0`.
- Family generalization: `not_expanded`.
- Full scoring remains `NOT_RUN` / disallowed.
- Memory lift and self-maintaining software remain undemonstrated.
