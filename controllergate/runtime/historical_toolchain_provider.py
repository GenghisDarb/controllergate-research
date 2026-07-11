from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import tarfile
import time
import tomllib
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


def inspect_rust_image(image: str) -> dict:
    fields={}
    for name,template in (("config_env","{{json .Config.Env}}"),("entrypoint","{{json .Config.Entrypoint}}"),("cmd","{{json .Config.Cmd}}")):
        run=subprocess.run(["docker","image","inspect",image,"--format",template],capture_output=True,text=True,timeout=30)
        try:fields[name]=json.loads(run.stdout.strip() or 'null')
        except Exception:fields[name]=run.stdout.strip()
    probe="id; printf 'PATH=%s\\n' \"$PATH\"; printf 'CARGO_HOME=%s\\n' \"$CARGO_HOME\"; printf 'RUSTUP_HOME=%s\\n' \"$RUSTUP_HOME\"; command -v cargo || true; command -v rustc || true; ls -la /usr/local/cargo/bin || true; ls -la /usr/local/rustup || true; /usr/local/cargo/bin/cargo --version || true; /usr/local/cargo/bin/rustc --version || true; rustc --version || true"
    outputs={}
    for mode,args in (("non_login",["-c",probe]),("login",["-lc",probe])):
        run=subprocess.run(["docker","run","--rm","--network","none","--entrypoint","/bin/sh",image,*args],capture_output=True,text=True,timeout=60);outputs[mode]={"returncode":run.returncode,"stdout":run.stdout,"stderr":run.stderr,"output_hash":hashlib.sha256((run.stdout+run.stderr).encode()).hexdigest()}
    non=outputs["non_login"]["stdout"];login=outputs["login"]["stdout"]
    binary="/usr/local/cargo/bin/cargo" if "cargo 1.79" in non else None
    classification="cargo_binary_present_path_reset_by_login_shell" if binary and "cargo 1.79" not in login else "cargo_binary_present_nonstandard_path" if binary else "cargo_binary_missing_from_selected_image"
    return {"status":"PASS" if binary else "BLOCK","image":image,**fields,"probes":outputs,"cargo_binary_path":binary,"login_shell_path_changed":next((line for line in non.splitlines() if line.startswith('PATH=')),None)!=next((line for line in login.splitlines() if line.startswith('PATH=')),None),"classification":classification}


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
    relative=manifest.relative_to(extracted).as_posix();lock_path=next(extracted.rglob('Cargo.lock'));lock_data=tomllib.loads(lock_path.read_text(encoding='utf-8'));packages=list(lock_data.get('package',[]))
    inspection=inspect_rust_image(rust_identity['repo_digest'])
    if inspection['status']!='PASS':return {'status':'BLOCK','blocker':'cargo_binary_not_discovered_after_absolute_path_probe','rust_image_inspection':inspection}
    explicit_path='/usr/local/cargo/bin:/usr/local/rustup/bin:/usr/local/bin:/usr/bin:/bin'
    command=['docker','run','--rm','--network','bridge','--entrypoint','/bin/sh','--cap-drop','ALL','--security-opt','no-new-privileges','--pids-limit','256','--memory','3g','--cpus','2','-v',f'{extracted.resolve()}:/src:ro','-v',f'{cache.resolve()}:/cargo-cache:rw','-e',f'PATH={explicit_path}','-e','CARGO_HOME=/cargo-cache','-e','RUSTUP_HOME=/usr/local/rustup','-e','CARGO_REGISTRIES_CRATES_IO_PROTOCOL=sparse',rust_identity['repo_digest'],'-c',f'/usr/local/cargo/bin/cargo fetch -vv --locked --manifest-path /src/{relative}']
    started=time.monotonic()
    try:run=subprocess.run(command,capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=1200)
    except (FileNotFoundError,subprocess.TimeoutExpired) as exc:return {'status':'BLOCK','blocker':'rpds_locked_cargo_provider_acquisition_unavailable','error':type(exc).__name__}
    cache_transport='host_bind_mount'
    # Docker Desktop cannot always apply crate archive mtimes to an NTFS bind
    # mount. Retry only that observed transport failure in a Docker-managed
    # volume, then export the locked cache for the same byte-level checks.
    mtime_transport_failure=run.returncode!=0 and 'failed to set mtime' in run.stderr and 'Invalid argument' in run.stderr
    if mtime_transport_failure:
        shutil.rmtree(cache,ignore_errors=True);cache.mkdir(parents=True,exist_ok=True)
        volume='controllergate-cargo-'+re.sub(r'[^a-z0-9-]','-',workspace.name.lower())[:36]
        create=subprocess.run(['docker','volume','create',volume],capture_output=True,text=True,timeout=30)
        if create.returncode==0:
            volume_command=list(command);mount_index=volume_command.index('-v',volume_command.index('-v')+1)+1;volume_command[mount_index]=f'{volume}:/cargo-cache:rw'
            retry=subprocess.run(volume_command,capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=1200)
            export_archive=workspace/'cargo_provider_cache_export.tar'
            export=subprocess.run(['docker','run','--rm','--network','none','--entrypoint','/bin/tar','-v',f'{volume}:/cargo-cache:ro',rust_identity['repo_digest'],'-C','/cargo-cache','-cf','-','.'],capture_output=True,timeout=300)
            subprocess.run(['docker','volume','rm','-f',volume],capture_output=True,text=True,timeout=30)
            if retry.returncode==0 and export.returncode==0:
                export_archive.write_bytes(export.stdout)
                try:
                    with tarfile.open(export_archive) as source:
                        for member in source.getmembers():
                            if member.name.startswith(('/', '\\')) or '..' in Path(member.name).parts or member.issym() or member.islnk():
                                raise ValueError('unsafe_cargo_provider_export')
                        source.extractall(cache)
                    run=retry;command=volume_command;cache_transport='docker_managed_volume_export'
                finally:
                    export_archive.unlink(missing_ok=True)
    files=sorted(path for path in cache.rglob('*') if path.is_file());manifest_rows=[{'path':path.relative_to(cache).as_posix(),'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'size':path.stat().st_size} for path in files]
    package_catalog=[{'name':item.get('name'),'version':item.get('version'),'source':item.get('source'),'checksum':item.get('checksum')} for item in packages]
    crate_verification=[]
    for path in files:
        if path.suffix!='.crate':continue
        digest=hashlib.sha256(path.read_bytes()).hexdigest();match=next((item for item in packages if path.name==f"{item.get('name')}-{item.get('version')}.crate"),None);crate_verification.append({'filename':path.name,'sha256':digest,'lock_checksum':match.get('checksum') if match else None,'status':'PASS' if match and match.get('checksum')==digest else 'BLOCK'})
    git_dependencies=[{'name':item.get('name'),'version':item.get('version'),'source':item.get('source'),'revision':str(item.get('source')).rsplit('#',1)[-1]} for item in packages if str(item.get('source','')).startswith('git+')]
    checksums_pass=all(item['status']=='PASS' for item in crate_verification) and bool(crate_verification)
    provider_hash=hashlib.sha256(json.dumps(manifest_rows,sort_keys=True).encode()).hexdigest()
    status='PASS' if run.returncode==0 and files and checksums_pass else 'BLOCK'
    return {'status':status,'blocker':None if status=='PASS' else 'rpds_locked_cargo_provider_acquisition_failed','command':command,'cache_transport':cache_transport,'explicit_cargo_binary':'/usr/local/cargo/bin/cargo','explicit_path':explicit_path,'network_policy':'bounded_provider_acquisition_only','network_destinations':['https://index.crates.io','https://static.crates.io','https://crates.io',*[item['source'] for item in git_dependencies]],'cargo_lock_sha256':hashlib.sha256(lock_path.read_bytes()).hexdigest(),'cargo_toml_sha256':hashlib.sha256(manifest.read_bytes()).hexdigest(),'manifest_path':relative,'cache_path':str(cache),'provider_file_count':len(files),'provider_manifest':manifest_rows,'provider_manifest_hash':provider_hash,'package_catalog':package_catalog,'crate_verification':crate_verification,'git_dependency_verification':git_dependencies,'registry_index_identity':hashlib.sha256(''.join(row['sha256'] for row in manifest_rows if 'index' in row['path']).encode()).hexdigest(),'rust_image_inspection':inspection,'returncode':run.returncode,'elapsed_seconds':round(time.monotonic()-started,3),'stdout':run.stdout,'stderr':run.stderr,'registry_protocol':'sparse'}


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
    tag='controllergate-batch068h7-builder:local'
    try:
        build=subprocess.run(["docker","build","--network=none","-t",tag,str(root)],capture_output=True,text=True,timeout=900)
    except (FileNotFoundError, subprocess.TimeoutExpired) as exc:
        return {"status":"BLOCK","blocker":"historical_builder_runtime_unavailable","rust":rust,"gcc":gcc,"error":type(exc).__name__}
    if build.returncode:return {"status":"BLOCK","blocker":"historical_builder_image_failed","rust":rust,"gcc":gcc,"stderr":build.stderr[-5000:]}
    identity=subprocess.run(["docker","image","inspect",tag,"--format","{{.Id}}"],capture_output=True,text=True).stdout.strip()
    metadata_manifest=cargo_provider['manifest_path'];source_root=workspace/'rpds_rust_source';probe_script=f"mkdir -p /tmp/cargo && cp -a /opt/cargo-provider/. /tmp/cargo/; python --version; pip --version; cc --version | head -1; /usr/local/cargo/bin/rustc --version; /usr/local/cargo/bin/cargo --version; /usr/local/cargo/bin/cargo metadata --locked --offline --manifest-path /src/{metadata_manifest} --format-version 1 >/tmp/metadata.json"
    probe=subprocess.run(["docker","run","--rm","--network","none","--read-only","--user","65534:65534","--cap-drop","ALL","--security-opt","no-new-privileges","--tmpfs","/tmp:rw,exec,nosuid,size=1g","-v",f"{source_root.resolve()}:/src:ro","-e","PATH=/usr/local/cargo/bin:/usr/local/rustup/bin:/usr/local/bin:/usr/bin:/bin","-e","CARGO_HOME=/tmp/cargo","-e","RUSTUP_HOME=/usr/local/rustup","-e","CARGO_NET_OFFLINE=true","--entrypoint","/bin/sh",tag,"-c",probe_script],capture_output=True,text=True,timeout=120)
    return {"status":"PASS" if probe.returncode==0 else "BLOCK","blocker":None if probe.returncode==0 else "historical_builder_identity_probe_failed","builder_image":tag,"builder_image_id":identity,"python":python,"rust":rust,"gcc":gcc,"cargo_provider":cargo_provider,"rust_publication_date":"2024-06-13T00:00:00Z","cutoff_compatible":True,"exact_historical_status":"cutoff_compatible_toolchain_current_container","signature_status":"container_registry_digest_verified_signature_not_established","probe_stdout":probe.stdout,"probe_stderr":probe.stderr[-4000:],"offline_cargo_metadata_pass":probe.returncode==0,"dockerfile_sha256":hashlib.sha256(dockerfile.read_bytes()).hexdigest()}
