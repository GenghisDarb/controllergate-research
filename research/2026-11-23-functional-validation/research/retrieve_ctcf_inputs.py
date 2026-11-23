"""Verify, or explicitly retrieve, the two original CTCF analysis inputs.

The public evidence export omits these data bytes because a separate data
redistribution license was not verified. This helper retrieves the exact files
from their original publisher repository. Existing files are never overwritten.
Network access is used only when --fetch is supplied and an input is absent.
"""
from pathlib import Path
import argparse
import hashlib
import json
import urllib.request

COMMIT = 'f155c4c889ea124a8f55ab8f620e540628e18f92'
BASE = 'https://raw.githubusercontent.com/elifesciences-publications/spot-on-matlab/' + COMMIT + '/'
INPUTS = [
    {
        'path': 'ctcf_rep1_cell01.mat',
        'upstream_path': 'Data/CTCF_134Hz_rep1/U2OS_C32_Halo-CTCF_PA-JF646_1ms-633nm_134Hz_rep1_cell01.mat',
        'bytes': 630482,
        'sha256': '6547e6b6e5f3dc2424dd7d1ceb17f116408acf7fff8ae67091c08b5d2f2850c1',
        'git_blob_sha1': '6486d6b15c68faf47395f54427d25f1680fc7acd',
    },
    {
        'path': 'ctcf_rep3_cell01.mat',
        'upstream_path': 'Data/CTCF_134Hz_rep3/U2OS_C32_Halo-CTCF_PA-JF646_1ms-633nm_134Hz_rep3_cell01.mat',
        'bytes': 435233,
        'sha256': '9cb8e989666f634a005a0ede86a02230705bf62ee2e36840131aefad4b490351',
        'git_blob_sha1': '49627183cf193d00c6a663750c2de408f58a4919',
    },
]


def check(raw, record):
    observed = {
        'bytes': len(raw),
        'sha256': hashlib.sha256(raw).hexdigest(),
        'git_blob_sha1': hashlib.sha1(b'blob ' + str(len(raw)).encode() + b'\0' + raw).hexdigest(),
    }
    for field, value in observed.items():
        if value != record[field]:
            raise ValueError(f"Input identity mismatch for {record['path']}: {field}")
    return observed


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--fetch', action='store_true', help='Retrieve missing files from the pinned publisher source.')
    parser.add_argument('--directory', type=Path, default=Path(__file__).resolve().parent)
    args = parser.parse_args()
    records = []
    for item in INPUTS:
        dest = args.directory / item['path']
        source = BASE + item['upstream_path']
        if dest.exists():
            raw = dest.read_bytes()
            origin = 'existing_local_file'
        elif args.fetch:
            req = urllib.request.Request(source, headers={'User-Agent': 'ControllerGate-research-input-retrieval/1'})
            with urllib.request.urlopen(req, timeout=30) as response:
                raw = response.read(item['bytes'] + 1)
            check(raw, item)
            dest.parent.mkdir(parents=True, exist_ok=True)
            with dest.open('xb') as handle:
                handle.write(raw)
            origin = 'retrieved_from_pinned_publisher_source'
        else:
            raise SystemExit(f"Missing {dest}. Run with --fetch to retrieve the pinned original input.")
        records.append({'path': str(dest), 'source_url': source, 'origin': origin, **check(raw, item)})
    print(json.dumps({'status': 'PASS', 'scope': 'Exact input identity; no new analysis execution or redistribution license assertion.', 'inputs': records}, indent=2))


if __name__ == '__main__':
    main()
