from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from controllergate.evidence.provider_parity import contract_for_candidate, load_provider_contracts, verify_provider_observation


PROBE = r'''import json,platform,sys,sysconfig
print(json.dumps({
  "implementation": sys.implementation.name,
  "python_version": platform.python_version(),
  "cache_tag": sys.implementation.cache_tag,
  "soabi": sysconfig.get_config_var("SOABI"),
  "platform_tag": sysconfig.get_platform(),
  "os_family": platform.system().lower(),
  "architecture": platform.machine().lower(),
  "libc_identity": " ".join(platform.libc_ver()).strip(),
  "kernel_identity": " ".join((platform.system(), platform.release(), platform.version())).strip(),
  "executable": sys.executable,
}, sort_keys=True))'''


def abi_tag(observation: dict[str, object]) -> str:
    cache_tag = str(observation.get("cache_tag") or "")
    soabi = str(observation.get("soabi") or "")
    if cache_tag == "cpython-37" and soabi.startswith("cpython-37m"):
        return "cp37m"
    if cache_tag.startswith("cpython-"):
        digits = cache_tag.removeprefix("cpython-").replace(".", "")
        if digits.isdigit() and soabi.startswith(f"cpython-{digits}"):
            return f"cp{digits}"
    return "unresolved"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--candidate", required=True)
    parser.add_argument("--python", required=True)
    parser.add_argument("--contracts", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    contracts = load_provider_contracts(args.contracts)
    contract = contract_for_candidate(contracts, args.candidate)
    completed = subprocess.run([args.python, "-c", PROBE], check=False, capture_output=True, text=True)
    if completed.returncode:
        observation = {"provider_probe_return_code": completed.returncode, "provider_probe_stderr": completed.stderr}
    else:
        observation = json.loads(completed.stdout)
    observation.update(
        {
            "abi_tag": abi_tag(observation),
            "runner_image": "ubuntu-22.04" if os.environ.get("ImageOS") == "ubuntu22" and os.environ.get("RUNNER_OS") == "Linux" else os.environ.get("ImageOS"),
            "runner_image_version": "22.04" if os.environ.get("ImageOS") == "ubuntu22" else os.environ.get("ImageOS"),
            "runner_build_version": os.environ.get("ImageVersion"),
            "source_commit": contract["source_commit"],
            "dependency_graph_hash": contract["dependency_graph_hash"],
            "runner_identity": "github-actions-ubuntu-22.04-x64" if os.environ.get("ImageOS") == "ubuntu22" else "unverified-runner",
            "harness_identity": contract["harness_identity"],
            "command_identity": contract["command_identity"],
        }
    )
    result = verify_provider_observation(contract, observation)
    result["observation"] = observation
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({"candidate_id": args.candidate, "status": result["status"], "failures": result["failures"]}, sort_keys=True))
    return 0 if result["status"] == "PASS_EXACT_FROZEN_LINUX_PARITY" else 1


if __name__ == "__main__":
    raise SystemExit(main())
