"""Normalise `ProtoOAExecutionEvent` into the facts the journal records.

The protocol reports one event shape for several different things: an order accepted, an order
filled that *opened* a position, an order filled that *closed* one, a rejection. The journal cares
about three of them, so the branching lives here rather than being repeated at every call site.

A close is recognised by the deal carrying a `closePositionDetail` — the same record that carries
the broker's own gross profit, swap, commission, and the quote-to-deposit rate. Preferring those
figures over anything computed locally is what keeps cTrader the money source of truth.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal

from .volume import scale_price

EventKind = Literal["fill", "close", "reject", "accepted", "ignored"]


@dataclass(frozen=True)
class ExecutionFact:
    """One journal-relevant thing that happened at the broker."""

    kind: EventKind
    cid: str | None = None
    position_id: int | None = None
    order_id: int | None = None
    symbol_id: int | None = None
    side: str | None = None
    volume: int | None = None
    price: float | None = None
    ts_ms: int | None = None
    gross_pnl: float | None = None
    commission: float | None = None
    swap: float | None = None
    reason: str | None = None


def _money(raw: int | None, digits: int) -> float | None:
    """cTrader money fields are integers scaled by the record's own `moneyDigits`."""
    if raw is None:
        return None
    return raw / (10 ** (digits or 2))


def normalise_execution(event: Any) -> ExecutionFact:
    """Turn one execution event into a fact, or `ignored` when the journal does not care."""
    execution_type = event.executionType
    name = _EXECUTION_NAMES.get(execution_type, str(execution_type))

    if name == "ORDER_REJECTED":
        return ExecutionFact(
            kind="reject",
            cid=event.order.clientOrderId or None,
            order_id=event.order.orderId or None,
            reason=str(event.errorCode or "rejected"),
        )

    if name == "ORDER_ACCEPTED":
        return ExecutionFact(kind="accepted", cid=event.order.clientOrderId or None,
                             order_id=event.order.orderId or None)

    if name not in ("ORDER_FILLED", "ORDER_PARTIAL_FILL"):
        return ExecutionFact(kind="ignored")

    deal = event.deal
    detail = deal.closePositionDetail if deal.HasField("closePositionDetail") else None
    side = "buy" if deal.tradeSide == 1 else "sell"

    if detail is not None:
        # A closing deal: the position is going away and the broker is telling us what it cost.
        digits = detail.moneyDigits or deal.moneyDigits
        return ExecutionFact(
            kind="close",
            cid=event.order.clientOrderId or None,
            position_id=deal.positionId or None,
            order_id=deal.orderId or None,
            symbol_id=deal.symbolId or None,
            side=side,
            volume=deal.filledVolume or deal.volume or None,
            price=scale_price(deal.executionPrice) if deal.executionPrice else None,
            ts_ms=deal.executionTimestamp or None,
            gross_pnl=_money(detail.grossProfit, digits),
            commission=_money(deal.commission, deal.moneyDigits),
            swap=_money(detail.swap, digits),
        )

    return ExecutionFact(
        kind="fill",
        cid=event.order.clientOrderId or None,
        position_id=deal.positionId or None,
        order_id=deal.orderId or None,
        symbol_id=deal.symbolId or None,
        side=side,
        volume=deal.filledVolume or deal.volume or None,
        price=scale_price(deal.executionPrice) if deal.executionPrice else None,
        ts_ms=deal.executionTimestamp or None,
        commission=_money(deal.commission, deal.moneyDigits),
    )


def _execution_names() -> dict[int, str]:
    from ctrader_open_api.messages import OpenApiModelMessages_pb2 as model

    return {value.number: value.name for value in model.ProtoOAExecutionType.DESCRIPTOR.values}


_EXECUTION_NAMES = _execution_names()
