# ControllerGate quick start

ControllerGate is a research harness for proof-gated software changes. The smallest local demonstration uses only included fixture files and the Python standard library; it needs no account, token, network connection, container engine, or external repository.

From the repository root, run:

```powershell
python scripts/run_local_controllergate_demo.py
```

The JSON proof shows five bounded steps:

1. A manifest defines the only source path that may change.
2. An attempted test-expectation edit is blocked.
3. A source-only one-line change is authorized and applied in a temporary workspace.
4. The declared behavior is validated.
5. The original bytes are restored and their SHA256 is rechecked.

To retain the proof outside the repository:

```powershell
python scripts/run_local_controllergate_demo.py --output C:\Temp\controllergate-demo-proof.json
```

This demonstration validates the local authorization, validation, rollback, and proof-record pattern. It is not an external repair episode, does not affect repair counts, and does not demonstrate AMDS effectiveness, memory lift, production readiness, live-device repair, or self-maintaining software.

The validated protocol is `v2.19 authorized_amds_active_maintenance_lane`. The current evidence boundary contains 6 issue-derived and 4 native external repair episodes. See [CAPABILITY_AND_CLAIM_MATRIX.md](CAPABILITY_AND_CLAIM_MATRIX.md) for the precise status of broader capabilities.
