from pathlib import Path

from controllergate.runtime.runtime_root_policy import LOCAL_ROOT, validate_runtime_root


ROOT = Path(__file__).resolve().parents[2]


def test_c_root_accepted():
    assert validate_runtime_root(LOCAL_ROOT, repo_root=ROOT, env={})["status"] == "PASS"


def test_e_root_rejected():
    assert validate_runtime_root(r"E:\ControllerGate_Runtime", repo_root=ROOT, env={})["status"] == "BLOCK"


def test_repo_and_incoming_rejected():
    assert validate_runtime_root(ROOT, repo_root=ROOT)["status"] == "BLOCK"
    assert validate_runtime_root(ROOT / "incoming_artifacts", repo_root=ROOT)["status"] == "BLOCK"


def test_synced_folder_rejected():
    assert validate_runtime_root(r"C:\Users\x\OneDrive\ControllerGate_Runtime", repo_root=ROOT, env={})["status"] == "BLOCK"


def test_ci_root():
    env = {"GITHUB_ACTIONS": "true", "RUNNER_TEMP": "/tmp/runner"}
    assert validate_runtime_root("/tmp/runner/controllergate-runtime", repo_root=ROOT, env=env)["status"] == "PASS"
