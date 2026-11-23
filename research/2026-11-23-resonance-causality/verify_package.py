"""Verify package bytes and frozen source identities; run no science."""
from pathlib import Path, PurePosixPath
import hashlib
import json

ROOT=Path(__file__).resolve().parent
def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def safe_path(value):
    p=PurePosixPath(value)
    if p.is_absolute() or '..' in p.parts or '\\' in value or (p.parts and ':' in p.parts[0]):
        raise ValueError('Unsafe package-relative path')
    result=ROOT.joinpath(*p.parts)
    if result.is_symlink():raise ValueError('Symlink is not a package payload')
    return result
def main():
    manifest=json.loads((ROOT/'MANIFEST.json').read_text(encoding='utf-8'))
    expected=set()
    for entry in manifest['files']:
        path=safe_path(entry['path'])
        if entry['path'] in expected:raise ValueError('Duplicate manifest path')
        expected.add(entry['path'])
        assert path.is_file(),entry['path']
        assert path.stat().st_size==entry['bytes'],entry['path']
        assert digest(path)==entry['sha256'],entry['path']
    actual={p.relative_to(ROOT).as_posix() for p in ROOT.rglob('*')
            if p.is_file() and '__pycache__' not in p.parts}
    assert actual==expected|{'MANIFEST.json'},'Unmanifested or missing payload'
    freezes=['causal/FROZEN_DESIGN.json','dynamics/FROZEN_DESIGN.json',
             'dynamics/admissibility/FROZEN_EXTENSION.json']
    checks=0
    for relative in freezes:
        freeze_path=safe_path(relative)
        frozen=json.loads(freeze_path.read_text(encoding='utf-8'))
        for name,sha in frozen['files'].items():
            nested=(PurePosixPath(relative).parent/PurePosixPath(name)).as_posix()
            assert digest(safe_path(nested))==sha,nested
            checks+=1
    for relative in ['causal/MANIFEST.json','research/PUBLICATION_FILE_MANIFEST.json']:
        record=json.loads(safe_path(relative).read_text(encoding='utf-8'))
        for entry in record['files']:
            name=entry.get('path',entry.get('file'))
            resolved=('causal/'+name) if relative.startswith('causal/') else name
            target=safe_path(resolved)
            assert target.stat().st_size==entry['bytes'],resolved
            assert digest(target)==entry['sha256'],resolved
    report={'status':'PASS','manifest_sha256':digest(ROOT/'MANIFEST.json'),
            'payload_files':len(expected),'frozen_manifests':len(freezes),
            'frozen_input_hashes_checked':checks,'nested_custody_manifests':2,
            'scope':'Byte integrity and frozen identities only. No numerical experiment was rerun. The manifest is not self-hashed; preserve its hash in external custody.'}
    print(json.dumps(report,indent=2))
if __name__=='__main__':main()
