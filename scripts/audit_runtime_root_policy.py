from __future__ import annotations

import sys
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from controllergate.runtime.runtime_root_policy import LOCAL_ROOT, validate_runtime_root


def main() -> int:
    repo = Path.cwd()
    if os.environ.get("GITHUB_ACTIONS", "").lower() == "true":
        runtime = Path(os.environ["RUNNER_TEMP"]) / "controllergate-runtime"
        accepted = validate_runtime_root(runtime, repo_root=repo)["status"] == "PASS"
    else:
        accepted = validate_runtime_root(LOCAL_ROOT, repo_root=repo, env={})["status"] == "PASS"
    e_rejected = validate_runtime_root(r"E:\ControllerGate_Runtime", repo_root=repo, env={})["status"] == "BLOCK"
    repo_rejected = validate_runtime_root(repo, repo_root=repo)["status"] == "BLOCK"
    incoming_rejected = validate_runtime_root(repo / "incoming_artifacts", repo_root=repo)["status"] == "BLOCK"
    passed = all((accepted, e_rejected, repo_rejected, incoming_rejected))
    print("runtime root policy:", "PASS" if passed else "FAIL")
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
