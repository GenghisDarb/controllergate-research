from __future__ import annotations

import hashlib
from pathlib import Path
import re
import shutil
import shlex
import subprocess
import tarfile
import time

from .build_provider_resolver import classify_build_failure


def build_one(*, package: str, version: str, artifact: Path, artifact_store: Path, output_dir: Path, image_digest: str, timeout: int = 600, provider_requirements: list[str] | None = None, build_environment: dict[str,str] | None = None) -> dict:
    shutil.rmtree(output_dir,ignore_errors=True);output_dir.mkdir(parents=True,exist_ok=True);output_dir.chmod(0o777);before=set();start=time.monotonic()
    requirements=' '.join(shlex.quote(item) for item in (provider_requirements or []));install=(f'/tmp/build/bin/python -m pip install --no-index --find-links=/artifacts {requirements} && ' if requirements else '')
    script=f"mkdir -p /tmp/cargo; if [ -f /opt/cargo-config.toml ]; then cp /opt/cargo-config.toml /tmp/cargo/config.toml; elif [ -d /opt/cargo-provider ]; then cp -a /opt/cargo-provider/. /tmp/cargo/; fi; python -m venv /tmp/build && {install}export PATH=/tmp/build/bin:$PATH && /tmp/build/bin/python -m pip wheel --no-build-isolation --no-index --find-links=/artifacts --no-deps --wheel-dir=/built /artifacts/{artifact.name}"
    environment=[]
    for key,value in sorted((build_environment or {}).items()):environment.extend(['-e',f'{key}={value}'])
    command=["docker","run","--rm","--network","none","--read-only","--user","65534:65534","--cap-drop","ALL","--security-opt","no-new-privileges","--pids-limit","256","--memory","3g","--cpus","2","--tmpfs","/tmp:rw,exec,nosuid,size=2g","-v",f"{artifact_store.resolve()}:/artifacts:ro","-v",f"{output_dir.resolve()}:/built:rw","-e","HOME=/tmp","-e","PATH=/usr/local/cargo/bin:/usr/local/rustup/bin:/usr/local/bin:/usr/bin:/bin","-e","CARGO_HOME=/tmp/cargo","-e","RUSTUP_HOME=/usr/local/rustup","-e","CARGO_NET_OFFLINE=true",*environment,"--entrypoint","/bin/sh",image_digest,"-c",script]
    try:r=subprocess.run(command,capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=timeout)
    except FileNotFoundError as exc:return {"status":"BLOCK","blocker":"docker_runtime_unavailable","package":package,"version":version,"command":command,"error":type(exc).__name__,"elapsed_seconds":time.monotonic()-start}
    except subprocess.TimeoutExpired as exc:return {"status":"BLOCK","blocker":"build_timeout","package":package,"version":version,"command":command,"stdout":str(exc.stdout or '')[-8000:],"stderr":str(exc.stderr or '')[-8000:],"elapsed_seconds":time.monotonic()-start}
    output_transport='host_bind_mount'
    bind_boundary=r.returncode!=0 and "Operation not permitted: '/built/" in r.stderr and 'Successfully built' in r.stdout
    if bind_boundary:
        shutil.rmtree(output_dir,ignore_errors=True);output_dir.mkdir(parents=True,exist_ok=True)
        volume='controllergate-wheel-'+re.sub(r'[^a-z0-9-]','-',f'{package}-{output_dir.parent.name}'.lower())[:40]
        create=subprocess.run(['docker','volume','create',volume],capture_output=True,text=True,timeout=30)
        if create.returncode==0:
            initialize=subprocess.run(['docker','run','--rm','--network','none','--entrypoint','/bin/sh','-v',f'{volume}:/built:rw',image_digest,'-c','chmod 0777 /built'],capture_output=True,text=True,timeout=30)
            retry_command=list(command);mount_index=retry_command.index('-v',retry_command.index('-v')+1)+1;retry_command[mount_index]=f'{volume}:/built:rw'
            retry=subprocess.run(retry_command,capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=timeout) if initialize.returncode==0 else initialize
            export=subprocess.run(['docker','run','--rm','--network','none','--entrypoint','/bin/tar','-v',f'{volume}:/built:ro',image_digest,'-C','/built','-cf','-','.'],capture_output=True,timeout=300)
            subprocess.run(['docker','volume','rm','-f',volume],capture_output=True,text=True,timeout=30)
            if retry.returncode==0 and export.returncode==0:
                archive=output_dir.parent/f'{output_dir.name}-wheel-export.tar';archive.write_bytes(export.stdout)
                try:
                    with tarfile.open(archive) as source:
                        for member in source.getmembers():
                            if member.name.startswith(('/', '\\')) or '..' in Path(member.name).parts or member.issym() or member.islnk():raise ValueError('unsafe_wheel_export')
                        source.extractall(output_dir)
                    r=retry;command=retry_command;output_transport='docker_managed_volume_export'
                finally:archive.unlink(missing_ok=True)
    produced=sorted(p for p in output_dir.glob('*.whl') if p.name not in before); classification=classify_build_failure(r.stderr,r.returncode)
    return {"status":"PASS" if r.returncode==0 and len(produced)==1 else "BLOCK","blocker":None if r.returncode==0 and len(produced)==1 else ("wheel_output_ambiguous" if r.returncode==0 else "single_package_wheel_build_failed"),"package":package,"version":version,"artifact_sha256":hashlib.sha256(artifact.read_bytes()).hexdigest(),"command":command,"returncode":r.returncode,"elapsed_seconds":round(time.monotonic()-start,3),"stdout":r.stdout[-16000:],"stderr":r.stderr[-16000:],"stdout_sha256":hashlib.sha256(r.stdout.encode()).hexdigest(),"stderr_sha256":hashlib.sha256(r.stderr.encode()).hexdigest(),"network_policy":"none","source_read_only":True,"provider_requirements":list(provider_requirements or []),"build_environment":dict(build_environment or {}),"output_transport":output_transport,"produced_wheels":[str(p) for p in produced],"failure_classification":classification}
