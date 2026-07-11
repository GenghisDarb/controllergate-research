from __future__ import annotations

import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import tarfile
import zipfile


RUST_TAG="rust:1.79.0-slim-bookworm"
GCC_TAG="gcc:12.3.0-bookworm"


def _pull_identity(tag: str) -> dict:
    try:
        pull=subprocess.run(["docker","pull",tag],capture_output=True,text=True,timeout=600)
    except FileNotFoundError:
        return {"status":"BLOCK","tag":tag,"blocker":"docker_runtime_unavailable"}
    except subprocess.TimeoutExpired:
        return {"status":"BLOCK","tag":tag,"blocker":"toolchain_image_pull_timeout"}
    if pull.returncode:return {"status":"BLOCK","tag":tag,"blocker":"toolchain_image_pull_failed","stderr":pull.stderr[-3000:]}
    inspect=subprocess.run(["docker","image","inspect",tag,"--format","{{json .RepoDigests}}"],capture_output=True,text=True,timeout=30)
    digests=json.loads(inspect.stdout.strip() or '[]');digest=next((d for d in digests if '@sha256:' in d),None)
    return {"status":"PASS" if digest else "BLOCK","tag":tag,"repo_digest":digest,"image_id":subprocess.run(["docker","image","inspect",tag,"--format","{{.Id}}"],capture_output=True,text=True).stdout.strip()}


def _extract_verified_source(archive: Path, destination: Path) -> Path:
    destination.mkdir(parents=True,exist_ok=True)
    if tarfile.is_tarfile(archive):
        with tarfile.open(archive) as source:
            for member in source.getmembers():
                parts=Path(member.name).parts
                if member.name.startswith(('/', '\\')) or '..' in parts or member.issym() or member.islnk():
                    raise ValueError('unsafe_rust_source_archive')
            source.extractall(destination)
    elif zipfile.is_zipfile(archive):
        with zipfile.ZipFile(archive) as source:
            for name in source.namelist():
                if name.startswith(('/', '\\')) or '..' in Path(name).parts:
                    raise ValueError('unsafe_rust_source_archive')
            source.extractall(destination)
    else:
        raise ValueError('unsupported_rust_source_archive')
    manifests=sorted(destination.rglob('Cargo.toml'))
    locks=sorted(destination.rglob('Cargo.lock'))
    if not manifests or not locks:
        raise ValueError('rust_source_lock_or_manifest_missing')
    lock_parent=locks[0].parent
    return next((item for item in manifests if item.parent==lock_parent),manifests[0])


def _acquire_locked_rust_dependencies(workspace: Path, rust_identity: dict, rust_sdist: Path | None) -> dict:
    if rust_sdist is None:
        return {'status':'BLOCK','blocker':'rpds_source_archive_missing_for_cargo_lock'}
    extracted=workspace/'rpds_rust_source';cache=workspace/'cargo_provider_cache';cache.mkdir(parents=True,exist_ok=True)
    try:manifest=_extract_verified_source(rust_sdist,extracted)
    except Exception as exc:return {'status':'BLOCK','blocker':'rpds_cargo_lock_extraction_failed','error':type(exc).__name__}
    relative=manifest.relative_to(extracted).as_posix()
    command=['docker','run','--rm','--network','bridge','--cap-drop','ALL','--security-opt','no-new-privileges','--pids-limit','256','--memory','3g','--cpus','2','-v',f'{extracted.resolve()}:/src:ro','-v',f'{cache.resolve()}:/cargo:rw','-e','CARGO_HOME=/cargo',rust_identity['repo_digest'],'sh','-lc',f'cargo fetch --locked --manifest-path /src/{relative}']
    try:run=subprocess.run(command,capture_output=True,text=True,timeout=1200)
    except (FileNotFoundError,subprocess.TimeoutExpired) as exc:return {'status':'BLOCK','blocker':'rpds_locked_cargo_provider_acquisition_unavailable','error':type(exc).__name__}
    files=sorted(path for path in cache.rglob('*') if path.is_file());manifest_rows=[{'path':path.relative_to(cache).as_posix(),'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'size':path.stat().st_size} for path in files]
    return {'status':'PASS' if run.returncode==0 and files else 'BLOCK','blocker':None if run.returncode==0 and files else 'rpds_locked_cargo_provider_acquisition_failed','command':command,'network_policy':'bounded_provider_acquisition_only','cargo_lock_sha256':hashlib.sha256(next(extracted.rglob('Cargo.lock')).read_bytes()).hexdigest(),'manifest_path':relative,'cache_path':str(cache),'provider_file_count':len(files),'provider_manifest_hash':hashlib.sha256(json.dumps(manifest_rows,sort_keys=True).encode()).hexdigest(),'stdout':run.stdout[-4000:],'stderr':run.stderr[-4000:]}


def prepare_historical_builder(workspace: Path, python_digest: str, rust_sdist: Path | None = None) -> dict:
    python=_pull_identity(python_digest);rust=_pull_identity(RUST_TAG);gcc=_pull_identity(GCC_TAG)
    if python["status"]!="PASS" or rust["status"]!="PASS" or gcc["status"]!="PASS":return {"status":"BLOCK","blocker":"historical_toolchain_identity_unavailable","python":python,"rust":rust,"gcc":gcc}
    cargo_provider=_acquire_locked_rust_dependencies(workspace,rust,rust_sdist)
    if cargo_provider['status']!='PASS':return {"status":"BLOCK","blocker":cargo_provider['blocker'],"python":python,"rust":rust,"gcc":gcc,"cargo_provider":cargo_provider}
    root=workspace/'historical_builder';root.mkdir(parents=True,exist_ok=True)
    cache_source=Path(cargo_provider['cache_path'])
    for folder in ('registry','git'):
        source=cache_source/folder
        if source.exists():
            target=root/'cargo_provider'/folder
            target.parent.mkdir(parents=True,exist_ok=True)
            shutil.copytree(source,target,dirs_exist_ok=True)
    dockerfile=root/'Dockerfile';dockerfile.write_text(f"FROM {python_digest} AS py\nFROM {rust['repo_digest']} AS rust\nFROM {gcc['repo_digest']}\nCOPY --from=py /usr/local /usr/local\nCOPY --from=rust /usr/local/cargo /usr/local/cargo\nCOPY --from=rust /usr/local/rustup /usr/local/rustup\nCOPY cargo_provider/ /opt/cargo-provider/\nENV PATH=/usr/local/cargo/bin:/usr/local/bin:/usr/bin:/bin\nENV RUSTUP_HOME=/usr/local/rustup\nENV CARGO_HOME=/tmp/cargo\nENV CARGO_NET_OFFLINE=true\n",encoding='utf-8',newline='\n')
    tag='controllergate-batch068h6-builder:local'
    try:
        build=subprocess.run(["docker","build","--network=none","-t",tag,str(root)],capture_output=True,text=True,timeout=900)
    except (FileNotFoundError, subprocess.TimeoutExpired) as exc:
        return {"status":"BLOCK","blocker":"historical_builder_runtime_unavailable","rust":rust,"gcc":gcc,"error":type(exc).__name__}
    if build.returncode:return {"status":"BLOCK","blocker":"historical_builder_image_failed","rust":rust,"gcc":gcc,"stderr":build.stderr[-5000:]}
    identity=subprocess.run(["docker","image","inspect",tag,"--format","{{.Id}}"],capture_output=True,text=True).stdout.strip()
    probe=subprocess.run(["docker","run","--rm","--network","none",tag,"sh","-lc","python --version && rustc --version && cargo --version && cc --version | head -1"],capture_output=True,text=True,timeout=60)
    return {"status":"PASS" if probe.returncode==0 else "BLOCK","blocker":None if probe.returncode==0 else "historical_builder_identity_probe_failed","builder_image":tag,"builder_image_id":identity,"python":python,"rust":rust,"gcc":gcc,"cargo_provider":cargo_provider,"rust_publication_date":"2024-06-13T00:00:00Z","cutoff_compatible":True,"signature_status":"container_registry_digest_verified_signature_not_established","probe_stdout":probe.stdout,"dockerfile_sha256":hashlib.sha256(dockerfile.read_bytes()).hexdigest()}
