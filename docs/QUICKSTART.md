# ControllerGate quick start

> Current boundary: protocol `v2.19`, package `0.2.0b2.dev0`, 6 issue-derived and 4 native external repair episodes, historical increment 0. Product Beta RC is blocked; prospective effectiveness and memory lift are not established; full scoring is disallowed; public writes and automatic merge are inactive; production readiness and autonomous self-maintenance are not demonstrated.

For a credential-free first run, inspect the frozen candidate contracts from an installed wheel:

```powershell
python -m venv .demo-venv
.demo-venv\Scripts\python -m pip install dist\controllergate-0.2.0b2.dev0-py3-none-any.whl
.demo-venv\Scripts\controllergate evidence inspect-contracts --contracts configs\candidate_execution_contracts_v2.jsonl
```

This command is read-only. It performs no network operation, candidate execution, patch, count change, or release action. A `PASS` means only that the contracts parse and their custody hashes are internally consistent.

ControllerGate safely abstains when legal evidence cannot distinguish the remaining causal hypotheses. The blocker and reopen condition are the useful result; abstention is not permission to guess a patch. Human authorization is a separate, candidate/run/frame-bound prerequisite after scientific source ownership, never a substitute for it.

Evidence and blockers are written to the relevant `outputs/` campaign directory. See [the claim envelope](CLAIM_ENVELOPE.md), [evidence levels](EVIDENCE_LEVELS.md), and [the high-assurance workflow](HIGH_ASSURANCE_REPAIR_WORKFLOW.md). Advanced Reactome and TLD material is architectural/shadow metadata and is intentionally outside this first-use path.

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
