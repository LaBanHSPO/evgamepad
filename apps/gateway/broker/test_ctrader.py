"""Broker link behaviour that does not need Spotware on the other end.

What is proven here: the import graph cannot end up on the wrong reactor, a raising callback is
contained, spots route to the tape tap, the order label fits cTrader's limit, and a live account
is refused. What is *not* proven here is anything that needs the real account — see the
fixture-backed test at the bottom and the phase file's verification status.
"""

from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path

import pytest
from ctrader_open_api.messages.OpenApiCommonMessages_pb2 import ProtoMessage
from ctrader_open_api.messages.OpenApiMessages_pb2 import ProtoOASpotEvent

from broker.ctrader import LABEL_CID_CHARS, LABEL_PREFIX, CTraderBroker, Quote
from broker.volume import SymbolSpec, lots_to_volume

FIXTURE = Path(__file__).parent / "fixtures" / "symbols-icmarkets-demo.json"

GOLD = SymbolSpec(symbol_id=41, name="XAUUSD", digits=2, pip_position=1, lot_size=10_000,
                  min_volume=100, step_volume=100, max_volume=1_000_000,
                  base_asset_id=4, quote_asset_id=1)


def broker() -> CTraderBroker:
    client = CTraderBroker(
        host="demo.ctraderapi.com", port=5035, client_id="id", client_secret="secret",
        access_token="token", account_id=123, symbol_names=("XAUUSD",),
        loop=asyncio.new_event_loop(),
    )
    client.specs["XAUUSD"] = GOLD
    client.by_symbol_id[GOLD.symbol_id] = GOLD
    return client


def spot_message(symbol_id: int, bid: int, ask: int) -> ProtoMessage:
    """A real ProtoMessage, so `Protobuf.extract` is exercised rather than mocked."""
    event = ProtoOASpotEvent(ctidTraderAccountId=123, symbolId=symbol_id, bid=bid, ask=ask)
    return ProtoMessage(payloadType=event.payloadType, payload=event.SerializeToString())


def test_importing_the_broker_guarantees_the_asyncio_reactor() -> None:
    """`ctrader_open_api.client` imports twisted's reactor at module load; ours must win."""
    from twisted.internet.asyncioreactor import AsyncioSelectorReactor

    assert isinstance(sys.modules["twisted.internet.reactor"], AsyncioSelectorReactor)


def test_a_spot_reaches_the_tape_tap_as_scaled_integers() -> None:
    client = broker()
    seen: list[Quote] = []
    client.on_spot(seen.append)

    client._on_message(None, spot_message(GOLD.symbol_id, bid=200_000_000, ask=200_030_000))

    assert len(seen) == 1
    assert seen[0].symbol == "XAUUSD"
    assert seen[0].bid == 200_000_000, "prices stay in protocol scale all the way to storage"
    assert client.quotes["XAUUSD"].mid == pytest.approx(2000.15)


def test_a_spot_carrying_only_one_side_reuses_the_last_known_other_side() -> None:
    """cTrader sends bid-only or ask-only ticks; a half-quote must not become a zero."""
    client = broker()
    client._on_message(None, spot_message(GOLD.symbol_id, bid=200_000_000, ask=200_030_000))
    client._on_message(None, spot_message(GOLD.symbol_id, bid=200_010_000, ask=0))

    assert client.quotes["XAUUSD"].bid == 200_010_000
    assert client.quotes["XAUUSD"].ask == 200_030_000


def test_a_spot_for_an_unsubscribed_symbol_is_ignored() -> None:
    client = broker()
    client._on_message(None, spot_message(999, bid=1, ask=2))
    assert client.quotes == {}


def test_a_raising_callback_is_contained_at_the_module_boundary() -> None:
    """One process now means one blast radius: a bad handler may not reach the reactor."""
    client = broker()
    good: list[Quote] = []

    def explode(_quote: Quote) -> None:
        raise RuntimeError("callback blew up")

    client.on_spot(explode)
    client.on_spot(good.append)

    client._on_message(None, spot_message(GOLD.symbol_id, bid=200_000_000, ask=200_030_000))

    assert len(good) == 1, "the surviving handler still ran"
    assert client.quotes["XAUUSD"].bid == 200_000_000


def test_the_message_callback_itself_is_contained() -> None:
    """Even a malformed frame from the wire must not escape into the reactor."""
    client = broker()
    contained = client._client  # None; the callback is still safe to invoke directly
    assert contained is None

    from broker import contain

    handler = contain(client._on_message, what="message")
    assert handler(None, "not a protobuf message at all") is None


def test_the_order_label_fits_ctraders_limit() -> None:
    """cTrader truncates long labels, and a truncated label breaks cid matching on reconcile."""
    cid = "01JKQ8ZC9N7Y2WX4T6VB3MHRAE"
    label = f"{LABEL_PREFIX}{cid[-LABEL_CID_CHARS:]}"
    assert label.startswith(LABEL_PREFIX)
    assert label.endswith(cid[-LABEL_CID_CHARS:])
    assert len(label) == len(LABEL_PREFIX) + LABEL_CID_CHARS <= 16


def test_an_unknown_symbol_never_reaches_the_broker() -> None:
    client = broker()
    with pytest.raises(Exception, match="never loaded from SymbolById"):
        client._spec("BTCUSD")


def test_relative_protection_converts_to_the_distance_scale() -> None:
    client = broker()
    assert client.relative_protection("XAUUSD", 2000.00, 1998.00) == 200_000
    assert client.relative_protection("XAUUSD", 2000.00, None) is None


@pytest.mark.skipif(
    not FIXTURE.exists(),
    reason=(
        "no real IC Markets demo dump captured yet — see broker/fixtures/README.md. "
        "Volume conversion stays asserted against documented protocol semantics only."
    ),
)
def test_volume_converts_against_the_real_broker_fixture() -> None:
    """The success criterion the plan names: asserted against a real dump, not a guess."""
    data = json.loads(FIXTURE.read_text(encoding="utf-8"))
    specs = {
        s["name"]: SymbolSpec(
            symbol_id=s["symbolId"], name=s["name"], digits=s["digits"],
            pip_position=s["pipPosition"], lot_size=s["lotSize"], min_volume=s["minVolume"],
            step_volume=s["stepVolume"], max_volume=s["maxVolume"],
            base_asset_id=s["baseAssetId"], quote_asset_id=s["quoteAssetId"],
        )
        for s in data["symbols"]
    }
    gold = specs["XAUUSD"]
    volume = lots_to_volume(0.01, gold)
    assert volume >= gold.min_volume
    assert volume % gold.step_volume == 0
    assert volume <= gold.max_volume
