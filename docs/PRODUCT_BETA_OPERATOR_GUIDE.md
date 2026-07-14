# Product Beta operator guide

ControllerGate is operated through `controllergate doctor`, `run`, `resume`, `status`, `verify`, `canary`, and `watch`. Product operations require an explicit manifest, an isolated runtime root outside OneDrive and `E:\`, verified provider identity, typed prerequisite tokens, a single active worker lease, and a rollback-ready proof path. Public remote writes remain disabled.

Batch085 is an exact blocked release candidate: the canonical runtime is present, but the historical Product Beta evidence gate is incomplete. Operators must not translate this controlled capability into a production-readiness or autonomous-maintenance claim.
