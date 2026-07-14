from __future__ import annotations

from controllergate.watch.backoff import record_failure
from controllergate.watch.controller import WatchController


def test_watch_persists_cursor_deduplicates_and_restarts(tmp_path):
    database = tmp_path / "controller-state.sqlite"
    first = WatchController(database).observe("fixture", [{"id": "1"}], "cursor-1")
    assert first["new_events"] == 1 and first["public_writes"] == 0
    second = WatchController(database).observe("fixture", [{"id": "1"}, {"id": "2"}], "cursor-2")
    assert second["new_events"] == 1 and second["duplicates_suppressed"] == 1


def test_watch_circuit_breaker(tmp_path):
    controller = WatchController(tmp_path / "state.sqlite")
    for _ in range(3): result = record_failure(controller.repository.connection, "fixture")
    assert result["circuit_state"] == "OPEN"
    assert controller.observe("fixture", [], None)["blocker"] == "watch_circuit_open"
