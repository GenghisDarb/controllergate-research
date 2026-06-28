# Evidence model

ControllerGate separates evidence into explicit classes.

## Native repair evidence

Evidence from project-native tests physically present in the selected source tree. Native evidence is required for native external repair counts.

## Issue-derived evidence

Evidence derived from issue text or issue reproduction details. It can guide investigation only when timestamp and source-context guards pass. It does not count as native evidence.

## Diagnostic evidence

Logs, failed probes, environment failures, collection failures, and replay diagnostics. Diagnostic evidence may explain blockers but does not prove repair success.

## Documentation evidence

README, public docs, claim-boundary files, and readiness reports. Documentation evidence must stay consistent with audited outputs.

## Infrastructure evidence

Workflow definitions, manifests, artifact payload reports, registry validation, transport records, and byte-custody reports.

All evidence classes must preserve decision-time and outcome-time separation.
