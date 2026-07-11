from __future__ import annotations

from packaging.markers import default_environment
from packaging.requirements import Requirement

from .historical_metadata import canonicalize_name


TARGET_ENV = {**default_environment(), "python_version": "3.13", "python_full_version": "3.13.0b2", "implementation_name": "cpython", "sys_platform": "linux", "platform_system": "Linux", "os_name": "posix"}


def applicable_requirement(raw: str, extras: set[str] | None = None) -> dict[str, object]:
    req = Requirement(raw); extras = extras or {""}; applies = req.marker is None or any(req.marker.evaluate({**TARGET_ENV, "extra": extra}) for extra in extras)
    return {"applies": applies, "name": canonicalize_name(req.name), "specifier": str(req.specifier), "extras": sorted(req.extras), "marker": str(req.marker) if req.marker else None, "raw": raw}
