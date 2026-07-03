# Failure Taxonomy

Batch021 records exact runtime-provider blocker classes instead of collapsing failures into a generic blocked state.

## Current operational gate status

- Batch021 preserves the Batch020 manual dependency lock boundary and adds Dynamic Era Materialization.
- Runtime Provider Selection blocks target replay unless an exact Python 3.7 provider is verified.
- Containerized Era Runtime remains plan-only until container identity and in-container runtime probes pass.
- The self-hosted runtime plan is the next safe action when no exact provider is verified.
- Confirmed external native repair episodes remain `4`.
- Confirmed issue-derived repair episodes remain `0`.
- Full scoring remains `NOT_RUN/disallowed`.
- Memory lift remains `not_demonstrated`.
- Self-maintaining software remains `false/not_demonstrated`.
- Broad runtime-readiness claims are not made.
