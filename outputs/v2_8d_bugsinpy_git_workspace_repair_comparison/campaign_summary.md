# v2.8d BugsInPy Git-Workspace Repair Comparison

Aggregate result: `blocked_apoptosis_watchdog_triggered`.

The git-workspace runner fixed the checkout/runtime copy failure. All three
promoted BugsInPy candidates passed the pre-repair replay gate and created
Git-based no-memory and memory-enabled repair workspaces.

The campaign remains not scoreable because all three repair paths were
quarantined by the apoptosis watchdog for no-op/flatline behavior. Full scoring
remains disallowed. Memory lift and self-maintaining software remain
undemonstrated.
