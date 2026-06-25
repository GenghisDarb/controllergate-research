# ControllerGate current protocol

The stable day-to-day ControllerGate protocol now points to `v2.13`, named `minimal_forensic_context_lane`.

The current-protocol interface is an infrastructure layer only. It does not replace, rewrite, or delete historical versioned workflows, scripts, audits, or output bundles. Those versioned files remain the reproducibility references for each scientific result.

## Current commands

Use the generic entry points for day-to-day checks:

```powershell
python scripts/controllergate_audit.py --protocol current
python scripts/controllergate_run.py --protocol current --dry-run
```

The same interface can explicitly select the current versioned protocol:

```powershell
python scripts/controllergate_audit.py --protocol v2.13
python scripts/controllergate_run.py --protocol v2.13 --dry-run
```

`controllergate_audit.py` dispatches to the configured v2.13 audit and must not weaken the underlying audit. `controllergate_run.py --dry-run` reports the configured runner and metadata without executing a repair workflow.

Non-dry-run dispatch through the generic current runner is intentionally disabled for now because the v2.13 runner can create or mutate campaign evidence. New evidence-producing work should be authorized explicitly and performed through the versioned runner or a future reviewed current-protocol mechanism.

## Current pointer and outputs

The current protocol is declared in:

```text
configs/controllergate_current.yaml
```

`outputs/current` is an active pointer and summary layer. It is not a replacement for verified historical outputs and must not duplicate the full v2.13 artifact payload. The verified v2.13 evidence remains in:

```text
outputs/v2_13_minimal_forensic_context_lane
```

## Claim boundaries

The current-protocol refactor does not alter v2.13 scientific claims:

- Full scoring remains `NOT_RUN` / disallowed.
- Self-maintaining software remains false / not demonstrated.
- Family generalization remains `not_expanded`.
- Non-Ansible positive-memory count remains `0`.
- PySnooper:2 remains blocked by deterministic fixture materialization evidence: `blocked_fixture_materialization_incomplete`.

v2.14 capability work is separate from this current-protocol pointer. The current protocol remains v2.13 until an official v2.14 artifact is verified, ingested, and explicitly promoted in a later step.
