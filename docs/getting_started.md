# Getting started

Use a normal checkout of `C:\Dev\ControllerGate` on the `controllergate-v1.7-alpha-real-trace-pilot` branch.

Basic local checks:

```bash
python scripts/byte_custody_preflight.py
python -m pytest tests/core -q
python scripts/validate_external_candidate_registry.py
python scripts/controllergate_audit.py --protocol current
python scripts/controllergate_run.py --protocol current --dry-run
```

To run the clean replication adapter:

```bash
python scripts/controllergate_clean_repair.py --config configs/clean_replication_batch_001.json
python scripts/audit_clean_replication_protocol.py
```

Do not place downloaded artifacts, external source checkouts, virtual environments, credentials, caches, ZIP files, or temporary workspaces inside the repository.
