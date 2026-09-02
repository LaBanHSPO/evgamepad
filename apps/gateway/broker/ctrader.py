"""The cTrader Open API link, spoken in-process by the gateway.

This module is the only thing that talks to Spotware. It owns connect, heartbeat, app and account
auth, the symbol/asset map, spots and trendbars, and the three broker-changing calls: MARKET open
with relative protection, absolute SL/TP amendment on an open position, and a full close.

Two boundaries matter more than the protocol details:

* **Containment.** Every Protobuf callback runs through `broker.contain`. With the sidecar gone,
  an exception escaping into the reactor would take the HUD and the journal down with it.
* **Demo only.** The live host is refused by config at boot, and the account's own `isLive` flag
  is checked against the broker's account list before a single order can be built.

Import hazard: `ctrader_open_api` reaches `twisted.internet.reactor` at import time, so any module
that imports it *before* this one lands on Twisted's default reactor. Nothing outside this module
should import `ctrader_open_api` directly — an import sorter will move it above a first-party
import without a second thought, and `test_reactor_setup.py` proves what that costs.
"""

from __future__ import annotations

import asyncio
import logging
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

from .reactor_setup import install as _install_reactor

# `ctrader_open_api.client` does `from twisted.internet import reactor` at import time, which
# installs the *default* reactor if none exists yet. Installing ours first makes the ordering a
# property of the import graph rather than a rule someone has to remember in main.py.
_install_reactor()

from ctrader_open_api import Client, Protobuf, TcpProtocol  # noqa: E402
from ctrader_open_api.messages.OpenApiCommonMessages_pb2 import (  # noqa: E402
    ProtoHeartbeatEvent,
)
from ctrader_open_api.messages.OpenApiMessages_pb2 import (  # noqa: E402
    ProtoOAAccountAuthReq,
    ProtoOAAmendPositionSLTPReq,
    ProtoOAApplicationAuthReq,
    ProtoOAAssetListReq,
    ProtoOAClosePositionReq,
    ProtoOAErrorRes,
    ProtoOAGetAccountListByAccessTokenReq,
    ProtoOAGetTrendbarsReq,
    ProtoOANewOrderReq,
    ProtoOAReconcileReq,
    ProtoOASubscribeLiveTrendbarReq,
    ProtoOASubscribeSpotsReq,
    ProtoOASymbolByIdReq,
    ProtoOASymbolsListReq,
    ProtoOATraderReq,
)
from ctrader_open_api.messages.OpenApiModelMessages_pb2 import (  # noqa: E402
    BUY as SIDE_BUY,
)
from ctrader_open_api.messages.OpenApiModelMessages_pb2 import (  # noqa: E402
    MARKET,
    ProtoOATrendbarPeriod,
)
from ctrader_open_api.messages.OpenApiModelMessages_pb2 import (  # noqa: E402
    SELL as SIDE_SELL,
)
from twisted.internet.defer import TimeoutError as TwistedTimeoutError  # noqa: E402

from . import Broker, BrokerResult, contain  # noqa: E402
from .conversion import AssetGraph  # noqa: E402
from .volume import (  # noqa: E402
    SymbolSpec,
    lots_to_volume,
    relative_distance,
    scale_price,
)

log = logging.getLogger(__name__)

# Spotware drops a connection with no traffic; stay well inside the window.
HEARTBEAT_S = 10.0

# Non-historical requests are capped at 50/s per connection, historical at 5/s.
TRENDBAR_MIN_INTERVAL_S = 0.2

DEFAULT_REQUEST_TIMEOUT_S = 15.0

# cTrader truncates order labels; `evgp` plus a short cid stays inside it.
LABEL_PREFIX = "evgp"
LABEL_CID_CHARS = 8

SIDES = {"buy": SIDE_BUY, "sell": SIDE_SELL}


class BrokerError(RuntimeError):
    """The broker refused, or the link is not in a state where the call makes sense."""


@dataclass
class Quote:
    """Latest book for a symbol, as scaled protocol integers."""

    symbol: str
    bid: int
    ask: int
    ts_ms: int

    @property
    def mid(self) -> float:
        return scale_price((self.bid + self.ask) // 2)


@dataclass
class LinkState:
    """What `/healthz` and the HUD's link indicator read. Never touches the network."""

    connected: bool = False
    authenticated: bool = False
    account_id: int | None = None
    is_live: bool | None = None
    symbols: int = 0
    last_error: str | None = None
    last_heartbeat_ms: int | None = None
    maintenance_until: int | None = None

    def as_dict(self) -> dict[str, Any]:
        return {
            "connected": self.connected,
            "authenticated": self.authenticated,
            "account_id": self.account_id,
            "is_live": self.is_live,
            "symbols": self.symbols,
            "last_error": self.last_error,
            "maintenance_until": self.maintenance_until,
        }


@dataclass
class CTraderBroker(Broker):
    """OpenApiPy client wrapped in the interface the gateway's risk layer calls directly."""

    host: str
    port: int
    client_id: str
    client_secret: str
    access_token: str
    account_id: int
    symbol_names: tuple[str, ...]
    loop: asyncio.AbstractEventLoop

    state: LinkState = field(default_factory=LinkState)
    specs: dict[str, SymbolSpec] = field(default_factory=dict)
    by_symbol_id: dict[int, SymbolSpec] = field(default_factory=dict)
    assets: dict[int, str] = field(default_factory=dict)
    quotes: dict[str, Quote] = field(default_factory=dict)
    graph: AssetGraph | None = None

    _client: Client | None = field(default=None, init=False)
    _spot_handlers: list[Callable[[Quote], None]] = field(default_factory=list, init=False)
    _event_handlers: list[Callable[[Any], None]] = field(default_factory=list, init=False)
    _heartbeat: asyncio.Task | None = field(default=None, init=False)
    _last_trendbar_req: float = field(default=0.0, init=False)

    # -- lifecycle -------------------------------------------------------------------

    async def connect(self) -> None:
        """Open the Protobuf link, authenticate, and load the symbol and asset maps."""
        client = Client(self.host, self.port, TcpProtocol)
        client.setConnectedCallback(contain(self._on_connected, what="connected"))
        client.setDisconnectedCallback(contain(self._on_disconnected, what="disconnected"))
        client.setMessageReceivedCallback(contain(self._on_message, what="message"))
        self._client = client
        client.startService()

        await asyncio.wait_for(
            self._await_deferred(client.whenConnected()),
            timeout=DEFAULT_REQUEST_TIMEOUT_S,
        )
        self.state.connected = True

        await self._authenticate()
        await self._load_symbols()
        self._heartbeat = self.loop.create_task(self._heartbeat_loop())

    async def disconnect(self) -> None:
        if self._heartbeat is not None:
            self._heartbeat.cancel()
            self._heartbeat = None
        if self._client is not None:
            self._client.stopService()
            self._client = None
        self.state.connected = False
        self.state.authenticated = False

    async def _heartbeat_loop(self) -> None:
        """`ProtoHeartbeatEvent` keeps the proxy from dropping an idle evening."""
        while True:
            await asyncio.sleep(HEARTBEAT_S)
            try:
                await self._send(ProtoHeartbeatEvent(), expect_response=False)
                self.state.last_heartbeat_ms = int(time.time() * 1000)
            except Exception:  # a failed heartbeat is a link problem, not a process problem
                log.exception("heartbeat failed")

    # -- transport -------------------------------------------------------------------

    async def _await_deferred(self, deferred: Any) -> Any:
        return await deferred.asFuture(self.loop)

    async def _send(
        self, request: Any, *, expect_response: bool = True, timeout_s: float = DEFAULT_REQUEST_TIMEOUT_S
    ) -> Any:
        if self._client is None:
            raise BrokerError("broker link is not open")
        if not expect_response:
            try:
                protocol = await asyncio.wait_for(
                    self._await_deferred(self._client.whenConnected()),
                    timeout=timeout_s,
                )
                protocol.send(request, instant=True)
            except (TimeoutError, TwistedTimeoutError) as e:
                raise BrokerError(
                    f"broker link not available to send {type(request).__name__}"
                ) from e
            return None
        try:
            deferred = self._client.send(request, responseTimeoutInSeconds=timeout_s)
            response = await self._await_deferred(deferred)
        except TwistedTimeoutError as e:
            req_name = type(request).__name__
            raise BrokerError(f"broker request timed out after {timeout_s}s: {req_name}") from e
        message = Protobuf.extract(response)
        if isinstance(message, ProtoOAErrorRes):
            self.state.last_error = message.errorCode
            if message.maintenanceEndTimestamp:
                self.state.maintenance_until = message.maintenanceEndTimestamp
            raise BrokerError(f"{message.errorCode}: {message.description}")
        return message

    # -- auth ------------------------------------------------------------------------

    async def _authenticate(self) -> None:
        """App auth, then the demo guard, then account auth. The guard runs before the account."""
        await self._send(
            ProtoOAApplicationAuthReq(clientId=self.client_id, clientSecret=self.client_secret)
        )
        await self._assert_demo_account()
        await self._send(
            ProtoOAAccountAuthReq(
                ctidTraderAccountId=self.account_id, accessToken=self.access_token
            )
        )
        self.state.authenticated = True
        self.state.account_id = self.account_id

    async def _assert_demo_account(self) -> None:
        """`isLive` lives on the account list, not on the trader record. Refuse a live account."""
        accounts = await self._send(
            ProtoOAGetAccountListByAccessTokenReq(accessToken=self.access_token)
        )
        for account in accounts.ctidTraderAccount:
            if account.ctidTraderAccountId == self.account_id:
                self.state.is_live = bool(account.isLive)
                if account.isLive:
                    raise BrokerError(
                        f"account {self.account_id} is LIVE; this build trades demo only"
                    )
                return
        raise BrokerError(f"account {self.account_id} is not on this access token")

    # -- symbols and assets ----------------------------------------------------------

    async def _load_symbols(self) -> None:
        """Light symbols give ids; `SymbolById` gives the volume specs; assets close the graph.

        The light symbol carries no `minVolume`, `stepVolume`, or `lotSize`, so sizing from it is
        the bug that sends a huge ounce count on a 0.01 lot gold order.
        """
        listed = await self._send(ProtoOASymbolsListReq(ctidTraderAccountId=self.account_id))
        light = {s.symbolName.upper(): s for s in listed.symbol}

        missing = [name for name in self.symbol_names if name.upper() not in light]
        if missing:
            raise BrokerError(f"symbols not offered by this account: {', '.join(missing)}")

        asset_list = await self._send(ProtoOAAssetListReq(ctidTraderAccountId=self.account_id))
        self.assets = {a.assetId: a.name for a in asset_list.asset}

        for name in self.symbol_names:
            entry = light[name.upper()]
            detail = await self._send(
                ProtoOASymbolByIdReq(ctidTraderAccountId=self.account_id, symbolId=[entry.symbolId])
            )
            if not detail.symbol:
                raise BrokerError(f"{name}: SymbolById returned no record")
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
            self.specs[name] = spec
            self.by_symbol_id[spec.symbol_id] = spec
            # Logged at subscribe time so a scale surprise is diagnosable from the evening's log.
            log.info(
                "symbol %s id=%d lotSize=%d min=%d step=%d max=%d digits=%d quote=%s",
                name, spec.symbol_id, spec.lot_size, spec.min_volume, spec.step_volume,
                spec.max_volume, spec.digits, self.assets.get(spec.quote_asset_id),
            )

        self.graph = AssetGraph(assets=self.assets, symbols=dict(self.by_symbol_id))
        self.state.symbols = len(self.specs)

    async def subscribe(self, period: str = "M5") -> None:
        """Spots for every configured symbol, plus live M5 trendbars for the chart."""
        symbol_ids = [spec.symbol_id for spec in self.specs.values()]
        await self._send(
            ProtoOASubscribeSpotsReq(ctidTraderAccountId=self.account_id, symbolId=symbol_ids)
        )
        for symbol_id in symbol_ids:
            await self._send(
                ProtoOASubscribeLiveTrendbarReq(
                    ctidTraderAccountId=self.account_id,
                    period=ProtoOATrendbarPeriod.Value(period),
                    symbolId=symbol_id,
                )
            )

    async def trendbars(self, symbol: str, *, period: str = "M5", count: int = 200) -> Any:
        """M5 history for the chart seed. Historical calls stay under 5 req/s."""
        spec = self._spec(symbol)
        elapsed = time.monotonic() - self._last_trendbar_req
        if elapsed < TRENDBAR_MIN_INTERVAL_S:
            await asyncio.sleep(TRENDBAR_MIN_INTERVAL_S - elapsed)
        self._last_trendbar_req = time.monotonic()

        now_ms = int(time.time() * 1000)
        period_ms = 5 * 60 * 1000
        return await self._send(
            ProtoOAGetTrendbarsReq(
                ctidTraderAccountId=self.account_id,
                symbolId=spec.symbol_id,
                period=ProtoOATrendbarPeriod.Value(period),
                fromTimestamp=now_ms - count * period_ms,
                toTimestamp=now_ms,
                count=count,
            )
        )

    # -- callbacks -------------------------------------------------------------------

    def on_spot(self, handler: Callable[[Quote], None]) -> None:
        """Register a pre-conflation spot tap. The tape ring uses this."""
        self._spot_handlers.append(contain(handler, what="spot"))

    def on_event(self, handler: Callable[[Any], None]) -> None:
        """Register an execution-event handler (fills, amendments, closes)."""
        self._event_handlers.append(contain(handler, what="execution"))

    def on_fill(self, handler: Callable[[dict[str, Any]], None]) -> None:
        self.on_event(handler)

    def _on_connected(self, _client: Client) -> None:
        self.state.connected = True
        log.info("broker link connected to %s:%d", self.host, self.port)

    def _on_disconnected(self, _client: Client, reason: Any) -> None:
        self.state.connected = False
        self.state.authenticated = False
        log.warning("broker link lost: %s", reason)

    def _on_message(self, _client: Client, message: Any) -> None:
        """Every inbound message lands here, inside the containment boundary."""
        extracted = Protobuf.extract(message)
        name = type(extracted).__name__

        if name == "ProtoOASpotEvent":
            spec = self.by_symbol_id.get(extracted.symbolId)
            if spec is None:
                return
            previous = self.quotes.get(spec.name)
            bid = extracted.bid or (previous.bid if previous else 0)
            ask = extracted.ask or (previous.ask if previous else 0)
            if not bid or not ask:
                return
            quote = Quote(symbol=spec.name, bid=bid, ask=ask, ts_ms=int(time.time() * 1000))
            self.quotes[spec.name] = quote
            for handler in self._spot_handlers:
                handler(quote)
            return

        if name == "ProtoOAExecutionEvent":
            for handler in self._event_handlers:
                handler(extracted)
            return

        if name == "ProtoOAErrorRes":
            self.state.last_error = extracted.errorCode
            if extracted.maintenanceEndTimestamp:
                self.state.maintenance_until = extracted.maintenanceEndTimestamp

    # -- Broker interface ------------------------------------------------------------

    def snapshot(self) -> dict[str, Any]:
        return self.state.as_dict()

    async def health(self) -> BrokerResult:
        if not self.state.connected:
            return BrokerResult(ok=False, reason="disconnected")
        if not self.state.authenticated:
            return BrokerResult(ok=False, reason="unauthenticated")
        return BrokerResult(ok=True, detail=self.state.as_dict())

    async def account(self) -> dict[str, Any]:
        """Balance and equity from cTrader. The journal never re-derives these from fills."""
        trader = await self._send(ProtoOATraderReq(ctidTraderAccountId=self.account_id))
        digits = trader.trader.moneyDigits or 2
        divisor = 10**digits
        return {
            "account_id": trader.trader.ctidTraderAccountId,
            "balance": trader.trader.balance / divisor,
            "broker": trader.trader.brokerName,
        }

    async def positions(self) -> list[dict[str, Any]]:
        """`Reconcile` — cTrader is the source of truth for what is open."""
        reconciled = await self._send(ProtoOAReconcileReq(ctidTraderAccountId=self.account_id))
        out: list[dict[str, Any]] = []
        for position in reconciled.position:
            spec = self.by_symbol_id.get(position.tradeData.symbolId)
            out.append(
                {
                    "positionId": position.positionId,
                    "symbol": spec.name if spec else str(position.tradeData.symbolId),
                    "side": "buy" if position.tradeData.tradeSide == SIDE_BUY else "sell",
                    "volume": position.tradeData.volume,
                    "entry": position.price,
                    "sl": position.stopLoss or None,
                    "tp": position.takeProfit or None,
                    "label": position.tradeData.label,
                    "openedAt": position.tradeData.openTimestamp,
                }
            )
        return out

    async def place(
        self, *, cid: str, sym: str, side: str, lots: float,
        relative_sl: int | None = None, relative_tp: int | None = None,
    ) -> BrokerResult:
        """MARKET open. Protection is relative — absolute SL/TP is not valid for this order type."""
        spec = self._spec(sym)
        trade_side = SIDES.get(side.lower())
        if trade_side is None:
            return BrokerResult(ok=False, reason="bad_side", detail={"cid": cid, "side": side})

        request = ProtoOANewOrderReq(
            ctidTraderAccountId=self.account_id,
            symbolId=spec.symbol_id,
            orderType=MARKET,
            tradeSide=trade_side,
            volume=lots_to_volume(lots, spec),
            label=f"{LABEL_PREFIX}{cid[-LABEL_CID_CHARS:]}",
            clientOrderId=cid,
        )
        if relative_sl is not None:
            request.relativeStopLoss = relative_sl
        if relative_tp is not None:
            request.relativeTakeProfit = relative_tp

        try:
            await self._send(request)
        except BrokerError as exc:
            return BrokerResult(ok=False, reason="broker_reject", detail={"cid": cid, "error": str(exc)})
        return BrokerResult(ok=True, detail={"cid": cid, "volume": request.volume})

    async def close(self, *, cid: str, position_id: int) -> BrokerResult:
        """Full close. No partial closes exist in this product."""
        open_positions = {p["positionId"]: p for p in await self.positions()}
        position = open_positions.get(position_id)
        if position is None:
            return BrokerResult(ok=False, reason="unknown_position", detail={"cid": cid})
        try:
            await self._send(
                ProtoOAClosePositionReq(
                    ctidTraderAccountId=self.account_id,
                    positionId=position_id,
                    volume=position["volume"],
                )
            )
        except BrokerError as exc:
            return BrokerResult(ok=False, reason="broker_reject", detail={"cid": cid, "error": str(exc)})
        return BrokerResult(ok=True, detail={"cid": cid, "positionId": position_id})

    async def amend_position_sl_tp(
        self, *, cid: str, position_id: int, sl: float | None = None, tp: float | None = None
    ) -> BrokerResult:
        """Absolute SL/TP on an open position — the one place absolute protection is valid."""
        request = ProtoOAAmendPositionSLTPReq(
            ctidTraderAccountId=self.account_id, positionId=position_id
        )
        if sl is not None:
            request.stopLoss = sl
        if tp is not None:
            request.takeProfit = tp
        try:
            await self._send(request)
        except BrokerError as exc:
            return BrokerResult(ok=False, reason="broker_reject", detail={"cid": cid, "error": str(exc)})
        return BrokerResult(ok=True, detail={"cid": cid, "positionId": position_id})

    async def panic(self, *, cid: str) -> list[BrokerResult]:
        """Flatten everything. Each close is independent — one failure never stops the rest."""
        results: list[BrokerResult] = []
        for position in await self.positions():
            results.append(await self.close(cid=cid, position_id=position["positionId"]))
        return results

    # -- helpers ---------------------------------------------------------------------

    def _spec(self, symbol: str) -> SymbolSpec:
        spec = self.specs.get(symbol)
        if spec is None:
            raise BrokerError(f"{symbol} was never loaded from SymbolById")
        return spec

    def relative_protection(self, symbol: str, entry: float, protection: float | None) -> int | None:
        """Absolute price to the 1/100000 distance a MARKET order accepts."""
        if protection is None:
            return None
        self._spec(symbol)
        return relative_distance(entry, protection)
