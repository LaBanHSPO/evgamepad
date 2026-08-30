"""lots <-> cTrader protocol volume, and price scaling.

The HUD speaks lots. cTrader speaks cents of a unit. Getting this wrong on gold
means a 0.01-lot press sends a huge ounce count, so every conversion goes
through here and every input comes from ``ProtoOASymbolByIdReq``.
"""

from __future__ import annotations

from decimal import ROUND_HALF_UP, Decimal

from .types import RELATIVE_UNITS_PER_PRICE, VOLUME_CENTS_PER_UNIT, SymbolSpec


class VolumeError(ValueError):
    """A lot size the broker's own spec refuses. Carries a protocol reject
    reason so the caller does not have to invent one."""

    def __init__(self, reason: str, detail: str) -> None:
        super().__init__(f"{reason}: {detail}")
        self.reason = reason
        self.detail = detail


def lots_to_volume(lots: float, spec: SymbolSpec) -> int:
    """Convert lots to protocol volume, snapped to the broker's own step grid.

    Raises rather than silently clamping a too-large order: an order that is not
    the size the player pressed is a different order.
    """
    if lots <= 0:
        raise VolumeError("lot_step", f"lots must be positive, got {lots}")

    raw = Decimal(str(lots)) * Decimal(spec.lot_size)
    step = Decimal(spec.step_volume)
    if step <= 0:
        raise VolumeError("lot_step", f"{spec.name}: stepVolume is {spec.step_volume}")

    snapped = int((raw / step).quantize(Decimal(1), rounding=ROUND_HALF_UP) * step)

    if snapped < spec.min_volume:
        raise VolumeError(
            "lot_step",
            f"{spec.name}: {lots} lots -> {snapped}, below minVolume {spec.min_volume}",
        )
    if snapped > spec.max_volume:
        raise VolumeError(
            "max_lots",
            f"{spec.name}: {lots} lots -> {snapped}, above maxVolume {spec.max_volume}",
        )
    return snapped


def volume_to_lots(volume: int, spec: SymbolSpec) -> float:
    if spec.lot_size <= 0:
        raise VolumeError("lot_step", f"{spec.name}: lotSize is {spec.lot_size}")
    return float(Decimal(volume) / Decimal(spec.lot_size))


def volume_to_units(volume: int) -> Decimal:
    """Protocol volume is cents of a unit. Risk maths needs units."""
    return Decimal(volume) / Decimal(VOLUME_CENTS_PER_UNIT)


def scale_price(raw: int, spec: SymbolSpec) -> float:
    """Spot prices arrive as 1/100000 of a price unit: ``123000`` -> ``1.23``."""
    value = Decimal(raw) / Decimal(RELATIVE_UNITS_PER_PRICE)
    return float(round(value, spec.digits))


def unscale_price(price: float, spec: SymbolSpec) -> int:
    value = Decimal(str(price)) * Decimal(RELATIVE_UNITS_PER_PRICE)
    return int(value.quantize(Decimal(1), rounding=ROUND_HALF_UP))


def price_distance_to_relative(distance: float) -> int:
    """A MARKET order carries ``relativeStopLoss``/``relativeTakeProfit`` in
    1/100000 distance units -- absolute SL/TP is not available on this order
    type, and an SL/TP edit later goes through ``AmendPositionSLTP`` instead."""
    if distance <= 0:
        raise VolumeError("bad_distance", f"distance must be positive, got {distance}")
    value = Decimal(str(distance)) * Decimal(RELATIVE_UNITS_PER_PRICE)
    return int(value.quantize(Decimal(1), rounding=ROUND_HALF_UP))


def relative_to_price_distance(relative: int) -> float:
    return float(Decimal(relative) / Decimal(RELATIVE_UNITS_PER_PRICE))
