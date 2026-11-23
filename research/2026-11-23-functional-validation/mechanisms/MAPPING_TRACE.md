# Existing translation paths and the local semantic extension

All repository observations below concern commit `38897b79588f3ff4b1b9002eedc299a9bcf05140`. Physical source-line ranges and pinned URLs are in `SOURCE_LEDGER.json`; the larger prior history snapshot remains unchanged.

## The existing path is more than a naming scheme

`ValueBindingResolver` resolves content-addressed participant, catalyst, compartment, modification, event-order and related records. `compile_value_bound_candidate` keeps the source event identity, graph hash and individual reference lists, marks open/uncertain contracts, and forbids these records from granting repair authority. Those are real provenance and structural controls. The local experiment does not replace or discredit them.

The canonical runtime also performs actual primitive calls, tests missing-field and authority controls, uses registered stage services and writes receipts. Its numeric RESOURCE_FLUX has a real underflow check. TRANSLOCATION has a source-compartment guard for its expected dictionary-shaped input. These capabilities already existed.

The narrower issue is whether **the payload and current state that reach each guard** preserve the biological relation being claimed. Several distinct implementation paths must be kept separate.

| Source relation | Existing source/value-bound path | Executed or statically verified meaning | Local candidate change |
|---|---|---|---|
| Event and participant identity | Content-addressed references, source stable ID, source graph hash | Retains provenance and participant records | Keeps exact curated directed event IDs and maps every resource to a distinct software place |
| Input/output roles and quantities | `_actual_event` puts records into entity_state and commit_transition; nominal resource_delta is a nonnegative difference of row counts | Records resolve; normal primitive selection does not add RESOURCE_FLUX. A row-count scalar would lose entity, amount and location even if emitted | Uses separate consumed/produced coefficient maps and a current inventory; jointly checks before updating |
| Catalyst role | Catalyst references and a nonempty source list reach CATALYST | Source activity record is present; this is not a measured active-enzyme inventory | Reads a separately supplied asserted-active role without consuming it; its biological validity remains an input obligation |
| Compartment identity and transport | Resolved compartment/transition lists enter compartment/destination fields | The special TRANSLOCATION guard expects a dictionary with source; a resolved nonempty list does not enter that branch. This is a static type-path finding, not an additional executed transport receipt | Each physical entity/compartment has its own place; transport is a sourced consumed→produced transition between the distinct places |
| Required input AND | Canonical stages already require their prescribed tokens | Real software-stage prerequisites are enforced; source metadata alone does not establish current metabolite availability | The chosen reaction's whole multiset and catalytic read conditions are checked against one inventory |
| Resource interlock | RESOURCE_FLUX exists, but `_primitives` omits it from value-bound candidate selection; integrated composition falls back to another nonempty field | Executed fixture sends entity_state list as resource_delta; presence conformance PASS, no numeric balance produced | Per-resource numeric guards run on private working state; commit only after all changes succeed |
| Timing and environment | Edition lineage or explicit source-time-not-exposed placeholder populates progress_clock | Does not provide a kinetic duration or rate law | Rate/deadline questions remain UNRESOLVED; location and availability are the only tested environmental dimensions |
| Normal/variant and regulators | Source records and semantic signatures retained | Structural and conformance evidence; no newly inferred quantitative effect | LDH negative regulation is recorded as outside this compact dynamic model, not changed to a hard-zero rule |
| Canonical maintenance order | Required prior tokens, frozen anchors, verified stage output and nonauthorizing simulation boundary | Real stage execution discipline; it does not reconstruct omitted molecular resource semantics | Candidate transition would need a warranted inventory and transactional commit before a success token; no live integration has occurred |

## Why the downstream receipts do not remove this particular loss

The inspected `execute_simulation_stage` consumes the source event and primitive results, requiring each result to be PASS. `verify_simulation_stage` checks stage identity, producer execution, source-event hash, mechanism-result hashes and nonauthorizing state. It does not derive participant stoichiometry or current availability independently. This is an appropriate custody/conformance layer but cannot recover an inventory that was never supplied.

The executed paired-world witness keeps the same LDH reaction metadata and source-event hash. One world contains its required proton in the cytosol; the other has the same total proton count only in the extracellular region. The chosen source-token oracle gives PASS versus BLOCK. The archived source-event projection is identical. The point is a representational limit, not a claim that the archived conformance PASS falsely asserted a physical event.

## Separate later Batch103 path

The later `reactome_source_grounded_scenarios_v2.py` maps present source fields to primitive IDs and operation-family names. Its operation sequence includes acquisition, gate checks, ordered transitions, replay and proof-ledger steps. The inspected `build_batch103_reactome_closure.py` loop generates a hash chain over those operation families and corresponding nonauthorizing receipts; it does not call this earlier primitive runtime in that loop. Source-backed field coverage and operation-order provenance should therefore not be equated with the new token-state fidelity result. Conversely, that later hash-chain path does not erase the earlier real resource, compartment and canonical-state services.

## Canonical order and biological analogy boundary

The existing canonical stack encodes the software sequence: five-set reference core; fourteen-set native topology; materialization; six-set activation licensing; bounded operation; fourteen-contact audit; duplicate clean replay; phase/seed constraint; 196 proof obligations. Its own code rejects exact universal biological interpretations of those counts and rejects Reactome coverage as evidence of causal gain. The present experiment does not alter the order, prove it optimal, or supply a biological derivation of 5/14/6/196. It adds a concrete semantic-preservation test that such an architecture can host.

## Repair playbook

**Root cause:** a source-reference/type-presence contract and an execution-state contract answer different questions. The adapter preserves provenance but does not preserve the inventory-conditioned transition relation; generic fallback values can also bypass specialized type-dependent guards.

**Local fix:** compile typed, identified, compartment-qualified resources; separate consumed inputs from reusable read conditions; supply explicit current state; check all requirements jointly; apply the archived resource guard per identity; preserve the original state on failure; keep unknown evidence unresolved.

**Detection:** retain paired states with identical source metadata but different availability, two sequential uses of a reusable catalyst, same-chemical/different-compartment cases, shared-resource overcommit, and missing-output/unknown-state controls. Compare exact successor states and composed traces, not only PASS/BLOCK counts or semantic labels.

**Where the same pattern may appear:** generic primitive-field fallbacks, source lists passed to dictionary/numeric-specific guards, source order mistaken for event timing, and hashes of earlier PASS results used as stronger semantic evidence. These are places to inspect, not claims that every project path has the same defect.
