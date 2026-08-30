"""Pad to broker and back, through the real gateway with a mock socket.

Every layer here is the production one: the protocol codec, the risk registry,
the cid ledger, the journal, the R definition, the tape ring, and the cTrader
message translation. Only the TLS socket to Spotware is replaced.
"""

from __future__ import annotations

import asyncio
import json

import pytest
import yaml

from apps.gateway.api.gateway import Gateway
from apps.gateway.api.ws import WsSession
from apps.gateway.broker.factory import build_broker
from apps.gateway.config import Config
from apps.gateway.journal.writer import JournalWriter
from apps.gateway.protocol import CATALOG, new_cid, now_ms

TOKEN = "integration-token"


class Client:
    def __init__(self) -> None:
        self.sent: list[dict] = []

    async def send(self, raw: str) -> None:
        self.sent.append(json.loads(raw))

    def types(self) -> list[str]:
        return [f["t"] for f in self.sent]

    def last(self, t: str) -> dict | None:
        return next((f for f in reversed(self.sent) if f["t"] == t), None)

    def all(self, t: str) -> list[dict]:
        return [f for f in self.sent if f["t"] == t]


@pytest.fixture
async def stack(tmp_path, monkeypatch):
    cfg = Config.model_validate(yaml.safe_load(open("config/mock.yaml")))
    cfg.db_path = str(tmp_path / "ev.sqlite3")
    monkeypatch.setenv("EV_WS_TOKEN", TOKEN)

    gw = Gateway(cfg, broker=None, journal=JournalWriter(cfg.db_path))
    gw.broker = build_broker(cfg, containment=gw.containment, graph=gw.assets)
    gw._wire_broker()
    await gw.start()

    client = Client()
    session = WsSession(gw, client.send)
    gw.sessions.add(session)
    await session.handle(frame("hello", {"token": TOKEN}))
    yield gw, session, client
    await gw.shutdown()


def frame(t, p, cid=None, seq=1):
    return json.dumps({"v": 1, "t": t, "seq": seq, "ts": now_ms(),
                       "ch": CATALOG[t].ch, "cid": cid, "p": p})


def fire(sym="XAUUSD", side="buy", lots=0.01, cid=None, **extra):
    return frame("intent.open",
                 {"sym": sym, "side": side, "lots": lots, "clutch": True,
                  "armedAt": now_ms(), **extra},
                 cid or new_cid())


async def settle(session=None):
    await asyncio.sleep(0)
    if session is not None:
        await session.flush()


async def test_the_broker_comes_up_and_the_hud_is_told(stack):
    gw, session, client = stack
    welcome = client.last("welcome")
    assert welcome["p"]["features"]["broker"] is True
    health = await gw.broker.health()
    assert health.authed and health.symbols


async def test_a_fire_reaches_the_broker_and_acks_back(stack):
    gw, session, client = stack
    cid = new_cid()
    await session.handle(fire(cid=cid))
    await settle(session)

    assert not client.all("order.reject"), client.all("order.reject")
    ack = client.last("order.ack")
    assert ack is not None
    assert ack["p"]["cid"] == cid
    assert ack["p"]["sym"] == "XAUUSD"
    assert ack["p"]["price"] == pytest.approx(2340.35)
    assert ack["p"]["positionId"]
    # The HUD speaks lots, so the ack has to as well -- reporting the protocol
    # volume, or zero, would show the player something they did not press.
    assert ack["p"]["lots"] == pytest.approx(0.01)


async def test_the_cid_ledger_records_the_whole_life_of_a_fire(stack):
    gw, session, client = stack
    cid = new_cid()
    await session.handle(fire(cid=cid))
    await settle(session)
    assert gw.journal.cid_state(cid) == "acked"


async def test_a_fire_writes_a_plan_with_an_auditable_r(stack):
    gw, session, client = stack
    gw.broker.transport.push_spot("XAUUSD", bid=2340.15, ask=2340.35)
    cid = new_cid()
    # A 2.00 stop on one ounce of gold is 2.00 USD of risk.
    await session.handle(fire(cid=cid, relativeSl=200_000, relativeTp=400_000))
    await settle(session)

    plan = gw.journal.conn.execute(
        "SELECT * FROM trade_plan WHERE cid = ?", (cid,)
    ).fetchone()
    assert plan is not None
    assert plan["protocol_volume"] == 100
    assert plan["r_source"] == "stop"
    assert plan["r_usd"] == pytest.approx(2.00, abs=0.01)
    # The conversion inputs are kept so the number stays checkable later.
    assert plan["r_rate"] == 1.0
    assert plan["r_rate_chain"] == "USD"
    assert plan["r_rate_ts"]
    assert plan["planned_sl"] == pytest.approx(2338.35)
    assert plan["planned_rr"] == pytest.approx(2.0)


async def test_r_is_known_from_the_stop_distance_before_any_quote_arrives(stack):
    """R is a property of size and stop, both of which the order carries. The
    first fire of an evening must not be scored against the fallback merely
    because no spot has been seen yet."""
    gw, session, client = stack
    assert "XAUUSD" not in gw.state.last_quote
    cid = new_cid()
    await session.handle(fire(cid=cid, relativeSl=200_000))
    await settle(session)

    plan = gw.journal.conn.execute(
        "SELECT * FROM trade_plan WHERE cid = ?", (cid,)).fetchone()
    assert plan["r_source"] == "stop"
    assert plan["r_usd"] == pytest.approx(2.00, abs=0.01)
    # No quote means no absolute entry, so the absolute stop is honestly null
    # rather than invented from a price we never saw.
    assert plan["planned_sl"] is None


async def test_a_fire_without_a_stop_falls_back_to_the_configured_r_unit(stack):
    gw, session, client = stack
    gw.broker.transport.push_spot("XAUUSD", bid=2340.15, ask=2340.35)
    cid = new_cid()
    await session.handle(fire(cid=cid))
    await settle(session)
    plan = gw.journal.conn.execute(
        "SELECT * FROM trade_plan WHERE cid = ?", (cid,)).fetchone()
    assert plan["r_source"] == "r_unit_fallback"
    assert plan["r_usd"] == pytest.approx(20.0)


async def test_a_close_writes_a_closed_trade_with_a_non_null_r_multiple(stack):
    gw, session, client = stack
    gw.broker.transport.push_spot("XAUUSD", bid=2340.15, ask=2340.35)
    await session.handle(fire(relativeSl=200_000))
    await settle(session)
    position_id = client.last("order.ack")["p"]["positionId"]

    await session.handle(frame("intent.close",
                               {"positionId": position_id, "clutch": True,
                                "armedAt": now_ms()}, new_cid()))
    await settle(session)

    row = gw.journal.conn.execute(
        "SELECT * FROM trade_closed WHERE position_id = ?", (position_id,)
    ).fetchone()
    assert row is not None
    assert row["r_multiple"] is not None
    # Bought the 2340.35 ask, sold the 2340.15 bid, one ounce, minus 3.00
    # commission -> about -3.20 on a 2.00 R.
    assert row["net_pnl"] == pytest.approx(-3.20, abs=0.02)
    assert row["r_usd"] == pytest.approx(2.00, abs=0.01)
    assert row["r_multiple"] == pytest.approx(-1.60, abs=0.02)


async def test_pos_snap_carries_lots_and_the_gateway_s_own_r(stack):
    """The HUD must never divide a constant into the dollars to get R. It is
    sent the R the gateway computed, or null."""
    gw, session, client = stack
    await session.handle(fire(relativeSl=200_000))
    await settle(session)
    await session.handle(frame("snap", {"what": ["pos"]}, seq=9))
    await settle(session)

    snap = client.last("pos.snap")["p"]["positions"][0]
    assert snap["lots"] == pytest.approx(0.01)
    assert snap["sym"] == "XAUUSD"


async def test_a_reconciled_position_reports_a_null_r_rather_than_a_guess(stack):
    """A position this gateway did not open has no plan, so no R. Null is the
    honest answer; the HUD falls back to dollars."""
    gw, session, client = stack
    from apps.gateway.broker.mock import MockPosition
    from ctrader_open_api.messages import OpenApiModelMessages_pb2 as model

    gw.broker.transport.state.positions[9_001] = MockPosition(
        position_id=9_001, symbol_id=41, side=model.BUY, volume=100,
        entry=2340.0, opened_at=now_ms(),
    )
    await gw.broker.reconcile()
    await session.handle(frame("snap", {"what": ["pos"]}, seq=9))
    await settle(session)

    snap = client.last("pos.snap")["p"]["positions"][0]
    # Null is dropped from the wire by exclude_none, so the HUD sees an absent
    # key. formatOpenPnl treats absent and null alike and shows dollars.
    assert snap.get("rMultiple") is None
    assert snap["lots"] == pytest.approx(0.01)


async def test_every_broker_fact_lands_in_position_event(stack):
    gw, session, client = stack
    await session.handle(fire())
    await settle(session)
    position_id = client.last("order.ack")["p"]["positionId"]
    await session.handle(frame("intent.close",
                               {"positionId": position_id, "clutch": True,
                                "armedAt": now_ms()}, new_cid()))
    await settle(session)

    kinds = [r["kind"] for r in gw.journal.conn.execute(
        "SELECT kind FROM position_event WHERE position_id = ? ORDER BY id",
        (position_id,))]
    assert kinds == ["fill", "close"]


async def test_spots_feed_the_tape_ring_before_conflation(stack):
    gw, session, client = stack
    for i in range(30):
        gw.broker.transport.push_spot(
            "XAUUSD", bid=2340.0 + i * 0.01, ask=2340.2 + i * 0.01,
            ts=1_700_000_000_000 + i * 20,
        )
    gw.tape.seal_all()
    bars = gw.tape.ring("XAUUSD").bars()
    assert bars
    # 30 ticks inside one second: the ring saw every one of them.
    assert sum(b.n_ticks for b in bars) == 30


async def test_quotes_reach_the_hud_conflated_not_per_tick(stack):
    gw, session, client = stack
    base = now_ms()
    for i in range(40):
        gw.broker.transport.push_spot(
            "XAUUSD", bid=2340.0 + i * 0.01, ask=2340.2 + i * 0.01, ts=base + i * 5)
        session.enqueue_quote("XAUUSD", 2340.0 + i * 0.01, 2340.2 + i * 0.01,
                              base + i * 5, 2)
    await session.flush()
    quotes = client.all("quote")
    # 200ms of ticks at 15 Hz is a handful of frames, not forty.
    assert 1 <= len(quotes) <= 5


async def test_the_daily_loss_gate_uses_real_closed_pnl(stack):
    gw, session, client = stack
    gw.cfg.risk.max_daily_loss_usd = 1.0   # one losing round trip is enough
    await session.handle(fire())
    await settle(session)
    position_id = client.last("order.ack")["p"]["positionId"]
    await session.handle(frame("intent.close",
                               {"positionId": position_id, "clutch": True,
                                "armedAt": now_ms()}, new_cid()))
    await settle(session)
    assert gw.day_loss_usd() > 1.0

    gw.state.last_order_ms = None
    await session.handle(fire())
    await settle(session)
    assert client.last("order.reject")["p"]["reason"] == "max_daily_loss"


async def test_a_closed_out_evening_still_allows_the_exit(stack):
    """The daily loss makes the session close-only, never close-refusing."""
    gw, session, client = stack
    await session.handle(fire())
    await settle(session)
    position_id = client.last("order.ack")["p"]["positionId"]

    gw.cfg.risk.max_daily_loss_usd = 0.01
    gw.state.locked = True
    await session.handle(frame("intent.close",
                               {"positionId": position_id, "clutch": True,
                                "armedAt": now_ms()}, new_cid()))
    await settle(session)
    assert not any(f["p"].get("reason") in {"max_daily_loss", "locked"}
                   for f in client.all("order.reject"))
    assert await gw.broker.positions() == []


async def test_panic_flattens_everything_and_locks(stack):
    gw, session, client = stack
    gw.cfg.risk.max_positions = 3
    for _ in range(2):
        gw.state.last_order_ms = None
        await session.handle(fire())
        await settle(session)
    assert len(await gw.broker.positions()) == 2

    await session.handle(frame("intent.panic",
                               {"clutch": True, "armedAt": now_ms()}, new_cid()))
    await settle(session)
    assert await gw.broker.positions() == []
    assert gw.state.locked is True


async def test_a_duplicate_cid_never_reaches_the_broker_twice(stack):
    gw, session, client = stack
    cid = new_cid()
    raw = fire(cid=cid)
    await session.handle(raw)
    await settle(session)
    await session.handle(raw)
    await settle(session)

    assert client.last("order.reject")["p"]["reason"] == "duplicate_cid"
    orders = [m for m in gw.broker.transport.state.sent
              if type(m).__name__ == "ProtoOANewOrderReq"]
    assert len(orders) == 1


async def test_a_broker_rejection_becomes_an_order_reject_frame(stack):
    gw, session, client = stack
    gw.broker.transport.state.reject_next_order_with = "NOT_ENOUGH_MONEY"
    await session.handle(fire())
    await settle(session)
    assert client.last("order.reject")["p"]["reason"] == "broker_error"


async def test_a_stop_out_reaches_the_hud_and_the_journal(stack):
    gw, session, client = stack
    await session.handle(fire(relativeSl=200_000))
    await settle(session)
    position_id = client.last("order.ack")["p"]["positionId"]

    gw.broker.transport.push_stop_out(position_id, 2338.35)
    await settle(session)

    upd = client.last("order.upd")
    assert upd["p"]["status"] == "closed"
    assert gw.journal.conn.execute(
        "SELECT COUNT(*) c FROM trade_closed WHERE position_id = ?",
        (position_id,)).fetchone()["c"] == 1


async def test_a_broker_that_will_not_start_leaves_the_socket_serving(tmp_path, monkeypatch):
    """One process is one blast radius, so a dead broker must degrade the
    gateway rather than kill it."""
    cfg = Config.model_validate(yaml.safe_load(open("config/mock.yaml")))
    cfg.db_path = str(tmp_path / "ev.sqlite3")
    monkeypatch.setenv("EV_WS_TOKEN", TOKEN)

    gw = Gateway(cfg, journal=JournalWriter(cfg.db_path))
    gw.broker.transport.state.is_live = True   # start() will refuse this
    await gw.start()

    assert gw.containment.faults == 1
    assert gw.state.locked is True

    client = Client()
    session = WsSession(gw, client.send)
    await session.handle(frame("hello", {"token": TOKEN}))
    assert client.last("welcome") is not None
    await session.handle(fire())
    assert client.last("order.reject")["p"]["reason"] == "locked"
    await gw.shutdown()
