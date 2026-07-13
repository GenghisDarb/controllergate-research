from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from controllergate.runtime.runtime_root_policy import LOCAL_ROOT, validate_runtime_root


def main() -> int:
    repo = Path.cwd()
    accepted = validate_runtime_root(LOCAL_ROOT, repo_root=repo)["status"] == "PASS"
    e_rejected = validate_runtime_root(r"E:\ControllerGate_Runtime", repo_root=repo)["status"] == "BLOCK"
    repo_rejected = validate_runtime_root(repo, repo_root=repo)["status"] == "BLOCK"
    incoming_rejected = validate_runtime_root(repo / "incoming_artifacts", repo_root=repo)["status"] == "BLOCK"
    passed = all((accepted, e_rejected, repo_rejected, incoming_rejected))
    print("runtime root policy:", "PASS" if passed else "FAIL")
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
