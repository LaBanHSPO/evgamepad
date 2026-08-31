"""The sentinel: what the tape looks like right now, computed locally.

No LLM, no network, no API key. It paints the HUD strip every couple of seconds whether or not
the desk is reachable, which is the difference between a HUD that degrades and one that hangs.

Its most useful output is the honest one: `opportunity_quality`. A dead tape is supposed to look
like a dead tape, so that standing down feels like the correct read rather than a missed evening.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from method.volman import Candle, SetupTag, SetupTracker
from signals.calendar import CalendarCache, CalendarEvent

# Below this the strip says the spread is fine; above it, the tape is expensive.
SPREAD_OK = 0.6
SPREAD_WIDE = 1.0

# Component weights for the numeric quality score. They sum to 1.0.
QUALITY_WEIGHTS = {"spread": 0.3, "setup": 0.4, "session": 0.2, "calendar": 0.1}

# How a setup tag reads as opportunity. A range is not an opportunity; its break is.
SETUP_QUALITY = {
    "false_break": 1.0,
    "range_break": 0.85,
    "ema_pullback": 0.7,
    "buildup": 0.5,
    "range": 0.2,
}

# Buckets the HUD paints when the numeric score is unavailable (documented fallback).
QUALITY_BUCKETS = ((0.66, "live"), (0.33, "thin"), (0.0, "dead"))


@dataclass(frozen=True)
class SentinelTick:
    """One strip update. Matches the frozen `sentinel.tick` payload."""

    sym: str
    spread: float
    state: str
    ts: int
    quality: float
    quality_band: str
    components: dict[str, float]
    setup: str | None
    setup_side: str | None
    session_remaining_s: int | None
    next_event: str | None
    next_event_t_minus_s: float | None
    news_age_s: float | None
    locked: bool

    def payload(self) -> dict[str, Any]:
        """The wire shape. `sentinel.tick` is frozen at three fields, so the rest ride `state`'s
        siblings under the same message — the catalog validates only what it declared."""
        return {"sym": self.sym, "spread": self.spread, "state": self.state, "ts": self.ts}

    def desk_payload(self) -> dict[str, Any]:
        """The full picture, for the desk tab and the copilot's read-only tools."""
        return {
            "sym": self.sym,
            "spread": self.spread,
            "state": self.state,
            "quality": self.quality,
            "qualityBand": self.quality_band,
            "components": self.components,
            "setup": self.setup,
            "setupSide": self.setup_side,
            "sessionRemainingS": self.session_remaining_s,
            "nextEvent": self.next_event,
            "nextEventTMinusS": self.next_event_t_minus_s,
            "newsAgeS": self.news_age_s,
            "locked": self.locked,
        }


def band_for(quality: float) -> str:
    for threshold, name in QUALITY_BUCKETS:
        if quality >= threshold:
            return name
    return "dead"


def spread_state(spread: float, cap: float | None) -> str:
    """Spread against this symbol's own cap, not an absolute number."""
    limit = cap if cap and cap > 0 else SPREAD_WIDE
    ratio = spread / limit
    if ratio <= SPREAD_OK:
        return "tight"
    if ratio <= 1.0:
        return "fair"
    return "wide"


@dataclass
class SentinelEngine:
    """Holds the per-symbol trackers and builds a tick on demand."""

    timezone: str
    spread_caps: dict[str, float] = field(default_factory=dict)
    calendar: CalendarCache | None = None
    trackers: dict[str, SetupTracker] = field(default_factory=dict)
    last_news_ms: int | None = None

    def tracker(self, symbol: str) -> SetupTracker:
        return self.trackers.setdefault(symbol, SetupTracker())

    def observe(self, symbol: str, candles: list[Candle]) -> list[tuple[str, SetupTag]]:
        """Fold new M5 bars in. Returns setup born/died events for `signal.item`."""
        return self.tracker(symbol).update(candles)

    def tick(
        self,
        *,
        symbol: str,
        bid: float,
        ask: float,
        now_ms: int,
        session_remaining_s: int | None,
        locked: bool,
        currencies: list[str] | None = None,
    ) -> SentinelTick:
        spread = max(0.0, ask - bid)
        cap = self.spread_caps.get(symbol)
        state = spread_state(spread, cap)

        setup = self.tracker(symbol).current
        event = None
        if self.calendar is not None:
            upcoming = self.calendar.upcoming(now_ms, currencies=currencies, limit=1)
            event = upcoming[0] if upcoming else None

        components = self._components(state, setup, session_remaining_s, event, now_ms)
        quality = sum(components[name] * weight for name, weight in QUALITY_WEIGHTS.items())

        return SentinelTick(
            sym=symbol,
            spread=round(spread, 5),
            state=state,
            ts=now_ms,
            quality=round(quality, 3),
            quality_band=band_for(quality),
            components={k: round(v, 3) for k, v in components.items()},
            setup=setup.kind if setup else None,
            setup_side=setup.side if setup else None,
            session_remaining_s=session_remaining_s,
            next_event=event.title if event else None,
            next_event_t_minus_s=round(event.t_minus_s(now_ms), 1) if event else None,
            news_age_s=None if self.last_news_ms is None else (now_ms - self.last_news_ms) / 1000,
            locked=locked,
        )

    def _components(
        self,
        state: str,
        setup: SetupTag | None,
        session_remaining_s: int | None,
        event: CalendarEvent | None,
        now_ms: int,
    ) -> dict[str, float]:
        """Each component is 0-1 and independently readable, so a low score can be explained."""
        spread_component = {"tight": 1.0, "fair": 0.6, "wide": 0.1}.get(state, 0.5)
        setup_component = SETUP_QUALITY.get(setup.kind, 0.0) if setup else 0.0

        # A session with minutes left is not an opportunity, however good the setup looks.
        if session_remaining_s is None:
            session_component = 0.0
        elif session_remaining_s <= 0:
            session_component = 0.0
        else:
            session_component = min(1.0, session_remaining_s / 3600)

        calendar_component = 1.0
        if event is not None:
            t_minus = event.t_minus_s(now_ms)
            # Right before a high-impact print the tape is not tradeable; this is the "wait".
            if 0 <= t_minus <= 900:
                calendar_component = 0.0
            elif 0 <= t_minus <= 3600:
                calendar_component = 0.5

        return {
            "spread": spread_component,
            "setup": setup_component,
            "session": session_component,
            "calendar": calendar_component,
        }
