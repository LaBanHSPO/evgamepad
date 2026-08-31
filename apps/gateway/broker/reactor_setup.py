"""Install the asyncio reactor before anything imports `twisted.internet.reactor`.

OpenApiPy is Twisted; the gateway is asyncio. In one process they must share one event loop, and
Twisted decides that at the moment the reactor is first installed — which happens implicitly on
the first `from twisted.internet import reactor` anywhere in the import graph. Import this module
first and the choice is ours.

Get it wrong and nothing crashes: quotes arrive in bursts, awaits never resume, and the socket
merely looks slow. That is why a mismatch is a boot-fail with a named error rather than a warning.
"""

from __future__ import annotations

import asyncio
import sys
from typing import Any

REACTOR_MODULE = "twisted.internet.reactor"


class ReactorMismatch(RuntimeError):
    """A reactor other than the asyncio one is already installed. Fatal, never recoverable."""


def _is_asyncio_reactor(reactor: Any) -> bool:
    from twisted.internet.asyncioreactor import AsyncioSelectorReactor

    return isinstance(reactor, AsyncioSelectorReactor)


def install(loop: asyncio.AbstractEventLoop | None = None) -> Any:
    """Install (or verify) the asyncio reactor on `loop`. Returns the reactor.

    Idempotent when the installed reactor is already ours; raises `ReactorMismatch` otherwise, so
    an import-order regression fails at boot instead of at 3 a.m. mid-session.
    """
    existing = sys.modules.get(REACTOR_MODULE)
    if existing is not None:
        if not _is_asyncio_reactor(existing):
            raise ReactorMismatch(
                f"a {type(existing).__name__} is already installed; the gateway requires "
                "twisted.internet.asyncioreactor and something imported twisted.internet.reactor "
                "before broker.reactor_setup"
            )
        return existing

    from twisted.internet import asyncioreactor

    if loop is None:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    asyncioreactor.install(eventloop=loop)

    from twisted.internet import reactor

    return reactor


def start(reactor: Any) -> None:
    """Start the reactor's services without letting it own the loop or the signals.

    `reactor.run()` would block and install its own signal handlers; uvicorn owns both. The
    reactor only needs its services started — the asyncio loop underneath drives it from there.
    """
    if not reactor.running:
        reactor.startRunning(installSignalHandlers=False)


def verify_installed() -> Any:
    """Assert at boot that the reactor in play is the asyncio one."""
    reactor = sys.modules.get(REACTOR_MODULE)
    if reactor is None:
        raise ReactorMismatch("no reactor installed; call broker.reactor_setup.install() at boot")
    if not _is_asyncio_reactor(reactor):
        raise ReactorMismatch(f"installed reactor is {type(reactor).__name__}, not asyncio")
    return reactor
