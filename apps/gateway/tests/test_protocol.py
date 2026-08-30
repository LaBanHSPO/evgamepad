"""Protocol v1 round-trips and the rejections that must never reach a handler."""

from __future__ import annotations

import json

import pytest

from apps.gateway.protocol import (
    CATALOG,
    MAX_FRAME_BYTES,
    ProtocolError,
    catalog,
    decode,
    encode,
    new_cid,
)


CID = "01JBXQ4T7ZK9M2N5P8R3V6W1YZ"


def frame(t: str, p: dict, *, cid: str | None = None, seq: int = 1, v: int = 1) -> str:
    return json.dumps(
        {"v": v, "t": t, "seq": seq, "ts": 1_700_000_000_000, "ch": CATALOG[t].ch,
         "cid": cid, "p": p}
    )


#: One sample per server->client type. Explicit rather than generated: a
#: generated sample proves the model can validate itself, while these also
#: pin the field names the HUD reads.
S2C_SAMPLES: dict[str, dict] = {
    "welcome": {"sessionId": "s", "seq": 0, "serverTs": 1, "tz": "Asia/Ho_Chi_Minh",
                "symbols": ["XAUUSD"], "resumed": False, "features": {"broker": False}},
    "pong": {"clutch": True, "serverTs": 1},
    "quote": {"sym": "XAUUSD", "bid": 2340.0, "ask": 2340.2, "ts": 1, "digits": 2},
    "candle": {"sym": "XAUUSD", "tf": "M5", "ts": 1, "o": 1, "h": 2, "l": 0.5,
               "c": 1.5, "closed": True},
    "order.ack": {"cid": CID, "sym": "XAUUSD", "side": "buy", "lots": 0.01,
                  "price": 2340.0, "ts": 1, "orderId": 9, "positionId": 8},
    "order.reject": {"cid": CID, "reason": "cooldown", "detail": "tilt"},
    "order.upd": {"cid": CID, "positionId": 8, "status": "closed", "ts": 1},
    "pos.snap": {"ts": 1, "positions": [
        {"positionId": 8, "sym": "XAUUSD", "side": "sell", "lots": 0.01,
         "entry": 2340.0, "openedAt": 1, "pnl": -3.0, "rMultiple": -1.5}]},
    "pnl": {"ts": 1, "balance": 10000.0, "equity": 9990.0, "openPnl": -10.0,
            "dayPnl": -10.0},
    "session": {"state": "open", "opensAllowed": True, "tz": "Asia/Ho_Chi_Minh",
                "startsAt": 1, "endsAt": 2},
    "risk": {"locked": False, "reasons": ["max_daily_loss"], "positions": 1,
             "maxPositions": 1, "dayLossUsd": 12.0, "maxDailyLossUsd": 200.0},
    "sentinel.tick": {"ts": 1, "sym": "XAUUSD", "spread": 0.4, "spreadOk": True,
                      "sessionOk": True, "newsOk": False, "band": "amber"},
    "news.item": {"id": "n1", "ts": 1, "title": "CPI", "impact": "high",
                  "currency": "USD"},
    "signal.item": {"id": "s1", "ts": 1, "source": "tradingview", "sym": "XAUUSD",
                    "tf": "M5", "text": "long"},
    "ai.advice": {"kind": "advise", "ts": 1, "text": "stand down", "disabled": False},
    "error": {"reason": "bad_token"},
    "maint": {"reason": "broker_down", "until": 2},
    "voice.transcript": {"voiceId": CID, "ok": True, "text": "took the retest",
                         "durMs": 4200, "sttMs": 900},
    "voice.state": {"busy": True, "queued": 2},
    "tilt": {"score": 0.7, "band": "hot", "top": ["armFlips"], "cooldownUntil": 9},
    "grade": {"cid": CID, "playbookId": "volman-m5", "required_pass": 3,
              "required_total": 4, "clean": False,
              "results": [{"ruleId": "r1", "required": True, "passed": False}]},
    "playbook.list": {"playbooks": [{"playbookId": "volman-m5", "name": "Volman M5",
                                     "ruleCount": 7, "requiredCount": 4}]},
    "score.session": {"axes": {"adherence": 0.8}, "total": 0.74, "na": ["review"],
                      "weightsVersion": "1"},
}


def test_every_server_type_has_a_sample():
    """A new message type must arrive with a round-trip sample, not slip in
    untested."""
    assert set(S2C_SAMPLES) == set(catalog.types_for("s2c"))


@pytest.mark.parametrize("t", sorted(S2C_SAMPLES))
def test_server_frames_round_trip(t):
    raw = encode(t, S2C_SAMPLES[t], seq=7)
    got_frame, got = decode(raw, direction="s2c")
    assert got_frame.t == t
    assert got_frame.seq == 7
    assert got_frame.ch == CATALOG[t].ch
    assert type(got) is catalog.model_for(t)
    dumped = got.model_dump(mode="json", by_alias=True, exclude_none=True)
    for key, value in S2C_SAMPLES[t].items():
        assert dumped[key] == value, key


def test_intent_open_round_trip():
    cid = new_cid()
    raw = frame(
        "intent.open",
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
    f, p = decode(raw)
    assert f.cid == cid
    assert p.sym == "XAUUSD"
    assert p.relativeSl == 200000
    assert p.relativeTp is None


def test_pad_telemetry_from_alias():
    """`from` is a Python keyword; the wire name still has to be `from`."""
    raw = frame("pad.telemetry", {"ts": 1, "from": "idle", "to": "arm", "clutchMs": 40})
    _, p = decode(raw)
    assert p.from_ == "idle"
    assert json.loads(encode("pad.telemetry", p, seq=1))["p"]["from"] == "idle"


def test_oversize_frame_refused_before_parsing():
    payload = json.dumps({"v": 1, "t": "ping", "seq": 1, "ts": 1, "ch": "session",
                          "p": {"pad": "x" * MAX_FRAME_BYTES}})
    with pytest.raises(ProtocolError) as exc:
        decode(payload)
    assert exc.value.reason == "frame_too_large"


@pytest.mark.parametrize(
    "raw,reason",
    [
        ("{", "bad_json"),
        ('{"v":1,"t":"ping","seq":1,"ts":1,"ch":"session","p":{},"extra":1}', "bad_envelope"),
        ('{"v":2,"t":"ping","seq":1,"ts":1,"ch":"session","p":{}}', "bad_version"),
        ('{"v":1,"t":"nope","seq":1,"ts":1,"ch":"session","p":{}}', "unknown_type"),
        ('{"v":1,"t":"welcome","seq":1,"ts":1,"ch":"session","p":{}}', "wrong_direction"),
        ('{"v":1,"t":"ping","seq":1,"ts":1,"ch":"quotes","p":{}}', "wrong_channel"),
    ],
)
def test_rejections(raw, reason):
    with pytest.raises(ProtocolError) as exc:
        decode(raw)
    assert exc.value.reason == reason


def test_intent_without_cid_is_refused():
    raw = frame("intent.panic", {"clutch": True, "armedAt": 1})
    with pytest.raises(ProtocolError) as exc:
        decode(raw)
    assert exc.value.reason == "missing_cid"


def test_intent_without_clutch_is_a_payload_error():
    """`clutch: Literal[True]` means a clutchless intent cannot even be built,
    let alone reach the risk layer."""
    raw = frame("intent.close", {"positionId": 1, "clutch": False, "armedAt": 1},
                cid=new_cid())
    with pytest.raises(ProtocolError) as exc:
        decode(raw)
    assert exc.value.reason == "bad_payload"


def test_unknown_field_is_refused():
    raw = frame("ping", {"clutch": True, "surprise": 1})
    with pytest.raises(ProtocolError) as exc:
        decode(raw)
    assert exc.value.reason == "bad_payload"


def test_cid_must_be_a_ulid():
    raw = frame("intent.panic", {"clutch": True, "armedAt": 1}, cid="not-a-ulid")
    with pytest.raises(ProtocolError) as exc:
        decode(raw)
    assert exc.value.reason == "bad_envelope"


def test_journal_layer_is_frozen_in_phase_one():
    """Phases 7-14 must find their messages already in the v1 catalog. Adding
    any of these later would be a v2 migration."""
    for t in (
        "voice.begin", "voice.cancel", "voice.transcript", "voice.state",
        "journal.memo.link", "pad.telemetry", "tilt", "grade", "grade.answer",
        "playbook.select", "playbook.list", "score.session",
    ):
        assert t in CATALOG, t
    assert CATALOG["voice.begin"].ch == "voice"
    # Telemetry, tilt, grades and score ride `session`; the journal layer adds
    # exactly one new channel.
    for t in ("pad.telemetry", "tilt", "grade", "score.session"):
        assert CATALOG[t].ch == "session"


def test_cooldown_reject_reason_is_reserved_for_phase_nine():
    from typing import get_args

    assert "cooldown" in get_args(catalog.RejectReason)
