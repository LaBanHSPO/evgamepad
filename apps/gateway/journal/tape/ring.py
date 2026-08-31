"""1 Hz bid+ask ring, tapped **before** the browser conflation.

The HUD sees quotes conflated to 10-20 Hz; the tape sees the same stream at full rate and folds it
into one-second OHLC bars for both sides of the book. It runs whether or not a position is open,
which is the only way pre-roll can exist for a trade nobody knew was coming.

Prices stay as the protocol's scaled integers all the way into storage — converting to float here
would round the tape and then round it again on the way out.
"""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass

DEFAULT_DT_S = 1


@dataclass
class Bar:
    """One second of both sides of the book."""

    ts_s: int
    bid_o: int
    bid_h: int
    bid_l: int
    bid_c: int
    ask_o: int
    ask_h: int
    ask_l: int
    ask_c: int
    n_ticks: int

    def update(self, bid: int, ask: int) -> None:
        self.bid_h = max(self.bid_h, bid)
        self.bid_l = min(self.bid_l, bid)
        self.bid_c = bid
        self.ask_h = max(self.ask_h, ask)
        self.ask_l = min(self.ask_l, ask)
        self.ask_c = ask
        self.n_ticks += 1

    @classmethod
    def opened(cls, ts_s: int, bid: int, ask: int) -> Bar:
        return cls(ts_s, bid, bid, bid, bid, ask, ask, ask, ask, 1)


class TapeRing:
    """A fixed-size RAM ring per symbol. Roughly 1 MB at the default 90 minutes."""

    def __init__(self, ring_minutes: int = 90, dt_s: int = DEFAULT_DT_S) -> None:
        if dt_s <= 0:
            raise ValueError("dt_s must be positive")
        self.dt_s = dt_s
        self.capacity = max(1, (ring_minutes * 60) // dt_s)
        self._bars: dict[str, deque[Bar]] = {}
        self._open: dict[str, Bar] = {}

    def tick(self, symbol: str, *, bid: int, ask: int, ts_ms: int) -> None:
        """Fold one spot into the current bar, rolling to a new one on each bucket boundary."""
        bucket = (ts_ms // 1000 // self.dt_s) * self.dt_s
        current = self._open.get(symbol)

        if current is None:
            self._open[symbol] = Bar.opened(bucket, bid, ask)
            return
        if bucket == current.ts_s:
            current.update(bid, ask)
            return
        if bucket < current.ts_s:
            # Out-of-order spot from a reconnect; the current bar is already ahead of it.
            return

        self._commit(symbol, current)
        self._open[symbol] = Bar.opened(bucket, bid, ask)

    def _commit(self, symbol: str, bar: Bar) -> None:
        self._bars.setdefault(symbol, deque(maxlen=self.capacity)).append(bar)

    def flush(self, symbol: str | None = None) -> None:
        """Commit the in-progress bar. Called at shutdown and at session end."""
        symbols = [symbol] if symbol is not None else list(self._open)
        for name in symbols:
            bar = self._open.pop(name, None)
            if bar is not None:
                self._commit(name, bar)

    def window(self, symbol: str, from_ts: int, to_ts: int) -> list[Bar]:
        """Committed bars in `[from_ts, to_ts]`, plus the in-progress bar when it falls inside.

        Including the open bar is what makes a shutdown flush and a short post-roll produce the
        same answer as a settled one — the window is whatever the tape actually holds.
        """
        bars = [b for b in self._bars.get(symbol, ()) if from_ts <= b.ts_s <= to_ts]
        current = self._open.get(symbol)
        if current is not None and from_ts <= current.ts_s <= to_ts:
            bars.append(current)
        return bars

    def depth(self, symbol: str) -> int:
        return len(self._bars.get(symbol, ())) + (1 if symbol in self._open else 0)
