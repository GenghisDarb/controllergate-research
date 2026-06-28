# ControllerGate workflows

Historical workflows are preserved so prior evidence can be reproduced and audited.

For new work, prefer `controllergate_reusable_lane.yml`. It accepts a lane id, runner, audit script, artifact name, regression level, and core-test toggle. New version-specific workflows should be added only when a lane needs behavior the reusable workflow cannot express safely.

v2.37 marks the transition from a long sequence of one-purpose workflows toward a maintained research harness with shared gates, consolidated state files, and selected regression checks.

Corrected post-v2.37 artifact uploads should use a clean staged payload directory and must not upload cache directories, compiled Python files, virtual environments, local downloads, credentials, or archive artifacts.
