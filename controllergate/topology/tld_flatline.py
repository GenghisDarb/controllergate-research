from __future__ import annotations

import math


def flatline_diagnostics(rms_by_n: dict[int, float]) -> dict[str, object]:
    finite = [value for value in rms_by_n.values() if math.isfinite(value)]
    return {"finite_count": len(finite), "nonfinite_count": len(rms_by_n) - len(finite), "flatline": bool(finite) and max(finite) - min(finite) <= 1e-15, "numerical_overflow": any(math.isinf(value) for value in rms_by_n.values())}
