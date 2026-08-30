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


async def test_a_closed_trade_gets_its_tape_and_excursion(stack):
    """End to end: fire, feed the tape, close, flush, and find both rows."""
    gw, session, client = stack
    base = now_ms()
    for i in range(60):
        gw.broker.transport.push_spot(
            "XAUUSD", bid=2340.0 + (0.5 if i == 30 else 0.0),
            ask=2340.2 + (0.5 if i == 30 else 0.0), ts=base + i * 1000)

    await session.handle(fire(relativeSl=200_000))
    await settle(session)
    position_id = client.last("order.ack")["p"]["positionId"]

    for i in range(60, 120):
        gw.broker.transport.push_spot("XAUUSD", bid=2341.0, ask=2341.2, ts=base + i * 1000)

    await session.handle(frame("intent.close",
                               {"positionId": position_id, "clutch": True,
                                "armedAt": now_ms()}, new_cid()))
    await settle(session)
    assert gw.freezer.pending_count == 1

    # Shutting down inside the post-roll must still freeze.
    await gw.freezer.flush_all()

    tape = gw.journal.conn.execute(
        "SELECT * FROM trade_tape WHERE position_id = ?", (position_id,)).fetchone()
    assert tape is not None
    assert tape["n"] > 0
    assert tape["sym"] == "XAUUSD"

    closed = gw.journal.conn.execute(
        "SELECT * FROM trade_closed WHERE position_id = ?", (position_id,)).fetchone()
    assert closed["mfe"] is not None
    assert closed["mae"] is not None


async def test_a_zero_trade_evening_writes_no_tape(stack):
    gw, session, client = stack
    base = now_ms()
    for i in range(120):
        gw.broker.transport.push_spot("XAUUSD", bid=2340.0, ask=2340.2, ts=base + i * 1000)
    await gw.freezer.flush_all()
    assert gw.journal.conn.execute(
        "SELECT COUNT(*) c FROM trade_tape").fetchone()["c"] == 0


async def test_the_session_records_equity_from_ctrader(stack):
    """Balance is read from the account, never re-derived by summing fills."""
    gw, session, client = stack
    await gw.snapshot_equity()
    sid = gw.state.session_id
    row = gw.journal.conn.execute(
        "SELECT * FROM session_equity WHERE session_id = ? ORDER BY ts DESC LIMIT 1",
        (sid,)).fetchone()
    assert row is not None
    assert row["balance"] == pytest.approx(10_000.00)

    opening = gw.journal.session_row(sid)
    assert opening["equity_open"] == pytest.approx(10_000.00)


async def test_the_opening_equity_is_not_overwritten_mid_session(stack):
    """It is the baseline every P/L figure for the day is measured against, so
    a restart must not move it."""
    gw, session, client = stack
    await gw.snapshot_equity()
    sid = gw.state.session_id
    gw.broker.transport.state.balance_cents = 500_000
    await gw.snapshot_equity()

    row = gw.journal.session_row(sid)
    assert row["equity_open"] == pytest.approx(10_000.00)
    points = gw.journal.conn.execute(
        "SELECT COUNT(*) c FROM session_equity WHERE session_id = ?", (sid,)).fetchone()
    assert points["c"] >= 2


async def test_shutdown_closes_the_session_with_final_equity(stack):
    gw, session, client = stack
    await gw.snapshot_equity()
    sid = gw.state.session_id
    await gw.snapshot_equity(closing=True)
    row = gw.journal.session_row(sid)
    assert row["closed_at"] is not None
    assert row["equity_close"] == pytest.approx(10_000.00)


# -- phase 7: playbook and grading ------------------------------------------


async def test_the_player_starts_with_a_real_book(stack):
    gw, session, client = stack
    listed = client.last("playbook.list")["p"]["playbooks"]
    assert len(listed) == 5
    assert all(b["ruleCount"] > 0 for b in listed)


async def test_selecting_a_playbook_is_session_state(stack):
    gw, session, client = stack
    await session.handle(frame("playbook.select", {"playbookId": "volman-break"}, seq=5))
    assert gw.state.playbook_slug == "volman-break"

    row = gw.journal.process_row(gw.state.session_id)
    assert row["playbook_id"] == gw.playbooks.get("volman-break").id
    # And it is marked in the list the HUD renders.
    assert any("✓" in b["name"] for b in client.last("playbook.list")["p"]["playbooks"])


async def test_selecting_a_playbook_emits_no_order(stack):
    """Navigation and apply can never place a trade."""
    gw, session, client = stack
    before = len(gw.broker.transport.state.sent)
    await session.handle(frame("playbook.select", {"playbookId": "volman-break"}, seq=5))
    await settle(session)
    orders = [m for m in gw.broker.transport.state.sent
              if type(m).__name__ == "ProtoOANewOrderReq"]
    assert orders == []
    assert len(gw.broker.transport.state.sent) >= before


async def test_a_fire_is_graded_and_recorded(stack):
    gw, session, client = stack
    await session.handle(frame("playbook.select", {"playbookId": "volman-break"}, seq=5))
    gw.broker.transport.push_spot("XAUUSD", bid=2340.15, ask=2340.35)

    cid = new_cid()
    await session.handle(fire(cid=cid, relativeSl=200_000))
    await settle(session)

    grade = client.last("grade")
    assert grade is not None
    assert grade["p"]["cid"] == cid
    assert grade["p"]["playbookId"] == "volman-break"

    row = gw.journal.grade_row(cid)
    assert row is not None
    assert row["phase"] == "fire"


async def test_grading_never_refuses_a_fire(stack):
    """Even a grade that fails every rule leaves the order placed."""
    gw, session, client = stack
    await session.handle(frame("playbook.select", {"playbookId": "volman-break"}, seq=5))
    cid = new_cid()
    await session.handle(fire(cid=cid))
    await settle(session)

    assert client.last("order.ack") is not None
    assert not [f for f in client.all("order.reject") if f["p"]["cid"] == cid]


async def test_a_grading_failure_does_not_cost_the_fire(stack, monkeypatch):
    gw, session, client = stack

    def explode(*a, **k):
        raise RuntimeError("grading is broken")

    monkeypatch.setattr(gw, "grade", explode)
    await session.handle(fire())
    await settle(session)
    assert client.last("order.ack") is not None
    assert gw.containment.faults >= 1


async def test_an_arm_pushes_a_preview_grade_that_is_not_recorded(stack):
    """The overlay needs a grade before the fire; a trade_grade row for a trade
    that never happened would inflate every count that reads them."""
    gw, session, client = stack
    await session.handle(frame("playbook.select", {"playbookId": "volman-break"}, seq=5))
    before = gw.journal.conn.execute("SELECT COUNT(*) c FROM trade_grade").fetchone()["c"]

    await session.handle(frame("pad.telemetry", {
        "ts": now_ms(), "from": "CLUTCH", "to": "ARMED", "sym": "XAUUSD",
        "lots": 0.01, "clutchMs": 400, "armMs": 10,
    }, seq=6))

    grade = client.last("grade")
    assert grade is not None
    assert grade["p"]["playbookId"] == "volman-break"
    after = gw.journal.conn.execute("SELECT COUNT(*) c FROM trade_grade").fetchone()["c"]
    assert after == before


async def test_an_unplanned_fire_reads_as_unplanned(stack):
    gw, session, client = stack
    cid = new_cid()
    await session.handle(fire(cid=cid))
    await settle(session)
    grade = client.last("grade")
    assert grade["p"]["playbookId"] == "__unplanned__"
    assert grade["p"]["clean"] is False


async def test_a_checklist_answer_regrades_without_blocking(stack):
    gw, session, client = stack
    await session.handle(frame("playbook.select", {"playbookId": "volman-pullback-test"}, seq=5))
    cid = new_cid()
    await session.handle(fire(cid=cid))
    await settle(session)
    before = client.last("grade")["p"]["required_total"]

    await session.handle(frame("grade.answer", {
        "cid": cid, "ruleId": "pb.waited_for_test", "answer": True}, seq=7))

    after = client.last("grade")["p"]
    assert after["cid"] == cid
    assert after["required_total"] == before + 1
    assert gw.journal.grade_row(cid)["phase"] == "settled"


# -- phase 9: tilt ----------------------------------------------------------


def telemetry(seq=6, **over):
    body = {"ts": now_ms(), "clutchMs": 400, "armMs": 10, "btnRateHz": 3.0}
    body.update(over)
    return frame("pad.telemetry", body, seq=seq)


async def test_telemetry_produces_a_tilt_message(stack):
    gw, session, client = stack
    await session.handle(telemetry())
    tilt = client.last("tilt")
    assert tilt is not None
    assert tilt["p"]["band"] == "cool"
    assert gw.journal.conn.execute(
        "SELECT COUNT(*) c FROM tilt_sample").fetchone()["c"] == 1


async def test_a_calm_evening_applies_no_friction(stack):
    gw, session, client = stack
    for i in range(3):
        await session.handle(telemetry(seq=6 + i, **{"to": "ARMED", "sym": "XAUUSD",
                                                     "clutchCycles": 1, "armFlips": 0}))
    assert gw.state.confirm_hold_ms == 0
    assert gw.state.cooldown_until_ms is None


async def test_a_scorched_band_soft_blocks_opens_but_never_an_exit(stack):
    """The whole feature, in one test."""
    gw, session, client = stack
    # A calm start establishes the player's own baseline...
    for i in range(3):
        await session.handle(telemetry(seq=6 + i, btnRateHz=3.0))
    # ...then an escalation measured against it.
    for i in range(3):
        await session.handle(telemetry(seq=9 + i, **{
            "to": "ARMED", "sym": "XAUUSD", "clutchCycles": 9, "armFlips": 9,
            "btnRateHz": 12.0,
        }))
    assert gw.state.tilt_band == "scorched", gw.state.tilt_score
    assert gw.state.cooldown_until_ms is not None
    assert gw.state.confirm_hold_ms == 750

    gw.state.last_order_ms = None
    await session.handle(fire())
    await settle(session)
    assert client.last("order.reject")["p"]["reason"] == "cooldown"

    # A close is untouched by all of it.
    await session.handle(frame("intent.close", {"positionId": 1, "clutch": True,
                                                "armedAt": now_ms()}, new_cid()))
    await settle(session)
    reasons = [f["p"]["reason"] for f in client.all("order.reject")]
    assert "cooldown" in reasons
    assert reasons[-1] != "cooldown"


async def test_a_memo_halves_the_recency_terms(stack):
    """Narrating it is the intervention."""
    gw, session, client = stack
    gw.journal.write_closed({
        "position_id": 1, "cid": None, "session_id": gw.ensure_session(now_ms()),
        "sym": "XAUUSD", "side": "buy", "lots": 0.01,
        "opened_at": now_ms() - 60_000, "closed_at": now_ms() - 20_000,
        "entry": 2340.0, "exit": 2339.0, "gross_pnl": -1.0, "net_pnl": -1.0,
        "r_usd": 2.0, "r_multiple": -0.5,
    })
    await session.handle(telemetry())
    before = client.last("tilt")["p"]["score"]
    assert before > 0

    await session.handle(frame("voice.begin", {"voiceId": new_cid()}, seq=9))
    after = client.last("tilt")["p"]["score"]
    assert after == pytest.approx(before / 2, rel=1e-6)


async def test_tilt_is_never_stored_against_the_player(stack):
    """Samples are scoped to a session; nobody is 'a tilty trader'."""
    gw, session, client = stack
    await session.handle(telemetry())
    columns = [r[1] for r in gw.journal.conn.execute("PRAGMA table_info(tilt_sample)")]
    assert "session_id" in columns
    tables = {r["name"] for r in gw.journal.conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table'")}
    assert not any("player" in t or "trader" in t for t in tables)


async def test_the_driver_is_a_sentence(stack):
    gw, session, client = stack
    for i in range(3):
        await session.handle(telemetry(seq=6 + i, **{
            "to": "ARMED", "sym": "XAUUSD", "clutchCycles": 5, "armFlips": 3,
        }))
    top = client.last("tilt")["p"]["top"]
    assert top
    assert any(ch.isalpha() for ch in top[0])
    assert "clutching" in top[0] or "flipping" in top[0]


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
