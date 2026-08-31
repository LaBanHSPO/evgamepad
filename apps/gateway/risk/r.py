"""**The** definition of R. One function, imported everywhere R is spoken.

The HUD's risk readout, `trade_closed.r_multiple`, MFE/MAE in R, the tilt inputs, the process
score, and the phase 12 size calculator all call this. A second definition anywhere would mean
two different answers to "how big was that loss", which is the number the whole journal is for.

    units       = protocol_volume / 100
    risk_quote  = units * |entry - stop|          (in the symbol's quote asset)
    R_usd       = risk_quote * quote_to_usd_rate  (rate captured at entry, stored with the plan)

With no stop at entry there is nothing to measure, so `risk.r_unit_usd` stands in — the one case
where R is a policy number rather than a measured one, and it is recorded as such.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Literal

from broker.conversion import AssetGraph, ConversionAudit
from broker.volume import SymbolSpec, volume_to_units

RMethod = Literal["stop", "fallback"]


@dataclass(frozen=True)
class RRecord:
    """R and its provenance. Stored with the trade plan so the number stays auditable."""

    r_usd: float
    method: RMethod
    units: float
    stop_distance: float | None
    conversion: ConversionAudit | None

    def as_row(self) -> dict[str, object]:
        row: dict[str, object] = {
            "r_usd": self.r_usd,
            "r_method": self.method,
            "r_units": self.units,
            "r_stop_distance": self.stop_distance,
        }
        if self.conversion is not None:
            audit = self.conversion.as_row()
            row.update(
                {
                    "r_rate": audit["rate"],
                    "r_rate_chain": audit["chain"],
                    "r_rate_source": audit["source"],
                    "r_rate_ts": audit["ts_ms"],
                }
            )
        return row


def r_at_entry(
    *,
    volume: int,
    entry: float,
    stop: float | None,
    spec: SymbolSpec,
    graph: AssetGraph,
    prices: Mapping[int, float],
    ts_ms: int,
    r_unit_usd: float,
) -> RRecord:
    """R in USD for a fire, measured from its own stop where one exists."""
    units = volume_to_units(volume)

    if stop is None:
        return RRecord(r_usd=float(r_unit_usd), method="fallback", units=units,
                       stop_distance=None, conversion=None)

    distance = abs(entry - stop)
    if distance <= 0:
        raise ValueError(f"{spec.name}: stop {stop} sits at the entry {entry}; R would be zero")

    audit = graph.quote_to_usd(spec.quote_asset_id, prices, ts_ms)
    return RRecord(
        r_usd=units * distance * audit.rate,
        method="stop",
        units=units,
        stop_distance=distance,
        conversion=audit,
    )


def r_multiple(pnl_usd: float, r_usd: float) -> float:
    """Result in R. Never divides by a zero R — that would be an unmeasurable trade."""
    if r_usd <= 0:
        raise ValueError(f"R must be positive to express a multiple, got {r_usd}")
    return pnl_usd / r_usd
