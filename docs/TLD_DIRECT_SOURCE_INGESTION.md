# TLD direct-source ingestion

Batch098 supports private, directly supplied historical research files without requiring Dropbox, a public URL, or an external source artifact. The source material remains nonauthorizing shadow evidence. It cannot change maintenance state, create a causal fact, grant source ownership, authorize a repair, increment a count, or promote a release.

## Supplying lawful private copies

Place files under `incoming_artifacts/batch098_tld_direct_sources/`. This directory is ignored by Git. An authorized researcher may provide text, Markdown, JSON, notebook files, DOCX files, or a ZIP containing those formats. Do not place secrets, unrelated archives, or executable payloads there.

The expected corpus covers Notebooks 1 through 44 and includes the applicable formal lexicon, errata map, technical standard/input protocol, and source registry. Identity and coverage are determined from bytes and content—not filenames.

## Building and checking the bundle

```powershell
python scripts/build_batch098_tld_bundle_from_direct_sources.py `
  --source-root incoming_artifacts/batch098_tld_direct_sources `
  --output-bundle incoming_artifacts/batch098_tld_reconstructed/ControllerGate_TLD_1-44_Direct_Source_Custody_Bundle.zip `
  --output-manifest outputs/post_v2_37_hardening_batch098_causal_hypergraph_real_materialization_topology_probe_closure/tld_direct_bundle_builder_manifest_v1.json `
  --output-report outputs/post_v2_37_hardening_batch098_causal_hypergraph_real_materialization_topology_probe_closure/tld_direct_bundle_builder_report_v1.json

python scripts/audit_batch098_tld_direct_source_inventory.py `
  --source-root incoming_artifacts/batch098_tld_direct_sources `
  --output-dir outputs/post_v2_37_hardening_batch098_causal_hypergraph_real_materialization_topology_probe_closure

python scripts/verify_batch098_tld_bundle_reproducibility.py `
  --source-root incoming_artifacts/batch098_tld_direct_sources `
  --output-bundle incoming_artifacts/batch098_tld_reconstructed/ControllerGate_TLD_1-44_Direct_Source_Custody_Bundle.zip `
  --output-dir outputs/post_v2_37_hardening_batch098_causal_hypergraph_real_materialization_topology_probe_closure
```

The builder preserves original bytes separately from normalized text. It rejects unsafe paths, symlinks, unreadable text, encrypted members, normalized collisions, and case-fold collisions. ZIP timestamps, permissions, compression, member order, and JSON serialization are deterministic. The verifier builds twice in independent processes and temporary directories and requires identical final bytes.

Exact duplicates retain every original identity while normalized content may be deduplicated by hash. Partial overlaps retain both parents. Explicit errata can resolve notation history when its evidence hash and location are recorded. An unresolved conflict blocks the affected source rules; no invented consensus is generated.

## Requirement compilation and local execution

Requirements are compiled only when a supplied source contains supporting evidence. Public registry rows carry source hashes, opaque locations, evidence-window hashes, and neutral engineering statements; they do not reproduce private passages. Missing earlier interpretations are reported as `NOT_REESTABLISHED_FROM_DIRECT_SOURCE_CORPUS`.

Run the private-source helper with:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/run_batch098_with_local_tld_sources.ps1
```

Historical candidates require exact Python 3.7, 3.11, and 3.13 provider interpreters. Set `CG_PYTHON_37` and `CG_PYTHON_311` to the approved interpreter executables when they are not installed globally. The helper blocks before scientific materialization when provider parity is unavailable.

The helper uses separate subprocesses and immutable directory handoffs for custody, producers, verifiers, truth custody, experiments, source ownership, critic reconstruction, mutations, and finalization. A successful private run is labeled `LOCAL_PROTECTED_SOURCE_RUN`; it is never labeled a GitHub CI pass.

## Public reproducibility boundary

The public repository contains the builder, schemas, synthetic fixtures, tests, and these instructions. It does not contain the private research corpus or extracted passages. Another researcher can reproduce the mechanism only after lawfully obtaining and supplying their own copies. Outputs reproducible without the private corpus include path-safety controls, deterministic packaging behavior, authority-firewall behavior, conflict handling, and synthetic coverage tests.
