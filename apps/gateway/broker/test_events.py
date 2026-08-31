"""Execution-event normalisation, built from real protobuf messages rather than stand-ins."""

from __future__ import annotations

import pytest
from broker.events import normalise_execution
from ctrader_open_api.messages.OpenApiMessages_pb2 import ProtoOAExecutionEvent
from ctrader_open_api.messages.OpenApiModelMessages_pb2 import (
    ORDER_ACCEPTED,
    ORDER_FILLED,
    ORDER_REJECTED,
    SWAP,
)


def opening_fill() -> ProtoOAExecutionEvent:
    event = ProtoOAExecutionEvent(ctidTraderAccountId=1, executionType=ORDER_FILLED)
    event.order.clientOrderId = "01ABC"
    event.order.orderId = 5
    event.deal.dealId = 10
    event.deal.positionId = 9
    event.deal.orderId = 5
    event.deal.symbolId = 41
    event.deal.tradeSide = 1
    event.deal.volume = 100
    event.deal.filledVolume = 100
    event.deal.executionPrice = 200_000_000
    event.deal.executionTimestamp = 1_700_000_000_000
    event.deal.commission = -10
    event.deal.moneyDigits = 2
    return event


def closing_fill() -> ProtoOAExecutionEvent:
    event = opening_fill()
    event.deal.executionPrice = 200_400_000
    event.deal.closePositionDetail.entryPrice = 2000.0
    event.deal.closePositionDetail.grossProfit = 400
    event.deal.closePositionDetail.swap = -5
    event.deal.closePositionDetail.commission = -10
    event.deal.closePositionDetail.moneyDigits = 2
    return event


def test_an_opening_fill_becomes_a_fill_fact() -> None:
    fact = normalise_execution(opening_fill())
    assert fact.kind == "fill"
    assert fact.cid == "01ABC"
    assert fact.position_id == 9
    assert fact.side == "buy"
    assert fact.price == pytest.approx(2000.0)
    assert fact.commission == pytest.approx(-0.10)


def test_a_closing_deal_is_recognised_by_its_close_detail() -> None:
    """The broker's own gross profit and swap are preferred over anything computed locally."""
    fact = normalise_execution(closing_fill())
    assert fact.kind == "close"
    assert fact.position_id == 9
    assert fact.price == pytest.approx(2004.0)
    assert fact.gross_pnl == pytest.approx(4.0)
    assert fact.swap == pytest.approx(-0.05)


def test_money_fields_respect_their_own_digits() -> None:
    event = closing_fill()
    event.deal.closePositionDetail.moneyDigits = 3
    event.deal.closePositionDetail.grossProfit = 4000
    assert normalise_execution(event).gross_pnl == pytest.approx(4.0)


def test_a_rejection_carries_its_reason_back_to_the_cid() -> None:
    event = ProtoOAExecutionEvent(ctidTraderAccountId=1, executionType=ORDER_REJECTED,
                                  errorCode="NOT_ENOUGH_MONEY")
    event.order.clientOrderId = "01ABC"
    fact = normalise_execution(event)
    assert fact.kind == "reject"
    assert fact.cid == "01ABC"
    assert fact.reason == "NOT_ENOUGH_MONEY"


def test_an_acceptance_is_reported_but_is_not_a_fill() -> None:
    event = ProtoOAExecutionEvent(ctidTraderAccountId=1, executionType=ORDER_ACCEPTED)
    event.order.clientOrderId = "01ABC"
    assert normalise_execution(event).kind == "accepted"


def test_events_the_journal_does_not_care_about_are_ignored() -> None:
    event = ProtoOAExecutionEvent(ctidTraderAccountId=1, executionType=SWAP)
    assert normalise_execution(event).kind == "ignored"
