"""Phase 3's own tables: pad telemetry and the session check-in."""

from __future__ import annotations

import json

import pytest
import yaml
from fastapi.testclient import TestClient

from apps.gateway.config import Config
from apps.gateway.journal.writer import JournalWriter
from apps.gateway.main import create_app


@pytest.fixture
def writer(tmp_path):
    w = JournalWriter(str(tmp_path / "ev.sqlite3"))
    yield w
    w.close()


@pytest.fixture
def client(tmp_path, monkeypatch):
    cfg = Config.model_validate(yaml.safe_load(open("config/mock.yaml")))
    cfg.db_path = str(tmp_path / "api.sqlite3")
    monkeypatch.setenv("EV_WS_TOKEN", "t")
    with TestClient(create_app(cfg)) as c:
        yield c


def session_id(writer) -> int:
    return writer.open_session("2026-08-30", "Asia/Ho_Chi_Minh", 1_700_000_000_000)


def test_a_telemetry_batch_is_stored(writer):
    sid = session_id(writer)
    writer.append_pad_event(sid, {
        "ts": 1_700_000_001_000, "from": "CLUTCH", "to": "ARMED", "sym": "XAUUSD",
        "lots": 0.01, "reason": None, "clutchMs": 900, "armMs": 400,
        "clutchCycles": 2, "armFlips": 3, "btnRateHz": 4.5, "lotStepsSince": 1,
        "ttfMs": 820,
    })
    row = writer.conn.execute("SELECT * FROM pad_event").fetchone()
    assert row["arm_flips"] == 3
    assert row["clutch_ms"] == 900
    assert row["ttf_ms"] == 820
    assert row["sym"] == "XAUUSD"


def test_an_idle_heartbeat_is_stored_too(writer):
    """Phase 9 needs to tell a calm evening from an absent one."""
    sid = session_id(writer)
    writer.append_pad_event(sid, {"ts": 1, "clutchMs": 0, "armFlips": 0})
    assert writer.conn.execute("SELECT COUNT(*) c FROM pad_event").fetchone()["c"] == 1


def test_check_in_records_a_rating(writer):
    sid = session_id(writer)
    writer.write_check_in(sid, "pre", 4, 1_700_000_000_000, "slept well")
    row = writer.process_row(sid)
    assert row["pre_rating"] == 4
    assert row["pre_note"] == "slept well"
    assert row["post_rating"] is None


def test_a_skipped_check_in_is_recorded_as_a_skip(writer):
    """A skip and a question never asked are different facts, and phase 6
    should be able to tell them apart."""
    sid = session_id(writer)
    writer.write_check_in(sid, "pre", None, 1_700_000_000_000)
    row = writer.process_row(sid)
    assert row is not None
    assert row["pre_rating"] is None
    assert row["pre_at"] == 1_700_000_000_000


def test_a_rating_outside_one_to_five_is_refused(writer):
    import sqlite3

    sid = session_id(writer)
    with pytest.raises(sqlite3.IntegrityError):
        writer.write_check_in(sid, "pre", 9, 1)


def test_an_unknown_phase_is_refused(writer):
    sid = session_id(writer)
    with pytest.raises(ValueError, match="pre or post"):
        writer.write_check_in(sid, "middle", 3, 1)


def test_stand_downs_keep_their_conditions(writer):
    sid = session_id(writer)
    writer.record_stand_downs(sid, [
        {"at": 1, "conditions": ["news"]},
        {"at": 2, "conditions": ["window", "setup"]},
    ])
    row = writer.process_row(sid)
    assert row["stand_downs"] == 2
    assert json.loads(row["stand_down_json"])[1]["conditions"] == ["window", "setup"]


def test_check_in_endpoint_accepts_a_rating(client):
    res = client.post("/api/session/checkin", json={"phase": "pre", "rating": 4})
    assert res.status_code == 200
    assert res.json()["ok"] is True
    assert res.json()["skipped"] is False


def test_check_in_endpoint_accepts_a_skip(client):
    res = client.post("/api/session/checkin", json={"phase": "pre", "rating": None})
    assert res.status_code == 200
    assert res.json()["skipped"] is True


def test_check_in_endpoint_refuses_a_bad_rating(client):
    assert client.post("/api/session/checkin", json={"phase": "pre", "rating": 7}).status_code == 400
    assert client.post("/api/session/checkin", json={"phase": "x", "rating": 3}).status_code == 400


def test_check_in_never_blocks_the_session(client):
    """Even a refused check-in leaves the gateway serving."""
    client.post("/api/session/checkin", json={"phase": "pre", "rating": 99})
    assert client.get("/healthz").json()["ok"] is True


def test_stand_down_endpoint(client):
    res = client.post("/api/session/standdown", json={"events": [{"at": 1, "conditions": ["news"]}]})
    assert res.status_code == 200
    assert res.json()["count"] == 1
    assert client.post("/api/session/standdown", json={"events": "nope"}).status_code == 400
