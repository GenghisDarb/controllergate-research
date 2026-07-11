from __future__ import annotations


def classify_build_failure(stderr: str, returncode: int) -> dict:
    text=stderr.lower()
    rules=[("rust",("cargo","rustc","rust compiler")),("cmake",("cmake",)),("ninja",("ninja",)),("pkg_config",("pkg-config","pkg_config")),("C_compiler",("gcc","cc compiler","c compiler","unable to execute 'gcc'")),("Python_headers",("python.h",)),("unsupported_Python_3_13_beta",("unsupported python","python 3.13")),("resource_limit",("killed","out of memory"))]
    matches=[name for name,patterns in rules if any(p in text for p in patterns)]
    return {"status":"PASS" if returncode==0 else "BLOCK","matched_failure_families":matches or ([] if returncode==0 else ["build_backend_or_package_failure"]),"returncode":returncode}
