# ControllerGate

ControllerGate is a provenance-first software repair research harness. It is built around artifact byte custody, candidate provenance, replay discipline, source-only repair safety, registry validation, and explicit claim boundaries.

Current branch: `controllergate-v1.7-alpha-real-trace-pilot`

## Current status

- Current protocol remains `v2.13` / `minimal_forensic_context_lane`.
- Three external non-Ansible native source-only repair episodes are confirmed after official ingest: `py_bugger_issue_65`, `darker_non_ascii_drop_changes`, and `darker_stdin_filename`.
- ControllerGate has strong artifact custody, registry validation, claim-boundary enforcement, transport integrity checks, clean-replication scaffolding, artifact hygiene, and real-lead acquisition attempts.
- v2.37 and post-v2.37 work introduced shared core gates, reusable workflow scaffolding, transport integrity, risk regulation, a clean protocol adapter, and native/issue-derived evidence class separation.
- Clean replication batch002 now attempts real external leads, resolves project environments before replay, and produced one additional native repair for `darker_non_ascii_drop_changes` with target validation PASS and duplicate clean replay 3/3.
- The `darker_non_ascii_drop_changes` no-overreach result is target-file bounded only; stronger robustness is not claimed.
- The `darker_stdin_filename` matched-null comparison had equal Arm A and Arm B repair success, so it adds a native repair episode but does not provide memory separation evidence.
- Clean replication batch003 implements a matched-null ensemble challenge protocol with difficulty-band admission for moderate-complexity candidates. It must not reuse the three confirmed repair episodes as new candidates, and it blocks cleanly if no safe challenge candidate verifies.
- Full scoring remains `NOT_RUN/disallowed`.
- Memory lift on external real bugs is not demonstrated; the matched-null status is `undemonstrated_equal_performance`.
- Self-maintaining software is not demonstrated.
- BugsInPy remains globally blocked except for future byte-identical exception research.
- This repository is currently suitable as a pre-alpha research archive, not a technical validation release.

## What ControllerGate can do now

- Verify manually supplied workflow artifacts before ingesting output evidence.
- Preserve byte-level manifests and detect manifest drift.
- Validate the external candidate registry and repair episode registry.
- Separate native repair evidence, issue-derived evidence, diagnostic evidence, documentation evidence, and infrastructure evidence.
- Run the current protocol audit and dry-run without promoting later lanes to current.
- Run clean replication acquisition over explicit external leads.
- Create isolated candidate workspaces and attempt structured environment resolution before collection and replay.
- Generate bounded source-only repair patches from verified native candidate context and require patch safety, target validation, and duplicate replay before recording a repair success.
- Define deterministic matched-null ensemble policies for future challenge candidates, including memory-enabled and memory-disabled arm separation, fair null perturbations, and explicit score boundaries.

## Current limits

ControllerGate does not currently claim autonomous repair, full benchmark scoring, memory-lift evidence, self-maintaining software, or technical validation readiness. Issue-derived harnesses do not count as native external repairs. Historical lanes remain auditable evidence, but new replication work should use the clean replication protocol and reusable workflow where possible.

The next technical objective is a matched-null ensemble on a moderate-complexity verified native challenge candidate. If no candidate passes the admission gates, the correct state is a blocked batch003 record, not a success claim.

## Basic local checks

```bash
python scripts/byte_custody_preflight.py
python -m pytest tests/core -q
python scripts/validate_external_candidate_registry.py
python scripts/controllergate_audit.py --protocol current
python scripts/controllergate_run.py --protocol current --dry-run
```

## Manual artifact boundary

Workflow artifacts are ingested only after manual download and local ZIP verification. The repository records local artifact identity and ingests non-archive output files only. Codex must not bless an artifact it fetched for itself.

## Documentation

- Current status: `docs/current_status.md`
- Capability inventory: `docs/capability_inventory.md`
- Evidence model: `docs/evidence_model.md`
- Claim boundaries: `docs/claim_boundaries.md`
- Replication protocol: `docs/replication_protocol.md`
- Public readiness: `docs/public_release_readiness.md`
- Technical validation gap report: `docs/technical_validation_gap_report.md`
- Operational gate matrix: `docs/operational_gate_matrix.md`
