"""The broker interface and its containment boundary.

Removing the execution sidecar bought one process and one event loop, and cost
one blast radius: an unhandled exception in a Protobuf callback used to kill
``ev-exec`` alone, and would now take the HUD and the journal with it. That cost
is paid here, deliberately.

Every callback that Twisted or the Open API client can invoke goes through
:func:`contained`. A raised exception becomes an ``order.reject`` or a ``maint``
frame; it may never escape into the reactor.
"""

from __future__ import annotations

import logging
import traceback
from abc import ABC, abstractmethod
from collections.abc import Callable
from functools import wraps
from typing import Any

from .types import (
    AccountSnapshot,
    BrokerHealth,
    BrokerPosition,
    BrokerQuote,
    BrokerResult,
    OpenRequest,
    SymbolSpec,
)

log = logging.getLogger("ev.broker")

#: Called with (kind, detail, cid) when a callback faults. The gateway wires
#: this to an ``order.reject`` when a cid is in play and a ``maint`` otherwise.
FaultSink = Callable[[str, str, str | None], None]


class BrokerFault(RuntimeError):
    pass


class Containment:
    """One fault sink plus the decorator that feeds it."""

    def __init__(self, sink: FaultSink | None = None) -> None:
        self.sink: FaultSink | None = sink
        self.faults: int = 0

    def set_sink(self, sink: FaultSink) -> None:
        self.sink = sink

    def report(self, kind: str, detail: str, cid: str | None = None) -> None:
        self.faults += 1
        log.error("broker fault [%s] cid=%s: %s", kind, cid, detail)
        if self.sink is not None:
            try:
                self.sink(kind, detail, cid)
            except Exception:  # the sink itself must not escalate
                log.exception("fault sink raised; swallowing")

    def __call__(self, kind: str = "callback") -> Callable[[Callable], Callable]:
        """Decorator. Wraps a broker callback so it cannot take the process down."""

        def wrap(fn: Callable) -> Callable:
            @wraps(fn)
            def inner(*args: Any, **kwargs: Any) -> Any:
                try:
                    return fn(*args, **kwargs)
                except Exception as exc:
                    cid = kwargs.get("cid")
                    self.report(
                        kind,
                        f"{fn.__name__}: {exc}\n{traceback.format_exc(limit=4)}",
                        cid if isinstance(cid, str) else None,
                    )
                    return None

            return inner

        return wrap


class Broker(ABC):
    """A Python interface, not a wire protocol. The module that checks risk is
    the module that calls this -- there is no socket in between."""

    def __init__(self, containment: Containment | None = None) -> None:
        self.containment = containment or Containment()

    @abstractmethod
    async def health(self) -> BrokerHealth: ...

    @abstractmethod
    async def account(self) -> AccountSnapshot: ...

    @abstractmethod
    async def snapshot(self) -> dict[str, BrokerQuote]: ...

    @abstractmethod
    async def positions(self) -> list[BrokerPosition]: ...

    @abstractmethod
    async def place(self, req: OpenRequest) -> BrokerResult: ...

    @abstractmethod
    async def close(self, position_id: int, cid: str) -> BrokerResult: ...

    @abstractmethod
    async def amend_position_sl_tp(
        self, position_id: int, cid: str, sl: float | None, tp: float | None
    ) -> BrokerResult: ...

    @abstractmethod
    def symbol_spec(self, sym: str) -> SymbolSpec | None: ...

    # There is deliberately no cancel_pending and no partial_close: pending
    # orders and partial closes are outside this product.


class NotWiredBroker(Broker):
    """Phase 1's broker. Answers every question honestly and refuses to trade.

    ``place`` returning ``not_wired`` rather than raising is the point: the whole
    intent path -- protocol, cid reservation, risk, journal, reject frame -- is
    exercisable end to end before phase 2 has credentials to exercise it with.
    """

    def __init__(self, containment: Containment | None = None) -> None:
        super().__init__(containment)
        self.calls: list[tuple[str, Any]] = []

    async def health(self) -> BrokerHealth:
        return BrokerHealth(connected=False, authed=False, detail="not_wired: phase 2")

    async def account(self) -> AccountSnapshot:
        raise BrokerFault("not_wired: no cTrader connection until phase 2")

    async def snapshot(self) -> dict[str, BrokerQuote]:
        return {}

    async def positions(self) -> list[BrokerPosition]:
        return []

    async def place(self, req: OpenRequest) -> BrokerResult:
        self.calls.append(("place", req))
        return BrokerResult(ok=False, cid=req.cid, reason="not_wired")

    async def close(self, position_id: int, cid: str) -> BrokerResult:
        self.calls.append(("close", position_id))
        return BrokerResult(ok=False, cid=cid, reason="not_wired")

    async def amend_position_sl_tp(
        self, position_id: int, cid: str, sl: float | None, tp: float | None
    ) -> BrokerResult:
        self.calls.append(("amend", (position_id, sl, tp)))
        return BrokerResult(ok=False, cid=cid, reason="not_wired")

    def symbol_spec(self, sym: str) -> SymbolSpec | None:
        return None
