# Functional Reactome translation: local implementation and evidence

## Completed result

The stronger functional hypothesis is now tested on a declared executable model, beyond the earlier label control. A local compiler preserves the source-grounded participants, separate compartments, shared resources, catalytic roles and directed actions of six Reactome events. It executes joint prerequisites and atomic resource updates through the actual archived ControllerGate RESOURCE_FLUX primitive. An independently written, equally informed generic incidence/read-arc interpreter agrees exactly.

The existing project's resource guards, source references, nonauthorizing state, canonical stage services and receipt machinery are credited. The repair is at the boundary between those capabilities: a source record naming a resource is not a runtime inventory, and a generic nonempty payload is not a resource transaction.

## Executed results

Code, source transcription, model and protocol were locally frozen before outcome files were generated. The freeze is an execution-order receipt, not a trusted timestamp or an independently registered study.

| Comparison | Cases | Wrong enabling decisions | Wrong successful successor states | Meaning |
|---|---:|---:|---:|---|
| Faithful atomic translation |12,150|0|0|Matches the declared source-token oracle on the fixed domain|
| Competent generic incidence interpreter |12,150|0|0|Same information, exact tie with faithful translation|
| Edge-only incoming connectivity ablation |12,150|5,112|0 among mutually enabled cases|Missing joint requirements gives false enabling and negative diagnostic inventories|
| Consume-catalyst ablation |12,150|0|2,592|First-step enabling agrees while every enabled successor incorrectly depletes the catalyst|
| Pool-compartments ablation |12,150|508|0 among mutually enabled cases|Remote matter is incorrectly treated as locally available|

The source model enabled 2,592 of the 12,150 cases. These are designed finite-grid counts, not biological frequencies, clinical rates or provider performance. The mismatch columns must not be read as percentages of real-world reactions.

Every ordered pair of the six actions was also tested under three prescribed inventories: 108 batches. Both competent sequential atomic implementations matched the oracle in all 108. Independent approvals against the unchanged initial snapshot disagreed in 16 batches, producing 16 negative diagnostic inventories. This tests shared-resource reservation semantics in a deterministic model, not actual threaded or database concurrency.

Six fixed composed traces were retained. GAPDH→LDH→GAPDH→LDH completed four actions while restoring the shared NAD/NADH/H+ projection after each pair and converting two substrate units to products. Omitting the second GAPDH action gave PASS,PASS,BLOCK. A reusable catalyst allowed two LDH actions; the consume-catalyst ablation allowed only the first. Separate curated reverse events returned the selected model to its initial state. Correct transport resolved the remote-proton case through the source-defined cotransport action.

Sixteen focused unit tests passed. They cover exact successor agreement, catalyst reuse, joint prerequisites, location, reverse identity, projected versus full return, missing evidence, atomic rollback, overcommit, noninjective mappings, invalid numeric inputs, unsupported contracts, unknown kinetics and the archived floating-point guard's exact-integer range.

## The concrete existing-code finding

`legacy_witnesses.py` executes exact function bodies from the pinned archived source on an independently source-grounded RPIR-shaped LDH fixture. It does not pretend to replay the original large ledger or installed provider workflow.

1. `value_bound._primitives` selects EVENT_CONTRACT, ENTITY_STATE, COMPARTMENT, CATALYST and IRREVERSIBLE_REACTION for the fixture; it never selects RESOURCE_FLUX in that function's available branches.
2. `_actual_event` retains source records and creates a nominal resource_delta as `max(0,len(inputs)-len(outputs))`. A scalar count difference cannot express which resource was consumed, its compartment or its multiplicity, and the normal fixture does not emit that field because RESOURCE_FLUX is not selected.
3. `integrated_source_bound_scenario` supplies a missing primitive field from generic fallbacks. In the executed witness, `resource_delta` comes from the `entity_state` list.
4. The archived RESOURCE_FLUX accepts that nonempty list as generic conformance input; its numeric underflow branch is not entered, and no balance field is produced. The explicit numeric negative control correctly BLOCKs a spend of 1 from 0. The stronger primitive exists; this payload path does not engage it.
5. The inspected canonical simulation producer/verifier protects stage, source-event/result hashes and authority. It does not reconstruct the missing resource accounting from participant metadata.

The archived PASS is **source-bound conformance**. It is not reinterpreted as a claim that a physical reaction is enabled. The local addition supplies the stronger state/transition contract needed to test Brad's proposed functional correspondence.

## Implemented repair and reuse

`prepare_contract.py` normalizes the preserved, independently transcribed official source contract. It keeps all six directions separate and preserves thirteen identified places. `token_translation.py` supplies:

- `load_model(payload)` for the typed untimed token contract;
- `state_from(model,counts)` with exact nonnegative integers and explicit unknown values;
- `FaithfulTranslation(model).step(reaction,inventory)` for the source-to-software compiler and private atomic resource update;
- `GenericIncidence(model).step(...)` for the competent independent interpreter;
- `source_step(...)` for the separately written direct contract oracle;
- `sequential_batch(...)` for declared ordered commit semantics;
- PASS, BLOCK and UNRESOLVED outcomes with reasons and an unchanged state on a blocked/unresolved operation.

This is an isolated local module and reproducible experiment. It has not replaced the live ControllerGate compiler, broker, repository state service or source-ownership verifier. To integrate it, the runtime must supply an independently warranted inventory and active-role observation, preserve source/contract hashes, evaluate this transition before minting a success token, and commit the returned state through an appropriate transaction boundary. Source metadata and a self-generated receipt cannot themselves authenticate those runtime observations.

## Reproduce

Python 3.10+ and its standard library are sufficient. From this folder:

```bash
python -m unittest test_translation -v
python run_benchmark.py
python legacy_witnesses.py
python verify_artifacts.py
```

The evaluation scripts verify every frozen input hash before running. Re-running overwrites deterministic derived outcome files with the same fixed experiment; do not modify the frozen source or model to improve scores. `freeze_experiment.py` refuses to overwrite an existing freeze or to freeze after outcome files exist.

## Files and scope

`results.json` has all aggregates, per-event counts, bounded counterexamples, all 108 batch records and all composed traces. `source_oracle_truth_table.csv` contains the 12,150 initial states and expected successors in the frozen place order. `legacy_witnesses.json` contains the actual adapter payload, chosen primitives, fallback origin and paired local/remote worlds. `SOURCE_LEDGER.json` records exact source paths, line ranges and hashes. `FORMAL_TRANSFER.md` states the preservation proposition, proof and limits. `test_receipt.json` records the observed unit-test result; `verification.json` checks the frozen inputs and artifact consistency.

The biological input is an explicitly identified **manual transcription of official rendered Reactome records**, not exact SBML export bytes. The three catalyst places are aggregate active-role assertions: LDH and GAPDH alternatives are not falsely converted into AND requirements; the BSG:MCT transport complex is not treated as a DefinedSet. Its internal assembly is not modeled. PolyUb-LDHA regulation is retained as an unmodeled quantitative limitation, not converted to a hard-zero inhibitor. No rate, concentration, pH, diffusion, crowding, temperature, thermodynamic potential or physical trajectory is inferred.

The mathematical equivalence applies to the chosen untimed contract and representable exact-integer steps. It does not establish a full biological isomorphism, predictive cell dynamics, superiority over an equally informed generic solver, ControllerGate causal ownership, software repair gain, deployment readiness, a TORUS 14-layer derivation or a TLD validation run.
