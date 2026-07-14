from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
from pathlib import Path, PurePosixPath
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
BATCH = "post_v2_37_hardening_batch084_real_amds_canary_product_beta"
EXPECTED_PROVIDER_ARTIFACTS = {
    "8299791481": {
        "name": "batch083_openbb_linux_py311_complete_provider",
        "size": 199_813_732,
        "sha256": "256b55be636fe24d791a2cd0051b7d13aa776f6bf2e7410ce4cb64cc854f778d",
    },
    "8299749040": {
        "name": "batch083_openbb_rooted_openapi_reference_closure",
        "size": 136_807,
        "sha256": "a2a6659649d631f6d6da4dc171a1b0054f6876b82fd3501b5c4375ddd653001b",
    },
    "8299757219": {
        "name": "batch083_poetry_windows_py313_complete_provider",
        "size": 11_685_454,
        "sha256": "a081efda39609bae3285adbfbdc209131d415a950fdae0ab352dd69ac7dc3124",
    },
}


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def write_json(path: Path, value: Any) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    return path


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(row, sort_keys=True) + "\n" for row in rows), encoding="utf-8", newline="\n")
    return path


def run(command: list[str], *, cwd: Path | None = None, timeout: int = 600, env: dict[str, str] | None = None) -> dict[str, Any]:
    result = subprocess.run(command, cwd=cwd, text=True, capture_output=True, timeout=timeout, env=env, check=False)
    raw = (result.stdout + result.stderr).encode("utf-8", errors="replace")
    return {
        "command": command,
        "cwd": str(cwd) if cwd else None,
        "returncode": result.returncode,
        "log_sha256": sha256_bytes(raw),
        "log_tail": raw.decode("utf-8", errors="replace")[-5000:],
    }


def copy_tree_contents(source: Path, destination: Path) -> None:
    destination.mkdir(parents=True, exist_ok=True)
    for item in source.iterdir():
        target = destination / item.name
        if item.is_dir():
            if target.exists():
                shutil.rmtree(target)
            shutil.copytree(item, target)
        else:
            shutil.copy2(item, target)


def safe_relative_zip_path(value: str) -> bool:
    path = PurePosixPath(value.replace("\\", "/"))
    return not path.is_absolute() and ".." not in path.parts and not (path.parts and ":" in path.parts[0])


def manifest(out: Path) -> dict[str, str]:
    rows: dict[str, str] = {}
    for path in sorted(item for item in out.rglob("*") if item.is_file() and item.name not in {"SHA256SUMS.txt", "ARTIFACT_SHA256SUMS.txt"}):
        rows[path.relative_to(out).as_posix()] = sha256_file(path)
    (out / "SHA256SUMS.txt").write_text("".join(f"{digest}  {name}\n" for name, digest in rows.items()), encoding="utf-8", newline="\n")
    return rows
