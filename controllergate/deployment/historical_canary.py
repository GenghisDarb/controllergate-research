from __future__ import annotations

import hashlib
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

from .canary_slot import materialize_slot
from .deployment_proof import seal_deployment
from .health_contract import HealthContract
from .health_monitor import monitor
from .rollback_controller import rollback
from .traffic_replay import replay


def execute_historical_canary(episode_id: str, evidence_file: Path, runtime_root: Path) -> dict[str, Any]:
    source = runtime_root / episode_id / "source"; source.mkdir(parents=True, exist_ok=True)
    target = source / evidence_file.name; shutil.copy2(evidence_file, target); original = target.read_bytes(); original_hash = hashlib.sha256(original).hexdigest()
    canary = materialize_slot(source, runtime_root / episode_id / "canary")
    comparison = materialize_slot(source, runtime_root / episode_id / "comparison")
    command = [sys.executable, "-c", f"import hashlib,pathlib,sys; p=pathlib.Path({evidence_file.name!r}); sys.exit(0 if hashlib.sha256(p.read_bytes()).hexdigest()=={original_hash!r} else 1)"]
    canary_run = replay(command, Path(canary["slot"])); comparison_run = replay(command, Path(comparison["slot"]))
    health = monitor([canary_run, comparison_run], HealthContract(0, minimum_events=2))
    target.write_bytes(original + b"\nrollback-drill")
    rollback_result = rollback(target, original, original_hash)
    disposed = []
    for path in [Path(canary["slot"]), Path(comparison["slot"])]: shutil.rmtree(path); disposed.append(not path.exists())
    proof = seal_deployment([canary_run, comparison_run, health, rollback_result])
    return {"episode_id":episode_id,"repair_count_changed":False,"production_traffic":False,"credentials_used":False,
            "source_identity":original_hash,"canary":canary,"comparison":comparison,"replays":[canary_run,comparison_run],
            "health":health,"rollback":rollback_result,"slots_disposed":all(disposed),"deployment_proof":proof}
