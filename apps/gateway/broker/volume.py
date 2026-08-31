"""Unit conversions at the broker boundary.

Two scales, both easy to get wrong in a way that only shows up as a margin call:

* **Volume** in the protocol is *cents of units* — hundredths of the base unit — and so is
  `ProtoOASymbol.lotSize`. The HUD speaks lots. `protocol_volume = lots * lotSize`.
* **Prices** in the protocol are 1/100000 of a price unit (`123000` -> `1.23`), and relative
  SL/TP distances use the same scale.

Every min/step/max in `ProtoOASymbol` is protocol volume, so rounding happens in that space, not
in lots. Rounding is always *down* to the step: the player never gets more size than they asked.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import ROUND_DOWN, Decimal

# Protocol volume is hundredths of a unit.
VOLUME_UNIT_SCALE = 100

# Protocol prices and relative SL/TP distances are 1/100000 of a price unit.
RELATIVE_PRICE_SCALE = 100_000


class VolumeError(ValueError):
    """A size the broker would refuse, or would fill at a scale we did not intend."""


@dataclass(frozen=True)
class SymbolSpec:
    """The volume and price facts that only `ProtoOASymbolByIdReq` returns.

    `ProtoOASymbolsListReq` returns `ProtoOALightSymbol`, which carries none of this. Building a
    size from the light symbol is the bug that sends a huge ounce count on a 0.01 lot order.
    """

    symbol_id: int
    name: str
    digits: int
    pip_position: int
    lot_size: int
    min_volume: int
    step_volume: int
    max_volume: int
    base_asset_id: int
    quote_asset_id: int

    def __post_init__(self) -> None:
        for field in ("lot_size", "min_volume", "step_volume", "max_volume"):
            if getattr(self, field) <= 0:
                raise VolumeError(f"{self.name}: {field} must be positive, got {getattr(self, field)}")
        if self.min_volume > self.max_volume:
            raise VolumeError(f"{self.name}: minVolume {self.min_volume} exceeds maxVolume {self.max_volume}")


def lots_to_volume(lots: float, spec: SymbolSpec) -> int:
    """Convert HUD lots to protocol volume, rounded down to the broker's step.

    Raises rather than silently clamping when the result would fall below `minVolume`: a request
    the broker cannot fill should reach the player as a reject, not as a different size.
    """
    if lots <= 0:
        raise VolumeError(f"{spec.name}: lots must be positive, got {lots}")

    raw = Decimal(str(lots)) * Decimal(spec.lot_size)
    step = Decimal(spec.step_volume)
    volume = int((raw / step).quantize(Decimal(1), rounding=ROUND_DOWN) * step)

    if volume < spec.min_volume:
        raise VolumeError(
            f"{spec.name}: {lots} lots is {volume} protocol volume, below minVolume {spec.min_volume}"
        )
    if volume > spec.max_volume:
        raise VolumeError(
            f"{spec.name}: {lots} lots is {volume} protocol volume, above maxVolume {spec.max_volume}"
        )
    return volume


def volume_to_lots(volume: int, spec: SymbolSpec) -> float:
    """Protocol volume back to lots, for HUD payloads and journal rows."""
    return float(Decimal(volume) / Decimal(spec.lot_size))


def volume_to_units(volume: int) -> float:
    """Protocol volume to whole units of the base asset — the quantity R is computed on."""
    return float(Decimal(volume) / Decimal(VOLUME_UNIT_SCALE))


def scale_price(raw: int) -> float:
    """Protocol price integer to a real price."""
    return raw / RELATIVE_PRICE_SCALE


def unscale_price(price: float) -> int:
    """Real price to the protocol's integer scale."""
    return int(round(price * RELATIVE_PRICE_SCALE))


def relative_distance(entry: float, protection: float) -> int:
    """Absolute price distance expressed in the 1/100000 units a MARKET order's SL/TP uses.

    MARKET orders carry `relativeStopLoss` / `relativeTakeProfit` only; absolute `stopLoss` and
    `takeProfit` are for pending orders and for `ProtoOAAmendPositionSLTPReq` on an open position.
    """
    distance = abs(entry - protection)
    if distance <= 0:
        raise VolumeError(f"protection {protection} is at the entry price {entry}")
    return int(round(distance * RELATIVE_PRICE_SCALE))


def round_price(price: float, spec: SymbolSpec) -> float:
    """Round a price to the symbol's quoted precision."""
    return round(price, spec.digits)
