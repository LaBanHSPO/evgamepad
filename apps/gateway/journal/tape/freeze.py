"""Freeze one trade's window out of the ring: gzipped columnar bars plus MFE/MAE.

Only windows around actual trades are persisted, so a zero-trade evening writes nothing at all.

MFE/MAE read the **correct side of the book**. A long is exited on the bid, so its excursions are
measured there; a short is exited on the ask. Measuring both from one side would understate every
short's adverse move by the spread — a silent asymmetry that would quietly flatter half the
journal.
"""

from __future__ import annotations

import gzip
import json
import struct
from dataclasses import dataclass

from .ring import Bar

FORMAT_VERSION = 1

# ts_s as int64, eight scaled prices as int64, tick count as int32.
BAR_STRUCT = struct.Struct("<q8qi")


@dataclass(frozen=True)
class Excursions:
    """Favourable and adverse excursion, in price units, from the entry."""

    mfe: float
    mae: float


def pack_bars(bars: list[Bar], *, dt_s: int) -> bytes:
    """Gzipped columnar blob: a JSON header line, then fixed-width records."""
    header = json.dumps(
        {"v": FORMAT_VERSION, "n": len(bars), "dt_s": dt_s,
         "from_ts": bars[0].ts_s if bars else None,
         "to_ts": bars[-1].ts_s if bars else None},
        sort_keys=True,
    ).encode("utf-8")
    body = b"".join(
        BAR_STRUCT.pack(b.ts_s, b.bid_o, b.bid_h, b.bid_l, b.bid_c,
                        b.ask_o, b.ask_h, b.ask_l, b.ask_c, b.n_ticks)
        for b in bars
    )
    return gzip.compress(header + b"\n" + body, compresslevel=6)


def unpack_bars(blob: bytes) -> tuple[dict, list[Bar]]:
    """Inverse of `pack_bars`, for replay in phase 10."""
    raw = gzip.decompress(blob)
    header_line, _, body = raw.partition(b"\n")
    header = json.loads(header_line)
    if header.get("v") != FORMAT_VERSION:
        raise ValueError(f"unsupported tape format v{header.get('v')}")
    bars = [Bar(*BAR_STRUCT.unpack_from(body, off))
            for off in range(0, len(body), BAR_STRUCT.size)]
    return header, bars


def excursions(bars: list[Bar], *, side: str, entry: float, scale: int) -> Excursions:
    """Best and worst excursion from `entry`, read off the side the position exits on."""
    normalised = side.lower()
    if normalised not in ("buy", "sell"):
        raise ValueError(f"unknown side `{side}`")
    if not bars:
        return Excursions(mfe=0.0, mae=0.0)

    if normalised == "buy":
        # A long is closed by selling into the bid.
        best = max(b.bid_h for b in bars) / scale
        worst = min(b.bid_l for b in bars) / scale
        return Excursions(mfe=max(0.0, best - entry), mae=max(0.0, entry - worst))
    # A short is closed by buying back at the ask.
    best = min(b.ask_l for b in bars) / scale
    worst = max(b.ask_h for b in bars) / scale
    return Excursions(mfe=max(0.0, entry - best), mae=max(0.0, worst - entry))


def freeze_window(
    bars: list[Bar], *, side: str, entry: float, scale: int, dt_s: int
) -> tuple[bytes, Excursions]:
    """One trade's tape row: the packed window and the excursions computed from the same bars."""
    return pack_bars(bars, dt_s=dt_s), excursions(bars, side=side, entry=entry, scale=scale)
