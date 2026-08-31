"""Economic calendar: the Forex Factory weekly JSON, cached and treated as untrusted.

The feed is a third-party file fetched over the network, so it is parsed with Pydantic, capped in
length, and never allowed to fail the evening. Three degradation steps, in order: the live fetch,
the on-disk cache (up to a week old — a stale calendar still knows when NFP is), then a local
`calendar.yaml` the player controls. `source: off` skips straight to the file.
"""

from __future__ import annotations

import json
import logging
import time
import urllib.request
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal
from zoneinfo import ZoneInfo

import yaml
from pydantic import BaseModel, ConfigDict, Field, ValidationError

log = logging.getLogger(__name__)

FF_WEEKLY_URL = "https://nfs.faireconomy.media/ff_calendar_thisweek.json"

# Refetch no more than once every six hours; the file is weekly.
CACHE_TTL_S = 6 * 3600

# A stale cache still knows when the big events are, so it is preferred over having nothing.
STALE_LIMIT_S = 7 * 24 * 3600

# Untrusted input: a feed that suddenly returns 100k rows does not get to exhaust memory.
MAX_EVENTS = 500

FETCH_TIMEOUT_S = 10

Impact = Literal["Low", "Medium", "High", "Holiday", "Non-Economic"]
IMPACT_ORDER = {"Non-Economic": 0, "Holiday": 0, "Low": 1, "Medium": 2, "High": 3}

# Inside this window before a high-impact print, the desk's answer is "wait".
HIGH_IMPACT_GUARD_S = 900


class RawEvent(BaseModel):
    """One row of the feed, validated before anything else touches it."""

    model_config = ConfigDict(extra="ignore")

    title: str = Field(max_length=200)
    country: str = Field(max_length=8)
    date: str = Field(max_length=64)
    impact: str = Field(default="Low", max_length=32)
    forecast: str | None = Field(default=None, max_length=64)
    previous: str | None = Field(default=None, max_length=64)


@dataclass(frozen=True)
class CalendarEvent:
    """A normalised event, in UTC milliseconds plus the session's own zone for display."""

    title: str
    currency: str
    impact: str
    ts_ms: int
    local: str

    def t_minus_s(self, now_ms: int) -> float:
        return (self.ts_ms - now_ms) / 1000


def _parse_ts(value: str) -> int | None:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=UTC)
    return int(parsed.timestamp() * 1000)


def normalise(rows: list[dict[str, Any]], timezone: str) -> list[CalendarEvent]:
    """Validate, cap, and convert. A row that does not parse is dropped, not fatal."""
    zone = ZoneInfo(timezone)
    events: list[CalendarEvent] = []
    for row in rows[:MAX_EVENTS]:
        try:
            raw = RawEvent.model_validate(row)
        except ValidationError:
            continue
        ts_ms = _parse_ts(raw.date)
        if ts_ms is None:
            continue
        local = datetime.fromtimestamp(ts_ms / 1000, tz=zone)
        events.append(
            CalendarEvent(
                title=raw.title,
                currency=raw.country.upper(),
                impact=raw.impact,
                ts_ms=ts_ms,
                local=local.strftime("%a %H:%M"),
            )
        )
    return sorted(events, key=lambda e: e.ts_ms)


@dataclass
class CalendarCache:
    """Fetch, cache, and degrade. Never raises at the caller: an offline calendar is a state."""

    cache_path: Path
    timezone: str
    source: Literal["ff_weekly", "off"] = "ff_weekly"
    fallback_path: Path | None = None
    url: str = FF_WEEKLY_URL

    _events: list[CalendarEvent] | None = None
    _fetched_at: float = 0.0
    status: str = "cold"

    def _fetch(self) -> list[dict[str, Any]] | None:
        try:
            with urllib.request.urlopen(self.url, timeout=FETCH_TIMEOUT_S) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except Exception as exc:
            log.warning("calendar fetch failed (%s); falling back", exc)
            return None
        return payload if isinstance(payload, list) else None

    def _read_cache(self) -> list[dict[str, Any]] | None:
        if not self.cache_path.exists():
            return None
        age = time.time() - self.cache_path.stat().st_mtime
        if age > STALE_LIMIT_S:
            return None
        try:
            return json.loads(self.cache_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return None

    def _read_fallback(self) -> list[dict[str, Any]] | None:
        if self.fallback_path is None or not self.fallback_path.exists():
            return None
        try:
            data = yaml.safe_load(self.fallback_path.read_text(encoding="utf-8"))
        except (OSError, yaml.YAMLError):
            return None
        return data.get("events", []) if isinstance(data, dict) else None

    def events(self, now: float | None = None) -> list[CalendarEvent]:
        """Current events, refetching at most every `CACHE_TTL_S`."""
        now = time.time() if now is None else now
        if self._events is not None and now - self._fetched_at < CACHE_TTL_S:
            return self._events

        rows: list[dict[str, Any]] | None = None
        if self.source == "ff_weekly":
            rows = self._fetch()
            if rows is not None:
                self.status = "live"
                self.cache_path.parent.mkdir(parents=True, exist_ok=True)
                self.cache_path.write_text(json.dumps(rows), encoding="utf-8")
            else:
                rows = self._read_cache()
                if rows is not None:
                    self.status = "cached"

        if rows is None:
            rows = self._read_fallback()
            self.status = "file" if rows is not None else "offline"

        self._events = normalise(rows or [], self.timezone)
        self._fetched_at = now
        return self._events

    def upcoming(
        self,
        now_ms: int,
        *,
        currencies: list[str] | None = None,
        min_impact: str = "High",
        limit: int = 5,
    ) -> list[CalendarEvent]:
        """Events still ahead of us, filtered to what this basket actually cares about."""
        threshold = IMPACT_ORDER.get(min_impact, 3)
        wanted = {c.upper() for c in (currencies or [])}
        out = [
            event
            for event in self.events()
            if event.ts_ms >= now_ms
            and IMPACT_ORDER.get(event.impact, 0) >= threshold
            and (not wanted or event.currency in wanted)
        ]
        return out[:limit]

    def guard(self, now_ms: int, currencies: list[str] | None = None) -> CalendarEvent | None:
        """The high-impact print close enough that the honest advice is to wait."""
        for event in self.upcoming(now_ms, currencies=currencies, min_impact="High", limit=1):
            if 0 <= event.t_minus_s(now_ms) <= HIGH_IMPACT_GUARD_S:
                return event
        return None


def currencies_for(symbols: list[str]) -> list[str]:
    """Which currencies a symbol basket exposes you to. `XAUUSD` is gold plus the dollar."""
    out: set[str] = set()
    for symbol in symbols:
        name = symbol.upper()
        if name.startswith("XAU"):
            out.update({"USD", "XAU"})
            out.add(name[3:6])
        else:
            out.add(name[:3])
            out.add(name[3:6])
    return sorted(c for c in out if c)
