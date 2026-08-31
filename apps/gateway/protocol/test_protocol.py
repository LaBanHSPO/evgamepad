"""Protocol v1 round-trips and the guarantees the envelope is supposed to enforce."""

from __future__ import annotations

import json

import pytest

from protocol import (
    CATALOG,
    MAX_FRAME_BYTES,
    Envelope,
    ProtocolError,
    decode,
    new_cid,
    validate_frame,
)


def frame(t: str, ch: str, p: dict, *, cid: str | None = None) -> Envelope:
    return Envelope(t=t, seq=1, ts=1_700_000_000_000, ch=ch, cid=cid, p=p)


def test_every_catalog_type_round_trips() -> None:
    """Encode -> decode must return an identical envelope for every frozen message type."""
    for t, entry in CATALOG.items():
        env = frame(t, entry.ch, {}, cid=new_cid())
        assert decode(env.encode()) == env, t


def test_intent_open_round_trip() -> None:
    cid = new_cid()
    env = frame(
        "intent.open",
        "orders",
        {
            "sym": "XAUUSD",
            "side": "buy",
            "type": "market",
            "lots": 0.01,
            "relativeSl": 200000,
            "clutch": True,
            "armedAt": 1_700_000_000_000,
        },
        cid=cid,
    )
    msg = validate_frame(decode(env.encode()), expect="c2s")
    assert msg.lots == 0.01
    assert msg.relativeSl == 200000
    assert msg.relativeTp is None


def test_pad_telemetry_uses_the_wire_alias_for_from() -> None:
    """`from` is a Python keyword; the wire name still has to be `from`."""
    env = frame(
        "pad.telemetry",
        "session",
        {
            "ts": 1_700_000_000_000,
            "from": "IDLE",
            "to": "ARM",
            "clutchMs": 900,
            "armMs": 300,
            "clutchCycles": 2,
            "armFlips": 1,
            "btnRateHz": 3.5,
            "lotStepsSince": 0,
        },
    )
    msg = validate_frame(env, expect="c2s")
    assert msg.from_ == "IDLE"
    assert json.loads(msg.model_dump_json(by_alias=True))["from"] == "IDLE"


def test_intent_without_clutch_is_refused() -> None:
    """`clutch: true` is structural: an intent cannot be expressed without it."""
    env = frame("intent.open", "orders", {"sym": "XAUUSD", "side": "buy", "lots": 0.01,
                                          "armedAt": 1}, cid=new_cid())
    with pytest.raises(ProtocolError):
        validate_frame(env, expect="c2s")

    env_false = frame("intent.close", "orders", {"positionId": 1, "clutch": False, "armedAt": 1})
    with pytest.raises(ProtocolError):
        validate_frame(env_false, expect="c2s")


def test_unknown_type_and_wrong_channel_are_refused() -> None:
    with pytest.raises(ProtocolError, match="unknown message type"):
        validate_frame(frame("intent.yolo", "orders", {}))
    with pytest.raises(ProtocolError, match="rides"):
        validate_frame(frame("quote", "orders", {"sym": "XAUUSD", "bid": 1, "ask": 2, "ts": 1}))


def test_direction_is_enforced() -> None:
    """A client cannot claim to be the gateway by sending a server message type."""
    with pytest.raises(ProtocolError, match="is s2c"):
        validate_frame(frame("order.ack", "orders", {}), expect="c2s")


def test_unknown_payload_field_is_refused() -> None:
    env = frame("ping", "session", {"visible": True, "pad": True, "clutch": False, "extra": 1})
    with pytest.raises(ProtocolError, match="payload invalid"):
        validate_frame(env, expect="c2s")


def test_cid_must_be_a_ulid() -> None:
    with pytest.raises(ValueError, match="ULID"):
        frame("ping", "session", {}, cid="not-a-ulid")


def test_frame_cap_is_enforced_both_ways() -> None:
    big = frame("ai.advice", "ai", {"kind": "coach", "text": "x" * (MAX_FRAME_BYTES + 1), "ts": 1})
    with pytest.raises(ProtocolError, match="exceeds"):
        big.encode()
    with pytest.raises(ProtocolError, match="exceeds"):
        decode("x" * (MAX_FRAME_BYTES + 1))


def test_a_future_protocol_version_is_refused() -> None:
    raw = json.dumps({"v": 2, "t": "ping", "seq": 1, "ts": 1, "ch": "session", "p": {}})
    with pytest.raises(ValueError, match="unsupported protocol version"):
        decode(raw)


def test_journal_layer_is_already_frozen() -> None:
    """Phases 7-14 must not need a v2 migration to say anything they already plan to say."""
    for t in ("pad.telemetry", "voice.begin", "voice.cancel", "journal.memo.link", "grade.answer",
              "playbook.select", "voice.transcript", "voice.state", "tilt", "grade",
              "playbook.list", "score.session"):
        assert t in CATALOG, t
    assert {e.ch for e in CATALOG.values()} <= {"quotes", "orders", "session", "ai", "voice"}
