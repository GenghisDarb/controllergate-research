# Upgrade and migration

Batch085 introduces ControllerState schema version 2 and a proof-derived historical count migration. Before upgrading, preserve the state database and verify its event and proof chains. Apply migrations once, regenerate current-state views, and run the state-view synchronization audit. Legacy batch implementations remain historical replay evidence and are not production imports.
