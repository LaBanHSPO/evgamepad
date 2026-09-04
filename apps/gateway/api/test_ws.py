"""The order path end to end, minus Spotware.

A fake broker stands in for the network so the parts that decide whether an order happens — the
gates, the cid ledger, the exit exemption, the containment boundary — are exercised for real.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from api.conflate import Conflator
from api.ws import AI_DISABLED, GameSocket, GatewayState, origin_allowed
from broker import Broker, BrokerResult, contain
from db.migrate import connect, migrate
from journal.writer import JournalWriter
from protocol import Envelope, new_cid
from risk.session import SessionWindow

TZ = "Asia/Ho_Chi_Minh"


class FakeBroker(Broker):
    """Records what it was asked to do and answers however the test needs."""

    def __init__(self) -> None:
        self.placed: list[dict[str, Any]] = []
        self.closed: list[int] = []
        self.amended: list[dict[str, Any]] = []
        self.open_positions: list[dict[str, Any]] = []
        self.fail_reason: str | None = None

    def snapshot(self) -> dict[str, Any]:
        return {"connected": True}

    async def health(self) -> BrokerResult:
        return BrokerResult(ok=True)

    async def account(self) -> dict[str, Any]:
        return {"balance": 10_000.0}

    async def positions(self) -> list[dict[str, Any]]:
        return list(self.open_positions)

    async def place(self, *, cid: str, sym: str, side: str, lots: float,
                    relative_sl: int | None = None, relative_tp: int | None = None) -> BrokerResult:
        if self.fail_reason:
            return BrokerResult(ok=False, reason=self.fail_reason, detail={"cid": cid})
        self.placed.append({"cid": cid, "sym": sym, "side": side, "lots": lots,
                            "relative_sl": relative_sl, "relative_tp": relative_tp})
        return BrokerResult(ok=True, detail={"cid": cid})

    async def close(self, *, cid: str, position_id: int) -> BrokerResult:
        self.closed.append(position_id)
        return BrokerResult(ok=True, detail={"cid": cid})

    async def amend_position_sl_tp(self, *, cid: str, position_id: int, sl: float | None = None,
                                   tp: float | None = None) -> BrokerResult:
        self.amended.append({"positionId": position_id, "sl": sl, "tp": tp})
        return BrokerResult(ok=True, detail={"cid": cid})

    def on_fill(self, handler: Any) -> None:
        self._handler = contain(handler, what="fill")


@pytest.fixture()
def socket(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> GameSocket:
    db = tmp_path / "journal.db"
    migrate(db)
    journal = JournalWriter(connect(db))
    # The session row exists before the socket does in production, and telemetry's foreign key
    # depends on it — so the fixture opens one too.
    journal.open_session("S-1", timezone=TZ, opened_at=1, balance=None, equity=None)
    sent: list[str] = []

    async def send(raw: str) -> None:
        sent.append(raw)

    gs = GameSocket(
        send=send,
        broker=FakeBroker(),
        journal=journal,
        window=SessionWindow.from_config(TZ, ["sun", "mon", "tue", "wed", "thu", "fri", "sat"],
                                         "00:00", "23:59"),
        state=GatewayState(session_id="S-1"),
        allowed_symbols=frozenset({"XAUUSD", "EURUSD"}),
        max_positions=1,
        max_lots_by_symbol={"XAUUSD": 0.10, "EURUSD": 0.50},
        max_day_loss_usd=200.0,
        min_seconds_between_orders=2.0,
        heartbeat_dead_s=3.0,
    )
    gs.sent = sent  # type: ignore[attr-defined]
    return gs


def frames(socket: GameSocket) -> list[dict[str, Any]]:
    return [json.loads(raw) for raw in socket.sent]  # type: ignore[attr-defined]


def last(socket: GameSocket, t: str) -> dict[str, Any]:
    matching = [f for f in frames(socket) if f["t"] == t]
    assert matching, f"no `{t}` frame in {[f['t'] for f in frames(socket)]}"
    return matching[-1]


def open_intent(**over: Any) -> Envelope:
    payload = {"sym": "XAUUSD", "side": "buy", "type": "market", "lots": 0.01,
               "relativeSl": 200_000, "clutch": True, "armedAt": 1}
    payload.update(over)
    return Envelope(t="intent.open", seq=1, ts=1, ch="orders", cid=new_cid(), p=payload)


@pytest.mark.asyncio
async def test_a_clean_intent_reaches_the_broker_once(socket: GameSocket) -> None:
    await socket.route(open_intent())
    assert len(socket.broker.placed) == 1
    assert socket.broker.placed[0]["relative_sl"] == 200_000
    assert last(socket, "order.ack")["p"]["lots"] == 0.01


@pytest.mark.asyncio
async def test_a_duplicate_cid_does_not_double(socket: GameSocket) -> None:
    """The retry case: same cid twice sends one order and reports the original."""
    intent = open_intent()
    await socket.route(intent)
    socket.state.last_order_ms = 0  # remove the rate gate so only the cid ledger can stop it
    await socket.route(intent)

    assert len(socket.broker.placed) == 1
    assert last(socket, "order.upd")["p"]["state"].startswith("duplicate:")


@pytest.mark.asyncio
async def test_an_overlapping_retry_with_a_fresh_cid_hits_the_rate_gate(socket: GameSocket) -> None:
    await socket.route(open_intent())
    await socket.route(open_intent())
    assert len(socket.broker.placed) == 1
    assert last(socket, "order.reject")["p"]["reason"] == "rate_limited"


@pytest.mark.asyncio
async def test_a_fire_after_clutch_down_still_sends_one_order(socket: GameSocket) -> None:
    """Heartbeat clutch is dead-man only. The intent's own clutch is what authorises the fire."""
    socket.state.last_ping_ms = socket.now_ms()  # fresh heartbeat, whatever its clutch flag said
    await socket.route(open_intent(clutch=True))
    assert len(socket.broker.placed) == 1


@pytest.mark.asyncio
async def test_three_seconds_of_silence_rejects_an_open(socket: GameSocket) -> None:
    socket.state.last_ping_ms = socket.now_ms() - 3_500
    await socket.route(open_intent())
    assert socket.broker.placed == []
    assert last(socket, "order.reject")["p"]["reason"] == "dead_man"


@pytest.mark.asyncio
async def test_a_close_is_exempt_from_the_dead_man(socket: GameSocket) -> None:
    """The whole safety story: an exit is never blocked by an open-only gate."""
    socket.state.last_ping_ms = socket.now_ms() - 30_000
    socket.state.day_loss_usd = 1_000.0
    socket.state.locked = True

    await socket.route(Envelope(t="intent.close", seq=1, ts=1, ch="orders", cid=new_cid(),
                                p={"positionId": 9, "clutch": True, "armedAt": 1}))
    assert socket.broker.closed == [9]
    assert last(socket, "order.upd")["p"]["state"] == "closed"


@pytest.mark.asyncio
async def test_panic_flattens_everything_then_locks(socket: GameSocket) -> None:
    socket.broker.open_positions = [{"positionId": 1}, {"positionId": 2}]
    socket.state.last_ping_ms = socket.now_ms() - 30_000

    await socket.route(Envelope(t="intent.panic", seq=1, ts=1, ch="orders", cid=new_cid(),
                                p={"clutch": True, "armedAt": 1}))
    assert socket.broker.closed == [1, 2]
    assert socket.state.locked is True
    assert last(socket, "session")["p"]["locked"] is True


@pytest.mark.asyncio
async def test_the_daily_loss_makes_the_evening_close_only(socket: GameSocket) -> None:
    socket.state.day_loss_usd = 200.0
    await socket.route(open_intent())
    assert last(socket, "order.reject")["p"]["reason"] == "daily_loss"

    await socket.route(Envelope(t="intent.close", seq=1, ts=1, ch="orders", cid=new_cid(),
                                p={"positionId": 4, "clutch": True, "armedAt": 1}))
    assert socket.broker.closed == [4]


@pytest.mark.asyncio
async def test_a_locked_session_blocks_opens_but_not_exits(socket: GameSocket) -> None:
    await socket.route(Envelope(t="session.lock", seq=1, ts=1, ch="session", p={}))
    await socket.route(open_intent())
    assert last(socket, "order.reject")["p"]["reason"] == "session_closed"

    await socket.route(Envelope(t="session.unlock", seq=1, ts=1, ch="session", p={}))
    await socket.route(open_intent())
    assert len(socket.broker.placed) == 1


@pytest.mark.asyncio
async def test_a_broker_rejection_is_journalled_and_reported(socket: GameSocket) -> None:
    socket.broker.fail_reason = "broker_reject"
    intent = open_intent()
    await socket.route(intent)

    assert last(socket, "order.reject")["p"]["reason"] == "broker_reject"
    assert socket.journal.cid_state(str(intent.cid))["state"] == "rejected"


@pytest.mark.asyncio
async def test_a_modify_needs_the_clutch_like_any_broker_changing_action(socket: GameSocket) -> None:
    await socket.route(Envelope(t="intent.modify", seq=1, ts=1, ch="orders", cid=new_cid(),
                                p={"positionId": 9, "sl": 1998.0, "clutch": True, "armedAt": 1}))
    assert socket.broker.amended == [{"positionId": 9, "sl": 1998.0, "tp": None}]


@pytest.mark.asyncio
async def test_an_unknown_symbol_never_reaches_the_broker(socket: GameSocket) -> None:
    await socket.route(open_intent(sym="BTCUSD"))
    assert socket.broker.placed == []
    assert last(socket, "order.reject")["p"]["reason"] == "symbol_not_allowed"


@pytest.mark.asyncio
async def test_hello_welcomes_and_resync_replays_from_last_seq(socket: GameSocket) -> None:
    await socket.route(Envelope(t="hello", seq=1, ts=1, ch="session", p={"token": "t"}))
    assert last(socket, "welcome")["p"]["mode"] == "demo"

    await socket.emit("quote", "quotes", {"sym": "XAUUSD", "bid": 1.0, "ask": 1.1, "ts": 1})
    before = len(frames(socket))
    await socket.route(Envelope(t="resync", seq=2, ts=1, ch="session", p={"lastSeq": 1}))
    assert len(frames(socket)) > before, "missed frames are replayed, not dropped"


@pytest.mark.asyncio
async def test_snap_reads_positions_from_the_broker(socket: GameSocket) -> None:
    socket.broker.open_positions = [{"positionId": 7, "symbol": "XAUUSD"}]
    await socket.route(Envelope(t="snap", seq=1, ts=1, ch="session", p={"what": "all"}))
    assert last(socket, "pos.snap")["p"]["positions"][0]["positionId"] == 7
    assert socket.state.positions_open == 1


@pytest.mark.asyncio
async def test_quotes_only_go_to_subscribed_symbols(socket: GameSocket) -> None:
    await socket.push_quote("XAUUSD", 2000.0, 2000.3)
    assert not [f for f in frames(socket) if f["t"] == "quote"]

    await socket.route(Envelope(t="sub", seq=1, ts=1, ch="session", p={"ch": "quotes",
                                                                      "syms": ["XAUUSD"]}))
    await socket.push_quote("XAUUSD", 2000.0, 2000.3)
    assert last(socket, "quote")["p"]["sym"] == "XAUUSD"


@pytest.mark.asyncio
async def test_the_desk_answers_but_stays_disabled_until_phase_four(socket: GameSocket) -> None:
    await socket.route(Envelope(t="ai.ask", seq=1, ts=1, ch="ai", cid=new_cid(),
                                p={"kind": "advise", "sym": "XAUUSD"}))
    assert AI_DISABLED["reason"] in last(socket, "ai.advice")["p"]["text"]


@pytest.mark.asyncio
async def test_pad_telemetry_is_journalled_now_and_scored_in_phase_nine(socket: GameSocket) -> None:
    await socket.route(Envelope(t="pad.telemetry", seq=1, ts=1, ch="session", p={
        "ts": 1, "from": "IDLE", "to": "ARM", "clutchMs": 900, "armMs": 300, "clutchCycles": 1,
        "armFlips": 0, "btnRateHz": 2.0, "lotStepsSince": 0,
    }))
    row = socket.journal.conn.execute(
        "SELECT from_phase, to_phase, clutch_ms, btn_rate_hz FROM pad_event"
    ).fetchone()
    assert row == ("IDLE", "ARM", 900, 2.0)


@pytest.mark.asyncio
async def test_a_malformed_frame_is_an_error_not_a_crash(socket: GameSocket) -> None:
    await socket.handle_raw("{not json")
    assert last(socket, "error")["p"]["code"] == "bad_frame"

    await socket.handle_raw(json.dumps({"v": 1, "t": "intent.open", "seq": 1, "ts": 1,
                                        "ch": "orders", "p": {"sym": "XAUUSD"}}))
    assert last(socket, "error")["p"]["code"] == "bad_frame"
    assert socket.broker.placed == []


@pytest.mark.asyncio
async def test_a_contained_broker_failure_surfaces_as_a_maint_frame(socket: GameSocket) -> None:
    """A callback exception is swallowed at the boundary; the socket says so and stays up."""
    def explode(_payload: dict[str, Any]) -> None:
        raise RuntimeError("protobuf callback blew up")

    contained = contain(explode, what="fill")
    assert contained({"anything": True}) is None

    await socket.push_maint("broker callback failed")
    assert last(socket, "maint")["p"]["active"] is True

    await socket.route(open_intent())
    assert len(socket.broker.placed) == 1, "the socket and the order path are still alive"


def test_the_conflator_keeps_only_the_latest_quote_per_symbol() -> None:
    """Never 60 Hz of quote text: a burst collapses to one frame per symbol per tick."""
    conflator = Conflator()
    for i in range(60):
        conflator.offer("XAUUSD", {"sym": "XAUUSD", "bid": 2000 + i})
    conflator.offer("EURUSD", {"sym": "EURUSD", "bid": 1.1})

    drained = conflator.drain()
    assert len(drained) == 2
    assert {d["sym"] for d in drained} == {"XAUUSD", "EURUSD"}
    assert next(d for d in drained if d["sym"] == "XAUUSD")["bid"] == 2059
    assert conflator.drain() == []


def test_only_the_huds_own_origin_may_open_the_socket() -> None:
    assert origin_allowed("https://evgamepad.example", "https://evgamepad.example")
    assert origin_allowed("https://evgamepad.example/", "https://evgamepad.example")
    assert not origin_allowed("https://evil.example", "https://evgamepad.example")
    assert not origin_allowed(None, "https://evgamepad.example")
    assert origin_allowed("https://bobvolman.com", ["https://gw.bobvolman.com", "https://bobvolman.com"])
    assert not origin_allowed("https://evil.example", ["https://bobvolman.com"])


# -- tilt (phase 9) -------------------------------------------------------------------


def tilted(socket: GameSocket, band: str = "scorched") -> None:
    """Force the tracker into a band without waiting for an evening to go wrong."""
    from tilt.tracker import TiltTracker

    tracker = TiltTracker()
    tracker.session.observe_fire(0.01)
    tracker.losses_tonight = 5
    tracker.last_loss_ms = socket.now_ms()
    tracker.pending_lots = 0.10
    tracker.recent_grades.extend([False, False, False])
    tracker.clutch_cycles.extend([10.0, 10.0, 10.0])
    tracker.arm_flips.extend([5.0, 5.0, 5.0])
    tracker.last_btn_rate = 20.0
    tracker.session.observe_telemetry(2.0)
    socket.tilt = tracker
    if band == "scorched":
        socket.tilt.cooldown_until = socket.now_ms() + 300_000


@pytest.mark.asyncio
async def test_at_the_scorched_band_an_open_is_rejected_with_cooldown(socket: GameSocket) -> None:
    tilted(socket)
    await socket.route(open_intent())
    assert socket.broker.placed == []
    assert last(socket, "order.reject")["p"]["reason"] == "cooldown"


@pytest.mark.asyncio
async def test_tilt_at_one_still_lets_a_close_and_a_panic_through(socket: GameSocket) -> None:
    """The safety property the whole phase rests on."""
    tilted(socket)
    socket.broker.open_positions = [{"positionId": 7}, {"positionId": 8}]

    await socket.route(Envelope(t="intent.close", seq=1, ts=1, ch="orders", cid=new_cid(),
                                p={"positionId": 7, "clutch": True, "armedAt": 1}))
    assert socket.broker.closed == [7]

    await socket.route(Envelope(t="intent.panic", seq=2, ts=1, ch="orders", cid=new_cid(),
                                p={"clutch": True, "armedAt": 1}))
    assert socket.broker.closed == [7, 7, 8]


@pytest.mark.asyncio
async def test_an_expired_cooldown_stops_blocking(socket: GameSocket) -> None:
    tilted(socket)
    socket.tilt.cooldown_until = socket.now_ms() - 1
    await socket.route(open_intent())
    assert len(socket.broker.placed) == 1


@pytest.mark.asyncio
async def test_telemetry_produces_a_tilt_frame_and_a_sample_row(socket: GameSocket) -> None:
    from tilt.tracker import TiltTracker

    socket.tilt = TiltTracker()
    await socket.route(Envelope(t="pad.telemetry", seq=1, ts=1, ch="session", p={
        "ts": 1, "from": "IDLE", "to": "ARM", "clutchMs": 900, "armMs": 300, "clutchCycles": 4,
        "armFlips": 2, "btnRateHz": 6.0, "lotStepsSince": 0,
    }))

    frame = last(socket, "tilt")["p"]
    assert set(frame) >= {"score", "band", "top"}
    assert 0.0 <= frame["score"] <= 1.0

    row = socket.journal.conn.execute(
        "SELECT band, top_driver FROM tilt_sample"
    ).fetchone()
    assert row[0] == frame["band"]


@pytest.mark.asyncio
async def test_the_top_driver_is_a_sentence_not_a_number(socket: GameSocket) -> None:
    tilted(socket, band="hot")
    socket.tilt.cooldown_until = None
    await socket.push_tilt()
    top = last(socket, "tilt")["p"]["top"]
    assert top and isinstance(top[0], str)
    assert any(char.isalpha() for char in top[0])


@pytest.mark.asyncio
async def test_disabling_tilt_removes_it_entirely(socket: GameSocket) -> None:
    from tilt.tracker import TiltTracker

    socket.tilt = TiltTracker(enabled=False)
    socket.tilt.losses_tonight = 5
    socket.tilt.last_loss_ms = socket.now_ms()
    socket.tilt.pending_lots = 1.0

    await socket.push_tilt()
    assert last(socket, "tilt")["p"]["score"] == 0.0
    await socket.route(open_intent())
    assert len(socket.broker.placed) == 1


@pytest.mark.asyncio
async def test_with_no_tracker_at_all_the_socket_still_trades(socket: GameSocket) -> None:
    socket.tilt = None
    await socket.route(Envelope(t="pad.telemetry", seq=1, ts=1, ch="session", p={
        "ts": 1, "from": "IDLE", "to": "ARM", "clutchMs": 1, "armMs": 1, "clutchCycles": 1,
        "armFlips": 0, "btnRateHz": 1.0, "lotStepsSince": 0,
    }))
    await socket.route(open_intent())
    assert len(socket.broker.placed) == 1


class FakeDesk:
    """A desk that answers instantly. The real one speaks over the network; neither may block."""

    def __init__(self, text: str = "spread is wide; wait for it to settle") -> None:
        self.text = text
        self.monitor_calls: list[int] = []

    async def monitor(self, now_ms: int) -> Any:
        self.monitor_calls.append(now_ms)
        from copilot.client import DeskAnswer

        return DeskAnswer(text=self.text, sources=[])


@pytest.mark.asyncio
async def test_crossing_into_the_hot_band_emits_one_desk_advice(socket: GameSocket) -> None:
    """One advice on the way in, not one per telemetry batch."""
    desk = FakeDesk()
    socket.desk = desk
    tilted(socket, band="hot")
    socket.tilt.cooldown_until = None

    await socket.push_tilt()
    await socket.drain_desk()
    assert len(desk.monitor_calls) == 1
    assert last(socket, "ai.advice")["p"]["text"] == desk.text

    # Still hot a second later: the desk stays quiet, because nothing was crossed.
    await socket.push_tilt()
    await socket.drain_desk()
    assert len(desk.monitor_calls) == 1


@pytest.mark.asyncio
async def test_a_calm_evening_never_wakes_the_desk(socket: GameSocket) -> None:
    from tilt.tracker import TiltTracker

    desk = FakeDesk()
    socket.desk = desk
    socket.tilt = TiltTracker()
    await socket.push_tilt()
    await socket.drain_desk()
    assert desk.monitor_calls == []


@pytest.mark.asyncio
async def test_a_broken_desk_does_not_break_the_tilt_frame(socket: GameSocket) -> None:
    class Exploding:
        async def monitor(self, now_ms: int) -> Any:
            raise RuntimeError("no network")

    socket.desk = Exploding()
    tilted(socket, band="hot")
    socket.tilt.cooldown_until = None

    await socket.push_tilt()
    await socket.drain_desk()
    assert last(socket, "tilt")["p"]["band"] in ("hot", "scorched")


@pytest.mark.asyncio
async def test_the_desk_only_ever_sees_tilt_aggregates(socket: GameSocket) -> None:
    """Component values and raw pad frames stay on the box; the desk gets what the HUD shows."""
    view: dict[str, Any] = {}
    socket.tilt_view = view
    tilted(socket, band="hot")
    socket.tilt.cooldown_until = None
    await socket.push_tilt()

    assert set(view) == {"band", "score", "top"}
    assert all(isinstance(line, str) for line in view["top"])
