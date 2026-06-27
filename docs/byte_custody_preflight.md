# Byte-custody preflight

ControllerGate evidence files are checked by exact SHA256 manifests. A recurring failure mode is simple LF/CRLF drift: a manifest can be generated from Windows working-tree bytes, while GitHub Actions later checks out the same text files as LF bytes. The scientific content is unchanged, but the byte-level evidence check fails late in the workflow.

The preflight catches that class before dispatch.

Run this sequence before future workflow dispatch:

```bash
python scripts/byte_custody_preflight.py --fix
python scripts/byte_custody_preflight.py
git diff --check
git status --short
```

`--fix` rewrites `SHA256SUMS.txt` files using deterministic ordering and LF-stable text hashes for the v2.12+ auditable output era. It also writes `outputs/byte_custody_preflight_report.json`.

What may be fixed automatically:

- manifest ordering;
- manifest hashes when the only issue is LF/CRLF byte custody;
- the byte-custody report itself.

What must never be silently fixed:

- evidence content;
- registry values;
- patch bytes;
- target logs;
- candidate proof records;
- validation results;
- claim boundaries.

If preflight still fails after `--fix`, treat it as `byte_custody_preflight_failed` unless a real evidence, registry, patch, or validation mismatch is proven. The preflight does not promote the current protocol, enable full scoring, alter repair evidence, select candidates, or support any memory-lift or self-maintaining claim.
