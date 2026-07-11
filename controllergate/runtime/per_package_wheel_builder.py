from __future__ import annotations

import hashlib
from pathlib import Path
import subprocess
import time

from .build_provider_resolver import classify_build_failure


def build_one(*, package: str, version: str, artifact: Path, artifact_store: Path, output_dir: Path, image_digest: str, timeout: int = 600) -> dict:
    output_dir.mkdir(parents=True,exist_ok=True); output_dir.chmod(0o777); before={p.name for p in output_dir.glob('*')}; start=time.monotonic()
    command=["docker","run","--rm","--network","none","--read-only","--user","65534:65534","--cap-drop","ALL","--security-opt","no-new-privileges","--pids-limit","256","--memory","3g","--cpus","2","--tmpfs","/tmp:rw,nosuid,size=2g","-v",f"{artifact_store.resolve()}:/artifacts:ro","-v",f"{output_dir.resolve()}:/built:rw","-e","HOME=/tmp",image_digest,"sh","-lc",f"python -m pip wheel --no-index --find-links=/artifacts --no-deps --wheel-dir=/built /artifacts/{artifact.name}"]
    try:r=subprocess.run(command,capture_output=True,text=True,timeout=timeout)
    except FileNotFoundError as exc:return {"status":"BLOCK","blocker":"docker_runtime_unavailable","package":package,"version":version,"command":command,"error":type(exc).__name__,"elapsed_seconds":time.monotonic()-start}
    except subprocess.TimeoutExpired as exc:return {"status":"BLOCK","blocker":"build_timeout","package":package,"version":version,"command":command,"stdout":str(exc.stdout or '')[-8000:],"stderr":str(exc.stderr or '')[-8000:],"elapsed_seconds":time.monotonic()-start}
    produced=sorted(p for p in output_dir.glob('*.whl') if p.name not in before); classification=classify_build_failure(r.stderr,r.returncode)
    return {"status":"PASS" if r.returncode==0 and len(produced)==1 else "BLOCK","blocker":None if r.returncode==0 and len(produced)==1 else ("wheel_output_ambiguous" if r.returncode==0 else "single_package_wheel_build_failed"),"package":package,"version":version,"artifact_sha256":hashlib.sha256(artifact.read_bytes()).hexdigest(),"command":command,"returncode":r.returncode,"elapsed_seconds":round(time.monotonic()-start,3),"stdout":r.stdout[-16000:],"stderr":r.stderr[-16000:],"stdout_sha256":hashlib.sha256(r.stdout.encode()).hexdigest(),"stderr_sha256":hashlib.sha256(r.stderr.encode()).hexdigest(),"network_policy":"none","source_read_only":True,"produced_wheels":[str(p) for p in produced],"failure_classification":classification}
