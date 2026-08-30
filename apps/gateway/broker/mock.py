"""A mock cTrader endpoint that speaks real Protobuf.

Turned on with ``broker.transport: mock``. It replaces only the *socket*: the
gateway still builds genuine ``ProtoOANewOrderReq`` messages, and this module
parses them and answers with genuine ``ProtoOAExecutionEvent`` messages. So the
parts most likely to be wrong -- symbol mapping, the lots/volume scale,
execution-event translation, the ``isLive`` guard, error-code mapping -- are
exercised for real, without credentials.

What it is not: a matching engine, a price model, or a substitute for phase 2's
acceptance run against Spotware. Its symbol specs are shaped like
``ProtoOASymbol`` but they are **invented**, so a green test here says the
gateway handles the shape correctly, never that the numbers match IC Markets.
Phase 2's success criterion is still a real ``SymbolsList`` + ``SymbolById``
dump, and a hand-verified 0.01-lot gold round trip in cTrader web.
"""

from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import dataclass, field
from typing import Any

from ctrader_open_api.messages import OpenApiCommonMessages_pb2 as common
from ctrader_open_api.messages import OpenApiMessages_pb2 as msgs
from ctrader_open_api.messages import OpenApiModelMessages_pb2 as model

from .transport import MessageSink
from .types import RELATIVE_UNITS_PER_PRICE

log = logging.getLogger("ev.broker.mock")


@dataclass(frozen=True)
class MockSymbol:
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
    bid: float
    ask: float


ASSETS = {840: "USD", 978: "EUR", 826: "GBP", 392: "JPY", 41: "XAU"}

# One gold lot is 100 oz -> 10_000 cents of a unit. One FX lot is 100_000 units
# -> 10_000_000. The three-orders-of-magnitude gap between them is the whole
# reason lots are never converted with a hardcoded constant.
SYMBOLS: tuple[MockSymbol, ...] = (
    MockSymbol(41, "XAUUSD", 2, 2, 10_000, 100, 100, 1_000_000, 41, 840, 2340.15, 2340.35),
    MockSymbol(1, "EURUSD", 5, 4, 10_000_000, 100_000, 100_000, 10_000_000_000, 978, 840, 1.08501, 1.08513),
    MockSymbol(2, "GBPUSD", 5, 4, 10_000_000, 100_000, 100_000, 10_000_000_000, 826, 840, 1.27010, 1.27024),
    MockSymbol(4, "USDJPY", 3, 2, 10_000_000, 100_000, 100_000, 10_000_000_000, 840, 392, 150.004, 150.022),
)


@dataclass
class MockPosition:
    position_id: int
    symbol_id: int
    side: int
    volume: int
    entry: float
    opened_at: int
    sl: float | None = None
    tp: float | None = None
    label: str = ""


@dataclass
class MockState:
    """Everything a test may want to steer, in one place."""

    account_id: int = 5_100_001
    is_live: bool = False
    balance_cents: int = 1_000_000  # 10,000.00 at moneyDigits 2
    access_token: str = "mock-access-token"
    refresh_token: str = "mock-refresh-token"
    #: Set to a ProtoOAErrorCode name to make the next order fail that way.
    reject_next_order_with: str | None = None
    #: Set to make account auth fail once, exercising the refresh path.
    expire_access_token_once: bool = False
    positions: dict[int, MockPosition] = field(default_factory=dict)
    next_position_id: int = 7_000_001
    next_order_id: int = 9_000_001
    sent: list[Any] = field(default_factory=list)


class MockTransport:
    """Answers requests in process. Same interface as :class:`TwistedTransport`."""

    def __init__(self, state: MockState | None = None) -> None:
        self.state = state or MockState()
        self.connected = False
        self._sink: MessageSink | None = None
        self._by_id = {s.symbol_id: s for s in SYMBOLS}
        self._by_name = {s.name: s for s in SYMBOLS}
        self._subscribed: set[int] = set()

    # -- transport ----------------------------------------------------------

    async def connect(self) -> None:
        self.connected = True
        log.warning("broker.transport=mock -- NO ORDER REACHES ANY BROKER")

    async def disconnect(self) -> None:
        self.connected = False

    def set_message_sink(self, sink: MessageSink) -> None:
        self._sink = sink

    def send_nowait(self, message: Any, *, client_msg_id: str | None = None) -> None:
        self.state.sent.append(message)
        if type(message).__name__ == "ProtoHeartbeatEvent":
            self._push(common.ProtoHeartbeatEvent())

    async def request(
        self, message: Any, *, client_msg_id: str | None = None, timeout: float = 10.0
    ) -> Any:
        if not self.connected:
            raise ConnectionError("mock transport is not connected")
        self.state.sent.append(message)
        handler = getattr(self, f"_on_{type(message).__name__}", None)
        if handler is None:
            return _error("UNSUPPORTED_MESSAGE", type(message).__name__)
        return handler(message)

    def _push(self, message: Any) -> None:
        if self._sink is not None:
            self._sink(message)

    def _push_later(self, message: Any) -> None:
        """Deliver on the next loop tick, so a follow-up event lands *after*
        the reply it follows. Pushing inline would let the gateway see a fill
        before the accept that caused it, which the real API never does."""
        try:
            asyncio.get_running_loop().call_soon(self._push, message)
        except RuntimeError:
            self._push(message)

    # -- auth ---------------------------------------------------------------

    def _on_ProtoOAApplicationAuthReq(self, req: Any) -> Any:
        if not req.clientId or not req.clientSecret:
            return _error("CH_CLIENT_AUTH_FAILURE", "clientId/clientSecret empty")
        return msgs.ProtoOAApplicationAuthRes()

    def _on_ProtoOAGetAccountListByAccessTokenReq(self, req: Any) -> Any:
        res = msgs.ProtoOAGetAccountListByAccessTokenRes(accessToken=req.accessToken)
        account = res.ctidTraderAccount.add()
        account.ctidTraderAccountId = self.state.account_id
        account.isLive = self.state.is_live
        return res

    def _on_ProtoOAAccountAuthReq(self, req: Any) -> Any:
        if self.state.expire_access_token_once:
            self.state.expire_access_token_once = False
            return _error("CH_ACCESS_TOKEN_INVALID", "token expired")
        if req.accessToken != self.state.access_token:
            return _error("CH_ACCESS_TOKEN_INVALID", "unknown token")
        return msgs.ProtoOAAccountAuthRes(ctidTraderAccountId=req.ctidTraderAccountId)

    def _on_ProtoOARefreshTokenReq(self, req: Any) -> Any:
        if req.refreshToken != self.state.refresh_token:
            return _error("CH_ACCESS_TOKEN_INVALID", "unknown refresh token")
        self.state.access_token = "mock-access-token-refreshed"
        return msgs.ProtoOARefreshTokenRes(
            accessToken=self.state.access_token,
            refreshToken=self.state.refresh_token,
            tokenType="bearer",
            expiresIn=2_628_000,
        )

    # -- reference data -----------------------------------------------------

    def _on_ProtoOAAssetListReq(self, req: Any) -> Any:
        res = msgs.ProtoOAAssetListRes(ctidTraderAccountId=req.ctidTraderAccountId)
        for asset_id, name in ASSETS.items():
            a = res.asset.add()
            a.assetId = asset_id
            a.name = name
            a.displayName = name
        return res

    def _on_ProtoOASymbolsListReq(self, req: Any) -> Any:
        res = msgs.ProtoOASymbolsListRes(ctidTraderAccountId=req.ctidTraderAccountId)
        for s in SYMBOLS:
            light = res.symbol.add()
            light.symbolId = s.symbol_id
            light.symbolName = s.name
            light.enabled = True
            light.baseAssetId = s.base_asset_id
            light.quoteAssetId = s.quote_asset_id
        # A light symbol deliberately carries no volume spec, exactly as the
        # real API does -- reading min/step/max from here is the bug this
        # mock has to be able to catch.
        return res

    def _on_ProtoOASymbolByIdReq(self, req: Any) -> Any:
        res = msgs.ProtoOASymbolByIdRes(ctidTraderAccountId=req.ctidTraderAccountId)
        for symbol_id in req.symbolId:
            s = self._by_id.get(symbol_id)
            if s is None:
                return _error("SYMBOL_NOT_FOUND", str(symbol_id))
            full = res.symbol.add()
            full.symbolId = s.symbol_id
            full.digits = s.digits
            full.pipPosition = s.pip_position
            full.lotSize = s.lot_size
            full.minVolume = s.min_volume
            full.stepVolume = s.step_volume
            full.maxVolume = s.max_volume
        return res

    def _on_ProtoOASubscribeSpotsReq(self, req: Any) -> Any:
        self._subscribed.update(req.symbolId)
        return msgs.ProtoOASubscribeSpotsRes(ctidTraderAccountId=req.ctidTraderAccountId)

    def _on_ProtoOATraderReq(self, req: Any) -> Any:
        res = msgs.ProtoOATraderRes(ctidTraderAccountId=req.ctidTraderAccountId)
        res.trader.ctidTraderAccountId = req.ctidTraderAccountId
        res.trader.balance = self.state.balance_cents
        res.trader.moneyDigits = 2
        res.trader.depositAssetId = 840
        return res

    def _on_ProtoOAReconcileReq(self, req: Any) -> Any:
        res = msgs.ProtoOAReconcileRes(ctidTraderAccountId=req.ctidTraderAccountId)
        for p in self.state.positions.values():
            self._fill_position(res.position.add(), p)
        return res

    # -- trading ------------------------------------------------------------

    def _on_ProtoOANewOrderReq(self, req: Any) -> Any:
        if self.state.reject_next_order_with:
            code = self.state.reject_next_order_with
            self.state.reject_next_order_with = None
            return self._rejection(req, code)

        s = self._by_id.get(req.symbolId)
        if s is None:
            return _error("SYMBOL_NOT_FOUND", str(req.symbolId))
        # The broker checks the volume grid itself. If the gateway's conversion
        # is wrong, this is what says so -- which is the point of speaking real
        # protobuf rather than stubbing place().
        if req.volume < s.min_volume or req.volume > s.max_volume:
            return self._rejection(req, "TRADING_BAD_VOLUME")
        if req.volume % s.step_volume:
            return self._rejection(req, "TRADING_BAD_VOLUME")

        now = int(time.time() * 1000)
        entry = s.ask if req.tradeSide == model.BUY else s.bid
        position = MockPosition(
            position_id=self.state.next_position_id,
            symbol_id=s.symbol_id,
            side=req.tradeSide,
            volume=req.volume,
            entry=entry,
            opened_at=now,
            label=req.label,
        )
        # Relative distances are in 1/100000 price units and move against the
        # entry in the direction that protects the trade.
        sign = 1 if req.tradeSide == model.BUY else -1
        if req.HasField("relativeStopLoss") and req.relativeStopLoss:
            position.sl = entry - sign * req.relativeStopLoss / RELATIVE_UNITS_PER_PRICE
        if req.HasField("relativeTakeProfit") and req.relativeTakeProfit:
            position.tp = entry + sign * req.relativeTakeProfit / RELATIVE_UNITS_PER_PRICE

        self.state.next_position_id += 1
        order_id = self.state.next_order_id
        self.state.next_order_id += 1
        self.state.positions[position.position_id] = position

        # Real cTrader answers ORDER_ACCEPTED and then pushes ORDER_FILLED.
        # Reproducing both matters: it is what proves the gateway does not treat
        # "the broker took it" as "the position exists".
        accepted = self._execution(model.ORDER_ACCEPTED, position, order_id,
                                   client_order_id=req.clientOrderId)
        filled = self._execution(model.ORDER_FILLED, position, order_id,
                                 client_order_id=req.clientOrderId, with_deal=True)
        self._push_later(filled)
        return accepted

    def _on_ProtoOAClosePositionReq(self, req: Any) -> Any:
        position = self.state.positions.get(req.positionId)
        if position is None:
            return _error("POSITION_NOT_FOUND", str(req.positionId))
        if req.volume != position.volume:
            # Partial closes are outside this product; the gateway should never
            # ask for one, so the mock refuses rather than quietly allowing it.
            return _error("TRADING_BAD_VOLUME", "partial close is not supported")

        s = self._by_id[position.symbol_id]
        exit_price = s.bid if position.side == model.BUY else s.ask
        units = position.volume / 100
        direction = 1 if position.side == model.BUY else -1
        gross = (exit_price - position.entry) * direction * units

        del self.state.positions[req.positionId]
        order_id = self.state.next_order_id
        self.state.next_order_id += 1

        event = self._execution(model.ORDER_FILLED, position, order_id, closing=True)
        deal = event.deal
        deal.executionPrice = exit_price
        detail = deal.closePositionDetail
        detail.entryPrice = position.entry
        detail.grossProfit = int(round(gross * 100))
        detail.swap = 0
        detail.commission = -300  # -3.00, a plausible round-turn on 0.01 lots
        detail.moneyDigits = 2
        detail.closedVolume = position.volume
        self.state.balance_cents += detail.grossProfit + detail.commission
        return event

    def _on_ProtoOAAmendPositionSLTPReq(self, req: Any) -> Any:
        position = self.state.positions.get(req.positionId)
        if position is None:
            return _error("POSITION_NOT_FOUND", str(req.positionId))
        if req.HasField("stopLoss"):
            position.sl = req.stopLoss
        if req.HasField("takeProfit"):
            position.tp = req.takeProfit
        order_id = self.state.next_order_id
        self.state.next_order_id += 1
        return self._execution(model.ORDER_REPLACED, position, order_id)

    # -- test hooks ---------------------------------------------------------

    def push_spot(
        self, sym: str, bid: float | None = None, ask: float | None = None,
        ts: int | None = None,
    ) -> None:
        """Emit a spot tick. Omitting one side emits a genuinely one-sided
        event, which is how the real feed behaves and what the gateway's
        last-known-side handling has to survive."""
        s = self._by_name[sym]
        event = msgs.ProtoOASpotEvent(
            ctidTraderAccountId=self.state.account_id, symbolId=s.symbol_id
        )
        if bid is not None:
            event.bid = int(round(bid * RELATIVE_UNITS_PER_PRICE))
        if ask is not None:
            event.ask = int(round(ask * RELATIVE_UNITS_PER_PRICE))
        event.timestamp = ts if ts is not None else int(time.time() * 1000)
        self._push(event)

    def push_stop_out(self, position_id: int, price: float) -> None:
        """An SL hit: the broker closes a position with no request from us."""
        position = self.state.positions.pop(position_id)
        event = self._execution(model.ORDER_FILLED, position,
                                self.state.next_order_id, closing=True)
        self.state.next_order_id += 1
        event.order.isStopOut = True
        event.deal.executionPrice = price
        detail = event.deal.closePositionDetail
        detail.entryPrice = position.entry
        units = position.volume / 100
        direction = 1 if position.side == model.BUY else -1
        detail.grossProfit = int(round((price - position.entry) * direction * units * 100))
        detail.moneyDigits = 2
        detail.closedVolume = position.volume
        self._push(event)

    def push_error(self, code: str, description: str = "") -> None:
        self._push(_error(code, description))

    # -- builders -----------------------------------------------------------

    def _fill_position(self, target: Any, p: MockPosition) -> None:
        target.positionId = p.position_id
        target.positionStatus = model.POSITION_STATUS_OPEN
        target.price = p.entry
        target.moneyDigits = 2
        if p.sl is not None:
            target.stopLoss = p.sl
        if p.tp is not None:
            target.takeProfit = p.tp
        target.tradeData.symbolId = p.symbol_id
        target.tradeData.volume = p.volume
        target.tradeData.tradeSide = p.side
        target.tradeData.openTimestamp = p.opened_at
        target.tradeData.label = p.label

    def _execution(
        self, execution_type: int, p: MockPosition, order_id: int, *,
        client_order_id: str = "", closing: bool = False, with_deal: bool = False,
    ) -> Any:
        event = msgs.ProtoOAExecutionEvent(
            ctidTraderAccountId=self.state.account_id, executionType=execution_type
        )
        self._fill_position(event.position, p)
        order = event.order
        order.orderId = order_id
        order.orderType = model.MARKET
        order.orderStatus = (
            model.ORDER_STATUS_FILLED
            if execution_type == model.ORDER_FILLED
            else model.ORDER_STATUS_ACCEPTED
        )
        order.positionId = p.position_id
        order.closingOrder = closing
        if client_order_id:
            order.clientOrderId = client_order_id
        order.tradeData.symbolId = p.symbol_id
        order.tradeData.volume = p.volume
        order.tradeData.tradeSide = p.side
        order.tradeData.openTimestamp = p.opened_at

        if closing or with_deal:
            deal = event.deal
            deal.dealId = order_id
            deal.orderId = order_id
            deal.positionId = p.position_id
            deal.symbolId = p.symbol_id
            deal.volume = p.volume
            deal.filledVolume = p.volume
            deal.tradeSide = p.side
            deal.executionPrice = p.entry
            deal.moneyDigits = 2
        return event

    def _rejection(self, req: Any, code: str) -> Any:
        event = msgs.ProtoOAExecutionEvent(
            ctidTraderAccountId=self.state.account_id,
            executionType=model.ORDER_REJECTED,
        )
        event.errorCode = code
        order = event.order
        order.orderId = self.state.next_order_id
        self.state.next_order_id += 1
        order.orderType = model.MARKET
        order.orderStatus = model.ORDER_STATUS_REJECTED
        if getattr(req, "clientOrderId", ""):
            order.clientOrderId = req.clientOrderId
        order.tradeData.symbolId = req.symbolId
        order.tradeData.volume = req.volume
        order.tradeData.tradeSide = req.tradeSide
        return event


def _error(code: str, description: str = "") -> Any:
    res = msgs.ProtoOAErrorRes(errorCode=code)
    if description:
        res.description = description
    return res
