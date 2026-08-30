"""Freeze one trade's window out of the ring, and measure the excursion.

Runs at ``closed_at + tape.post_roll_s``, or early on shutdown / session end
with whatever post-roll exists -- ``n`` is stored, so a short window renders as
a short window rather than looking like missing data.
"""

from __future__ import annotations

import gzip
import json
from dataclasses import asdict, dataclass
from decimal import Decimal

from ...broker.types import RELATIVE_UNITS_PER_PRICE
from .ring import Bar

_COLUMNS = (
    "ts_s",
    "bid_o",
    "bid_h",
    "bid_l",
    "bid_c",
    "ask_o",
    "ask_h",
    "ask_l",
    "ask_c",
    "n_ticks",
)


@dataclass(frozen=True)
class Excursion:
    """Both in price units, signed from the entry.

    ``mfe`` is how far the trade ever went **in favour** (>= 0) and ``mae`` how
    far it ever went **against** (<= 0), so a deck row reads "+2.1R best,
    -0.6R worst" without a sign convention to remember.
    """

    mfe: float
    mae: float

    def in_r(self, r_usd_per_price: float) -> tuple[float, float]:
        if r_usd_per_price <= 0:
            raise ValueError("R per price unit must be positive")
        return (self.mfe / r_usd_per_price, self.mae / r_usd_per_price)


@dataclass(frozen=True)
class FrozenTape:
    sym: str
    from_ts: int
    to_ts: int
    dt_s: int
    n: int
    digits: int
    bars_gz: bytes
    events_json: str


def _scale(raw: int, digits: int) -> float:
    return float(round(Decimal(raw) / Decimal(RELATIVE_UNITS_PER_PRICE), digits))


def excursion(
    bars: list[Bar], *, side: str, entry: float, digits: int
) -> Excursion:
    """MFE/MAE from the side of the book the trade would actually exit on.

    A long exits by selling at the **bid**; a short exits by buying at the
    **ask**. Measuring both from one side would understate the excursion on one
    of them by a full spread every time -- a silent asymmetry that would quietly
    bias every R-multiple statistic in the journal.
    """
    if not bars:
        return Excursion(mfe=0.0, mae=0.0)

    if side == "buy":
        highs = [_scale(b.bid_h, digits) - entry for b in bars]
        lows = [_scale(b.bid_l, digits) - entry for b in bars]
    elif side == "sell":
        highs = [entry - _scale(b.ask_l, digits) for b in bars]
        lows = [entry - _scale(b.ask_h, digits) for b in bars]
    else:
        raise ValueError(f"side must be buy or sell, got {side!r}")

    return Excursion(mfe=max(0.0, max(highs)), mae=min(0.0, min(lows)))


def pack_bars(bars: list[Bar]) -> bytes:
    """Columnar, then gzip. Columns compress far better than rows here: eight of
    the ten are slowly-drifting integers that share most of their digits."""
    columns = {name: [getattr(b, name) for b in bars] for name in _COLUMNS}
    payload = json.dumps(columns, separators=(",", ":")).encode()
    return gzip.compress(payload, compresslevel=9)


def unpack_bars(blob: bytes) -> list[Bar]:
    columns = json.loads(gzip.decompress(blob))
    n = len(columns["ts_s"])
    return [Bar(**{name: columns[name][i] for name in _COLUMNS}) for i in range(n)]


def freeze(
    *,
    sym: str,
    bars: list[Bar],
    opened_at_ms: int,
    closed_at_ms: int,
    pre_roll_s: int,
    post_roll_s: int,
    dt_s: int,
    digits: int,
    events: list[dict] | None = None,
) -> FrozenTape:
    """Cut ``[opened_at - pre_roll, closed_at + post_roll]`` from the ring."""
    from_ts = opened_at_ms // 1000 - pre_roll_s
    to_ts = closed_at_ms // 1000 + post_roll_s
    window = [b for b in bars if from_ts <= b.ts_s <= to_ts]
    return FrozenTape(
        sym=sym,
        from_ts=from_ts,
        to_ts=to_ts,
        dt_s=dt_s,
        n=len(window),
        digits=digits,
        bars_gz=pack_bars(window),
        events_json=json.dumps(events or [], separators=(",", ":")),
    )


def in_trade(bars: list[Bar], opened_at_ms: int, closed_at_ms: int) -> list[Bar]:
    """Only the bars the position was actually open for. Excursion is measured
    over these; the pre/post roll is context for the replay, not risk taken."""
    return [b for b in bars if opened_at_ms // 1000 <= b.ts_s <= closed_at_ms // 1000]


def as_dicts(bars: list[Bar]) -> list[dict]:
    return [asdict(b) for b in bars]
