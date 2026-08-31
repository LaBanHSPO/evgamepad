"""Volman-style M5 price-action detectors.

These are **our own detectors**, built from concepts discussed publicly across Bob Volman's
*Forex Price Action Scalping* and *Understanding Price Action*. No book text is reproduced here or
in the fixtures; the books are cited in the HUD and the reader is pointed at them.

Everything in this module is deterministic and pure. It runs with no API key, which is the whole
point — the sentinel and the method lens must keep working when the desk is offline.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

# The one moving average the method leans on.
EMA_PERIOD = 20

# A range needs enough bars to be a range rather than a pause.
MIN_RANGE_BARS = 6

# Bars are "inside" a box while they stay within this fraction of the box height of its edges.
RANGE_TOLERANCE = 0.12

# A break that closes back inside within this many bars is a false break, not a breakout.
FALSE_BREAK_LOOKAHEAD = 3

# Buildup is a run of bars whose ranges are shrinking against the recent average.
BUILDUP_BARS = 4
BUILDUP_SHRINK = 0.7

SetupKind = Literal["range", "range_break", "false_break", "buildup", "ema_pullback"]
Side = Literal["buy", "sell", "none"]


@dataclass(frozen=True)
class Candle:
    """One M5 bar, as the gateway receives it from cTrader trendbars."""

    ts: int
    o: float
    h: float
    low: float
    c: float

    @property
    def range(self) -> float:
        return self.h - self.low

    @property
    def body(self) -> float:
        return abs(self.c - self.o)


@dataclass(frozen=True)
class RangeBox:
    """A horizontal band price has been respecting."""

    top: float
    bottom: float
    from_ts: int
    to_ts: int
    bars: int

    @property
    def height(self) -> float:
        return self.top - self.bottom

    def contains(self, price: float, tolerance: float = RANGE_TOLERANCE) -> bool:
        pad = self.height * tolerance
        return self.bottom - pad <= price <= self.top + pad


@dataclass(frozen=True)
class SetupTag:
    """What the chart is showing right now, in the method's vocabulary."""

    kind: SetupKind
    side: Side
    level: float | None
    ts: int
    note: str

    def key(self) -> tuple[str, str]:
        """Identity for lifecycle tracking — a setup is the same setup until its kind or side changes."""
        return (self.kind, self.side)


def ema(values: list[float], period: int = EMA_PERIOD) -> list[float]:
    """Exponential moving average, seeded on the first value so the series has no warm-up hole."""
    if not values:
        return []
    multiplier = 2 / (period + 1)
    out = [values[0]]
    for value in values[1:]:
        out.append((value - out[-1]) * multiplier + out[-1])
    return out


def bias(candles: list[Candle], period: int = EMA_PERIOD) -> Side:
    """Which way the tape is leaning: close against its own EMA."""
    if len(candles) < period:
        return "none"
    line = ema([c.c for c in candles], period)
    last, previous = line[-1], line[-2]
    if candles[-1].c > last and last >= previous:
        return "buy"
    if candles[-1].c < last and last <= previous:
        return "sell"
    return "none"


def _grow_box(candles: list[Candle], min_bars: int) -> RangeBox | None:
    """Grow a band backwards from the last bar given, stopping at the first bar that escapes it."""
    if len(candles) < min_bars:
        return None

    top = candles[-1].h
    bottom = candles[-1].low
    count = 1

    for candle in reversed(candles[:-1]):
        next_top = max(top, candle.h)
        next_bottom = min(bottom, candle.low)
        height = next_top - next_bottom
        if height <= 0:
            break
        # Growing the box by more than the tolerance means this bar is not part of the range.
        if (next_top - top) > height * RANGE_TOLERANCE or (bottom - next_bottom) > height * RANGE_TOLERANCE:
            break
        top, bottom, count = next_top, next_bottom, count + 1

    if count < min_bars:
        return None
    window = candles[-count:]
    return RangeBox(top=top, bottom=bottom, from_ts=window[0].ts, to_ts=window[-1].ts, bars=count)


def find_range(candles: list[Candle], min_bars: int = MIN_RANGE_BARS) -> RangeBox | None:
    """The band price has been respecting, allowing for a few bars of recent escape.

    Anchoring only on the newest bar would mean a breakout bar became part of its own range and
    nothing could ever break out. So the search steps the anchor back a few bars and keeps the
    longest band it finds — which is the range that was in play *before* the current action.
    """
    best: RangeBox | None = None
    for offset in range(0, FALSE_BREAK_LOOKAHEAD + 2):
        window = candles[: len(candles) - offset] if offset else candles
        box = _grow_box(window, min_bars)
        if box is not None and (best is None or box.bars > best.bars):
            best = box
    return best


def is_buildup(candles: list[Candle], bars: int = BUILDUP_BARS) -> bool:
    """Ranges shrinking against the recent average — pressure building, not a trend."""
    if len(candles) < bars * 2:
        return False
    recent = candles[-bars:]
    baseline = candles[-bars * 2 : -bars]
    recent_avg = sum(c.range for c in recent) / bars
    baseline_avg = sum(c.range for c in baseline) / bars
    if baseline_avg <= 0:
        return False
    return recent_avg <= baseline_avg * BUILDUP_SHRINK


def detect_false_break(candles: list[Candle], box: RangeBox) -> SetupTag | None:
    """A break of the box that closed back inside within a few bars.

    Volman's point, and the reason this detector exists: the failed break is the signal, and it
    points the *other* way from the break.
    """
    window = candles[-(FALSE_BREAK_LOOKAHEAD + 1) :]
    if len(window) < 2:
        return None

    for index, candle in enumerate(window[:-1]):
        broke_up = candle.h > box.top
        broke_down = candle.low < box.bottom
        if not (broke_up or broke_down):
            continue
        after = window[index + 1 :]
        if not after:
            continue
        back_inside = all(box.bottom <= bar.c <= box.top for bar in after)
        if not back_inside:
            continue
        return SetupTag(
            kind="false_break",
            side="sell" if broke_up else "buy",
            level=box.top if broke_up else box.bottom,
            ts=after[-1].ts,
            note=f"break of {'top' if broke_up else 'bottom'} closed back inside",
        )
    return None


def detect(candles: list[Candle]) -> tuple[SetupTag | None, RangeBox | None]:
    """The current setup tag and the box it relates to, if any.

    Order matters: a false break outranks the breakout it invalidates, and a live range outranks
    the buildup inside it.
    """
    if len(candles) < MIN_RANGE_BARS:
        return None, None

    # The box comes from the bars before the current one, so the current bar can be judged
    # against it rather than being swallowed by it.
    box = find_range(candles[:-1])
    last = candles[-1]

    if box is not None:
        false_break = detect_false_break(candles, box)
        if false_break is not None:
            return false_break, box

        if last.c > box.top:
            return SetupTag(kind="range_break", side="buy", level=box.top, ts=last.ts,
                            note="closed above the range"), box
        if last.c < box.bottom:
            return SetupTag(kind="range_break", side="sell", level=box.bottom, ts=last.ts,
                            note="closed below the range"), box

        if is_buildup(candles):
            return SetupTag(kind="buildup", side="none", level=None, ts=last.ts,
                            note=f"{BUILDUP_BARS} bars of shrinking range inside the box"), box

        return SetupTag(kind="range", side="none", level=None, ts=last.ts,
                        note=f"{box.bars} bars respecting the band"), box

    direction = bias(candles)
    if direction != "none":
        line = ema([c.c for c in candles])
        distance = abs(last.c - line[-1])
        if distance <= last.range:
            return SetupTag(kind="ema_pullback", side=direction, level=line[-1], ts=last.ts,
                            note="price back at the 20 EMA with the trend"), None
    return None, None


class SetupTracker:
    """Setup lifecycle, so the socket can say a setup *appeared* or *died* rather than repeating it."""

    def __init__(self) -> None:
        self._current: SetupTag | None = None

    def update(self, candles: list[Candle]) -> list[tuple[str, SetupTag]]:
        """Returns `('born'|'died', tag)` events since the last call. Usually empty."""
        tag, _box = detect(candles)
        events: list[tuple[str, SetupTag]] = []

        if self._current is not None and (tag is None or tag.key() != self._current.key()):
            events.append(("died", self._current))
            self._current = None
        if tag is not None and self._current is None:
            events.append(("born", tag))
            self._current = tag
        return events

    @property
    def current(self) -> SetupTag | None:
        return self._current
