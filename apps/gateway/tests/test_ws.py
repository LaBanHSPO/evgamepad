"""The socket path end to end, without a browser or a broker."""

from __future__ import annotations

import json

import pytest
import yaml

from apps.gateway.api.gateway import Gateway
from apps.gateway.api.ws import WsSession
from apps.gateway.broker import NotWiredBroker
from apps.gateway.config import Config
from apps.gateway.journal.writer import JournalWriter
from apps.gateway.protocol import CATALOG, new_cid, now_ms

TOKEN = "test-token"


class Client:
    """Collects what the gateway sent, decoded."""

    def __init__(self) -> None:
        self.sent: list[dict] = []

    async def send(self, raw: str) -> None:
        self.sent.append(json.loads(raw))

    def types(self) -> list[str]:
        return [f["t"] for f in self.sent]

    def last(self, t: str) -> dict | None:
        return next((f for f in reversed(self.sent) if f["t"] == t), None)


@pytest.fixture
def session(tmp_path, monkeypatch):
    cfg = Config.model_validate(yaml.safe_load(open("config/default.yaml")))
    cfg.db_path = str(tmp_path / "ev.sqlite3")
    monkeypatch.setenv("EV_WS_TOKEN", TOKEN)
    gw = Gateway(cfg, broker=NotWiredBroker(), journal=JournalWriter(cfg.db_path))
    client = Client()
    return WsSession(gw, client.send), client, gw


def frame(t, p, cid=None, seq=1):
    return json.dumps({"v": 1, "t": t, "seq": seq, "ts": now_ms(),
                       "ch": CATALOG[t].ch, "cid": cid, "p": p})


async def hello(session, client):
    await session.handle(frame("hello", {"token": TOKEN}))
    return client.last("welcome")


def intent(t, p, cid=None):
    return frame(t, {**p, "clutch": True, "armedAt": now_ms()}, cid or new_cid())


async def test_hello_returns_welcome_and_session(session):
    s, c, _ = session
    w = await hello(s, c)
    assert w["p"]["tz"] == "Asia/Ho_Chi_Minh"
    assert w["p"]["symbols"] == ["XAUUSD", "EURUSD", "GBPUSD", "USDJPY"]
    assert "session" in c.types()


async def test_bad_token_is_refused(session):
    s, c, _ = session
    await s.handle(frame("hello", {"token": "wrong"}))
    assert c.last("error")["p"]["reason"] == "bad_token"
    assert not s.authed


async def test_nothing_but_hello_works_unauthenticated(session):
    s, c, _ = session
    await s.handle(frame("ping", {"clutch": False}))
    assert c.last("error")["p"]["reason"] == "unauthenticated"


async def test_seq_is_monotonic(session):
    s, c, _ = session
    await hello(s, c)
    for _ in range(5):
        await s.handle(frame("ping", {"clutch": True}))
    seqs = [f["seq"] for f in c.sent]
    assert seqs == sorted(seqs) == list(range(1, len(seqs) + 1))


async def test_resync_replays_only_what_was_missed(session):
    s, c, _ = session
    await hello(s, c)
    for _ in range(3):
        await s.handle(frame("ping", {"clutch": True}))
    mark = len(c.sent)
    from_seq = c.sent[1]["seq"]
    await s.handle(frame("resync", {"fromSeq": from_seq}))
    replayed = c.sent[mark:]
    assert replayed
    assert all(f["seq"] > from_seq for f in replayed)


async def test_resync_beyond_the_replay_depth_resnaps(session):
    s, c, _ = session
    await hello(s, c)
    await s.handle(frame("resync", {"fromSeq": 0}))
    # seq 0 predates nothing here, so it replays; a genuine gap is the case
    # below, where the client claims a seq older than the buffer holds.
    s._replay.clear()
    s.seq = 10_000
    mark = len(c.sent)
    await s.handle(frame("resync", {"fromSeq": 5}))
    assert c.sent[mark]["t"] == "maint"
    assert c.sent[mark]["p"]["reason"] == "resync_gap"


async def test_an_oversize_frame_gets_an_error_not_a_crash(session):
    s, c, _ = session
    await hello(s, c)
    await s.handle(json.dumps({"v": 1, "t": "ping", "seq": 1, "ts": 1,
                               "ch": "session", "p": {"padSeq": "x" * 70000}}))
    assert c.last("error")["p"]["reason"] == "frame_too_large"


async def test_open_is_refused_with_not_wired_until_phase_two(session):
    s, c, gw = session
    gw.state.locked = False
    await hello(s, c)
    gw.session.is_open = lambda ms: True  # step outside the evening window
    await s.handle(intent("intent.open", {"sym": "XAUUSD", "side": "buy", "lots": 0.01}))
    rej = c.last("order.reject")
    assert rej["p"]["reason"] == "not_wired"


async def test_duplicate_cid_does_not_double(session):
    s, c, gw = session
    await hello(s, c)
    gw.session.is_open = lambda ms: True
    cid = new_cid()
    raw = intent("intent.open", {"sym": "XAUUSD", "side": "buy", "lots": 0.01}, cid)
    await s.handle(raw)
    await s.handle(raw)
    reasons = [f["p"]["reason"] for f in c.sent if f["t"] == "order.reject"]
    assert reasons == ["not_wired", "duplicate_cid"]
    assert len(gw.broker.calls) == 1, "the broker was called twice for one cid"


async def test_out_of_session_open_is_refused_but_close_is_not(session):
    s, c, gw = session
    await hello(s, c)
    gw.session.is_open = lambda ms: False
    await s.handle(intent("intent.open", {"sym": "XAUUSD", "side": "buy", "lots": 0.01}))
    assert c.last("order.reject")["p"]["reason"] == "session_closed"

    await s.handle(intent("intent.close", {"positionId": 1}))
    assert c.last("order.reject")["p"]["reason"] == "not_wired"


async def test_dead_man_locks_opens_and_never_a_panic(session):
    s, c, gw = session
    await hello(s, c)
    gw.session.is_open = lambda ms: True
    # handle() refreshes last_client_ms, so stale it after the frame is decoded
    # by driving the gateway directly -- the socket path is covered above.
    from apps.gateway.protocol.catalog import IntentOpen, IntentPanic

    gw.state.last_client_ms = now_ms() - 30_000
    ok, reason, _ = await gw.handle_intent(
        "intent.open", new_cid(),
        IntentOpen(sym="XAUUSD", side="buy", lots=0.01, clutch=True, armedAt=now_ms()),
    )
    assert (ok, reason) == (False, "dead_man")

    gw.state.last_client_ms = now_ms() - 30_000
    ok, reason, _ = await gw.handle_intent(
        "intent.panic", new_cid(), IntentPanic(clutch=True, armedAt=now_ms())
    )
    assert reason != "dead_man"


async def test_panic_locks_the_session(session):
    s, c, gw = session
    await hello(s, c)
    await s.handle(intent("intent.panic", {}))
    assert gw.state.locked is True


async def test_ai_ask_is_disabled_until_phase_four(session):
    s, c, _ = session
    await hello(s, c)
    await s.handle(frame("ai.ask", {"kind": "advise", "sym": "XAUUSD"}))
    assert c.last("ai.advice")["p"]["disabled"] is True


async def test_a_refused_intent_does_not_burn_its_cid(session):
    """A rejected fire must be retryable with the same cid once the reason
    clears -- reserving on refusal would strand it."""
    s, c, gw = session
    await hello(s, c)
    gw.session.is_open = lambda ms: False
    cid = new_cid()
    await s.handle(intent("intent.open", {"sym": "XAUUSD", "side": "buy", "lots": 0.01}, cid))
    assert gw.journal.cid_state(cid) is None
