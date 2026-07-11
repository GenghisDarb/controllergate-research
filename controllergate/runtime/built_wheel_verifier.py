from __future__ import annotations

import csv
import hashlib
import io
from pathlib import Path, PurePosixPath
import zipfile
from packaging.utils import parse_wheel_filename


def verify_built_wheel(path: Path, package: str, version: str, ordered_tags: list[str]) -> dict:
    errors=[]
    try:name,parsed_version,_,tags=parse_wheel_filename(path.name)
    except Exception as exc:return {"status":"BLOCK","blocker":"built_wheel_filename_invalid","error":type(exc).__name__}
    if str(name).lower().replace('_','-')!=package.lower().replace('_','-'):errors.append('package_identity_mismatch')
    if str(parsed_version)!=str(version):errors.append('version_identity_mismatch')
    with zipfile.ZipFile(path) as z:
        names=z.namelist(); unsafe=[n for n in names if PurePosixPath(n).is_absolute() or '..' in PurePosixPath(n).parts]
        records=[n for n in names if n.endswith('.dist-info/RECORD')]; metadata=[n for n in names if n.endswith('.dist-info/METADATA')]
        if unsafe:errors.append('unsafe_paths')
        if len(records)!=1:errors.append('record_missing_or_ambiguous')
        if len(metadata)!=1:errors.append('metadata_missing_or_ambiguous')
    compatible=any(str(tag) in set(ordered_tags) for tag in tags)
    if not compatible:errors.append('runtime_tag_incompatible')
    return {"status":"PASS" if not errors else "BLOCK","filename":path.name,"sha256":hashlib.sha256(path.read_bytes()).hexdigest(),"size":path.stat().st_size,"package":package,"version":version,"tags":sorted(str(t) for t in tags),"runtime_compatible":compatible,"record_verified":len(records)==1,"errors":errors}
