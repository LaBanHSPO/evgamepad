"""Denormalise one trade's window into a flat event list, at freeze time.

This is what makes replay coaching rather than charting. The bars show what the market did; these
show what *you* did — the arm you cancelled forty seconds before you fired, the stop you moved, the
band you crossed. None of it is reconstructible later at acceptable cost, because the sources are
keyed four different ways: pad telemetry by session, broker events by position, signals by session,
tilt samples by session. Joining them once, at freeze, is the whole point.

Everything here is a **read**. The tape row is the only thing written, and it is written once.
"""

from __future__ import annotations

import json
import logging
import sqlite3
from typing import Any

log = logging.getLogger(__name__)

# The pad phases that mean an arm began, and the ones an arm can end in without a fire.
ARMED = "ARMED"
FIRE = "FIRE"


def denormalise(
    conn: sqlite3.Connection, *, session_id: str | None, position_id: int | None,
    from_ms: int, to_ms: int,
) -> list[dict[str, Any]]:
    """Every event inside the tape window, oldest first.

    A source that is absent contributes nothing rather than failing the freeze — a tape with fewer
    event kinds still replays, and a trade with no tape at all cannot be reviewed.
    """
    events: list[dict[str, Any]] = []
    for collect in (_pad, _position, _signals, _tilt):
        try:
            events.extend(collect(conn, session_id=session_id, position_id=position_id,
                                  from_ms=from_ms, to_ms=to_ms))
        except sqlite3.Error:
            log.exception("replay events: one source failed; freezing the tape without it")
    events.sort(key=lambda e: e["ts"])
    return events


def _pad(conn: sqlite3.Connection, *, session_id: str | None, position_id: int | None,
         from_ms: int, to_ms: int) -> list[dict[str, Any]]:
    """Arms, cancels and fires, from the 1 Hz telemetry the client already sends."""
    if session_id is None:
        return []
    rows = conn.execute(
        "SELECT ts, from_phase, to_phase, reason, symbol, lots FROM pad_event "
        "WHERE session_id = ? AND ts BETWEEN ? AND ? ORDER BY ts",
        (session_id, from_ms, to_ms),
    ).fetchall()

    out: list[dict[str, Any]] = []
    for ts, from_phase, to_phase, reason, symbol, lots in rows:
        if to_phase == ARMED:
            out.append({"ts": ts, "kind": "arm", "label": _sized("armed", symbol, lots)})
        elif to_phase == FIRE:
            out.append({"ts": ts, "kind": "fire", "label": _sized("fired", symbol, lots)})
        elif from_phase == ARMED:
            # An arm that ended anywhere but FIRE is a trade you decided not to take. That is a
            # result, and the rail is the only place it is ever visible.
            out.append({"ts": ts, "kind": "cancel",
                        "label": f"stood down ({reason})" if reason else "stood down"})
    return out


def _sized(verb: str, symbol: str | None, lots: float | None) -> str:
    if symbol and lots:
        return f"{verb} {lots:g} {symbol}"
    return verb


def _position(conn: sqlite3.Connection, *, session_id: str | None, position_id: int | None,
              from_ms: int, to_ms: int) -> list[dict[str, Any]]:
    """The broker's own acknowledgement and any stop move, for this position only."""
    if position_id is None:
        return []
    rows = conn.execute(
        "SELECT kind, payload, ts FROM position_event WHERE position_id = ? ORDER BY ts, id",
        (position_id,),
    ).fetchall()

    out: list[dict[str, Any]] = []
    for kind, raw, ts in rows:
        payload = _loads(raw)
        if kind == "fill":
            out.append({"ts": ts, "kind": "ack",
                        "label": f"filled at {payload.get('entry')}",
                        "price": payload.get("entry")})
        elif kind == "amend":
            stop = payload.get("sl")
            out.append({"ts": ts, "kind": "sl_move",
                        "label": "stop removed" if stop is None else f"stop to {stop}",
                        "price": stop})
    return out


def _signals(conn: sqlite3.Connection, *, session_id: str | None, position_id: int | None,
             from_ms: int, to_ms: int) -> list[dict[str, Any]]:
    """Method tags and TradingView hints. Both are descriptions; neither ever placed an order."""
    if session_id is None:
        return []
    rows = conn.execute(
        "SELECT kind, text, ts FROM signal_item WHERE session_id = ? AND ts BETWEEN ? AND ? "
        "ORDER BY ts",
        (session_id, from_ms, to_ms),
    ).fetchall()
    mapped = {"volman": "volman_tag", "tv": "tv_signal"}
    return [{"ts": ts, "kind": mapped[kind], "label": text}
            for kind, text, ts in rows if kind in mapped]


def _tilt(conn: sqlite3.Connection, *, session_id: str | None, position_id: int | None,
          from_ms: int, to_ms: int) -> list[dict[str, Any]]:
    """Only the crossings. A band held for ten minutes is one event, not six hundred."""
    if session_id is None:
        return []
    rows = conn.execute(
        "SELECT ts, band, top_driver FROM tilt_sample WHERE session_id = ? AND ts BETWEEN ? AND ? "
        "ORDER BY ts",
        (session_id, from_ms, to_ms),
    ).fetchall()

    out: list[dict[str, Any]] = []
    previous: str | None = None
    for ts, band, driver in rows:
        if band != previous:
            out.append({"ts": ts, "kind": "tilt_band_change",
                        "label": f"tilt {band}" + (f" · {driver}" if driver else ""),
                        "band": band})
            previous = band
    return out


def _loads(raw: str | None) -> dict[str, Any]:
    if not raw:
        return {}
    try:
        parsed = json.loads(raw)
    except (TypeError, ValueError):
        return {}
    return parsed if isinstance(parsed, dict) else {}


def normalise(stored: Any) -> list[dict[str, Any]]:
    """Read any tape row's events as the flat shape, including pre-phase-10 rows.

    Phase 2 froze `{kind, payload, ts}` straight from `position_event`. Those tapes are still
    replayable — a thinner rail is a better answer than a 500 on last month's trade.
    """
    if not isinstance(stored, list):
        return []
    out: list[dict[str, Any]] = []
    for item in stored:
        if not isinstance(item, dict) or "ts" not in item:
            continue
        if "label" in item:
            out.append(item)
            continue
        payload = item.get("payload") if isinstance(item.get("payload"), dict) else {}
        kind = str(item.get("kind", "event"))
        out.append({"ts": item["ts"], "kind": kind, "label": kind, **payload})
    out.sort(key=lambda e: e["ts"])
    return out
