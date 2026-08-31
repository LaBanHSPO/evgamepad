"""The position-size calculator.

It does exactly one arithmetic job and it does it through phase 2's own functions: the same
quote-to-USD conversion that priced R at every fill, and the same volume rounding the broker
actually enforces. Sizing that agrees with the journal but not with the broker is worse than no
calculator at all.

Three numbers come back, deliberately separate:

- **requested** lots, what the risk implies exactly;
- **rounded** lots, what the broker will actually accept after its volume step;
- **actual risk**, recomputed *from the rounded volume* — because the rounding is what you are
  going to trade, and a calculator that reports the risk you asked for rather than the risk you
  will carry is lying by omission.

Applying a result changes the HUD's preview only. LT+RT is still the only thing that trades.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass

from broker.conversion import AssetGraph, ConversionError
from broker.volume import SymbolSpec, volume_to_lots, volume_to_units

# Volume is in hundredths of a lot throughout the cTrader API, the same unit `volume_to_units` uses.
VOLUME_PER_UNIT = 100


@dataclass(frozen=True)
class SizeResult:
    """What the calculator answers, including why it could not answer."""

    symbol: str
    requested_lots: float | None
    rounded_lots: float | None
    volume: int | None
    risk_usd: float | None
    actual_risk_usd: float | None
    stop_distance: float | None
    rate: float | None
    rate_chain: str | None
    capped_at: float | None = None
    reason: str | None = None

    @property
    def ok(self) -> bool:
        return self.rounded_lots is not None

    def payload(self) -> dict[str, object]:
        return {
            "symbol": self.symbol,
            "requestedLots": self.requested_lots,
            "roundedLots": self.rounded_lots,
            "volume": self.volume,
            "riskUsd": self.risk_usd,
            "actualRiskUsd": self.actual_risk_usd,
            "stopDistance": self.stop_distance,
            "rate": self.rate,
            "rateChain": self.rate_chain,
            "cappedAt": self.capped_at,
            "reason": self.reason,
        }


def _unusable(symbol: str, reason: str, risk_usd: float | None = None) -> SizeResult:
    """No size, and the reason said plainly. Never a zero standing in for "cannot"."""
    return SizeResult(symbol=symbol, requested_lots=None, rounded_lots=None, volume=None,
                      risk_usd=risk_usd, actual_risk_usd=None, stop_distance=None, rate=None,
                      rate_chain=None, reason=reason)


def risk_from(equity: float | None, risk_usd: float | None, risk_percent: float | None) -> float | None:
    """Risk in USD, from whichever of the two the player gave. A percent needs an equity to be one."""
    if risk_usd is not None and risk_usd > 0:
        return risk_usd
    if risk_percent is not None and risk_percent > 0 and equity and equity > 0:
        return equity * risk_percent / 100
    return None


def size_position(
    *,
    spec: SymbolSpec,
    entry: float,
    stop: float,
    equity: float | None = None,
    risk_usd: float | None = None,
    risk_percent: float | None = None,
    graph: AssetGraph | None = None,
    prices: Mapping[int, float] | None = None,
    ts_ms: int = 0,
    max_lots: float | None = None,
) -> SizeResult:
    """Lots for a risk, through phase 2's conversion and the broker's own volume step."""
    risk = risk_from(equity, risk_usd, risk_percent)
    if risk is None:
        return _unusable(spec.name, "give a risk in USD, or a percent and an equity")

    distance = abs(entry - stop)
    if distance <= 0:
        # A stop at the entry is not a small risk, it is an unmeasurable one.
        return _unusable(spec.name, "the stop sits at the entry, so risk cannot be measured", risk)

    if graph is None:
        return _unusable(spec.name, "no broker asset graph yet, so the quote cannot be priced", risk)
    try:
        audit = graph.quote_to_usd(spec.quote_asset_id, prices or {}, ts_ms)
    except ConversionError as exc:
        # XAUUSD converts by identity; USDJPY needs a real rate. Without one there is no honest
        # answer, and guessing 1.0 would silently size a JPY trade as if it were a USD one.
        return _unusable(spec.name, str(exc), risk)

    # r_usd = units * distance * rate, so units = risk / (distance * rate).
    units = risk / (distance * audit.rate)
    raw_volume = units * VOLUME_PER_UNIT
    # Two different scales, both from phase 2: volume is hundredths of a unit, and a lot is
    # `lot_size` of those. A standard EURUSD lot is 10,000,000 volume — 100,000 units.
    requested_lots = raw_volume / spec.lot_size
    volume = _round_to_step(int(raw_volume), spec)
    if volume < spec.min_volume:
        return _unusable(
            spec.name,
            f"that risk is smaller than the broker's minimum of "
            f"{volume_to_lots(spec.min_volume, spec):g} lots",
            risk,
        )

    capped_at = None
    if max_lots is not None:
        cap_volume = _round_to_step(int(round(max_lots * spec.lot_size)), spec)
        if volume > cap_volume:
            volume = max(spec.min_volume, cap_volume)
            capped_at = max_lots

    volume = min(volume, spec.max_volume)
    # Recomputed from the volume that will actually be sent, not from the request.
    actual = volume_to_units(volume) * distance * audit.rate

    return SizeResult(
        symbol=spec.name,
        requested_lots=requested_lots,
        rounded_lots=volume_to_lots(volume, spec),
        volume=volume,
        risk_usd=risk,
        actual_risk_usd=actual,
        stop_distance=distance,
        rate=audit.rate,
        rate_chain=" -> ".join(audit.chain),
        capped_at=capped_at,
    )


def _round_to_step(volume: int, spec: SymbolSpec) -> int:
    """Down to the broker's step, never up.

    Rounding up would hand back a size that carries more risk than the player asked for, which is
    the one direction a sizing tool must never round.
    """
    if spec.step_volume <= 0:
        return volume
    return (volume // spec.step_volume) * spec.step_volume
