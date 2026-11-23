# Publication safety and portability review

**Decision: suitable for publication within the inspected scope, with frozen bytes preserved.**

This review covers the four `archive/PUBLIC_*` files, the `research/` material and the `dynamics/` experiment, independent reviewer and admissibility extension. It does not cover the separate `causal/` package or an integrated report added after this review. No frozen experiment file was modified.

## Source safety

The inspected distributable files contain public-safe paraphrases, source metadata, mathematical reasoning, supplied synthetic inputs, code and numerical results. The review found no embedded private absolute filesystem paths, credentials, raw private chat passages or symlinks. Public reference links point to research publications or the identified project repository. Original conversation passages remain outside the distributable selection.

Use an explicit package allowlist. Include `archive/PUBLIC_*`, reviewed `research/` files, and the listed `dynamics/` files. Exclude every `PRIVATE_*` file, the archive builder, the nonpublic raw search coverage/hit files, and generated Python caches. Do not recursively copy the complete working folder or the complete archive directory.

The historical ledgers identify private source files by research title, SHA-256 and physical LF-separated line coordinates. They intentionally do not redistribute those private originals. Thus the included numerical experiments can be independently reproduced from the package, while checking every historical source passage still requires separately authorized access to the original archive. Hashes alone do not supply that access.

## Portability findings

The two experiment implementations and the independent reviewer locate inputs relative to their own script files. The complete original `kernels.py` module is not imported: its selected functions are extracted through the Python AST. The snapshot's ordinary package imports therefore do not require installing the original Field Studio application.

The main experiment and independent reviewer intentionally refuse to overwrite their stored results. Running them in place after downloading a package with archived results will stop. The admissibility extension separately supports a new `--output-dir`.

The added `reproduce_public_package.py` wrapper solves the overwrite issue without changing frozen code. It:

1. Verifies both frozen manifests in the distributed package.
2. Copies ten explicitly named input files into a new destination.
3. Verifies the copied hashes and records the local Python/NumPy environment.
4. Runs the main experiment, independent review and admissibility extension there.

Stored results, raw archives, private files and original review receipts are not copied into the reproduction directory. The generated execution timestamps will differ from the archived ones. Compare scientific fields, tolerances and status checks rather than expecting whole output JSON files to have identical hashes.

## Tested dependencies and reproduction command

The audited execution environment is **CPython 3.12.14 with NumPy 2.3.5**. NumPy is the only nonstandard dependency of the main experiment and independent reviewer. The admissibility extension and wrapper use only the Python standard library. These are the tested versions, not a claim to have determined the oldest compatible versions.

Using a Python environment with the tested interpreter, run from the unpacked package root:

```sh
python -m pip install -r research/requirements-reproduction.txt
python research/reproduce_public_package.py --output-dir ../torus_resonance_reproduction_2026_11_23
```

Choose a different destination if that path already exists. The command works with the same Python executable on Windows, macOS or Linux; only Linux was executed in this review. It launches subprocesses with argument lists, so spaces in paths are supported.

To check file preparation and hashes without repeating the numerical experiments:

```sh
python research/reproduce_public_package.py --output-dir ../torus_resonance_prepare_check --prepare-only
```

The expected result files in a completed fresh destination are:

- `dynamics/results.json` and `dynamics/summary.json`.
- `dynamics/independent_operator_review_receipt.json`.
- `dynamics/admissibility/RESULTS.json` and `dynamics/admissibility/SUMMARY.json`.
- `REPRODUCTION_ENVIRONMENT.json`.

## Preserve frozen line endings

The frozen manifests identify exact file bytes. Automatic LF-to-CRLF conversion changes those hashes even when Python semantics are unchanged. A ZIP download preserves the packaged bytes. For Git reproduction, disable automatic line-ending conversion for these frozen inputs, or add a package-local `.gitattributes` rule such as `dynamics/** -text` before distributing the package. This review did not change repository attributes or frozen files.

One research derivation names the earlier source-collection path `current_fieldstudio/python/torusbrot/kernels.py`. That is a provenance label rather than a runtime dependency. The complete matching distributable source is `dynamics/source_snapshot/kernels.py`.

## Verification performed

The packaging test used a fresh directory containing spaces and ran from a different working directory. All ten copied inputs matched their source hashes; both frozen manifests passed. The test confirmed that no archived numerical results or reviewer receipts were copied. It also confirmed that a second attempt at the same destination refused to overwrite it.

The wrapper preparation and safety tests are recorded in `PORTABILITY_REVIEW_RECEIPT.json`. The main experiment's scientific computations had already been independently reviewed; this packaging check did not rerun the full forcing suite. The separate source review reconstructed all twenty cases and checked all 120 saved forcing gains, with three scalar forced recurrences replayed, as stated in its own receipt.

Publication should retain the stated scientific limits: supplied parent references, synthetic iteration clocks and visibility floors, no preferred fourteen-layer result, and no claim that nonnegative projection implements biological reaction semantics. The stronger source-specific claims and historical repairs are already distinguished in the accompanying reports.
