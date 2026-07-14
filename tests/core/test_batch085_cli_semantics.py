from __future__ import annotations

import json

from controllergate.cli import main


def test_canary_rejection_has_exit_five_and_empty_records_rejected(tmp_path, capsys):
    proof = tmp_path / "proof.json"
    proof.write_text(json.dumps({"records": []}), encoding="utf-8")
    assert main(["canary", "--proof", str(proof)]) == 5


def test_status_requires_authority():
    assert main(["status"]) == 3
