# ControllerGate architecture

ControllerGate is a provenance-first software repair research harness.

The v2.37 transition introduces three maintained layers:

1. `controllergate.core`: reusable evidence, manifest, registry, replay, patch-safety, claim-boundary, and state helpers.
2. `controllergate.protocols`: stable protocol interfaces, including the clean replication adapter.
3. `controllergate.experiments`: batch-level orchestration that can use shared gates without creating a new one-purpose lane for every blocker.

Historical versioned lanes remain evidence history. They are not deleted or rewritten by v2.37.

The current protocol remains v2.13 until a later promotion is explicitly implemented and audited.
