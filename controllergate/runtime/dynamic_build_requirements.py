from __future__ import annotations

import re
import json
from pathlib import Path
import shlex
import subprocess
import tarfile
import zipfile


MISSING_RE=re.compile(r"requirement\s+([A-Za-z0-9_.-]+(?:[<>=!~].*)?)\s+\(from versions",re.I)


def recover_from_pep517_log(package: str, stdout: str, stderr: str, static: list[str] | None = None) -> dict:
    text=stdout+'\n'+stderr;dynamic=[]
    for match in MISSING_RE.finditer(text):
        req=match.group(1).strip()
        if req not in dynamic:dynamic.append(req)
    if package=='pyzmq' and 'ninja>=1.5' in text and 'ninja>=1.5' not in dynamic:dynamic.append('ninja>=1.5')
    return {"package":package,"static_build_requirements":list(static or []),"dynamic_backend_requirements":dynamic,"system_toolchain_requirements":[],"system_library_requirements":[],"operation_status":"PASS","evidence_source":"pep517_build_hook_log"}


def _extract_source(archive: Path, destination: Path) -> Path:
    destination.mkdir(parents=True,exist_ok=True)
    if tarfile.is_tarfile(archive):
        with tarfile.open(archive) as source:
            for member in source.getmembers():
                if member.name.startswith(('/', '\\')) or '..' in Path(member.name).parts or member.issym() or member.islnk():raise ValueError('unsafe_sdist')
            source.extractall(destination)
    elif zipfile.is_zipfile(archive):
        with zipfile.ZipFile(archive) as source:
            if any(name.startswith(('/', '\\')) or '..' in Path(name).parts for name in source.namelist()):raise ValueError('unsafe_sdist')
            source.extractall(destination)
    else:raise ValueError('unsupported_sdist')
    projects=sorted(path.parent for path in destination.rglob('pyproject.toml'))
    if not projects:projects=sorted(path.parent for path in destination.rglob('setup.py'))
    if not projects:raise ValueError('build_metadata_missing')
    return projects[0]


def probe_get_requires_for_build_wheel(*, package: str, artifact: Path, artifact_store: Path, workspace: Path, builder_image: str) -> dict:
    source_root=workspace/'pep517_metadata'/package
    try:project=_extract_source(artifact,source_root)
    except Exception as exc:return {'status':'BLOCK','blocker':'pep517_source_extraction_failed','package':package,'error':type(exc).__name__}
    try:
        import tomllib
        if (project/'pyproject.toml').is_file():
            pyproject=tomllib.loads((project/'pyproject.toml').read_text(encoding='utf-8'))
            build=pyproject['build-system'];static=list(build.get('requires',[]));backend=str(build['build-backend']);backend_path=list(build.get('backend-path',[]))
        else:
            static=['setuptools'];backend='setuptools.build_meta:__legacy__';backend_path=[]
    except Exception as exc:return {'status':'BLOCK','blocker':'pep517_build_system_parse_failed','package':package,'error':type(exc).__name__}
    script=workspace/f'pep517_probe_{package}.py'
    script.write_text("import json\nfrom pip._vendor.pyproject_hooks import BuildBackendHookCaller\ncaller=BuildBackendHookCaller('/tmp/project',"+repr(backend)+",backend_path="+repr(backend_path)+")\nprint('CONTROLLERGATE_GET_REQUIRES='+json.dumps(caller.get_requires_for_build_wheel({})))\n",encoding='utf-8',newline='\n')
    install=' '.join(shlex.quote(item) for item in static)
    shell=f"cp -a /src /tmp/project && chmod -R u+w /tmp/project && python -m venv /tmp/meta && /tmp/meta/bin/python -m pip install --no-index --find-links=/artifacts {install} && /tmp/meta/bin/python /probe.py"
    command=['docker','run','--rm','--network','none','--read-only','--user','65534:65534','--cap-drop','ALL','--security-opt','no-new-privileges','--pids-limit','128','--memory','2g','--cpus','1','--tmpfs','/tmp:rw,exec,nosuid,size=1g','-v',f'{artifact_store.resolve()}:/artifacts:ro','-v',f'{project.resolve()}:/src:ro','-v',f'{script.resolve()}:/probe.py:ro','-e','HOME=/tmp','--entrypoint','/bin/sh',builder_image,'-c',shell]
    try:run=subprocess.run(command,capture_output=True,text=True,timeout=600)
    except (FileNotFoundError,subprocess.TimeoutExpired) as exc:return {'status':'BLOCK','blocker':'pep517_get_requires_probe_unavailable','package':package,'error':type(exc).__name__}
    marker='CONTROLLERGATE_GET_REQUIRES=';line=next((item for item in run.stdout.splitlines() if item.startswith(marker)),None)
    try:dynamic=json.loads(line[len(marker):]) if line else []
    except Exception:dynamic=[]
    return {'status':'PASS' if run.returncode==0 and line is not None else 'BLOCK','blocker':None if run.returncode==0 and line is not None else 'pep517_get_requires_probe_failed','package':package,'static_build_requirements':static,'dynamic_backend_requirements':dynamic,'system_toolchain_requirements':[],'system_library_requirements':[],'operation_status':'PASS','evidence_source':'bounded_network_none_get_requires_for_build_wheel_capsule','command':command,'returncode':run.returncode,'stdout':run.stdout[-4000:],'stderr':run.stderr[-4000:]}
