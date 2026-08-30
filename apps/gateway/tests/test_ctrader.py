"""The cTrader link, driven through a mock that speaks real Protobuf.

Everything under test here is the gateway's own message construction and
translation. The mock replaces the socket, not the protocol -- so a bug in
symbol mapping, the lots/volume scale, or execution-event handling fails these
tests exactly as it would fail against Spotware.

What these tests cannot prove: that the *numbers* match IC Markets. The mock's
symbol specs are invented. Phase 2's acceptance run still needs a real
SymbolsList + SymbolById dump and a hand-verified 0.01-lot gold round trip.
"""

from __future__ import annotations

import asyncio

import pytest
import yaml
from ctrader_open_api.messages import OpenApiMessages_pb2 as msgs
from ctrader_open_api.messages import OpenApiModelMessages_pb2 as model

from apps.gateway.broker.base import BrokerFault
from apps.gateway.broker.ctrader import CTraderBroker
from apps.gateway.broker.mock import MockState, MockTransport
from apps.gateway.broker.types import OpenRequest
from apps.gateway.broker.volume import lots_to_volume
from apps.gateway.config import Config
from apps.gateway.protocol import new_cid


def config(**over) -> Config:
    raw = yaml.safe_load(open("config/mock.yaml"))
    raw.update(over)
    return Config.model_validate(raw)


def make(state: MockState | None = None, cfg: Config | None = None):
    cfg = cfg or config()
    transport = MockTransport(state)
    env = {
        cfg.broker.client_id_env: "id",
        cfg.broker.client_secret_env: "secret",
        cfg.broker.token_env: transport.state.access_token,
        cfg.broker.refresh_env: transport.state.refresh_token,
        cfg.broker.account_id_env: str(transport.state.account_id),
    }
    return CTraderBroker(cfg, transport, env=env), transport


async def started(state: MockState | None = None):
    broker, transport = make(state)
    await broker.start()
    return broker, transport


async def settle() -> None:
    """Let a deferred broker event land.

    A fill follows its accept on a later tick, exactly as it does over a real
    socket -- so a caller that needs the position to exist has to wait for it.
    """
    await asyncio.sleep(0)


# -- connect ----------------------------------------------------------------


async def test_start_resolves_symbols_assets_and_positions():
    broker, transport = await started()
    health = await broker.health()
    assert health.connected and health.authed
    assert health.symbols == ["EURUSD", "GBPUSD", "USDJPY", "XAUUSD"]
    assert broker.account_id == transport.state.account_id
    assert broker.is_live is False


async def test_a_live_account_is_refused_before_account_auth():
    """isLive lives on ProtoOACtidTraderAccount, so the guard fires before the
    gateway has authenticated, let alone placed anything."""
    broker, transport = make(MockState(is_live=True))
    with pytest.raises(BrokerFault, match="LIVE"):
        await broker.start()
    sent = [type(m).__name__ for m in transport.state.sent]
    assert "ProtoOAAccountAuthReq" not in sent
    assert "ProtoOANewOrderReq" not in sent


async def test_volume_spec_comes_from_symbol_by_id_not_the_light_symbol():
    """SymbolsList returns ProtoOALightSymbol, which carries no volume spec.
    If the broker ever read min/step/max from there they would all be zero."""
    broker, transport = await started()
    sent = [type(m).__name__ for m in transport.state.sent]
    assert sent.count("ProtoOASymbolByIdReq") == 4

    gold = broker.symbol_spec("XAUUSD")
    assert (gold.min_volume, gold.step_volume, gold.lot_size) == (100, 100, 10_000)
    # And the assets, which only the *light* symbol carries.
    assert broker.graph.asset_name(gold.quote_asset_id) == "USD"
    assert broker.graph.asset_name(broker.symbol_spec("USDJPY").quote_asset_id) == "JPY"


async def test_a_missing_symbol_refuses_rather_than_guessing_a_suffix():
    cfg = config()
    cfg.symbols[0].name = "XAUUSD.raw"
    broker, _ = make(cfg=cfg)
    with pytest.raises(BrokerFault, match="not on this account"):
        await broker.start()


async def test_an_expired_token_refreshes_and_retries(tmp_path):
    cfg = config()
    cfg.db_path = str(tmp_path / "ev.sqlite3")
    broker, transport = make(MockState(expire_access_token_once=True), cfg=cfg)
    await broker.start()
    assert broker.authed
    assert transport.state.access_token == "mock-access-token-refreshed"

    # Refreshed tokens land in the protected app volume at 0600 -- never git,
    # a log, the browser, or a backup.
    token_file = tmp_path / "ctrader-tokens.env"
    assert token_file.is_file()
    assert oct(token_file.stat().st_mode)[-3:] == "600"
    assert "mock-access-token-refreshed" in token_file.read_text()


async def test_no_refresh_token_names_the_manual_flow():
    cfg = config()
    broker, transport = make(MockState(expire_access_token_once=True), cfg=cfg)
    broker.env[cfg.broker.refresh_env] = ""
    with pytest.raises(BrokerFault, match="README"):
        await broker.start()


# -- orders -----------------------------------------------------------------


async def test_a_market_open_produces_a_position():
    broker, transport = await started()
    cid = new_cid()
    spec = broker.symbol_spec("XAUUSD")
    result = await broker.place(OpenRequest(
        cid=cid, sym="XAUUSD", side="buy",
        volume=lots_to_volume(0.01, spec),
    ))
    assert result.ok, result.detail
    assert result.position_id
    assert len(transport.state.positions) == 1
    assert transport.state.positions[result.position_id].volume == 100


async def test_the_order_carries_relative_protection_and_no_absolute():
    """MARKET orders take relativeStopLoss/relativeTakeProfit. Absolute SL/TP
    is not valid on this order type and goes through AmendPositionSLTP."""
    broker, transport = await started()
    spec = broker.symbol_spec("XAUUSD")
    await broker.place(OpenRequest(
        cid=new_cid(), sym="XAUUSD", side="buy",
        volume=lots_to_volume(0.01, spec),
        relative_sl=200_000, relative_tp=400_000,
    ))
    order = next(m for m in transport.state.sent
                 if type(m).__name__ == "ProtoOANewOrderReq")
    assert order.orderType == model.MARKET
    assert order.relativeStopLoss == 200_000
    assert order.relativeTakeProfit == 400_000
    assert not order.HasField("stopLoss")
    assert not order.HasField("takeProfit")


async def test_the_order_carries_the_cid_as_client_order_id():
    """cid is how a duplicate is caught and how a fill is matched back to the
    plan that produced it."""
    broker, transport = await started()
    cid = new_cid()
    spec = broker.symbol_spec("XAUUSD")
    await broker.place(OpenRequest(cid=cid, sym="XAUUSD", side="buy",
                                   volume=lots_to_volume(0.01, spec)))
    order = next(m for m in transport.state.sent
                 if type(m).__name__ == "ProtoOANewOrderReq")
    assert order.clientOrderId == cid
    assert order.label.startswith("evgp")
    assert len(order.label) <= 12


async def test_gold_sends_one_ounce_for_a_hundredth_of_a_lot():
    """The scale that would otherwise be a margin call, asserted against the
    volume the broker actually receives."""
    broker, transport = await started()
    spec = broker.symbol_spec("XAUUSD")
    await broker.place(OpenRequest(cid=new_cid(), sym="XAUUSD", side="buy",
                                   volume=lots_to_volume(0.01, spec)))
    order = next(m for m in transport.state.sent
                 if type(m).__name__ == "ProtoOANewOrderReq")
    assert order.volume == 100          # cents of a unit
    assert order.volume / 100 == 1      # one ounce

    eur = broker.symbol_spec("EURUSD")
    await broker.place(OpenRequest(cid=new_cid(), sym="EURUSD", side="buy",
                                   volume=lots_to_volume(0.01, eur)))
    orders = [m for m in transport.state.sent
              if type(m).__name__ == "ProtoOANewOrderReq"]
    assert orders[-1].volume / 100 == 1_000   # 0.01 FX lot = 1000 units


async def test_a_volume_off_the_broker_grid_is_rejected_not_rounded():
    """The mock enforces min/step/max the way the broker does, so a conversion
    bug surfaces as a rejection instead of a silently different order."""
    broker, _ = await started()
    result = await broker.place(OpenRequest(
        cid=new_cid(), sym="XAUUSD", side="buy", volume=150,
    ))
    assert not result.ok
    assert result.reason == "lot_step"


async def test_volume_above_the_broker_max_never_leaves_the_process():
    broker, transport = await started()
    result = await broker.place(OpenRequest(
        cid=new_cid(), sym="XAUUSD", side="buy", volume=99_999_999,
    ))
    assert (result.ok, result.reason) == (False, "max_lots")
    assert not [m for m in transport.state.sent
                if type(m).__name__ == "ProtoOANewOrderReq"]


async def test_broker_error_codes_map_to_protocol_reject_reasons():
    broker, transport = await started()
    spec = broker.symbol_spec("XAUUSD")
    transport.state.reject_next_order_with = "MARKET_CLOSED"
    result = await broker.place(OpenRequest(
        cid=new_cid(), sym="XAUUSD", side="buy", volume=lots_to_volume(0.01, spec)))
    assert (result.ok, result.reason) == (False, "session_closed")


async def test_close_sends_the_full_volume():
    """Partial closes are outside this product; the mock refuses one, so a
    regression that sent a partial would fail here."""
    broker, transport = await started()
    spec = broker.symbol_spec("XAUUSD")
    opened = await broker.place(OpenRequest(cid=new_cid(), sym="XAUUSD", side="buy",
                                            volume=lots_to_volume(0.01, spec)))
    await settle()   # the position exists once the fill lands, not before
    result = await broker.close(opened.position_id, new_cid())
    assert result.ok
    close = next(m for m in transport.state.sent
                 if type(m).__name__ == "ProtoOAClosePositionReq")
    assert close.volume == 100
    assert transport.state.positions == {}


async def test_closing_an_unknown_position_does_not_reach_the_broker():
    broker, transport = await started()
    result = await broker.close(999_999, new_cid())
    assert not result.ok
    assert not [m for m in transport.state.sent
                if type(m).__name__ == "ProtoOAClosePositionReq"]


async def test_amend_sends_absolute_prices_and_only_what_changed():
    """Leaving a field unset on AmendPositionSLTP clears that protection, so
    only the side the player edited may be present."""
    broker, transport = await started()
    spec = broker.symbol_spec("XAUUSD")
    opened = await broker.place(OpenRequest(cid=new_cid(), sym="XAUUSD", side="buy",
                                            volume=lots_to_volume(0.01, spec)))
    await settle()
    result = await broker.amend_position_sl_tp(opened.position_id, new_cid(),
                                               sl=2335.0, tp=None)
    assert result.ok
    amend = next(m for m in transport.state.sent
                 if type(m).__name__ == "ProtoOAAmendPositionSLTPReq")
    assert amend.stopLoss == pytest.approx(2335.0)
    assert not amend.HasField("takeProfit")
    assert transport.state.positions[opened.position_id].sl == pytest.approx(2335.0)


async def test_relative_protection_lands_on_the_protective_side():
    """A long's stop is below entry and a short's is above. Getting the sign
    wrong would place a stop that fills instantly."""
    broker, transport = await started()
    spec = broker.symbol_spec("XAUUSD")
    long = await broker.place(OpenRequest(
        cid=new_cid(), sym="XAUUSD", side="buy",
        volume=lots_to_volume(0.01, spec), relative_sl=200_000, relative_tp=400_000))
    short = await broker.place(OpenRequest(
        cid=new_cid(), sym="XAUUSD", side="sell",
        volume=lots_to_volume(0.01, spec), relative_sl=200_000, relative_tp=400_000))

    lp = transport.state.positions[long.position_id]
    sp = transport.state.positions[short.position_id]
    assert lp.sl < lp.entry < lp.tp
    assert sp.tp < sp.entry < sp.sl


# -- events -----------------------------------------------------------------


async def test_a_fill_arrives_as_an_event_after_the_accept():
    """cTrader answers ORDER_ACCEPTED and *then* pushes ORDER_FILLED. Treating
    the accept as a fill would show a position that does not exist yet."""
    seen = []
    broker, transport = await started()
    broker.set_execution_sink(seen.append)
    spec = broker.symbol_spec("XAUUSD")
    await broker.place(OpenRequest(cid=new_cid(), sym="XAUUSD", side="buy",
                                   volume=lots_to_volume(0.01, spec)))
    await settle()
    kinds = [u.kind for u in seen]
    assert kinds == ["accepted", "filled"]
    assert seen[-1].price == pytest.approx(2340.35)   # bought at the ask
    assert seen[-1].sym == "XAUUSD"
    assert seen[-1].side == "buy"


async def test_a_close_reports_pnl_scaled_by_money_digits():
    """grossProfit is an integer scaled by moneyDigits. Reading it raw would
    inflate every P/L a hundredfold."""
    seen = []
    broker, transport = await started()
    spec = broker.symbol_spec("XAUUSD")
    opened = await broker.place(OpenRequest(cid=new_cid(), sym="XAUUSD", side="buy",
                                            volume=lots_to_volume(0.01, spec)))
    await settle()
    broker.set_execution_sink(seen.append)
    await broker.close(opened.position_id, new_cid())

    closed = next(u for u in seen if u.kind == "closed")
    # Bought at 2340.35, sold at the 2340.15 bid, one ounce: -0.20.
    assert closed.gross_pnl == pytest.approx(-0.20, abs=0.01)
    assert closed.commission == pytest.approx(-3.00)
    assert closed.entry == pytest.approx(2340.35)


async def test_a_stop_out_closes_the_position_without_a_request():
    seen = []
    broker, transport = await started()
    spec = broker.symbol_spec("XAUUSD")
    opened = await broker.place(OpenRequest(cid=new_cid(), sym="XAUUSD", side="buy",
                                            volume=lots_to_volume(0.01, spec)))
    await settle()
    broker.set_execution_sink(seen.append)
    transport.push_stop_out(opened.position_id, 2335.00)
    assert seen[-1].kind == "closed"
    assert await broker.positions() == []


async def test_spots_update_quotes_and_the_conversion_graph():
    broker, transport = await started()
    ticks = []
    broker.set_spot_sink(lambda *a: ticks.append(a))
    transport.push_spot("XAUUSD", bid=2341.00, ask=2341.20, ts=1_700_000_000_000)

    quote = (await broker.snapshot())["XAUUSD"]
    assert (quote.bid, quote.ask) == (pytest.approx(2341.00), pytest.approx(2341.20))
    # The raw tap gets scaled integers, which is what the tape ring stores.
    assert ticks == [("XAUUSD", 234_100_000, 234_120_000, 1_700_000_000_000)]

    transport.push_spot("USDJPY", bid=150.10, ask=150.12)
    conv = broker.graph.to_usd("JPY", 0)
    assert conv.rate == pytest.approx(1 / 150.11)


async def test_a_one_sided_tick_keeps_the_other_side():
    """Real spot events carry only what moved. Publishing a zero for the
    missing side would produce a nonsense spread and a bogus sentinel."""
    broker, transport = await started()
    transport.push_spot("XAUUSD", bid=2341.00, ask=2341.20)
    transport.push_spot("XAUUSD", ask=2341.40)
    quote = (await broker.snapshot())["XAUUSD"]
    assert quote.bid == pytest.approx(2341.00)
    assert quote.ask == pytest.approx(2341.40)


async def test_a_spot_for_an_unknown_symbol_is_ignored():
    broker, transport = await started()
    event = msgs.ProtoOASpotEvent(ctidTraderAccountId=1, symbolId=99_999)
    event.bid = 100
    transport._push(event)
    assert "99999" not in (await broker.snapshot())


async def test_an_exception_in_a_callback_does_not_escape():
    """One process is one blast radius. A broken sink must not take the HUD,
    the socket, and the journal down with it."""
    broker, transport = await started()

    def explode(update):
        raise RuntimeError("sink is broken")

    broker.set_execution_sink(explode)
    faults_before = broker.containment.faults
    transport.push_spot("XAUUSD", bid=2341.0, ask=2341.2)  # still works
    spec = broker.symbol_spec("XAUUSD")
    result = await broker.place(OpenRequest(cid=new_cid(), sym="XAUUSD", side="buy",
                                            volume=lots_to_volume(0.01, spec)))
    await settle()
    assert result.ok, "a broken sink must not fail the order"
    assert broker.containment.faults > faults_before
    assert (await broker.health()).connected


async def test_an_unsolicited_error_becomes_a_fault_not_a_crash():
    broker, transport = await started()
    before = broker.containment.faults
    transport.push_error("MARKET_CLOSED", "out of hours")
    assert broker.containment.faults == before + 1


async def test_heartbeats_keep_the_proxy_alive():
    broker, transport = await started()
    transport.send_nowait(_heartbeat())
    assert any(type(m).__name__ == "ProtoHeartbeatEvent" for m in transport.state.sent)


def _heartbeat():
    from ctrader_open_api.messages import OpenApiCommonMessages_pb2 as common

    return common.ProtoHeartbeatEvent()


# -- reconnect --------------------------------------------------------------


async def test_reconcile_replaces_the_book_rather_than_merging_it():
    """cTrader is the source of truth after a reconnect. Merging would
    resurrect a position the broker closed while we were away."""
    broker, transport = await started()
    spec = broker.symbol_spec("XAUUSD")
    opened = await broker.place(OpenRequest(cid=new_cid(), sym="XAUUSD", side="buy",
                                            volume=lots_to_volume(0.01, spec)))
    await settle()
    assert len(await broker.positions()) == 1

    del transport.state.positions[opened.position_id]   # closed while away
    assert await broker.reconcile() == []
    assert await broker.positions() == []


async def test_reconcile_restores_a_position_this_process_never_opened():
    broker, transport = await started()
    from apps.gateway.broker.mock import MockPosition

    transport.state.positions[7_777] = MockPosition(
        position_id=7_777, symbol_id=41, side=model.SELL, volume=200,
        entry=2350.0, opened_at=1_700_000_000_000, sl=2355.0, label="evgpABCDEFGH",
    )
    positions = await broker.reconcile()
    assert len(positions) == 1
    p = positions[0]
    assert (p.sym, p.side, p.volume, p.entry) == ("XAUUSD", "sell", 200, 2350.0)
    assert p.sl == pytest.approx(2355.0)
    assert broker.lots_of(p) == pytest.approx(0.02)


async def test_closed_positions_are_not_reconciled_as_open():
    broker, transport = await started()
    res = msgs.ProtoOAReconcileRes(ctidTraderAccountId=broker.account_id)
    p = res.position.add()
    p.positionId = 42
    p.positionStatus = model.POSITION_STATUS_CLOSED
    p.price = 1.0
    p.tradeData.symbolId = 41
    p.tradeData.volume = 100
    p.tradeData.tradeSide = model.BUY
    transport._on_ProtoOAReconcileReq = lambda req: res
    assert await broker.reconcile() == []


# -- account ----------------------------------------------------------------


async def test_balance_is_read_from_ctrader_not_derived_from_fills():
    broker, transport = await started()
    account = await broker.account()
    assert account.balance == pytest.approx(10_000.00)
    assert account.is_live is False

    transport.state.balance_cents = 987_654
    assert (await broker.account()).balance == pytest.approx(9_876.54)


# -- reconnect watchdog -----------------------------------------------------


async def test_the_watchdog_restores_the_link_and_reconciles():
    """One link, one axis: either Spotware is reachable or it is not. On the
    way back cTrader is the source of truth, so the book is rebuilt."""
    import apps.gateway.broker.ctrader as ct
    from apps.gateway.broker.mock import MockPosition

    broker, transport = await started()
    seen: list[list] = []
    broker.set_reconnect_sink(seen.append)

    # The link drops, and a position appears while we are away.
    transport.connected = False
    broker.authed = False
    transport.state.positions[8_800] = MockPosition(
        position_id=8_800, symbol_id=41, side=model.BUY, volume=100,
        entry=2339.0, opened_at=1_700_000_000_000,
    )

    original = ct.RECONNECT_POLL_S
    ct.RECONNECT_POLL_S = 0.01
    try:
        await broker.stop()
        broker._watchdog_task = asyncio.create_task(broker._watchdog_loop())
        for _ in range(200):
            await asyncio.sleep(0.01)
            if broker.authed:
                break
        # Captured before teardown: stop() clears `authed` by design.
        recovered = broker.authed
        reconnects = broker.reconnects
        book = [p.position_id for p in await broker.positions()]
    finally:
        ct.RECONNECT_POLL_S = original
        await broker.stop()

    assert recovered is True, f"detail={broker._detail} faults={broker.containment.faults}"
    assert reconnects == 1
    assert book == [8_800]
    assert seen and [p.position_id for p in seen[0]] == [8_800]


async def test_health_reports_the_link_as_down_while_it_is_down():
    broker, transport = await started()
    transport.connected = False
    health = await broker.health()
    assert health.connected is False
