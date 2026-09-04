"""Live arcade HUD snapshot.

A REST picture of what the matrix and city artboards need to paint **without waiting on the
socket**. Quotes come from the broker's in-memory book (never synthesised). Positions are a
best-effort cached reconcile with a hard timeout so a stuck cTrader call cannot hang the HUD.
The payload is always 200: a missing figure is `null`, never a fake price.
"""

from __future__ import annotations

import asyncio
import sqlite3
import time
from datetime import datetime, timedelta
from typing import Any

from broker.volume import scale_price, volume_to_lots
from config import AppConfig
from risk.session import SessionWindow


def remaining_s(window: SessionWindow, now_ms: int) -> int:
    """Seconds until the window closes. Zero when it is already closed or not a trading day."""
    now = window.local(now_ms)
    if not window.is_open(now_ms):
        return 0
    end = datetime.combine(now.date(), window.end, tzinfo=now.tzinfo)
    if window.start > window.end and now.time() >= window.start:
        end = end + timedelta(days=1)
    return max(0, int((end - now).total_seconds()))


def duration_s(window: SessionWindow) -> int:
    """Length of the configured window, in seconds."""
    start = window.start.hour * 3600 + window.start.minute * 60 + window.start.second
    end = window.end.hour * 3600 + window.end.minute * 60 + window.end.second
    if end <= start:
        end += 24 * 3600
    return end - start


def format_clock(seconds: int) -> str:
    total = max(0, int(seconds))
    hours, rem = divmod(total, 3600)
    minutes, secs = divmod(rem, 60)
    if hours:
        return f"{hours}:{minutes:02d}:{secs:02d}"
    return f"{minutes}:{secs:02d}"


def _quote_row(raw: Any) -> dict[str, float | int | None]:
    bid = ask = ts = None
    if raw is None:
        return {"bid": None, "ask": None, "mid": None, "spread": None, "ts": None}
    if hasattr(raw, "bid"):
        bid = scale_price(int(raw.bid))
        ask = scale_price(int(raw.ask))
        ts = int(getattr(raw, "ts_ms", 0) or 0)
    elif isinstance(raw, dict):
        bid = float(raw["bid"]) if raw.get("bid") is not None else None
        ask = float(raw["ask"]) if raw.get("ask") is not None else None
        ts = int(raw.get("ts") or raw.get("ts_ms") or 0)
    spread = None if bid is None or ask is None else round(ask - bid, 6)
    mid = None if bid is None or ask is None else round((bid + ask) / 2, 6)
    return {"bid": bid, "ask": ask, "mid": mid, "spread": spread, "ts": ts or None}


def _cached_quotes(broker: Any) -> dict[str, Any]:
    return getattr(broker, "quotes", None) or {}


def _lots(broker: Any, symbol: str | None, volume: Any, lots: Any) -> float | None:
    if lots is not None:
        try:
            return float(lots)
        except (TypeError, ValueError):
            return None
    specs = getattr(broker, "specs", None) or {}
    spec = specs.get(symbol) if symbol else None
    if spec is None or volume is None:
        return None
    try:
        return volume_to_lots(int(volume), spec)
    except Exception:
        return None


async def _positions(broker: Any, timeout_s: float = 0.4) -> list[dict[str, Any]]:
    snap = broker.snapshot() if hasattr(broker, "snapshot") else {}
    if not isinstance(snap, dict) or not snap.get("connected"):
        return []
    try:
        rows = await asyncio.wait_for(broker.positions(), timeout=timeout_s)
    except Exception:
        return []
    out: list[dict[str, Any]] = []
    for row in rows or []:
        symbol = row.get("symbol") or row.get("sym")
        volume = row.get("volume")
        out.append({
            "positionId": row.get("positionId"),
            "symbol": symbol,
            "side": row.get("side"),
            "lots": _lots(broker, symbol, volume, row.get("lots")),
            "volume": volume,
            "entry": row.get("entry") or row.get("price"),
            "sl": row.get("sl"),
            "tp": row.get("tp"),
            "openedAt": row.get("openedAt"),
        })
    return out


def _hi_score(db_path: Any) -> int:
    try:
        conn = sqlite3.connect(db_path)
        row = conn.execute(
            "SELECT MAX(stood_down_count) FROM session_process"
        ).fetchone()
        conn.close()
    except sqlite3.Error:
        return 0
    return int(row[0] or 0) if row else 0


def _declined(journal: Any, session_id: str) -> int:
    try:
        today = journal.today(session_id)
    except Exception:
        return 0
    checkin = today.get("checkin") or {}
    return int(checkin.get("declined") or 0)


async def snapshot(
    *,
    config: AppConfig,
    broker: Any,
    sentinel: Any,
    journal: Any,
    now_ms: int | None = None,
) -> dict[str, Any]:
    now = now_ms if now_ms is not None else int(time.time() * 1000)
    window = SessionWindow.from_config(
        config.timezone, config.session.days, config.session.start, config.session.end,
    )
    session_id = window.local(now).strftime("%Y-%m-%d")
    remaining = remaining_s(window, now)
    total = duration_s(window)
    open_now = window.is_open(now)
    burned = 0 if (not open_now or total <= 0) else round(100 * (total - remaining) / total)
    quotes = _cached_quotes(broker)
    first_sym = config.symbols[0].name if config.symbols else "XAUUSD"
    first_quote = _quote_row(quotes.get(first_sym))
    tick = None
    if sentinel is not None and first_quote["bid"] is not None and first_quote["ask"] is not None:
        try:
            tick = sentinel.tick(
                symbol=first_sym,
                bid=float(first_quote["bid"]),
                ask=float(first_quote["ask"]),
                now_ms=now,
                session_remaining_s=remaining,
                locked=False,
            )
        except Exception:
            tick = None

    symbols = []
    for spec in config.symbols:
        q = _quote_row(quotes.get(spec.name))
        symbols.append({
            "name": spec.name,
            "maxLots": spec.max_lots,
            "defaultLots": spec.default_lots,
            "lotStep": spec.lot_step,
            "stop": config.risk.default_stop.get(spec.name),
            **q,
        })

    broker_snap = broker.snapshot() if hasattr(broker, "snapshot") else {}
    if not isinstance(broker_snap, dict):
        broker_snap = {}
    positions = await _positions(broker)
    sentinel_view = None if tick is None else tick.desk_payload()

    return {
        "mode": config.mode,
        "broker": {
            "connected": bool(broker_snap.get("connected")),
            "reason": broker_snap.get("reason") or broker_snap.get("last_error"),
        },
        "session": {
            "id": session_id,
            "open": open_now,
            "timezone": config.timezone,
            "start": config.session.start,
            "end": config.session.end,
            "remainingS": remaining,
            "durationS": total,
            "windowBurnedPct": burned,
            "clock": format_clock(remaining),
        },
        "risk": {
            "maxPositions": config.risk.max_positions,
            "maxDayLossUsd": config.risk.max_daily_loss_usd,
            "rUsd": config.risk.r_unit_usd,
            "positions": len(positions),
        },
        "symbols": symbols,
        "positions": positions,
        "pnl": {
            "openPnl": None,
            "dayPnl": None,
        },
        "sentinel": sentinel_view,
        "standDowns": _declined(journal, session_id) if journal is not None else 0,
        "hiScore": _hi_score(config.paths.db),
    }
