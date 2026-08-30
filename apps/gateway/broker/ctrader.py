"""cTrader Open API, in-process.

The module that checks risk calls this one directly. There is no sidecar, no
local RPC, and no second container -- which also means an exception raised in
here would take the HUD and the journal down with it, so every inbound callback
crosses the :class:`~apps.gateway.broker.base.Containment` boundary.

What lives where, because the Open API splits it awkwardly:

* ``ProtoOASymbolsListReq`` returns ``ProtoOALightSymbol`` -- ids, names, and
  base/quote asset ids, and **no volume spec at all**.
* ``ProtoOASymbolByIdReq`` returns ``ProtoOASymbol`` -- digits, pipPosition,
  lotSize, min/step/max volume, and **no name and no assets**.

:class:`SymbolSpec` is the join of the two. Reading min/step/max off the light
record is the bug that sends a thousand times the intended ounces of gold, so
this module refuses a symbol it has not resolved through *both* calls.
"""

from __future__ import annotations

import asyncio
import contextlib
import logging
import os
import time
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, Literal

from ctrader_open_api.messages import OpenApiCommonMessages_pb2 as common
from ctrader_open_api.messages import OpenApiMessages_pb2 as msgs
from ctrader_open_api.messages import OpenApiModelMessages_pb2 as model

from ..config import Config
from .base import Broker, BrokerFault, Containment
from .conversion import AssetGraph
from .transport import Transport, TransportError
from .types import (
    RELATIVE_UNITS_PER_PRICE,
    AccountSnapshot,
    Asset,
    BrokerHealth,
    BrokerPosition,
    BrokerQuote,
    BrokerResult,
    OpenRequest,
    Side,
    SymbolSpec,
)
from .volume import money_digits_of, scale_money, volume_to_lots

log = logging.getLogger("ev.broker.ctrader")

HEARTBEAT_S = 10.0

#: How often the watchdog checks whether the broker link came back.
RECONNECT_POLL_S = 5.0

_SIDE_TO_PROTO = {"buy": model.BUY, "sell": model.SELL}
_PROTO_TO_SIDE: dict[int, Side] = {model.BUY: "buy", model.SELL: "sell"}

_EXEC_NAME = {
    v.number: v.name
    for v in model.DESCRIPTOR.enum_types_by_name["ProtoOAExecutionType"].values
}

#: Open API error codes worth turning into a specific reject rather than a
#: generic broker_error. Anything unmapped keeps its code in the detail.
_ERROR_REASONS: dict[str, str] = {
    "TRADING_BAD_VOLUME": "lot_step",
    "TRADING_BAD_STOPS": "broker_error",
    "NOT_ENOUGH_MONEY": "broker_error",
    "SYMBOL_NOT_FOUND": "unknown_symbol",
    "MARKET_CLOSED": "session_closed",
    "TRADING_DISABLED": "locked",
    "CONNECTIONS_LIMIT_EXCEEDED": "rate_limited",
    "REQUEST_FREQUENCY_EXCEEDED": "rate_limited",
}


@dataclass(frozen=True)
class ExecutionUpdate:
    """One broker fact about an order or position, already translated.

    The gateway turns these into ``order.ack`` / ``order.upd`` frames and
    ``position_event`` rows. Prices here are real prices, not scaled integers --
    ``ProtoOAPosition.price`` and ``ProtoOADeal.executionPrice`` are doubles,
    unlike spot bid/ask.
    """

    kind: Literal["accepted", "filled", "closed", "amended", "rejected", "cancelled", "expired"]
    ts: int
    cid: str | None = None
    order_id: int | None = None
    position_id: int | None = None
    sym: str | None = None
    side: Side | None = None
    volume: int = 0
    price: float | None = None
    sl: float | None = None
    tp: float | None = None
    entry: float | None = None
    gross_pnl: float | None = None
    commission: float = 0.0
    swap: float = 0.0
    reason: str | None = None


ExecutionSink = Callable[[ExecutionUpdate], None]
SpotSink = Callable[[str, int, int, int], None]  # sym, bid, ask, ts_ms


class CTraderBroker(Broker):
    def __init__(
        self,
        cfg: Config,
        transport: Transport,
        *,
        containment: Containment | None = None,
        graph: AssetGraph | None = None,
        env: dict[str, str] | None = None,
    ) -> None:
        super().__init__(containment)
        self.cfg = cfg
        self.transport = transport
        self.graph = graph or AssetGraph()
        self.env = dict(os.environ if env is None else env)

        self.account_id: int = 0
        self.authed = False
        self.is_live: bool | None = None
        self.currency = "USD"
        self._specs: dict[str, SymbolSpec] = {}
        self._by_id: dict[int, SymbolSpec] = {}
        self._quotes: dict[str, BrokerQuote] = {}
        self._positions: dict[int, BrokerPosition] = {}
        self._last_heartbeat_ms: int | None = None
        self._heartbeat_task: asyncio.Task | None = None
        self._watchdog_task: asyncio.Task | None = None
        self.reconnects = 0
        self._on_execution: ExecutionSink | None = None
        self._on_spot: SpotSink | None = None
        self._on_reconnect: Callable[[list[BrokerPosition]], None] | None = None
        self._detail: str | None = None

        transport.set_message_sink(self.containment("inbound")(self._on_message))

    # -- wiring -------------------------------------------------------------

    def set_execution_sink(self, sink: ExecutionSink) -> None:
        self._on_execution = sink

    def set_spot_sink(self, sink: SpotSink) -> None:
        """Raw spot tap. The tape ring subscribes here, *before* the browser
        conflation, so ``n_ticks`` reflects real tick density."""
        self._on_spot = sink

    # -- connect ------------------------------------------------------------

    async def start(self) -> None:
        await self.transport.connect()
        await self._app_auth()
        await self._resolve_account()
        await self._account_auth()
        await self._load_assets()
        await self._load_symbols()
        await self._subscribe_spots()
        await self.reconcile()
        self.authed = True
        self._heartbeat_task = asyncio.create_task(self._heartbeat_loop())
        if self._watchdog_task is None:
            self._watchdog_task = asyncio.create_task(self._watchdog_loop())
        log.info(
            "cTrader ready: account=%s symbols=%s",
            self.account_id,
            ",".join(sorted(self._specs)),
        )

    async def _watchdog_loop(self) -> None:
        """Re-auth and reconcile after the socket comes back.

        With the sidecar gone there is one link rather than two, so the state
        machine has one axis: either Spotware is reachable or it is not. On
        the way back cTrader is the source of truth, so the local book is
        rebuilt from Reconcile rather than trusted across the gap.
        """
        while True:
            try:
                await asyncio.sleep(RECONNECT_POLL_S)
                if self.transport.connected:
                    continue

                self.authed = False
                self._detail = "reconnecting"
                await self.transport.connect()
                await self._app_auth()
                await self._account_auth()
                await self._subscribe_spots()
                positions = await self.reconcile()
                self.authed = True
                self._detail = None
                self.reconnects += 1
                log.info("broker link restored; reconciled %s position(s)", len(positions))
                if self._on_reconnect is not None:
                    self._on_reconnect(positions)
            except asyncio.CancelledError:
                return
            except Exception as exc:
                # Keep trying. A gateway that gives up on the broker is a
                # gateway the player has to restart mid-evening.
                self._detail = f"reconnect failed: {exc}"[:200]
                self.containment.report("reconnect", str(exc))

    def set_reconnect_sink(self, sink: Callable[[list[BrokerPosition]], None]) -> None:
        self._on_reconnect = sink

    async def stop(self) -> None:
        if self._watchdog_task is not None:
            self._watchdog_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._watchdog_task
            self._watchdog_task = None
        if self._heartbeat_task is not None:
            self._heartbeat_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._heartbeat_task
            self._heartbeat_task = None
        await self.transport.disconnect()
        self.authed = False

    async def _app_auth(self) -> None:
        client_id = self.env.get(self.cfg.broker.client_id_env, "")
        secret = self.env.get(self.cfg.broker.client_secret_env, "")
        req = msgs.ProtoOAApplicationAuthReq(clientId=client_id, clientSecret=secret)
        await self._call(req, "application auth")

    async def _resolve_account(self) -> None:
        """``isLive`` is on ``ProtoOACtidTraderAccount``, not on
        ``ProtoOATrader`` -- so the live check happens here, before account auth
        and long before anything could place an order."""
        token = self.env.get(self.cfg.broker.token_env, "")
        res = await self._call(
            msgs.ProtoOAGetAccountListByAccessTokenReq(accessToken=token),
            "account list",
        )
        wanted = int(self.env.get(self.cfg.broker.account_id_env, "0") or 0)
        accounts = list(res.ctidTraderAccount)
        if not accounts:
            raise BrokerFault("access token has no trading accounts")

        account = next(
            (a for a in accounts if a.ctidTraderAccountId == wanted), None
        )
        if account is None:
            raise BrokerFault(
                f"{self.cfg.broker.account_id_env}={wanted} is not on this token "
                f"(saw {[a.ctidTraderAccountId for a in accounts]})"
            )

        self.is_live = bool(account.isLive)
        if self.is_live:
            raise BrokerFault(
                f"account {account.ctidTraderAccountId} is LIVE. This product "
                "refuses real money; open an IC Markets demo account instead."
            )
        self.account_id = account.ctidTraderAccountId

    async def _account_auth(self) -> None:
        token = self.env.get(self.cfg.broker.token_env, "")
        try:
            await self._call(
                msgs.ProtoOAAccountAuthReq(
                    ctidTraderAccountId=self.account_id, accessToken=token
                ),
                "account auth",
            )
        except BrokerFault as exc:
            if "CH_ACCESS_TOKEN_INVALID" in str(exc) or "EXPIRED" in str(exc).upper():
                await self._refresh_token()
                await self._call(
                    msgs.ProtoOAAccountAuthReq(
                        ctidTraderAccountId=self.account_id,
                        accessToken=self.env.get(self.cfg.broker.token_env, ""),
                    ),
                    "account auth (post-refresh)",
                )
            else:
                raise

    async def _refresh_token(self) -> None:
        """Refresh the manually provisioned token. No auth helper ships in v1 --
        the gateway only refreshes what the README's consent flow provided."""
        refresh = self.env.get(self.cfg.broker.refresh_env, "")
        if not refresh:
            raise BrokerFault(
                f"{self.cfg.broker.refresh_env} is empty and the access token "
                "was refused. Re-run the manual consent flow in README.md."
            )
        res = await self._call(
            msgs.ProtoOARefreshTokenReq(refreshToken=refresh), "token refresh"
        )
        self.env[self.cfg.broker.token_env] = res.accessToken
        if res.refreshToken:
            self.env[self.cfg.broker.refresh_env] = res.refreshToken
        self._persist_tokens()

    def _persist_tokens(self) -> None:
        """Refreshed tokens go to the protected app volume at mode 0600 --
        never to git, a log, the browser, or a backup archive."""
        from pathlib import Path

        path = Path(self.cfg.db_path).parent / "ctrader-tokens.env"
        path.parent.mkdir(parents=True, exist_ok=True)
        body = (
            f"{self.cfg.broker.token_env}={self.env[self.cfg.broker.token_env]}\n"
            f"{self.cfg.broker.refresh_env}={self.env[self.cfg.broker.refresh_env]}\n"
        )
        fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
        with os.fdopen(fd, "w") as fh:
            fh.write(body)
        os.chmod(path, 0o600)
        log.info("refreshed cTrader token persisted to %s (0600)", path)

    async def _load_assets(self) -> None:
        res = await self._call(
            msgs.ProtoOAAssetListReq(ctidTraderAccountId=self.account_id), "asset list"
        )
        self.graph.set_assets(
            [Asset(asset_id=a.assetId, name=a.name) for a in res.asset]
        )

    async def _load_symbols(self) -> None:
        """Two calls per symbol, on purpose. See the module docstring."""
        res = await self._call(
            msgs.ProtoOASymbolsListReq(ctidTraderAccountId=self.account_id),
            "symbols list",
        )
        light = {s.symbolName.upper(): s for s in res.symbol}

        for name in self.cfg.symbol_names:
            entry = light.get(name.upper())
            if entry is None:
                # IC Markets uses plain unsuffixed names. A missing one means
                # the wrong broker or the wrong account, and guessing at a
                # suffixed variant would trade something the player did not pick.
                raise BrokerFault(
                    f"{name} is not on this account. Available sample: "
                    f"{sorted(light)[:8]}"
                )
            detail = await self._call(
                msgs.ProtoOASymbolByIdReq(
                    ctidTraderAccountId=self.account_id, symbolId=[entry.symbolId]
                ),
                f"symbol detail {name}",
            )
            if not detail.symbol:
                raise BrokerFault(f"{name}: SymbolById returned no spec")
            full = detail.symbol[0]
            spec = SymbolSpec(
                symbol_id=entry.symbolId,
                name=name,
                digits=full.digits,
                pip_position=full.pipPosition,
                lot_size=full.lotSize,
                min_volume=full.minVolume,
                step_volume=full.stepVolume,
                max_volume=full.maxVolume,
                base_asset_id=entry.baseAssetId,
                quote_asset_id=entry.quoteAssetId,
            )
            if spec.lot_size <= 0 or spec.step_volume <= 0:
                raise BrokerFault(
                    f"{name}: unusable volume spec "
                    f"(lotSize={spec.lot_size}, stepVolume={spec.step_volume})"
                )
            self._specs[name] = spec
            self._by_id[entry.symbolId] = spec
            self.graph.add_symbol(spec)
            # Logged at subscribe time so a wrong scale is visible in the log
            # before it is visible in the account.
            log.info(
                "symbol %s id=%s lotSize=%s min/step/max=%s/%s/%s digits=%s",
                name, spec.symbol_id, spec.lot_size,
                spec.min_volume, spec.step_volume, spec.max_volume, spec.digits,
            )

        # Conversion pairs the configured symbols do not themselves provide.
        for entry in light.values():
            if entry.symbolName.upper() not in self._specs:
                self.graph.add_symbol(
                    SymbolSpec(
                        symbol_id=entry.symbolId, name=entry.symbolName.upper(),
                        digits=5, pip_position=4, lot_size=0, min_volume=0,
                        step_volume=0, max_volume=0,
                        base_asset_id=entry.baseAssetId,
                        quote_asset_id=entry.quoteAssetId,
                    )
                )

    async def _subscribe_spots(self) -> None:
        ids = [s.symbol_id for s in self._specs.values()]
        if not ids:
            return
        await self._call(
            msgs.ProtoOASubscribeSpotsReq(
                ctidTraderAccountId=self.account_id, symbolId=ids
            ),
            "subscribe spots",
        )

    async def _heartbeat_loop(self) -> None:
        """``ProtoHeartbeatEvent`` keeps the proxy from dropping an idle socket."""
        while True:
            await asyncio.sleep(HEARTBEAT_S)
            try:
                self.transport.send_nowait(common.ProtoHeartbeatEvent())
                self._last_heartbeat_ms = int(time.time() * 1000)
            except Exception as exc:
                self.containment.report("heartbeat", str(exc))

    # -- inbound ------------------------------------------------------------

    def _on_message(self, message: Any) -> None:
        name = type(message).__name__
        if name == "ProtoOASpotEvent":
            self._handle_spot(message)
        elif name == "ProtoOAExecutionEvent":
            update = self._translate_execution(message)
            if update is not None:
                # Apply before emitting: the local book is this module's own
                # state and must not depend on whether anyone subscribed.
                self.apply_execution(update)
                self._emit_execution(update)
        elif name == "ProtoHeartbeatEvent":
            self._last_heartbeat_ms = int(time.time() * 1000)
        elif name == "ProtoOAErrorRes":
            self.containment.report("broker_error", _error_text(message))

    def _handle_spot(self, event: Any) -> None:
        spec = self._by_id.get(event.symbolId)
        if spec is None:
            return
        ts = event.timestamp if event.HasField("timestamp") else int(time.time() * 1000)
        prev = self._quotes.get(spec.name)
        # A spot event carries only what moved, so an ask-only tick must keep
        # the last bid rather than publishing a zero and blowing up the spread.
        bid_raw = event.bid if event.HasField("bid") else _unscale(prev.bid if prev else 0)
        ask_raw = event.ask if event.HasField("ask") else _unscale(prev.ask if prev else 0)
        if not bid_raw or not ask_raw:
            return

        bid = bid_raw / RELATIVE_UNITS_PER_PRICE
        ask = ask_raw / RELATIVE_UNITS_PER_PRICE
        self._quotes[spec.name] = BrokerQuote(
            sym=spec.name, bid=bid, ask=ask, ts=ts, digits=spec.digits
        )
        self.graph.observe(spec.name, bid, ask, ts)
        if self._on_spot:
            self._on_spot(spec.name, int(bid_raw), int(ask_raw), ts)

    def _translate_execution(self, event: Any) -> ExecutionUpdate | None:
        kind_name = _EXEC_NAME.get(event.executionType, str(event.executionType))
        ts = int(time.time() * 1000)
        order = event.order if event.HasField("order") else None
        position = event.position if event.HasField("position") else None
        deal = event.deal if event.HasField("deal") else None

        cid = order.clientOrderId if order and order.clientOrderId else None
        spec = None
        for source in (position, order):
            if source is not None and source.HasField("tradeData"):
                spec = self._by_id.get(source.tradeData.symbolId)
                break
        if spec is None and deal is not None:
            spec = self._by_id.get(deal.symbolId)

        side: Side | None = None
        volume = 0
        for source in (position, order):
            if source is not None and source.HasField("tradeData"):
                side = _PROTO_TO_SIDE.get(source.tradeData.tradeSide)
                volume = source.tradeData.volume
                break

        base = dict(
            ts=ts, cid=cid,
            order_id=order.orderId if order else None,
            position_id=(position.positionId if position else
                         (order.positionId if order and order.HasField("positionId") else None)),
            sym=spec.name if spec else None,
            side=side, volume=volume,
        )

        if kind_name == "ORDER_ACCEPTED":
            return ExecutionUpdate(kind="accepted", **base)

        if kind_name in {"ORDER_FILLED", "ORDER_PARTIAL_FILL"}:
            closing = bool(order and order.closingOrder)
            price = deal.executionPrice if deal and deal.HasField("executionPrice") else None
            if closing and deal is not None and deal.HasField("closePositionDetail"):
                d = deal.closePositionDetail
                digits = money_digits_of(d)
                return ExecutionUpdate(
                    kind="closed", price=price, entry=d.entryPrice,
                    gross_pnl=scale_money(d.grossProfit, digits),
                    commission=scale_money(d.commission, digits),
                    swap=scale_money(d.swap, digits),
                    **base,
                )
            return ExecutionUpdate(
                kind="closed" if closing else "filled",
                price=price,
                sl=position.stopLoss if position and position.HasField("stopLoss") else None,
                tp=position.takeProfit if position and position.HasField("takeProfit") else None,
                **base,
            )

        if kind_name == "ORDER_REPLACED":
            return ExecutionUpdate(
                kind="amended",
                sl=position.stopLoss if position and position.HasField("stopLoss") else None,
                tp=position.takeProfit if position and position.HasField("takeProfit") else None,
                **base,
            )

        if kind_name == "ORDER_REJECTED":
            return ExecutionUpdate(
                kind="rejected", reason=_error_code_name(event.errorCode), **base
            )
        if kind_name == "ORDER_CANCELLED":
            return ExecutionUpdate(kind="cancelled", **base)
        if kind_name == "ORDER_EXPIRED":
            return ExecutionUpdate(kind="expired", **base)
        return None

    # -- Broker interface ---------------------------------------------------

    async def health(self) -> BrokerHealth:
        return BrokerHealth(
            connected=bool(self.transport.connected),
            authed=self.authed,
            account_id=self.account_id or None,
            last_heartbeat_ms=self._last_heartbeat_ms,
            symbols=sorted(self._specs),
            detail=self._detail,
        )

    async def account(self) -> AccountSnapshot:
        res = await self._call(
            msgs.ProtoOATraderReq(ctidTraderAccountId=self.account_id), "trader"
        )
        trader = res.trader
        digits = money_digits_of(trader)
        balance = scale_money(trader.balance, digits)
        open_pnl = sum(p.pnl for p in self._positions.values())
        return AccountSnapshot(
            account_id=self.account_id,
            is_live=bool(self.is_live),
            currency=self.currency,
            balance=balance,
            # cTrader is the money source of truth for balance. Equity while a
            # position is open is balance plus the open P/L we are tracking --
            # it is never re-derived by summing fills.
            equity=balance + open_pnl,
            ts=int(time.time() * 1000),
        )

    async def snapshot(self) -> dict[str, BrokerQuote]:
        return dict(self._quotes)

    async def positions(self) -> list[BrokerPosition]:
        return list(self._positions.values())

    def symbol_spec(self, sym: str) -> SymbolSpec | None:
        return self._specs.get(sym)

    async def place(self, req: OpenRequest) -> BrokerResult:
        spec = self._specs.get(req.sym)
        if spec is None:
            return BrokerResult(ok=False, cid=req.cid, reason="unknown_symbol", detail=req.sym)
        if req.volume < spec.min_volume or req.volume > spec.max_volume:
            return BrokerResult(
                ok=False, cid=req.cid, reason="max_lots",
                detail=f"volume {req.volume} outside [{spec.min_volume}, {spec.max_volume}]",
            )

        order = msgs.ProtoOANewOrderReq(
            ctidTraderAccountId=self.account_id,
            symbolId=spec.symbol_id,
            orderType=model.MARKET,
            tradeSide=_SIDE_TO_PROTO[req.side],
            volume=req.volume,
            label=req.label,
            clientOrderId=req.cid,
        )
        # MARKET carries relative distances only; absolute stopLoss/takeProfit
        # are not valid on this order type. An SL/TP edit later goes through
        # amend_position_sl_tp, behind its own clutch+confirm.
        if req.relative_sl:
            order.relativeStopLoss = req.relative_sl
        if req.relative_tp:
            order.relativeTakeProfit = req.relative_tp

        return await self._order_call(order, req.cid)

    async def close(self, position_id: int, cid: str) -> BrokerResult:
        position = self._positions.get(position_id)
        if position is None:
            return BrokerResult(
                ok=False, cid=cid, reason="broker_error",
                detail=f"position {position_id} is not open",
            )
        # Full close only. Partial closes are outside this product, so the
        # volume sent is always the whole position.
        req = msgs.ProtoOAClosePositionReq(
            ctidTraderAccountId=self.account_id,
            positionId=position_id,
            volume=position.volume,
        )
        return await self._order_call(req, cid)

    async def amend_position_sl_tp(
        self, position_id: int, cid: str, sl: float | None, tp: float | None
    ) -> BrokerResult:
        req = msgs.ProtoOAAmendPositionSLTPReq(
            ctidTraderAccountId=self.account_id, positionId=position_id
        )
        # Absolute prices here, unlike the relative distances on a new MARKET
        # order. Leaving a field unset clears that protection, so only set what
        # the player actually asked to change.
        if sl is not None:
            req.stopLoss = sl
        if tp is not None:
            req.takeProfit = tp
        return await self._order_call(req, cid)

    async def trendbars(
        self, sym: str, timeframe: str = "M5", count: int = 200
    ) -> list[tuple[int, float, float, float, float]]:
        """M5 history for the chart seed, as ``(ts_s, o, h, l, c)``.

        ``ProtoOATrendbar`` is **delta encoded**: ``low`` is the only absolute
        price, and open/high/close are unsigned offsets *above* it. Reading
        ``deltaOpen`` as a price is the bug that draws a chart pinned near zero.
        Timestamps arrive as minutes since the epoch, not milliseconds.

        Seeded once per symbol per session -- the history endpoint is limited to
        roughly 5 req/s and live bars cover everything after the seed.
        """
        spec = self._specs.get(sym)
        if spec is None:
            raise BrokerFault(f"{sym} is not a resolved symbol")
        period = _PERIODS.get(timeframe)
        if period is None:
            raise BrokerFault(f"{timeframe} is not a supported trendbar period")

        seconds = _PERIOD_SECONDS[timeframe]
        now_ms_ = int(time.time() * 1000)
        req = msgs.ProtoOAGetTrendbarsReq(
            ctidTraderAccountId=self.account_id,
            symbolId=spec.symbol_id,
            period=period,
            fromTimestamp=now_ms_ - count * seconds * 1000,
            toTimestamp=now_ms_,
        )
        res = await self._call(req, f"trendbars {sym} {timeframe}")

        bars: list[tuple[int, float, float, float, float]] = []
        for tb in res.trendbar:
            low = tb.low
            bars.append((
                tb.utcTimestampInMinutes * 60,
                _px(low + tb.deltaOpen, spec.digits),
                _px(low + tb.deltaHigh, spec.digits),
                _px(low, spec.digits),
                _px(low + tb.deltaClose, spec.digits),
            ))
        bars.sort(key=lambda b: b[0])
        return bars

    async def reconcile(self) -> list[BrokerPosition]:
        """cTrader is the source of truth after any reconnect. The local book is
        replaced, never merged -- a merge would resurrect a position the broker
        already closed while we were away."""
        res = await self._call(
            msgs.ProtoOAReconcileReq(ctidTraderAccountId=self.account_id), "reconcile"
        )
        book: dict[int, BrokerPosition] = {}
        for p in res.position:
            if p.positionStatus != model.POSITION_STATUS_OPEN:
                continue
            spec = self._by_id.get(p.tradeData.symbolId)
            if spec is None:
                continue
            digits = money_digits_of(p)
            book[p.positionId] = BrokerPosition(
                position_id=p.positionId,
                sym=spec.name,
                side=_PROTO_TO_SIDE.get(p.tradeData.tradeSide, "buy"),
                volume=p.tradeData.volume,
                entry=p.price,
                opened_at=p.tradeData.openTimestamp,
                sl=p.stopLoss if p.HasField("stopLoss") else None,
                tp=p.takeProfit if p.HasField("takeProfit") else None,
                commission=scale_money(p.commission, digits),
                swap=scale_money(p.swap, digits),
                label=p.tradeData.label or None,
            )
        self._positions = book
        return list(book.values())

    def apply_execution(self, update: ExecutionUpdate) -> None:
        """Keep the local book in step with an execution event. Separate from
        translation so the gateway can journal the same update it applies."""
        if update.position_id is None:
            return
        if update.kind in {"closed", "cancelled", "expired"}:
            self._positions.pop(update.position_id, None)
            return
        if update.kind == "filled" and update.sym and update.side:
            spec = self._specs.get(update.sym)
            self._positions[update.position_id] = BrokerPosition(
                position_id=update.position_id,
                sym=update.sym,
                side=update.side,
                volume=update.volume,
                entry=update.price or 0.0,
                opened_at=update.ts,
                sl=update.sl,
                tp=update.tp,
                label=None,
            )
            if spec is None:
                log.warning("filled %s with no cached spec", update.sym)
        elif update.kind == "amended":
            existing = self._positions.get(update.position_id)
            if existing is not None:
                self._positions[update.position_id] = BrokerPosition(
                    **{**existing.__dict__, "sl": update.sl, "tp": update.tp}
                )

    def lots_of(self, position: BrokerPosition) -> float:
        spec = self._specs.get(position.sym)
        return volume_to_lots(position.volume, spec) if spec else 0.0

    # -- plumbing -----------------------------------------------------------

    def _emit_execution(self, update: ExecutionUpdate) -> None:
        """Hand an update to the sink, contained.

        The order has already reached the broker by this point. A listener that
        raises is a reporting bug; letting it turn a placed order into a failed
        one would be a trading bug.
        """
        if self._on_execution is None:
            return
        try:
            self._on_execution(update)
        except Exception as exc:
            self.containment.report("execution_sink", str(exc), update.cid)

    async def _call(self, message: Any, what: str, timeout: float = 15.0) -> Any:
        try:
            res = await self.transport.request(message, timeout=timeout)
        except TransportError as exc:
            raise BrokerFault(f"{what}: {exc}") from exc
        except asyncio.TimeoutError:
            raise BrokerFault(f"{what}: timed out after {timeout}s") from None
        if type(res).__name__ == "ProtoOAErrorRes":
            raise BrokerFault(f"{what}: {_error_text(res)}")
        return res

    async def _order_call(self, message: Any, cid: str) -> BrokerResult:
        """Broker-changing calls answer with an execution event, an error, or a
        rejection. All three become a ``BrokerResult`` -- none of them may
        escape as an exception, because this runs on the order hot path."""
        try:
            res = await self.transport.request(message, client_msg_id=cid, timeout=15.0)
        except Exception as exc:
            self.containment.report("order", f"{type(message).__name__}: {exc}", cid)
            return BrokerResult(ok=False, cid=cid, reason="broker_down", detail=str(exc)[:200])

        name = type(res).__name__
        if name == "ProtoOAErrorRes":
            code = _error_code_name(res.errorCode) if res.HasField("errorCode") else ""
            return BrokerResult(
                ok=False, cid=cid,
                reason=_ERROR_REASONS.get(code, "broker_error"),
                detail=_error_text(res),
            )
        if name != "ProtoOAExecutionEvent":
            return BrokerResult(ok=False, cid=cid, reason="broker_error", detail=name)

        update = self._translate_execution(res)
        if update is None:
            return BrokerResult(ok=False, cid=cid, reason="broker_error", detail="unmapped event")
        if update.kind == "rejected":
            code = update.reason or ""
            return BrokerResult(
                ok=False, cid=cid,
                reason=_ERROR_REASONS.get(code, "broker_error"), detail=code,
            )
        self.apply_execution(update)
        self._emit_execution(update)
        return BrokerResult(
            ok=True, cid=cid, order_id=update.order_id, position_id=update.position_id
        )


#: Trendbar periods the HUD offers, mapped to the Open API enum.
_PERIODS: dict[str, int] = {
    "M1": model.M1,
    "M5": model.M5,
    "M15": model.M15,
    "H1": model.H1,
    "H4": model.H4,
    "D1": model.D1,
}

_PERIOD_SECONDS: dict[str, int] = {
    "M1": 60, "M5": 300, "M15": 900, "H1": 3600, "H4": 14_400, "D1": 86_400,
}


def _px(raw: int, digits: int) -> float:
    return round(raw / RELATIVE_UNITS_PER_PRICE, digits)


def _unscale(price: float) -> int:
    return int(round(price * RELATIVE_UNITS_PER_PRICE))


def _error_code_name(code: Any) -> str:
    return str(code)


def _error_text(res: Any) -> str:
    code = res.errorCode if res.HasField("errorCode") else "?"
    desc = res.description if res.HasField("description") else ""
    return f"{code} {desc}".strip()
