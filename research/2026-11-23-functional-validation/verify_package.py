"""Verify included payloads against the bundled manifest; no network or writes."""
from pathlib import Path
import hashlib
import json
import sys

root = Path(__file__).resolve().parent
manifest = json.loads((root / 'PACKAGE_MANIFEST.json').read_text())
failures = []
for item in manifest['files']:
    path = root / item['path']
    if not path.is_file():
        failures.append({'path': item['path'], 'error': 'missing'})
        continue
    data = path.read_bytes()
    if len(data) != item['bytes'] or hashlib.sha256(data).hexdigest() != item['sha256']:
        failures.append({'path': item['path'], 'error': 'identity_mismatch'})
print(json.dumps({'status': 'PASS' if not failures else 'FAIL',
                  'verified_payloads': len(manifest['files']),
                  'failures': failures,
                  'scope': 'Consistency with bundled manifest, not external authentication.'}, indent=2))
sys.exit(bool(failures))
