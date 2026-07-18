# Read-only contract inspection

From an installed ControllerGate wheel, run:

```powershell
controllergate evidence inspect-contracts --contracts configs/candidate_execution_contracts_v2.jsonl
```

The command parses and hashes the sealed contracts. It performs no network access, candidate execution, repository writes, patching, repair counting, or release action.
