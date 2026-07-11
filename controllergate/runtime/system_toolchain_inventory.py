from __future__ import annotations

import json
import subprocess


TOOLS=("cc","c++","ld","cargo","rustc","cmake","ninja","pkg-config")


def inventory(image_digest: str) -> dict:
    script="import json,os,platform,shutil,sys; print(json.dumps({'os_release':open('/etc/os-release').read() if os.path.exists('/etc/os-release') else '', 'architecture':platform.machine(),'libc':platform.libc_ver(),'python':sys.version,'tools':{n:shutil.which(n) for n in " + repr(list(TOOLS)) + "}}))"
    command=["docker","run","--rm","--network","none","--read-only","--cap-drop","ALL","--security-opt","no-new-privileges","--pids-limit","64","--memory","512m","--cpus","1",image_digest,"python","-c",script]
    try:r=subprocess.run(command,capture_output=True,text=True,timeout=180)
    except (FileNotFoundError,subprocess.TimeoutExpired) as exc:return {"status":"BLOCK","blocker":"system_toolchain_inventory_unavailable","error":type(exc).__name__,"tools":{},"command":command}
    if r.returncode:return {"status":"BLOCK","blocker":"system_toolchain_inventory_failed","stderr":r.stderr[-2000:],"tools":{},"command":command}
    value=json.loads(r.stdout.splitlines()[-1]); return {"status":"PASS","image_digest":image_digest,"command":command,**value}
