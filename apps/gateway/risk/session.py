"""The trading window, in the configured IANA zone.

DST is the reason this is not arithmetic on a UTC timestamp: an 18:00 start in
`Asia/Ho_Chi_Minh` is a different UTC hour depending on the date in the zones it trades against.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, time
from zoneinfo import ZoneInfo

DAY_NAMES = ("mon", "tue", "wed", "thu", "fri", "sat", "sun")

# Market sessions in UTC, used to label a trade in the journal (phase 6 groups by them).
MARKET_SESSIONS = (("asia", 0, 8), ("london", 8, 13), ("ny", 13, 21), ("late", 21, 24))


def parse_hhmm(value: str) -> time:
    hour, minute = value.split(":")
    return time(int(hour), int(minute))


@dataclass(frozen=True)
class SessionWindow:
    """When the gateway will accept an open. Closes and panics ignore this entirely."""

    timezone: str
    days: frozenset[str]
    start: time
    end: time

    @classmethod
    def from_config(cls, timezone: str, days: list[str], start: str, end: str) -> SessionWindow:
        return cls(
            timezone=timezone,
            days=frozenset(d.lower() for d in days),
            start=parse_hhmm(start),
            end=parse_hhmm(end),
        )

    def local(self, ts_ms: int) -> datetime:
        return datetime.fromtimestamp(ts_ms / 1000, tz=ZoneInfo(self.timezone))

    def is_open(self, ts_ms: int) -> bool:
        """True when `ts_ms` falls inside the evening window on a trading day."""
        now = self.local(ts_ms)
        if DAY_NAMES[now.weekday()] not in self.days:
            return False
        current = now.time()
        if self.start <= self.end:
            return self.start <= current < self.end
        # A window that crosses midnight belongs to the day it started on.
        return current >= self.start or current < self.end

    def describe(self, ts_ms: int) -> str:
        now = self.local(ts_ms)
        return f"{DAY_NAMES[now.weekday()]} {now:%H:%M} {self.timezone}"


def market_session(ts_ms: int) -> str:
    """Which global session a trade was taken in, labelled from UTC."""
    hour = datetime.fromtimestamp(ts_ms / 1000, tz=UTC).hour
    for name, start, end in MARKET_SESSIONS:
        if start <= hour < end:
            return name
    return "late"
