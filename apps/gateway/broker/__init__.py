"""Broker boundary — an in-process module interface, not a wire protocol.

Phase 2 note: the network-touching calls are `async`. `snapshot()` stays synchronous because it
reads cached link state and `/healthz` must never wait on the broker.

There is no execution sidecar: the process that owns risk is the process that calls the broker.
Phase 1 freezes this interface and ships a stub that cannot place; phase 2 implements it against
OpenApiPy.

One process means one blast radius, so the containment boundary lives here from day one: a
broker callback may not raise past `contain`. Phase 2 tests that an exception inside a Protobuf
callback becomes an `order.reject`, not a dead gateway.
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any, TypeVar

log = logging.getLogger(__name__)

T = TypeVar("T")

NOT_WIRED = "not_wired"


@dataclass(frozen=True)
class BrokerResult:
    """Outcome of a broker-changing call. `reason` is what the HUD shows on a reject."""

    ok: bool
    reason: str | None = None
    detail: dict[str, Any] = field(default_factory=dict)


class Broker(ABC):
    """What the gateway is allowed to ask a broker for.

    No pending-order cancel and no partial close: v1 is MARKET in, full close out, with absolute
    SL/TP amendments on an open position.
    """

    @abstractmethod
    def snapshot(self) -> dict[str, Any]:
        """Cached link state. Synchronous and network-free — `/healthz` calls it."""

    @abstractmethod
    async def health(self) -> BrokerResult: ...

    @abstractmethod
    async def account(self) -> dict[str, Any]: ...

    @abstractmethod
    async def positions(self) -> list[dict[str, Any]]: ...

    @abstractmethod
    async def place(
        self,
        *,
        cid: str,
        sym: str,
        side: str,
        lots: float,
        relative_sl: int | None = None,
        relative_tp: int | None = None,
    ) -> BrokerResult: ...

    @abstractmethod
    async def close(self, *, cid: str, position_id: int) -> BrokerResult: ...

    @abstractmethod
    async def amend_position_sl_tp(
        self, *, cid: str, position_id: int, sl: float | None = None, tp: float | None = None
    ) -> BrokerResult: ...

    @abstractmethod
    def on_fill(self, handler: Callable[[dict[str, Any]], None]) -> None:
        """Register the fill callback. Implementations must route it through `contain`."""


class StubBroker(Broker):
    """Phase 1 placeholder: answers state queries emptily and refuses every order."""

    def __init__(self) -> None:
        self._fill_handler: Callable[[dict[str, Any]], None] | None = None

    def snapshot(self) -> dict[str, Any]:
        return {"connected": False, "reason": NOT_WIRED}

    async def health(self) -> BrokerResult:
        return BrokerResult(ok=False, reason=NOT_WIRED)

    async def account(self) -> dict[str, Any]:
        return {"reason": NOT_WIRED}

    async def positions(self) -> list[dict[str, Any]]:
        return []

    async def place(self, *, cid: str, sym: str, side: str, lots: float,
              relative_sl: int | None = None, relative_tp: int | None = None) -> BrokerResult:
        return BrokerResult(ok=False, reason=NOT_WIRED, detail={"cid": cid})

    async def close(self, *, cid: str, position_id: int) -> BrokerResult:
        return BrokerResult(ok=False, reason=NOT_WIRED, detail={"cid": cid})

    async def amend_position_sl_tp(self, *, cid: str, position_id: int,
                             sl: float | None = None, tp: float | None = None) -> BrokerResult:
        return BrokerResult(ok=False, reason=NOT_WIRED, detail={"cid": cid})

    def on_fill(self, handler: Callable[[dict[str, Any]], None]) -> None:
        self._fill_handler = contain(handler, what="fill")


def contain(fn: Callable[..., T], *, what: str, default: T | None = None) -> Callable[..., T | None]:
    """Wrap a broker callback so a raise inside it cannot take the gateway down.

    The exception is logged with its context and swallowed at this boundary. Callers that need
    to tell the player something turn the `None` into an `order.reject`.
    """

    def wrapped(*args: Any, **kwargs: Any) -> T | None:
        try:
            return fn(*args, **kwargs)
        except Exception:
            log.exception("broker callback `%s` raised; contained at the module boundary", what)
            return default

    return wrapped
