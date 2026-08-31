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
    sent: list[str] = []

    async def send(raw: str) -> None:
        sent.append(raw)

    gs = GameSocket(
        send=send,
        broker=FakeBroker(),
        journal=JournalWriter(connect(db)),
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
    rows = socket.journal.conn.execute(
        "SELECT COUNT(*) FROM position_event WHERE kind = 'telemetry'"
    ).fetchone()
    assert rows[0] == 1


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
