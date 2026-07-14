from __future__ import annotations

from pathlib import Path

from controllergate.connectors.audit import audit_events, redact
from controllergate.connectors.circuit_breaker import CircuitBreaker
from controllergate.connectors.offline_canary import execute_offline_canary
from controllergate.connectors.read_only import reject_write
from controllergate.deployment.historical_canary import execute_historical_canary


def test_offline_connector_canary_executes_all_failures() -> None:
    result=execute_offline_canary();cases={row["case"] for row in result["events"]}
    assert result["status"]=="EXECUTED_WITH_RESULT"
    assert {"success","timeout","retry","rate_limit","malformed","write","redaction"}<=cases


def test_connector_write_is_rejected_and_secret_redacted() -> None:
    event=reject_write("local");assert event["executed"] is False
    assert audit_events([event])["status"]=="PASS"
    clean,changed=redact("token=private");assert changed and "private" not in clean


def test_circuit_breaker_opens_and_recovers() -> None:
    breaker=CircuitBreaker(2);assert breaker.record(False)=="CLOSED";assert breaker.record(False)=="OPEN";assert breaker.record(True)=="CLOSED"


def test_historical_canary_health_and_rollback(tmp_path: Path) -> None:
    evidence=tmp_path/"evidence.txt";evidence.write_text("proof",encoding="utf-8")
    result=execute_historical_canary("episode",evidence,tmp_path/"runtime")
    assert result["health"]["status"]=="CANARY_HEALTH_WINDOW_PASSED"
    assert result["rollback"]["status"]=="ROLLBACK_DRILL_PASSED" and result["slots_disposed"]
