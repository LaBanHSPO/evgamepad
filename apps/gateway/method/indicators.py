"""EMA and ATR over the candle book, for auto-graded playbook rules.

Pure functions over closed bars. Nothing here reads the network, and nothing
here is allowed to be a second definition of something already defined
elsewhere -- the HUD's EMA is the same formula, and both are seeded the same
way for the same reason.
"""

from __future__ import annotations

from dataclasses import dataclass

EMA_PERIOD = 20
ATR_PERIOD = 14


@dataclass(frozen=True)
class OHLC:
    ts: int
    o: float
    h: float
    l: float
    c: float


def ema(closes: list[float], period: int = EMA_PERIOD) -> float | None:
    """Seeded with the simple average of the first `period` closes.

    Seeding from a single close starts the line away from the data and lets it
    drift into place over the next few dozen bars, which reads as a signal when
    it is only an artefact of the seed.
    """
    if len(closes) < period:
        return None
    k = 2 / (period + 1)
    value = sum(closes[:period]) / period
    for close in closes[period:]:
        value = close * k + value * (1 - k)
    return value


def true_range(bar: OHLC, previous_close: float | None) -> float:
    """The gap matters: without the previous close this is just the bar's own
    range, which understates volatility across a session break."""
    if previous_close is None:
        return bar.h - bar.l
    return max(bar.h - bar.l, abs(bar.h - previous_close), abs(bar.l - previous_close))


def atr(bars: list[OHLC], period: int = ATR_PERIOD) -> float | None:
    """Wilder's ATR. Returns None until there are enough bars to mean it."""
    if len(bars) < period + 1:
        return None
    ranges: list[float] = []
    for i in range(1, len(bars)):
        ranges.append(true_range(bars[i], bars[i - 1].c))
    if len(ranges) < period:
        return None
    value = sum(ranges[:period]) / period
    for tr in ranges[period:]:
        value = (value * (period - 1) + tr) / period
    return value
