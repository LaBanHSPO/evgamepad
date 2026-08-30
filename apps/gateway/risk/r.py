"""**The** definition of R. There is no second formula anywhere in this repo.

The HUD's R, ``trade_closed.r_multiple``, MFE/MAE in R, phase 9's tilt inputs,
phase 11's Process Score, and phase 12's position-size calculator all call these
functions. If R ever needs to change, it changes here and everything moves with
it -- which is the whole reason this module is four functions and not a method
on something.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Literal

from ..broker.conversion import AssetGraph, Conversion
from ..broker.types import SymbolSpec
from ..broker.volume import volume_to_units

RSource = Literal["stop", "r_unit_fallback"]


@dataclass(frozen=True)
class RValue:
    """One R, in USD, with everything needed to re-check it a year later."""

    usd: float
    source: RSource
    rate: float
    chain: str
    rate_ts: int

    def multiple(self, pnl_usd: float) -> float:
        if self.usd <= 0:
            raise ValueError("R must be positive")
        return float(Decimal(str(pnl_usd)) / Decimal(str(self.usd)))


def r_from_distance(
    *,
    protocol_volume: int,
    distance: float,
    spec: SymbolSpec,
    graph: AssetGraph,
    ts: int,
) -> RValue:
    """Risk over a stop *distance*, converted to USD at the entry-time rate.

    Distance, not entry and stop, because that is what the order actually
    carries: a MARKET order sends ``relativeStopLoss``, and R is knowable from
    it before any fill price exists. ``units = protocolVolume / 100``; raw risk
    is ``units * distance`` in the symbol's **quote** asset. XAUUSD is already
    USD (identity); USDJPY is JPY and must be converted before it may be called
    USD.
    """
    d = abs(Decimal(str(distance)))
    if d == 0:
        raise ValueError("zero stop distance; use r_fallback instead")

    units = volume_to_units(protocol_volume)
    raw_quote = float(units * d)

    quote_asset = graph.asset_name(spec.quote_asset_id)
    if not quote_asset:
        raise ValueError(f"{spec.name}: quote asset {spec.quote_asset_id} unknown")

    conv: Conversion = graph.to_usd(quote_asset, ts)
    return RValue(
        usd=conv.apply(raw_quote),
        source="stop",
        rate=conv.rate,
        chain=conv.chain,
        rate_ts=conv.ts,
    )


def r_from_stop(
    *,
    protocol_volume: int,
    entry: float,
    stop: float,
    spec: SymbolSpec,
    graph: AssetGraph,
    ts: int,
) -> RValue:
    """Risk to an absolute stop. Thin wrapper over :func:`r_from_distance` so
    there is still exactly one formula."""
    distance = abs(Decimal(str(entry)) - Decimal(str(stop)))
    if distance == 0:
        raise ValueError("stop equals entry; use r_fallback instead")
    return r_from_distance(
        protocol_volume=protocol_volume, distance=float(distance),
        spec=spec, graph=graph, ts=ts,
    )


def r_fallback(r_unit_usd: float, ts: int) -> RValue:
    """No SL at entry. ``risk.r_unit_usd`` stands in, and says so, so a trade
    without protection is never quietly scored as if it had some."""
    if r_unit_usd <= 0:
        raise ValueError("risk.r_unit_usd must be positive")
    return RValue(
        usd=float(r_unit_usd),
        source="r_unit_fallback",
        rate=1.0,
        chain="USD",
        rate_ts=ts,
    )


def r_for_entry(
    *,
    protocol_volume: int,
    entry: float,
    stop: float | None,
    spec: SymbolSpec,
    graph: AssetGraph,
    ts: int,
    r_unit_usd: float,
) -> RValue:
    """The one call site everything else should use: stop-derived when a stop
    exists at entry, the configured unit otherwise. Never returns ``None``, so
    ``r_multiple`` is non-null for every closed trade."""
    if stop is not None and stop != entry:
        return r_from_stop(
            protocol_volume=protocol_volume,
            entry=entry,
            stop=stop,
            spec=spec,
            graph=graph,
            ts=ts,
        )
    return r_fallback(r_unit_usd, ts)


def lots_for_risk(
    *,
    risk_usd: float,
    entry: float,
    stop: float,
    spec: SymbolSpec,
    graph: AssetGraph,
    ts: int,
) -> float:
    """Inverse of :func:`r_from_stop`, for phase 12's calculator. Returns raw
    lots; the caller snaps them with ``volume.lots_to_volume``, which is what
    enforces the broker's step and max."""
    distance = abs(Decimal(str(entry)) - Decimal(str(stop)))
    if distance == 0:
        raise ValueError("stop equals entry")
    quote_asset = graph.asset_name(spec.quote_asset_id)
    if not quote_asset:
        raise ValueError(f"{spec.name}: quote asset {spec.quote_asset_id} unknown")

    conv = graph.to_usd(quote_asset, ts)
    if conv.rate <= 0:
        raise ValueError(f"{spec.name}: conversion rate is {conv.rate}")

    risk_in_quote = Decimal(str(risk_usd)) / Decimal(str(conv.rate))
    units = risk_in_quote / distance
    volume = units * Decimal(100)
    return float(volume / Decimal(spec.lot_size))
