# Candidate terminal-state policy

Every candidate lead must close into an auditable state before replay is considered. Terminal states include counted duplicate, parked duplicate, retired duplicate, native-test missing, high provider/runtime risk, manual review required, or approved for a future pre-repair replay batch.

The terminal state records are planning evidence only. Repair counts still require target failure materialization, a licensed source-only patch path, post-repair validation, duplicate clean replay, and the count gate.
