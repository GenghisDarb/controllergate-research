"""Reproduce the published operator experiments without overwriting evidence.

Run from any working directory. The distribution must retain sibling research/
and dynamics/ directories. Only an explicit input allowlist is copied. Historical
archives, stored results and private research material are never copied by this
wrapper. Frozen inputs are checked before and after copying.
"""
from pathlib import Path
import argparse
from datetime import datetime, timezone
import hashlib
from importlib.metadata import PackageNotFoundError, version
import json
import platform
import shutil
import subprocess
import sys

PACKAGE = Path(__file__).resolve().parents[1]
INPUTS = (
    'dynamics/experiment_spec.json',
    'dynamics/FROZEN_DESIGN.json',
    'dynamics/run_operator_audit.py',
    'dynamics/independent_operator_review.py',
    'dynamics/source_snapshot/kernels.py',
    'dynamics/source_snapshot/SOURCE_PROVENANCE.json',
    'dynamics/admissibility/EXPERIMENT_SPEC.json',
    'dynamics/admissibility/FROZEN_EXTENSION.json',
    'dynamics/admissibility/run_admissibility.py',
    'dynamics/admissibility/source_snapshot/kernels.py',
)
FREEZES = (
    'dynamics/FROZEN_DESIGN.json',
    'dynamics/admissibility/FROZEN_EXTENSION.json',
)


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify_freezes(root):
    for relative in FREEZES:
        record = root/relative
        freeze = json.loads(record.read_text(encoding='utf-8'))
        for filename, expected in freeze['files'].items():
            if sha256(record.parent/filename) != expected:
                raise RuntimeError(f'Frozen hash mismatch: {relative}: {filename}')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-dir', required=True, type=Path,
                        help='A new directory; existing paths are refused.')
    parser.add_argument('--prepare-only', action='store_true',
                        help='Copy and verify inputs without running experiments.')
    args = parser.parse_args()
    destination = args.output_dir.resolve()
    if destination.exists():
        raise RuntimeError('Use a new output directory; existing evidence is preserved.')
    verify_freezes(PACKAGE)
    for relative in INPUTS:
        if not (PACKAGE/relative).is_file():
            raise FileNotFoundError(relative)
    destination.mkdir(parents=True)
    for relative in INPUTS:
        copied = destination/relative
        copied.parent.mkdir(parents=True,exist_ok=True)
        shutil.copyfile(PACKAGE/relative,copied)
        if sha256(copied) != sha256(PACKAGE/relative):
            raise RuntimeError(f'Copy hash mismatch: {relative}')
    verify_freezes(destination)
    try:
        numpy_version = version('numpy')
    except PackageNotFoundError:
        numpy_version = None
    environment = {
        'created_utc':datetime.now(timezone.utc).isoformat(),
        'python':platform.python_version(),
        'implementation':platform.python_implementation(),
        'numpy':numpy_version,
        'system':platform.system(),
        'machine':platform.machine(),
        'tested_reference_environment':{'python':'3.12.14','numpy':'2.3.5'},
        'input_sha256':{relative:sha256(destination/relative) for relative in INPUTS},
        'scope':'Fresh generated results; execution timestamps and JSON hashes need not match archived outputs.',
    }
    (destination/'REPRODUCTION_ENVIRONMENT.json').write_text(
        json.dumps(environment,indent=2)+'\n',encoding='utf-8')
    scripts = (
        'dynamics/run_operator_audit.py',
        'dynamics/independent_operator_review.py',
        'dynamics/admissibility/run_admissibility.py',
    )
    if args.prepare_only:
        print(json.dumps({'status':'PREPARED_AND_HASH_VERIFIED','input_files':len(INPUTS),'scripts':scripts}))
        return
    for script in scripts:
        subprocess.run([sys.executable,str(destination/script)],
                       cwd=destination,check=True)
    print(json.dumps({'status':'REPRODUCED','output_dir':str(destination),
                      'scripts_completed':len(scripts)}))


if __name__ == '__main__':
    main()
