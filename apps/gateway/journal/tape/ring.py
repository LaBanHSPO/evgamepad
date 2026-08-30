"""1 Hz bid+ask OHLC ring, tapped **before** the browser conflation.

The HUD sees quotes conflated to 10-20 Hz. If the tape were tapped after that,
``n_ticks`` would always be 1 and every wiggle a replay is supposed to show
would already be gone. So the ring subscribes to the raw spot stream and
conflation stays a browser concern.

The ring is always running, whether or not a position is open -- that is what
makes pre-roll exist at the moment a trade opens. It costs about a megabyte of
RAM for 90 minutes across four symbols, and it writes nothing: a zero-trade
evening persists no tape at all.
"""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass

#: Prices are kept as the broker's raw scaled integers (1/100000). Scaling to a
#: float per tick would cost precision for no benefit -- the reader scales once.


@dataclass
class Bar:
    ts_s: int
    bid_o: int
    bid_h: int
    bid_l: int
    bid_c: int
    ask_o: int
    ask_h: int
    ask_l: int
    ask_c: int
    n_ticks: int = 1

    def update(self, bid: int, ask: int) -> None:
        self.bid_h = max(self.bid_h, bid)
        self.bid_l = min(self.bid_l, bid)
        self.bid_c = bid
        self.ask_h = max(self.ask_h, ask)
        self.ask_l = min(self.ask_l, ask)
        self.ask_c = ask
        self.n_ticks += 1

    @classmethod
    def opening(cls, ts_s: int, bid: int, ask: int) -> Bar:
        return cls(ts_s, bid, bid, bid, bid, ask, ask, ask, ask, 1)


class SymbolRing:
    def __init__(self, sym: str, digits: int, capacity_s: int, dt_s: int = 1) -> None:
        self.sym = sym
        self.digits = digits
        self.dt_s = max(1, dt_s)
        self._bars: deque[Bar] = deque(maxlen=max(1, capacity_s // self.dt_s))
        self._open: Bar | None = None

    def on_tick(self, bid: int, ask: int, ts_ms: int) -> None:
        slot = (ts_ms // 1000) // self.dt_s * self.dt_s
        if self._open is None:
            self._open = Bar.opening(slot, bid, ask)
            return
        if slot == self._open.ts_s:
            self._open.update(bid, ask)
            return
        if slot < self._open.ts_s:
            # Out-of-order tick from a reconnect burst. Folding it into the
            # current bar is wrong; dropping one tick is the smaller lie.
            return
        self._bars.append(self._open)
        self._open = Bar.opening(slot, bid, ask)

    def seal(self) -> None:
        """Close the in-progress bar. Called on shutdown and at session end so a
        freeze during the post-roll still sees the last second."""
        if self._open is not None:
            self._bars.append(self._open)
            self._open = None

    def bars(self) -> list[Bar]:
        out = list(self._bars)
        if self._open is not None:
            out.append(self._open)
        return out

    def window(self, from_s: int, to_s: int) -> list[Bar]:
        return [b for b in self.bars() if from_s <= b.ts_s <= to_s]

    def __len__(self) -> int:
        return len(self._bars) + (1 if self._open else 0)


class TapeRing:
    def __init__(self, ring_minutes: int = 90, dt_s: int = 1) -> None:
        self.capacity_s = ring_minutes * 60
        self.dt_s = dt_s
        self._rings: dict[str, SymbolRing] = {}

    def track(self, sym: str, digits: int) -> SymbolRing:
        ring = self._rings.get(sym)
        if ring is None:
            ring = SymbolRing(sym, digits, self.capacity_s, self.dt_s)
            self._rings[sym] = ring
        return ring

    def on_tick(self, sym: str, bid: int, ask: int, ts_ms: int, digits: int = 5) -> None:
        self.track(sym, digits).on_tick(bid, ask, ts_ms)

    def ring(self, sym: str) -> SymbolRing | None:
        return self._rings.get(sym)

    def window(self, sym: str, from_s: int, to_s: int) -> list[Bar]:
        ring = self._rings.get(sym)
        return ring.window(from_s, to_s) if ring else []

    def seal_all(self) -> None:
        for ring in self._rings.values():
            ring.seal()
