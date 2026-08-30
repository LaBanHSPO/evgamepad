"""Serving a frozen tape back for replay."""

from __future__ import annotations

import pytest
import yaml
from fastapi.testclient import TestClient

from apps.gateway.config import Config
from apps.gateway.journal.tape.ring import TapeRing
from apps.gateway.journal.tape.scheduler import FreezeScheduler, PendingFreeze
from apps.gateway.journal.writer import JournalWriter
from apps.gateway.main import create_app

CID = "01JBXQ4T7ZK9M2N5P8R3V6W1YZ"
T0 = 1_700_000_000
MS = T0 * 1000


def px(v: float) -> int:
    return int(round(v * 100_000))


def seeded(writer: JournalWriter) -> None:
    """A closed trade with a real frozen window behind it."""
    writer.reserve_cid(CID, "open", MS, "XAUUSD")
    writer.mark_cid(CID, "acked", MS, position_id=7001)
    writer.write_closed({
        "position_id": 7001, "cid": CID, "session_id": None, "sym": "XAUUSD",
        "side": "buy", "lots": 0.01, "opened_at": MS, "closed_at": MS + 60_000,
        "entry": 2340.0, "exit": 2342.0, "gross_pnl": 2.0, "net_pnl": 2.0,
        "r_usd": 2.0, "r_multiple": 1.0, "exit_reason": "manual",
    })
    writer.append_event(7001, MS, "fill", cid=CID, price=2340.0, lots=0.01)
    writer.append_event(7001, MS + 60_000, "close", cid=CID, price=2342.0)

    ring = TapeRing(ring_minutes=90, dt_s=1)
    for i in range(120):
        bid = 2340.0 + (0.5 if i == 30 else 0.0)
        ring.on_tick("XAUUSD", px(bid), px(bid + 0.20), MS + i * 1000, digits=2)
    ring.seal_all()

    FreezeScheduler(ring, writer, pre_roll_s=300, post_roll_s=300, dt_s=1).flush_one(
        PendingFreeze(
            position_id=7001, cid=CID, sym="XAUUSD", side="buy", entry=2340.0,
            digits=2, opened_at=MS, closed_at=MS + 60_000,
            r_usd=2.0, protocol_volume=100, r_rate=1.0,
        )
    )


@pytest.fixture
def client(tmp_path, monkeypatch):
    cfg = Config.model_validate(yaml.safe_load(open("config/mock.yaml")))
    cfg.db_path = str(tmp_path / "replay.sqlite3")
    monkeypatch.setenv("EV_WS_TOKEN", "t")
    with TestClient(create_app(cfg)) as c:
        seeded(c.app.state.gw.journal)
        yield c


def test_a_trade_with_no_tape_is_a_404(client):
    assert client.get("/api/replay/01JBXQ4T7ZK9M2N5P8R3V6W1ZZ").status_code == 404


def test_the_whole_window_comes_back_in_one_read(client):
    body = client.get(f"/api/replay/{CID}").json()
    assert body["ok"] is True
    assert body["sym"] == "XAUUSD"
    assert body["fromTs"] == T0 - 300
    assert body["toTs"] == T0 + 60 + 300
    assert body["dtS"] == 1


def test_bars_arrive_columnar_as_scaled_integers(client):
    """Columnar so the chart gets arrays rather than thousands of objects, and
    integers because the protocol's prices are scaled, never floats."""
    bars = client.get(f"/api/replay/{CID}").json()["bars"]
    assert set(bars) == {
        "ts", "bid_o", "bid_h", "bid_l", "bid_c",
        "ask_o", "ask_h", "ask_l", "ask_c", "n_ticks",
    }
    assert len(bars["ts"]) == len(bars["bid_c"]) > 0
    assert all(isinstance(v, int) for v in bars["bid_c"])
    assert bars["bid_c"][0] > 100_000_000  # scaled, not a float price


def test_both_sides_of_the_book_are_stored(client):
    """A long's excursion is measured on the bid and a short's on the ask.
    Bid-only would be a silent asymmetry bug in MAE."""
    bars = client.get(f"/api/replay/{CID}").json()["bars"]
    assert bars["ask_c"][0] > bars["bid_c"][0]


def test_the_closed_trade_facts_come_with_it(client):
    trade = client.get(f"/api/replay/{CID}").json()["trade"]
    assert trade["r_multiple"] == pytest.approx(1.0)
    assert trade["mfe"] is not None
    assert trade["exit_reason"] == "manual"


def test_events_are_what_make_it_coaching_rather_than_charting(client):
    events = client.get(f"/api/replay/{CID}").json()["events"]
    kinds = {e.get("kind") for e in events}
    assert {"fill", "close"} <= kinds
    assert any(e.get("price") == 2340.0 for e in events)


def test_the_index_drives_stepping_between_replays(client):
    body = client.get("/api/replay/index").json()
    assert body["ok"] is True
    assert len(body["trades"]) == 1
    row = body["trades"][0]
    assert row["cid"] == CID
    assert row["n"] > 0


def test_the_index_lists_only_trades_that_have_a_tape(client):
    """A row the replay route would 404 on has no business in the list that
    drives stepping."""
    gw = client.app.state.gw
    gw.journal.write_closed({
        "position_id": 9999, "cid": None, "session_id": None, "sym": "EURUSD",
        "side": "sell", "lots": 0.1, "opened_at": MS, "closed_at": MS + 1000,
        "entry": 1.08, "exit": 1.079, "gross_pnl": 1.0, "net_pnl": 1.0,
        "r_usd": 2.0, "r_multiple": 0.5,
    })
    trades = client.get("/api/replay/index").json()["trades"]
    assert [t["position_id"] for t in trades] == [7001]


def test_the_index_respects_its_limit(client):
    assert len(client.get("/api/replay/index?limit=0").json()["trades"]) == 0
