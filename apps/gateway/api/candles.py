"""Chart bars: history from cTrader, live bars from the spot stream.

Two sources, one shape. The seed comes from ``ProtoOAGetTrendbarsReq`` once per
symbol per session (the API's history limit is ~5 req/s and this is not worth
spending it on), and everything after that is aggregated locally from the same
raw spot tap the tape ring uses.

Bars are built from the **bid**, which is what a long exits at and what a chart
conventionally plots. The tape keeps both sides for MFE/MAE; this does not need
to.
"""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass

#: The timeframes the HUD offers. Anything outside this is a protocol error
#: long before it reaches here.
TIMEFRAME_SECONDS: dict[str, int] = {
    "M1": 60,
    "M5": 300,
    "M15": 900,
    "H1": 3600,
    "H4": 14_400,
    "D1": 86_400,
}

#: Per symbol per timeframe. Enough to fill a screen and scroll back a little,
#: small enough that four symbols cost nothing.
MAX_BARS = 500


@dataclass
class Bar:
    ts: int
    """Bar open, unix seconds."""
    o: float
    h: float
    l: float
    c: float
    closed: bool = False

    def update(self, price: float) -> None:
        self.h = max(self.h, price)
        self.l = min(self.l, price)
        self.c = price

    @classmethod
    def opening(cls, ts: int, price: float) -> Bar:
        return cls(ts=ts, o=price, h=price, l=price, c=price)


def bucket(ts_s: int, timeframe: str) -> int:
    seconds = TIMEFRAME_SECONDS[timeframe]
    return ts_s // seconds * seconds


class CandleBook:
    """Live bars for every subscribed symbol and timeframe."""

    def __init__(self, timeframes: list[str] | None = None, max_bars: int = MAX_BARS) -> None:
        self.timeframes = timeframes or ["M1", "M5", "M15", "H1"]
        self.max_bars = max_bars
        self._bars: dict[tuple[str, str], deque[Bar]] = {}
        self._open: dict[tuple[str, str], Bar] = {}
        self._seeded: set[tuple[str, str]] = set()

    def _series(self, sym: str, tf: str) -> deque[Bar]:
        key = (sym, tf)
        if key not in self._bars:
            self._bars[key] = deque(maxlen=self.max_bars)
        return self._bars[key]

    def seed(self, sym: str, tf: str, bars: list[Bar]) -> None:
        """Install history. Idempotent per symbol/timeframe, because the
        history endpoint is rate-limited and re-seeding mid-session would also
        discard bars built since."""
        key = (sym, tf)
        if key in self._seeded:
            return
        series = self._series(sym, tf)
        series.clear()
        for bar in bars[-self.max_bars :]:
            series.append(Bar(bar.ts, bar.o, bar.h, bar.l, bar.c, closed=True))
        self._seeded.add(key)

    def is_seeded(self, sym: str, tf: str) -> bool:
        return (sym, tf) in self._seeded

    def on_price(self, sym: str, price: float, ts_ms: int) -> list[tuple[str, Bar]]:
        """Feed one tick. Returns the timeframes whose bar just **closed**.

        Only closes are returned: a forming bar changes on every tick and is
        pushed to the browser on a timer instead, so the chart does not become
        another quote-rate stream on the socket that carries order acks.
        """
        ts_s = ts_ms // 1000
        closed: list[tuple[str, Bar]] = []

        for tf in self.timeframes:
            key = (sym, tf)
            slot = bucket(ts_s, tf)
            current = self._open.get(key)

            if current is None:
                self._open[key] = Bar.opening(slot, price)
                continue
            if slot == current.ts:
                current.update(price)
                continue
            if slot < current.ts:
                # Out-of-order tick from a reconnect burst. Folding it into the
                # current bar would corrupt an OHLC that is already published.
                continue

            current.closed = True
            self._series(sym, tf).append(current)
            closed.append((tf, current))
            self._open[key] = Bar.opening(slot, price)

        return closed

    def forming(self, sym: str, tf: str) -> Bar | None:
        return self._open.get((sym, tf))

    def history(self, sym: str, tf: str, limit: int | None = None) -> list[Bar]:
        """Closed bars, oldest first, with the forming bar appended so the
        chart's right edge is live rather than a timeframe behind."""
        bars = list(self._series(sym, tf))
        if limit is not None:
            bars = bars[-limit:]
        current = self._open.get((sym, tf))
        if current is not None:
            bars.append(current)
        return bars


def payload(sym: str, tf: str, bar: Bar) -> dict:
    """A `candle` frame payload. Times go out in **milliseconds**, matching
    every other timestamp in the protocol; the chart converts on arrival."""
    return {
        "sym": sym,
        "tf": tf,
        "ts": bar.ts * 1000,
        "o": bar.o,
        "h": bar.h,
        "l": bar.l,
        "c": bar.c,
        "closed": bar.closed,
    }
