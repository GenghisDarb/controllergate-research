# Reusable workflow plan

v2.36 records a future workflow-consolidation plan only.

A future reusable workflow should accept `workflow_dispatch` inputs for version, runner script, audit script, artifact name, required outputs, and regression set. The reusable workflow must keep byte-custody preflight, registry validation, current-protocol audit, and artifact upload gates explicit.
