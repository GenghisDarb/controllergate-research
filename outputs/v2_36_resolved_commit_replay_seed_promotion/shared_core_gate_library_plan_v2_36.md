# Shared core gate library plan

v2.36 records this as carry-forward planning only. It does not perform the refactor.

Future modules:

- `controllergate/core/evidence.py`
- `controllergate/core/manifests.py`
- `controllergate/core/registry.py`
- `controllergate/core/git_verify.py`
- `controllergate/core/environment.py`
- `controllergate/core/patch_safety.py`
- `controllergate/core/replay.py`
- `controllergate/core/audit.py`
- `controllergate/core/claim_boundary.py`

The future library must preserve versioned evidence bytes and claim boundaries.
