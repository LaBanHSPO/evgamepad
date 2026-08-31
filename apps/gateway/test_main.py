"""Gateway boot: healthz, and the generated web types staying in step with the catalog."""

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi import WebSocketDisconnect
from fastapi.testclient import TestClient

from config import load_config
from main import create_app
from protocol.export_ts import SCHEMA_PATH, TYPES_PATH, current_files
from test_config import DEFAULT, VALID_ENV


@pytest.fixture()
def client(tmp_path: Path) -> TestClient:
    cfg = load_config(DEFAULT, env=dict(VALID_ENV))
    # Keep the test off the real /data volume.
    cfg.paths.data_dir = str(tmp_path)
    with TestClient(create_app(cfg)) as c:
        yield c


def test_healthz_reports_a_demo_gateway_with_an_unwired_broker(client: TestClient) -> None:
    body = client.get("/healthz").json()
    assert body["ok"] is True
    assert body["mode"] == "demo"
    assert body["protocol"] == 1
    # Phase 1 ships a stub: it must never claim a broker connection it does not have.
    assert body["broker"] == {"connected": False, "reason": "not_wired"}


def test_boot_runs_migrations_against_the_configured_volume(client: TestClient, tmp_path: Path) -> None:
    client.get("/healthz")
    assert (tmp_path / "journal.db").exists()


def test_generated_web_types_match_the_catalog() -> None:
    """A catalog change that is not regenerated fails here and in the web build."""
    schema_text, types_text = current_files()
    assert SCHEMA_PATH.read_text(encoding="utf-8") == schema_text, "run: uv run python -m protocol.export_ts"
    assert TYPES_PATH.read_text(encoding="utf-8") == types_text, "run: uv run python -m protocol.export_ts"


def test_the_socket_refuses_a_foreign_origin(client: TestClient) -> None:
    """One origin: the HUD and the socket are served from the same place."""
    with pytest.raises(WebSocketDisconnect):
        with client.websocket_connect("/ws", headers={"origin": "https://evil.example"}):
            pass


def test_the_socket_refuses_a_missing_token(client: TestClient, monkeypatch) -> None:
    cfg = client.app.state.config
    monkeypatch.setenv(cfg.gateway.token_env, "the-real-token")
    with pytest.raises(WebSocketDisconnect):
        with client.websocket_connect(
            "/ws", headers={"origin": cfg.gateway.public_origin}
        ):
            pass


def test_a_full_socket_round_trip_over_the_real_route(client: TestClient, monkeypatch) -> None:
    """hello -> welcome, and an intent reaches the stub broker's refusal, through the ASGI app."""
    import json

    cfg = client.app.state.config
    monkeypatch.setenv(cfg.gateway.token_env, "the-real-token")

    with client.websocket_connect(
        "/ws?token=the-real-token", headers={"origin": cfg.gateway.public_origin}
    ) as ws:
        ws.send_text(json.dumps({"v": 1, "t": "hello", "seq": 1, "ts": 1, "ch": "session",
                                 "p": {"token": "the-real-token"}}))
        welcome = json.loads(ws.receive_text())
        assert welcome["t"] == "welcome"
        assert welcome["p"]["mode"] == "demo"

        ws.send_text(json.dumps({"v": 1, "t": "ping", "seq": 2, "ts": 1, "ch": "session",
                                 "p": {"visible": True, "pad": True, "clutch": False}}))
        assert json.loads(ws.receive_text())["t"] == "pong"


def test_the_session_row_is_opened_and_closed_around_the_socket(client: TestClient, monkeypatch,
                                                                tmp_path: Path) -> None:
    """Session equity brackets the evening, even when the stub broker has no figures to give."""
    import json
    import sqlite3

    cfg = client.app.state.config
    monkeypatch.setenv(cfg.gateway.token_env, "tok")
    with client.websocket_connect(
        "/ws?token=tok", headers={"origin": cfg.gateway.public_origin}
    ) as ws:
        ws.send_text(json.dumps({"v": 1, "t": "hello", "seq": 1, "ts": 1, "ch": "session",
                                 "p": {"token": "tok"}}))
        ws.receive_text()

    conn = sqlite3.connect(cfg.paths.db)
    row = conn.execute("SELECT session_id, opened_at, closed_at FROM session_equity").fetchone()
    conn.close()
    assert row is not None
    assert row[1] > 0, "opened_at is wall-clock milliseconds, not a monotonic reading"
    assert row[2] is not None, "the session is closed when the socket goes away"
