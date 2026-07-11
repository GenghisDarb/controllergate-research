from __future__ import annotations

import json
import subprocess

from packaging.tags import Tag
from packaging.utils import parse_wheel_filename


def wheel_compatibility(filename: str, *, python_tag: str = "cp313", platform: str = "linux_x86_64") -> dict[str, object]:
    if not filename.endswith(".whl"): return {"compatible": False, "reason": "not_wheel", "preference": 99}
    try: _, _, _, tags = parse_wheel_filename(filename)
    except Exception: return {"compatible": False, "reason": "wheel_filename_invalid", "preference": 99}
    for tag in tags:
        if tag.interpreter in {"py3", "py2.py3"} and tag.abi == "none" and tag.platform == "any": return {"compatible": True, "reason": "pure_python_universal", "preference": 1}
        if tag.interpreter in {"py3", "py2.py3"} and tag.abi == "none" and ("x86_64" in tag.platform and ("manylinux" in tag.platform or tag.platform == platform)): return {"compatible": True, "reason": "python_independent_linux_binary", "preference": 2}
        if tag.interpreter == python_tag and tag.platform in {"any", platform, "manylinux_2_17_x86_64", "manylinux2014_x86_64"}: return {"compatible": True, "reason": "target_python_platform", "preference": 2}
        if tag.abi == "abi3" and tag.platform in {platform, "manylinux_2_17_x86_64", "manylinux2014_x86_64"}: return {"compatible": True, "reason": "stable_abi", "preference": 2}
    return {"compatible": False, "reason": "wheel_tag_incompatible", "preference": 99}


def compatible_with_ordered_tags(filename: str, ordered_tags: list[str]) -> dict[str, object]:
    if not filename.endswith(".whl"): return {"compatible": False, "rank": None, "reason": "not_wheel"}
    try: _, _, _, wheel_tags = parse_wheel_filename(filename)
    except Exception: return {"compatible": False, "rank": None, "reason": "wheel_filename_invalid"}
    ranks = {value: index for index, value in enumerate(ordered_tags)}
    matches = sorted((ranks[str(tag)], str(tag)) for tag in wheel_tags if str(tag) in ranks)
    return {"compatible": bool(matches), "rank": matches[0][0] if matches else None, "matched_tag": matches[0][1] if matches else None, "reason": "exact_runtime_sys_tag" if matches else "wheel_tag_incompatible"}


def collect_exact_runtime_tags(image_digest: str) -> dict[str, object]:
    script = "import json,platform,sys; from pip._vendor.packaging.tags import sys_tags; print(json.dumps({'tags':[str(t) for t in sys_tags()],'python':sys.version,'platform':platform.platform(),'machine':platform.machine()}))"
    command=["docker","run","--rm","--network","none","--read-only","--cap-drop","ALL","--security-opt","no-new-privileges","--pids-limit","64","--memory","512m","--cpus","1",image_digest,"python","-c",script]
    try: result=subprocess.run(command,capture_output=True,text=True,timeout=180)
    except (FileNotFoundError,subprocess.TimeoutExpired) as exc: return {"status":"BLOCK","blocker":"exact_runtime_tag_capsule_unavailable","error":type(exc).__name__,"image_digest":image_digest,"command":command,"tags":[]}
    if result.returncode!=0: return {"status":"BLOCK","blocker":"exact_runtime_tag_capsule_failed","stderr":result.stderr[-2000:],"image_digest":image_digest,"command":command,"tags":[]}
    try: value=json.loads(result.stdout.splitlines()[-1])
    except Exception: return {"status":"BLOCK","blocker":"exact_runtime_tag_output_invalid","stdout":result.stdout[-2000:],"tags":[]}
    return {"status":"PASS","image_digest":image_digest,"command":command,"ordered_tag_count":len(value["tags"]),**value}
