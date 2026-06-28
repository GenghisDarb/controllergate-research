# Current protocol

The current ControllerGate protocol remains:

- version: `v2.13`
- lane: `minimal_forensic_context_lane`
- config: `configs/controllergate_current.yaml`

v2.37 adds a maintained clean replication adapter, but it does not promote v2.37 to current protocol.

Historical lanes from v2.12 through v2.36 remain preserved evidence. They can be audited by their versioned scripts, but new replication work should use the shared core package and clean replication protocol unless a new versioned lane is explicitly justified.
