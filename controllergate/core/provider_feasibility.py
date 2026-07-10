from __future__ import annotations

from typing import Any


COMPILED_MARKERS = ("cython", "numpy", "scipy", "gcc", "clang", "rust", "maturin", "cmake", "meson")
SERVICE_MARKERS = ("postgres", "mysql", "redis", "docker", "kafka", "mongodb")
NETWORK_MODEL_MARKERS = ("download", "huggingface", "torch", "tensorflow", "model")
PLATFORM_MARKERS = ("win32", "windows", "darwin", "macos", "linux-only")


def classify_provider_feasibility(metadata_text: str, metadata_paths: list[str]) -> dict[str, Any]:
    text = metadata_text.lower()
    compiled = sorted({marker for marker in COMPILED_MARKERS if marker in text})
    services = sorted({marker for marker in SERVICE_MARKERS if marker in text})
    network = sorted({marker for marker in NETWORK_MODEL_MARKERS if marker in text})
    platforms = sorted({marker for marker in PLATFORM_MARKERS if marker in text})
    if services:
        classification = "external_service_required_static"
    elif network:
        classification = "network_or_model_dependency_static"
    elif compiled:
        classification = "compiled_or_system_dependency_static"
    elif metadata_paths:
        classification = "bounded_python_provider_surface_static"
    else:
        classification = "provider_metadata_missing"
    return {
        "status": "PASS" if metadata_paths else "BLOCK",
        "classification": classification,
        "declared_dependencies": sorted(set(compiled + services + network)),
        "compiled_system_dependency_indicators": compiled,
        "external_service_indicators": services,
        "network_model_indicators": network,
        "platform_restrictions": platforms,
        "provider_probe_executed": False,
    }
