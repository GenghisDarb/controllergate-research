from __future__ import annotations

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
