"""Callback containment and the reactor guard."""

from __future__ import annotations

import sys

import pytest

from apps.gateway.broker import Containment, NotWiredBroker
from apps.gateway.broker.base import BrokerFault
from apps.gateway.broker.reactor_setup import ReactorError, verify
from apps.gateway.broker.types import OpenRequest


def test_a_raised_callback_becomes_a_fault_not_a_dead_process():
    """Removing the sidecar means a broker bug would otherwise take the HUD and
    the journal with it. It does not."""
    faults: list[tuple] = []
    c = Containment(lambda kind, detail, cid: faults.append((kind, cid)))

    @c("execution")
    def on_execution_event(event, cid=None):
        raise RuntimeError("protobuf field missing")

    assert on_execution_event({"x": 1}, cid="01J000000000000000000000AA") is None
    assert c.faults == 1
    assert faults == [("execution", "01J000000000000000000000AA")]


def test_a_faulty_fault_sink_cannot_escalate():
    def bad_sink(kind, detail, cid):
        raise RuntimeError("the sink is broken too")

    c = Containment(bad_sink)

    @c()
    def cb():
        raise ValueError("boom")

    assert cb() is None
    assert c.faults == 1


def test_containment_passes_a_healthy_return_through():
    c = Containment()

    @c()
    def cb(x):
        return x * 2

    assert cb(21) == 42
    assert c.faults == 0


async def test_not_wired_broker_refuses_every_broker_changing_call():
    b = NotWiredBroker()
    r = await b.place(OpenRequest(cid="01J000000000000000000000AA", sym="XAUUSD",
                                  side="buy", volume=100))
    assert (r.ok, r.reason) == (False, "not_wired")
    assert (await b.close(1, "c")).reason == "not_wired"
    assert (await b.amend_position_sl_tp(1, "c", 1.0, 2.0)).reason == "not_wired"
    assert (await b.health()).connected is False
    assert await b.positions() == []
    with pytest.raises(BrokerFault):
        await b.account()


def test_the_broker_interface_has_no_pending_or_partial_close():
    """Pending orders and partial closes are outside this product. Absence is a
    decision, so it is asserted."""
    names = dir(NotWiredBroker)
    assert not [n for n in names if "pending" in n or "partial" in n]


def test_order_label_fits_ctraders_limit():
    req = OpenRequest(cid="01JBXQ4T7ZK9M2N5P8R3V6W1YZ", sym="XAUUSD",
                      side="buy", volume=100)
    assert req.label.startswith("evgp")
    assert len(req.label) <= 12


def test_reactor_verify_is_a_no_op_without_twisted():
    if "twisted" in sys.modules or _twisted_installed():
        pytest.skip("twisted present; covered by the mismatch test instead")
    assert verify() is False


def test_reactor_mismatch_boot_fails():
    twisted = pytest.importorskip("twisted.internet")
    from twisted.internet import asyncioreactor

    class NotAsyncio:
        pass

    saved = sys.modules.get("twisted.internet.reactor")
    sys.modules["twisted.internet.reactor"] = NotAsyncio()  # type: ignore[assignment]
    try:
        with pytest.raises(ReactorError) as exc:
            verify()
        assert "AsyncioSelectorReactor" in str(exc.value)
        assert exc.value.code != 0
    finally:
        if saved is None:
            del sys.modules["twisted.internet.reactor"]
        else:
            sys.modules["twisted.internet.reactor"] = saved
    assert asyncioreactor  # referenced so the import is not flagged unused


def _twisted_installed() -> bool:
    import importlib.util

    return importlib.util.find_spec("twisted") is not None
